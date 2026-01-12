"""Tests for projects module models and core functionality.

Comprehensive test suite for ProjectDefinition, reference types, and
related model classes. Target: 30+ tests covering all model operations.
"""

import pytest
from datetime import datetime
from projects import (
    ProjectDefinition,
    PaperReference,
    TalkReference,
    RepositoryReference,
    ExecutionConfig,
    QualityMetrics,
    SourceType,
    ResearchMaturityStage,
    ProjectException,
    ProjectNotFoundError,
    InvalidArtifactError,
)


# ===== Helper for PHASE B (Event-scoped projects) =====
def create_project(**kwargs):
    """Helper to create ProjectDefinition with required Phase B fields.
    
    Automatically injects event_id and odata_type if not provided.
    """
    if "event_id" not in kwargs:
        kwargs["event_id"] = "event_default"
    if "odata_type" not in kwargs:
        kwargs["odata_type"] = "#microsoft.graph.project"
    return ProjectDefinition(**kwargs)


# ===== Fixtures =====

@pytest.fixture
def sample_paper():
    """Create a sample paper reference."""
    return PaperReference(
        id="paper_001",
        title="Attention Is All You Need",
        authors=["Vaswani, A.", "Shazeer, N.", "Parmar, N."],
        publication_venue="NeurIPS 2017",
        publication_year=2017,
        doi_or_url="https://arxiv.org/abs/1706.03762",
        abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks..."
    )


@pytest.fixture
def sample_talk():
    """Create a sample talk reference."""
    return TalkReference(
        id="talk_001",
        title="The Future of Distributed Systems",
        speaker="Martin Kleppmann",
        event_name="Strange Loop 2019",
        event_date="2019-09-12",
        video_url="https://www.youtube.com/watch?v=XXX",
        slides_url="https://example.com/slides.pdf",
        summary="Overview of emerging patterns in distributed systems..."
    )


@pytest.fixture
def sample_repository():
    """Create a sample repository reference."""
    return RepositoryReference(
        id="repo_001",
        name="awesome-vision",
        url="https://github.com/example/awesome-vision",
        language="Python",
        description="Curated list of computer vision resources",
        stars=5000,
        last_updated="2024-12-15"
    )


@pytest.fixture
def sample_project(sample_paper, sample_talk, sample_repository):
    """Create a sample project with artifacts."""
    project = create_project(
        id="project_001",
        event_id="event_001",
        name="Knowledge Extraction POC",
        description="Proof of concept for knowledge extraction",
        research_area="Machine Learning",
        objectives=["Extract key concepts", "Build knowledge graph"],
        keywords=["ml", "knowledge", "extraction"]
    )
    project.add_paper(sample_paper)
    project.add_talk(sample_talk)
    project.add_repository(sample_repository)
    return project


# ===== PaperReference Tests =====

class TestPaperReference:
    """Tests for PaperReference model."""
    
    def test_create_paper_reference(self, sample_paper):
        """Test creating a paper reference."""
        assert sample_paper.id == "paper_001"
        assert sample_paper.title == "Attention Is All You Need"
        assert len(sample_paper.authors) == 3
        assert sample_paper.publication_year == 2017
    
    def test_paper_to_dict(self, sample_paper):
        """Test serializing paper reference to dict."""
        data = sample_paper.to_dict()
        assert data["id"] == "paper_001"
        assert data["title"] == "Attention Is All You Need"
        assert data["publication_year"] == 2017
        assert "abstract" in data
    
    def test_paper_from_dict(self, sample_paper):
        """Test deserializing paper reference from dict."""
        data = sample_paper.to_dict()
        restored = PaperReference.from_dict(data)
        assert restored.id == sample_paper.id
        assert restored.title == sample_paper.title
        assert restored.publication_year == sample_paper.publication_year
    
    def test_paper_reference_minimal(self):
        """Test creating paper with minimal fields."""
        paper = PaperReference(
            id="minimal_paper",
            title="Minimal Paper",
            authors=["Author"],
            publication_venue="Journal",
            publication_year=2024,
            doi_or_url="https://example.com"
        )
        assert paper.abstract is None
        data = paper.to_dict()
        assert data["abstract"] is None


