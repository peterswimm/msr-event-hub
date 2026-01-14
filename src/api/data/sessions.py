"""Data endpoints for sessions (pure CRUD, no business logic) - Phase 3."""

from __future__ import annotations

from typing import Optional

try:
    from fastapi import APIRouter, HTTPException
except ModuleNotFoundError:
    APIRouter = None  # type: ignore


def get_data_sessions_router(repo=None):
    """
    Create data sessions router.
    
    Pure CRUD endpoints for session management:
    - GET /data/sessions - List all sessions
    - GET /data/sessions/{sessionId} - Get single session
    - POST /data/sessions - Create session
    - PATCH /data/sessions/{sessionId} - Update session
    - DELETE /data/sessions/{sessionId} - Delete session
    - GET /data/events/{eventId}/sessions - List sessions for event
    """
    if not APIRouter:
        return None
    
    router = APIRouter(prefix="/data/sessions", tags=["data-sessions"])
    
    # ===== List All Sessions =====
    @router.get("")
    async def list_data_sessions(event_id: Optional[str] = None):
        """List all sessions, optionally filtered by event."""
        if not repo:
            raise HTTPException(status_code=503, detail="Session repository not initialized")
        
        try:
            if event_id:
                sessions = repo.list_by_event(event_id)
            else:
                sessions = repo.list_all()
            
            return {
                "value": [s.to_dict() for s in sessions],
                "@odata.context": "https://api.internal.microsoft.com/data/$metadata#sessions",
                "count": len(sessions)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")
    
    # ===== Get Single Session =====
    @router.get("/{session_id}")
    async def get_data_session(session_id: str):
        """Get a single session by ID."""
        if not repo:
            raise HTTPException(status_code=503, detail="Session repository not initialized")
        
        try:
            session = repo.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
            return session.to_dict()
        except Exception as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")
    
    # ===== Create Session =====
    @router.post("")
    async def create_data_session(payload: dict):
        """Create a new session."""
        if not repo:
            raise HTTPException(status_code=503, detail="Session repository not initialized")
        
        try:
            from src.core.event_models import Session
            
            # Validate required fields
            if "id" not in payload:
                raise ValueError("Session 'id' is required")
            if "eventId" not in payload:
                raise ValueError("Session 'eventId' is required")
            
            session = Session.from_dict(payload)
            repo.create(session)
            return {"status": "created", "data": session.to_dict()}, 201
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid session data: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
    
    # ===== Update Session =====
    @router.patch("/{session_id}")
    async def update_data_session(session_id: str, payload: dict):
        """Update an existing session (partial update)."""
        if not repo:
            raise HTTPException(status_code=503, detail="Session repository not initialized")
        
        try:
            from src.core.event_models import Session
            
            # Get current session
            current = repo.get(session_id)
            if not current:
                raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
            
            # Merge payload with current
            merged = {**current.to_dict(), **payload}
            session = Session.from_dict(merged)
            repo.update(session)
            return session.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")
    
    # ===== Delete Session =====
    @router.delete("/{session_id}")
    async def delete_data_session(session_id: str):
        """Delete a session."""
        if not repo:
            raise HTTPException(status_code=503, detail="Session repository not initialized")
        
        try:
            session = repo.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
            
            repo.delete(session_id)
            return {"status": "deleted", "id": session_id}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
    
    return router
