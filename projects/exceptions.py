"""Custom exception classes for project operations.

Provides domain-specific exceptions for projects module to enable precise
error handling and meaningful error messages throughout the pipeline.
"""


class ProjectException(Exception):
    """Base exception for all project-related errors."""
    pass


class ProjectNotFoundError(ProjectException):
    """Raised when a project cannot be found in the repository."""
    def __init__(self, project_id: str):
        self.project_id = project_id
        super().__init__(f"Project not found: {project_id}")


class ProjectAlreadyExistsError(ProjectException):
    """Raised when attempting to create a project with a duplicate ID."""
    def __init__(self, project_id: str):
        self.project_id = project_id
        super().__init__(f"Project already exists: {project_id}")


class InvalidProjectStateError(ProjectException):
    """Raised when an operation is invalid for the current project state."""
    def __init__(self, project_id: str, current_status: str, attempted_operation: str):
        self.project_id = project_id
        self.current_status = current_status
        self.attempted_operation = attempted_operation
        super().__init__(
            f"Cannot {attempted_operation} project {project_id} in state {current_status}"
        )


class InvalidArtifactError(ProjectException):
    """Raised when an artifact fails validation."""
    def __init__(self, artifact_id: str, reason: str):
        self.artifact_id = artifact_id
        self.reason = reason
        super().__init__(f"Invalid artifact {artifact_id}: {reason}")


class ArtifactNotFoundError(ProjectException):
    """Raised when an artifact cannot be found in a project."""
    def __init__(self, project_id: str, artifact_id: str):
        self.project_id = project_id
        self.artifact_id = artifact_id
        super().__init__(f"Artifact {artifact_id} not found in project {project_id}")


class DuplicateArtifactError(ProjectException):
    """Raised when attempting to add an artifact with a duplicate ID."""
    def __init__(self, project_id: str, artifact_id: str):
        self.project_id = project_id
        self.artifact_id = artifact_id
        super().__init__(f"Artifact {artifact_id} already exists in project {project_id}")


class InvalidProjectConfigError(ProjectException):
    """Raised when project execution configuration is invalid."""
    def __init__(self, project_id: str, config_issue: str):
        self.project_id = project_id
        self.config_issue = config_issue
        super().__init__(f"Invalid configuration for project {project_id}: {config_issue}")


class StorageError(ProjectException):
    """Raised when persistence operations fail."""
    def __init__(self, operation: str, message: str):
        self.operation = operation
        super().__init__(f"Storage error during {operation}: {message}")


class RepositoryError(ProjectException):
    """Raised when repository operations fail."""
    def __init__(self, message: str):
        super().__init__(f"Repository error: {message}")
