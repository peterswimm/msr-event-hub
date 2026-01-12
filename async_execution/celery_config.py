"""Celery worker configuration and startup."""

import logging
from typing import Optional

from celery import signals
from sqlalchemy.orm import Session

from async_execution import celery_app, JobStatus, JobModel
from infra.database import DatabaseEngine
from observability.monitoring import ApplicationMetrics, Logger

logger = Logger(__name__)
metrics = ApplicationMetrics()


class CeleryWorkerManager:
    """Manager for Celery worker lifecycle and events."""
    
    def __init__(self, db_engine: DatabaseEngine):
        """Initialize worker manager.
        
        Args:
            db_engine: Database engine instance
        """
        self.db_engine = db_engine
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup Celery event handlers."""
        
        @signals.task_prerun.connect(sender=celery_app)
        def task_prerun(sender, task_id, task, args, kwargs, **extra):
            """Handle pre-task execution."""
            db = self.db_engine.session_factory()
            job = db.query(JobModel).filter(JobModel.id == task_id).first()
            
            if job:
                job.status = JobStatus.RUNNING
                job.started_at = None  # Will be set by task
                db.commit()
            
            logger.info(f"Task started: {task.name}", extra={"task_id": task_id})
            metrics.task_started(task.name)
            db.close()
        
        @signals.task_postrun.connect(sender=celery_app)
        def task_postrun(sender, task_id, task, args, kwargs, retval, state, **extra):
            """Handle post-task execution."""
            db = self.db_engine.session_factory()
            job = db.query(JobModel).filter(JobModel.id == task_id).first()
            
            if job:
                job.status = JobStatus.COMPLETED
                job.result = retval if isinstance(retval, dict) else {"result": str(retval)}
                db.commit()
            
            logger.info(f"Task completed: {task.name}", extra={"task_id": task_id})
            metrics.task_completed(task.name)
            db.close()
        
        @signals.task_failure.connect(sender=celery_app)
        def task_failure(sender, task_id, exception, args, kwargs, traceback, einfo, **extra):
            """Handle task failure."""
            db = self.db_engine.session_factory()
            job = db.query(JobModel).filter(JobModel.id == task_id).first()
            
            if job:
                job.status = JobStatus.FAILED
                job.error = str(exception)
                db.commit()
            
            logger.error(
                f"Task failed: {sender.name}",
                extra={
                    "task_id": task_id,
                    "exception": str(exception)
                }
            )
            metrics.task_failed(sender.name)
            db.close()
        
        @signals.task_retry.connect(sender=celery_app)
        def task_retry(sender, task_id, reason, einfo, **extra):
            """Handle task retry."""
            logger.warning(
                f"Task retrying: {sender.name}",
                extra={
                    "task_id": task_id,
                    "reason": str(reason)
                }
            )
        
        @signals.worker_ready.connect(sender=celery_app)
        def worker_ready(sender, **extra):
            """Handle worker startup."""
            logger.info("Celery worker ready", extra={"worker": sender.hostname})
        
        @signals.worker_shutdown.connect(sender=celery_app)
        def worker_shutdown(sender, **extra):
            """Handle worker shutdown."""
            logger.info("Celery worker shutting down", extra={"worker": sender.hostname})


def start_worker(app, loglevel="info", concurrency=4, queues: Optional[list] = None):
    """Start Celery worker.
    
    Args:
        app: Celery application
        loglevel: Log level (debug, info, warning, error)
        concurrency: Number of concurrent workers
        queues: Specific queues to consume (None = all)
    """
    worker = app.Worker(
        loglevel=loglevel,
        concurrency=concurrency,
        queues=queues or ["celery"],
        pool="prefork",
        prefetch_multiplier=4,
        max_tasks_per_child=1000,
        task_events=True,
        task_track_started=True
    )
    
    logger.info(
        f"Starting Celery worker",
        extra={
            "loglevel": loglevel,
            "concurrency": concurrency,
            "queues": queues or ["celery"]
        }
    )
    
    worker.start()


if __name__ == "__main__":
    from infra.database import DatabaseEngine
    
    db_engine = DatabaseEngine()
    manager = CeleryWorkerManager(db_engine)
    start_worker(celery_app, loglevel="info", concurrency=4)
