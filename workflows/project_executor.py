"""Project executor that ties together evaluation results and project state.

This module avoids network calls and uses deterministic inputs so it can be
unit-tested without external dependencies. It assumes artifacts have already
been extracted; it only interprets evaluator outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from projects import ProjectDefinition
from projects.repository import ProjectRepository
from evaluation.hybrid_evaluator import HybridEvaluator
from evaluation.expert_review import ExpertReview


@dataclass
class ExecutionResult:
    """Outcome of a single evaluation iteration."""

    project_id: str
    passed: bool
    iterations_used: int
    scorecard: Dict
    suggestions: list
    status: str


class ProjectExecutor:
    """Evaluates a project using HybridEvaluator and updates repository state."""

    def __init__(
        self,
        repository: ProjectRepository,
        evaluator: Optional[HybridEvaluator] = None,
        *,
        max_iterations: int = 2,
    ) -> None:
        self.repository = repository
        self.evaluator = evaluator or HybridEvaluator()
        self.max_iterations = max_iterations

    def evaluate_once(
        self,
        project: ProjectDefinition,
        *,
        structure_metrics: Dict,
        extraction_metrics: Dict,
        fidelity_metrics: Dict,
        expert_review: Optional[ExpertReview] = None,
        iteration_index: int = 0,
    ) -> ExecutionResult:
        """Run a single evaluation pass and update project status."""
        result = self.evaluator.evaluate(
            structure_metrics=structure_metrics,
            extraction_metrics=extraction_metrics,
            fidelity_metrics=fidelity_metrics,
            expert_review=expert_review,
        )

        passed = bool(result["passed"])
        project.updated_at = project.updated_at  # no-op; keep signature explicit

        if passed:
            project.status = "ready_for_compilation"
        else:
            project.status = "iterating" if iteration_index + 1 < self.max_iterations else "failed"

        # Persist change
        self.repository.update(project)

        return ExecutionResult(
            project_id=project.id,
            passed=passed,
            iterations_used=iteration_index + 1,
            scorecard=result["scorecard"].__dict__,
            suggestions=result["suggestions"],
            status=project.status,
        )
