"""Tests for validators module.

Comprehensive test suite for project and artifact validation functions.
Target: 20+ tests covering all validation scenarios.
"""

import pytest
from datetime import datetime

from projects import (
    ProjectDefinition,
    PaperReference,
    TalkReference,
    RepositoryReference,
    ExecutionConfig,
    validate_project_definition,
    validate_paper_reference,
    validate_talk_reference,
    validate_repository_reference,
    validate_execution_config,
    validate_projects_for_compilation,
    validate_project_artifacts_completeness,
    ValidationResult,
)
from src.core.projects.validators import (
    is_valid_id,
    is_valid_url,
    is_valid_year,
    is_valid_confidence_score,
    is_valid_iso_date,
)


# ===== Helper for PHASE B (Event-scoped projects) =====
def create_project(**kwargs):
    """Helper to create ProjectDefinition with required Phase B fields."""
    if 'event_id' not in kwargs:
        kwargs['event_id'] = 'event_default'
    if 'odata_type' not in kwargs:
        kwargs['odata_type'] = '#microsoft.graph.project'
    return ProjectDefinition(**kwargs)
)




# ===== Helper for PHASE B (Event-scoped projects) =====
def create_project(**kwargs):
    """Helper to create ProjectDefinition with required Phase B fields."""
    if 'event_id' not in kwargs:
        kwargs['event_id'] = 'event_default'
    if 'odata_type' not in kwargs:
        kwargs['odata_type'] = '#microsoft.graph.project'
    return create_project(**kwargs)
# ===== Basic Validator Tests =====

class TestBasicValidators:
    """Tests for basic validation functions."""
    
    def test_is_valid_id_valid(self):
        """Test valid IDs."""
        assert is_valid_id("valid_id_123")
        assert is_valid_id("test-id")
        assert is_valid_id("a")
        assert is_valid_id("ID_WITH_UNDERSCORES")
    
    def test_is_valid_id_invalid(self):
        """Test invalid IDs."""
        assert not is_valid_id("")
        assert not is_valid_id("id with spaces")
        assert not is_valid_id("id-with-$pecial")
        assert not is_valid_id(None)
        assert not is_valid_id(123)
    
    def test_is_valid_url_valid(self):
        """Test valid URLs."""
        assert is_valid_url("https://example.com")
        assert is_valid_url("http://example.com")
        assert is_valid_url("doi:10.1234/example")
        assert is_valid_url("file:///path/to/file")
    
    def test_is_valid_url_invalid(self):
        """Test invalid URLs."""
        assert not is_valid_url("not a url")
        assert not is_valid_url("example.com")
        assert not is_valid_url(None)
        assert not is_valid_url(123)
    
    def test_is_valid_year_valid(self):
        """Test valid years."""
        assert is_valid_year(2024)
        assert is_valid_year(1950)
        assert is_valid_year(2025)
    
    def test_is_valid_year_invalid(self):
        """Test invalid years."""
        assert not is_valid_year(1899)
        assert not is_valid_year(2050)
        assert not is_valid_year("2024")
    
    def test_is_valid_confidence_score_valid(self):
        """Test valid confidence scores."""
        assert is_valid_confidence_score(1.0)
        assert is_valid_confidence_score(3.5)
        assert is_valid_confidence_score(5.0)
        assert is_valid_confidence_score(2)
    
    def test_is_valid_confidence_score_invalid(self):
        """Test invalid confidence scores."""
        assert not is_valid_confidence_score(0.5)
        assert not is_valid_confidence_score(5.5)
        assert not is_valid_confidence_score("3.0")
    
    def test_is_valid_iso_date_valid(self):
        """Test valid ISO dates."""
        assert is_valid_iso_date("2024-01-01")
        assert is_valid_iso_date("2024-12-31T23:59:59")
        assert is_valid_iso_date(datetime.now().isoformat())
    
    def test_is_valid_iso_date_invalid(self):
        """Test invalid ISO dates."""
        assert not is_valid_iso_date("01/01/2024")
        assert not is_valid_iso_date("2024-13-01")
        assert not is_valid_iso_date("not a date")
        assert not is_valid_iso_date(None)


# ===== Reference Validation Tests =====

