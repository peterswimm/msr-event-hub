"""
Paper Knowledge Extraction Agent

Extracts structured knowledge from research papers.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pdfplumber

from ..core.schemas.base_schema import BaseKnowledgeArtifact, SourceType
from ..core.schemas.paper_schema import (
    PaperKnowledgeArtifact,
    DatasetInfo,
)
from .base_agent import BaseKnowledgeAgent
from ..prompts.paper_prompts import get_paper_prompts


logger = logging.getLogger(__name__)


class PaperAgent(BaseKnowledgeAgent):
    """Agent for extracting knowledge from research papers"""

    def __init__(
        self,
        llm_provider: str = "azure-openai",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ):
        """Initialize PaperAgent

        Args:
            llm_provider: LLM provider (azure-openai, openai, or anthropic)
            model: Model name (uses environment defaults if not provided)
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum tokens for LLM response
        """
        super().__init__(
            source_type=SourceType.PAPER,
            llm_provider=llm_provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info(f"Initialized PaperAgent with provider={llm_provider}, model={model}")

    def get_prompts(self) -> Dict[str, str]:
        """Get paper extraction prompts"""
        return get_paper_prompts()

    def extract_from_source(self, source_input: str) -> str:
        """Extract text from PDF file

        Args:
            source_input: Path to PDF file

        Returns:
            Extracted text from the PDF
        """
        pdf_path = Path(source_input)

        if not pdf_path.exists():
            raise FileNotFoundError(f"Paper not found: {source_input}")

        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"Expected PDF file, got: {pdf_path.suffix}")

        logger.info(f"Extracting text from PDF: {pdf_path}")

        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"PDF has {len(pdf.pages)} pages")

                # Extract metadata
                if pdf.metadata:
                    text += f"Title: {pdf.metadata.get('Title', 'Unknown')}\n"
                    text += f"Author: {pdf.metadata.get('Author', 'Unknown')}\n\n"

                # Extract text from pages, limiting to first 50 pages to avoid token explosion
                max_pages = min(len(pdf.pages), 50)
                for i, page in enumerate(pdf.pages[:max_pages]):
                    text += f"\n--- Page {i+1} ---\n"
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text

                    # Log progress for long documents
                    if (i + 1) % 10 == 0:
                        logger.debug(f"Extracted {i+1} pages from PDF")

            if len(pdf.pages) > 50:
                text += f"\n[Note: PDF has {len(pdf.pages)} pages; extracted first 50]"

            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text

        except Exception as e:
            logger.error(f"Failed to extract PDF: {e}")
            raise

    def parse_extraction_output(self, llm_response: str) -> BaseKnowledgeArtifact:
        """Parse LLM response into PaperKnowledgeArtifact

        Args:
            llm_response: LLM response with JSON extraction

        Returns:
            BaseKnowledgeArtifact with combined base and paper-specific fields
        """
        logger.info("Parsing paper extraction output from LLM")

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
                source_type=SourceType.PAPER,
                title=extraction_data.get("title", "Unknown Paper"),
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
                agent_name="PaperAgent",
            )

            # Extract paper-specific fields
            paper_data = extraction_data.get("paper_specific", {})

            # Parse datasets
            datasets = []
            for dataset_info in paper_data.get("datasets_used", []):
                if isinstance(dataset_info, dict):
                    datasets.append(DatasetInfo(
                        name=dataset_info.get("name", "Unknown"),
                        size=dataset_info.get("size", "Unknown"),
                        availability=dataset_info.get("availability", "unknown"),
                        description=dataset_info.get("description"),
                    ))

            paper_artifact = PaperKnowledgeArtifact(
                publication_venue=paper_data.get("publication_venue"),
                publication_year=paper_data.get("publication_year"),
                peer_reviewed=paper_data.get("peer_reviewed", False),
                related_prior_work=paper_data.get("related_prior_work", []),
                datasets_used=datasets,
                evaluation_benchmarks=paper_data.get("evaluation_benchmarks", []),
                evaluation_metrics=paper_data.get("evaluation_metrics", []),
                baseline_comparisons=paper_data.get("baseline_comparisons"),
                key_quantitative_results=paper_data.get("key_quantitative_results", []),
                statistical_significance=paper_data.get("statistical_significance"),
                reproducibility_notes=paper_data.get("reproducibility_notes"),
                research_maturity_stage=paper_data.get("research_maturity_stage", "exploratory"),
                ethical_considerations_discussed=paper_data.get("ethical_considerations_discussed", False),
            )

            # Store paper-specific data in additional_knowledge
            base_artifact.additional_knowledge.update({
                "paper_specific": {
                    "publication_venue": paper_artifact.publication_venue,
                    "publication_year": paper_artifact.publication_year,
                    "peer_reviewed": paper_artifact.peer_reviewed,
                    "related_prior_work": paper_artifact.related_prior_work,
                    "datasets_used": [
                        {"name": d.name, "size": d.size, "availability": d.availability}
                        for d in paper_artifact.datasets_used
                    ],
                    "evaluation_benchmarks": paper_artifact.evaluation_benchmarks,
                    "evaluation_metrics": paper_artifact.evaluation_metrics,
                    "baseline_comparisons": paper_artifact.baseline_comparisons,
                    "key_quantitative_results": paper_artifact.key_quantitative_results,
                    "statistical_significance": paper_artifact.statistical_significance,
                    "reproducibility_notes": paper_artifact.reproducibility_notes,
                    "research_maturity_stage": paper_artifact.research_maturity_stage,
                    "ethical_considerations_discussed": paper_artifact.ethical_considerations_discussed,
                }
            })

            return base_artifact

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON extraction: {e}")
            raise ValueError(f"Invalid JSON in LLM response: {e}") from e
        except Exception as e:
            logger.error(f"Error parsing extraction output: {e}")
            raise
