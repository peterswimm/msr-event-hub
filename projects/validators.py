"""Validation functions for projects and artifacts.

Provides comprehensive validation for ProjectDefinition, reference types,
and execution configuration. Enables pre-flight validation before storage
and processing.
"""

from typing import List, Tuple
import re
from datetime import datetime

from projects.models import (
    ProjectDefinition,
    PaperReference,
    TalkReference,
    RepositoryReference,
    ExecutionConfig,
)
from projects.exceptions import InvalidArtifactError, InvalidProjectConfigError


class ValidationError:
    """Represents a single validation error."""
    
    def __init__(self, field: str, message: str):
        """Initialize validation error.
        
        Args:
            field: The field that failed validation.
            message: Description of the validation failure.
        """
        self.field = field
        self.message = message
    
    def __repr__(self) -> str:
        return f"ValidationError({self.field}: {self.message})"
    
    def __str__(self) -> str:
        return f"{self.field}: {self.message}"


class ValidationResult:
    """Result of validation with errors collected."""
    
    def __init__(self, is_valid: bool = True, errors: List[ValidationError] = None):
        """Initialize validation result.
        
        Args:
            is_valid: Whether validation passed.
            errors: List of validation errors.
        """
        self.is_valid = is_valid
        self.errors = errors or []
    
    @property
    def error_count(self) -> int:
        """Get number of errors."""
        return len(self.errors)
    
    def add_error(self, field: str, message: str) -> None:
        """Add a validation error.
        
        Args:
            field: The field that failed.
            message: Description of the failure.
        """
        self.is_valid = False
        self.errors.append(ValidationError(field, message))
    
    def __str__(self) -> str:
        if self.is_valid:
            return "✓ Valid"
        return f"✗ Invalid ({self.error_count} errors):\n" + \
               "\n".join(f"  {err}" for err in self.errors)


# ===== Basic Validators =====

def is_valid_id(value: str) -> bool:
    """Check if a value is a valid ID.
    
    IDs must be non-empty strings, alphanumeric with underscores/hyphens.
    
    Args:
        value: The ID to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(value, str):
        return False
    if not value:
        return False
    # Allow alphanumeric, underscore, hyphen
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', value))


def is_valid_url(value: str) -> bool:
    """Check if a value is a valid URL.
    
    Args:
        value: The URL to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(value, str):
        return False
    return value.startswith(('http://', 'https://', 'doi:', 'file://'))


def is_valid_year(value: int) -> bool:
    """Check if a value is a valid publication year.
    
    Args:
        value: The year to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    return isinstance(value, int) and 1900 <= value <= datetime.now().year + 1


def is_valid_confidence_score(value: float) -> bool:
    """Check if a value is a valid confidence score (1-5).
    
    Args:
        value: The score to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    return isinstance(value, (int, float)) and 1.0 <= value <= 5.0


