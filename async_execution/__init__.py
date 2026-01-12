"""Phase E2: Async Execution.

Celery + Redis job queue for background task processing,
job history tracking, and task status updates.
"""

from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import json

from celery import Celery, Task
from celery.result import AsyncResult
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, JSON, Integer, Float
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

from infra.models import Base
from infra.database import DatabaseEngine


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobModel(Base):
    """Model for tracking async jobs in database."""
    __tablename__ = "jobs"
    
    id = Column(String(255), primary_key=True)
    task_name = Column(String(255), nullable=False, index=True)
    status = Column(PG_ENUM(JobStatus), nullable=False, index=True, default=JobStatus.PENDING)
    result = Column(JSON, nullable=True)  # Result data
    error = Column(String(500), nullable=True)  # Error message if failed
    progress = Column(Integer, nullable=True)  # Progress percentage (0-100)
    metadata = Column(JSON, nullable=True)  # Additional context
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task_name": self.task_name,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "duration_seconds": self.duration_seconds
        }


class CeleryConfig:
    """Celery configuration."""
    
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    accept_content: list = ["json"]
    task_serializer: str = "json"
    result_serializer: str = "json"
    timezone: str = "UTC"
    enable_utc: bool = True
    task_track_started: bool = True
    task_time_limit: int = 3600  # 1 hour
    task_soft_time_limit: int = 3300  # 55 minutes
    worker_prefetch_multiplier: int = 4
    worker_max_tasks_per_child: int = 1000


def create_celery_app(config: CeleryConfig = None) -> Celery:
    """Create and configure Celery application.
    
    Args:
        config: Celery configuration (uses defaults if None)
        
    Returns:
        Configured Celery application
    """
    if config is None:
        config = CeleryConfig()
    
    app = Celery("knowledge_agent")
    
    # Apply configuration
    app.conf.update(
        broker_url=config.broker_url,
        result_backend=config.result_backend,
        accept_content=config.accept_content,
        task_serializer=config.task_serializer,
        result_serializer=config.result_serializer,
        timezone=config.timezone,
        enable_utc=config.enable_utc,
        task_track_started=config.task_track_started,
        task_time_limit=config.task_time_limit,
        task_soft_time_limit=config.task_soft_time_limit,
        worker_prefetch_multiplier=config.worker_prefetch_multiplier,
        worker_max_tasks_per_child=config.worker_max_tasks_per_child
    )
    
    return app


# Global Celery instance
celery_app = create_celery_app()


class DatabaseTask(Task):
    """Base task class with database access.
    
    Usage:
        @celery_app.task(base=DatabaseTask)
        def evaluate_project(project_id: str):
            db = self.get_db_session()
            ...
            db.close()
    """
    
    def get_db_session(self) -> Session:
        """Get database session.
        
        Returns:
            SQLAlchemy session
        """
        db_engine = DatabaseEngine()
        return db_engine.session_factory()


celery_app.Task = DatabaseTask


# Task definitions

@celery_app.task(bind=True)
def evaluate_project(self, project_id: str, configuration: str = "default") -> Dict[str, Any]:
    """Evaluate a project asynchronously.
    
    Args:
        project_id: Project to evaluate
        configuration: Evaluation configuration
        
    Returns:
        Evaluation results
    """
    from infra.database import get_db
    
    db = next(get_db())
    
    try:
        # Update job status
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100})
        
        # Perform evaluation (placeholder)
        result = {
            "project_id": project_id,
            "configuration": configuration,
            "status": "success",
            "score": 0.95
        }
        
        return result
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise
    finally:
        db.close()


