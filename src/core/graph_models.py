"""Graph-aligned response wrappers and base entities.

Following Microsoft Graph conventions:
- @odata.type: OData type annotation
- @odata.etag: ETag for optimistic concurrency
- Collections: { "value": [...], "@odata.context": "...", "@odata.nextLink": "..." }
- Errors: { "error": { "code": "...", "message": "..." } }
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from enum import Enum
import json

T = TypeVar("T")


@dataclass
class GraphEntity:
    """Base class for all Graph-aligned entities."""

    id: str
    odata_type: str  # e.g., "#microsoft.graph.event"
    odata_etag: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary with Graph properties."""
        data = asdict(self)
        # Use snake_case keys with @ prefix for Graph properties
        data["@odata.type"] = data.pop("odata_type")
        data["@odata.etag"] = data.pop("odata_etag", None)
        # Convert datetime to ISO format
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        if isinstance(data.get("updated_at"), datetime):
            data["updated_at"] = data["updated_at"].isoformat()
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "GraphEntity":
        """Create from dictionary, handling Graph properties."""
        data_copy = data.copy()
        # Extract Graph properties
        data_copy["odata_type"] = data_copy.pop("@odata.type", None)
        data_copy["odata_etag"] = data_copy.pop("@odata.etag", None)
        # Parse ISO strings to datetime
        if isinstance(data_copy.get("created_at"), str):
            data_copy["created_at"] = datetime.fromisoformat(data_copy["created_at"])
        if isinstance(data_copy.get("updated_at"), str):
            data_copy["updated_at"] = datetime.fromisoformat(data_copy["updated_at"])
        return cls(**{k: v for k, v in data_copy.items() if k in cls.__dataclass_fields__})


@dataclass
class GraphCollectionResponse(Generic[T]):
    """Graph-aligned collection response."""

    value: List[T]
    odata_context: Optional[str] = None
    odata_next_link: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to Graph collection format."""
        result = {
            "value": [
                v.to_dict() if hasattr(v, "to_dict") else v
                for v in self.value
            ]
        }
        if self.odata_context:
            result["@odata.context"] = self.odata_context
        if self.odata_next_link:
            result["@odata.nextLink"] = self.odata_next_link
        return result


@dataclass
class GraphErrorResponse:
    """Graph-aligned error response."""

    code: str
    message: str
    details: Optional[List[dict]] = None
    inner_error: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to Graph error format."""
        error_dict = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            error_dict["details"] = self.details
        if self.inner_error:
            error_dict["innerError"] = self.inner_error
        return {"error": error_dict}


# Enum for common OData types
class ODataType(str, Enum):
    """Common OData type annotations."""

    EVENT = "#microsoft.graph.event"
    SESSION = "#microsoft.graph.session"
    PROJECT = "#microsoft.graph.project"
    KNOWLEDGE_ARTIFACT = "#microsoft.graph.knowledgeArtifact"
    PUBLISHED_KNOWLEDGE = "#microsoft.graph.publishedKnowledge"
    BOOKMARK = "#microsoft.graph.bookmark"
    POSTER = "#microsoft.graph.poster"