def is_valid_iso_date(value: str) -> bool:
    """Check if a value is a valid ISO format date.
    
    Args:
        value: The date string to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


# ===== Reference Validators =====

def validate_paper_reference(paper: PaperReference) -> ValidationResult:
    """Validate a PaperReference.
    
    Args:
        paper: The PaperReference to validate.
    
    Returns:
        ValidationResult with any errors found.
    """
    result = ValidationResult()
    
    # Required fields
    if not is_valid_id(paper.id):
        result.add_error("id", "ID must be a non-empty alphanumeric string")
    
    if not paper.title or not isinstance(paper.title, str):
        result.add_error("title", "Title must be a non-empty string")
    
    if not paper.authors or not isinstance(paper.authors, list) or len(paper.authors) == 0:
        result.add_error("authors", "Must have at least one author")
    
    if not paper.publication_venue or not isinstance(paper.publication_venue, str):
        result.add_error("publication_venue", "Publication venue must be a non-empty string")
    
    if not is_valid_year(paper.publication_year):
        result.add_error("publication_year", f"Year must be between 1900 and {datetime.now().year}")
    
    if not is_valid_url(paper.doi_or_url):
        result.add_error("doi_or_url", "Must be a valid URL or DOI")
    
    # Optional fields
    if paper.abstract and not isinstance(paper.abstract, str):
        result.add_error("abstract", "Abstract must be a string")
    
    return result


def validate_talk_reference(talk: TalkReference) -> ValidationResult:
    """Validate a TalkReference.
    
    Args:
        talk: The TalkReference to validate.
    
    Returns:
        ValidationResult with any errors found.
    """
    result = ValidationResult()
    
    # Required fields
    if not is_valid_id(talk.id):
        result.add_error("id", "ID must be a non-empty alphanumeric string")
    
    if not talk.title or not isinstance(talk.title, str):
        result.add_error("title", "Title must be a non-empty string")
    
    if not talk.speaker or not isinstance(talk.speaker, str):
        result.add_error("speaker", "Speaker must be a non-empty string")
    
    if not talk.event_name or not isinstance(talk.event_name, str):
        result.add_error("event_name", "Event name must be a non-empty string")
    
    if not is_valid_iso_date(talk.event_date):
        result.add_error("event_date", "Event date must be in ISO format (YYYY-MM-DD)")
    
    # Optional fields
    if talk.video_url and not is_valid_url(talk.video_url):
        result.add_error("video_url", "Must be a valid URL")
    
    if talk.slides_url and not is_valid_url(talk.slides_url):
        result.add_error("slides_url", "Must be a valid URL")
    
    if talk.summary and not isinstance(talk.summary, str):
        result.add_error("summary", "Summary must be a string")
    
    return result


def validate_repository_reference(repo: RepositoryReference) -> ValidationResult:
    """Validate a RepositoryReference.
    
    Args:
        repo: The RepositoryReference to validate.
    
    Returns:
        ValidationResult with any errors found.
    """
    result = ValidationResult()
    
    # Required fields
    if not is_valid_id(repo.id):
        result.add_error("id", "ID must be a non-empty alphanumeric string")
    
    if not repo.name or not isinstance(repo.name, str):
        result.add_error("name", "Name must be a non-empty string")
    
    if not is_valid_url(repo.url):
        result.add_error("url", "Must be a valid URL")
    
    if not repo.language or not isinstance(repo.language, str):
        result.add_error("language", "Language must be a non-empty string")
    
    # Optional fields
    if repo.description and not isinstance(repo.description, str):
        result.add_error("description", "Description must be a string")
    
    if repo.stars is not None and not isinstance(repo.stars, int):
        result.add_error("stars", "Stars must be an integer")
    
    if repo.last_updated and not is_valid_iso_date(repo.last_updated):
        result.add_error("last_updated", "Last updated must be in ISO format")
    
    return result


# ===== Configuration Validators =====

def validate_execution_config(config: ExecutionConfig) -> ValidationResult:
    """Validate ExecutionConfig.
    
    Args:
        config: The ExecutionConfig to validate.
    
    Returns:
        ValidationResult with any errors found.
    """
    result = ValidationResult()
    
    if not config.extraction_agent_type:
        result.add_error("extraction_agent_type", "Agent type must be specified")
    
    if config.max_iterations < 1:
        result.add_error("max_iterations", "Max iterations must be at least 1")
    
    if not is_valid_confidence_score(config.quality_threshold):
        result.add_error("quality_threshold", "Quality threshold must be between 1.0 and 5.0")
    
    if config.timeout_seconds < 1:
        result.add_error("timeout_seconds", "Timeout must be at least 1 second")
    
    return result


# ===== Project Validators =====

def validate_project_definition(project: ProjectDefinition) -> ValidationResult:
    """Validate a complete ProjectDefinition.
    
    This performs comprehensive validation on the project and all its artifacts.
    
    Args:
        project: The ProjectDefinition to validate.
    
    Returns:
        ValidationResult with any errors found.
    """
    result = ValidationResult()
    
    # Project metadata
    if not is_valid_id(project.id):
        result.add_error("id", "Project ID must be a non-empty alphanumeric string")
    
    if not project.name or not isinstance(project.name, str):
        result.add_error("name", "Project name must be a non-empty string")
    
    if not project.description or not isinstance(project.description, str):
        result.add_error("description", "Project description must be a non-empty string")
    
    if not project.research_area or not isinstance(project.research_area, str):
        result.add_error("research_area", "Research area must be a non-empty string")
    
    # Validate keywords
    if not isinstance(project.keywords, list):
        result.add_error("keywords", "Keywords must be a list")
    elif any(not isinstance(k, str) for k in project.keywords):
        result.add_error("keywords", "All keywords must be strings")
    
    # Validate objectives
    if not isinstance(project.objectives, list):
        result.add_error("objectives", "Objectives must be a list")
    elif any(not isinstance(o, str) for o in project.objectives):
        result.add_error("objectives", "All objectives must be strings")
    
    # Validate execution config
    config_result = validate_execution_config(project.execution_config)
    if not config_result.is_valid:
        for err in config_result.errors:
            result.add_error(f"execution_config.{err.field}", err.message)
    
    # Validate all paper references
    for i, paper in enumerate(project.papers):
        paper_result = validate_paper_reference(paper)
        if not paper_result.is_valid:
            for err in paper_result.errors:
                result.add_error(f"papers[{i}].{err.field}", err.message)
    
    # Validate all talk references
    for i, talk in enumerate(project.talks):
        talk_result = validate_talk_reference(talk)
        if not talk_result.is_valid:
            for err in talk_result.errors:
                result.add_error(f"talks[{i}].{err.field}", err.message)
    
    # Validate all repository references
    for i, repo in enumerate(project.repositories):
        repo_result = validate_repository_reference(repo)
        if not repo_result.is_valid:
            for err in repo_result.errors:
                result.add_error(f"repositories[{i}].{err.field}", err.message)
    
    # Check for duplicate artifact IDs across types
    all_ids = []
    for p in project.papers:
        if p.id in all_ids:
            result.add_error("papers", f"Duplicate artifact ID: {p.id}")
        all_ids.append(p.id)
    
    for t in project.talks:
        if t.id in all_ids:
            result.add_error("talks", f"Duplicate artifact ID: {t.id}")
        all_ids.append(t.id)
    
    for r in project.repositories:
        if r.id in all_ids:
            result.add_error("repositories", f"Duplicate artifact ID: {r.id}")
        all_ids.append(r.id)
    
    return result


# ===== Batch Validators =====

def validate_projects_for_compilation(
    projects: List[ProjectDefinition]
) -> Tuple[List[ProjectDefinition], List[Tuple[str, ValidationResult]]]:
    """Validate a batch of projects for compilation readiness.
    
    Args:
        projects: List of projects to validate.
    
    Returns:
        Tuple of (valid_projects, failed_projects_with_errors).
    """
    valid_projects = []
    failed_projects = []
    
    for project in projects:
        result = validate_project_definition(project)
        if result.is_valid:
            valid_projects.append(project)
        else:
            failed_projects.append((project.id, result))
    
    return valid_projects, failed_projects


def validate_project_artifacts_completeness(project: ProjectDefinition) -> ValidationResult:
    """Validate that a project has sufficient artifacts for compilation.
    
    Ensures the project has a minimum number of artifacts from various sources.
    
    Args:
        project: The project to validate.
    
    Returns:
        ValidationResult indicating if project is ready for compilation.
    """
    result = ValidationResult()
    
    total_artifacts = project.artifact_count()
    
    if total_artifacts == 0:
        result.add_error("artifacts", "Project must have at least one artifact")
    
    if project.execution_config.quality_threshold < 1.0 or \
       project.execution_config.quality_threshold > 5.0:
        result.add_error("quality_threshold", "Quality threshold out of valid range")
    
    return result
