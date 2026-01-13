"""Integration tests for Phase D workflow components.

Tests ProjectExecutor, IterationController, evaluators, and EvaluationExecution
repository working together in the context of the ApplicationContext.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from main import ApplicationContext
from src.core.workflow_status import (
    EvaluationExecution,
    EvaluationExecutionRepository,
    ExecutionStatus,
    IterationResult,
    ExecutionScorecard
)
from projects import ProjectDefinition
from src.workflows.project_executor import ProjectExecutor
from src.workflows.iteration_controller import IterationController
from src.evaluation.hybrid_evaluator import HybridEvaluator


class TestWorkflowComponentsIntegration:
    """Test workflow components together."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def app_context(self, temp_storage):
        """Create application context with temporary storage."""
        return ApplicationContext(storage_root=temp_storage)

    def test_application_context_initializes_workflow_components(self, app_context):
        """Test that ApplicationContext initializes workflow components."""
        assert app_context.executor is not None
        assert isinstance(app_context.executor, ProjectExecutor)
        assert app_context.iteration_controller is not None
        assert isinstance(app_context.iteration_controller, IterationController)
        assert app_context.evaluator is not None
        assert isinstance(app_context.evaluator, HybridEvaluator)

    def test_executor_has_repository_reference(self, app_context):
        """Test that ProjectExecutor has access to repository."""
        assert app_context.executor.repository is not None
        assert app_context.executor.repository is app_context.project_repo

    def test_iteration_controller_has_executor_reference(self, app_context):
        """Test that IterationController has executor."""
        assert app_context.iteration_controller.executor is not None
        assert app_context.iteration_controller.executor is app_context.executor


