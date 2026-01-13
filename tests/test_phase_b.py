"""Tests for Phase B: Graph-aligned models, repositories, and event-scoped API."""

import pytest
from datetime import datetime
from pathlib import Path

from src.core.event_models import Event, Session, EventStatus, SessionType
from src.core.knowledge_models import KnowledgeArtifact, PublishedKnowledge, ApprovalStatus, PKAProvenance
from src.core.event_repository import EventRepository, SessionRepository
from src.core.knowledge_repository import KnowledgeArtifactRepository, PublishedKnowledgeRepository
from src.core.projects.models import ProjectDefinition
from src.core.projects.repository import ProjectRepository
from src.core.graph_models import ODataType


@pytest.fixture
def event_repo(tmp_path):
    return EventRepository(storage_dir=str(tmp_path / "events"))


@pytest.fixture
def session_repo(tmp_path):
    return SessionRepository(storage_dir=str(tmp_path / "sessions"))


@pytest.fixture
def artifact_repo(tmp_path):
    return KnowledgeArtifactRepository(storage_dir=str(tmp_path / "artifacts"))


@pytest.fixture
def published_repo(tmp_path):
    return PublishedKnowledgeRepository(storage_dir=str(tmp_path / "published"))


@pytest.fixture
def project_repo(tmp_path):
    return ProjectRepository(storage_dir=str(tmp_path / "projects"))


def test_event_model_to_dict():
    """Test Event model Graph alignment."""
    event = Event(
        id="evt-1",
        display_name="Test Event",
        description="A test event",
        event_type=EventStatus.PUBLISHED,
        odata_type=ODataType.EVENT.value,
    )
    data = event.to_dict()
    assert data["@odata.type"] == ODataType.EVENT.value
    assert data["displayName"] == "Test Event"
    assert "id" in data


def test_event_repository_crud(event_repo):
    """Test Event CRUD operations."""
    event = Event(
        id="evt-1",
        display_name="Conference",
        odata_type=ODataType.EVENT.value,
    )
    created = event_repo.create(event)
    assert created.id == "evt-1"

    retrieved = event_repo.get("evt-1")
    assert retrieved.display_name == "Conference"

    retrieved.display_name = "Updated Conference"
    updated = event_repo.update(retrieved)
    assert updated.display_name == "Updated Conference"

    event_repo.delete("evt-1")
    assert not event_repo.exists("evt-1")


def test_session_repository_list_by_event(session_repo):
    """Test SessionRepository list_by_event filtering."""
    s1 = Session(id="sess-1", event_id="evt-1", title="Talk 1", odata_type=ODataType.SESSION.value)
    s2 = Session(id="sess-2", event_id="evt-2", title="Talk 2", odata_type=ODataType.SESSION.value)

    session_repo.create(s1)
    session_repo.create(s2)

    evt1_sessions = session_repo.list_by_event("evt-1")
    assert len(evt1_sessions) == 1
    assert evt1_sessions[0].id == "sess-1"


def test_knowledge_artifact_model():
    """Test KnowledgeArtifact model."""
    provenance = PKAProvenance(
        agent_name="paper_agent",
        agent_version="1.0",
        prompt_version="1.0",
        run_date_time=datetime.now(),
    )
    artifact = KnowledgeArtifact(
        id="artifact-1",
        project_id="proj-1",
        title="Research Summary",
        plain_language_overview="A summary",
        primary_claims=[],
        provenance=provenance,
        odata_type=ODataType.KNOWLEDGE_ARTIFACT.value,
    )
    data = artifact.to_dict()
    assert data["@odata.type"] == ODataType.KNOWLEDGE_ARTIFACT.value
    assert data["approvalStatus"] == "draft"


def test_artifact_repository_crud(artifact_repo):
    """Test KnowledgeArtifactRepository CRUD."""
    provenance = PKAProvenance(
        agent_name="paper_agent",
        agent_version="1.0",
        prompt_version="1.0",
        run_date_time=datetime.now(),
    )
    artifact = KnowledgeArtifact(
        id="artifact-1",
        project_id="proj-1",
        title="Research",
        plain_language_overview="Overview",
        primary_claims=[],
        provenance=provenance,
        odata_type=ODataType.KNOWLEDGE_ARTIFACT.value,
    )
    created = artifact_repo.create(artifact)
    assert created.id == "artifact-1"

    retrieved = artifact_repo.get("artifact-1")
    assert retrieved.project_id == "proj-1"

    by_project = artifact_repo.list_by_project("proj-1")
    assert len(by_project) == 1


