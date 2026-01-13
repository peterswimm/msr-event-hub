"""Search action handlers."""

import logging
from typing import Dict, Any, Tuple, Optional

from src.api.actions.base import BaseActionHandler
from src.api.actions.decorators import register_action
from src.api.actions.helpers import build_project_carousel, apply_filter, format_project_list
from src.storage.event_data import get_event_data

logger = logging.getLogger(__name__)


@register_action(
    "keyword_search",
    description="Full-text search across project names and descriptions",
)
class KeywordSearchHandler(BaseActionHandler):
    """Handler for keyword_search action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute keyword_search action."""
        try:
            keyword = payload.get("keyword", "").lower()
            if not keyword:
                raise ValueError("Keyword parameter is required")

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            filtered = apply_filter(
                all_projects,
                lambda p: (
                    keyword in p.get("description", "").lower()
                    or keyword in p.get("name", "").lower()
                ),
            )

            logger.info(f"Keyword search '{keyword}': found {len(filtered)} projects")

            limit = payload.get("limit", 10)
            card = build_project_carousel(
                filtered,
                title=f"Search Results for '{keyword}'",
                subtitle=f"Showing {min(limit, len(filtered))} of {len(filtered)} results",
                max_items=limit,
            ) if filtered else None

            text = f"Found {len(filtered)} projects for keyword: {keyword}."
            return text, card

        except Exception as e:
            logger.error(f"Error in keyword_search handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        keyword = payload.get("keyword", "")
        if keyword:
            context.add_keyword(keyword)
        context.conversation_stage = "show_results"


@register_action(
    "researcher_search",
    description="Find projects by team member name",
    requires_foundry=True,
)
class ResearcherSearchHandler(BaseActionHandler):
    """Handler for researcher_search action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute researcher_search action."""
        try:
            researcher = payload.get("researcher", "").lower()
            if not researcher:
                raise ValueError("Researcher parameter is required")

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            filtered = apply_filter(
                all_projects,
                lambda p: any(
                    researcher in m.get("name", "").lower()
                    for m in p.get("team", [])
                ),
            )

            logger.info(f"Researcher search '{researcher}': found {len(filtered)} projects")

            limit = payload.get("limit", 10)
            card = build_project_carousel(
                filtered,
                title=f"Research by {researcher}",
                subtitle=f"Showing {min(limit, len(filtered))} of {len(filtered)} projects",
                max_items=limit,
            ) if filtered else None

            text = f"Found {len(filtered)} projects for researcher: {researcher}."
            return text, card

        except Exception as e:
            logger.error(f"Error in researcher_search handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        researcher = payload.get("researcher", "")
        if researcher:
            context.add_researcher(researcher)
        context.conversation_stage = "show_results"
