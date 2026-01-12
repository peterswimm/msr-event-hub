"""SQLAlchemy-based repositories for database persistence.

Replaces JSON file-based storage from Phase B/C/D.
Provides CRUD operations with transaction safety and relationship management.
"""

from typing import List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from infra.models import (
    EventModel, SessionModel, ProjectModel, KnowledgeArtifactModel,
    PublishedKnowledgeModel, EvaluationExecutionModel, ExecutionStatusEnum
)
from core_interfaces import (
    Event, Session as SessionInterface, Project, KnowledgeArtifact,
    PublishedKnowledge, EvaluationExecution
)


class BaseRepository:
    """Base repository with common CRUD operations."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def commit(self) -> None:
        """Commit current transaction."""
        self.session.commit()
    
    def rollback(self) -> None:
        """Rollback current transaction."""
        self.session.rollback()
    
    def flush(self) -> None:
        """Flush pending changes without committing."""
        self.session.flush()


class EventRepository(BaseRepository):
    """Repository for Event entities."""
    
    def create(self, event: Event) -> Event:
        """Create new event in database.
        
        Args:
            event: Event to create
            
        Returns:
            Created event with database ID
        """
        db_event = EventModel(
            id=event.id,
            display_name=event.display_name,
            description=getattr(event, 'description', None),
            created_at=event.created_at,
            updated_at=event.updated_at
        )
        self.session.add(db_event)
        self.session.flush()
        return self._to_domain(db_event)
    
    def get(self, event_id: str) -> Optional[Event]:
        """Get event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event or None if not found
        """
        db_event = self.session.query(EventModel).filter(
            EventModel.id == event_id
        ).first()
        return self._to_domain(db_event) if db_event else None
    
    def get_all(self) -> List[Event]:
        """Get all events.
        
        Returns:
            List of all events
        """
        db_events = self.session.query(EventModel).order_by(
            EventModel.created_at.desc()
        ).all()
        return [self._to_domain(e) for e in db_events]
    
    def update(self, event: Event) -> Event:
        """Update existing event.
        
        Args:
            event: Updated event
            
        Returns:
            Updated event
        """
        db_event = self.session.query(EventModel).filter(
            EventModel.id == event.id
        ).first()
        
        if not db_event:
            raise ValueError(f"Event {event.id} not found")
        
        db_event.display_name = event.display_name
        db_event.description = getattr(event, 'description', None)
        db_event.updated_at = datetime.utcnow()
        self.session.flush()
        return self._to_domain(db_event)
    
    def delete(self, event_id: str) -> None:
        """Delete event by ID.
        
        Args:
            event_id: Event ID
        """
        self.session.query(EventModel).filter(
            EventModel.id == event_id
        ).delete()
        self.session.flush()
    
    @staticmethod
    def _to_domain(db_event: EventModel) -> Event:
        """Convert database model to domain model."""
        return Event(
            id=str(db_event.id),
            display_name=db_event.display_name,
            description=db_event.description,
            created_at=db_event.created_at,
            updated_at=db_event.updated_at
        )


class SessionRepository(BaseRepository):
    """Repository for Session entities."""
    
    def create(self, session: SessionInterface) -> SessionInterface:
        """Create new session in database.
        
        Args:
            session: Session to create
            
        Returns:
            Created session
        """
        db_session = SessionModel(
            id=session.id,
            event_id=session.event_id,
            name=getattr(session, 'name', None),
            created_at=session.created_at,
            updated_at=session.updated_at
        )
        self.session.add(db_session)
        self.session.flush()
        return self._to_domain(db_session)
    
    def get(self, session_id: str) -> Optional[SessionInterface]:
        """Get session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session or None if not found
        """
        db_session = self.session.query(SessionModel).filter(
            SessionModel.id == session_id
        ).first()
        return self._to_domain(db_session) if db_session else None
    
    def get_by_event(self, event_id: str) -> List[SessionInterface]:
        """Get all sessions for an event.
        
        Args:
            event_id: Event ID
            
        Returns:
            List of sessions
        """
        db_sessions = self.session.query(SessionModel).filter(
            SessionModel.event_id == event_id
        ).order_by(SessionModel.created_at.desc()).all()
        return [self._to_domain(s) for s in db_sessions]
    
    @staticmethod
    def _to_domain(db_session: SessionModel) -> SessionInterface:
        """Convert database model to domain model."""
        return SessionInterface(
            id=str(db_session.id),
            event_id=str(db_session.event_id),
            name=db_session.name,
            created_at=db_session.created_at,
            updated_at=db_session.updated_at
        )


class ProjectRepository(BaseRepository):
    """Repository for Project entities."""
    
    def create(self, project: Project) -> Project:
        """Create new project in database.
        
        Args:
            project: Project to create
            
        Returns:
            Created project
        """
        db_project = ProjectModel(
            id=project.id,
            event_id=project.event_id,
            name=project.name,
            description=project.description,
            artifacts_count=project.artifacts_count,
            status=project.status,
            metadata=project.metadata,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
        self.session.add(db_project)
        self.session.flush()
        return self._to_domain(db_project)
    
    def get(self, project_id: str) -> Optional[Project]:
        """Get project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project or None if not found
        """
        db_project = self.session.query(ProjectModel).filter(
            ProjectModel.id == project_id
        ).first()
        return self._to_domain(db_project) if db_project else None
    
    def get_by_event(self, event_id: str) -> List[Project]:
        """Get all projects for an event.
        
        Args:
            event_id: Event ID
            
        Returns:
            List of projects
        """
        db_projects = self.session.query(ProjectModel).filter(
            ProjectModel.event_id == event_id
        ).order_by(ProjectModel.created_at.desc()).all()
        return [self._to_domain(p) for p in db_projects]
    
    def get_by_status(self, event_id: str, status: str) -> List[Project]:
        """Get projects by event and status.
        
        Args:
            event_id: Event ID
            status: Project status
            
        Returns:
            List of projects with specified status
        """
        db_projects = self.session.query(ProjectModel).filter(
            and_(
                ProjectModel.event_id == event_id,
                ProjectModel.status == status
            )
        ).order_by(ProjectModel.created_at.desc()).all()
        return [self._to_domain(p) for p in db_projects]
    
    def update(self, project: Project) -> Project:
        """Update existing project.
        
        Args:
            project: Updated project
            
        Returns:
            Updated project
        """
        db_project = self.session.query(ProjectModel).filter(
            ProjectModel.id == project.id
        ).first()
        
        if not db_project:
            raise ValueError(f"Project {project.id} not found")
        
        db_project.name = project.name
        db_project.description = project.description
        db_project.artifacts_count = project.artifacts_count
        db_project.status = project.status
        db_project.metadata = project.metadata
        db_project.updated_at = datetime.utcnow()
        self.session.flush()
        return self._to_domain(db_project)
    
    def delete(self, project_id: str) -> None:
        """Delete project by ID.
        
        Args:
            project_id: Project ID
        """
        self.session.query(ProjectModel).filter(
            ProjectModel.id == project_id
        ).delete()
        self.session.flush()
    
    @staticmethod
    def _to_domain(db_project: ProjectModel) -> Project:
        """Convert database model to domain model."""
        return Project(
            id=db_project.id,
            event_id=str(db_project.event_id),
            name=db_project.name,
            description=db_project.description,
            artifacts_count=db_project.artifacts_count,
            status=db_project.status,
            metadata=db_project.metadata or {},
            created_at=db_project.created_at,
            updated_at=db_project.updated_at
        )


class KnowledgeArtifactRepository(BaseRepository):
    """Repository for KnowledgeArtifact entities."""
    
    def create(self, artifact: KnowledgeArtifact) -> KnowledgeArtifact:
        """Create new knowledge artifact in database.
        
        Args:
            artifact: Artifact to create
            
        Returns:
            Created artifact
        """
        db_artifact = KnowledgeArtifactModel(
            id=artifact.id,
            project_id=artifact.project_id,
            artifact_type=artifact.artifact_type,
            title=artifact.title,
            content=artifact.content,
            source=getattr(artifact, 'source', None),
            status=artifact.status,
            confidence_score=getattr(artifact, 'confidence_score', None),
            extraction_metadata=getattr(artifact, 'extraction_metadata', None),
            created_at=artifact.created_at,
            updated_at=artifact.updated_at
        )
        self.session.add(db_artifact)
        self.session.flush()
        return self._to_domain(db_artifact)
    
    def get(self, artifact_id: str) -> Optional[KnowledgeArtifact]:
        """Get artifact by ID.
        
        Args:
            artifact_id: Artifact ID
            
        Returns:
            Artifact or None if not found
        """
        db_artifact = self.session.query(KnowledgeArtifactModel).filter(
            KnowledgeArtifactModel.id == artifact_id
        ).first()
        return self._to_domain(db_artifact) if db_artifact else None
    
    def get_by_project(self, project_id: str) -> List[KnowledgeArtifact]:
        """Get all artifacts for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of artifacts
        """
        db_artifacts = self.session.query(KnowledgeArtifactModel).filter(
            KnowledgeArtifactModel.project_id == project_id
        ).order_by(KnowledgeArtifactModel.created_at.desc()).all()
        return [self._to_domain(a) for a in db_artifacts]
    
    def get_by_status(self, project_id: str, status: str) -> List[KnowledgeArtifact]:
        """Get artifacts by project and status.
        
        Args:
            project_id: Project ID
            status: Artifact status
            
        Returns:
            List of artifacts with specified status
        """
        db_artifacts = self.session.query(KnowledgeArtifactModel).filter(
            and_(
                KnowledgeArtifactModel.project_id == project_id,
                KnowledgeArtifactModel.status == status
            )
        ).order_by(KnowledgeArtifactModel.created_at.desc()).all()
        return [self._to_domain(a) for a in db_artifacts]
    
    def update(self, artifact: KnowledgeArtifact) -> KnowledgeArtifact:
        """Update existing artifact.
        
        Args:
            artifact: Updated artifact
            
        Returns:
            Updated artifact
        """
        db_artifact = self.session.query(KnowledgeArtifactModel).filter(
            KnowledgeArtifactModel.id == artifact.id
        ).first()
        
        if not db_artifact:
            raise ValueError(f"Artifact {artifact.id} not found")
        
        db_artifact.title = artifact.title
        db_artifact.content = artifact.content
        db_artifact.status = artifact.status
        db_artifact.confidence_score = getattr(artifact, 'confidence_score', None)
        db_artifact.extraction_metadata = getattr(artifact, 'extraction_metadata', None)
        db_artifact.updated_at = datetime.utcnow()
        self.session.flush()
        return self._to_domain(db_artifact)
    
    def delete(self, artifact_id: str) -> None:
        """Delete artifact by ID.
        
        Args:
            artifact_id: Artifact ID
        """
        self.session.query(KnowledgeArtifactModel).filter(
            KnowledgeArtifactModel.id == artifact_id
        ).delete()
        self.session.flush()
    
    @staticmethod
    def _to_domain(db_artifact: KnowledgeArtifactModel) -> KnowledgeArtifact:
        """Convert database model to domain model."""
        return KnowledgeArtifact(
            id=db_artifact.id,
            project_id=db_artifact.project_id,
            artifact_type=db_artifact.artifact_type,
            title=db_artifact.title,
            content=db_artifact.content,
            source=db_artifact.source,
            status=db_artifact.status,
            confidence_score=db_artifact.confidence_score,
            extraction_metadata=db_artifact.extraction_metadata or {},
            created_at=db_artifact.created_at,
            updated_at=db_artifact.updated_at
        )


class PublishedKnowledgeRepository(BaseRepository):
    """Repository for PublishedKnowledge entities."""
    
    def create(self, knowledge: PublishedKnowledge) -> PublishedKnowledge:
        """Create new published knowledge in database.
        
        Args:
            knowledge: Published knowledge to create
            
        Returns:
            Created published knowledge
        """
        db_knowledge = PublishedKnowledgeModel(
            id=knowledge.id,
            project_id=knowledge.project_id,
            title=knowledge.title,
            summary=getattr(knowledge, 'summary', None),
            content=getattr(knowledge, 'content', None),
            approval_status=knowledge.approval_status,
            approved_by=getattr(knowledge, 'approved_by', None),
            approved_at=getattr(knowledge, 'approved_at', None),
            created_at=knowledge.created_at,
            updated_at=knowledge.updated_at
        )
        self.session.add(db_knowledge)
        self.session.flush()
        return self._to_domain(db_knowledge)
    
    def get(self, knowledge_id: str) -> Optional[PublishedKnowledge]:
        """Get published knowledge by ID.
        
        Args:
            knowledge_id: Published knowledge ID
            
        Returns:
            Published knowledge or None if not found
        """
        db_knowledge = self.session.query(PublishedKnowledgeModel).filter(
            PublishedKnowledgeModel.id == knowledge_id
        ).first()
        return self._to_domain(db_knowledge) if db_knowledge else None
    
    def get_by_project(self, project_id: str) -> List[PublishedKnowledge]:
        """Get all published knowledge for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of published knowledge
        """
        db_knowledge_list = self.session.query(PublishedKnowledgeModel).filter(
            PublishedKnowledgeModel.project_id == project_id
        ).order_by(PublishedKnowledgeModel.created_at.desc()).all()
        return [self._to_domain(k) for k in db_knowledge_list]
    
    def get_by_approval_status(self, project_id: str, status: str) -> List[PublishedKnowledge]:
        """Get published knowledge by project and approval status.
        
        Args:
            project_id: Project ID
            status: Approval status
            
        Returns:
            List of published knowledge with specified status
        """
        db_knowledge_list = self.session.query(PublishedKnowledgeModel).filter(
            and_(
                PublishedKnowledgeModel.project_id == project_id,
                PublishedKnowledgeModel.approval_status == status
            )
        ).order_by(PublishedKnowledgeModel.created_at.desc()).all()
        return [self._to_domain(k) for k in db_knowledge_list]
    
    def update(self, knowledge: PublishedKnowledge) -> PublishedKnowledge:
        """Update existing published knowledge.
        
        Args:
            knowledge: Updated published knowledge
            
        Returns:
            Updated published knowledge
        """
        db_knowledge = self.session.query(PublishedKnowledgeModel).filter(
            PublishedKnowledgeModel.id == knowledge.id
        ).first()
        
        if not db_knowledge:
            raise ValueError(f"Published knowledge {knowledge.id} not found")
        
        db_knowledge.title = knowledge.title
        db_knowledge.summary = getattr(knowledge, 'summary', None)
        db_knowledge.content = getattr(knowledge, 'content', None)
        db_knowledge.approval_status = knowledge.approval_status
        db_knowledge.approved_by = getattr(knowledge, 'approved_by', None)
        db_knowledge.approved_at = getattr(knowledge, 'approved_at', None)
        db_knowledge.updated_at = datetime.utcnow()
        self.session.flush()
        return self._to_domain(db_knowledge)
    
    def delete(self, knowledge_id: str) -> None:
        """Delete published knowledge by ID.
        
        Args:
            knowledge_id: Published knowledge ID
        """
        self.session.query(PublishedKnowledgeModel).filter(
            PublishedKnowledgeModel.id == knowledge_id
        ).delete()
        self.session.flush()
    
    @staticmethod
    def _to_domain(db_knowledge: PublishedKnowledgeModel) -> PublishedKnowledge:
        """Convert database model to domain model."""
        return PublishedKnowledge(
            id=db_knowledge.id,
            project_id=db_knowledge.project_id,
            title=db_knowledge.title,
            summary=db_knowledge.summary,
            content=db_knowledge.content,
            approval_status=db_knowledge.approval_status,
            approved_by=db_knowledge.approved_by,
            approved_at=db_knowledge.approved_at,
            created_at=db_knowledge.created_at,
            updated_at=db_knowledge.updated_at
        )


class EvaluationExecutionRepository(BaseRepository):
    """Repository for EvaluationExecution entities."""
    
    def create(self, execution: EvaluationExecution) -> EvaluationExecution:
        """Create new evaluation execution in database.
        
        Args:
            execution: Execution to create
            
        Returns:
            Created execution
        """
        db_execution = EvaluationExecutionModel(
            id=execution.id,
            project_id=execution.project_id,
            event_id=execution.event_id,
            status=ExecutionStatusEnum[execution.status.upper()],
            configuration=execution.configuration,
            quality_threshold=execution.quality_threshold,
            max_iterations=execution.max_iterations,
            current_iteration=execution.current_iteration,
            created_at=execution.created_at,
            started_at=getattr(execution, 'started_at', None),
            completed_at=getattr(execution, 'completed_at', None),
            duration_seconds=execution.duration_seconds,
            final_score=getattr(execution, 'final_score', None),
            final_decision=getattr(execution, 'final_decision', None),
            error_message=getattr(execution, 'error_message', None),
            total_artifacts=execution.total_artifacts,
            artifacts_passed=execution.artifacts_passed,
            artifacts_failed=execution.artifacts_failed,
            iterations_data=getattr(execution, 'iterations_data', None),
            final_scorecard=getattr(execution, 'final_scorecard', None),
            artifact_details=getattr(execution, 'artifact_details', None),
            tags=getattr(execution, 'tags', None),
            updated_at=execution.updated_at
        )
        self.session.add(db_execution)
        self.session.flush()
        return self._to_domain(db_execution)
    
    def get(self, execution_id: str) -> Optional[EvaluationExecution]:
        """Get execution by ID.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution or None if not found
        """
        db_execution = self.session.query(EvaluationExecutionModel).filter(
            EvaluationExecutionModel.id == execution_id
        ).first()
        return self._to_domain(db_execution) if db_execution else None
    
    def get_by_project(self, project_id: str) -> List[EvaluationExecution]:
        """Get all executions for a project.
        
        Args:
            project_id: Project ID
            
        Returns:
            List of executions
        """
        db_executions = self.session.query(EvaluationExecutionModel).filter(
            EvaluationExecutionModel.project_id == project_id
        ).order_by(EvaluationExecutionModel.created_at.desc()).all()
        return [self._to_domain(e) for e in db_executions]
    
    def get_by_status(self, project_id: str, status: str) -> List[EvaluationExecution]:
        """Get executions by project and status.
        
        Args:
            project_id: Project ID
            status: Execution status
            
        Returns:
            List of executions with specified status
        """
        status_enum = ExecutionStatusEnum[status.upper()]
        db_executions = self.session.query(EvaluationExecutionModel).filter(
            and_(
                EvaluationExecutionModel.project_id == project_id,
                EvaluationExecutionModel.status == status_enum
            )
        ).order_by(EvaluationExecutionModel.created_at.desc()).all()
        return [self._to_domain(e) for e in db_executions]
    
    def update(self, execution: EvaluationExecution) -> EvaluationExecution:
        """Update existing execution.
        
        Args:
            execution: Updated execution
            
        Returns:
            Updated execution
        """
        db_execution = self.session.query(EvaluationExecutionModel).filter(
            EvaluationExecutionModel.id == execution.id
        ).first()
        
        if not db_execution:
            raise ValueError(f"Execution {execution.id} not found")
        
        db_execution.status = ExecutionStatusEnum[execution.status.upper()]
        db_execution.current_iteration = execution.current_iteration
        db_execution.started_at = getattr(execution, 'started_at', None)
        db_execution.completed_at = getattr(execution, 'completed_at', None)
        db_execution.duration_seconds = execution.duration_seconds
        db_execution.final_score = getattr(execution, 'final_score', None)
        db_execution.final_decision = getattr(execution, 'final_decision', None)
        db_execution.error_message = getattr(execution, 'error_message', None)
        db_execution.artifacts_passed = execution.artifacts_passed
        db_execution.artifacts_failed = execution.artifacts_failed
        db_execution.iterations_data = getattr(execution, 'iterations_data', None)
        db_execution.final_scorecard = getattr(execution, 'final_scorecard', None)
        db_execution.artifact_details = getattr(execution, 'artifact_details', None)
        db_execution.tags = getattr(execution, 'tags', None)
        db_execution.updated_at = datetime.utcnow()
        self.session.flush()
        return self._to_domain(db_execution)
    
    def delete(self, execution_id: str) -> None:
        """Delete execution by ID.
        
        Args:
            execution_id: Execution ID
        """
        self.session.query(EvaluationExecutionModel).filter(
            EvaluationExecutionModel.id == execution_id
        ).delete()
        self.session.flush()
    
    @staticmethod
    def _to_domain(db_execution: EvaluationExecutionModel) -> EvaluationExecution:
        """Convert database model to domain model."""
        return EvaluationExecution(
            id=str(db_execution.id),
            project_id=db_execution.project_id,
            event_id=str(db_execution.event_id) if db_execution.event_id else None,
            status=db_execution.status.value,
            configuration=db_execution.configuration,
            quality_threshold=db_execution.quality_threshold,
            max_iterations=db_execution.max_iterations,
            current_iteration=db_execution.current_iteration,
            created_at=db_execution.created_at,
            started_at=db_execution.started_at,
            completed_at=db_execution.completed_at,
            duration_seconds=db_execution.duration_seconds,
            final_score=db_execution.final_score,
            final_decision=db_execution.final_decision,
            error_message=db_execution.error_message,
            total_artifacts=db_execution.total_artifacts,
            artifacts_passed=db_execution.artifacts_passed,
            artifacts_failed=db_execution.artifacts_failed,
            iterations_data=db_execution.iterations_data or {},
            final_scorecard=db_execution.final_scorecard or {},
            artifact_details=db_execution.artifact_details or {},
            tags=db_execution.tags or [],
            updated_at=db_execution.updated_at
        )