def test_artifact_repository_list_by_status(artifact_repo):
    """Test filtering artifacts by approval status."""
    provenance = PKAProvenance(
        agent_name="agent",
        agent_version="1.0",
        prompt_version="1.0",
        run_date_time=datetime.now(),
    )
    a1 = KnowledgeArtifact(
        id="a1",
        project_id="p1",
        title="A1",
        plain_language_overview="",
        primary_claims=[],
        provenance=provenance,
        approval_status=ApprovalStatus.DRAFT,
        odata_type=ODataType.KNOWLEDGE_ARTIFACT.value,
    )
    a2 = KnowledgeArtifact(
        id="a2",
        project_id="p1",
        title="A2",
        plain_language_overview="",
        primary_claims=[],
        provenance=provenance,
        approval_status=ApprovalStatus.APPROVED,
        odata_type=ODataType.KNOWLEDGE_ARTIFACT.value,
    )
    artifact_repo.create(a1)
    artifact_repo.create(a2)

    drafts = artifact_repo.list_by_status(ApprovalStatus.DRAFT)
    assert len(drafts) == 1
    assert drafts[0].id == "a1"


def test_project_requires_event_id(project_repo):
    """Test that ProjectDefinition now requires event_id."""
    project = ProjectDefinition(
        id="proj-1",
        event_id="evt-1",  # Required in Phase B
        name="Project",
        description="Test",
        research_area="AI",
        odata_type=ODataType.PROJECT.value,
    )
    created = project_repo.create(project)
    assert created.event_id == "evt-1"

    retrieved = project_repo.get("proj-1")
    assert retrieved.event_id == "evt-1"


def test_project_repository_list_by_event(project_repo):
    """Test ProjectRepository.list_by_event."""
    p1 = ProjectDefinition(id="p1", event_id="evt-1", name="P1", description="", research_area="", odata_type=ODataType.PROJECT.value)
    p2 = ProjectDefinition(id="p2", event_id="evt-2", name="P2", description="", research_area="", odata_type=ODataType.PROJECT.value)

    project_repo.create(p1)
    project_repo.create(p2)

    evt1_projects = project_repo.list_by_event("evt-1")
    assert len(evt1_projects) == 1
    assert evt1_projects[0].id == "p1"


def test_project_knowledge_split():
    """Test that ProjectDefinition has draft_artifacts and published_knowledge (no compiled_knowledge)."""
    project = ProjectDefinition(
        id="p1",
        event_id="evt-1",
        name="Project",
        description="",
        research_area="",
        draft_artifacts=["artifact-1", "artifact-2"],
        published_knowledge="published-1",
        odata_type=ODataType.PROJECT.value,
    )
    data = project.to_dict()
    assert data["draftArtifacts"] == ["artifact-1", "artifact-2"]
    assert data["publishedKnowledge"] == "published-1"
    assert "compiledKnowledge" not in data  # Removed in Phase B


def test_published_knowledge_model():
    """Test PublishedKnowledge for approved attendee-safe content."""
    published = PublishedKnowledge(
        id="pub-1",
        project_id="proj-1",
        title="Published Research",
        content="Approved summary for attendees",
        approved_by="admin-1",
        approved_at=datetime.now(),
        source_artifacts=["artifact-1"],
        odata_type=ODataType.PUBLISHED_KNOWLEDGE.value,
    )
    data = published.to_dict()
    assert data["@odata.type"] == ODataType.PUBLISHED_KNOWLEDGE.value
    assert data["approvedBy"] == "admin-1"


def test_published_knowledge_repository(published_repo):
    """Test PublishedKnowledgeRepository."""
    pub = PublishedKnowledge(
        id="pub-1",
        project_id="proj-1",
        title="Published",
        content="Content",
        approved_by="admin",
        approved_at=datetime.now(),
        odata_type=ODataType.PUBLISHED_KNOWLEDGE.value,
    )
    created = published_repo.create(pub)
    assert created.id == "pub-1"

    by_project = published_repo.list_by_project("proj-1")
    assert len(by_project) == 1
