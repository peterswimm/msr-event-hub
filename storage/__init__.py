"""Storage package for repository abstractions and managers."""

from storage.base_repository import BaseRepository
from storage.storage_manager import StorageManager

__all__ = ["BaseRepository", "StorageManager"]
