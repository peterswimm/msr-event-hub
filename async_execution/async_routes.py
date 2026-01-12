"""FastAPI routes for async job management.

Endpoints for enqueueing, monitoring, and managing async tasks.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from async_execution import (
    JobQueue, evaluate_project, process_artifact_batch, 
    generate_report
)
from infra.database import get_db, DatabaseEngine

router = APIRouter(prefix="/api/async", tags=["async"])


def get_job_queue(db: Session = Depends(get_db)) -> JobQueue:
    """Dependency for job queue instance.
    
    Args:
        db: Database session
        
    Returns:
        JobQueue instance
    """
    db_engine = DatabaseEngine()
    return JobQueue(db_engine)


@router.post("/evaluate/{project_id}")
async def start_evaluation(
    project_id: str,
    configuration: str = "default",
    job_queue: JobQueue = Depends(get_job_queue)
) -> dict:
    """Start async project evaluation.
    
    Args:
        project_id: Project to evaluate
        configuration: Evaluation configuration
        job_queue: Job queue dependency
        
    Returns:
        Job details with ID
        
    Raises:
        HTTPException: If project not found
    """
    try:
        job_id = job_queue.enqueue(
            task_name="evaluate_project",
            task_func=evaluate_project,
            args=(project_id, configuration),
            metadata={"project_id": project_id, "configuration": configuration}
        )
        
        return {
            "job_id": job_id,
            "task": "evaluate_project",
            "status": "queued",
            "project_id": project_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-process/{project_id}")
async def start_batch_processing(
    project_id: str,
    batch_size: int = 10,
    job_queue: JobQueue = Depends(get_job_queue)
) -> dict:
    """Start async artifact batch processing.
    
    Args:
        project_id: Project with artifacts
        batch_size: Artifacts per batch
        job_queue: Job queue dependency
        
    Returns:
        Job details with ID
    """
    try:
        job_id = job_queue.enqueue(
            task_name="process_artifact_batch",
            task_func=process_artifact_batch,
            args=(project_id,),
            kwargs={"batch_size": batch_size},
            metadata={"project_id": project_id, "batch_size": batch_size}
        )
        
        return {
            "job_id": job_id,
            "task": "process_artifact_batch",
            "status": "queued",
            "project_id": project_id,
            "batch_size": batch_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-report/{project_id}")
async def start_report_generation(
    project_id: str,
    job_queue: JobQueue = Depends(get_job_queue)
) -> dict:
    """Start async report generation.
    
    Args:
        project_id: Project to report on
        job_queue: Job queue dependency
        
    Returns:
        Job details with ID
    """
    try:
        job_id = job_queue.enqueue(
            task_name="generate_report",
            task_func=generate_report,
            args=(project_id,),
            metadata={"project_id": project_id}
        )
        
        return {
            "job_id": job_id,
            "task": "generate_report",
            "status": "queued",
            "project_id": project_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    job_queue: JobQueue = Depends(get_job_queue)
) -> dict:
    """Get async job status.
    
    Args:
        job_id: Job ID
        job_queue: Job queue dependency
        
    Returns:
        Job status and metadata
        
    Raises:
        HTTPException: If job not found
    """
    try:
        status = job_queue.get_job_status(job_id)
        
        if status.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Fetch result if ready
        result = job_queue.get_task_result(job_id)
        if result:
            status["result"] = result
        
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def cancel_job(
    job_id: str,
    job_queue: JobQueue = Depends(get_job_queue)
) -> dict:
    """Cancel async job.
    
    Args:
        job_id: Job ID
        job_queue: Job queue dependency
        
    Returns:
        Cancellation result
    """
    try:
        cancelled = job_queue.cancel_job(job_id)
        
        if not cancelled:
            raise HTTPException(status_code=400, detail="Could not cancel job")
        
        return {"job_id": job_id, "cancelled": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    job_queue: JobQueue = Depends(get_job_queue)
) -> dict:
    """List async jobs.
    
    Args:
        status: Filter by status (pending, queued, running, completed, failed, cancelled)
        limit: Maximum results
        job_queue: Job queue dependency
        
    Returns:
        List of jobs
    """
    try:
        from async_execution import JobStatus
        
        status_enum = None
        if status:
            try:
                status_enum = JobStatus[status.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status. Must be one of: {', '.join([s.value for s in JobStatus])}"
                )
        
        jobs = job_queue.list_jobs(status=status_enum, limit=limit)
        
        return {
            "total": len(jobs),
            "limit": limit,
            "status_filter": status,
            "jobs": jobs
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> dict:
    """Check async system health.
    
    Returns:
        Health status
    """
    try:
        from async_execution import celery_app
        
        # Check Celery connectivity
        inspect = celery_app.control.inspect()
        active = inspect.active()
        
        return {
            "status": "healthy",
            "celery": "connected" if active is not None else "disconnected",
            "workers": len(active) if active else 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "celery": "disconnected",
            "error": str(e)
        }
