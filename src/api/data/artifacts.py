"""Data endpoints for artifacts (pure CRUD, no business logic) - Phase 3."""

from __future__ import annotations

from typing import Optional

try:
    from fastapi import APIRouter, HTTPException
except ModuleNotFoundError:
    APIRouter = None  # type: ignore


def get_data_artifacts_router(repo=None):
    """
    Create data artifacts router.
    
    Pure CRUD endpoints for knowledge artifact management:
    - GET /data/artifacts - List all artifacts
    - GET /data/artifacts/{artifactId} - Get single artifact
    - POST /data/artifacts - Create artifact
    - PATCH /data/artifacts/{artifactId} - Update artifact
    - DELETE /data/artifacts/{artifactId} - Delete artifact
    - GET /data/projects/{projectId}/artifacts - List artifacts for project
    """
    if not APIRouter:
        return None
    
    router = APIRouter(prefix="/data/artifacts", tags=["data-artifacts"])
    
    # ===== List All Artifacts =====
    @router.get("")
    async def list_data_artifacts(project_id: Optional[str] = None):
        """List all artifacts, optionally filtered by project."""
        if not repo:
            raise HTTPException(status_code=503, detail="Artifact repository not initialized")
        
        try:
            if project_id:
                artifacts = repo.list_by_project(project_id)
            else:
                artifacts = repo.list_all()
            
            return {
                "value": [a.to_dict() for a in artifacts],
                "@odata.context": "https://api.internal.microsoft.com/data/$metadata#artifacts",
                "count": len(artifacts)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list artifacts: {str(e)}")
    
    # ===== Get Single Artifact =====
    @router.get("/{artifact_id}")
    async def get_data_artifact(artifact_id: str):
        """Get a single artifact by ID."""
        if not repo:
            raise HTTPException(status_code=503, detail="Artifact repository not initialized")
        
        try:
            artifact = repo.get(artifact_id)
            if not artifact:
                raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found")
            return artifact.to_dict()
        except Exception as e:
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e))
            raise HTTPException(status_code=500, detail=f"Failed to get artifact: {str(e)}")
    
    # ===== Create Artifact =====
    @router.post("")
    async def create_data_artifact(payload: dict):
        """Create a new knowledge artifact."""
        if not repo:
            raise HTTPException(status_code=503, detail="Artifact repository not initialized")
        
        try:
            from src.core.event_models import KnowledgeArtifact
            
            # Validate required fields
            if "id" not in payload:
                raise ValueError("Artifact 'id' is required")
            if "projectId" not in payload:
                raise ValueError("Artifact 'projectId' is required")
            
            artifact = KnowledgeArtifact.from_dict(payload)
            repo.create(artifact)
            return {"status": "created", "data": artifact.to_dict()}, 201
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid artifact data: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create artifact: {str(e)}")
    
    # ===== Update Artifact =====
    @router.patch("/{artifact_id}")
    async def update_data_artifact(artifact_id: str, payload: dict):
        """Update an existing artifact (partial update)."""
        if not repo:
            raise HTTPException(status_code=503, detail="Artifact repository not initialized")
        
        try:
            from src.core.event_models import KnowledgeArtifact
            
            # Get current artifact
            current = repo.get(artifact_id)
            if not current:
                raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found")
            
            # Merge payload with current
            merged = {**current.to_dict(), **payload}
            artifact = KnowledgeArtifact.from_dict(merged)
            repo.update(artifact)
            return artifact.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update artifact: {str(e)}")
    
    # ===== Delete Artifact =====
    @router.delete("/{artifact_id}")
    async def delete_data_artifact(artifact_id: str):
        """Delete an artifact."""
        if not repo:
            raise HTTPException(status_code=503, detail="Artifact repository not initialized")
        
        try:
            artifact = repo.get(artifact_id)
            if not artifact:
                raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found")
            
            repo.delete(artifact_id)
            return {"status": "deleted", "id": artifact_id}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete artifact: {str(e)}")
    
    return router
