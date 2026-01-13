"""
Repository-Specific Knowledge Schema

Extends BaseKnowledgeArtifact with code/model repository-specific fields.
Implements all requirements from POC spec section 6.3.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from .base_schema import BaseKnowledgeArtifact


@dataclass
class RepositoryKnowledgeArtifact(BaseKnowledgeArtifact):
    """Extended knowledge artifact for code/model repositories"""

    # Artifact classification
    artifact_type: str = "framework"  # sdk|service|model|dataset|framework|tool|other
    primary_purpose: Optional[str] = None
    intended_users: str = "developers"  # researchers|practitioners|enterprises|general

    # Technology stack
    primary_languages: List[str] = field(default_factory=list)  # Python, C++, etc.
    key_frameworks: List[str] = field(default_factory=list)  # PyTorch, TensorFlow, etc.
    supported_platforms: List[str] = field(default_factory=list)  # Linux, macOS, Windows

    # Operational requirements
    hardware_dependencies: Optional[str] = None  # "GPU with 8GB VRAM", "CPU-only", etc.
    installation_complexity: str = "medium"  # low|medium|high
    setup_prerequisites: List[str] = field(default_factory=list)

    # Training/Inference context
    training_environment: Optional[str] = None  # "GPU required", "CPU-only", etc.
    inference_environment: Optional[str] = None
    inference_speed: Optional[str] = None  # "100ms per sample on GPU"

    # Dependencies
    runtime_dependencies: List[str] = field(default_factory=list)
    restrictive_external_dependencies: List[str] = field(default_factory=list)

    # API and usage
    example_use_cases: List[str] = field(default_factory=list)
    api_surface_summary: Optional[str] = None  # High-level overview of API
    model_or_system_limitations: List[str] = field(default_factory=list)

    # Project maturity
    maintenance_status: str = "active"  # active|experimental|archived|dormant
    license: Optional[str] = None  # MIT, Apache2.0, GPL, proprietary, etc.

    # Data usage
    data_usage_constraints: Optional[str] = None  # "For research use only", etc.
    training_data_source: Optional[str] = None

    # Design insights
    implicit_design_decisions: Optional[str] = None
    undocumented_workflows: Optional[str] = None
    performance_caveats: Optional[str] = None
    community_patterns: Optional[str] = None  # Common usage patterns from community
