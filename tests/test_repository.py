"""Tests for ProjectRepository and persistence operations.

Comprehensive test suite for repository CRUD operations, serialization,
and file-based storage. Target: 25+ tests covering all repository operations.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from projects import (
    ProjectDefinition,
    PaperReference,
    ProjectNotFoundError,
    ProjectAlreadyExistsError,
    StorageError,
)
from projects.repository import ProjectRepository


# ===== Helper for PHASE B (Event-scoped projects) =====
def create_project(**kwargs):
    """Helper to create ProjectDefinition with required Phase B fields."""
    if 'event_id' not in kwargs:
        kwargs['event_id'] = 'event_default'
    if 'odata_type' not in kwargs:
        kwargs['odata_type'] = '#microsoft.graph.project'
    return ProjectDefinition(**kwargs)


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def repository(temp_storage):
    """Create a repository with temporary storage."""
    return ProjectRepository(storage_dir=temp_storage)


@pytest.fixture
def sample_project():
    """Create a sample project."""
    project = create_project(
        id="test_project_001",
        name="Test Project",
        description="A test project",
        research_area="Testing"
    )
    return project


@pytest.fixture
def project_with_artifacts(sample_project):
    """Create a project with artifacts."""
    paper = PaperReference(
        id="paper_001",
        title="Test Paper",
        authors=["Author"],
        publication_venue="Venue",
        publication_year=2024,
        doi_or_url="https://example.com"
    )
    sample_project.add_paper(paper)
    return sample_project


class TestRepositoryCreate:
    """Tests for project creation."""
    
    def test_create_simple_project(self, repository, sample_project):
        """Test creating a simple project."""
        created = repository.create(sample_project)
        assert created.id == sample_project.id
        assert repository.exists(sample_project.id)
    
    def test_create_project_stores_file(self, repository, sample_project, temp_storage):
        """Test that create stores a file."""
        repository.create(sample_project)
        project_file = Path(temp_storage) / f"{sample_project.id}.json"
        assert project_file.exists()
    
    def test_create_project_file_contains_data(self, repository, sample_project, temp_storage):
        """Test that the stored file contains valid JSON."""
        repository.create(sample_project)
        project_file = Path(temp_storage) / f"{sample_project.id}.json"
        
        with open(project_file, 'r') as f:
            data = json.load(f)
        
        assert data["id"] == sample_project.id
        assert data["name"] == sample_project.name
    
    def test_create_duplicate_raises_error(self, repository, sample_project):
        """Test that creating duplicate project raises error."""
        repository.create(sample_project)
        with pytest.raises(ProjectAlreadyExistsError):
            repository.create(sample_project)
    
    def test_create_project_with_artifacts(self, repository, project_with_artifacts):
        """Test creating a project with artifacts."""
        created = repository.create(project_with_artifacts)
        assert created.artifact_count() == 1
        assert len(created.papers) == 1


class TestRepositoryRead:
    """Tests for project retrieval."""
    
    def test_get_existing_project(self, repository, sample_project):
        """Test retrieving an existing project."""
        repository.create(sample_project)
        retrieved = repository.get(sample_project.id)
        assert retrieved.id == sample_project.id
        assert retrieved.name == sample_project.name
    
    def test_get_nonexistent_project_raises_error(self, repository):
        """Test that getting nonexistent project raises error."""
        with pytest.raises(ProjectNotFoundError):
            repository.get("nonexistent_id")
    
    def test_get_preserves_artifacts(self, repository, project_with_artifacts):
        """Test that retrieval preserves artifacts."""
        repository.create(project_with_artifacts)
        retrieved = repository.get(project_with_artifacts.id)
        assert retrieved.artifact_count() == 1
        assert len(retrieved.papers) == 1
    
    def test_get_preserves_metadata(self, repository, sample_project):
        """Test that retrieval preserves project metadata."""
        sample_project.keywords = ["testing", "metadata"]
        sample_project.objectives = ["Test objective"]
        repository.create(sample_project)
        
        retrieved = repository.get(sample_project.id)
        assert retrieved.keywords == sample_project.keywords
        assert retrieved.objectives == sample_project.objectives


class TestRepositoryUpdate:
    """Tests for project updates."""
    
    def test_update_existing_project(self, repository, sample_project):
        """Test updating an existing project."""
        repository.create(sample_project)
        
        sample_project.name = "Updated Name"
        updated = repository.update(sample_project)
        assert updated.name == "Updated Name"
    
    def test_update_persists_changes(self, repository, sample_project):
        """Test that update persists changes to disk."""
        repository.create(sample_project)
        
        sample_project.name = "Updated Name"
        repository.update(sample_project)
        
        retrieved = repository.get(sample_project.id)
        assert retrieved.name == "Updated Name"
    
    def test_update_nonexistent_raises_error(self, repository, sample_project):
        """Test that updating nonexistent project raises error."""
        with pytest.raises(ProjectNotFoundError):
            repository.update(sample_project)
    
    def test_update_refreshes_timestamp(self, repository, sample_project):
        """Test that update refreshes the updated_at timestamp."""
        repository.create(sample_project)
        original_updated = sample_project.updated_at
        
        # Wait a tiny bit and update
        import time
        time.sleep(0.01)
        sample_project.name = "Updated"
        updated = repository.update(sample_project)
        
        assert updated.updated_at > original_updated


class TestRepositoryDelete:
    """Tests for project deletion."""
    
    def test_delete_existing_project(self, repository, sample_project):
        """Test deleting an existing project."""
        repository.create(sample_project)
        assert repository.exists(sample_project.id)
        
        repository.delete(sample_project.id)
        assert not repository.exists(sample_project.id)
    
    def test_delete_nonexistent_raises_error(self, repository):
        """Test that deleting nonexistent project raises error."""
        with pytest.raises(ProjectNotFoundError):
            repository.delete("nonexistent_id")
    
    def test_delete_removes_file(self, repository, sample_project, temp_storage):
        """Test that delete removes the file from disk."""
        repository.create(sample_project)
        project_file = Path(temp_storage) / f"{sample_project.id}.json"
        assert project_file.exists()
        
        repository.delete(sample_project.id)
        assert not project_file.exists()


class TestRepositoryList:
    """Tests for listing projects."""
    
    def test_list_empty_repository(self, repository):
        """Test listing projects in an empty repository."""
        projects = repository.list_all()
        assert projects == []
    
    def test_list_single_project(self, repository, sample_project):
        """Test listing a repository with one project."""
        repository.create(sample_project)
        projects = repository.list_all()
        assert len(projects) == 1
        assert projects[0].id == sample_project.id
    
    def test_list_multiple_projects(self, repository):
        """Test listing a repository with multiple projects."""
        for i in range(3):
            project = create_project(
                id=f"project_{i}",
                name=f"Project {i}",
                description="Test",
                research_area="Testing"
            )
            repository.create(project)
        
        projects = repository.list_all()
        assert len(projects) == 3
    
    def test_list_preserves_project_data(self, repository, project_with_artifacts):
        """Test that listing preserves full project data."""
        repository.create(project_with_artifacts)
        projects = repository.list_all()
        
        assert len(projects) == 1
        assert projects[0].artifact_count() == 1


class TestRepositoryExists:
    """Tests for existence checking."""
    
    def test_exists_returns_true_for_existing_project(self, repository, sample_project):
        """Test exists returns True for stored project."""
        repository.create(sample_project)
        assert repository.exists(sample_project.id)
    
    def test_exists_returns_false_for_nonexistent_project(self, repository):
        """Test exists returns False for nonexistent project."""
        assert not repository.exists("nonexistent_id")


class TestRepositoryCount:
    """Tests for counting projects."""
    
    def test_count_empty_repository(self, repository):
        """Test counting projects in empty repository."""
        assert repository.count() == 0
    
    def test_count_single_project(self, repository, sample_project):
        """Test counting single project."""
        repository.create(sample_project)
        assert repository.count() == 1
    
    def test_count_multiple_projects(self, repository):
        """Test counting multiple projects."""
        for i in range(5):
            project = create_project(
                id=f"project_{i}",
                name=f"Project {i}",
                description="Test",
                research_area="Testing"
            )
            repository.create(project)
        
        assert repository.count() == 5


class TestRepositoryExport:
    """Tests for export operations."""
    
    def test_export_to_dict(self, repository, sample_project):
        """Test exporting project to dictionary."""
        repository.create(sample_project)
        exported = repository.export_to_dict(sample_project.id)
        
        assert exported["id"] == sample_project.id
        assert isinstance(exported, dict)
    
    def test_export_nonexistent_raises_error(self, repository):
        """Test exporting nonexistent project raises error."""
        with pytest.raises(ProjectNotFoundError):
            repository.export_to_dict("nonexistent_id")


class TestRepositoryImport:
    """Tests for import operations."""
    
    def test_import_from_dict(self, repository):
        """Test importing project from dictionary."""
        project_dict = {
            "id": "imported_project",
            "name": "Imported Project",
            "description": "Test",
            "research_area": "Testing",
            "papers": [],
            "talks": [],
            "repositories": [],
            "objectives": [],
            "keywords": [],
            "maturity_stage": "exploratory",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "created",
            "execution_config": {
                "extraction_agent_type": "paper",
                "max_iterations": 2,
                "quality_threshold": 3.0,
                "parallelization": True,
                "timeout_seconds": 300
            },
            "compiled_knowledge": None,
            "quality_metrics": {
                "total_artifacts": 0,
                "artifacts_reviewed": 0,
                "average_confidence": 0.0,
                "average_coverage": 0.0,
                "last_updated": None
            }
        }
        
        imported = repository.import_from_dict(project_dict)
        assert imported.id == "imported_project"
        assert repository.exists("imported_project")
    
    def test_import_duplicate_raises_error(self, repository, sample_project):
        """Test importing duplicate raises error."""
        repository.create(sample_project)
        with pytest.raises(ProjectAlreadyExistsError):
            repository.import_from_dict(sample_project.to_dict())


class TestRepositoryClear:
    """Tests for clearing the repository."""
    
    def test_clear_removes_all_projects(self, repository):
        """Test that clear removes all projects."""
        for i in range(3):
            project = create_project(
                id=f"project_{i}",
                name=f"Project {i}",
                description="Test",
                research_area="Testing"
            )
            repository.create(project)
        
        assert repository.count() == 3
        repository.clear()
        assert repository.count() == 0


class TestRepositoryBackup:
    """Tests for backup operations."""
    
    def test_backup_creates_directory(self, repository, sample_project, temp_storage):
        """Test that backup creates a backup directory."""
        repository.create(sample_project)
        backup_dir = Path(temp_storage) / "backups"
        
        backup_path = repository.backup(str(backup_dir))
        assert Path(backup_path).exists()
    
    def test_backup_copies_projects(self, repository, sample_project, temp_storage):
        """Test that backup copies project files."""
        repository.create(sample_project)
        backup_dir = Path(temp_storage) / "backups"
        
        backup_path = repository.backup(str(backup_dir))
        backup_file = Path(backup_path) / f"{sample_project.id}.json"
        assert backup_file.exists()
    
    def test_backup_preserves_data(self, repository, project_with_artifacts, temp_storage):
        """Test that backup preserves project data."""
        repository.create(project_with_artifacts)
        backup_dir = Path(temp_storage) / "backups"
        
        backup_path = repository.backup(str(backup_dir))
        backup_file = Path(backup_path) / f"{project_with_artifacts.id}.json"
        
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        assert backup_data["id"] == project_with_artifacts.id
        assert len(backup_data["papers"]) == 1


class TestRepositoryRestore:
    """Tests for restore operations."""
    
    def test_restore_from_backup(self, repository, sample_project, temp_storage):
        """Test restoring projects from backup."""
        repository.create(sample_project)
        backup_dir = Path(temp_storage) / "backups"
        backup_path = repository.backup(str(backup_dir))
        
        # Clear the repository
        repository.clear()
        assert repository.count() == 0
        
        # Restore from backup
        restored_count = repository.restore_from_backup(backup_path)
        assert restored_count == 1
        assert repository.count() == 1
    
    def test_restore_nonexistent_backup_raises_error(self, repository):
        """Test restoring from nonexistent backup raises error."""
        with pytest.raises(StorageError):
            repository.restore_from_backup("nonexistent/backup/dir")


class TestRepositoryIntegration:
    """Integration tests for complete workflows."""
    
    def test_create_update_retrieve_workflow(self, repository):
        """Test complete create-update-retrieve workflow."""
        # Create
        project = create_project(
            id="workflow_test",
            name="Workflow Test",
            description="Test workflow",
            research_area="Integration"
        )
        repository.create(project)
        
        # Update
        project.name = "Updated Workflow Test"
        repository.update(project)
        
        # Retrieve
        retrieved = repository.get("workflow_test")
        assert retrieved.name == "Updated Workflow Test"
    
    def test_backup_restore_workflow(self, repository, temp_storage):
        """Test complete backup-restore workflow."""
        # Create projects
        for i in range(2):
            project = create_project(
                id=f"backup_test_{i}",
                name=f"Backup Test {i}",
                description="Test",
                research_area="Backup Testing"
            )
            repository.create(project)
        
        # Backup
        backup_dir = Path(temp_storage) / "backups"
        backup_path = repository.backup(str(backup_dir))
        
        # Clear and restore
        repository.clear()
        restored_count = repository.restore_from_backup(backup_path)
        
        assert restored_count == 2
        assert repository.count() == 2
    
    def test_export_import_roundtrip(self, repository, project_with_artifacts):
        """Test export-import roundtrip."""
        repository.create(project_with_artifacts)
        
        # Export
        exported = repository.export_to_dict(project_with_artifacts.id)
        
        # Create new repository and import
        with tempfile.TemporaryDirectory() as tmpdir:
            repo2 = ProjectRepository(storage_dir=tmpdir)
            imported = repo2.import_from_dict(exported)
            
            assert imported.id == project_with_artifacts.id
            assert imported.artifact_count() == project_with_artifacts.artifact_count()
