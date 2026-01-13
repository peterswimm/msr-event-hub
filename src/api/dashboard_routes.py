"""Dashboard API routes (FastAPI optional)."""

from __future__ import annotations

from typing import Optional

try:  # pragma: no cover
    from fastapi import APIRouter
except ModuleNotFoundError:  # pragma: no cover
    APIRouter = None  # type: ignore

from src.core.projects.repository import ProjectRepository


def get_dashboard_metrics(repo: Optional[ProjectRepository] = None) -> dict:
    if repo is None:
        return {"projects": 0, "compiled": 0, "iterating": 0, "failed": 0}

    projects = repo.list_all()
    return {
        "projects": len(projects),
        "compiled": sum(1 for p in projects if p.status == "compiled"),
        "iterating": sum(1 for p in projects if p.status == "iterating"),
        "failed": sum(1 for p in projects if p.status == "failed"),
    }


def get_dashboard_router(repo: Optional[ProjectRepository] = None):
    if APIRouter is None:
        return None
    router = APIRouter(prefix="/dashboard", tags=["dashboard"])

    @router.get("/health")
    def health():
        return {"status": "ok"}

    @router.get("/metrics")
    def metrics():
        return get_dashboard_metrics(repo)

    return router