# ===== TalkReference Tests =====

class TestTalkReference:
    """Tests for TalkReference model."""
    
    def test_create_talk_reference(self, sample_talk):
        """Test creating a talk reference."""
        assert sample_talk.id == "talk_001"
        assert sample_talk.title == "The Future of Distributed Systems"
        assert sample_talk.speaker == "Martin Kleppmann"
        assert sample_talk.event_date == "2019-09-12"
    
    def test_talk_to_dict(self, sample_talk):
        """Test serializing talk reference to dict."""
        data = sample_talk.to_dict()
        assert data["id"] == "talk_001"
        assert data["speaker"] == "Martin Kleppmann"
        assert data["event_date"] == "2019-09-12"
    
    def test_talk_from_dict(self, sample_talk):
        """Test deserializing talk reference from dict."""
        data = sample_talk.to_dict()
        restored = TalkReference.from_dict(data)
        assert restored.id == sample_talk.id
        assert restored.speaker == sample_talk.speaker
        assert restored.event_date == sample_talk.event_date
    
    def test_talk_reference_minimal(self):
        """Test creating talk with minimal fields."""
        talk = TalkReference(
            id="minimal_talk",
            title="Minimal Talk",
            speaker="Speaker Name",
            event_name="Event",
            event_date="2024-01-01"
        )
        assert talk.video_url is None
        assert talk.slides_url is None


# ===== RepositoryReference Tests =====

class TestRepositoryReference:
    """Tests for RepositoryReference model."""
    
    def test_create_repository_reference(self, sample_repository):
        """Test creating a repository reference."""
        assert sample_repository.id == "repo_001"
        assert sample_repository.name == "awesome-vision"
        assert sample_repository.language == "Python"
        assert sample_repository.stars == 5000
    
    def test_repository_to_dict(self, sample_repository):
        """Test serializing repository reference to dict."""
        data = sample_repository.to_dict()
        assert data["id"] == "repo_001"
        assert data["name"] == "awesome-vision"
        assert data["language"] == "Python"
    
    def test_repository_from_dict(self, sample_repository):
        """Test deserializing repository reference from dict."""
        data = sample_repository.to_dict()
        restored = RepositoryReference.from_dict(data)
        assert restored.id == sample_repository.id
        assert restored.name == sample_repository.name
        assert restored.url == sample_repository.url


# ===== ExecutionConfig Tests =====

class TestExecutionConfig:
    """Tests for ExecutionConfig model."""
    
    def test_default_execution_config(self):
        """Test default execution config values."""
        config = ExecutionConfig()
        assert config.extraction_agent_type == "paper"
        assert config.max_iterations == 2
        assert config.quality_threshold == 3.0
        assert config.parallelization is True
        assert config.timeout_seconds == 300
    
    def test_custom_execution_config(self):
        """Test custom execution config."""
        config = ExecutionConfig(
            extraction_agent_type="talk",
            max_iterations=3,
            quality_threshold=4.0,
            parallelization=False,
            timeout_seconds=600
        )
        assert config.extraction_agent_type == "talk"
        assert config.max_iterations == 3
        assert config.quality_threshold == 4.0
    
    def test_execution_config_serialization(self):
        """Test execution config to_dict and from_dict."""
        config = ExecutionConfig(max_iterations=5)
        data = config.to_dict()
        restored = ExecutionConfig.from_dict(data)
        assert restored.max_iterations == 5


# ===== QualityMetrics Tests =====

class TestQualityMetrics:
    """Tests for QualityMetrics model."""
    
    def test_default_quality_metrics(self):
        """Test default quality metrics."""
        metrics = QualityMetrics()
        assert metrics.total_artifacts == 0
        assert metrics.artifacts_reviewed == 0
        assert metrics.average_confidence == 0.0
        assert metrics.average_coverage == 0.0
    
    def test_quality_metrics_with_values(self):
        """Test quality metrics with custom values."""
        now = datetime.now()
        metrics = QualityMetrics(
            total_artifacts=10,
            artifacts_reviewed=8,
            average_confidence=4.2,
            average_coverage=0.95,
            last_updated=now
        )
        assert metrics.total_artifacts == 10
        assert metrics.artifacts_reviewed == 8
        assert metrics.average_confidence == 4.2
    
    def test_quality_metrics_serialization(self):
        """Test quality metrics serialization with datetime."""
        metrics = QualityMetrics(
            total_artifacts=5,
            average_confidence=3.5,
            last_updated=datetime.now()
        )
        data = metrics.to_dict()
        restored = QualityMetrics.from_dict(data)
        assert restored.total_artifacts == 5
        assert restored.average_confidence == 3.5


