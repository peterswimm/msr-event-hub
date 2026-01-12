"""Storage manager for repository directories.

Centralizes directory creation and resolution so repositories share a
consistent base path and can migrate between backends.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from projects.exceptions import StorageError


class StorageManager:
    """Manages storage directories for repositories."""

    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.projects_dir = self.base_dir / "projects"
        try:
            self.projects_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise StorageError("initialization", f"Cannot create storage root: {exc}")

    def get_projects_dir(self) -> Path:
        """Return the projects storage directory."""
        return self.projects_dir

    def clear_projects(self) -> None:
        """Remove all project files."""
        for file_path in self.projects_dir.glob("*.json"):
            try:
                file_path.unlink()
            except Exception as exc:
                raise StorageError("clear", f"Cannot delete {file_path}: {exc}")
