"""Projects module for managing knowledge artifact collection and compilation.

This module provides the core models and interfaces for defining research projects,
managing artifact references, and orchestrating the knowledge extraction pipeline.
"""

from projects.exceptions import (
    ProjectException,
    ProjectNotFoundError,
    ProjectAlreadyExistsError,
    InvalidProjectStateError,
    InvalidArtifactError,
    ArtifactNotFoundError,
    DuplicateArtifactError,
    InvalidProjectConfigError,
    StorageError,
    RepositoryError,
)

from projects.models import (
    ProjectDefinition,
    PaperReference,
    TalkReference,
    RepositoryReference,
    ExecutionConfig,
    QualityMetrics,
    SourceType,
    ResearchMaturityStage,
)

from projects.validators import (
    ValidationResult,
    ValidationError,
    validate_project_definition,
    validate_paper_reference,
    validate_talk_reference,
    validate_repository_reference,
    validate_execution_config,
    validate_projects_for_compilation,
    validate_project_artifacts_completeness,
)

__all__ = [
    # Exceptions
    "ProjectException",
    "ProjectNotFoundError",
    "ProjectAlreadyExistsError",
    "InvalidProjectStateError",
    "InvalidArtifactError",
    "ArtifactNotFoundError",
    "DuplicateArtifactError",
    "InvalidProjectConfigError",
    "StorageError",
    "RepositoryError",
    # Models
    "ProjectDefinition",
    "PaperReference",
    "TalkReference",
    "RepositoryReference",
    "ExecutionConfig",
    "QualityMetrics",
    "SourceType",
    "ResearchMaturityStage",
]
