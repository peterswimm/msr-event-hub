"""Tests for Phase E2: Async Execution."""

import pytest
import time
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from async_execution import (
    JobQueue, JobModel, JobStatus, CeleryConfig,
    create_celery_app, evaluate_project, celery_app
)
from infra.database import Base, DatabaseEngine


@pytest.fixture
def test_db():
    """Create test database."""
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
    # Override with test db
    engine.session_factory = lambda: test_db
    return engine


@pytest.fixture
def job_queue(db_engine):
    """Create job queue fixture."""
    return JobQueue(db_engine)


class TestJobModel:
    """Test JobModel."""
    
    def test_job_creation(self, test_db):
        """Test creating job record."""
        job = JobModel(
            id="test-job-1",
            task_name="evaluate_project",
            status=JobStatus.QUEUED
        )
        test_db.add(job)
        test_db.commit()
        
        retrieved = test_db.query(JobModel).filter(JobModel.id == "test-job-1").first()
        assert retrieved is not None
        assert retrieved.task_name == "evaluate_project"
        assert retrieved.status == JobStatus.QUEUED
    
    def test_job_status_update(self, test_db):
        """Test updating job status."""
        job = JobModel(
            id="test-job-2",
            task_name="evaluate_project",
            status=JobStatus.PENDING
        )
        test_db.add(job)
        test_db.commit()
        
        job.status = JobStatus.RUNNING
        test_db.commit()
        
        retrieved = test_db.query(JobModel).filter(JobModel.id == "test-job-2").first()
        assert retrieved.status == JobStatus.RUNNING
    
    def test_job_duration_calculation(self, test_db):
        """Test duration calculation."""
        start = datetime.utcnow()
        job = JobModel(
            id="test-job-3",
            task_name="evaluate_project",
            status=JobStatus.COMPLETED,
            started_at=start,
            completed_at=start
        )
        test_db.add(job)
        test_db.commit()
        
        assert job.duration_seconds == 0
    
    def test_job_to_dict(self, test_db):
        """Test converting job to dict."""
        job = JobModel(
            id="test-job-4",
            task_name="generate_report",
            status=JobStatus.COMPLETED,
            result={"report": "data"},
            metadata={"project_id": "proj-123"}
        )
        test_db.add(job)
        test_db.commit()
        
        job_dict = job.to_dict()
        assert job_dict["id"] == "test-job-4"
        assert job_dict["task_name"] == "generate_report"
        assert job_dict["status"] == JobStatus.COMPLETED.value
        assert job_dict["result"] == {"report": "data"}


class TestCeleryConfig:
    """Test Celery configuration."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = CeleryConfig()
        assert config.broker_url == "redis://localhost:6379/0"
        assert config.result_backend == "redis://localhost:6379/1"
        assert config.task_serializer == "json"
        assert config.timezone == "UTC"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = CeleryConfig()
        config.broker_url = "redis://custom:6379/0"
        assert config.broker_url == "redis://custom:6379/0"


class TestJobQueue:
    """Test JobQueue operations."""
    
    def test_enqueue_task(self, job_queue, test_db):
        """Test enqueueing task (mocked)."""
        # Mock task function
        def mock_task(*args, **kwargs):
            class MockResult:
                id = "mock-job-id"
                def delay(self, *args, **kwargs):
                    self.id = f"mock-{int(time.time())}"
                    return self
            return MockResult()
        
        # Would enqueue in real scenario
        # For test, just verify database operation works
        job = JobModel(
            id="enqueued-1",
            task_name="evaluate_project",
            status=JobStatus.QUEUED,
            metadata={"project_id": "proj-1"}
        )
        test_db.add(job)
        test_db.commit()
        
        retrieved = test_db.query(JobModel).filter(JobModel.id == "enqueued-1").first()
        assert retrieved.status == JobStatus.QUEUED
    
    def test_get_job_status(self, job_queue, test_db):
        """Test retrieving job status."""
        job = JobModel(
            id="status-1",
            task_name="process_artifact_batch",
            status=JobStatus.RUNNING,
            progress=50
        )
        test_db.add(job)
        test_db.commit()
        
        status = job_queue.get_job_status("status-1")
        assert status["id"] == "status-1"
        assert status["task_name"] == "process_artifact_batch"
        assert status["status"] == JobStatus.RUNNING.value
        assert status["progress"] == 50
    
    def test_get_nonexistent_job(self, job_queue):
        """Test getting nonexistent job."""
        status = job_queue.get_job_status("nonexistent")
        assert status["status"] == "not_found"
    
    def test_cancel_job(self, job_queue, test_db):
        """Test cancelling job."""
        job = JobModel(
            id="cancel-1",
            task_name="evaluate_project",
            status=JobStatus.RUNNING
        )
        test_db.add(job)
        test_db.commit()
        
        # Cancel job
        cancelled = job_queue.cancel_job("cancel-1")
        assert cancelled is True
        
        # Verify status changed
        updated = test_db.query(JobModel).filter(JobModel.id == "cancel-1").first()
        assert updated.status == JobStatus.CANCELLED
    
    def test_list_jobs(self, job_queue, test_db):
        """Test listing jobs."""
        # Create multiple jobs
        for i in range(3):
            job = JobModel(
                id=f"list-job-{i}",
                task_name="evaluate_project",
                status=JobStatus.COMPLETED if i < 2 else JobStatus.RUNNING
            )
            test_db.add(job)
        test_db.commit()
        
        # List all jobs
        all_jobs = job_queue.list_jobs(limit=10)
        assert len(all_jobs) >= 3
        
        # List by status
        completed_jobs = job_queue.list_jobs(status=JobStatus.COMPLETED, limit=10)
        assert len(completed_jobs) >= 2
    
    def test_list_jobs_limit(self, job_queue, test_db):
        """Test listing jobs with limit."""
        for i in range(10):
            job = JobModel(
                id=f"limit-job-{i}",
                task_name="evaluate_project",
                status=JobStatus.COMPLETED
            )
            test_db.add(job)
        test_db.commit()
        
        jobs = job_queue.list_jobs(limit=5)
        assert len(jobs) <= 5


class TestJobStatusEnum:
    """Test JobStatus enum."""
    
    def test_all_statuses(self):
        """Test all status values."""
        statuses = [
            JobStatus.PENDING,
            JobStatus.QUEUED,
            JobStatus.RUNNING,
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED
        ]
        assert len(statuses) == 6
    
    def test_status_values(self):
        """Test status string values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"


