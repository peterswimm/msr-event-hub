"""Repositories for Event and Session entities (Graph-aligned persistence)."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.core.event_models import Event, Session, EventStatus, SessionType
from src.storage.base_repository import BaseRepository
from src.storage.storage_manager import StorageManager
from src.core.projects.exceptions import (
    ProjectNotFoundError,
    RepositoryError,
    StorageError,
)
from src.observability.telemetry import telemetry_decorator


class EventRepository(BaseRepository[Event]):
    """JSON repository for Event persistence."""

    def __init__(
        self,
        storage_dir: str = "data/events",
        storage_manager: Optional[StorageManager] = None,
    ) -> None:
        """Initialize the repository."""
        self.storage_dir = (
            storage_manager.get_events_dir()
            if storage_manager is not None
            else Path(storage_dir)
        )
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(
                "initialization", f"Cannot create storage directory: {str(e)}"
            )

    def _get_event_path(self, event_id: str) -> Path:
        """Get the file path for an event."""
        return self.storage_dir / f"{event_id}.json"

    @telemetry_decorator("create", "event")
    def create(self, event: Event) -> Event:
        """Create a new event."""
        event_path = self._get_event_path(event.id)
        if event_path.exists():
            raise StorageError("create", f"Event {event.id} already exists")
        try:
            data = event.to_dict()
            with open(event_path, "w") as f:
                json.dump(data, f, indent=2)
            return event
        except Exception as e:
            raise StorageError("create", f"Cannot save event: {str(e)}")

    @telemetry_decorator("read", "event")
    def get(self, event_id: str) -> Event:
        """Retrieve an event by ID."""
        event_path = self._get_event_path(event_id)
        if not event_path.exists():
            raise ProjectNotFoundError(event_id)
        try:
            with open(event_path, "r") as f:
                data = json.load(f)
            return Event.from_dict(data)
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("get", f"Cannot load event: {str(e)}")

    @telemetry_decorator("update", "event")
    def update(self, event: Event) -> Event:
        """Update an existing event."""
        event_path = self._get_event_path(event.id)
        if not event_path.exists():
            raise ProjectNotFoundError(event.id)
        try:
            event.updated_at = datetime.now()
            data = event.to_dict()
            with open(event_path, "w") as f:
                json.dump(data, f, indent=2)
            return event
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("update", f"Cannot update event: {str(e)}")

    @telemetry_decorator("delete", "event")
    def delete(self, event_id: str) -> None:
        """Delete an event."""
        event_path = self._get_event_path(event_id)
        if not event_path.exists():
            raise ProjectNotFoundError(event_id)
        try:
            event_path.unlink()
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("delete", f"Cannot delete event: {str(e)}")

    @telemetry_decorator("list", "event")
    def list_all(self) -> List[Event]:
        """List all events in the repository."""
        try:
            events = []
            for event_file in self.storage_dir.glob("*.json"):
                try:
                    with open(event_file, "r") as f:
                        data = json.load(f)
                    events.append(Event.from_dict(data))
                except Exception as e:
                    print(f"Warning: Could not load event from {event_file}: {str(e)}")
            return events
        except Exception as e:
            raise StorageError("list_all", f"Cannot list events: {str(e)}")

    def exists(self, event_id: str) -> bool:
        """Check if an event exists."""
        return self._get_event_path(event_id).exists()

    def count(self) -> int:
        """Count the number of events."""
        return len(list(self.storage_dir.glob("*.json")))

    def clear(self) -> None:
        """Delete all events."""
        try:
            for event_file in self.storage_dir.glob("*.json"):
                event_file.unlink()
        except Exception as e:
            raise StorageError("clear", f"Cannot clear repository: {str(e)}")


class SessionRepository(BaseRepository[Session]):
    """JSON repository for Session persistence (event-scoped)."""

    def __init__(
        self,
        storage_dir: str = "data/sessions",
        storage_manager: Optional[StorageManager] = None,
    ) -> None:
        """Initialize the repository."""
        self.storage_dir = (
            storage_manager.get_sessions_dir()
            if storage_manager is not None
            else Path(storage_dir)
        )
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(
                "initialization", f"Cannot create storage directory: {str(e)}"
            )

    def _get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.storage_dir / f"{session_id}.json"

    @telemetry_decorator("create", "session")
    def create(self, session: Session) -> Session:
        """Create a new session."""
        session_path = self._get_session_path(session.id)
        if session_path.exists():
            raise StorageError("create", f"Session {session.id} already exists")
        try:
            data = session.to_dict()
            with open(session_path, "w") as f:
                json.dump(data, f, indent=2)
            return session
        except Exception as e:
            raise StorageError("create", f"Cannot save session: {str(e)}")

    @telemetry_decorator("read", "session")
    def get(self, session_id: str) -> Session:
        """Retrieve a session by ID."""
        session_path = self._get_session_path(session_id)
        if not session_path.exists():
            raise ProjectNotFoundError(session_id)
        try:
            with open(session_path, "r") as f:
                data = json.load(f)
            return Session.from_dict(data)
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("get", f"Cannot load session: {str(e)}")

    @telemetry_decorator("update", "session")
    def update(self, session: Session) -> Session:
        """Update an existing session."""
        session_path = self._get_session_path(session.id)
        if not session_path.exists():
            raise ProjectNotFoundError(session.id)
        try:
            session.updated_at = datetime.now()
            data = session.to_dict()
            with open(session_path, "w") as f:
                json.dump(data, f, indent=2)
            return session
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("update", f"Cannot update session: {str(e)}")

    @telemetry_decorator("delete", "session")
    def delete(self, session_id: str) -> None:
        """Delete a session."""
        session_path = self._get_session_path(session_id)
        if not session_path.exists():
            raise ProjectNotFoundError(session_id)
        try:
            session_path.unlink()
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("delete", f"Cannot delete session: {str(e)}")

    def list_all(self) -> List[Session]:
        """List all sessions."""
        try:
            sessions = []
            for session_file in self.storage_dir.glob("*.json"):
                try:
                    with open(session_file, "r") as f:
                        data = json.load(f)
                    sessions.append(Session.from_dict(data))
                except Exception as e:
                    print(f"Warning: Could not load session from {session_file}: {str(e)}")
            return sessions
        except Exception as e:
            raise StorageError("list_all", f"Cannot list sessions: {str(e)}")
    @telemetry_decorator("list", "session")    def list_by_event(self, event_id: str) -> List[Session]:
        """List all sessions for a specific event."""
        return [s for s in self.list_all() if s.event_id == event_id]

    def exists(self, session_id: str) -> bool:
        """Check if a session exists."""
        return self._get_session_path(session_id).exists()

    def count(self) -> int:
        """Count the number of sessions."""
        return len(list(self.storage_dir.glob("*.json")))

    def clear(self) -> None:
        """Delete all sessions."""
        try:
            for session_file in self.storage_dir.glob("*.json"):
                session_file.unlink()
        except Exception as e:
            raise StorageError("clear", f"Cannot clear repository: {str(e)}")
