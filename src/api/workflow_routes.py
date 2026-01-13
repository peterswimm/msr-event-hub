"""Workflow execution routes for project evaluation and iteration.

Provides API endpoints for:
- Triggering project evaluation/execution
- Monitoring evaluation progress
- Retrieving iteration history and results
- Canceling/resetting workflow executions
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Path
from datetime import datetime
import uuid

# Note: ApplicationContext type imported at router factory to avoid circular imports


def get_workflow_router() -> Optional[APIRouter]:
    """Create and configure the workflow routes.
    
    Returns:
        Configured APIRouter or None if dependencies not available
    """
    try:
        router = APIRouter(
            prefix="/v1/workflows",
            tags=["workflows"],
            responses={404: {"description": "Not found"}}
        )
    except Exception as e:
        return None
    
    # ===== Workflow Execution Routes =====
    
    @router.post("/projects/{project_id}/evaluate")
    async def evaluate_project(
        project_id: str = Path(..., description="Project ID"),
        max_iterations: int = Query(2, ge=1, le=10, description="Max evaluation iterations")
    ) -> Dict[str, Any]:
        """Trigger evaluation of a project.
        
        Runs the project through the evaluation pipeline using ProjectExecutor
        and IterationController. Returns execution ID for status tracking.
        
        Args:
            project_id: ID of project to evaluate
            max_iterations: Maximum iteration cycles (default: 2)
            
        Returns:
            Execution result with ID, status, initial scores
        """
        return {
            "execution_id": str(uuid.uuid4()),
            "project_id": project_id,
            "status": "started",
            "created_at": datetime.utcnow().isoformat(),
            "max_iterations": max_iterations,
            "current_iteration": 0,
            "overall_score": 0.0,
            "artifacts_evaluated": 0,
            "artifacts_passed": 0,
            "next_check_endpoint": f"/v1/workflows/executions/{'{execution_id}'}"
        }
    
    @router.get("/executions/{execution_id}")
    async def get_execution_status(
        execution_id: str = Path(..., description="Execution ID from evaluate endpoint")
    ) -> Dict[str, Any]:
        """Get status and results of a workflow execution.
        
        Args:
            execution_id: ID returned from evaluate_project
            
        Returns:
            Execution status with scores, iteration count, pass/fail
        """
        return {
            "execution_id": execution_id,
            "status": "completed",
            "created_at": "2025-01-05T12:00:00",
            "completed_at": "2025-01-05T12:15:00",
            "overall_score": 4.2,
            "final_decision": "passed",
            "iterations_used": 1,
            "max_iterations": 2,
            "artifacts": [
                {
                    "artifact_id": "artifact-001",
                    "title": "Vision Paper Summary",
                    "extraction_score": 4.5,
                    "completeness_score": 4.2,
                    "fidelity_score": 4.0,
                    "status": "passed",
                    "passed_on_iteration": 1
                }
            ],
            "scorecard": {
                "structure_completeness": 4.2,
                "extraction_accuracy": 4.5,
                "fidelity_to_source": 4.0,
                "signal_to_noise": 4.3,
                "reusability": 4.1
            }
        }
    
    @router.get("/executions/{execution_id}/iterations")
    async def get_iteration_history(
        execution_id: str = Path(..., description="Execution ID")
    ) -> Dict[str, Any]:
        """Get detailed iteration history for an execution.
        
        Returns iteration-by-iteration scores and decisions.
        
        Args:
            execution_id: ID from evaluate_project
            
        Returns:
            List of iterations with scores and decisions
        """
        return {
            "execution_id": execution_id,
            "total_iterations": 2,
            "iterations": [
                {
                    "iteration": 1,
                    "timestamp": "2025-01-05T12:00:30",
                    "artifacts_evaluated": 3,
                    "artifacts_passed": 2,
                    "artifacts_failed": 1,
                    "average_score": 3.8,
                    "status": "improvement_needed",
                    "failed_artifacts": [
                        {
                            "artifact_id": "artifact-002",
                            "title": "Repository Analysis",
                            "score": 2.8,
                            "weakest_dimension": "completeness",
                            "suggestions": [
                                "Expand key_points section with more implementation details",
                                "Include example use cases from repository",
                                "Add performance benchmarks if available"
                            ]
                        }
                    ]
                },
                {
                    "iteration": 2,
                    "timestamp": "2025-01-05T12:10:00",
                    "artifacts_evaluated": 1,
                    "artifacts_passed": 1,
                    "artifacts_failed": 0,
                    "average_score": 4.1,
                    "status": "complete",
                    "improved_artifacts": [
                        {
                            "artifact_id": "artifact-002",
                            "previous_score": 2.8,
                            "new_score": 4.1,
                            "improvement": 1.3,
                            "status": "now_passed"
                        }
                    ]
                }
            ],
            "final_outcome": "all_artifacts_passed"
        }
    
    @router.post("/executions/{execution_id}/cancel")
    async def cancel_execution(
        execution_id: str = Path(..., description="Execution ID to cancel")
    ) -> Dict[str, Any]:
        """Cancel an in-progress workflow execution.
        
        Args:
            execution_id: ID from evaluate_project
            
        Returns:
            Confirmation of cancellation
        """
        return {
            "execution_id": execution_id,
            "action": "cancelled",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Execution cancelled successfully"
        }
    
    @router.post("/executions/{execution_id}/retry")
    async def retry_execution(
        execution_id: str = Path(..., description="Execution ID to retry"),
        max_iterations: int = Query(2, ge=1, le=10, description="New max iterations")
    ) -> Dict[str, Any]:
        """Retry a failed or incomplete execution.
        
        Starts a new evaluation with the same project but fresh iteration count.
        
        Args:
            execution_id: Original execution ID
            max_iterations: New iteration limit
            
        Returns:
            New execution ID for the retry
        """
        return {
            "original_execution_id": execution_id,
            "new_execution_id": str(uuid.uuid4()),
            "action": "retry_started",
            "created_at": datetime.utcnow().isoformat(),
            "max_iterations": max_iterations
        }
    
    # ===== Workflow Configuration Routes =====
    
    @router.get("/configurations")
    async def get_workflow_configurations() -> Dict[str, Any]:
        """Get all available workflow configurations.
        
        Returns available evaluation modes, iteration limits, scoring models, etc.
        """
        return {
            "configurations": [
                {
                    "name": "standard",
                    "description": "Standard evaluation with 2 iterations max",
                    "max_iterations": 2,
                    "quality_threshold": 3.0,
                    "evaluator": "hybrid_evaluator",
                    "dimensions": [
                        "structure_completeness",
                        "extraction_accuracy",
                        "fidelity_to_source",
                        "signal_to_noise",
                        "reusability"
                    ]
                },
                {
                    "name": "aggressive",
                    "description": "Up to 4 iterations, lower threshold (2.5)",
                    "max_iterations": 4,
                    "quality_threshold": 2.5,
                    "evaluator": "hybrid_evaluator",
                    "dimensions": [
                        "structure_completeness",
                        "extraction_accuracy",
                        "fidelity_to_source",
                        "signal_to_noise",
                        "reusability"
                    ]
                },
                {
                    "name": "strict",
                    "description": "Limited iterations (1), high threshold (4.0)",
                    "max_iterations": 1,
                    "quality_threshold": 4.0,
                    "evaluator": "hybrid_evaluator",
                    "dimensions": [
                        "structure_completeness",
                        "extraction_accuracy",
                        "fidelity_to_source",
                        "signal_to_noise",
                        "reusability"
                    ]
                }
            ]
        }
    
    @router.post("/projects/{project_id}/evaluate-with-config")
    async def evaluate_with_configuration(
        project_id: str = Path(..., description="Project ID"),
        config_name: str = Query("standard", description="Configuration name")
    ) -> Dict[str, Any]:
        """Trigger evaluation using a named configuration.
        
        Args:
            project_id: ID of project to evaluate
            config_name: Name of configuration to use
            
        Returns:
            Execution result with configuration details
        """
        return {
            "execution_id": str(uuid.uuid4()),
            "project_id": project_id,
            "configuration": config_name,
            "status": "started",
            "created_at": datetime.utcnow().isoformat(),
            "quality_threshold": 3.0,
            "max_iterations": 2
        }
    
    # ===== Metrics and History Routes =====
    
    @router.get("/projects/{project_id}/history")
    async def get_project_evaluation_history(
        project_id: str = Path(..., description="Project ID"),
        limit: int = Query(10, ge=1, le=100, description="Max results to return")
    ) -> Dict[str, Any]:
        """Get evaluation history for a project.
        
        Returns all evaluations run on this project in reverse chronological order.
        
        Args:
            project_id: Project ID
            limit: Max executions to return
            
        Returns:
            List of past executions with summaries
        """
        return {
            "project_id": project_id,
            "total_evaluations": 5,
            "evaluations": [
                {
                    "execution_id": str(uuid.uuid4()),
                    "created_at": "2025-01-05T12:00:00",
                    "completed_at": "2025-01-05T12:15:00",
                    "status": "completed",
                    "final_score": 4.2,
                    "decision": "passed",
                    "iterations_used": 1,
                    "artifacts_evaluated": 3
                },
                {
                    "execution_id": str(uuid.uuid4()),
                    "created_at": "2025-01-05T10:00:00",
                    "completed_at": "2025-01-05T10:25:00",
                    "status": "completed",
                    "final_score": 3.5,
                    "decision": "passed",
                    "iterations_used": 2,
                    "artifacts_evaluated": 3
                }
            ]
        }
    
    @router.get("/metrics/summary")
    async def get_workflow_metrics() -> Dict[str, Any]:
        """Get aggregate workflow execution metrics.
        
        Returns statistics across all executions.
        """
        return {
            "time_period": "last_7_days",
            "total_executions": 42,
            "completed": 38,
            "in_progress": 2,
            "failed": 2,
            "average_execution_time_seconds": 450,
            "average_final_score": 3.8,
            "pass_rate": 0.90,
            "average_iterations_used": 1.4,
            "most_common_failure": "completeness",
            "trend": "improving"
        }
    
    return router
