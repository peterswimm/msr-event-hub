"""Workflow execution status tracking models and persistence.

Tracks evaluation execution state, iteration history, and results for
complete audit trail and status monitoring of project evaluations.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime
import json
import uuid

from src.core.base_repository import BaseRepository


class ExecutionStatus(str, Enum):
    """Status of a workflow execution."""
    PENDING = "pending"          # Created but not started
    RUNNING = "running"          # Currently executing
    EVALUATING = "evaluating"    # In evaluation phase
    ITERATING = "iterating"      # In iteration phase
    COMPLETED = "completed"      # Finished successfully
    FAILED = "failed"            # Execution failed
    CANCELLED = "cancelled"      # User cancelled


class IterationOutcome(str, Enum):
    """Result of a single iteration."""
    SUCCESS = "success"          # All artifacts passed
    IMPROVED = "improved"        # Some improved, some still failing
    UNCHANGED = "unchanged"      # No improvement
    DEGRADED = "degraded"        # Quality went down


@dataclass
class ArtifactScore:
    """Scores for a single artifact in iteration."""
    artifact_id: str
    title: str
    extraction_score: float
    completeness_score: float
    fidelity_score: float
    overall_score: float
    status: str = "pending"  # pending, evaluating, passed, failed
    passed_on_iteration: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class IterationResult:
    """Result of a single evaluation iteration."""
    iteration_number: int
    timestamp: str
    artifacts_evaluated: int
    artifacts_passed: int
    artifacts_failed: int
    average_score: float
    overall_score: float
    outcome: str  # success, improved, unchanged, degraded
    artifact_scores: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ExecutionScorecard:
    """Overall scores from evaluation execution."""
    structure_completeness: float
    extraction_accuracy: float
    fidelity_to_source: float
    signal_to_noise: float
    reusability: float
    
    def overall(self) -> float:
        """Calculate overall average."""
        scores = [
            self.structure_completeness,
            self.extraction_accuracy,
            self.fidelity_to_source,
            self.signal_to_noise,
            self.reusability
        ]
        return sum(scores) / len(scores) if scores else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "structure_completeness": self.structure_completeness,
            "extraction_accuracy": self.extraction_accuracy,
            "fidelity_to_source": self.fidelity_to_source,
            "signal_to_noise": self.signal_to_noise,
            "reusability": self.reusability,
            "overall": self.overall()
        }


@dataclass
class EvaluationExecution:
    """Complete workflow execution tracking."""
    execution_id: str
    project_id: str
    event_id: Optional[str] = None
    status: str = ExecutionStatus.PENDING.value
    configuration: str = "standard"
    quality_threshold: float = 3.0
    max_iterations: int = 2
    current_iteration: int = 0
    
    # Timing
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0
    
    # Results
    iterations: List[Dict[str, Any]] = field(default_factory=list)
    final_scorecard: Optional[Dict[str, Any]] = None
    final_decision: str = "pending"  # pending, passed, failed
    final_score: float = 0.0
    
    # Artifacts
    total_artifacts: int = 0
    artifacts_passed: int = 0
    artifacts_failed: int = 0
    artifact_details: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationExecution":
        """Create instance from dictionary."""
        return cls(**data)
    
    def is_complete(self) -> bool:
        """Check if execution is complete."""
        return self.status in [
            ExecutionStatus.COMPLETED.value,
            ExecutionStatus.FAILED.value,
            ExecutionStatus.CANCELLED.value
        ]
    
    def passed_quality_gate(self) -> bool:
        """Check if final score passes quality threshold."""
        return self.final_score >= self.quality_threshold


class EvaluationExecutionRepository(BaseRepository):
    """Repository for persisting evaluation executions."""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """Initialize repository.
        
        Args:
            storage_dir: Directory for storing execution records
        """
        super().__init__(
            storage_dir=storage_dir or Path("./data/executions"),
            entity_name="EvaluationExecution"
        )
    
    def create_execution(
        self,
        project_id: str,
        event_id: Optional[str] = None,
        configuration: str = "standard",
        max_iterations: int = 2,
        quality_threshold: float = 3.0
    ) -> EvaluationExecution:
        """Create a new evaluation execution.
        
        Args:
            project_id: Project to evaluate
            event_id: Optional event context
            configuration: Configuration name
            max_iterations: Max iterations allowed
            quality_threshold: Minimum passing score
            
        Returns:
            Created EvaluationExecution
        """
        execution = EvaluationExecution(
            execution_id=str(uuid.uuid4()),
            project_id=project_id,
            event_id=event_id,
            configuration=configuration,
            max_iterations=max_iterations,
            quality_threshold=quality_threshold
        )
        self.save(execution.execution_id, execution.to_dict())
        return execution
    
    def get_execution(self, execution_id: str) -> Optional[EvaluationExecution]:
        """Get execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            EvaluationExecution or None if not found
        """
        data = self.load(execution_id)
        if data:
            return EvaluationExecution.from_dict(data)
        return None
    
    def update_execution(self, execution: EvaluationExecution) -> bool:
        """Update an existing execution.
        
        Args:
            execution: Updated EvaluationExecution
            
        Returns:
            True if successful
        """
        return self.save(execution.execution_id, execution.to_dict())
    
    def list_by_project(self, project_id: str) -> List[EvaluationExecution]:
        """List executions for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of executions for this project
        """
        executions = []
        for data in self.list_all():
            exec_obj = EvaluationExecution.from_dict(data)
            if exec_obj.project_id == project_id:
                executions.append(exec_obj)
        
        # Sort by created_at descending
        executions.sort(
            key=lambda x: x.created_at,
            reverse=True
        )
        return executions
    
    def list_by_status(self, status: str) -> List[EvaluationExecution]:
        """List executions with given status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List of executions with this status
        """
        executions = []
        for data in self.list_all():
            exec_obj = EvaluationExecution.from_dict(data)
            if exec_obj.status == status:
                executions.append(exec_obj)
        
        executions.sort(
            key=lambda x: x.created_at,
            reverse=True
        )
        return executions
    
    def list_active(self) -> List[EvaluationExecution]:
        """List all active (non-terminal) executions.
        
        Returns:
            List of active executions
        """
        active_statuses = [
            ExecutionStatus.PENDING.value,
            ExecutionStatus.RUNNING.value,
            ExecutionStatus.EVALUATING.value,
            ExecutionStatus.ITERATING.value
        ]
        
        active = []
        for data in self.list_all():
            exec_obj = EvaluationExecution.from_dict(data)
            if exec_obj.status in active_statuses:
                active.append(exec_obj)
        
        return active
    
    def mark_started(self, execution_id: str) -> bool:
        """Mark execution as started.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if successful
        """
        execution = self.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.RUNNING.value
            execution.started_at = datetime.utcnow().isoformat()
            return self.update_execution(execution)
        return False
    
    def mark_evaluating(self, execution_id: str) -> bool:
        """Mark execution as in evaluation phase.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            True if successful
        """
        execution = self.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.EVALUATING.value
            return self.update_execution(execution)
        return False
    
    def mark_iterating(self, execution_id: str, iteration: int) -> bool:
        """Mark execution as in iteration phase.
        
        Args:
            execution_id: Execution ID
            iteration: Current iteration number
            
        Returns:
            True if successful
        """
        execution = self.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.ITERATING.value
            execution.current_iteration = iteration
            return self.update_execution(execution)
        return False
    
    def mark_completed(
        self,
        execution_id: str,
        final_score: float,
        scorecard: Dict[str, Any],
        passed: bool
    ) -> bool:
        """Mark execution as completed.
        
        Args:
            execution_id: Execution ID
            final_score: Final overall score
            scorecard: Scorecard dictionary
            passed: Whether execution passed quality gate
            
        Returns:
            True if successful
        """
        execution = self.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.COMPLETED.value
            execution.completed_at = datetime.utcnow().isoformat()
            execution.final_score = final_score
            execution.final_scorecard = scorecard
            execution.final_decision = "passed" if passed else "failed"
            
            # Calculate duration
            if execution.started_at:
                start = datetime.fromisoformat(execution.started_at)
                end = datetime.fromisoformat(execution.completed_at)
                execution.duration_seconds = (end - start).total_seconds()
            
            return self.update_execution(execution)
        return False
    
    def mark_failed(self, execution_id: str, error_message: str) -> bool:
        """Mark execution as failed.
        
        Args:
            execution_id: Execution ID
            error_message: Error details
            
        Returns:
            True if successful
        """
        execution = self.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.FAILED.value
            execution.completed_at = datetime.utcnow().isoformat()
            execution.error_message = error_message
            
            if execution.started_at:
                start = datetime.fromisoformat(execution.started_at)
                end = datetime.fromisoformat(execution.completed_at)
                execution.duration_seconds = (end - start).total_seconds()
            
            return self.update_execution(execution)
        return False
    
    def add_iteration_result(
        self,
        execution_id: str,
        iteration_result: Dict[str, Any]
    ) -> bool:
        """Add iteration result to execution.
        
        Args:
            execution_id: Execution ID
            iteration_result: Iteration result dictionary
            
        Returns:
            True if successful
        """
        execution = self.get_execution(execution_id)
        if execution:
            execution.iterations.append(iteration_result)
            return self.update_execution(execution)
        return False
