"""Integration tests for Phase E1: Database Layer.

Tests cover:
- CRUD operations for all entities
- Transaction management
- Relationship integrity
- Database health checks
- Concurrent access patterns
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from infra.database import DatabaseEngine, DatabaseConfig, get_db
from infra.models import Base, ExecutionStatusEnum
from repositories.sqlalchemy_repositories import (
    EventRepository, SessionRepository, ProjectRepository,
    KnowledgeArtifactRepository, PublishedKnowledgeRepository,
    EvaluationExecutionRepository
)
from core_interfaces import (
    Event, Session as SessionInterface, Project, KnowledgeArtifact,
    PublishedKnowledge, EvaluationExecution
)


# Test database configuration (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_db():
    """Create test database and initialize schema."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def event_repo(test_db):
    """Create EventRepository instance."""
    return EventRepository(test_db)


@pytest.fixture
def session_repo(test_db):
    """Create SessionRepository instance."""
    return SessionRepository(test_db)


@pytest.fixture
def project_repo(test_db):
    """Create ProjectRepository instance."""
    return ProjectRepository(test_db)


@pytest.fixture
def artifact_repo(test_db):
    """Create KnowledgeArtifactRepository instance."""
    return KnowledgeArtifactRepository(test_db)


@pytest.fixture
def published_repo(test_db):
    """Create PublishedKnowledgeRepository instance."""
    return PublishedKnowledgeRepository(test_db)


@pytest.fixture
def execution_repo(test_db):
    """Create EvaluationExecutionRepository instance."""
    return EvaluationExecutionRepository(test_db)


