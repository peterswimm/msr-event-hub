"""Advanced scoring utilities for evaluation phase.

Provides deterministic, testable scoring that combines structure, quality,
fidelity, and optional expert review into a single scorecard. Designed to
work without remote calls so it is reliable in unit tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from src.evaluation.expert_review import ExpertReview


@dataclass
class ScoreBreakdown:
    """Detailed scores for each dimension used to compute the overall score."""

    structure_score: float
    extraction_score: float
    fidelity_score: float
    expert_score: Optional[float]
    coverage_score: float
    overall_score: float
    passed: bool


class AdvancedScorer:
    """Combines evaluator outputs into a single decision-ready scorecard."""

    def __init__(
        self,
        *,
        min_overall_score: float = 3.0,
        min_fidelity_score: float = 3.0,
        min_structure_score: float = 3.0,
    ) -> None:
        self.min_overall_score = min_overall_score
        self.min_fidelity_score = min_fidelity_score
        self.min_structure_score = min_structure_score

    def compute_scores(
        self,
        *,
        structure_metrics: Dict,
        extraction_metrics: Dict,
        fidelity_metrics: Dict,
        expert_review: Optional[ExpertReview] = None,
    ) -> ScoreBreakdown:
        """Compute normalized scores (1-5 scale) and pass/fail.

        Inputs are outputs from the existing evaluators:
        - structure_metrics: result from StructureCompletenessEvaluator
        - extraction_metrics: result from ExtractionQualityEvaluator
        - fidelity_metrics: result from SourceFidelityEvaluator
        - expert_review: optional ExpertReview object
        """

        structure_score = self._score_structure(structure_metrics)
        extraction_score = self._score_extraction(extraction_metrics)
        fidelity_score = self._score_fidelity(fidelity_metrics)
        coverage_score = self._score_coverage(extraction_metrics)
        expert_score = expert_review.overall_score if expert_review else None

        scores = [structure_score, extraction_score, fidelity_score, coverage_score]
        if expert_score is not None:
            scores.append(expert_score)

        overall_score = sum(scores) / len(scores) if scores else 0.0

        passed = (
            overall_score >= self.min_overall_score
            and fidelity_score >= self.min_fidelity_score
            and structure_score >= self.min_structure_score
        )

        return ScoreBreakdown(
            structure_score=round(structure_score, 2),
            extraction_score=round(extraction_score, 2),
            fidelity_score=round(fidelity_score, 2),
            expert_score=round(expert_score, 2) if expert_score is not None else None,
            coverage_score=round(coverage_score, 2),
            overall_score=round(overall_score, 2),
            passed=passed,
        )

    def _score_structure(self, metrics: Dict) -> float:
        raw = metrics.get("structure_completeness_score", 0)
        return max(1.0, min(5.0, (raw / 100.0) * 5.0))

    def _score_extraction(self, metrics: Dict) -> float:
        word_count = metrics.get("summary_word_count", 0)
        key_points = metrics.get("key_points_count", 0)
        summary_quality = metrics.get("summary_quality", "needs_improvement")

        score = 3.0
        if summary_quality == "good":
            score += 0.5
        if 3 <= key_points <= 12:
            score += 0.25
        if word_count < 50:
            score -= 0.5
        if word_count > 800:
            score -= 0.5
        return max(1.0, min(5.0, score))

    def _score_fidelity(self, metrics: Dict) -> float:
        return float(metrics.get("fidelity_score", 3.0))

    def _score_coverage(self, metrics: Dict) -> float:
        coverage = metrics.get("field_coverage_percent", 0.0)
        if coverage >= 80:
            return 4.5
        if coverage >= 60:
            return 4.0
        if coverage >= 40:
            return 3.0
        if coverage >= 20:
            return 2.5
        return 1.5