# ===== ProjectDefinition Tests =====

class TestProjectDefinition:
    """Tests for ProjectDefinition model."""
    
    def test_create_empty_project(self):
        """Test creating an empty project."""
        project = create_project(
            id="test_project",
            name="Test Project",
            description="A test project",
            research_area="Testing"
        )
        assert project.id == "test_project"
        assert project.name == "Test Project"
        assert project.artifact_count() == 0
        assert len(project.papers) == 0
        assert len(project.talks) == 0
    
    def test_project_add_paper(self, sample_project, sample_paper):
        """Test adding a paper to a project."""
        initial_count = sample_project.artifact_count()
        new_paper = PaperReference(
            id="paper_002",
            title="Another Paper",
            authors=["Author"],
            publication_venue="Conference",
            publication_year=2024,
            doi_or_url="https://example.com"
        )
        sample_project.add_paper(new_paper)
        assert sample_project.artifact_count() == initial_count + 1
    
    def test_project_add_talk(self, sample_project, sample_talk):
        """Test adding a talk to a project."""
        initial_count = sample_project.artifact_count()
        new_talk = TalkReference(
            id="talk_002",
            title="Another Talk",
            speaker="Another Speaker",
            event_name="Another Event",
            event_date="2024-01-01"
        )
        sample_project.add_talk(new_talk)
        assert sample_project.artifact_count() == initial_count + 1
    
    def test_project_add_repository(self, sample_project):
        """Test adding a repository to a project."""
        initial_count = sample_project.artifact_count()
        new_repo = RepositoryReference(
            id="repo_002",
            name="another-repo",
            url="https://github.com/example/another-repo",
            language="Java"
        )
        sample_project.add_repository(new_repo)
        assert sample_project.artifact_count() == initial_count + 1
    
    def test_project_remove_paper(self, sample_project):
        """Test removing a paper from a project."""
        initial_count = sample_project.artifact_count()
        paper_id = sample_project.papers[0].id
        sample_project.remove_paper(paper_id)
        assert sample_project.artifact_count() == initial_count - 1
        assert not any(p.id == paper_id for p in sample_project.papers)
    
    def test_project_remove_talk(self, sample_project):
        """Test removing a talk from a project."""
        initial_count = sample_project.artifact_count()
        talk_id = sample_project.talks[0].id
        sample_project.remove_talk(talk_id)
        assert sample_project.artifact_count() == initial_count - 1
    
    def test_project_remove_repository(self, sample_project):
        """Test removing a repository from a project."""
        initial_count = sample_project.artifact_count()
        repo_id = sample_project.repositories[0].id
        sample_project.remove_repository(repo_id)
        assert sample_project.artifact_count() == initial_count - 1
    
    def test_project_duplicate_paper_error(self, sample_project, sample_paper):
        """Test that adding duplicate paper raises error."""
        with pytest.raises(ValueError, match="already exists"):
            sample_project.add_paper(sample_paper)
    
    def test_project_duplicate_talk_error(self, sample_project, sample_talk):
        """Test that adding duplicate talk raises error."""
        with pytest.raises(ValueError, match="already exists"):
            sample_project.add_talk(sample_talk)
    
    def test_project_artifact_count(self, sample_project):
        """Test artifact count calculation."""
        count = sample_project.artifact_count()
        assert count == 3  # 1 paper, 1 talk, 1 repository
    
    def test_project_maturity_stage(self):
        """Test project maturity stage."""
        project = create_project(
            id="p1",
            name="Project",
            description="Desc",
            research_area="Area",
            maturity_stage=ResearchMaturityStage.VALIDATED
        )
        assert project.maturity_stage == ResearchMaturityStage.VALIDATED
    
    def test_project_status_tracking(self):
        """Test project status tracking."""
        project = create_project(
            id="p1",
            name="Project",
            description="Desc",
            research_area="Area",
            status="created"
        )
        assert project.status == "created"
        project.status = "active"
        assert project.status == "active"
    
    def test_project_execution_config(self):
        """Test project execution configuration."""
        config = ExecutionConfig(max_iterations=5)
        project = create_project(
            id="p1",
            name="Project",
            description="Desc",
            research_area="Area",
            execution_config=config
        )
        assert project.execution_config.max_iterations == 5
    
    def test_project_keywords_and_objectives(self):
        """Test keywords and objectives."""
        project = create_project(
            id="p1",
            name="Project",
            description="Desc",
            research_area="Area",
            keywords=["ml", "vision"],
            objectives=["Build model", "Evaluate results"]
        )
        assert len(project.keywords) == 2
        assert len(project.objectives) == 2
        assert "ml" in project.keywords


