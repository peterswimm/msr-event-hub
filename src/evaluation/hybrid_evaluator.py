"""Hybrid evaluator that unifies metrics, scoring, and suggestions.

Consumes outputs from existing evaluators plus optional ExpertReview to
produce a decision-ready result with pass/fail and suggested improvements.
"""

from __future__ import annotations

from typing import Dict, Optional

from src.evaluation.advanced_scoring import AdvancedScorer, ScoreBreakdown
from src.evaluation.expert_review import ExpertReview
from src.evaluation.suggestions import SuggestionEngine


class HybridEvaluator:
    """Compose scorer + suggestion engine for a unified evaluation output."""

    def __init__(
        self,
        scorer: Optional[AdvancedScorer] = None,
        suggester: Optional[SuggestionEngine] = None,
    ) -> None:
        self.scorer = scorer or AdvancedScorer()
        self.suggester = suggester or SuggestionEngine()

    def evaluate(
        self,
        *,
        structure_metrics: Dict,
        extraction_metrics: Dict,
        fidelity_metrics: Dict,
        expert_review: Optional[ExpertReview] = None,
    ) -> Dict:
        """Return combined scorecard and suggestions."""
        scorecard: ScoreBreakdown = self.scorer.compute_scores(
            structure_metrics=structure_metrics,
            extraction_metrics=extraction_metrics,
            fidelity_metrics=fidelity_metrics,
            expert_review=expert_review,
        )

        suggestions = self.suggester.suggest_improvements(
            structure_metrics=structure_metrics,
            extraction_metrics=extraction_metrics,
            fidelity_metrics=fidelity_metrics,
            expert_review=expert_review,
        )

        return {
            "scorecard": scorecard,
            "passed": scorecard.passed,
            "suggestions": suggestions,
        }
