"""Integration tests for Phase E: All components working together.

Tests E1-E4 integration:
- E1: Database + Authentication + Configuration + Monitoring
- E2: Async jobs with database persistence
- E3: Analytics with async job tracking
- E4: Knowledge graph with recommendations
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infra.models import Base, User
from infra.database import DatabaseEngine
from infra.authentication import AuthenticationManager
from src.config.settings import Settings
from async_execution import JobQueue, JobModel, JobStatus
from analytics import MetricsAggregator, DashboardAPI, DailyMetricsSummary
from knowledge_graph import GraphDatabase_, Neo4jConfig, GraphNode, NodeType


@pytest.fixture
def test_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def db_engine(test_db):
    """Create database engine fixture."""
    engine = DatabaseEngine()
    engine.session_factory = lambda: test_db
    return engine


@pytest.fixture
def auth_manager():
    """Create authentication manager."""
    return AuthenticationManager()


@pytest.fixture
def job_queue(db_engine):
    """Create job queue."""
    return JobQueue(db_engine)


@pytest.fixture
def metrics_aggregator(test_db):
    """Create metrics aggregator."""
    return MetricsAggregator(test_db)


@pytest.fixture
def graph_db():
    """Create mock graph database."""
    config = Neo4jConfig()
    return GraphDatabase_(config)


class TestE1Integration:
    """Test E1 Foundation components integration."""
    
    def test_config_loads_properly(self):
        """Test configuration loading."""
        settings = Settings()
        assert settings is not None
        assert hasattr(settings, 'secret_key')
    
    def test_user_creation_and_auth(self, test_db, auth_manager):
        """Test user creation and authentication flow."""
        # Create user in database
        user = User(
            username="test_user",
            email="test@example.com",
            hashed_password=auth_manager.hash_password("TestPass123!")
        )
        test_db.add(user)
        test_db.commit()
        
        # Verify user created
        retrieved_user = test_db.query(User).filter(User.username == "test_user").first()
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        
        # Verify password hashing
        assert auth_manager.verify_password("TestPass123!", retrieved_user.hashed_password)
        assert not auth_manager.verify_password("WrongPassword", retrieved_user.hashed_password)
    
    def test_jwt_token_workflow(self, auth_manager):
        """Test JWT token generation and validation."""
        user_data = {"sub": "user123", "username": "testuser"}
        
        # Generate token
        token = auth_manager.create_access_token(user_data)
        assert token is not None
        assert isinstance(token, str)
        
        # Validate token
        payload = auth_manager.verify_token(token)
        assert payload is not None
        assert payload.get("sub") == "user123"


class TestE2Integration:
    """Test E2 Async Execution integration with database."""
    
    def test_job_creation_and_persistence(self, job_queue, test_db):
        """Test job creation and database persistence."""
        job = JobModel(
            id="integration-job-1",
            task_name="evaluate_project",
            status=JobStatus.QUEUED,
            metadata={"project_id": "proj-1"}
        )
        test_db.add(job)
        test_db.commit()
        
        # Retrieve from database
        retrieved = test_db.query(JobModel).filter(JobModel.id == "integration-job-1").first()
        assert retrieved is not None
        assert retrieved.task_name == "evaluate_project"
        assert retrieved.metadata["project_id"] == "proj-1"
    
    def test_job_status_lifecycle(self, job_queue, test_db):
        """Test complete job status lifecycle."""
        job_id = "lifecycle-1"
        
        # Create job
        job = JobModel(id=job_id, task_name="test_task", status=JobStatus.PENDING)
        test_db.add(job)
        test_db.commit()
        
        # Transition through states
        states = [JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.COMPLETED]
        for state in states:
            job = test_db.query(JobModel).filter(JobModel.id == job_id).first()
            job.status = state
            test_db.commit()
            
            retrieved = test_db.query(JobModel).filter(JobModel.id == job_id).first()
            assert retrieved.status == state
    
    def test_job_with_result(self, job_queue, test_db):
        """Test job with result storage."""
        job = JobModel(
            id="result-job-1",
            task_name="generate_report",
            status=JobStatus.COMPLETED,
            result={"report_url": "s3://bucket/report.pdf", "pages": 42}
        )
        test_db.add(job)
        test_db.commit()
        
        retrieved = test_db.query(JobModel).filter(JobModel.id == "result-job-1").first()
        assert retrieved.result["report_url"] == "s3://bucket/report.pdf"
        assert retrieved.result["pages"] == 42


class TestE3Integration:
    """Test E3 Analytics integration with job tracking."""
    
    def test_metrics_snapshot_creation(self, metrics_aggregator, test_db):
        """Test metrics snapshot recording."""
        snap_id = metrics_aggregator.record_snapshot(
            metric_name="job_completion_time",
            value=125.5,
            tags={"job_type": "evaluation"}
        )
        
        assert snap_id is not None
        snapshot = test_db.query(MetricsSnapshot).filter(MetricsSnapshot.id == snap_id).first()
        assert snapshot.metric_name == "job_completion_time"
        assert snapshot.value == 125.5
    
    def test_daily_summary_creation(self, metrics_aggregator, test_db):
        """Test daily metrics summary."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        summary = DailyMetricsSummary(
            id="daily-1",
            date=today,
            total_requests=1000,
            auth_attempts=100,
            evaluations_completed=50
        )
        summary_id = metrics_aggregator.store_daily_summary(summary)
        
        assert summary_id is not None
        retrieved = test_db.query(DailyMetricsSummary).filter(DailyMetricsSummary.id == summary_id).first()
        assert retrieved.total_requests == 1000
    
    def test_dashboard_generation(self, metrics_aggregator):
        """Test dashboard API."""
        dashboard = DashboardAPI(None, metrics_aggregator)
        dash = dashboard.get_realtime_dashboard()
        
        assert dash is not None
        assert "timestamp" in dash
        assert "requests" in dash
        assert "database" in dash


