"""Evaluation API routes (FastAPI optional)."""

from __future__ import annotations

try:  # pragma: no cover
    from fastapi import APIRouter
except ModuleNotFoundError:  # pragma: no cover
    APIRouter = None  # type: ignore

from evaluation.hybrid_evaluator import HybridEvaluator
from projects.repository import ProjectRepository
from workflows.project_executor import ProjectExecutor
from workflows.iteration_controller import IterationController


def score_payload(payload: dict, evaluator: HybridEvaluator | None = None) -> dict:
    evaluator = evaluator or HybridEvaluator()
    result = evaluator.evaluate(
        structure_metrics=payload.get("structure_metrics", {}),
        extraction_metrics=payload.get("extraction_metrics", {}),
        fidelity_metrics=payload.get("fidelity_metrics", {}),
        expert_review=None,
    )
    return {
        "passed": result["passed"],
        "scorecard": result["scorecard"].__dict__,
        "suggestions": result["suggestions"],
    }


def run_project_iterations(
    repo: ProjectRepository,
    payload: dict,
    *,
    evaluator: HybridEvaluator | None = None,
) -> dict:
    project_id = payload["project_id"]
    iterations = payload.get("iterations", [])
    if not iterations:
        raise ValueError("iterations payload is required")

    max_iterations = payload.get("max_iterations", len(iterations))
    project = repo.get(project_id)
    executor = ProjectExecutor(repo, evaluator=evaluator, max_iterations=max_iterations)
    controller = IterationController(executor, max_iterations=max_iterations)

    def metrics_provider(idx: int):
        capped_idx = min(idx, len(iterations) - 1)
        return iterations[capped_idx]

    result = controller.run_iterations(project, metrics_provider)
    return {
        "project_id": project_id,
        "passed": result.passed,
        "status": result.status,
        "iterations_used": result.iterations_used,
        "scorecard": result.scorecard,
        "suggestions": result.suggestions,
    }


def get_evaluation_router(repo: ProjectRepository | None = None):
    if APIRouter is None:
        return None
    router = APIRouter(prefix="/evaluation", tags=["evaluation"])
    evaluator = HybridEvaluator()

    @router.post("/score")
    def score(payload: dict):
        return score_payload(payload, evaluator)

    @router.post("/run")
    def run(payload: dict):
        if repo is None:
            raise ValueError("ProjectRepository is required for run endpoint")
        return run_project_iterations(repo, payload, evaluator=evaluator)

    return router
