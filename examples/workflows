"""Workflow execution example: End-to-end project evaluation with iteration.

Demonstrates complete workflow from project creation through evaluation,
iteration, and result tracking without requiring FastAPI server.

Usage:
    python workflow_example.py [--storage-dir ./workflow_example_data]
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from main import ApplicationContext
from core.workflow_status import EvaluationExecutionRepository, ExecutionStatus
from projects import ProjectDefinition, ProjectStatus
from core.event_repository import Event, Session


def create_demo_project(app_context: ApplicationContext, event_id: str) -> ProjectDefinition:
    """Create a demo project for evaluation."""
    project = ProjectDefinition(
        project_id="workflow-demo-proj",
        event_id=event_id,
        name="Vision AI Framework Analysis",
        description="Comprehensive analysis of modern vision AI frameworks",
        artifacts_count=3,
        status=ProjectStatus.CREATED.value,
        created_at=datetime.utcnow().isoformat(),
        odata_type="microsoft.graph.project",
        odata_etag="1"
    )
    
    # Save project
    app_context.project_repo.save(project.project_id, project.to_dict())
    return project


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n→ {title}")
    print(f"  {'-'*66}")


async def main():
    """Run complete workflow example."""
    
    # Configuration
    storage_dir = Path("./workflow_example_data")
    storage_dir.mkdir(exist_ok=True)
    
    print_section("PHASE D: WORKFLOW INTEGRATION EXAMPLE")
    print("This example demonstrates project evaluation with iteration.\n")
    
    # =========================================================================
    # 1. Initialize Application Context
    # =========================================================================
    
    print_subsection("1. Initialize Application Context")
    app_context = ApplicationContext(storage_root=storage_dir)
    print("✓ ApplicationContext initialized")
    print(f"  Storage: {app_context.storage_root}")
    print(f"  ProjectExecutor: {app_context.executor is not None}")
    print(f"  IterationController: {app_context.iteration_controller is not None}")
    print(f"  HybridEvaluator: {app_context.evaluator is not None}")
    
    # =========================================================================
    # 2. Create Event and Project
    # =========================================================================
    
    print_subsection("2. Create Event and Project")
    
    event = Event.create()
    app_context.event_repo.save(event.id, event.to_dict())
    print(f"✓ Event created: {event.id}")
    
    session = Session.create(event_id=event.id)
    app_context.session_repo.save(session.id, session.to_dict())
    print(f"✓ Session created: {session.id}")
    
    project = create_demo_project(app_context, event.id)
    print(f"✓ Project created: {project.project_id}")
    print(f"  Name: {project.name}")
    print(f"  Event: {project.event_id}")
    
    # =========================================================================
    # 3. Initialize Execution Repository
    # =========================================================================
    
    print_subsection("3. Initialize Evaluation Execution")
    
    execution_repo = EvaluationExecutionRepository(
        storage_dir=storage_dir / "executions"
    )
    
    # Create new execution
    execution = execution_repo.create_execution(
        project_id=project.project_id,
        event_id=event.id,
        configuration="standard",
        max_iterations=2,
        quality_threshold=3.0
    )
    
    print(f"✓ Execution created: {execution.execution_id}")
    print(f"  Configuration: {execution.configuration}")
    print(f"  Max iterations: {execution.max_iterations}")
    print(f"  Quality threshold: {execution.quality_threshold}")
    
    # =========================================================================
    # 4. Start Execution
    # =========================================================================
    
    print_subsection("4. Start Execution")
    
    execution_repo.mark_started(execution.execution_id)
    exe = execution_repo.get_execution(execution.execution_id)
    
    print(f"✓ Execution started")
    print(f"  Status: {exe.status}")
    print(f"  Started at: {exe.started_at}")
    
    # =========================================================================
    # 5. Evaluation Phase (Simulated)
    # =========================================================================
    
    print_subsection("5. Evaluation Phase (Simulated)")
    
    execution_repo.mark_evaluating(execution.execution_id)
    exe = execution_repo.get_execution(execution.execution_id)
    print(f"✓ Moved to evaluation phase")
    print(f"  Status: {exe.status}")
    
    # Simulate evaluation results
    print("\n  Evaluating artifacts...")
    artifact_scores = [
        {
            "artifact_id": "artifact-vision-01",
            "title": "Vision Transformer Paper Summary",
            "extraction_score": 4.2,
            "completeness_score": 4.1,
            "fidelity_score": 4.0,
            "overall_score": 4.1,
            "status": "passed"
        },
        {
            "artifact_id": "artifact-vision-02",
            "title": "YOLO Real-time Detection Repository",
            "extraction_score": 3.5,
            "completeness_score": 3.2,
            "fidelity_score": 3.4,
            "overall_score": 3.4,
            "status": "failed"
        },
        {
            "artifact_id": "artifact-vision-03",
            "title": "Vision Keynote Transcript",
            "extraction_score": 4.3,
            "completeness_score": 4.2,
            "fidelity_score": 4.1,
            "overall_score": 4.2,
            "status": "passed"
        }
    ]
    
    for score in artifact_scores:
        status_icon = "✓" if score["status"] == "passed" else "✗"
        print(f"    {status_icon} {score['title']}: {score['overall_score']:.1f}/5.0")
    
    # =========================================================================
    # 6. Iteration Phase (Simulated)
    # =========================================================================
    
    print_subsection("6. Iteration Phase (Simulated)")
    
    execution_repo.mark_iterating(execution.execution_id, iteration=1)
    exe = execution_repo.get_execution(execution.execution_id)
    print(f"✓ Moved to iteration phase")
    print(f"  Iteration: {exe.current_iteration}")
    
    # Record first iteration
    iteration_1 = {
        "iteration_number": 1,
        "timestamp": datetime.utcnow().isoformat(),
        "artifacts_evaluated": 3,
        "artifacts_passed": 2,
        "artifacts_failed": 1,
        "average_score": 3.9,
        "overall_score": 3.9,
        "outcome": "improved",
        "artifact_scores": artifact_scores,
        "suggestions": [
            "YOLO artifact needs more implementation details",
            "Expand key_points with specific metrics",
            "Include performance benchmarks"
        ]
    }
    
    execution_repo.add_iteration_result(execution.execution_id, iteration_1)
    print(f"\n  ✓ Iteration 1 completed")
    print(f"    Evaluated: {iteration_1['artifacts_evaluated']} artifacts")
    print(f"    Passed: {iteration_1['artifacts_passed']}, Failed: {iteration_1['artifacts_failed']}")
    print(f"    Average score: {iteration_1['average_score']:.1f}/5.0")
    
    # Re-evaluate failed artifact (simulated)
    print(f"\n  Re-extracting failed artifact with feedback...")
    artifact_scores[1]["extraction_score"] = 4.0
    artifact_scores[1]["completeness_score"] = 4.1
    artifact_scores[1]["fidelity_score"] = 4.0
    artifact_scores[1]["overall_score"] = 4.05
    artifact_scores[1]["status"] = "passed"
    
    iteration_2 = {
        "iteration_number": 2,
        "timestamp": datetime.utcnow().isoformat(),
        "artifacts_evaluated": 1,
        "artifacts_passed": 1,
        "artifacts_failed": 0,
        "average_score": 4.05,
        "overall_score": 4.15,
        "outcome": "success",
        "artifact_scores": [artifact_scores[1]],
        "improved_artifacts": [
            {
                "artifact_id": "artifact-vision-02",
                "previous_score": 3.4,
                "new_score": 4.05,
                "improvement": 0.65
            }
        ]
    }
    
    execution_repo.add_iteration_result(execution.execution_id, iteration_2)
    print(f"  ✓ Iteration 2 completed")
    print(f"    Evaluated: {iteration_2['artifacts_evaluated']} artifacts")
    print(f"    All artifacts passed!")
    
    # =========================================================================
    # 7. Completion
    # =========================================================================
    
    print_subsection("7. Completion")
    
    scorecard = {
        "structure_completeness": 4.1,
        "extraction_accuracy": 4.15,
        "fidelity_to_source": 4.05,
        "signal_to_noise": 4.1,
        "reusability": 4.2
    }
    
    execution_repo.mark_completed(
        execution.execution_id,
        final_score=4.12,
        scorecard=scorecard,
        passed=True
    )
    
    final = execution_repo.get_execution(execution.execution_id)
    print(f"✓ Execution completed")
    print(f"  Status: {final.status}")
    print(f"  Final decision: {final.final_decision}")
    print(f"  Final score: {final.final_score:.2f}/5.0")
    print(f"  Iterations used: {len(final.iterations)}/{final.max_iterations}")
    print(f"  Duration: {final.duration_seconds:.1f} seconds")
    
    # =========================================================================
    # 8. Results and Metrics
    # =========================================================================
    
    print_subsection("8. Results and Metrics")
    
    print(f"\n✓ Scorecard:")
    for dimension, score in scorecard.items():
        print(f"    {dimension}: {score:.2f}/5.0")
    
    print(f"\n✓ Execution Summary:")
    print(f"    Project: {final.project_id}")
    print(f"    Event: {final.event_id}")
    print(f"    Configuration: {final.configuration}")
    print(f"    Quality threshold: {final.quality_threshold}")
    print(f"    Passed quality gate: {final.passed_quality_gate()}")
    
    # =========================================================================
    # 9. Project Execution History
    # =========================================================================
    
    print_subsection("9. Execution History for Project")
    
    history = execution_repo.list_by_project(project.project_id)
    print(f"✓ Found {len(history)} execution(s) for this project:")
    
    for exe in history:
        print(f"\n    Execution: {exe.execution_id}")
        print(f"    Status: {exe.status}")
        print(f"    Score: {exe.final_score:.2f}/5.0")
        print(f"    Created: {exe.created_at}")
    
    # =========================================================================
    # 10. Summary Statistics
    # =========================================================================
    
    print_subsection("10. Summary Statistics")
    
    all_executions = execution_repo.list_all()
    completed = execution_repo.list_by_status(ExecutionStatus.COMPLETED.value)
    
    print(f"✓ Workflow Statistics:")
    print(f"    Total executions: {len(all_executions)}")
    print(f"    Completed: {len(completed)}")
    print(f"    Success rate: {len(completed)/max(len(all_executions), 1)*100:.0f}%")
    
    if completed:
        avg_score = sum(e.final_score for e in completed) / len(completed)
        avg_iterations = sum(len(e.iterations) for e in completed) / len(completed)
        print(f"    Average final score: {avg_score:.2f}/5.0")
        print(f"    Average iterations: {avg_iterations:.1f}")
    
    print_section("WORKFLOW INTEGRATION EXAMPLE COMPLETE")
    print(f"\nData saved to: {storage_dir}")
    print("✓ All components working together successfully!\n")


if __name__ == "__main__":
    asyncio.run(main())