class TestPaperReferenceValidation:
    """Tests for paper reference validation."""
    
    def test_valid_paper(self):
        """Test validation of valid paper."""
        paper = PaperReference(
            id="paper_001",
            title="Test Paper",
            authors=["Author 1", "Author 2"],
            publication_venue="Conference 2024",
            publication_year=2024,
            doi_or_url="https://example.com/paper"
        )
        result = validate_paper_reference(paper)
        assert result.is_valid
    
    def test_paper_missing_id(self):
        """Test paper with missing ID."""
        paper = PaperReference(
            id="",
            title="Test Paper",
            authors=["Author"],
            publication_venue="Venue",
            publication_year=2024,
            doi_or_url="https://example.com"
        )
        result = validate_paper_reference(paper)
        assert not result.is_valid
        assert any("id" in str(e) for e in result.errors)
    
    def test_paper_missing_authors(self):
        """Test paper with no authors."""
        paper = PaperReference(
            id="paper_001",
            title="Test Paper",
            authors=[],
            publication_venue="Venue",
            publication_year=2024,
            doi_or_url="https://example.com"
        )
        result = validate_paper_reference(paper)
        assert not result.is_valid
    
    def test_paper_invalid_year(self):
        """Test paper with invalid year."""
        paper = PaperReference(
            id="paper_001",
            title="Test Paper",
            authors=["Author"],
            publication_venue="Venue",
            publication_year=1850,
            doi_or_url="https://example.com"
        )
        result = validate_paper_reference(paper)
        assert not result.is_valid
    
    def test_paper_invalid_url(self):
        """Test paper with invalid URL."""
        paper = PaperReference(
            id="paper_001",
            title="Test Paper",
            authors=["Author"],
            publication_venue="Venue",
            publication_year=2024,
            doi_or_url="not a url"
        )
        result = validate_paper_reference(paper)
        assert not result.is_valid


class TestTalkReferenceValidation:
    """Tests for talk reference validation."""
    
    def test_valid_talk(self):
        """Test validation of valid talk."""
        talk = TalkReference(
            id="talk_001",
            title="Test Talk",
            speaker="Test Speaker",
            event_name="Test Event",
            event_date="2024-01-01",
            video_url="https://example.com/video"
        )
        result = validate_talk_reference(talk)
        assert result.is_valid
    
    def test_talk_invalid_date(self):
        """Test talk with invalid date format."""
        talk = TalkReference(
            id="talk_001",
            title="Test Talk",
            speaker="Speaker",
            event_name="Event",
            event_date="01/01/2024"
        )
        result = validate_talk_reference(talk)
        assert not result.is_valid
    
    def test_talk_missing_speaker(self):
        """Test talk with missing speaker."""
        talk = TalkReference(
            id="talk_001",
            title="Test Talk",
            speaker="",
            event_name="Event",
            event_date="2024-01-01"
        )
        result = validate_talk_reference(talk)
        assert not result.is_valid


class TestRepositoryReferenceValidation:
    """Tests for repository reference validation."""
    
    def test_valid_repository(self):
        """Test validation of valid repository."""
        repo = RepositoryReference(
            id="repo_001",
            name="awesome-project",
            url="https://github.com/example/awesome-project",
            language="Python",
            stars=1000
        )
        result = validate_repository_reference(repo)
        assert result.is_valid
    
    def test_repository_invalid_url(self):
        """Test repository with invalid URL."""
        repo = RepositoryReference(
            id="repo_001",
            name="awesome-project",
            url="not-a-url",
            language="Python"
        )
        result = validate_repository_reference(repo)
        assert not result.is_valid
    
    def test_repository_missing_language(self):
        """Test repository with missing language."""
        repo = RepositoryReference(
            id="repo_001",
            name="awesome-project",
            url="https://github.com/example/awesome-project",
            language=""
        )
        result = validate_repository_reference(repo)
        assert not result.is_valid


# ===== Configuration Validation Tests =====

class TestExecutionConfigValidation:
    """Tests for execution config validation."""
    
    def test_valid_config(self):
        """Test validation of valid config."""
        config = ExecutionConfig(
            extraction_agent_type="paper",
            max_iterations=2,
            quality_threshold=3.0
        )
        result = validate_execution_config(config)
        assert result.is_valid
    
    def test_config_invalid_quality_threshold(self):
        """Test config with invalid quality threshold."""
        config = ExecutionConfig(quality_threshold=6.0)
        result = validate_execution_config(config)
        assert not result.is_valid
    
    def test_config_invalid_iterations(self):
        """Test config with invalid iterations."""
        config = ExecutionConfig(max_iterations=0)
        result = validate_execution_config(config)
        assert not result.is_valid


# ===== Project Validation Tests =====

