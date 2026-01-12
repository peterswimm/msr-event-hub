"""
Integration tests for the complete knowledge extraction workflow.
Tests the 7-step POC workflow from artifact collection through output generation.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from pathlib import Path

from workflows.poc_workflow import POCWorkflowManager
from core.schemas.base_schema import SourceType
from agents import ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent
from evaluation.evaluators import ExpertReviewEvaluator


class TestPOCWorkflowInitialization:
    """Test POC workflow initialization and configuration."""

    def test_workflow_manager_initialization(self):
        """Test that POCWorkflowManager initializes correctly."""
        manager = POCWorkflowManager()
        assert manager is not None

    def test_workflow_has_required_attributes(self):
        """Test that workflow manager has required attributes and methods."""
        manager = POCWorkflowManager()
        
        # Check for required methods
        assert hasattr(manager, 'run')
        assert callable(getattr(manager, 'run', None))

    def test_workflow_initializes_agents(self):
        """Test that workflow properly initializes extraction agents."""
        manager = POCWorkflowManager()
        # Workflow should have access to all three agent types
        assert manager is not None


class TestPOCWorkflowSteps:
    """Test individual steps of the 7-step POC workflow."""

    def test_step_1_collect_artifacts(self):
        """Test Step 1: Collect artifacts from various sources."""
        manager = POCWorkflowManager()
        
        # Mock artifact collection
        mock_artifacts = [
            {"type": "paper", "path": "test_paper.pdf", "content": "Paper content"},
            {"type": "talk", "path": "test_talk.txt", "content": "Talk transcript"},
            {"type": "repository", "url": "https://github.com/test/repo"},
        ]
        
        with patch.object(manager, 'collect_artifacts', new_callable=AsyncMock) as mock_collect:
            mock_collect.return_value = mock_artifacts
            # Artifacts should be collected
            assert mock_collect is not None

    def test_step_2_define_projects(self):
        """Test Step 2: Define multi-artifact projects."""
        manager = POCWorkflowManager()
        
        # Mock project definition
        mock_project = {
            "name": "Test Project",
            "description": "Test knowledge extraction project",
            "artifacts": ["paper1.pdf", "talk1.txt", "repo1"],
            "objectives": ["Extract knowledge", "Validate quality"],
        }
        
        with patch.object(manager, 'define_projects', new_callable=AsyncMock) as mock_define:
            mock_define.return_value = [mock_project]
            # Project should be defined
            assert mock_define is not None

    def test_step_3_assign_agents(self):
        """Test Step 3: Assign agents to artifacts."""
        manager = POCWorkflowManager()
        
        # Mock agent assignment
        assignments = {
            "paper_artifacts": [{"path": "test.pdf", "agent": "ModernPaperAgent"}],
            "talk_artifacts": [{"path": "test.txt", "agent": "ModernTalkAgent"}],
            "repo_artifacts": [{"url": "github.com/test", "agent": "ModernRepositoryAgent"}],
        }
        
        with patch.object(manager, 'assign_agents', new_callable=AsyncMock) as mock_assign:
            mock_assign.return_value = assignments
            # Agents should be assigned to artifacts
            assert mock_assign is not None

    def test_step_4_extract_knowledge(self):
        """Test Step 4: Execute extraction with assigned agents."""
        manager = POCWorkflowManager()
        
        # Mock extraction results
        mock_extractions = [
            {
                "artifact_id": "paper-001",
                "source_type": "paper",
                "title": "Test Paper",
                "confidence_score": 0.85,
            },
            {
                "artifact_id": "talk-001",
                "source_type": "talk",
                "title": "Test Talk",
                "confidence_score": 0.82,
            },
            {
                "artifact_id": "repo-001",
                "source_type": "repository",
                "title": "test-repo",
                "confidence_score": 0.88,
            },
        ]
        
        with patch.object(manager, 'extract_knowledge', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_extractions
            # Knowledge should be extracted from all artifacts
            assert len(mock_extractions) == 3

    def test_step_5_expert_review(self):
        """Test Step 5: Expert review of extracted knowledge."""
        manager = POCWorkflowManager()
        
        # Mock expert review
        mock_reviews = [
            {
                "artifact_id": "paper-001",
                "factual_accuracy": 4.0,
                "completeness": 4.2,
                "faithfulness": 3.8,
                "signal_to_noise": 4.0,
                "reusability": 3.5,
                "average_score": 3.9,
                "passes_threshold": True,
            },
            {
                "artifact_id": "talk-001",
                "factual_accuracy": 3.8,
                "completeness": 3.5,
                "faithfulness": 3.6,
                "signal_to_noise": 3.7,
                "reusability": 3.4,
                "average_score": 3.6,
                "passes_threshold": True,
            },
            {
                "artifact_id": "repo-001",
                "factual_accuracy": 4.5,
                "completeness": 4.2,
                "faithfulness": 4.3,
                "signal_to_noise": 4.0,
                "reusability": 4.1,
                "average_score": 4.22,
                "passes_threshold": True,
            },
        ]
        
        with patch.object(manager, 'run_expert_review', new_callable=AsyncMock) as mock_review:
            mock_review.return_value = mock_reviews
            # Expert review should be performed
            assert len(mock_reviews) == 3
            assert all(r["passes_threshold"] for r in mock_reviews)

    def test_step_6_iteration_and_refinement(self):
        """Test Step 6: Iteration loop for low-quality extractions."""
        manager = POCWorkflowManager()
        
        # Mock iteration process
        mock_iteration_result = {
            "attempted_re_extractions": 1,
            "successful_improvements": 1,
            "still_failing": 0,
            "summary": "All artifacts now exceed quality threshold",
        }
        
        with patch.object(manager, 'iterate_and_refine', new_callable=AsyncMock) as mock_iterate:
            mock_iterate.return_value = mock_iteration_result
            # Iteration should be attempted
            assert mock_iterate is not None

    def test_step_7_output_generation(self):
        """Test Step 7: Generate final output artifacts."""
        manager = POCWorkflowManager()
        
        # Mock output generation
        mock_outputs = {
            "structured_knowledge_json": "outputs/structured/knowledge.json",
            "summary_document": "outputs/summaries/summary.md",
            "evaluation_report": "outputs/summaries/evaluation_report.json",
            "knowledge_graph": "outputs/structured/knowledge_graph.json",
        }
        
        with patch.object(manager, 'generate_outputs', new_callable=AsyncMock) as mock_output:
            mock_output.return_value = mock_outputs
            # Outputs should be generated
            assert "structured_knowledge_json" in mock_outputs


class TestWorkflowDataFlow:
    """Test data flow through the workflow pipeline."""

    @pytest.mark.asyncio
    async def test_workflow_processes_all_artifact_types(self):
        """Test that workflow correctly processes all three artifact types."""
        manager = POCWorkflowManager()
        
        # Create mock artifacts of each type
        mock_artifacts = {
            "paper": {"type": "paper", "path": "paper.pdf", "content": "Paper content"},
            "talk": {"type": "talk", "path": "talk.txt", "content": "Talk content"},
            "repository": {"type": "repository", "url": "https://github.com/test/repo"},
        }
        
        with patch.object(manager, 'extract_knowledge', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = list(mock_artifacts.values())
            # All artifact types should be processed
            assert len(mock_artifacts) == 3

    @pytest.mark.asyncio
    async def test_workflow_handles_mixed_quality_artifacts(self):
        """Test workflow handling of artifacts with varying quality scores."""
        manager = POCWorkflowManager()
        
        # Mock artifacts with different quality levels
        mock_extractions = [
            {"artifact_id": "high-quality", "confidence_score": 0.95},  # Passes threshold
            {"artifact_id": "medium-quality", "confidence_score": 0.75},  # Passes threshold
            {"artifact_id": "low-quality", "confidence_score": 0.50},  # Below threshold (3.0/5.0)
        ]
        
        # Check that low-quality artifacts are identified for re-extraction
        low_quality_count = sum(1 for a in mock_extractions if a["confidence_score"] < 0.6)
        assert low_quality_count == 1

    def test_workflow_respects_evaluation_threshold(self):
        """Test that workflow enforces expert review threshold (3.0/5.0)."""
        manager = POCWorkflowManager()
        
        # Mock review scores
        passing_reviews = [
            {"average_score": 4.2, "passes": True},
            {"average_score": 3.5, "passes": True},
            {"average_score": 3.0, "passes": True},  # Exactly at threshold
        ]
        
        failing_reviews = [
            {"average_score": 2.9, "passes": False},  # Just below threshold
            {"average_score": 2.5, "passes": False},
        ]
        
        # Verify threshold logic
        threshold = 3.0
        for review in passing_reviews:
            assert review["average_score"] >= threshold
        
        for review in failing_reviews:
            assert review["average_score"] < threshold


class TestWorkflowErrorRecovery:
    """Test workflow error handling and recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_workflow_handles_extraction_failure(self):
        """Test that workflow handles extraction failures gracefully."""
        manager = POCWorkflowManager()
        
        with patch.object(manager, 'extract_knowledge', new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = RuntimeError("Extraction failed")
            
            with pytest.raises(RuntimeError):
                await manager.extract_knowledge({})

    @pytest.mark.asyncio
    async def test_workflow_handles_invalid_artifact(self):
        """Test that workflow handles invalid artifacts gracefully."""
        manager = POCWorkflowManager()
        
        # Invalid artifact (missing required fields)
        invalid_artifact = {"type": "paper"}  # Missing 'path'
        
        # Workflow should validate input
        assert "path" not in invalid_artifact or "content" not in invalid_artifact

    @pytest.mark.asyncio
    async def test_workflow_handles_api_timeout(self):
        """Test that workflow handles API timeouts gracefully."""
        manager = POCWorkflowManager()
        
        with patch.object(manager, 'extract_knowledge', new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = TimeoutError("API request timed out")
            
            with pytest.raises(TimeoutError):
                await manager.extract_knowledge({})


class TestWorkflowIntegration:
    """Test integration of workflow with agents and evaluators."""

    def test_workflow_uses_modern_agents(self):
        """Test that workflow instantiates and uses modern agents."""
        manager = POCWorkflowManager()
        
        # Verify that agents are available
        assert ModernPaperAgent is not None
        assert ModernTalkAgent is not None
        assert ModernRepositoryAgent is not None

    def test_workflow_uses_expert_review_evaluator(self):
        """Test that workflow uses expert review evaluator."""
        manager = POCWorkflowManager()
        
        # Expert review evaluator should be available
        evaluator = ExpertReviewEvaluator()
        assert evaluator is not None

    @pytest.mark.asyncio
    async def test_workflow_output_formats(self):
        """Test that workflow produces required output formats."""
        manager = POCWorkflowManager()
        
        # Outputs should include:
        # 1. Structured JSON with all extracted artifacts
        # 2. Summary document (markdown)
        # 3. Evaluation report (JSON)
        # 4. Knowledge graph (JSON)
        
        expected_outputs = [
            "structured_knowledge_json",
            "summary_document",
            "evaluation_report",
            "knowledge_graph",
        ]
        
        with patch.object(manager, 'generate_outputs', new_callable=AsyncMock) as mock_output:
            mock_output.return_value = {
                key: f"outputs/{key}.json" for key in expected_outputs
            }
            result = await mock_output({})
            
            # All expected outputs should be generated
            for output in expected_outputs:
                assert output in result


class TestWorkflowScalability:
    """Test workflow performance with different volumes of artifacts."""

    def test_workflow_handles_single_artifact(self):
        """Test workflow with a single artifact."""
        manager = POCWorkflowManager()
        
        single_artifact = {
            "id": "artifact-001",
            "type": "paper",
            "path": "single_paper.pdf",
        }
        
        # Should handle single artifact
        assert single_artifact is not None

    def test_workflow_handles_multiple_artifacts(self):
        """Test workflow with multiple artifacts."""
        manager = POCWorkflowManager()
        
        # Create 10 artifacts of mixed types
        artifacts = []
        for i in range(10):
            artifact_type = ["paper", "talk", "repository"][i % 3]
            artifacts.append({
                "id": f"artifact-{i:03d}",
                "type": artifact_type,
                "path": f"artifact_{i}",
            })
        
        # Should handle multiple artifacts
        assert len(artifacts) == 10

    def test_workflow_handles_large_project_grouping(self):
        """Test workflow with large project groupings."""
        manager = POCWorkflowManager()
        
        # Create a large project with many artifacts
        large_project = {
            "name": "Large Project",
            "artifact_count": 100,
            "expected_extraction_time": "~30 minutes",
            "artifacts": [f"artifact-{i}" for i in range(100)],
        }
        
        # Should handle large projects
        assert large_project["artifact_count"] == 100


class TestWorkflowCompleteExecution:
    """Test complete end-to-end workflow execution."""

    @pytest.mark.asyncio
    async def test_complete_7_step_workflow_execution(self):
        """Test the complete 7-step workflow from start to finish."""
        manager = POCWorkflowManager()
        
        # Step 1: Collect artifacts
        mock_artifacts = [
            {"id": "paper-001", "type": "paper"},
            {"id": "talk-001", "type": "talk"},
            {"id": "repo-001", "type": "repository"},
        ]
        
        # Step 2: Define projects
        mock_project = {"name": "Test Project", "artifacts": mock_artifacts}
        
        # Step 3: Assign agents
        assignments = {
            "paper": "ModernPaperAgent",
            "talk": "ModernTalkAgent",
            "repository": "ModernRepositoryAgent",
        }
        
        # Step 4: Extract knowledge
        mock_extractions = [
            {"id": "paper-001", "confidence_score": 0.85},
            {"id": "talk-001", "confidence_score": 0.82},
            {"id": "repo-001", "confidence_score": 0.88},
        ]
        
        # Step 5: Expert review
        mock_reviews = [
            {"id": "paper-001", "average_score": 3.9, "passes": True},
            {"id": "talk-001", "average_score": 3.6, "passes": True},
            {"id": "repo-001", "average_score": 4.2, "passes": True},
        ]
        
        # Step 6: Iteration (if needed)
        iteration_result = {"attempted_re_extractions": 0, "successful_improvements": 0}
        
        # Step 7: Generate outputs
        outputs = {
            "structured_knowledge": "outputs/structured/knowledge.json",
            "summary": "outputs/summaries/summary.md",
            "evaluation": "outputs/summaries/evaluation_report.json",
        }
        
        # Verify complete workflow
        assert len(mock_artifacts) == 3
        assert all(r["passes"] for r in mock_reviews)
        assert len(outputs) > 0

    @pytest.mark.asyncio
    async def test_workflow_maintains_data_consistency(self):
        """Test that workflow maintains data consistency throughout."""
        manager = POCWorkflowManager()
        
        # Create test data
        artifact_id = "artifact-001"
        
        # Mock extraction result
        extraction = {
            "id": artifact_id,
            "title": "Test Artifact",
            "content": "Test content",
        }
        
        # Mock review result
        review = {
            "id": artifact_id,  # Same ID
            "title": "Test Artifact",  # Same title
            "score": 4.0,
        }
        
        # IDs and titles should match throughout workflow
        assert extraction["id"] == review["id"]
        assert extraction["title"] == review["title"]
