"""Event-scoped Projects API routes (Graph-aligned, Phase B).

Handlers are testable without FastAPI; when FastAPI is missing the router
factory returns None, but the pure handler functions remain usable.
"""

from __future__ import annotations

try:  # pragma: no cover - dependency guard
    from fastapi import APIRouter
except ModuleNotFoundError:  # pragma: no cover
    APIRouter = None  # type: ignore

from typing import Any, List

from projects.repository import ProjectRepository
from projects import ProjectDefinition
from compilation.compiler import compile_project_summary


def list_projects_handler(repo: ProjectRepository, event_id: str) -> dict:
    """List all projects for an event."""
    projects = repo.list_by_event(event_id)
    return {
        "value": [p.to_dict() for p in projects],
        "@odata.context": f"https://eventhub.internal.microsoft.com/v1/$metadata#events('{event_id}')/projects",
    }


def get_project_handler(repo: ProjectRepository, project_id: str) -> dict:
    """Get a single project."""
    project = repo.get(project_id)
    return project.to_dict()


def create_project_handler(repo: ProjectRepository, event_id: str, payload: dict) -> dict:
    """Create a new project in an event."""
    payload["eventId"] = event_id
    project = ProjectDefinition.from_dict(payload)
    repo.create(project)
    return project.to_dict()


def update_project_handler(repo: ProjectRepository, project_id: str, payload: dict) -> dict:
    current = repo.get(project_id).to_dict()
    merged = {**current, **payload}
    project = ProjectDefinition.from_dict(merged)
    repo.update(project)
    return project.to_dict()


def delete_project_handler(repo: ProjectRepository, project_id: str) -> dict:
    repo.delete(project_id)
    return {"deleted": project_id}


def _coerce_artifact(payload: Any) -> Any:
    if hasattr(payload, "source_type"):
        return payload
    return type("Artifact", (), {
        "source_type": payload.get("source_type"),
        "title": payload.get("title", ""),
        "primary_claims_capabilities": payload.get("primary_claims_capabilities", []),
        "key_methods_approach": payload.get("key_methods_approach", []),
        "limitations_constraints": payload.get("limitations_constraints", []),
    })()


def compile_project_handler(repo: ProjectRepository, project_id: str, artifacts: List[dict]) -> dict:
    project = repo.get(project_id)
    artifact_objs = [_coerce_artifact(a) for a in artifacts]
    summary = compile_project_summary(project.name, artifact_objs)
    project.compiled_knowledge = summary
    project.status = "compiled"
    repo.update(project)
    return {"project_id": project_id, "status": project.status, "compiled": summary}


def get_projects_router(repo: ProjectRepository):
    """Create FastAPI router for /v1/events/{eventId}/projects endpoints."""
    if APIRouter is None:
        return None
    router = APIRouter(prefix="/v1/events/{eventId}/projects", tags=["projects"])

    @router.get("/")
    def list_projects(eventId: str):
        return list_projects_handler(repo, eventId)

    @router.get("/{projectId}")
    def get_project(eventId: str, projectId: str):
        return get_project_handler(repo, projectId)

    @router.post("/")
    def create_project(eventId: str, payload: dict):
        return create_project_handler(repo, eventId, payload)

    @router.patch("/{projectId}")
    def update_project_route(eventId: str, projectId: str, payload: dict):
        return update_project_handler(repo, projectId, payload)

    @router.delete("/{projectId}")
    def delete_project_route(eventId: str, projectId: str):
        return delete_project_handler(repo, projectId)

    @router.post("/{projectId}/compile")
    def compile_project_route(eventId: str, projectId: str, payload: dict):
        artifacts = payload.get("artifacts", []) if payload else []
        return compile_project_handler(repo, projectId, artifacts)

    return router
