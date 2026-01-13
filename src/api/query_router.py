"""Deterministic Query Router for MSR Event Hub.

Routes 70-80% of queries via pattern matching to structured API calls,
bypassing LLM for common lookups (projects, sessions, people, logistics).
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from src.api.router_config import router_config
from src.api.router_prompt import INTENT_PATTERNS, CONFIDENCE_THRESHOLD_DETERMINISTIC

logger = logging.getLogger(__name__)


class QueryIntent:
    """Represents a classified query intent."""

    def __init__(
        self,
        intent: str,
        confidence: float,
        entities: Dict[str, Any],
        filters: Dict[str, Any],
        query_plan: List[Dict[str, Any]],
    ):
        self.intent = intent
        self.confidence = confidence
        self.entities = entities
        self.filters = filters
        self.query_plan = query_plan

    def is_deterministic(self) -> bool:
        """Check if this intent can be handled deterministically."""
        return self.confidence >= CONFIDENCE_THRESHOLD_DETERMINISTIC

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "entities": self.entities,
            "filters": self.filters,
            "query_plan": self.query_plan,
        }


class DeterministicRouter:
    """Deterministic query router using regex patterns."""

    def __init__(self):
        """Initialize router with compiled patterns."""
        self.patterns = {
            intent: [re.compile(p, re.IGNORECASE) for p in patterns]
            for intent, patterns in INTENT_PATTERNS.items()
        }

    def classify(self, query: str) -> Tuple[str, float]:
        """Classify query into primary intent with confidence.

        Returns:
            Tuple of (intent_name, confidence_score)
        """
        query_lower = query.lower()
        intent_scores = {}

        # Score each intent based on pattern matches
        for intent, patterns in self.patterns.items():
            matches = sum(1 for p in patterns if p.search(query_lower))
            if matches > 0:
                # Confidence = matches / total_patterns for this intent
                confidence = min(0.9, 0.5 + (matches / len(patterns)) * 0.4)
                intent_scores[intent] = confidence

        if not intent_scores:
            return ("project_search", 0.3)  # Default fallback

        # Return highest scoring intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent

    def extract_entities(self, query: str, intent: str) -> Dict[str, Any]:
        """Extract entities from query based on intent."""
        entities = {
            "eventId": None,
            "sessionId": None,
            "projectId": None,
            "projectTitleQuery": None,
            "personQuery": None,
            "categoryQuery": None,
        }

        query_lower = query.lower()

        # Extract quoted strings as exact matches
        quoted = re.findall(r'["\']([^"\']+)["\']', query)
        if quoted and intent in ["project_detail", "recording_status"]:
            entities["projectTitleQuery"] = quoted[0]

        # Extract category for category_browse
        if intent == "category_browse":
            category_patterns = [
                r"\bin\s+([A-Z]{2,})\b",  # "in HCI", "in AI"
                r"\bcategor[y|ies]\s+([A-Z]{2,})\b",
                r"\btrack\s+([A-Z]{2,})\b",
            ]
            for pattern in category_patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    entities["categoryQuery"] = match.group(1).upper()
                    break

        # Extract person names for people_lookup
        if intent == "people_lookup":
            # Look for "by <Name>" or "<Name>'s project"
            by_pattern = r"\bby\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
            possessive_pattern = r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s"
            match = re.search(by_pattern, query) or re.search(possessive_pattern, query)
            if match:
                entities["personQuery"] = match.group(1)

        # For project_search, extract keywords
        if intent == "project_search" and not entities["projectTitleQuery"]:
            # Extract everything after "about/related to/on"
            keyword_pattern = r"(?:about|related to|on)\s+(.+?)(?:\s+project|\s+poster|$)"
            match = re.search(keyword_pattern, query_lower)
            if match:
                entities["projectTitleQuery"] = match.group(1).strip()

        return entities

    def extract_filters(self, query: str, intent: str) -> Dict[str, Any]:
        """Extract filters from query."""
        filters = {
            "researchCategory": None,
            "preferredFormat": None,
            "equipmentKeywords": [],
            "placementKeywords": [],
            "requiresDedicatedSpace": None,
            "largeDisplay": None,
            "monitors27": None,
            "inference2030": None,
            "recordingSubmitted": None,
            "recordingEdited": None,
            "communicationSent": None,
        }

        query_lower = query.lower()

        # Equipment filters
        if intent == "logistics_equipment":
            if re.search(r"\blarge\s+display\b", query_lower):
                filters["largeDisplay"] = True
            # Extract monitor count
            monitor_match = re.search(r"(\d+)\s+monitor", query_lower)
            if monitor_match:
                filters["monitors27"] = int(monitor_match.group(1))
            # Extract equipment keywords
            equipment_terms = ["monitor", "display", "av", "power", "projector"]
            filters["equipmentKeywords"] = [
                term for term in equipment_terms if term in query_lower
            ]

        # Recording filters
        if intent == "recording_status":
            if "submitted" in query_lower:
                filters["recordingSubmitted"] = True
            if "edited" in query_lower:
                filters["recordingEdited"] = True

        # Format filters
        if intent == "logistics_format":
            if "demo" in query_lower:
                filters["preferredFormat"] = "demo"
            elif "poster" in query_lower:
                filters["preferredFormat"] = "poster"
            if "dedicated space" in query_lower:
                filters["requiresDedicatedSpace"] = True

        return filters

    def build_query_plan(
        self, intent: str, entities: Dict[str, Any], filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Build structured query plan based on intent."""
        plan = []

        if intent == "event_overview":
            plan.append(
                {
                    "operation": "get",
                    "endpoint": "GET /v1/events/{eventId}",
                    "params": {},
                    "return_fields": [
                        "displayName",
                        "description",
                        "eventType",
                        "startDate",
                        "endDate",
                        "location",
                        "timeZone",
                    ],
                }
            )

        elif intent == "session_lookup":
            plan.append(
                {
                    "operation": "list",
                    "endpoint": "GET /v1/events/{eventId}/sessions",
                    "params": {
                        "speaker": entities.get("personQuery"),
                        "keywords": entities.get("projectTitleQuery"),
                    },
                    "return_fields": [
                        "id",
                        "title",
                        "sessionType",
                        "startDateTime",
                        "endDateTime",
                        "location",
                        "speakers",
                    ],
                }
            )

        elif intent in ["project_search", "project_detail"]:
            operation = "get" if entities.get("projectId") else "search"
            endpoint = (
                f"GET /v1/events/{{eventId}}/projects/{{projectId}}"
                if operation == "get"
                else "GET /v1/events/{eventId}/projects"
            )
            plan.append(
                {
                    "operation": operation,
                    "endpoint": endpoint,
                    "params": {
                        "keywords": entities.get("projectTitleQuery"),
                        "category": filters.get("researchCategory")
                        or entities.get("categoryQuery"),
                    },
                    "return_fields": [
                        "id",
                        "name",
                        "description",
                        "researchArea",
                        "team",
                        "posterUrl",
                        "imageUrl",
                        "location",
                        "papers",
                        "repositories",
                    ],
                }
            )

        elif intent == "people_lookup":
            plan.append(
                {
                    "operation": "search",
                    "endpoint": "GET /v1/events/{eventId}/projects",
                    "params": {"person": entities.get("personQuery")},
                    "return_fields": [
                        "id",
                        "name",
                        "description",
                        "team",
                        "location",
                    ],
                }
            )

        elif intent == "category_browse":
            plan.append(
                {
                    "operation": "filter",
                    "endpoint": "GET /v1/events/{eventId}/projects",
                    "params": {
                        "category": filters.get("researchCategory")
                        or entities.get("categoryQuery")
                    },
                    "return_fields": [
                        "id",
                        "name",
                        "description",
                        "researchArea",
                        "team",
                        "location",
                    ],
                }
            )

        elif intent in [
            "logistics_equipment",
            "logistics_placement",
            "logistics_format",
            "recording_status",
        ]:
            # These require RRS Source of Truth table (spreadsheet/DB)
            plan.append(
                {
                    "operation": "filter",
                    "source": "rrs_source_of_truth_table",
                    "params": filters,
                    "return_fields": self._get_rrs_fields_for_intent(intent),
                }
            )

        return plan

    def _get_rrs_fields_for_intent(self, intent: str) -> List[str]:
        """Get RRS table fields to return for a given intent."""
        base_fields = ["ID", "Project Title", "Brief Project Description", "Team Members"]

        intent_fields = {
            "logistics_equipment": [
                "Equipment Needs",
                "Large Display",
                "27\" Monitors",
                "Technician Notes",
            ],
            "logistics_placement": ["Placement", "Location"],
            "logistics_format": [
                "Preferred Presentation Format",
                "Special Demo Requirements",
                "Requires non-floor dedicated space",
            ],
            "recording_status": [
                "Recording Submitted",
                "Recording Edited",
                "Recording Link",
                "Recording Notes",
            ],
        }

        return base_fields + intent_fields.get(intent, [])

    def route(self, query: str) -> QueryIntent:
        """Route a query to structured plan or LLM fallback.

        Returns:
            QueryIntent with classification and execution plan
        """
        # Check if deterministic routing is disabled
        if not router_config.enable_deterministic_routing:
            logger.info("Deterministic routing disabled; returning low-confidence intent for LLM fallback")
            return QueryIntent(
                intent="project_search",
                confidence=0.3,
                entities={},
                filters={},
                query_plan=[],
            )

        # Classify intent
        intent, confidence = self.classify(query)

        # Extract entities and filters
        entities = self.extract_entities(query, intent)
        filters = self.extract_filters(query, intent)

        # Build query plan
        query_plan = self.build_query_plan(intent, entities, filters)

        # Log routing decision
        is_deterministic = router_config.should_use_deterministic(confidence)
        if router_config.log_routing_decisions:
            logger.info(
                f"Routed query: intent={intent}, confidence={confidence:.2f}, "
                f"strategy={router_config.routing_strategy.value}, "
                f"deterministic={is_deterministic}, entities={entities}"
            )

        return QueryIntent(
            intent=intent,
            confidence=confidence,
            entities=entities,
            filters=filters,
            query_plan=query_plan,
        )
