"""Iteration controller for project evaluation loops.

Coordinates multiple evaluation passes until pass/fail decision.
"""

from __future__ import annotations

from typing import Dict, Optional, Callable

from src.core.projects import ProjectDefinition
from src.evaluation.expert_review import ExpertReview
from src.workflows.project_executor import ProjectExecutor, ExecutionResult


class IterationController:
    """Controls evaluation iterations for a project."""

    def __init__(
        self,
        executor: ProjectExecutor,
        *,
        max_iterations: int = 2,
    ) -> None:
        self.executor = executor
        self.max_iterations = max_iterations

    def run_iterations(
        self,
        project: ProjectDefinition,
        metrics_provider: Callable[[int], Dict[str, Dict]],
        expert_review_provider: Optional[Callable[[int], Optional[ExpertReview]]] = None,
    ) -> ExecutionResult:
        """Run evaluation up to max_iterations using provided metrics.

        metrics_provider(iteration_index) must return a dict with keys:
        - structure_metrics
        - extraction_metrics
        - fidelity_metrics
        """
        last_result: Optional[ExecutionResult] = None

        for i in range(self.max_iterations):
            metrics = metrics_provider(i)
            expert_review = expert_review_provider(i) if expert_review_provider else None

            last_result = self.executor.evaluate_once(
                project,
                structure_metrics=metrics["structure_metrics"],
                extraction_metrics=metrics["extraction_metrics"],
                fidelity_metrics=metrics["fidelity_metrics"],
                expert_review=expert_review,
                iteration_index=i,
            )

            if last_result.passed:
                break

        return last_result  # type: ignore[return-value]
