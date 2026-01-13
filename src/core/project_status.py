"""Project status enums and execution phase definitions.

This module defines the core status tracking enums used throughout the project
lifecycle, from creation through compilation and archival.
"""

from enum import Enum


class ProjectStatus(str, Enum):
    """Project lifecycle status.
    
    Represents the current state of a project as it moves through the knowledge
    extraction and compilation pipeline.
    """
    CREATED = "created"  # Project created, awaiting agent assignment
    ACTIVE = "active"  # Agents are extracting knowledge artifacts
    IN_REVIEW = "in_review"  # Artifacts under expert review
    READY_FOR_ITERATION = "ready_for_iteration"  # Review complete, ready for refinement
    ITERATING = "iterating"  # Agents refining artifacts based on feedback
    READY_FOR_COMPILATION = "ready_for_compilation"  # All artifacts ready to compile
    COMPILING = "compiling"  # Knowledge compilation in progress
    COMPILED = "compiled"  # Compilation complete, knowledge graph ready
    ARCHIVED = "archived"  # Project archived, no further changes


class ArtifactStatus(str, Enum):
    """Individual artifact status.
    
    Tracks the processing state of each knowledge artifact (paper, talk,
    repository summary) within a project.
    """
    PENDING = "pending"  # Awaiting agent extraction
    EXTRACTED = "extracted"  # Initial extraction complete
    REVIEWED = "reviewed"  # Expert review complete with scores
    NEEDS_ITERATION = "needs_iteration"  # Review identified issues for refinement
    ITERATED = "iterated"  # Refinement complete, resubmitted
    ACCEPTED = "accepted"  # Ready for compilation
    FAILED = "failed"  # Extraction or review failed


class ExecutionPhase(str, Enum):
    """Project execution phases.
    
    Defines the distinct phases of knowledge extraction and compilation,
    enabling phase-specific behavior and rollup metrics.
    """
    PHASE_PREPARATION = "preparation"  # Project definition and agent assignment
    PHASE_EXTRACTION = "extraction"  # Agent-based knowledge artifact extraction
    PHASE_REVIEW = "review"  # Expert review and scoring
    PHASE_ITERATION = "iteration"  # Refinement cycles based on feedback
    PHASE_COMPILATION = "compilation"  # Knowledge synthesis and graph building
    PHASE_COMPLETE = "complete"  # All phases finished


class ReviewStatus(str, Enum):
    """Review completion status for artifacts.
    
    Distinguishes between expert reviews in progress and completed reviews.
    """
    NOT_REVIEWED = "not_reviewed"  # Review not yet started
    IN_PROGRESS = "in_progress"  # Review currently underway
    COMPLETED = "completed"  # Review complete
    REJECTED = "rejected"  # Review determined artifact should be rejected/redone