class TestProjectDefinitionValidation:
    """Tests for complete project validation."""
    
    def test_valid_project(self):
        """Test validation of valid project."""
        project = create_project(
            id="project_001",
            name="Test Project",
            description="A test project",
            research_area="Testing",
            keywords=["test"],
            objectives=["Test objective"]
        )
        result = validate_project_definition(project)
        assert result.is_valid
    
    def test_project_with_valid_artifacts(self):
        """Test validation of project with artifacts."""
        project = create_project(
            id="project_001",
            name="Test Project",
            description="A test project",
            research_area="Testing"
        )
        paper = PaperReference(
            id="paper_001",
            title="Paper",
            authors=["Author"],
            publication_venue="Venue",
            publication_year=2024,
            doi_or_url="https://example.com"
        )
        project.add_paper(paper)
        
        result = validate_project_definition(project)
        assert result.is_valid
    
    def test_project_missing_name(self):
        """Test project with missing name."""
        project = create_project(
            id="project_001",
            name="",
            description="A test project",
            research_area="Testing"
        )
        result = validate_project_definition(project)
        assert not result.is_valid
    
    def test_project_with_invalid_paper(self):
        """Test project containing invalid paper."""
        project = create_project(
            id="project_001",
            name="Test Project",
            description="A test project",
            research_area="Testing"
        )
        # Manually add invalid paper (bypassing add_paper validation)
        invalid_paper = PaperReference(
            id="paper_001",
            title="Paper",
            authors=[],  # Invalid: no authors
            publication_venue="Venue",
            publication_year=2024,
            doi_or_url="https://example.com"
        )
        project.papers.append(invalid_paper)
        
        result = validate_project_definition(project)
        assert not result.is_valid
    
    def test_project_duplicate_artifact_ids(self):
        """Test project with duplicate artifact IDs."""
        project = create_project(
            id="project_001",
            name="Test Project",
            description="A test project",
            research_area="Testing"
        )
        paper1 = PaperReference(
            id="artifact_001",
            title="Paper 1",
            authors=["Author"],
            publication_venue="Venue",
            publication_year=2024,
            doi_or_url="https://example.com"
        )
        project.papers.append(paper1)
        
        talk = TalkReference(
            id="artifact_001",  # Duplicate ID
            title="Talk",
            speaker="Speaker",
            event_name="Event",
            event_date="2024-01-01"
        )
        project.talks.append(talk)
        
        result = validate_project_definition(project)
        assert not result.is_valid
    
    def test_project_missing_research_area(self):
        """Test project with missing research area."""
        project = create_project(
            id="project_001",
            name="Test Project",
            description="A test project",
            research_area=""
        )
        result = validate_project_definition(project)
        assert not result.is_valid
    
    def test_project_invalid_keywords(self):
        """Test project with invalid keywords."""
        project = create_project(
            id="project_001",
            name="Test Project",
            description="A test project",
            research_area="Testing",
            keywords=["valid", 123]  # Invalid: not all strings
        )
        result = validate_project_definition(project)
        assert not result.is_valid


# ===== Batch Validation Tests =====

class TestBatchValidation:
    """Tests for batch validation operations."""
    
    def test_validate_projects_for_compilation_all_valid(self):
        """Test batch validation with all valid projects."""
        projects = []
        for i in range(3):
            project = create_project(
                id=f"project_{i}",
                name=f"Project {i}",
                description="Test",
                research_area="Testing"
            )
            projects.append(project)
        
        valid, failed = validate_projects_for_compilation(projects)
        assert len(valid) == 3
        assert len(failed) == 0
    
    def test_validate_projects_for_compilation_mixed(self):
        """Test batch validation with mixed valid/invalid projects."""
        projects = []
        
        # Valid project
        valid_project = create_project(
            id="valid_project",
            name="Valid",
            description="Valid project",
            research_area="Testing"
        )
        projects.append(valid_project)
        
        # Invalid project
        invalid_project = create_project(
            id="invalid_project",
            name="",  # Invalid
            description="Invalid",
            research_area="Testing"
        )
        projects.append(invalid_project)
        
        valid, failed = validate_projects_for_compilation(projects)
        assert len(valid) == 1
        assert len(failed) == 1
    
    def test_validate_project_completeness_with_artifacts(self):
        """Test artifact completeness validation."""
        project = create_project(
            id="project_001",
            name="Test",
            description="Test",
            research_area="Testing"
        )
        paper = PaperReference(
            id="paper_001",
            title="Paper",
            authors=["Author"],
            publication_venue="Venue",
            publication_year=2024,
            doi_or_url="https://example.com"
        )
        project.add_paper(paper)
        
        result = validate_project_artifacts_completeness(project)
        assert result.is_valid
    
    def test_validate_project_completeness_no_artifacts(self):
        """Test artifact completeness validation with no artifacts."""
        project = create_project(
            id="project_001",
            name="Test",
            description="Test",
            research_area="Testing"
        )
        
        result = validate_project_artifacts_completeness(project)
        assert not result.is_valid


# ===== ValidationResult Tests =====

class TestValidationResult:
    """Tests for ValidationResult class."""
    
    def test_valid_result(self):
        """Test valid ValidationResult."""
        result = ValidationResult()
        assert result.is_valid
        assert result.error_count == 0
    
    def test_invalid_result_with_errors(self):
        """Test invalid ValidationResult."""
        result = ValidationResult()
        result.add_error("field1", "Error message")
        result.add_error("field2", "Another error")
        
        assert not result.is_valid
        assert result.error_count == 2
    
    def test_validation_result_string_representation(self):
        """Test string representation of results."""
        result = ValidationResult()
        assert "Valid" in str(result)
        
        result.add_error("field", "Error")
        assert "Invalid" in str(result)
        assert "field: Error" in str(result)
