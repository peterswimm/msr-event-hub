"""Knowledge artifact API routes (Graph-aligned, Phase B)."""

from __future__ import annotations

from typing import Optional

try:
    from fastapi import APIRouter
except ModuleNotFoundError:
    APIRouter = None  # type: ignore

from src.core.knowledge_repository import KnowledgeArtifactRepository, PublishedKnowledgeRepository
from src.core.knowledge_models import KnowledgeArtifact, PublishedKnowledge, ApprovalStatus


def list_artifacts_handler(repo: Optional[KnowledgeArtifactRepository], project_id: str) -> dict:
    """List artifacts for a project."""
    if repo is None:
        return {"value": []}
    artifacts = repo.list_by_project(project_id)
    return {
        "value": [a.to_dict() for a in artifacts],
        "@odata.context": f"https://eventhub.internal.microsoft.com/v1/$metadata#projects('{project_id}')/knowledgeArtifacts",
    }


def get_artifact_handler(repo: KnowledgeArtifactRepository, artifact_id: str) -> dict:
    """Get a single knowledge artifact."""
    artifact = repo.get(artifact_id)
    return artifact.to_dict()


def create_artifact_handler(repo: KnowledgeArtifactRepository, payload: dict) -> dict:
    """Create a new knowledge artifact."""
    artifact = KnowledgeArtifact.from_dict(payload)
    repo.create(artifact)
    return artifact.to_dict()


def approve_artifact_handler(repo: KnowledgeArtifactRepository, artifact_id: str) -> dict:
    """Approve (change status to approved) a knowledge artifact."""
    artifact = repo.get(artifact_id)
    artifact.approval_status = ApprovalStatus.APPROVED
    repo.update(artifact)
    return artifact.to_dict()


def get_published_handler(repo: Optional[PublishedKnowledgeRepository], project_id: str) -> dict:
    """Get published knowledge for a project (attendee-safe)."""
    if repo is None:
        return None
    published = repo.list_by_project(project_id)
    return {
        "value": [p.to_dict() for p in published],
        "@odata.context": f"https://eventhub.internal.microsoft.com/v1/$metadata#projects('{project_id}')/publishedKnowledge",
    }


def publish_knowledge_handler(repo: PublishedKnowledgeRepository, project_id: str, payload: dict) -> dict:
    """Publish approved knowledge for a project."""
    payload["projectId"] = project_id
    knowledge = PublishedKnowledge.from_dict(payload)
    repo.create(knowledge)
    return knowledge.to_dict()


def get_knowledge_router(
    artifact_repo: Optional[KnowledgeArtifactRepository] = None,
    published_repo: Optional[PublishedKnowledgeRepository] = None,
):
    """Create FastAPI router for /v1/events/{eventId}/projects/{projectId}/knowledge endpoints."""
    if APIRouter is None:
        return None
    router = APIRouter(
        prefix="/v1/events/{eventId}/projects/{projectId}/knowledge",
        tags=["Knowledge"],
    )

    @router.get("/artifacts")
    def list_artifacts(eventId: str, projectId: str):
        return list_artifacts_handler(artifact_repo, projectId)

    @router.get("/artifacts/{artifactId}")
    def get_artifact(eventId: str, projectId: str, artifactId: str):
        if artifact_repo is None:
            raise ValueError("KnowledgeArtifactRepository required")
        return get_artifact_handler(artifact_repo, artifactId)

    @router.post("/artifacts")
    def create_artifact(eventId: str, projectId: str, payload: dict):
        if artifact_repo is None:
            raise ValueError("KnowledgeArtifactRepository required")
        payload["projectId"] = projectId
        return create_artifact_handler(artifact_repo, payload)

    @router.patch("/artifacts/{artifactId}/approve")
    def approve_artifact(eventId: str, projectId: str, artifactId: str):
        if artifact_repo is None:
            raise ValueError("KnowledgeArtifactRepository required")
        return approve_artifact_handler(artifact_repo, artifactId)

    @router.get("/published")
    def get_published(eventId: str, projectId: str):
        return get_published_handler(published_repo, projectId)

    @router.put("/published")
    def publish_knowledge(eventId: str, projectId: str, payload: dict):
        if published_repo is None:
            raise ValueError("PublishedKnowledgeRepository required")
        return publish_knowledge_handler(published_repo, projectId, payload)

    return router
