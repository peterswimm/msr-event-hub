"""Event-scoped API routes for Event Hub (Graph-aligned, Phase B)."""

from __future__ import annotations

from typing import Optional

try:
    from fastapi import APIRouter
except ModuleNotFoundError:
    APIRouter = None  # type: ignore

from src.core.event_repository import EventRepository, SessionRepository
from src.core.event_models import Event, Session
from src.core.graph_models import GraphCollectionResponse


def list_events_handler(repo: EventRepository) -> dict:
    """List all events."""
    events = repo.list_all()
    return {
        "value": [e.to_dict() for e in events],
        "@odata.context": "https://eventhub.internal.microsoft.com/v1/$metadata#events",
    }


def get_event_handler(repo: EventRepository, event_id: str) -> dict:
    """Get a single event."""
    event = repo.get(event_id)
    return event.to_dict()


def create_event_handler(repo: EventRepository, payload: dict) -> dict:
    """Create a new event."""
    event = Event.from_dict(payload)
    repo.create(event)
    return event.to_dict()


def update_event_handler(repo: EventRepository, event_id: str, payload: dict) -> dict:
    """Update an existing event."""
    current = repo.get(event_id).to_dict()
    merged = {**current, **payload}
    event = Event.from_dict(merged)
    repo.update(event)
    return event.to_dict()


def delete_event_handler(repo: EventRepository, event_id: str) -> dict:
    """Delete an event."""
    repo.delete(event_id)
    return {"deleted": event_id}


def list_sessions_handler(repo: SessionRepository, event_id: str) -> dict:
    """List all sessions for an event."""
    sessions = repo.list_by_event(event_id)
    return {
        "value": [s.to_dict() for s in sessions],
        "@odata.context": f"https://eventhub.internal.microsoft.com/v1/$metadata#events('{event_id}')/sessions",
    }


def get_session_handler(repo: SessionRepository, session_id: str) -> dict:
    """Get a single session."""
    session = repo.get(session_id)
    return session.to_dict()


def create_session_handler(repo: SessionRepository, event_id: str, payload: dict) -> dict:
    """Create a new session."""
    payload["eventId"] = event_id
    session = Session.from_dict(payload)
    repo.create(session)
    return session.to_dict()


def update_session_handler(repo: SessionRepository, session_id: str, payload: dict) -> dict:
    """Update an existing session."""
    current = repo.get(session_id).to_dict()
    merged = {**current, **payload}
    session = Session.from_dict(merged)
    repo.update(session)
    return session.to_dict()


def delete_session_handler(repo: SessionRepository, session_id: str) -> dict:
    """Delete a session."""
    repo.delete(session_id)
    return {"deleted": session_id}


def get_events_router(repo: Optional[EventRepository] = None):
    """Create FastAPI router for /v1/events endpoints."""
    if APIRouter is None:
        return None
    router = APIRouter(prefix="/v1/events", tags=["Events"])

    @router.get("/")
    def list_events():
        if repo is None:
            raise ValueError("EventRepository required")
        return list_events_handler(repo)

    @router.post("/")
    def create_event(payload: dict):
        if repo is None:
            raise ValueError("EventRepository required")
        return create_event_handler(repo, payload)

    @router.get("/{eventId}")
    def get_event(eventId: str):
        if repo is None:
            raise ValueError("EventRepository required")
        return get_event_handler(repo, eventId)

    @router.patch("/{eventId}")
    def update_event(eventId: str, payload: dict):
        if repo is None:
            raise ValueError("EventRepository required")
        return update_event_handler(repo, eventId, payload)

    @router.delete("/{eventId}")
    def delete_event(eventId: str):
        if repo is None:
            raise ValueError("EventRepository required")
        return delete_event_handler(repo, eventId)

    return router


def get_sessions_router(repo: Optional[SessionRepository] = None):
    """Create FastAPI router for /v1/events/{eventId}/sessions endpoints."""
    if APIRouter is None:
        return None
    router = APIRouter(prefix="/v1/events/{eventId}/sessions", tags=["Sessions"])

    @router.get("/")
    def list_sessions(eventId: str):
        if repo is None:
            raise ValueError("SessionRepository required")
        return list_sessions_handler(repo, eventId)

    @router.post("/")
    def create_session(eventId: str, payload: dict):
        if repo is None:
            raise ValueError("SessionRepository required")
        return create_session_handler(repo, eventId, payload)

    @router.get("/{sessionId}")
    def get_session(sessionId: str):
        if repo is None:
            raise ValueError("SessionRepository required")
        return get_session_handler(repo, sessionId)

    @router.patch("/{sessionId}")
    def update_session(sessionId: str, payload: dict):
        if repo is None:
            raise ValueError("SessionRepository required")
        return update_session_handler(repo, sessionId, payload)

    @router.delete("/{sessionId}")
    def delete_session(sessionId: str):
        if repo is None:
            raise ValueError("SessionRepository required")
        return delete_session_handler(repo, sessionId)

    return router
