"""Tests for storage abstraction and storage manager."""

import tempfile
from pathlib import Path
import pytest

from storage.base_repository import BaseRepository
from storage.storage_manager import StorageManager
from projects.repository import ProjectRepository
from projects import ProjectDefinition


# ===== Helper for PHASE B (Event-scoped projects) =====
def create_project(**kwargs):
    """Helper to create ProjectDefinition with required Phase B fields."""
    if 'event_id' not in kwargs:
        kwargs['event_id'] = 'event_default'
    if 'odata_type' not in kwargs:
        kwargs['odata_type'] = '#microsoft.graph.project'
    return ProjectDefinition(**kwargs)


class DummyRepository(BaseRepository[str]):
    """Minimal in-memory repository for interface validation in tests."""

    def __init__(self):
        self.items = {}

    def create(self, item: str) -> str:
        self.items[item] = item
        return item

    def get(self, item_id: str) -> str:
        return self.items[item_id]

    def update(self, item: str) -> str:
        self.items[item] = item
        return item

    def delete(self, item_id: str) -> None:
        del self.items[item_id]

    def list_all(self):
        return list(self.items.values())

    def exists(self, item_id: str) -> bool:
        return item_id in self.items

    def count(self) -> int:
        return len(self.items)

    def clear(self) -> None:
        self.items = {}


class TestBaseRepositoryABC:
    """Ensure BaseRepository enforces abstract methods."""

    def test_cannot_instantiate_directly(self):
        with pytest.raises(TypeError):
            BaseRepository()  # type: ignore[abstract]

    def test_dummy_repository_satisfies_interface(self):
        repo = DummyRepository()
        repo.create("item1")
        assert repo.exists("item1")
        assert repo.get("item1") == "item1"
        assert repo.count() == 1
        repo.update("item1")
        assert repo.list_all() == ["item1"]
        repo.delete("item1")
        assert not repo.exists("item1")
        repo.clear()
        assert repo.count() == 0


class TestStorageManager:
    """Tests for StorageManager directory handling."""

    def test_creates_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StorageManager(base_dir=tmpdir)
            assert manager.get_projects_dir().exists()
            assert manager.get_projects_dir().is_dir()

    def test_clear_projects_removes_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StorageManager(base_dir=tmpdir)
            projects_dir = manager.get_projects_dir()
            sample_file = projects_dir / "sample.json"
            sample_file.write_text("{}")
            assert sample_file.exists()
            manager.clear_projects()
            assert not sample_file.exists()


class TestProjectRepositoryWithManager:
    """Integration tests for ProjectRepository using StorageManager."""

    def test_repository_uses_manager_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StorageManager(base_dir=tmpdir)
            repo = ProjectRepository(storage_manager=manager)
            project = create_project(
                id="proj1",
                name="Proj",
                description="Desc",
                research_area="Area",
            )
            repo.create(project)
            stored_file = manager.get_projects_dir() / "proj1.json"
            assert stored_file.exists()

    def test_repository_with_manager_crud(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = StorageManager(base_dir=tmpdir)
            repo = ProjectRepository(storage_manager=manager)
            project = create_project(
                id="proj1",
                name="Proj",
                description="Desc",
                research_area="Area",
            )
            repo.create(project)
            fetched = repo.get("proj1")
            assert fetched.id == "proj1"
            fetched.name = "Updated"
            repo.update(fetched)
            fetched2 = repo.get("proj1")
            assert fetched2.name == "Updated"
            repo.delete("proj1")
            assert not repo.exists("proj1")
