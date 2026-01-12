"""Knowledge artifact models—PKA (draft) and Published variants."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from core.graph_models import GraphEntity, ODataType


class PKAClaimType(str, Enum):
    """Type of knowledge claim."""
    FACT = "fact"
    RESULT = "result"
    INTERPRETATION = "interpretation"


class ApprovalStatus(str, Enum):
    """Knowledge artifact approval state."""
    DRAFT = "draft"
    PENDING_REVIEW = "pendingReview"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class PKACitation:
    """Citation for a claim in PKA."""
    snapshot_id: str
    locator: str  # e.g., page, line, timestamp
    
    def to_dict(self) -> dict:
        return {
            "snapshotId": self.snapshot_id,
            "locator": self.locator,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PKACitation":
        return cls(
            snapshot_id=data["snapshotId"],
            locator=data["locator"],
        )


@dataclass
class PKABaselineClaim:
    """A single claim in PKA baseline."""
    text: str
    claim_type: PKAClaimType
    citations: List[PKACitation]
    confidence: float  # 0.0-1.0
    
    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "claimType": self.claim_type.value if isinstance(self.claim_type, PKAClaimType) else self.claim_type,
            "citations": [c.to_dict() for c in self.citations],
            "confidence": self.confidence,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PKABaselineClaim":
        return cls(
            text=data["text"],
            claim_type=PKAClaimType(data["claimType"]),
            citations=[PKACitation.from_dict(c) for c in data.get("citations", [])],
            confidence=data["confidence"],
        )


@dataclass
class PKAProvenance:
    """Extraction metadata for PKA."""
    agent_name: str  # e.g., "paper_agent"
    agent_version: str
    prompt_version: str
    run_date_time: datetime
    source_url_or_path: Optional[str] = None
    extraction_model: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "agentName": self.agent_name,
            "agentVersion": self.agent_version,
            "promptVersion": self.prompt_version,
            "runDateTime": self.run_date_time.isoformat(),
            "sourceUrlOrPath": self.source_url_or_path,
            "extractionModel": self.extraction_model,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PKAProvenance":
        return cls(
            agent_name=data["agentName"],
            agent_version=data["agentVersion"],
            prompt_version=data["promptVersion"],
            run_date_time=datetime.fromisoformat(data["runDateTime"]),
            source_url_or_path=data.get("sourceUrlOrPath"),
            extraction_model=data.get("extractionModel"),
        )


@dataclass
class KnowledgeArtifact(GraphEntity):
    """PKA (draft) knowledge artifact from extraction."""

    project_id: str = ""
    title: str = ""
    plain_language_overview: str = ""
    primary_claims: List[PKABaselineClaim] = field(default_factory=list)
    provenance: PKAProvenance = field(default_factory=lambda: PKAProvenance())
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    novelty_vs_prior_work: Optional[str] = None
    key_methods: Optional[str] = None
    potential_impact: Optional[str] = None
    limitations: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    additional_knowledge: Dict[str, Any] = field(default_factory=dict)
    reviewer_notes: Optional[str] = None

    def __post_init__(self):
        if not self.odata_type:
            self.odata_type = ODataType.KNOWLEDGE_ARTIFACT.value

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = super().to_dict()
        result.update({
            "projectId": self.project_id,
            "title": self.title,
            "plainLanguageOverview": self.plain_language_overview,
            "primaryClaims": [c.to_dict() for c in self.primary_claims],
            "provenance": self.provenance.to_dict(),
            "approvalStatus": self.approval_status.value,
            "noveltyVsPriorWork": self.novelty_vs_prior_work,
            "keyMethods": self.key_methods,
            "potentialImpact": self.potential_impact,
            "limitations": self.limitations,
            "openQuestions": self.open_questions,
            "additionalKnowledge": self.additional_knowledge,
            "reviewerNotes": self.reviewer_notes,
        })
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeArtifact":
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy["project_id"] = data_copy.pop("projectId", "")
        data_copy["plain_language_overview"] = data_copy.pop("plainLanguageOverview", "")
        data_copy["primary_claims"] = [PKABaselineClaim.from_dict(c) for c in data_copy.pop("primaryClaims", [])]
        data_copy["provenance"] = PKAProvenance.from_dict(data_copy.pop("provenance", {}))
        data_copy["approval_status"] = ApprovalStatus(data_copy.pop("approvalStatus", "draft"))
        data_copy["novelty_vs_prior_work"] = data_copy.pop("noveltyVsPriorWork", None)
        data_copy["key_methods"] = data_copy.pop("keyMethods", None)
        data_copy["potential_impact"] = data_copy.pop("potentialImpact", None)
        data_copy["open_questions"] = data_copy.pop("openQuestions", [])
        data_copy["additional_knowledge"] = data_copy.pop("additionalKnowledge", {})
        data_copy["reviewer_notes"] = data_copy.pop("reviewerNotes", None)
        data_copy["odata_type"] = data_copy.pop("@odata.type", ODataType.KNOWLEDGE_ARTIFACT.value)
        data_copy["odata_etag"] = data_copy.pop("@odata.etag", "")

        return cls(**{k: v for k, v in data_copy.items() if k in cls.__dataclass_fields__})


@dataclass
class PublishedKnowledge(GraphEntity):
    """Published, human-approved knowledge for a project."""

    project_id: str = ""
    title: str = ""
    content: str = ""  # Markdown or rich text
    approved_by: str = ""  # User ID
    approved_at: datetime = field(default_factory=datetime.now)
    source_artifacts: List[str] = field(default_factory=list)  # IDs of KnowledgeArtifact

    def __post_init__(self):
        if not self.odata_type:
            self.odata_type = ODataType.PUBLISHED_KNOWLEDGE.value

    def to_dict(self) -> dict:
        """Convert to dictionary, ensuring all datetimes are serialized."""
        result = super().to_dict()
        # Ensure approved_at is ISO format
        approved_at_value = self.approved_at.isoformat() if isinstance(self.approved_at, datetime) else self.approved_at
        result.update({
            "projectId": self.project_id,
            "title": self.title,
            "content": self.content,
            "approvedBy": self.approved_by,
            "approvedAt": approved_at_value,
            "sourceArtifacts": self.source_artifacts,
        })
        # Final pass to ensure no datetimes remain
        return {k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "PublishedKnowledge":
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy["project_id"] = data_copy.pop("projectId", "")
        data_copy["approved_by"] = data_copy.pop("approvedBy", "")
        data_copy["approved_at"] = datetime.fromisoformat(data_copy.pop("approvedAt", datetime.now().isoformat()))
        data_copy["source_artifacts"] = data_copy.pop("sourceArtifacts", [])
        data_copy["odata_type"] = data_copy.pop("@odata.type", ODataType.PUBLISHED_KNOWLEDGE.value)
        data_copy["odata_etag"] = data_copy.pop("@odata.etag", "")

        return cls(**{k: v for k, v in data_copy.items() if k in cls.__dataclass_fields__})
