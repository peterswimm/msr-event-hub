"""Event and Session models for Event Hub."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from src.core.graph_models import GraphEntity, ODataType


class EventStatus(str, Enum):
    """Event lifecycle state."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class EventType(str, Enum):
    """Type of event."""
    RESEARCH_SHOWCASE = "researchShowcase"
    TAB = "tab"
    WORKSHOP = "workshop"
    LECTURE_SERIES = "lectureSeries"
    OTHER = "other"


@dataclass
class Event(GraphEntity):
    """Event entity—container for sessions and projects."""

    display_name: str = ""
    description: Optional[str] = None
    event_type: EventType = EventType.RESEARCH_SHOWCASE
    status: EventStatus = EventStatus.DRAFT
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    time_zone: str = "UTC"
    location: Optional[str] = None

    def __post_init__(self):
        if not self.odata_type:
            self.odata_type = ODataType.EVENT.value
        super().__init__(
            id=self.id,
            odata_type=self.odata_type,
            odata_etag=self.odata_etag,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = super().to_dict()
        result.update({
            "displayName": self.display_name,
            "description": self.description,
            "eventType": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "status": self.status.value if isinstance(self.status, EventStatus) else self.status,
            "startDate": self.start_date.isoformat() if self.start_date else None,
            "endDate": self.end_date.isoformat() if self.end_date else None,
            "timeZone": self.time_zone,
            "location": self.location,
        })
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """Create from dictionary."""
        data_copy = data.copy()
        # Map camelCase from API to snake_case
        data_copy["display_name"] = data_copy.pop("displayName", "")
        data_copy["event_type"] = data_copy.pop("eventType", "researchShowcase")
        data_copy["start_date"] = data_copy.pop("startDate", None)
        data_copy["end_date"] = data_copy.pop("endDate", None)
        data_copy["time_zone"] = data_copy.pop("timeZone", "UTC")
        data_copy["odata_type"] = data_copy.pop("@odata.type", ODataType.EVENT.value)
        data_copy["odata_etag"] = data_copy.pop("@odata.etag", "")

        if isinstance(data_copy.get("event_type"), str):
            data_copy["event_type"] = EventType(data_copy["event_type"])
        if isinstance(data_copy.get("status"), str):
            data_copy["status"] = EventStatus(data_copy["status"])

        return cls(**{k: v for k, v in data_copy.items() if k in cls.__dataclass_fields__})


class SessionType(str, Enum):
    """Type of session."""
    TALK = "talk"
    KEYNOTE = "keynote"
    WORKSHOP = "workshop"
    PANEL = "panel"
    LIGHTNING_TALK = "lightningTalk"
    POSTER_SESSION = "posterSession"
    OTHER = "other"


@dataclass
class Session(GraphEntity):
    """Session entity—part of an event."""

    event_id: str = ""
    title: str = ""
    session_type: SessionType = SessionType.TALK
    description: Optional[str] = None
    start_date_time: Optional[datetime] = None
    end_date_time: Optional[datetime] = None
    location: Optional[str] = None

    def __post_init__(self):
        if not self.odata_type:
            self.odata_type = ODataType.SESSION.value

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = super().to_dict()
        result.update({
            "eventId": self.event_id,
            "title": self.title,
            "sessionType": self.session_type.value if isinstance(self.session_type, SessionType) else self.session_type,
            "description": self.description,
            "startDateTime": self.start_date_time.isoformat() if self.start_date_time else None,
            "endDateTime": self.end_date_time.isoformat() if self.end_date_time else None,
            "location": self.location,
        })
        return {k: v for k, v in result.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create from dictionary."""
        data_copy = data.copy()
        data_copy["event_id"] = data_copy.pop("eventId", "")
        data_copy["session_type"] = data_copy.pop("sessionType", "talk")
        data_copy["start_date_time"] = data_copy.pop("startDateTime", None)
        data_copy["end_date_time"] = data_copy.pop("endDateTime", None)
        data_copy["odata_type"] = data_copy.pop("@odata.type", ODataType.SESSION.value)
        data_copy["odata_etag"] = data_copy.pop("@odata.etag", "")

        if isinstance(data_copy.get("session_type"), str):
            data_copy["session_type"] = SessionType(data_copy["session_type"])

        return cls(**{k: v for k, v in data_copy.items() if k in cls.__dataclass_fields__})
