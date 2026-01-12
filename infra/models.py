"""SQLAlchemy ORM models for all entities.

Maps domain models to PostgreSQL tables with relationships.
"""

from datetime import datetime
from typing import Optional, List
import uuid

from sqlalchemy import (
    Column, String, DateTime, Integer, Float, Boolean, Text, 
    ForeignKey, Table, Enum, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from infra.database import Base
import enum


# ============================================================================
# EVENT & SESSION MODELS
# ============================================================================

class EventModel(Base):
    """Event entity (ORM)."""
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    display_name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("SessionModel", back_populates="event", cascade="all, delete-orphan")
    projects = relationship("ProjectModel", back_populates="event", cascade="all, delete-orphan")
    executions = relationship("EvaluationExecutionModel", back_populates="event", cascade="all, delete-orphan")
    
    # Indices
    __table_args__ = (
        Index('ix_events_display_name', 'display_name'),
        Index('ix_events_created_at', 'created_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "display_name": self.display_name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class SessionModel(Base):
    """Session entity (ORM)."""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = relationship("EventModel", back_populates="sessions")
    
    # Indices
    __table_args__ = (
        Index('ix_sessions_event_id', 'event_id'),
        Index('ix_sessions_created_at', 'created_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "event_id": str(self.event_id),
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# PROJECT MODEL
# ============================================================================

class ProjectModel(Base):
    """Project entity (ORM)."""
    __tablename__ = "projects"
    
    id = Column(String(255), primary_key=True, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    artifacts_count = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False, default="created", index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    event = relationship("EventModel", back_populates="projects")
    artifacts = relationship("KnowledgeArtifactModel", back_populates="project", cascade="all, delete-orphan")
    published = relationship("PublishedKnowledgeModel", back_populates="project", cascade="all, delete-orphan")
    executions = relationship("EvaluationExecutionModel", back_populates="project", cascade="all, delete-orphan")
    
    # Indices
    __table_args__ = (
        Index('ix_projects_event_id', 'event_id'),
        Index('ix_projects_status', 'status'),
        Index('ix_projects_created_at', 'created_at'),
        Index('ix_projects_event_id_status', 'event_id', 'status'),
    )
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "project_id": self.id,
            "event_id": str(self.event_id),
            "name": self.name,
            "description": self.description,
            "artifacts_count": self.artifacts_count,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# KNOWLEDGE ARTIFACT MODELS
# ============================================================================

class KnowledgeArtifactModel(Base):
    """Knowledge artifact entity (ORM)."""
    __tablename__ = "knowledge_artifacts"
    
    id = Column(String(255), primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    artifact_type = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    source = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="draft", index=True)
    confidence_score = Column(Float, nullable=True)
    extraction_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("ProjectModel", back_populates="artifacts")
    
    # Indices
    __table_args__ = (
        Index('ix_ka_project_id', 'project_id'),
        Index('ix_ka_status', 'status'),
        Index('ix_ka_type', 'artifact_type'),
        Index('ix_ka_created_at', 'created_at'),
        Index('ix_ka_project_status', 'project_id', 'status'),
    )
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "artifact_id": self.id,
            "project_id": self.project_id,
            "artifact_type": self.artifact_type,
            "title": self.title,
            "status": self.status,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class PublishedKnowledgeModel(Base):
    """Published knowledge entity (ORM)."""
    __tablename__ = "published_knowledge"
    
    id = Column(String(255), primary_key=True, index=True)
    project_id = Column(String(255), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    approval_status = Column(String(50), nullable=False, default="pending", index=True)
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("ProjectModel", back_populates="published")
    
    # Indices
    __table_args__ = (
        Index('ix_pk_project_id', 'project_id'),
        Index('ix_pk_approval_status', 'approval_status'),
        Index('ix_pk_created_at', 'created_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "approval_status": self.approval_status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# EVALUATION EXECUTION MODEL
# ============================================================================

class ExecutionStatusEnum(str, enum.Enum):
    """Execution status values."""
    PENDING = "pending"
    RUNNING = "running"
    EVALUATING = "evaluating"
    ITERATING = "iterating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EvaluationExecutionModel(Base):
    """Evaluation execution entity (ORM)."""
    __tablename__ = "evaluation_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(String(255), ForeignKey('projects.id', ondelete='CASCADE'), nullable=False, index=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id', ondelete='CASCADE'), nullable=True, index=True)
    status = Column(Enum(ExecutionStatusEnum), nullable=False, default=ExecutionStatusEnum.PENDING, index=True)
    configuration = Column(String(50), nullable=False, default="standard")
    quality_threshold = Column(Float, nullable=False, default=3.0)
    max_iterations = Column(Integer, nullable=False, default=2)
    current_iteration = Column(Integer, nullable=False, default=0)
    
    # Timing
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=False, default=0.0)
    
    # Results
    final_score = Column(Float, nullable=True)
    final_decision = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Counts
    total_artifacts = Column(Integer, nullable=False, default=0)
    artifacts_passed = Column(Integer, nullable=False, default=0)
    artifacts_failed = Column(Integer, nullable=False, default=0)
    
    # JSON storage for complex data
    iterations_data = Column(JSON, nullable=True)
    final_scorecard = Column(JSON, nullable=True)
    artifact_details = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Relationships
    project = relationship("ProjectModel", back_populates="executions")
    event = relationship("EventModel", back_populates="executions")
    
    # Indices
    __table_args__ = (
        Index('ix_ee_project_id', 'project_id'),
        Index('ix_ee_event_id', 'event_id'),
        Index('ix_ee_status', 'status'),
        Index('ix_ee_created_at', 'created_at'),
        Index('ix_ee_project_status', 'project_id', 'status'),
    )
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "execution_id": str(self.id),
            "project_id": self.project_id,
            "event_id": str(self.event_id) if self.event_id else None,
            "status": self.status.value,
            "configuration": self.configuration,
            "quality_threshold": self.quality_threshold,
            "max_iterations": self.max_iterations,
            "current_iteration": self.current_iteration,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "final_score": self.final_score,
            "final_decision": self.final_decision,
            "duration_seconds": self.duration_seconds
        }
