"""
Base Knowledge Schema - Common structure for all artifact types

All knowledge extraction agents produce outputs following this baseline schema,
with optional datatype-specific extensions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class SourceType(str, Enum):
    """Source artifact type"""
    PAPER = "paper"
    TALK = "talk"
    REPOSITORY = "repository"


class ResearchMaturityStage(str, Enum):
    """Research maturity stage"""
    EXPLORATORY = "exploratory"
    VALIDATED = "validated"
    DEPLOYED = "deployed"


@dataclass
class BaseKnowledgeArtifact:
    """
    Common baseline knowledge schema for all research artifacts.

    Produced by all knowledge extraction agents (paper, talk, repository).
    Each agent appends datatype-specific schema + flexible "additional" section.
    """

    # Core Identity
    title: str
    """Primary title or name of the research artifact"""

    contributors: List[str]
    """Authors, speakers, or primary contributors"""

    source_type: SourceType
    """Type of source artifact: paper, talk, or repository"""

    # High-Level Understanding
    plain_language_overview: str
    """Concise, non-technical summary accessible to general audience"""

    technical_problem_addressed: str
    """The specific technical or research problem being solved"""

    # Methods & Approach
    key_methods_approach: str
    """Core methodology, techniques, or architectural approach"""

    primary_claims_capabilities: List[str]
    """Main claims or capabilities presented/demonstrated"""

    # Positioning
    novelty_vs_prior_work: str
    """What is novel or different compared to existing work"""

    limitations_constraints: List[str]
    """Known limitations, constraints, or acknowledged weaknesses"""

    # Impact & Vision
    potential_impact: str
    """Potential impact on the field, downstream applications, or societal benefit"""

    open_questions_future_work: List[str]
    """Unresolved questions or suggested future research directions"""

    # Evidence & Citations
    key_evidence_citations: List[str]
    """Key evidence, citations, or references supporting claims"""

    # Quality Assessment
    confidence_score: float
    """Extraction confidence (0.0-1.0) - human assessor input"""

    confidence_reasoning: Optional[str] = None
    """Why this confidence score was assigned"""

    # Provenance
    provenance: Dict[str, Any] = field(default_factory=dict)
    """
    Source information:
    - agent_name: which extraction agent produced this
    - source_type: paper/talk/repository
    - extraction_date: when this was extracted
    - extraction_model: which LLM was used
    - source_url_or_path: reference to original source
    """

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    """When this artifact was created"""

    updated_at: Optional[datetime] = None
    """When this artifact was last updated"""

    # Additional/Found Knowledge (Flexible)
    additional_knowledge: Dict[str, Any] = field(default_factory=dict)
    """
    Flexible container for unanticipated insights not captured in structured fields.
    Examples:
    - Emergent implications
    - Cross-domain connections
    - Implicit assumptions discovered
    - Strategic hints or roadmap signals
    """

    last_reviewed_at: Optional[datetime] = None
    """When this was last human-reviewed"""

    # Flexible Extension
    additional_knowledge: Dict[str, Any] = field(default_factory=dict)
    """
    Datatype-specific and unanticipated findings:
    - Paper: evaluation_metrics, reproducibility_notes, ethical_considerations
    - Talk: demo_description, audience_questions, implicit_assumptions
    - Repository: undocumented_features, performance_characteristics, community_patterns
    """

    # Review Metadata
    review_status: Optional[str] = None
    """Review status: draft, under_review, approved, needs_revision"""

    reviewer_notes: Optional[str] = None
    """Human reviewer feedback and assessment notes"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "title": self.title,
            "contributors": self.contributors,
            "source_type": self.source_type.value,
            "plain_language_overview": self.plain_language_overview,
            "technical_problem_addressed": self.technical_problem_addressed,
            "key_methods_approach": self.key_methods_approach,
            "primary_claims_capabilities": self.primary_claims_capabilities,
            "novelty_vs_prior_work": self.novelty_vs_prior_work,
            "limitations_constraints": self.limitations_constraints,
            "potential_impact": self.potential_impact,
            "open_questions_future_work": self.open_questions_future_work,
            "key_evidence_citations": self.key_evidence_citations,
            "confidence_score": self.confidence_score,
            "confidence_reasoning": self.confidence_reasoning,
            "provenance": self.provenance,
            "created_at": self.created_at.isoformat(),
            "last_reviewed_at": self.last_reviewed_at.isoformat() if self.last_reviewed_at else None,
            "additional_knowledge": self.additional_knowledge,
            "review_status": self.review_status,
            "reviewer_notes": self.reviewer_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseKnowledgeArtifact":
        """Create from dictionary (e.g., from JSON deserialization)"""
        data_copy = data.copy()

        # Convert string enums
        if isinstance(data_copy.get("source_type"), str):
            data_copy["source_type"] = SourceType(data_copy["source_type"])

        # Convert ISO timestamp strings to datetime
        if isinstance(data_copy.get("created_at"), str):
            data_copy["created_at"] = datetime.fromisoformat(data_copy["created_at"])
        if isinstance(data_copy.get("last_reviewed_at"), str):
            data_copy["last_reviewed_at"] = datetime.fromisoformat(data_copy["last_reviewed_at"])

        return cls(**data_copy)


# Datatype-specific schemas will extend BaseKnowledgeArtifact with additional fields