# ===== Serialization Tests =====

class TestSerialization:
    """Tests for model serialization and deserialization."""
    
    def test_project_to_dict(self, sample_project):
        """Test serializing full project to dict."""
        data = sample_project.to_dict()
        assert data["id"] == sample_project.id
        assert data["name"] == sample_project.name
        assert len(data["papers"]) == 1
        assert len(data["talks"]) == 1
        assert len(data["repositories"]) == 1
    
    def test_project_from_dict(self, sample_project):
        """Test deserializing project from dict."""
        data = sample_project.to_dict()
        restored = ProjectDefinition.from_dict(data)
        assert restored.id == sample_project.id
        assert restored.name == sample_project.name
        assert restored.artifact_count() == sample_project.artifact_count()
        assert len(restored.papers) == 1
        assert len(restored.talks) == 1
    
    def test_roundtrip_serialization(self, sample_project):
        """Test roundtrip serialization (object -> dict -> object)."""
        data = sample_project.to_dict()
        restored = ProjectDefinition.from_dict(data)
        data2 = restored.to_dict()
        
        # Both serializations should be equivalent
        assert data["id"] == data2["id"]
        assert data["name"] == data2["name"]
        assert len(data["papers"]) == len(data2["papers"])
    
    def test_datetime_serialization(self):
        """Test datetime serialization in project."""
        now = datetime.now()
        project = create_project(
            id="p1",
            name="Project",
            description="Desc",
            research_area="Area",
            created_at=now,
            updated_at=now
        )
        data = project.to_dict()
        restored = ProjectDefinition.from_dict(data)
        
        # Datetime should round-trip correctly
        assert abs((restored.created_at - now).total_seconds()) < 0.001


# ===== Integration Tests =====

class TestProjectIntegration:
    """Integration tests for complete project workflows."""
    
    def test_complete_project_workflow(self):
        """Test a complete project creation and population workflow."""
        # Create project
        project = create_project(
            id="workflow_test",
            name="Complete Workflow",
            description="Test complete workflow",
            research_area="Integration Testing",
            keywords=["testing", "workflow"],
            objectives=["Create and populate project"]
        )
        
        # Add multiple artifacts
        for i in range(3):
            paper = PaperReference(
                id=f"paper_{i}",
                title=f"Paper {i}",
                authors=["Author"],
                publication_venue="Venue",
                publication_year=2024,
                doi_or_url=f"https://example.com/{i}"
            )
            project.add_paper(paper)
        
        assert project.artifact_count() == 3
        assert len(project.papers) == 3
    
    def test_quality_metrics_update_workflow(self):
        """Test updating quality metrics in a project."""
        project = create_project(
            id="metrics_test",
            name="Metrics Test",
            description="Test metrics",
            research_area="Metrics",
            quality_metrics=QualityMetrics(
                total_artifacts=5,
                artifacts_reviewed=3,
                average_confidence=4.1
            )
        )
        
        assert project.quality_metrics.total_artifacts == 5
        assert project.quality_metrics.artifacts_reviewed == 3
        
        # Update metrics
        project.quality_metrics.artifacts_reviewed = 5
        assert project.quality_metrics.artifacts_reviewed == 5
