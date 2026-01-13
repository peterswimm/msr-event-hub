"""
Paper-Specific Knowledge Schema

Extends BaseKnowledgeArtifact with research paper-specific fields.
Implements all requirements from POC spec section 6.1.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from .base_schema import BaseKnowledgeArtifact, ResearchMaturityStage


@dataclass
class DatasetInfo:
    """Information about a dataset used in research"""
    name: str
    size: str  # e.g., "10K samples", "1M examples"
    availability: str  # "public", "private", "on request"
    description: Optional[str] = None
    url: Optional[str] = None


@dataclass
class QuantitativeResult:
    """A quantitative research result"""
    metric: str
    value: str
    context: Optional[str] = None
    comparison_to_baseline: Optional[str] = None


@dataclass
class PaperKnowledgeArtifact(BaseKnowledgeArtifact):
    """Extended knowledge artifact for research papers"""

    # Publication context
    publication_venue: Optional[str] = None  # Conference name or journal
    publication_year: Optional[int] = None
    peer_reviewed: bool = False
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None

    # Related work
    related_prior_work: List[str] = field(default_factory=list)

    # Data and evaluation
    datasets_used: List[DatasetInfo] = field(default_factory=list)
    evaluation_benchmarks: List[str] = field(default_factory=list)
    evaluation_metrics: List[str] = field(default_factory=list)

    # Results
    baseline_comparisons: Optional[str] = None
    key_quantitative_results: List[str] = field(default_factory=list)
    statistical_significance: Optional[str] = None  # "p<0.05", "not reported", etc.

    # Reproducibility
    reproducibility_notes: Optional[str] = None  # "code available at", "data available on request", etc.

    # Maturity assessment
    research_maturity_stage: str = "exploratory"  # exploratory|validated|deployed

    # Ethical considerations
    ethical_considerations_discussed: bool = False
    ethical_summary: Optional[str] = None

    # Results & Evidence (Enhanced)
    key_quantitative_results_structured: List[QuantitativeResult] = field(default_factory=list)
    figures_tables_referenced: List[str] = field(default_factory=list)
    
    # Most Influential Prior Work
    influential_prior_work: List[str] = field(default_factory=list)
    
    # Author-Acknowledged Limitations
    author_acknowledged_limitations: List[str] = field(default_factory=list)
    
    # Additional/Found Knowledge (Spec Section 6.1)
    unanticipated_methods: Optional[str] = None
    side_findings: Optional[str] = None
    domain_crossovers: Optional[str] = None  # e.g., "Applies NLP to computer vision"
    emergent_implications: Optional[str] = None
