"""
Talk-Specific Knowledge Schema

Extends BaseKnowledgeArtifact with research talk/transcript-specific fields.
Implements all requirements from POC spec section 6.2.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from .base_schema import BaseKnowledgeArtifact


@dataclass
class TalkSection:
    """Section of a talk with timing information"""
    title: str
    start_minute: int
    duration_minutes: int
    description: Optional[str] = None
    time_code: Optional[str] = None  # e.g., "01:23:45"


@dataclass
class KeySegment:
    """Time-coded key segment in talk"""
    time_code: str
    title: str
    description: str
    importance: str  # "high", "medium", "low"


@dataclass
class TalkKnowledgeArtifact(BaseKnowledgeArtifact):
    """Extended knowledge artifact for research talks and transcripts"""

    # Talk metadata
    talk_type: str = "research_update"  # research_update|keynote|demo|tutorial|other
    duration_minutes: Optional[int] = None

    # Presentation Structure (Spec Section 6.2)
    section_breakdown: List[TalkSection] = field(default_factory=list)
    key_segments: List[KeySegment] = field(default_factory=list)  # Time-coded highlights

    # Demonstrations
    demo_included: bool = False
    demo_description: Optional[str] = None
    demo_type: Optional[str] = None  # "live", "recorded", "simulated"

    # Demonstration & Evidence (Spec Section 6.2)
    experimental_results_discussed: List[str] = field(default_factory=list)
    
    # Challenges & Forward-Looking Content (Spec Section 6.2)
    technical_challenges_mentioned: List[str] = field(default_factory=list)
    open_risks: List[str] = field(default_factory=list)
    pending_experiments: List[str] = field(default_factory=list)
    next_milestones: List[str] = field(default_factory=list)
    collaboration_requests: List[str] = field(default_factory=list)

    # Audience context
    intended_audience: str = "technical"  # technical|general|mixed
    technical_depth_level: str = "intermediate"  # introductory|intermediate|advanced
    assumed_background: Optional[str] = None

    # Engagement signals
    off_script_insights: Optional[str] = None  # Speaker asides and elaborations
    implicit_assumptions: List[str] = field(default_factory=list)
    audience_qa_signals: Optional[str] = None  # What questions revealed about understanding
    strategic_hints: Optional[str] = None  # Hints about commercialization, roadmap, etc.

    # Confidence markers
    speaker_confidence_markers: Optional[str] = None  # Hedging language, uncertainty indicators