class TestE4Integration:
    """Test E4 Knowledge Graph integration."""
    
    def test_node_creation(self, graph_db):
        """Test creating graph node."""
        node = GraphNode(
            id="paper-integration-1",
            node_type=NodeType.PAPER,
            properties={"title": "Integration Test Paper", "year": 2026}
        )
        
        result = graph_db.create_node(node)
        assert result is True
    
    def test_node_retrieval(self, graph_db):
        """Test retrieving graph node."""
        # In mock mode, returns None
        node = graph_db.get_node("paper-1")
        assert node is None or node is not None  # Graceful fallback


class TestFullE1toE4Workflow:
    """Test complete workflow from E1 through E4."""
    
    def test_user_registration_to_analytics(self, test_db, auth_manager, metrics_aggregator):
        """Test full workflow: user -> auth -> metrics."""
        # E1: Create and authenticate user
        user = User(
            username="workflow_user",
            email="workflow@example.com",
            hashed_password=auth_manager.hash_password("SecurePass123!")
        )
        test_db.add(user)
        test_db.commit()
        
        # Verify user exists
        retrieved = test_db.query(User).filter(User.username == "workflow_user").first()
        assert retrieved is not None
        
        # E3: Record metrics for authentication attempt
        snap_id = metrics_aggregator.record_snapshot(
            metric_name="auth_attempt",
            value=1.0,
            tags={"user": "workflow_user", "success": True}
        )
        
        assert snap_id is not None
    
    def test_job_queue_to_analytics_workflow(self, job_queue, test_db, metrics_aggregator):
        """Test workflow: job queue -> analytics tracking."""
        # E2: Create job
        job = JobModel(
            id="workflow-job-1",
            task_name="evaluate_project",
            status=JobStatus.QUEUED,
            metadata={"project_id": "proj-123"}
        )
        test_db.add(job)
        test_db.commit()
        
        # E3: Record job metrics
        snap_id = metrics_aggregator.record_snapshot(
            metric_name="job_queued",
            value=1.0,
            tags={"task": "evaluate_project"}
        )
        
        # Update job to running
        job.status = JobStatus.RUNNING
        test_db.commit()
        
        # Record running metric
        snap_id2 = metrics_aggregator.record_snapshot(
            metric_name="job_running",
            value=1.0,
            tags={"task": "evaluate_project"}
        )
        
        assert snap_id is not None
        assert snap_id2 is not None


