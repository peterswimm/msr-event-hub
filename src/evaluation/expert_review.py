"""
Expert Review System

Implements the expert review process from POC spec section 8.
Reviews extractions across 5 dimensions with 1-5 scale ratings.
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from src.core.schemas.base_schema import BaseKnowledgeArtifact


class ReviewDimension(str, Enum):
    """Expert review dimensions from spec."""
    FACTUAL_ACCURACY = "factual_accuracy"
    COMPLETENESS = "completeness"
    FAITHFULNESS_TO_SOURCE = "faithfulness_to_source"
    SIGNAL_TO_NOISE = "signal_to_noise_ratio"
    REUSABILITY = "reusability_for_ai"


@dataclass
class DimensionScore:
    """Score for a single review dimension."""
    dimension: ReviewDimension
    score: float  # 1-5 scale
    rationale: str
    specific_issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "dimension": self.dimension.value,
            "score": self.score,
            "rationale": self.rationale,
            "specific_issues": self.specific_issues
        }


@dataclass
class ExpertReview:
    """
    Expert review of a knowledge extraction.
    
    Evaluates extraction quality across 5 dimensions on 1-5 scale:
    - 1: Poor (major issues, significant rework needed)
    - 2: Below Average (several issues, needs improvement)
    - 3: Acceptable (meets minimum bar, some gaps)
    - 4: Good (solid quality, minor gaps)
    - 5: Excellent (comprehensive, accurate, highly reusable)
    """
    
    artifact_title: str
    artifact_type: str
    reviewer: str  # "automated" or human reviewer name
    
    dimension_scores: List[DimensionScore] = field(default_factory=list)
    
    overall_score: float = 0.0
    overall_comments: str = ""
    
    approved: bool = False
    requires_iteration: bool = False
    
    def calculate_overall_score(self) -> float:
        """Calculate overall score as average of dimension scores."""
        if not self.dimension_scores:
            return 0.0
        
        total = sum(s.score for s in self.dimension_scores)
        self.overall_score = total / len(self.dimension_scores)
        return self.overall_score
    
    def get_weakest_dimension(self) -> Optional[DimensionScore]:
        """Get the dimension with lowest score."""
        if not self.dimension_scores:
            return None
        return min(self.dimension_scores, key=lambda s: s.score)
    
    def get_strongest_dimension(self) -> Optional[DimensionScore]:
        """Get the dimension with highest score."""
        if not self.dimension_scores:
            return None
        return max(self.dimension_scores, key=lambda s: s.score)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "artifact_title": self.artifact_title,
            "artifact_type": self.artifact_type,
            "reviewer": self.reviewer,
            "dimension_scores": [s.to_dict() for s in self.dimension_scores],
            "overall_score": self.overall_score,
            "overall_comments": self.overall_comments,
            "approved": self.approved,
            "requires_iteration": self.requires_iteration
        }


# ============================================================================
# REVIEW DIMENSION EVALUATORS
# ============================================================================

def evaluate_factual_accuracy(artifact: BaseKnowledgeArtifact) -> DimensionScore:
    """
    Evaluate factual accuracy of extraction.
    
    Checks:
    - Are claims supported by source?
    - Are technical details correct?
    - Are citations/references accurate?
    """
    # Automated heuristics (in production, would use LLM judge)
    issues = []
    score = 5.0
    
    # Check if key fields are populated
    if not artifact.key_evidence_citations:
        issues.append("No evidence or citations provided")
        score -= 1.0
    
    if not artifact.technical_problem_addressed:
        issues.append("Technical problem not clearly stated")
        score -= 0.5
    
    # Check confidence score
    if hasattr(artifact, 'confidence_score'):
        if artifact.confidence_score < 0.7:
            issues.append(f"Low confidence score: {artifact.confidence_score}")
            score -= 0.5
    
    score = max(1.0, score)
    
    return DimensionScore(
        dimension=ReviewDimension.FACTUAL_ACCURACY,
        score=score,
        rationale=f"Automated evaluation of factual accuracy. {len(issues)} issues found.",
        specific_issues=issues
    )


def evaluate_completeness(artifact: BaseKnowledgeArtifact) -> DimensionScore:
    """
    Evaluate completeness of extraction.
    
    Checks:
    - Are all required baseline fields populated?
    - Are datatype-specific fields complete?
    - Is additional_knowledge explored?
    """
    issues = []
    score = 5.0
    
    # Check baseline required fields
    required_fields = [
        'contributors',
        'plain_language_overview',
        'technical_problem_addressed',
        'key_methods_approach',
        'primary_claims_capabilities',
        'limitations_constraints',
        'potential_impact'
    ]
    
    for field_name in required_fields:
        value = getattr(artifact, field_name, None)
        if not value or (isinstance(value, (list, dict)) and len(value) == 0):
            issues.append(f"Missing or empty: {field_name}")
            score -= 0.5
    
    # Check additional_knowledge
    if hasattr(artifact, 'additional_knowledge'):
        if not artifact.additional_knowledge:
            issues.append("additional_knowledge not explored")
            score -= 0.3
    
    score = max(1.0, score)
    
    return DimensionScore(
        dimension=ReviewDimension.COMPLETENESS,
        score=score,
        rationale=f"Checked {len(required_fields)} baseline fields. {len(issues)} issues found.",
        specific_issues=issues
    )


def evaluate_faithfulness_to_source(artifact: BaseKnowledgeArtifact) -> DimensionScore:
    """
    Evaluate faithfulness to source material.
    
    Checks:
    - Does extraction stay true to source?
    - Are there unwarranted extrapolations?
    - Is provenance clear?
    """
    issues = []
    score = 5.0
    
    # Check provenance
    if hasattr(artifact, 'provenance'):
        if not artifact.provenance:
            issues.append("Provenance information missing")
            score -= 1.0
    else:
        issues.append("No provenance tracking")
        score -= 1.0
    
    # Check confidence reasoning
    if hasattr(artifact, 'confidence_reasoning'):
        if not artifact.confidence_reasoning:
            issues.append("No confidence reasoning provided")
            score -= 0.5
    
    score = max(1.0, score)
    
    return DimensionScore(
        dimension=ReviewDimension.FAITHFULNESS_TO_SOURCE,
        score=score,
        rationale="Evaluated provenance tracking and confidence reasoning.",
        specific_issues=issues
    )


def evaluate_signal_to_noise(artifact: BaseKnowledgeArtifact) -> DimensionScore:
    """
    Evaluate signal-to-noise ratio.
    
    Checks:
    - Is information high-value and actionable?
    - Is there unnecessary detail or fluff?
    - Are key insights highlighted?
    """
    issues = []
    score = 5.0
    
    # Check for overly verbose fields (heuristic: >500 chars might be too verbose)
    if len(artifact.plain_language_overview) > 500:
        issues.append("Plain language overview may be too verbose")
        score -= 0.3
    
    # Check if key insights are captured
    if not artifact.primary_claims_capabilities:
        issues.append("Primary claims/capabilities not clearly identified")
        score -= 0.5
    
    if not artifact.open_questions_future_work:
        issues.append("Open questions/future work not identified")
        score -= 0.3
    
    score = max(1.0, score)
    
    return DimensionScore(
        dimension=ReviewDimension.SIGNAL_TO_NOISE,
        score=score,
        rationale="Evaluated information density and actionability.",
        specific_issues=issues
    )


def evaluate_reusability_for_ai(artifact: BaseKnowledgeArtifact) -> DimensionScore:
    """
    Evaluate AI reusability.
    
    Checks:
    - Is extraction well-structured for AI consumption?
    - Are fields properly typed and formatted?
    - Is metadata sufficient for retrieval?
    """
    issues = []
    score = 5.0
    
    # Check structured data quality
    if not artifact.contributors:
        issues.append("Contributors list empty")
        score -= 0.5
    
    if not artifact.limitations_constraints:
        issues.append("Limitations not structured")
        score -= 0.5
    
    # Check metadata
    if not hasattr(artifact, 'source_type') or not artifact.source_type:
        issues.append("Source type not specified")
        score -= 0.3
    
    # Check for structured lists vs text blobs
    if isinstance(artifact.primary_claims_capabilities, str):
        issues.append("Primary claims should be list, not string")
        score -= 0.5
    
    score = max(1.0, score)
    
    return DimensionScore(
        dimension=ReviewDimension.REUSABILITY,
        score=score,
        rationale="Evaluated structure, typing, and metadata for AI consumption.",
        specific_issues=issues
    )


# ============================================================================
# MAIN REVIEW FUNCTION
# ============================================================================

async def run_expert_review(
    artifact: BaseKnowledgeArtifact,
    reviewer: str = "automated",
    minimum_passing_score: float = 3.0
) -> ExpertReview:
    """
    Run expert review on a knowledge artifact.
    
    Args:
        artifact: The knowledge artifact to review
        reviewer: Name of reviewer (default: "automated")
        minimum_passing_score: Minimum score to pass (default: 3.0)
        
    Returns:
        ExpertReview with scores across all dimensions
    """
    review = ExpertReview(
        artifact_title=artifact.title,
        artifact_type=artifact.source_type,
        reviewer=reviewer
    )
    
    # Evaluate all dimensions
    review.dimension_scores = [
        evaluate_factual_accuracy(artifact),
        evaluate_completeness(artifact),
        evaluate_faithfulness_to_source(artifact),
        evaluate_signal_to_noise(artifact),
        evaluate_reusability_for_ai(artifact)
    ]
    
    # Calculate overall score
    review.calculate_overall_score()
    
    # Determine if approved
    review.approved = review.overall_score >= minimum_passing_score
    review.requires_iteration = not review.approved
    
    # Generate overall comments
    weakest = review.get_weakest_dimension()
    strongest = review.get_strongest_dimension()
    
    comments = []
    comments.append(f"Overall Score: {review.overall_score:.1f}/5.0")
    
    if weakest:
        comments.append(
            f"Weakest dimension: {weakest.dimension.value} "
            f"({weakest.score:.1f}/5.0) - {weakest.rationale}"
        )
    
    if strongest:
        comments.append(
            f"Strongest dimension: {strongest.dimension.value} "
            f"({strongest.score:.1f}/5.0)"
        )
    
    if review.approved:
        comments.append("✓ APPROVED - Meets minimum quality threshold")
    else:
        comments.append("✗ REQUIRES ITERATION - Below quality threshold")
    
    review.overall_comments = " | ".join(comments)
    
    return review


# ============================================================================
# REVIEW TEMPLATES
# ============================================================================

REVIEW_TEMPLATE_INSTRUCTIONS = """
# Expert Review Instructions

