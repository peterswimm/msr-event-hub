"""Project data models for knowledge artifact management.

Refactored to align with OpenAPI spec: projects are event-scoped,
knowledge split into draft (PKA) and published variants.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum
import json

from src.core.graph_models import GraphEntity, ODataType


class SourceType(str, Enum):
    """Types of knowledge sources."""
    PAPER = "paper"
    TALK = "talk"
    REPOSITORY = "repository"


class ResearchMaturityStage(str, Enum):
    """Research maturity progression stages."""
    EXPLORATORY = "exploratory"  # Early-stage research
    VALIDATED = "validated"  # Research validated with evidence
    DEPLOYED = "deployed"  # Research in production use


@dataclass
class PaperReference:
    """Reference to an academic paper source."""
    id: str
    title: str
    authors: list[str]
    publication_venue: str
    publication_year: int
    doi_or_url: str
    abstract: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "publication_venue": self.publication_venue,
            "publication_year": self.publication_year,
            "doi_or_url": self.doi_or_url,
            "abstract": self.abstract,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PaperReference":
        return cls(
            id=data["id"],
            title=data["title"],
            authors=data["authors"],
            publication_venue=data["publication_venue"],
            publication_year=data["publication_year"],
            doi_or_url=data["doi_or_url"],
            abstract=data.get("abstract"),
        )


@dataclass
class TalkReference:
    """Reference to a talk/presentation source."""
    id: str
    title: str
    speaker: str
    event_name: str
    event_date: str  # ISO format date
    video_url: Optional[str] = None
    slides_url: Optional[str] = None
    summary: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "speaker": self.speaker,
            "event_name": self.event_name,
            "event_date": self.event_date,
            "video_url": self.video_url,
            "slides_url": self.slides_url,
            "summary": self.summary,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TalkReference":
        return cls(
            id=data["id"],
            title=data["title"],
            speaker=data["speaker"],
            event_name=data["event_name"],
            event_date=data["event_date"],
            video_url=data.get("video_url"),
            slides_url=data.get("slides_url"),
            summary=data.get("summary"),
        )


@dataclass
class RepositoryReference:
    """Reference to a code repository source."""
    id: str
    name: str
    url: str
    language: str
    description: Optional[str] = None
    stars: Optional[int] = None
    last_updated: Optional[str] = None  # ISO format date
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "language": self.language,
            "description": self.description,
            "stars": self.stars,
            "last_updated": self.last_updated,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "RepositoryReference":
        return cls(
            id=data["id"],
            name=data["name"],
            url=data["url"],
            language=data["language"],
            description=data.get("description"),
            stars=data.get("stars"),
            last_updated=data.get("last_updated"),
        )


@dataclass
class ExecutionConfig:
    """Configuration for how agents execute on a project."""
    extraction_agent_type: str = "paper"
    max_iterations: int = 2
    quality_threshold: float = 3.0
    parallelization: bool = True
    timeout_seconds: int = 300
    
    def to_dict(self) -> dict:
        return {
            "extraction_agent_type": self.extraction_agent_type,
            "max_iterations": self.max_iterations,
            "quality_threshold": self.quality_threshold,
            "parallelization": self.parallelization,
            "timeout_seconds": self.timeout_seconds,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionConfig":
        return cls(
            extraction_agent_type=data.get("extraction_agent_type", "paper"),
            max_iterations=data.get("max_iterations", 2),
            quality_threshold=data.get("quality_threshold", 3.0),
            parallelization=data.get("parallelization", True),
            timeout_seconds=data.get("timeout_seconds", 300),
        )


@dataclass
class QualityMetrics:
    """Quality metrics aggregated across all artifacts in a project."""
    total_artifacts: int = 0
    artifacts_reviewed: int = 0
    average_confidence: float = 0.0
    average_coverage: float = 0.0
    last_updated: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "total_artifacts": self.total_artifacts,
            "artifacts_reviewed": self.artifacts_reviewed,
            "average_confidence": self.average_confidence,
            "average_coverage": self.average_coverage,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "QualityMetrics":
        last_updated = None
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"])
        return cls(
            total_artifacts=data.get("total_artifacts", 0),
            artifacts_reviewed=data.get("artifacts_reviewed", 0),
            average_confidence=data.get("average_confidence", 0.0),
            average_coverage=data.get("average_coverage", 0.0),
            last_updated=last_updated,
        )


@dataclass
class ProjectDefinition(GraphEntity):
    """Complete project definition—now event-scoped with split knowledge.
    
    Breaking change: projects now require event_id and belong to an event.
    Knowledge split: draft_artifacts (extraction) vs published_knowledge (approved).
    """
    event_id: str = ""  # NEW: projects are scoped to events
    name: str = ""
    description: str = ""
    research_area: str = ""
    papers: list[PaperReference] = field(default_factory=list)
    talks: list[TalkReference] = field(default_factory=list)
    repositories: list[RepositoryReference] = field(default_factory=list)
    objectives: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    maturity_stage: ResearchMaturityStage = ResearchMaturityStage.EXPLORATORY
    status: str = "created"
    execution_config: ExecutionConfig = field(default_factory=ExecutionConfig)
    quality_metrics: QualityMetrics = field(default_factory=QualityMetrics)
    draft_artifacts: list[str] = field(default_factory=list)  # KnowledgeArtifact IDs
    published_knowledge: Optional[str] = None  # PublishedKnowledge ID

    def __post_init__(self):
        if not self.odata_type:
            self.odata_type = ODataType.PROJECT.value

    def artifact_count(self) -> int:
        """Get total count of artifacts in this project."""
        return len(self.papers) + len(self.talks) + len(self.repositories)
    
    def add_paper(self, paper: PaperReference) -> None:
        """Add a paper reference to the project."""
        if any(p.id == paper.id for p in self.papers):
            raise ValueError(f"Paper with id {paper.id} already exists")
        self.papers.append(paper)
        self.updated_at = datetime.now()
    
    def add_talk(self, talk: TalkReference) -> None:
        """Add a talk reference to the project."""
        if any(t.id == talk.id for t in self.talks):
            raise ValueError(f"Talk with id {talk.id} already exists")
        self.talks.append(talk)
        self.updated_at = datetime.now()
    
    def add_repository(self, repo: RepositoryReference) -> None:
        """Add a repository reference to the project."""
        if any(r.id == repo.id for r in self.repositories):
            raise ValueError(f"Repository with id {repo.id} already exists")
        self.repositories.append(repo)
        self.updated_at = datetime.now()
    
    def remove_paper(self, paper_id: str) -> None:
        """Remove a paper reference by id."""
        self.papers = [p for p in self.papers if p.id != paper_id]
        self.updated_at = datetime.now()
    
    def remove_talk(self, talk_id: str) -> None:
        """Remove a talk reference by id."""
        self.talks = [t for t in self.talks if t.id != talk_id]
        self.updated_at = datetime.now()
    
    def remove_repository(self, repo_id: str) -> None:
        """Remove a repository reference by id."""
        self.repositories = [r for r in self.repositories if r.id != repo_id]
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = super().to_dict()
        result.update({
            "eventId": self.event_id,
            "name": self.name,
            "description": self.description,
            "research_area": self.research_area,
            "papers": [p.to_dict() for p in self.papers],
            "talks": [t.to_dict() for t in self.talks],
            "repositories": [r.to_dict() for r in self.repositories],
            "objectives": self.objectives,
            "keywords": self.keywords,
            "maturity_stage": self.maturity_stage.value,
            "status": self.status,
            "execution_config": self.execution_config.to_dict(),
            "quality_metrics": self.quality_metrics.to_dict(),
            "draftArtifacts": self.draft_artifacts,
            "publishedKnowledge": self.published_knowledge,
        })
        return {k: v for k, v in result.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: dict) -> "ProjectDefinition":
        """Create from dictionary for deserialization."""
        papers = [PaperReference.from_dict(p) for p in data.get("papers", [])]
        talks = [TalkReference.from_dict(t) for t in data.get("talks", [])]
        repositories = [RepositoryReference.from_dict(r) for r in data.get("repositories", [])]
        
        maturity_stage = ResearchMaturityStage(data.get("maturity_stage", "exploratory"))
        execution_config = ExecutionConfig.from_dict(data.get("execution_config", {}))
        quality_metrics = QualityMetrics.from_dict(data.get("quality_metrics", {}))
        
        created_at = datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now()
        updated_at = datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        
        return cls(
            id=data["id"],
            event_id=data.get("event_id") or data.get("eventId", ""),
            name=data["name"],
            description=data["description"],
            research_area=data["research_area"],
            papers=papers,
            talks=talks,
            repositories=repositories,
            objectives=data.get("objectives", []),
            keywords=data.get("keywords", []),
            maturity_stage=maturity_stage,
            created_at=created_at,
            updated_at=updated_at,
            status=data.get("status", "created"),
            execution_config=execution_config,
            quality_metrics=quality_metrics,
            odata_type=data.get("@odata.type", ODataType.PROJECT.value),
            odata_etag=data.get("@odata.etag"),
            draft_artifacts=data.get("draft_artifacts", []) or data.get("draftArtifacts", []),
            published_knowledge=data.get("published_knowledge") or data.get("publishedKnowledge"),
        )
