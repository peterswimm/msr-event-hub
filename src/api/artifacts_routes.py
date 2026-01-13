"""Artifacts API routes (FastAPI optional)."""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover
    from fastapi import APIRouter
except ModuleNotFoundError:  # pragma: no cover
    APIRouter = None  # type: ignore

from src.core.projects.repository import ProjectRepository


def list_artifacts_handler(repo: Optional[ProjectRepository] = None, project_id: Optional[str] = None):
    if repo is None or project_id is None:
        return {"artifacts": []}

    project = repo.get(project_id)
    compiled = project.compiled_knowledge or {}
    return {
        "project_id": project_id,
        "artifact_count": compiled.get("artifact_count", 0),
        "titles": compiled.get("titles", []),
        "sources": compiled.get("sources", []),
    }


def get_artifacts_router(repo: Optional[ProjectRepository] = None):
    if APIRouter is None:
        return None
    router = APIRouter(prefix="/artifacts", tags=["artifacts"])

    @router.get("/")
    def list_artifacts():
        # Placeholder for future artifact registry
        return {"artifacts": []}

    @router.get("/{project_id}")
    def list_project_artifacts(project_id: str):
        return list_artifacts_handler(repo, project_id)

    return router
