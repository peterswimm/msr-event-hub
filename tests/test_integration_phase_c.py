"""Integration tests for Phase C: Full application wiring.

Tests the complete application context with all repositories working together.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from main import ApplicationContext
from core.event_models import Event, Session, EventType, EventStatus, SessionType
from projects.models import ProjectDefinition
from core.knowledge_models import KnowledgeArtifact, PKAProvenance, PublishedKnowledge, ApprovalStatus


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def app_context(temp_storage):
    """Create application context with temporary storage."""
    return ApplicationContext(storage_root=temp_storage)


class TestApplicationIntegration:
    """Full integration tests for the application."""

    def test_health_check(self, app_context):
        """Test health check status."""
        health = app_context.get_health_status()
        assert health["status"] == "healthy"
        assert "repositories" in health
        assert health["repositories"]["events"] == "ready"

    def test_event_creation_and_retrieval(self, app_context):
        """Test creating and retrieving events."""
        event = Event(
            id="evt_test_001",
            display_name="Test Event",
            description="A test event",
            event_type=EventType.WORKSHOP,
            status=EventStatus.PLANNING,
            odata_type="#microsoft.graph.event",
        )
        
        # Create
        app_context.event_repo.create(event)
        
        # Retrieve
        retrieved = app_context.event_repo.get("evt_test_001")
        assert retrieved.display_name == "Test Event"
        assert retrieved.event_type == EventType.WORKSHOP

    def test_session_creation_for_event(self, app_context):
        """Test creating sessions within an event."""
        # Create event first
        event = Event(
            id="evt_sessions",
            display_name="Event with Sessions",
            odata_type="#microsoft.graph.event",
        )
        app_context.event_repo.create(event)
        
        # Create session
        session = Session(
            id="sess_001",
            event_id="evt_sessions",
            title="Session 1",
            session_type=SessionType.TALK,
            odata_type="#microsoft.graph.session",
        )
        app_context.session_repo.create(session)
        
        # List by event
        sessions = app_context.session_repo.list_by_event("evt_sessions")
        assert len(sessions) == 1
        assert sessions[0].title == "Session 1"

    def test_event_scoped_projects(self, app_context):
        """Test projects are scoped to events (Phase B)."""
        # Create event
        event = Event(
            id="evt_projects",
            display_name="Event with Projects",
            odata_type="#microsoft.graph.event",
        )
        app_context.event_repo.create(event)
        
        # Create event-scoped project
        project = ProjectDefinition(
            id="proj_scoped",
            event_id="evt_projects",  # Phase B: Required
            name="Scoped Project",
            description="Project in an event",
            research_area="Test",
            odata_type="#microsoft.graph.project",
        )
        app_context.project_repo.create(project)
        
        # List by event
        projects = app_context.project_repo.list_by_event("evt_projects")
        assert len(projects) == 1
        assert projects[0].event_id == "evt_projects"

    def test_knowledge_artifact_workflow(self, app_context):
        """Test draft → approved → published knowledge workflow."""
        # Create project
        project = ProjectDefinition(
            id="proj_ka",
            event_id="evt_ka",
            name="Knowledge Project",
            research_area="Test",
            odata_type="#microsoft.graph.project",
        )
        app_context.project_repo.create(project)
        
        # Create draft artifact
        artifact = KnowledgeArtifact(
            id="artifact_draft",
            project_id="proj_ka",
            title="Draft Knowledge",
            plain_language_overview="A test artifact",
            provenance=PKAProvenance(
                agent_name="TestAgent",
                agent_version="1.0",
                prompt_version="1.0",
                run_date_time=datetime.now(),
            ),
            approval_status=ApprovalStatus.DRAFT,
            odata_type="#microsoft.graph.knowledgeArtifact",
        )
        app_context.artifact_repo.create(artifact)
        
        # Verify draft exists
        draft_artifacts = app_context.artifact_repo.list_by_status(ApprovalStatus.DRAFT)
        assert len(draft_artifacts) == 1
        assert draft_artifacts[0].title == "Draft Knowledge"

    def test_published_knowledge_creation(self, app_context):
        """Test creating published knowledge from approved artifacts."""
        # Create project
        project = ProjectDefinition(
            id="proj_pub",
            event_id="evt_pub",
            name="Publish Project",
            research_area="Test",
            odata_type="#microsoft.graph.project",
        )
        app_context.project_repo.create(project)
        
        # Create published knowledge
        published = PublishedKnowledge(
            id="pub_001",
            project_id="proj_pub",
            artifact_id="artifact_approved",
            title="Published Knowledge",
            content="# Structured Knowledge\n\nApproved for distribution.",
            approved_by="reviewer@example.com",
            approved_at=datetime.now(),
            source_artifacts=["artifact_approved"],
            odata_type="#microsoft.graph.publishedKnowledge",
        )
        app_context.published_repo.create(published)
        
        # Retrieve
        retrieved = app_context.published_repo.get("pub_001")
        assert retrieved.title == "Published Knowledge"
        assert retrieved.approved_by == "reviewer@example.com"

    def test_full_event_workflow(self, app_context):
        """Test complete event → project → knowledge workflow."""
        # 1. Create event
        event = Event(
            id="evt_full",
            display_name="Full Workflow Event",
            odata_type="#microsoft.graph.event",
        )
        app_context.event_repo.create(event)
        
        # 2. Create session in event
        session = Session(
            id="sess_full",
            event_id="evt_full",
            title="Full Session",
            session_type=SessionType.KEYNOTE,
            odata_type="#microsoft.graph.session",
        )
        app_context.session_repo.create(session)
        
        # 3. Create project in event
        project = ProjectDefinition(
            id="proj_full",
            event_id="evt_full",
            name="Full Project",
            research_area="Integration Test",
            odata_type="#microsoft.graph.project",
        )
        app_context.project_repo.create(project)
        
        # 4. Create draft artifact in project
        artifact = KnowledgeArtifact(
            id="artifact_full",
            project_id="proj_full",
            title="Full Knowledge Artifact",
            plain_language_overview="Complete workflow test",
            provenance=PKAProvenance(
                agent_name="IntegrationAgent",
                agent_version="1.0",
                prompt_version="1.0",
                run_date_time=datetime.now(),
            ),
            approval_status=ApprovalStatus.DRAFT,
            odata_type="#microsoft.graph.knowledgeArtifact",
        )
        app_context.artifact_repo.create(artifact)
        
        # 5. Verify relationships
        event_projects = app_context.project_repo.list_by_event("evt_full")
        assert len(event_projects) == 1
        
        event_sessions = app_context.session_repo.list_by_event("evt_full")
        assert len(event_sessions) == 1
        
        project_artifacts = app_context.artifact_repo.list_by_project("proj_full")
        assert len(project_artifacts) == 1
        
        # All data is correctly related
        assert event_projects[0].id == "proj_full"
        assert event_sessions[0].id == "sess_full"
        assert project_artifacts[0].title == "Full Knowledge Artifact"


class TestRepositoryPersistence:
    """Test that repositories properly persist data to JSON."""

    def test_event_persistence(self, app_context):
        """Test events are persisted to disk."""
        event = Event(
            id="evt_persist",
            display_name="Persistent Event",
            odata_type="#microsoft.graph.event",
        )
        app_context.event_repo.create(event)
        
        # Verify file exists
        event_file = app_context.storage_root / "events" / "evt_persist.json"
        assert event_file.exists()
        
        # Verify can read back
        retrieved = app_context.event_repo.get("evt_persist")
        assert retrieved.display_name == "Persistent Event"

    def test_project_persistence(self, app_context):
        """Test projects are persisted to disk."""
        project = ProjectDefinition(
            id="proj_persist",
            event_id="evt_test",
            name="Persistent Project",
            research_area="Test",
            odata_type="#microsoft.graph.project",
        )
        app_context.project_repo.create(project)
        
        # Verify file exists
        project_file = app_context.storage_root / "projects" / "proj_persist.json"
        assert project_file.exists()
        
        # Verify can read back
        retrieved = app_context.project_repo.get("proj_persist")
        assert retrieved.event_id == "evt_test"

    def test_artifact_persistence(self, app_context):
        """Test artifacts are persisted to disk."""
        artifact = KnowledgeArtifact(
            id="artifact_persist",
            project_id="proj_test",
            title="Persistent Artifact",
            plain_language_overview="Test",
            provenance=PKAProvenance(
                agent_name="Test",
                agent_version="1.0",
                prompt_version="1.0",
                run_date_time=datetime.now(),
            ),
            approval_status=ApprovalStatus.DRAFT,
            odata_type="#microsoft.graph.knowledgeArtifact",
        )
        app_context.artifact_repo.create(artifact)
        
        # Verify file exists
        artifact_file = app_context.storage_root / "artifacts" / "artifact_persist.json"
        assert artifact_file.exists()
        
        # Verify can read back
        retrieved = app_context.artifact_repo.get("artifact_persist")
        assert retrieved.title == "Persistent Artifact"