Review the extracted knowledge artifact across 5 dimensions:

## 1. Factual Accuracy (1-5)
- Are claims supported by the source material?
- Are technical details correct and precise?
- Are citations and references accurate?
- Is there any hallucination or extrapolation?

Score:
- 5: All facts verified, no inaccuracies
- 4: Mostly accurate, minor issues
- 3: Generally accurate, some concerns
- 2: Several inaccuracies present
- 1: Major factual errors

## 2. Completeness (1-5)
- Are all required baseline fields populated?
- Are datatype-specific fields thoroughly extracted?
- Is the additional_knowledge section explored?
- Are there obvious gaps in coverage?

Score:
- 5: Comprehensive, all key info captured
- 4: Mostly complete, minor gaps
- 3: Acceptable coverage, some gaps
- 2: Several important omissions
- 1: Major gaps in coverage

## 3. Faithfulness to Source (1-5)
- Does extraction stay true to source material?
- Are there unwarranted interpretations?
- Is provenance clearly tracked?
- Are confidence levels appropriate?

Score:
- 5: Perfect fidelity to source
- 4: High fidelity, minor liberties
- 3: Acceptable fidelity, some extrapolation
- 2: Notable deviations from source
- 1: Poor fidelity, significant extrapolation

## 4. Signal-to-Noise Ratio (1-5)
- Is information high-value and actionable?
- Is there unnecessary verbosity?
- Are key insights clearly highlighted?
- Is the extraction concise yet complete?

Score:
- 5: Perfect signal, no noise
- 4: High signal, minimal noise
- 3: Acceptable ratio, some fluff
- 2: Noisy with diluted insights
- 1: Low signal, mostly noise

## 5. Reusability for AI (1-5)
- Is extraction well-structured for AI consumption?
- Are fields properly typed and formatted?
- Is metadata sufficient for retrieval?
- Can an AI easily parse and use this?

Score:
- 5: Perfectly structured for AI
- 4: Well-structured, minor improvements possible
- 3: Acceptable structure, some issues
- 2: Poor structure, needs work
- 1: Unusable for AI without major rework

## Overall Assessment
- Calculate average score across 5 dimensions
- Minimum passing: 3.0/5.0
- Recommend iteration if below threshold
"""


def get_review_template() -> str:
    """Get the expert review template instructions."""
    return REVIEW_TEMPLATE_INSTRUCTIONS