@celery_app.task(bind=True)
def process_artifact_batch(self, project_id: str, batch_size: int = 10) -> Dict[str, Any]:
    """Process artifacts in batch asynchronously.
    
    Args:
        project_id: Project containing artifacts
        batch_size: Artifacts per batch
        
    Returns:
        Processing results
    """
    try:
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': batch_size})
        
        result = {
            "project_id": project_id,
            "batch_size": batch_size,
            "processed": 0,
            "status": "success"
        }
        
        return result
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery_app.task
def generate_report(project_id: str) -> Dict[str, Any]:
    """Generate project report asynchronously.
    
    Args:
        project_id: Project to report on
        
    Returns:
        Report data
    """
    return {
        "project_id": project_id,
        "report_type": "summary",
        "generated_at": datetime.utcnow().isoformat()
    }


class JobQueue:
    """Queue for managing async jobs."""
    
    def __init__(self, db_engine: DatabaseEngine):
        """Initialize job queue.
        
        Args:
            db_engine: Database engine for job persistence
        """
        self.db_engine = db_engine
    
    def enqueue(self, task_name: str, task_func: Callable, 
                args: tuple = (), kwargs: dict = None, 
                metadata: Dict = None) -> str:
        """Enqueue async task.
        
        Args:
            task_name: Task identifier
            task_func: Task function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            metadata: Additional metadata
            
        Returns:
            Job ID
        """
        kwargs = kwargs or {}
        
        # Execute task asynchronously
        result = task_func.delay(*args, **kwargs)
        
        # Persist job record
        db = self.db_engine.session_factory()
        job = JobModel(
            id=result.id,
            task_name=task_name,
            status=JobStatus.QUEUED,
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()
        db.close()
        
        return result.id
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get job status.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status and metadata
        """
        db = self.db_engine.session_factory()
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            return {"status": "not_found"}
        
        result = job.to_dict()
        db.close()
        return result
    
    def get_task_result(self, job_id: str, timeout: int = 30) -> Optional[Dict]:
        """Get task result from Celery.
        
        Args:
            job_id: Job ID
            timeout: Seconds to wait for result
            
        Returns:
            Task result or None if not ready
        """
        result = AsyncResult(job_id, app=celery_app)
        
        try:
            if result.ready():
                return result.get(timeout=timeout)
            return None
        except Exception as e:
            return {"error": str(e)}
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel async job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if cancelled successfully
        """
        # Revoke Celery task
        celery_app.control.revoke(job_id, terminate=True)
        
        # Update database
        db = self.db_engine.session_factory()
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if job:
            job.status = JobStatus.CANCELLED
            job.updated_at = datetime.utcnow()
            db.commit()
        db.close()
        
        return True
    
    def list_jobs(self, status: JobStatus = None, limit: int = 50) -> list:
        """List jobs, optionally filtered by status.
        
        Args:
            status: Filter by status
            limit: Maximum results
            
        Returns:
            List of jobs
        """
        db = self.db_engine.session_factory()
        query = db.query(JobModel)
        
        if status:
            query = query.filter(JobModel.status == status)
        
        jobs = query.order_by(JobModel.created_at.desc()).limit(limit).all()
        result = [job.to_dict() for job in jobs]
        db.close()
        
        return result


# API routes for async jobs

async def enqueue_evaluation(project_id: str, configuration: str = "default") -> Dict[str, str]:
    """Enqueue project evaluation.
    
    Args:
        project_id: Project to evaluate
        configuration: Evaluation configuration
        
    Returns:
        Job details with ID
    """
    result = evaluate_project.delay(project_id, configuration)
    return {"job_id": result.id, "status": "queued"}


async def get_job_status(job_id: str, job_queue: JobQueue) -> Dict:
    """Get async job status.
    
    Args:
        job_id: Job ID
        job_queue: Job queue instance
        
    Returns:
        Job status
    """
    return job_queue.get_job_status(job_id)


async def cancel_job(job_id: str, job_queue: JobQueue) -> Dict:
    """Cancel async job.
    
    Args:
        job_id: Job ID
        job_queue: Job queue instance
        
    Returns:
        Cancellation result
    """
    success = job_queue.cancel_job(job_id)
    return {"job_id": job_id, "cancelled": success}