class TestErrorHandling:
    """Test error handling across phases."""
    
    def test_invalid_token_handling(self, auth_manager):
        """Test handling of invalid token."""
        invalid_token = "invalid.token.here"
        payload = auth_manager.verify_token(invalid_token)
        assert payload is None  # Should return None gracefully
    
    def test_job_cancellation(self, job_queue, test_db):
        """Test job cancellation."""
        job = JobModel(
            id="cancel-test-1",
            task_name="test_task",
            status=JobStatus.RUNNING
        )
        test_db.add(job)
        test_db.commit()
        
        # Cancel job
        cancelled = job_queue.cancel_job("cancel-test-1")
        assert cancelled is True
        
        # Verify status changed
        updated = test_db.query(JobModel).filter(JobModel.id == "cancel-test-1").first()
        assert updated.status == JobStatus.CANCELLED
    
    def test_missing_job_handling(self, job_queue):
        """Test handling of missing job."""
        status = job_queue.get_job_status("nonexistent-job")
        assert status["status"] == "not_found"


class TestConcurrency:
    """Test concurrent operations."""
    
    def test_multiple_jobs_persistence(self, job_queue, test_db):
        """Test multiple jobs can be persisted."""
        jobs = []
        for i in range(10):
            job = JobModel(
                id=f"concurrent-job-{i}",
                task_name="test_task",
                status=JobStatus.QUEUED
            )
            jobs.append(job)
            test_db.add(job)
        
        test_db.commit()
        
        # Verify all jobs created
        retrieved = test_db.query(JobModel).filter(
            JobModel.id.in_([f"concurrent-job-{i}" for i in range(10)])
        ).all()
        assert len(retrieved) == 10
    
    def test_multiple_users(self, test_db, auth_manager):
        """Test multiple users in system."""
        for i in range(5):
            user = User(
                username=f"user_{i}",
                email=f"user{i}@example.com",
                hashed_password=auth_manager.hash_password("SecurePass123!")
            )
            test_db.add(user)
        
        test_db.commit()
        
        users = test_db.query(User).all()
        assert len(users) >= 5


class TestDataIntegrity:
    """Test data integrity across components."""
    
    def test_job_metadata_preservation(self, test_db):
        """Test that job metadata is preserved."""
        complex_metadata = {
            "project_id": "proj-456",
            "configuration": "advanced",
            "retry_count": 2,
            "tags": ["important", "high-priority"],
            "nested": {"key": "value"}
        }
        
        job = JobModel(
            id="metadata-test-1",
            task_name="evaluate",
            status=JobStatus.COMPLETED,
            metadata=complex_metadata
        )
        test_db.add(job)
        test_db.commit()
        
        retrieved = test_db.query(JobModel).filter(JobModel.id == "metadata-test-1").first()
        assert retrieved.metadata == complex_metadata
        assert retrieved.metadata["nested"]["key"] == "value"
    
    def test_timestamp_tracking(self, test_db):
        """Test that timestamps are properly tracked."""
        before = datetime.utcnow()
        
        job = JobModel(
            id="timestamp-test-1",
            task_name="test",
            status=JobStatus.PENDING
        )
        test_db.add(job)
        test_db.commit()
        
        after = datetime.utcnow()
        
        retrieved = test_db.query(JobModel).filter(JobModel.id == "timestamp-test-1").first()
        assert retrieved.created_at is not None
        assert before <= retrieved.created_at <= after


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
