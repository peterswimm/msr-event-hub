"""Data endpoints for events (pure CRUD, no business logic) - Phase 3."""

from __future__ import annotations

from typing import Optional

try:
    from fastapi import APIRouter, HTTPException, Depends
    from fastapi.responses import JSONResponse
except ModuleNotFoundError:
    APIRouter = None  # type: ignore


def get_data_events_router(repo=None):
    """
    Create data events router.
    
    Pure CRUD endpoints for event management:
    - GET /data/events - List all events
    - GET /data/events/{eventId} - Get single event
    - POST /data/events - Create event
    - PATCH /data/events/{eventId} - Update event
    - DELETE /data/events/{eventId} - Delete event
    """
    if not APIRouter:
        return None
    
    router = APIRouter(prefix="/data/events", tags=["data-events"])
    
    # ===== List Events =====
    @router.get("")
    async def list_data_events():
        """List all events with pagination support."""
        if not repo:
            raise HTTPException(status_code=503, detail="Event repository not initialized")
        
        try:
            events = repo.list_all()
            return {
                "value": [e.to_dict() for e in events],
                "@odata.context": "https://api.internal.microsoft.com/data/$metadata#events",
                "count": len(events)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list events: {str(e)}")
    
    # ===== Get Single Event =====
    @router.get("/{event_id}")
    async def get_data_event(event_id: str):
        """Get a single event by ID."""
        if not repo:
            raise HTTPException(status_code=503, detail="Event repository not initialized")
        
        try:
            event = repo.get(event_id)
            if not event:
                raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
            return event.to_dict()
        except Exception as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to get event: {str(e)}")
    
    # ===== Create Event =====
    @router.post("")
    async def create_data_event(payload: dict):
        """Create a new event."""
        if not repo:
            raise HTTPException(status_code=503, detail="Event repository not initialized")
        
        try:
            # Import here to avoid circular imports
            from src.core.event_models import Event
            
            # Validate required fields
            if "id" not in payload:
                raise ValueError("Event 'id' is required")
            
            event = Event.from_dict(payload)
            repo.create(event)
            return {"status": "created", "data": event.to_dict()}, 201
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid event data: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")
    
    # ===== Update Event =====
    @router.patch("/{event_id}")
    async def update_data_event(event_id: str, payload: dict):
        """Update an existing event (partial update)."""
        if not repo:
            raise HTTPException(status_code=503, detail="Event repository not initialized")
        
        try:
            from src.core.event_models import Event
            
            # Get current event
            current = repo.get(event_id)
            if not current:
                raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
            
            # Merge payload with current
            merged = {**current.to_dict(), **payload}
            event = Event.from_dict(merged)
            repo.update(event)
            return event.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update event: {str(e)}")
    
    # ===== Delete Event =====
    @router.delete("/{event_id}")
    async def delete_data_event(event_id: str):
        """Delete an event."""
        if not repo:
            raise HTTPException(status_code=503, detail="Event repository not initialized")
        
        try:
            event = repo.get(event_id)
            if not event:
                raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
            
            repo.delete(event_id)
            return {"status": "deleted", "id": event_id}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete event: {str(e)}")
    
    return router
