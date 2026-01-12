"""
Talk Knowledge Extraction Agent

Extracts structured knowledge from research talk transcripts.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from ..core.schemas.base_schema import BaseKnowledgeArtifact, SourceType
from ..core.schemas.talk_schema import (
    TalkKnowledgeArtifact,
    TalkSection,
)
from .base_agent import BaseKnowledgeAgent
from ..prompts.talk_prompts import get_talk_prompts


logger = logging.getLogger(__name__)


class TalkAgent(BaseKnowledgeAgent):
    """Agent for extracting knowledge from research talks and transcripts"""

    def __init__(
        self,
        llm_provider: str = "azure-openai",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ):
        """Initialize TalkAgent

        Args:
            llm_provider: LLM provider (azure-openai, openai, or anthropic)
            model: Model name (uses environment defaults if not provided)
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum tokens for LLM response
        """
        super().__init__(
            source_type=SourceType.TALK,
            llm_provider=llm_provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info(f"Initialized TalkAgent with provider={llm_provider}, model={model}")

    def get_prompts(self) -> Dict[str, str]:
        """Get talk extraction prompts"""
        return get_talk_prompts()

    def extract_from_source(self, source_input: str) -> str:
        """Extract text from transcript file or raw text

        Args:
            source_input: Either path to transcript file or raw transcript text

        Returns:
            Extracted transcript text
        """
        # Check if input is a file path
        source_path = Path(source_input)

        if source_path.exists() and source_path.is_file():
            logger.info(f"Reading transcript from file: {source_path}")

            try:
                # Support common transcript formats
                if source_path.suffix.lower() == '.txt':
                    with open(source_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                elif source_path.suffix.lower() in ['.md', '.markdown']:
                    with open(source_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                elif source_path.suffix.lower() == '.json':
                    # Assume JSON has "transcript" or "text" field
                    with open(source_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            text = data.get('transcript') or data.get('text') or json.dumps(data)
                        else:
                            text = json.dumps(data)
                else:
                    # Try reading as text
                    with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
                        text = f.read()

                logger.info(f"Successfully read transcript: {len(text)} characters")
                return text

            except Exception as e:
                logger.error(f"Failed to read transcript file: {e}")
                raise
        else:
            # Assume input is raw transcript text
            logger.info("Using input as raw transcript text")
            if len(source_input) < 50:
                logger.warning("Transcript seems very short, may be a file path that doesn't exist")
            return source_input

    def parse_extraction_output(self, llm_response: str) -> BaseKnowledgeArtifact:
        """Parse LLM response into TalkKnowledgeArtifact

        Args:
            llm_response: LLM response with JSON extraction

        Returns:
            BaseKnowledgeArtifact with combined base and talk-specific fields
        """
        logger.info("Parsing talk extraction output from LLM")

        try:
            # Extract JSON from response
            response_text = llm_response.strip()

            # Try to find JSON block in response
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end == -1:
                    end = len(response_text)
                json_text = response_text[start:end]
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end == -1:
                    end = len(response_text)
                json_text = response_text[start:end]
            else:
                json_text = response_text

            extraction_data = json.loads(json_text.strip())
            logger.info(f"Successfully parsed JSON extraction: {extraction_data.get('title', 'Unknown')}")

            # Extract base fields
            base_artifact = BaseKnowledgeArtifact(
                source_type=SourceType.TALK,
                title=extraction_data.get("title", "Unknown Talk"),
                contributors=extraction_data.get("contributors", []),
                plain_language_overview=extraction_data.get("plain_language_overview", ""),
                technical_problem_addressed=extraction_data.get("technical_problem_addressed", ""),
                key_methods_approach=extraction_data.get("key_methods_approach", ""),
                primary_claims_capabilities=extraction_data.get("primary_claims_capabilities", []),
                novelty_vs_prior_work=extraction_data.get("novelty_vs_prior_work", ""),
                limitations_constraints=extraction_data.get("limitations_constraints", []),
                potential_impact=extraction_data.get("potential_impact", ""),
                open_questions_future_work=extraction_data.get("open_questions_future_work", []),
                key_evidence_citations=extraction_data.get("key_evidence_citations", []),
                confidence_score=float(extraction_data.get("confidence_score", 0.5)),
                confidence_reasoning=extraction_data.get("confidence_reasoning", ""),
                agent_name="TalkAgent",
            )

            # Extract talk-specific fields
            talk_data = extraction_data.get("talk_specific", {})

            # Parse section breakdown
            sections = []
            for section_info in talk_data.get("section_breakdown", []):
                if isinstance(section_info, dict):
                    sections.append(TalkSection(
                        title=section_info.get("title", "Untitled"),
                        start_minute=section_info.get("start_min", 0),
                        duration_minutes=section_info.get("duration_min", 0),
                        description=section_info.get("description"),
                    ))

            talk_artifact = TalkKnowledgeArtifact(
                talk_type=talk_data.get("talk_type", "research_update"),
                duration_minutes=talk_data.get("duration_minutes"),
                section_breakdown=sections,
                demo_included=talk_data.get("demo_included", False),
                demo_description=talk_data.get("demo_description"),
                demo_type=talk_data.get("demo_type"),
                experimental_results_discussed=talk_data.get("experimental_results_discussed", False),
                technical_challenges_mentioned=talk_data.get("technical_challenges_mentioned", []),
                risks_discussed=talk_data.get("risks_discussed", []),
                pending_experiments=talk_data.get("pending_experiments", []),
                collaboration_requests=talk_data.get("collaboration_requests"),
                intended_audience=talk_data.get("intended_audience", "technical"),
                technical_depth_level=talk_data.get("technical_depth_level", "intermediate"),
                assumed_background=talk_data.get("assumed_background"),
                off_script_insights=talk_data.get("off_script_insights"),
                implicit_assumptions=talk_data.get("implicit_assumptions", []),
                audience_qa_signals=talk_data.get("audience_qa_signals"),
                strategic_hints=talk_data.get("strategic_hints"),
            )

            # Store talk-specific data in additional_knowledge
            base_artifact.additional_knowledge.update({
                "talk_specific": {
                    "talk_type": talk_artifact.talk_type,
                    "duration_minutes": talk_artifact.duration_minutes,
                    "demo_included": talk_artifact.demo_included,
                    "demo_description": talk_artifact.demo_description,
                    "demo_type": talk_artifact.demo_type,
                    "experimental_results_discussed": talk_artifact.experimental_results_discussed,
                    "technical_challenges_mentioned": talk_artifact.technical_challenges_mentioned,
                    "risks_discussed": talk_artifact.risks_discussed,
                    "intended_audience": talk_artifact.intended_audience,
                    "technical_depth_level": talk_artifact.technical_depth_level,
                    "assumed_background": talk_artifact.assumed_background,
                    "off_script_insights": talk_artifact.off_script_insights,
                    "implicit_assumptions": talk_artifact.implicit_assumptions,
                    "audience_qa_signals": talk_artifact.audience_qa_signals,
                    "strategic_hints": talk_artifact.strategic_hints,
                }
            })

            return base_artifact

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON extraction: {e}")
            raise ValueError(f"Invalid JSON in LLM response: {e}") from e
        except Exception as e:
            logger.error(f"Error parsing extraction output: {e}")
            raise
