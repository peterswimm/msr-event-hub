"""Repositories for Knowledge Artifacts (PKA draft and Published variants)."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.core.knowledge_models import KnowledgeArtifact, PublishedKnowledge, ApprovalStatus
from src.storage.base_repository import BaseRepository
from src.storage.storage_manager import StorageManager
from src.core.projects.exceptions import (
    ProjectNotFoundError,
    RepositoryError,
    StorageError,
)


class KnowledgeArtifactRepository(BaseRepository[KnowledgeArtifact]):
    """JSON repository for draft Knowledge Artifacts (PKA)."""

    def __init__(
        self,
        storage_dir: str = "data/knowledge_artifacts",
        storage_manager: Optional[StorageManager] = None,
    ) -> None:
        """Initialize the repository."""
        self.storage_dir = (
            storage_manager.get_knowledge_artifacts_dir()
            if storage_manager is not None
            else Path(storage_dir)
        )
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(
                "initialization", f"Cannot create storage directory: {str(e)}"
            )

    def _get_artifact_path(self, artifact_id: str) -> Path:
        """Get the file path for an artifact."""
        return self.storage_dir / f"{artifact_id}.json"

    def create(self, artifact: KnowledgeArtifact) -> KnowledgeArtifact:
        """Create a new knowledge artifact."""
        artifact_path = self._get_artifact_path(artifact.id)
        if artifact_path.exists():
            raise StorageError("create", f"Artifact {artifact.id} already exists")
        try:
            data = artifact.to_dict()
            with open(artifact_path, "w") as f:
                json.dump(data, f, indent=2)
            return artifact
        except Exception as e:
            raise StorageError("create", f"Cannot save artifact: {str(e)}")

    def get(self, artifact_id: str) -> KnowledgeArtifact:
        """Retrieve an artifact by ID."""
        artifact_path = self._get_artifact_path(artifact_id)
        if not artifact_path.exists():
            raise ProjectNotFoundError(artifact_id)
        try:
            with open(artifact_path, "r") as f:
                data = json.load(f)
            return KnowledgeArtifact.from_dict(data)
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("get", f"Cannot load artifact: {str(e)}")

    def update(self, artifact: KnowledgeArtifact) -> KnowledgeArtifact:
        """Update an existing artifact."""
        artifact_path = self._get_artifact_path(artifact.id)
        if not artifact_path.exists():
            raise ProjectNotFoundError(artifact.id)
        try:
            artifact.updated_at = datetime.now()
            data = artifact.to_dict()
            with open(artifact_path, "w") as f:
                json.dump(data, f, indent=2)
            return artifact
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("update", f"Cannot update artifact: {str(e)}")

    def delete(self, artifact_id: str) -> None:
        """Delete an artifact."""
        artifact_path = self._get_artifact_path(artifact_id)
        if not artifact_path.exists():
            raise ProjectNotFoundError(artifact_id)
        try:
            artifact_path.unlink()
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("delete", f"Cannot delete artifact: {str(e)}")

    def list_all(self) -> List[KnowledgeArtifact]:
        """List all artifacts."""
        try:
            artifacts = []
            for artifact_file in self.storage_dir.glob("*.json"):
                try:
                    with open(artifact_file, "r") as f:
                        data = json.load(f)
                    artifacts.append(KnowledgeArtifact.from_dict(data))
                except Exception as e:
                    print(f"Warning: Could not load artifact from {artifact_file}: {str(e)}")
            return artifacts
        except Exception as e:
            raise StorageError("list_all", f"Cannot list artifacts: {str(e)}")

    def list_by_project(self, project_id: str) -> List[KnowledgeArtifact]:
        """List all artifacts for a specific project."""
        return [a for a in self.list_all() if a.project_id == project_id]

    def list_by_status(self, status: ApprovalStatus) -> List[KnowledgeArtifact]:
        """List all artifacts by approval status."""
        return [a for a in self.list_all() if a.approval_status == status]

    def exists(self, artifact_id: str) -> bool:
        """Check if an artifact exists."""
        return self._get_artifact_path(artifact_id).exists()

    def count(self) -> int:
        """Count the number of artifacts."""
        return len(list(self.storage_dir.glob("*.json")))

    def clear(self) -> None:
        """Delete all artifacts."""
        try:
            for artifact_file in self.storage_dir.glob("*.json"):
                artifact_file.unlink()
        except Exception as e:
            raise StorageError("clear", f"Cannot clear repository: {str(e)}")


class PublishedKnowledgeRepository(BaseRepository[PublishedKnowledge]):
    """JSON repository for Published (approved) Knowledge."""

    def __init__(
        self,
        storage_dir: str = "data/published_knowledge",
        storage_manager: Optional[StorageManager] = None,
    ) -> None:
        """Initialize the repository."""
        self.storage_dir = (
            storage_manager.get_published_knowledge_dir()
            if storage_manager is not None
            else Path(storage_dir)
        )
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise StorageError(
                "initialization", f"Cannot create storage directory: {str(e)}"
            )

    def _get_knowledge_path(self, knowledge_id: str) -> Path:
        """Get the file path for published knowledge."""
        return self.storage_dir / f"{knowledge_id}.json"

    def create(self, knowledge: PublishedKnowledge) -> PublishedKnowledge:
        """Create a new published knowledge entry."""
        knowledge_path = self._get_knowledge_path(knowledge.id)
        if knowledge_path.exists():
            raise StorageError("create", f"Knowledge {knowledge.id} already exists")
        try:
            data = knowledge.to_dict()
            with open(knowledge_path, "w") as f:
                json.dump(data, f, indent=2)
            return knowledge
        except Exception as e:
            raise StorageError("create", f"Cannot save knowledge: {str(e)}")

    def get(self, knowledge_id: str) -> PublishedKnowledge:
        """Retrieve published knowledge by ID."""
        knowledge_path = self._get_knowledge_path(knowledge_id)
        if not knowledge_path.exists():
            raise ProjectNotFoundError(knowledge_id)
        try:
            with open(knowledge_path, "r") as f:
                data = json.load(f)
            return PublishedKnowledge.from_dict(data)
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("get", f"Cannot load knowledge: {str(e)}")

    def update(self, knowledge: PublishedKnowledge) -> PublishedKnowledge:
        """Update published knowledge."""
        knowledge_path = self._get_knowledge_path(knowledge.id)
        if not knowledge_path.exists():
            raise ProjectNotFoundError(knowledge.id)
        try:
            knowledge.updated_at = datetime.now()
            data = knowledge.to_dict()
            with open(knowledge_path, "w") as f:
                json.dump(data, f, indent=2)
            return knowledge
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("update", f"Cannot update knowledge: {str(e)}")

    def delete(self, knowledge_id: str) -> None:
        """Delete published knowledge."""
        knowledge_path = self._get_knowledge_path(knowledge_id)
        if not knowledge_path.exists():
            raise ProjectNotFoundError(knowledge_id)
        try:
            knowledge_path.unlink()
        except ProjectNotFoundError:
            raise
        except Exception as e:
            raise StorageError("delete", f"Cannot delete knowledge: {str(e)}")

    def list_all(self) -> List[PublishedKnowledge]:
        """List all published knowledge."""
        try:
            items = []
            for knowledge_file in self.storage_dir.glob("*.json"):
                try:
                    with open(knowledge_file, "r") as f:
                        data = json.load(f)
                    items.append(PublishedKnowledge.from_dict(data))
                except Exception as e:
                    print(f"Warning: Could not load knowledge from {knowledge_file}: {str(e)}")
            return items
        except Exception as e:
            raise StorageError("list_all", f"Cannot list knowledge: {str(e)}")

    def list_by_project(self, project_id: str) -> List[PublishedKnowledge]:
        """List all published knowledge for a specific project."""
        return [k for k in self.list_all() if k.project_id == project_id]

    def get_latest_by_project(self, project_id: str) -> Optional[PublishedKnowledge]:
        """Get the latest published knowledge for a project."""
        items = self.list_by_project(project_id)
        if not items:
            return None
        return max(items, key=lambda k: k.approved_at)

    def exists(self, knowledge_id: str) -> bool:
        """Check if published knowledge exists."""
        return self._get_knowledge_path(knowledge_id).exists()

    def count(self) -> int:
        """Count the number of published knowledge entries."""
        return len(list(self.storage_dir.glob("*.json")))

    def clear(self) -> None:
        """Delete all published knowledge."""
        try:
            for knowledge_file in self.storage_dir.glob("*.json"):
                knowledge_file.unlink()
        except Exception as e:
            raise StorageError("clear", f"Cannot clear repository: {str(e)}")