class TestEvaluationExecutionRepository:
    """Test EvaluationExecution persistence."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def repo(self, temp_storage):
        """Create execution repository."""
        return EvaluationExecutionRepository(storage_dir=temp_storage / "executions")

    def test_create_execution(self, repo):
        """Test creating a new execution."""
        execution = repo.create_execution(
            project_id="proj-001",
            event_id="event-001",
            configuration="standard",
            max_iterations=2,
            quality_threshold=3.0
        )

        assert execution.execution_id is not None
        assert execution.project_id == "proj-001"
        assert execution.event_id == "event-001"
        assert execution.configuration == "standard"
        assert execution.max_iterations == 2
        assert execution.quality_threshold == 3.0
        assert execution.status == ExecutionStatus.PENDING.value

    def test_get_execution(self, repo):
        """Test retrieving execution."""
        created = repo.create_execution(project_id="proj-002")
        retrieved = repo.get_execution(created.execution_id)

        assert retrieved is not None
        assert retrieved.execution_id == created.execution_id
        assert retrieved.project_id == "proj-002"

    def test_update_execution(self, repo):
        """Test updating execution."""
        execution = repo.create_execution(project_id="proj-003")

        execution.status = ExecutionStatus.RUNNING.value
        execution.current_iteration = 1
        repo.update_execution(execution)

        retrieved = repo.get_execution(execution.execution_id)
        assert retrieved.status == ExecutionStatus.RUNNING.value
        assert retrieved.current_iteration == 1

    def test_list_by_project(self, repo):
        """Test listing executions by project."""
        repo.create_execution(project_id="proj-001")
        repo.create_execution(project_id="proj-001")
        repo.create_execution(project_id="proj-002")

        proj1_executions = repo.list_by_project("proj-001")
        proj2_executions = repo.list_by_project("proj-002")

        assert len(proj1_executions) == 2
        assert len(proj2_executions) == 1
        assert all(e.project_id == "proj-001" for e in proj1_executions)
        assert proj2_executions[0].project_id == "proj-002"

    def test_list_by_status(self, repo):
        """Test listing executions by status."""
        exe1 = repo.create_execution(project_id="proj-001")
        exe2 = repo.create_execution(project_id="proj-001")
        exe3 = repo.create_execution(project_id="proj-001")

        exe1.status = ExecutionStatus.RUNNING.value
        exe2.status = ExecutionStatus.COMPLETED.value
        exe3.status = ExecutionStatus.COMPLETED.value

        repo.update_execution(exe1)
        repo.update_execution(exe2)
        repo.update_execution(exe3)

        running = repo.list_by_status(ExecutionStatus.RUNNING.value)
        completed = repo.list_by_status(ExecutionStatus.COMPLETED.value)

        assert len(running) == 1
        assert len(completed) == 2

    def test_list_active(self, repo):
        """Test listing active executions."""
        exe1 = repo.create_execution(project_id="proj-001")
        exe2 = repo.create_execution(project_id="proj-001")
        exe3 = repo.create_execution(project_id="proj-001")

        exe1.status = ExecutionStatus.RUNNING.value
        exe2.status = ExecutionStatus.COMPLETED.value
        exe3.status = ExecutionStatus.EVALUATING.value

        repo.update_execution(exe1)
        repo.update_execution(exe2)
        repo.update_execution(exe3)

        active = repo.list_active()

        assert len(active) == 2
        assert exe1 in active
        assert exe3 in active
        assert exe2 not in active

    def test_mark_started(self, repo):
        """Test marking execution as started."""
        execution = repo.create_execution(project_id="proj-001")

        assert execution.started_at is None
        repo.mark_started(execution.execution_id)

        retrieved = repo.get_execution(execution.execution_id)
        assert retrieved.status == ExecutionStatus.RUNNING.value
        assert retrieved.started_at is not None

    def test_mark_evaluating(self, repo):
        """Test marking execution as evaluating."""
        execution = repo.create_execution(project_id="proj-001")

        repo.mark_started(execution.execution_id)
        repo.mark_evaluating(execution.execution_id)

        retrieved = repo.get_execution(execution.execution_id)
        assert retrieved.status == ExecutionStatus.EVALUATING.value

    def test_mark_iterating(self, repo):
        """Test marking execution as iterating."""
        execution = repo.create_execution(project_id="proj-001")

        repo.mark_started(execution.execution_id)
        repo.mark_iterating(execution.execution_id, iteration=2)

        retrieved = repo.get_execution(execution.execution_id)
        assert retrieved.status == ExecutionStatus.ITERATING.value
        assert retrieved.current_iteration == 2

    def test_mark_completed(self, repo):
        """Test marking execution as completed."""
        execution = repo.create_execution(project_id="proj-001")

        repo.mark_started(execution.execution_id)

        scorecard = {
            "structure_completeness": 4.0,
            "extraction_accuracy": 4.2,
            "fidelity_to_source": 4.1,
            "signal_to_noise": 4.0,
            "reusability": 4.0
        }

        repo.mark_completed(
            execution.execution_id,
            final_score=4.06,
            scorecard=scorecard,
            passed=True
        )

        retrieved = repo.get_execution(execution.execution_id)
        assert retrieved.status == ExecutionStatus.COMPLETED.value
        assert retrieved.completed_at is not None
        assert retrieved.final_score == 4.06
        assert retrieved.final_decision == "passed"
        assert retrieved.duration_seconds > 0

    def test_mark_failed(self, repo):
        """Test marking execution as failed."""
        execution = repo.create_execution(project_id="proj-001")

        repo.mark_started(execution.execution_id)
        repo.mark_failed(execution.execution_id, error_message="Evaluation crashed")

        retrieved = repo.get_execution(execution.execution_id)
        assert retrieved.status == ExecutionStatus.FAILED.value
        assert retrieved.completed_at is not None
        assert retrieved.error_message == "Evaluation crashed"

    def test_add_iteration_result(self, repo):
        """Test adding iteration result."""
        execution = repo.create_execution(project_id="proj-001")

        iteration_data = {
            "iteration_number": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "artifacts_evaluated": 3,
            "artifacts_passed": 2,
            "artifacts_failed": 1,
            "average_score": 3.5,
            "outcome": "improved"
        }

        repo.add_iteration_result(execution.execution_id, iteration_data)

        retrieved = repo.get_execution(execution.execution_id)
        assert len(retrieved.iterations) == 1
        assert retrieved.iterations[0]["iteration_number"] == 1

    def test_execution_is_complete(self, repo):
        """Test is_complete() check."""
        execution = repo.create_execution(project_id="proj-001")

        assert not execution.is_complete()

        execution.status = ExecutionStatus.COMPLETED.value
        assert execution.is_complete()

        execution.status = ExecutionStatus.FAILED.value
        assert execution.is_complete()

        execution.status = ExecutionStatus.CANCELLED.value
        assert execution.is_complete()

    def test_passed_quality_gate(self, repo):
        """Test quality gate check."""
        execution = repo.create_execution(
            project_id="proj-001",
            quality_threshold=3.0
        )

        execution.final_score = 2.5
        assert not execution.passed_quality_gate()

        execution.final_score = 3.0
        assert execution.passed_quality_gate()

        execution.final_score = 3.5
        assert execution.passed_quality_gate()


class TestExecutionScorecard:
    """Test ExecutionScorecard calculations."""

    def test_overall_score_calculation(self):
        """Test overall score calculation."""
        scorecard = ExecutionScorecard(
            structure_completeness=4.0,
            extraction_accuracy=4.0,
            fidelity_to_source=4.0,
            signal_to_noise=4.0,
            reusability=4.0
        )

        assert scorecard.overall() == 4.0

    def test_overall_score_with_mixed_scores(self):
        """Test overall with mixed scores."""
        scorecard = ExecutionScorecard(
            structure_completeness=5.0,
            extraction_accuracy=4.0,
            fidelity_to_source=3.0,
            signal_to_noise=4.0,
            reusability=3.0
        )

        expected = (5.0 + 4.0 + 3.0 + 4.0 + 3.0) / 5
        assert abs(scorecard.overall() - expected) < 0.01

    def test_scorecard_to_dict(self):
        """Test scorecard serialization."""
        scorecard = ExecutionScorecard(
            structure_completeness=4.2,
            extraction_accuracy=4.3,
            fidelity_to_source=4.1,
            signal_to_noise=4.0,
            reusability=4.2
        )

        data = scorecard.to_dict()

        assert data["structure_completeness"] == 4.2
        assert data["extraction_accuracy"] == 4.3
        assert data["overall"] > 4.0


class TestEvaluationExecutionLifecycle:
    """Test complete evaluation execution lifecycle."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def repo(self, temp_storage):
        """Create execution repository."""
        return EvaluationExecutionRepository(storage_dir=temp_storage / "executions")

    def test_complete_execution_lifecycle(self, repo):
        """Test full execution lifecycle: create → start → evaluate → complete."""

        # 1. Create execution
        execution = repo.create_execution(
            project_id="proj-complete-test",
            event_id="event-001",
            configuration="standard"
        )
        assert execution.status == ExecutionStatus.PENDING.value

        # 2. Start execution
        repo.mark_started(execution.execution_id)
        exe = repo.get_execution(execution.execution_id)
        assert exe.status == ExecutionStatus.RUNNING.value

        # 3. Move to evaluation
        repo.mark_evaluating(execution.execution_id)
        exe = repo.get_execution(execution.execution_id)
        assert exe.status == ExecutionStatus.EVALUATING.value

        # 4. Add iteration result
        iteration_data = {
            "iteration_number": 1,
            "timestamp": datetime.utcnow().isoformat(),
            "artifacts_evaluated": 3,
            "artifacts_passed": 3,
            "artifacts_failed": 0,
            "average_score": 4.2,
            "outcome": "success"
        }
        repo.add_iteration_result(execution.execution_id, iteration_data)

        # 5. Complete execution
        scorecard = {
            "structure_completeness": 4.2,
            "extraction_accuracy": 4.3,
            "fidelity_to_source": 4.1,
            "signal_to_noise": 4.2,
            "reusability": 4.2
        }
        repo.mark_completed(
            execution.execution_id,
            final_score=4.2,
            scorecard=scorecard,
            passed=True
        )

        # Verify final state
        final = repo.get_execution(execution.execution_id)
        assert final.status == ExecutionStatus.COMPLETED.value
        assert final.final_score == 4.2
        assert final.final_decision == "passed"
        assert len(final.iterations) == 1
        assert final.duration_seconds > 0
        assert final.is_complete()
        assert final.passed_quality_gate()

    def test_failed_execution_lifecycle(self, repo):
        """Test failed execution: create → start → fail."""

        execution = repo.create_execution(project_id="proj-fail-test")

        repo.mark_started(execution.execution_id)
        repo.mark_failed(
            execution.execution_id,
            error_message="Agent evaluation failed: no artifacts found"
        )

        final = repo.get_execution(execution.execution_id)
        assert final.status == ExecutionStatus.FAILED.value
        assert final.completed_at is not None
        assert final.error_message == "Agent evaluation failed: no artifacts found"
        assert final.is_complete()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