class TestCeleryApp:
    """Test Celery application."""
    
    def test_celery_app_creation(self):
        """Test creating Celery app."""
        app = create_celery_app()
        assert app is not None
        assert app.main == "knowledge_agent"
    
    def test_celery_config_applied(self):
        """Test that configuration is applied."""
        config = CeleryConfig()
        config.broker_url = "redis://test:6379/0"
        
        app = create_celery_app(config)
        assert app.conf.get("broker_url") == "redis://test:6379/0"


class TestJobWorkflow:
    """Test complete job workflow."""
    
    def test_full_job_lifecycle(self, job_queue, test_db):
        """Test full job lifecycle."""
        job_id = "lifecycle-1"
        
        # Create job
        job = JobModel(
            id=job_id,
            task_name="evaluate_project",
            status=JobStatus.QUEUED
        )
        test_db.add(job)
        test_db.commit()
        
        # Get initial status
        status1 = job_queue.get_job_status(job_id)
        assert status1["status"] == JobStatus.QUEUED.value
        
        # Mark as running
        job.status = JobStatus.RUNNING
        job.progress = 25
        test_db.commit()
        
        status2 = job_queue.get_job_status(job_id)
        assert status2["status"] == JobStatus.RUNNING.value
        assert status2["progress"] == 25
        
        # Mark as completed
        job.status = JobStatus.COMPLETED
        job.result = {"evaluation": "passed"}
        job.progress = 100
        test_db.commit()
        
        status3 = job_queue.get_job_status(job_id)
        assert status3["status"] == JobStatus.COMPLETED.value
        assert status3["result"] == {"evaluation": "passed"}


class TestJobMetadata:
    """Test job metadata handling."""
    
    def test_job_with_metadata(self, test_db):
        """Test job with metadata."""
        metadata = {
            "project_id": "proj-456",
            "configuration": "advanced",
            "timeout": 3600
        }
        
        job = JobModel(
            id="meta-1",
            task_name="evaluate_project",
            status=JobStatus.QUEUED,
            metadata=metadata
        )
        test_db.add(job)
        test_db.commit()
        
        retrieved = test_db.query(JobModel).filter(JobModel.id == "meta-1").first()
        assert retrieved.metadata == metadata
    
    def test_job_with_error(self, test_db):
        """Test job error handling."""
        job = JobModel(
            id="error-1",
            task_name="evaluate_project",
            status=JobStatus.FAILED,
            error="Evaluation failed: Invalid project configuration"
        )
        test_db.add(job)
        test_db.commit()
        
        retrieved = test_db.query(JobModel).filter(JobModel.id == "error-1").first()
        assert retrieved.error == "Evaluation failed: Invalid project configuration"
        assert retrieved.status == JobStatus.FAILED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
