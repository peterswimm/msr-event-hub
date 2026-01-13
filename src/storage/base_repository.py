"""Abstract repository interface for storage backends.

Provides a consistent CRUD and lifecycle contract so concrete repositories
(e.g., JSON, SQLite) can be swapped without changing callers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Iterable, List, Optional, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """Abstract base class for repositories managing stored items."""

    @abstractmethod
    def create(self, item: T) -> T:
        """Persist a new item and return it."""
        raise NotImplementedError

    @abstractmethod
    def get(self, item_id: str) -> T:
        """Fetch an item by ID or raise if missing."""
        raise NotImplementedError

    @abstractmethod
    def update(self, item: T) -> T:
        """Persist updates to an existing item and return it."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, item_id: str) -> None:
        """Delete an item by ID."""
        raise NotImplementedError

    @abstractmethod
    def list_all(self) -> List[T]:
        """Return all stored items."""
        raise NotImplementedError

    @abstractmethod
    def exists(self, item_id: str) -> bool:
        """Return True if an item exists."""
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """Return total number of stored items."""
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored items."""
        raise NotImplementedError

    def backup(self, backup_dir: str) -> str:
        """Optional: create a backup and return its path."""
        raise NotImplementedError

    def restore_from_backup(self, backup_dir: str) -> int:
        """Optional: restore items from backup and return count restored."""
        raise NotImplementedError
