"""Data endpoints for projects (pure CRUD, no business logic) - Phase 3."""

from __future__ import annotations

from typing import Optional

try:
    from fastapi import APIRouter, HTTPException, Depends
except ModuleNotFoundError:
    APIRouter = None  # type: ignore


def get_data_projects_router(repo=None):
    """
    Create data projects router.
    
    Pure CRUD endpoints for project management:
    - GET /data/projects - List all projects
    - GET /data/projects/{projectId} - Get single project
    - POST /data/projects - Create project
    - PATCH /data/projects/{projectId} - Update project
    - DELETE /data/projects/{projectId} - Delete project
    - GET /data/events/{eventId}/projects - List projects for specific event
    """
    if not APIRouter:
        return None
    
    router = APIRouter(prefix="/data/projects", tags=["data-projects"])
    
    # ===== List All Projects =====
    @router.get("")
    async def list_data_projects(event_id: Optional[str] = None):
        """List all projects, optionally filtered by event."""
        if not repo:
            raise HTTPException(status_code=503, detail="Project repository not initialized")
        
        try:
            if event_id:
                projects = repo.list_by_event(event_id)
            else:
                projects = repo.list_all()
            
            return {
                "value": [p.to_dict() for p in projects],
                "@odata.context": "https://api.internal.microsoft.com/data/$metadata#projects",
                "count": len(projects)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")
    
    # ===== Get Single Project =====
    @router.get("/{project_id}")
    async def get_data_project(project_id: str):
        """Get a single project by ID."""
        if not repo:
            raise HTTPException(status_code=503, detail="Project repository not initialized")
        
        try:
            project = repo.get(project_id)
            if not project:
                raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
            return project.to_dict()
        except Exception as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")
    
    # ===== Create Project =====
    @router.post("")
    async def create_data_project(payload: dict):
        """Create a new project."""
        if not repo:
            raise HTTPException(status_code=503, detail="Project repository not initialized")
        
        try:
            from src.core.event_models import ProjectDefinition
            
            # Validate required fields
            if "id" not in payload:
                raise ValueError("Project 'id' is required")
            if "eventId" not in payload:
                raise ValueError("Project 'eventId' is required")
            
            project = ProjectDefinition.from_dict(payload)
            repo.create(project)
            return {"status": "created", "data": project.to_dict()}, 201
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid project data: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")
    
    # ===== Update Project =====
    @router.patch("/{project_id}")
    async def update_data_project(project_id: str, payload: dict):
        """Update an existing project (partial update)."""
        if not repo:
            raise HTTPException(status_code=503, detail="Project repository not initialized")
        
        try:
            from src.core.event_models import ProjectDefinition
            
            # Get current project
            current = repo.get(project_id)
            if not current:
                raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
            
            # Merge payload with current
            merged = {**current.to_dict(), **payload}
            project = ProjectDefinition.from_dict(merged)
            repo.update(project)
            return project.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")
    
    # ===== Delete Project =====
    @router.delete("/{project_id}")
    async def delete_data_project(project_id: str):
        """Delete a project."""
        if not repo:
            raise HTTPException(status_code=503, detail="Project repository not initialized")
        
        try:
            project = repo.get(project_id)
            if not project:
                raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
            
            repo.delete(project_id)
            return {"status": "deleted", "id": project_id}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")
    
    return router
