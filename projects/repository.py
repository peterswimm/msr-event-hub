"""JSON-based repository for persistent project storage.

Provides CRUD operations for ProjectDefinition objects with JSON serialization,
enabling file-based persistence as an MVP. Future versions will migrate to SQLite.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from projects.exceptions import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    RepositoryError,
    StorageError,
)
from projects.models import ProjectDefinition
from storage.base_repository import BaseRepository
from storage.storage_manager import StorageManager


class ProjectRepository(BaseRepository[ProjectDefinition]):
    """JSON repository for managing projects.

    Uses a StorageManager to resolve the projects directory, enabling easy
    migration to future backends (e.g., SQLite) without changing callers.
    """

    def __init__(
        self,
        storage_dir: str = "data/projects",
        storage_manager: Optional[StorageManager] = None,
    ) -> None:
        """Initialize the repository.

        Args:
            storage_dir: Directory path for storing project JSON files when no manager is provided.
            storage_manager: Optional shared storage manager. When provided, its projects_dir is used.

        Raises:
            StorageError: If the storage directory cannot be created.
        """
        self.storage_dir = (
            storage_manager.get_projects_dir()
            if storage_manager is not None
            else Path(storage_dir)
        )
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(
                "initialization", f"Cannot create storage directory: {str(e)}"
            )
    
    def _get_project_path(self, project_id: str) -> Path:
        """Get the file path for a project."""
        return self.storage_dir / f"{project_id}.json"
    
    def create(self, project: ProjectDefinition) -> ProjectDefinition:
        """Create a new project.
        
        Args:
            project: The ProjectDefinition to create.
        
        Returns:
            The created ProjectDefinition.
        
        Raises:
            ProjectAlreadyExistsError: If a project with this ID already exists.
            StorageError: If the file cannot be written.
        """
        project_path = self._get_project_path(project.id)
        
        if project_path.exists():
            raise ProjectAlreadyExistsError(project.id)
        
        try:
            project.updated_at = datetime.now()
            data = project.to_dict()
            with open(project_path, 'w') as f:
                json.dump(data, f, indent=2)
            return project
        except ProjectAlreadyExistsError:
            raise
        except Exception as e:
            raise StorageError("create", f"Cannot save project: {str(e)}")
    
    def get(self, project_id: str) -> ProjectDefinition:
        """Retrieve a project by ID.
        
        Args:
            project_id: The ID of the project to retrieve.
        
        Returns:
            The ProjectDefinition.
        
        Raises:
            ProjectNotFoundError: If the project doesn't exist.
            StorageError: If the file cannot be read.
        """
        project_path = self._get_project_path(project_id)
        
        if not project_path.exists():
            raise ProjectNotFoundError(project_id)
        
        try:
            with open(project_path, 'r') as f:
                data = json.load(f)
            return ProjectDefinition.from_dict(data)
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("get", f"Cannot load project: {str(e)}")
    
    def update(self, project: ProjectDefinition) -> ProjectDefinition:
        """Update an existing project.
        
        Args:
            project: The ProjectDefinition with updated values.
        
        Returns:
            The updated ProjectDefinition.
        
        Raises:
            ProjectNotFoundError: If the project doesn't exist.
            StorageError: If the file cannot be written.
        """
        project_path = self._get_project_path(project.id)
        
        if not project_path.exists():
            raise ProjectNotFoundError(project.id)
        
        try:
            project.updated_at = datetime.now()
            data = project.to_dict()
            with open(project_path, 'w') as f:
                json.dump(data, f, indent=2)
            return project
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("update", f"Cannot update project: {str(e)}")
    
    def delete(self, project_id: str) -> None:
        """Delete a project.
        
        Args:
            project_id: The ID of the project to delete.
        
        Raises:
            ProjectNotFoundError: If the project doesn't exist.
            StorageError: If the file cannot be deleted.
        """
        project_path = self._get_project_path(project_id)
        
        if not project_path.exists():
            raise ProjectNotFoundError(project_id)
        
        try:
            project_path.unlink()
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("delete", f"Cannot delete project: {str(e)}")
    
    def list_all(self) -> List[ProjectDefinition]:
        """List all projects in the repository.
        
        Returns:
            List of all ProjectDefinition objects.
        
        Raises:
            StorageError: If projects cannot be read.
        """
        try:
            projects = []
            for project_file in self.storage_dir.glob("*.json"):
                try:
                    with open(project_file, 'r') as f:
                        data = json.load(f)
                    projects.append(ProjectDefinition.from_dict(data))
                except Exception as e:
                    # Log but continue on individual file errors
                    print(f"Warning: Could not load project from {project_file}: {str(e)}")
            return projects
        except Exception as e:
            raise StorageError("list_all", f"Cannot list projects: {str(e)}")
    
    def list_by_event(self, event_id: str) -> List[ProjectDefinition]:
        """List all projects for a specific event (NEW: event-scoped access).
        
        Args:
            event_id: The event to filter by.
        
        Returns:
            List of ProjectDefinition objects for the event.
        """
        return [p for p in self.list_all() if p.event_id == event_id]
    
    def exists(self, project_id: str) -> bool:
        """Check if a project exists.
        
        Args:
            project_id: The ID to check.
        
        Returns:
            True if the project exists, False otherwise.
        """
        project_path = self._get_project_path(project_id)
        return project_path.exists()
    
    def count(self) -> int:
        """Count the number of projects in the repository.
        
        Returns:
            The number of project files.
        """
        return len(list(self.storage_dir.glob("*.json")))
    
    def clear(self) -> None:
        """Delete all projects in the repository.
        
        Raises:
            StorageError: If projects cannot be deleted.
        """
        try:
            for project_file in self.storage_dir.glob("*.json"):
                project_file.unlink()
        except Exception as e:
            raise StorageError("clear", f"Cannot clear repository: {str(e)}")
    
    def export_to_dict(self, project_id: str) -> dict:
        """Export a project as a dictionary.
        
        Args:
            project_id: The ID of the project to export.
        
        Returns:
            Dictionary representation of the project.
        
        Raises:
            ProjectNotFoundError: If the project doesn't exist.
        """
        project = self.get(project_id)
        return project.to_dict()
    
    def import_from_dict(self, project_dict: dict) -> ProjectDefinition:
        """Import a project from a dictionary.
        
        Args:
            project_dict: Dictionary representation of a project.
        
        Returns:
            The imported and stored ProjectDefinition.
        
        Raises:
            ProjectAlreadyExistsError: If the project ID already exists.
            StorageError: If the project cannot be created.
        """
        project = ProjectDefinition.from_dict(project_dict)
        return self.create(project)
    
    def backup(self, backup_dir: str = "backups/projects") -> str:
        """Create a backup of all projects.
        
        Args:
            backup_dir: Directory to store the backup.
        
        Returns:
            Path to the backup directory.
        
        Raises:
            StorageError: If the backup cannot be created.
        """
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Create timestamped backup subdirectory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamped_backup = backup_path / f"backup_{timestamp}"
            timestamped_backup.mkdir(parents=True, exist_ok=True)
            
            # Copy all project files
            for project_file in self.storage_dir.glob("*.json"):
                with open(project_file, 'r') as src:
                    data = json.load(src)
                backup_file = timestamped_backup / project_file.name
                with open(backup_file, 'w') as dst:
                    json.dump(data, dst, indent=2)
            
            return str(timestamped_backup)
        except Exception as e:
            raise StorageError("backup", f"Cannot create backup: {str(e)}")
    
    def restore_from_backup(self, backup_dir: str) -> int:
        """Restore projects from a backup directory.
        
        Args:
            backup_dir: Directory containing backup project files.
        
        Returns:
            Number of projects restored.
        
        Raises:
            StorageError: If the restoration fails.
        """
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                raise StorageError("restore", f"Backup directory not found: {backup_dir}")
            
            restored_count = 0
            for backup_file in backup_path.glob("*.json"):
                try:
                    with open(backup_file, 'r') as f:
                        data = json.load(f)
                    # Skip if project already exists
                    project_id = data.get("id")
                    if project_id and not self.exists(project_id):
                        self.import_from_dict(data)
                        restored_count += 1
                except Exception as e:
                    print(f"Warning: Could not restore project from {backup_file}: {str(e)}")
            
            return restored_count
        except StorageError:
            raise
        except Exception as e:
            raise StorageError("restore", f"Cannot restore from backup: {str(e)}")
