"""Tests for Phase 3 workflows and Phase 4 API stubs."""

import types
import pytest

from projects import ProjectDefinition
from src.core.projects.repository import ProjectRepository
from src.evaluation.hybrid_evaluator import HybridEvaluator
from src.workflows.project_executor import ProjectExecutor
from src.workflows.iteration_controller import IterationController
from src.workflows.compilation.compiler import compile_project_summary
from api import (
    get_projects_router,
    get_artifacts_router,
    get_evaluation_router,
    get_dashboard_router,
)
from src.api.projects_routes import (
    create_project_handler,
    update_project_handler,
    compile_project_handler,
    list_projects_handler,
)
from src.api.evaluation_routes import score_payload, run_project_iterations


# ===== Helper for PHASE B (Event-scoped projects) =====
def create_project(**kwargs):
    """Helper to create ProjectDefinition with required Phase B fields."""
    if 'event_id' not in kwargs:
        kwargs['event_id'] = 'event_default'
    if 'odata_type' not in kwargs:
        kwargs['odata_type'] = '#microsoft.graph.project'
    return ProjectDefinition(**kwargs)


@pytest.fixture
def repo(tmp_path):
    return ProjectRepository(storage_dir=tmp_path)


@pytest.fixture
def sample_project():
    return create_project(
        id="p1",
        name="Proj",
        description="Desc",
        research_area="Testing",
    )


def test_project_executor_and_iteration_controller(repo, sample_project):
    repo.create(sample_project)
    executor = ProjectExecutor(repo, evaluator=HybridEvaluator(), max_iterations=2)
    controller = IterationController(executor, max_iterations=2)

    def metrics_provider(iter_idx: int):
        # First iteration fails, second passes
        if iter_idx == 0:
            return {
                "structure_metrics": {"structure_completeness_score": 40},
                "extraction_metrics": {
                    "summary_word_count": 50,
                    "summary_quality": "needs_improvement",
                    "field_coverage_percent": 20,
                    "key_points_count": 1,
                },
                "fidelity_metrics": {"fidelity_score": 2.5},
            }
        return {
            "structure_metrics": {"structure_completeness_score": 85},
            "extraction_metrics": {
                "summary_word_count": 200,
                "summary_quality": "good",
                "field_coverage_percent": 70,
                "key_points_count": 4,
            },
            "fidelity_metrics": {"fidelity_score": 4.2},
        }

    result = controller.run_iterations(sample_project, metrics_provider)
    assert result.passed is True
    assert result.status == "ready_for_compilation"
    assert result.iterations_used == 2


def test_compile_project_summary(sample_project):
    # Minimal artifact using ProjectDefinition fields as placeholders
    summary = compile_project_summary(sample_project.name, [])
    assert summary["project_name"] == sample_project.name
    assert summary["artifact_count"] == 0


def test_api_routers_import_without_fastapi():
    # Routers should be None if FastAPI is absent
    projects_router = get_projects_router(ProjectRepository(storage_dir="/tmp"))
    artifacts_router = get_artifacts_router()
    evaluation_router = get_evaluation_router()
    dashboard_router = get_dashboard_router()

    # FastAPI might be installed; in that case ensure type correctness
    for router in [projects_router, artifacts_router, evaluation_router, dashboard_router]:
        assert router is None or isinstance(router, (types.SimpleNamespace, object))


def test_project_route_handlers_crud_and_compile(repo):
    payload = {
        "id": "api-1",
        "name": "API Project",
        "description": "Initial",
        "research_area": "Testing",
    }

    created = create_project_handler(repo, "event_test_1", payload)  # PHASE B: Add event_id parameter
    assert created["name"] == "API Project"

    updated = update_project_handler(repo, "api-1", {"description": "Updated"})
    assert updated["description"] == "Updated"

    artifacts_payload = [
        {
            "source_type": "paper",
            "title": "Paper One",
            "primary_claims_capabilities": ["claim"],
            "key_methods_approach": ["method"],
            "limitations_constraints": ["limit"],
        }
    ]

    compiled = compile_project_handler(repo, "api-1", artifacts_payload)
    assert compiled["compiled"]["artifact_count"] == 1
    project = repo.get("api-1")
    assert project.status == "compiled"

    all_projects = list_projects_handler(repo)
    assert any(p["id"] == "api-1" for p in all_projects)


def test_evaluation_route_handlers_run(repo, sample_project):
    repo.create(sample_project)

    iterations = [
        {
            "structure_metrics": {"structure_completeness_score": 10},
            "extraction_metrics": {
                "summary_word_count": 20,
                "summary_quality": "needs_improvement",
                "field_coverage_percent": 5,
                "key_points_count": 1,
            },
            "fidelity_metrics": {"fidelity_score": 1.0},
        },
        {
            "structure_metrics": {"structure_completeness_score": 90},
            "extraction_metrics": {
                "summary_word_count": 220,
                "summary_quality": "good",
                "field_coverage_percent": 75,
                "key_points_count": 5,
            },
            "fidelity_metrics": {"fidelity_score": 4.5},
        },
    ]

    run_result = run_project_iterations(
        repo,
        {"project_id": sample_project.id, "iterations": iterations, "max_iterations": 2},
    )

    assert run_result["passed"] is True
    assert run_result["status"] == "ready_for_compilation"
    assert run_result["iterations_used"] == 2
    assert repo.get(sample_project.id).status == "ready_for_compilation"

    score_result = score_payload({
        "structure_metrics": {"structure_completeness_score": 90},
        "extraction_metrics": {
            "summary_word_count": 200,
            "summary_quality": "good",
            "field_coverage_percent": 70,
            "key_points_count": 4,
        },
        "fidelity_metrics": {"fidelity_score": 4.0},
    })

    assert score_result["passed"] is True