class TestEventRepository:
    """Tests for EventRepository."""
    
    def test_create_event(self, event_repo, test_db):
        """Test creating an event."""
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            description="Test event description",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        created = event_repo.create(event)
        test_db.commit()
        
        assert created.id == event.id
        assert created.display_name == "Test Event"
        assert created.description == "Test event description"
    
    def test_get_event(self, event_repo, test_db):
        """Test retrieving an event."""
        event_id = str(uuid.uuid4())
        event = Event(
            id=event_id,
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        event_repo.create(event)
        test_db.commit()
        
        retrieved = event_repo.get(event_id)
        assert retrieved is not None
        assert retrieved.id == event_id
        assert retrieved.display_name == "Test Event"
    
    def test_get_nonexistent_event(self, event_repo):
        """Test retrieving nonexistent event returns None."""
        result = event_repo.get("nonexistent-id")
        assert result is None
    
    def test_get_all_events(self, event_repo, test_db):
        """Test retrieving all events."""
        events = [
            Event(
                id=str(uuid.uuid4()),
                display_name=f"Event {i}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            for i in range(3)
        ]
        
        for event in events:
            event_repo.create(event)
        test_db.commit()
        
        all_events = event_repo.get_all()
        assert len(all_events) == 3
    
    def test_update_event(self, event_repo, test_db):
        """Test updating an event."""
        event_id = str(uuid.uuid4())
        event = Event(
            id=event_id,
            display_name="Original Name",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        event_repo.create(event)
        test_db.commit()
        
        # Update event
        event.display_name = "Updated Name"
        updated = event_repo.update(event)
        test_db.commit()
        
        retrieved = event_repo.get(event_id)
        assert retrieved.display_name == "Updated Name"
    
    def test_delete_event(self, event_repo, test_db):
        """Test deleting an event."""
        event_id = str(uuid.uuid4())
        event = Event(
            id=event_id,
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        event_repo.create(event)
        test_db.commit()
        
        event_repo.delete(event_id)
        test_db.commit()
        
        retrieved = event_repo.get(event_id)
        assert retrieved is None


class TestProjectRepository:
    """Tests for ProjectRepository."""
    
    def test_create_project(self, event_repo, project_repo, test_db):
        """Test creating a project."""
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        project = Project(
            id="test-project",
            event_id=event.id,
            name="Test Project",
            description="Test project description",
            artifacts_count=0,
            status="pending",
            metadata={"key": "value"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        created = project_repo.create(project)
        test_db.commit()
        
        assert created.id == "test-project"
        assert created.name == "Test Project"
        assert created.event_id == event.id
    
    def test_get_project(self, event_repo, project_repo, test_db):
        """Test retrieving a project."""
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        project = Project(
            id="test-project",
            event_id=event.id,
            name="Test Project",
            description="",
            artifacts_count=0,
            status="pending",
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        project_repo.create(project)
        test_db.commit()
        
        retrieved = project_repo.get("test-project")
        assert retrieved is not None
        assert retrieved.id == "test-project"
    
    def test_get_projects_by_event(self, event_repo, project_repo, test_db):
        """Test retrieving projects by event."""
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        for i in range(3):
            project = Project(
                id=f"project-{i}",
                event_id=event.id,
                name=f"Project {i}",
                description="",
                artifacts_count=0,
                status="pending",
                metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            project_repo.create(project)
        test_db.commit()
        
        projects = project_repo.get_by_event(event.id)
        assert len(projects) == 3
    
    def test_get_projects_by_status(self, event_repo, project_repo, test_db):
        """Test retrieving projects by status."""
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        # Create projects with different statuses
        for status in ["pending", "in_progress", "completed"]:
            project = Project(
                id=f"project-{status}",
                event_id=event.id,
                name=f"Project {status}",
                description="",
                artifacts_count=0,
                status=status,
                metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            project_repo.create(project)
        test_db.commit()
        
        completed = project_repo.get_by_status(event.id, "completed")
        assert len(completed) == 1
        assert completed[0].status == "completed"


class TestKnowledgeArtifactRepository:
    """Tests for KnowledgeArtifactRepository."""
    
    def test_create_artifact(self, event_repo, project_repo, artifact_repo, test_db):
        """Test creating a knowledge artifact."""
        # Setup: create event and project
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        project = Project(
            id="test-project",
            event_id=event.id,
            name="Test Project",
            description="",
            artifacts_count=0,
            status="pending",
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        project_repo.create(project)
        test_db.commit()
        
        # Create artifact
        artifact = KnowledgeArtifact(
            id="artifact-1",
            project_id="test-project",
            artifact_type="paper",
            title="Test Paper",
            content="Paper content",
            source="arXiv",
            status="extracted",
            confidence_score=0.95,
            extraction_metadata={"method": "pdf_parser"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        created = artifact_repo.create(artifact)
        test_db.commit()
        
        assert created.id == "artifact-1"
        assert created.artifact_type == "paper"
        assert created.confidence_score == 0.95
    
    def test_get_artifacts_by_project(self, event_repo, project_repo, artifact_repo, test_db):
        """Test retrieving artifacts by project."""
        # Setup
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        project = Project(
            id="test-project",
            event_id=event.id,
            name="Test Project",
            description="",
            artifacts_count=0,
            status="pending",
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        project_repo.create(project)
        test_db.commit()
        
        # Create artifacts
        for i in range(3):
            artifact = KnowledgeArtifact(
                id=f"artifact-{i}",
                project_id="test-project",
                artifact_type="paper",
                title=f"Paper {i}",
                content="Content",
                status="extracted",
                confidence_score=0.9,
                extraction_metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            artifact_repo.create(artifact)
        test_db.commit()
        
        artifacts = artifact_repo.get_by_project("test-project")
        assert len(artifacts) == 3
    
    def test_get_artifacts_by_status(self, event_repo, project_repo, artifact_repo, test_db):
        """Test retrieving artifacts by status."""
        # Setup
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        project = Project(
            id="test-project",
            event_id=event.id,
            name="Test Project",
            description="",
            artifacts_count=0,
            status="pending",
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        project_repo.create(project)
        test_db.commit()
        
        # Create artifacts with different statuses
        for status in ["extracted", "validated", "rejected"]:
            artifact = KnowledgeArtifact(
                id=f"artifact-{status}",
                project_id="test-project",
                artifact_type="paper",
                title=f"Paper {status}",
                content="Content",
                status=status,
                confidence_score=0.9,
                extraction_metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            artifact_repo.create(artifact)
        test_db.commit()
        
        validated = artifact_repo.get_by_status("test-project", "validated")
        assert len(validated) == 1
        assert validated[0].status == "validated"


class TestEvaluationExecutionRepository:
    """Tests for EvaluationExecutionRepository."""
    
    def test_create_execution(self, event_repo, project_repo, execution_repo, test_db):
        """Test creating an evaluation execution."""
        # Setup
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        project = Project(
            id="test-project",
            event_id=event.id,
            name="Test Project",
            description="",
            artifacts_count=0,
            status="pending",
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        project_repo.create(project)
        test_db.commit()
        
        # Create execution
        execution = EvaluationExecution(
            id=str(uuid.uuid4()),
            project_id="test-project",
            event_id=event.id,
            status="pending",
            configuration="default",
            quality_threshold=0.8,
            max_iterations=5,
            current_iteration=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            duration_seconds=0.0,
            total_artifacts=3,
            artifacts_passed=0,
            artifacts_failed=0
        )
        
        created = execution_repo.create(execution)
        test_db.commit()
        
        assert created.id == execution.id
        assert created.status == "pending"
        assert created.project_id == "test-project"
    
    def test_update_execution_status(self, event_repo, project_repo, execution_repo, test_db):
        """Test updating execution status."""
        # Setup
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        project = Project(
            id="test-project",
            event_id=event.id,
            name="Test Project",
            description="",
            artifacts_count=0,
            status="pending",
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        project_repo.create(project)
        test_db.commit()
        
        exec_id = str(uuid.uuid4())
        execution = EvaluationExecution(
            id=exec_id,
            project_id="test-project",
            event_id=event.id,
            status="pending",
            configuration="default",
            quality_threshold=0.8,
            max_iterations=5,
            current_iteration=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            duration_seconds=0.0,
            total_artifacts=3,
            artifacts_passed=0,
            artifacts_failed=0
        )
        
        execution_repo.create(execution)
        test_db.commit()
        
        # Update status
        execution.status = "completed"
        execution.final_score = 0.95
        execution.artifacts_passed = 3
        execution_repo.update(execution)
        test_db.commit()
        
        retrieved = execution_repo.get(exec_id)
        assert retrieved.status == "completed"
        assert retrieved.final_score == 0.95
    
    def test_get_executions_by_project(self, event_repo, project_repo, execution_repo, test_db):
        """Test retrieving executions by project."""
        # Setup
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        project = Project(
            id="test-project",
            event_id=event.id,
            name="Test Project",
            description="",
            artifacts_count=0,
            status="pending",
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        project_repo.create(project)
        test_db.commit()
        
        # Create executions
        for i in range(3):
            execution = EvaluationExecution(
                id=str(uuid.uuid4()),
                project_id="test-project",
                event_id=event.id,
                status="completed",
                configuration="default",
                quality_threshold=0.8,
                max_iterations=5,
                current_iteration=5,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                duration_seconds=10.0,
                total_artifacts=3,
                artifacts_passed=3,
                artifacts_failed=0
            )
            execution_repo.create(execution)
        test_db.commit()
        
        executions = execution_repo.get_by_project("test-project")
        assert len(executions) == 3


class TestDatabaseIntegration:
    """Integration tests for complete database workflows."""
    
    def test_end_to_end_workflow(self, event_repo, session_repo, project_repo, 
                                 artifact_repo, execution_repo, test_db):
        """Test complete workflow: event → project → artifacts → execution."""
        # Create event
        event = Event(
            id=str(uuid.uuid4()),
            display_name="ML Conference 2025",
            description="Annual ML research conference",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        event_repo.create(event)
        test_db.commit()
        
        # Create session
        session = SessionInterface(
            id=str(uuid.uuid4()),
            event_id=event.id,
            name="Keynote Session",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session_repo.create(session)
        test_db.commit()
        
        # Create project
        project = Project(
            id="ml-research",
            event_id=event.id,
            name="ML Research Analysis",
            description="Analyze ML papers from conference",
            artifacts_count=0,
            status="in_progress",
            metadata={"conference": "ML2025"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        project_repo.create(project)
        test_db.commit()
        
        # Create artifacts
        for i in range(3):
            artifact = KnowledgeArtifact(
                id=f"paper-{i}",
                project_id="ml-research",
                artifact_type="paper",
                title=f"Research Paper {i}",
                content=f"Content of paper {i}",
                source="arxiv",
                status="extracted",
                confidence_score=0.9 + (i * 0.02),
                extraction_metadata={"pages": 10 + i},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            artifact_repo.create(artifact)
        test_db.commit()
        
        # Create execution
        execution = EvaluationExecution(
            id=str(uuid.uuid4()),
            project_id="ml-research",
            event_id=event.id,
            status="completed",
            configuration="comprehensive",
            quality_threshold=0.85,
            max_iterations=3,
            current_iteration=3,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            duration_seconds=125.5,
            final_score=0.92,
            final_decision="approved",
            total_artifacts=3,
            artifacts_passed=3,
            artifacts_failed=0,
            final_scorecard={"overall": 0.92, "quality": 0.95, "completeness": 0.89}
        )
        execution_repo.create(execution)
        test_db.commit()
        
        # Verify complete workflow
        retrieved_event = event_repo.get(event.id)
        assert retrieved_event.display_name == "ML Conference 2025"
        
        sessions = session_repo.get_by_event(event.id)
        assert len(sessions) == 1
        
        projects = project_repo.get_by_event(event.id)
        assert len(projects) == 1
        
        artifacts = artifact_repo.get_by_project("ml-research")
        assert len(artifacts) == 3
        
        executions = execution_repo.get_by_project("ml-research")
        assert len(executions) == 1
        assert executions[0].final_score == 0.92


class TestTransactionManagement:
    """Tests for transaction management and error handling."""
    
    def test_rollback_on_error(self, event_repo, test_db):
        """Test that rollback works on error."""
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Test Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            event_repo.create(event)
            # Simulate error
            raise ValueError("Test error")
        except ValueError:
            test_db.rollback()
        
        # Event should not exist after rollback
        retrieved = event_repo.get(event.id)
        assert retrieved is None
    
    def test_commit_persistence(self, event_repo, test_db):
        """Test that committed data persists."""
        event = Event(
            id=str(uuid.uuid4()),
            display_name="Persistent Event",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        event_repo.create(event)
        test_db.commit()
        
        # Verify data persists after commit
        retrieved = event_repo.get(event.id)
        assert retrieved is not None
        assert retrieved.display_name == "Persistent Event"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
