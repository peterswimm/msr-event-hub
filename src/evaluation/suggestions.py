"""Improvement suggestion engine for evaluation outputs.

Generates actionable, deterministic suggestions based on evaluator metrics
and (optionally) expert review. No remote calls; safe for unit testing.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from src.evaluation.expert_review import ExpertReview, DimensionScore, ReviewDimension


class SuggestionEngine:
    """Produces improvement suggestions from evaluation signals."""

    def __init__(self, *, min_key_points: int = 3, min_summary_words: int = 100):
        self.min_key_points = min_key_points
        self.min_summary_words = min_summary_words

    def suggest_improvements(
        self,
        *,
        structure_metrics: Dict,
        extraction_metrics: Dict,
        fidelity_metrics: Dict,
        expert_review: Optional[ExpertReview] = None,
    ) -> List[str]:
        suggestions: List[str] = []

        # Structure suggestions
        missing = structure_metrics.get("missing_fields", [])
        incomplete = structure_metrics.get("incomplete_fields", [])
        if missing:
            suggestions.append(f"Populate missing fields: {', '.join(missing)}")
        if incomplete:
            suggestions.append(f"Complete partial fields: {', '.join(incomplete)}")

        # Key points and summary length
        kp_count = extraction_metrics.get("key_points_count", 0)
        if kp_count < self.min_key_points:
            suggestions.append(
                f"Add more key points (have {kp_count}, need {self.min_key_points}+)."
            )
        summary_words = extraction_metrics.get("summary_word_count", 0)
        if summary_words < self.min_summary_words:
            suggestions.append(
                f"Expand summary to at least {self.min_summary_words} words (current {summary_words})."
            )

        # Fidelity issues
        fidelity_score = fidelity_metrics.get("fidelity_score", 3)
        if fidelity_score < 4:
            suggestions.append(
                "Tighten grounding to the source text and cite specific evidence to boost fidelity."
            )

        # Expert review signals
        if expert_review:
            low_dims = [
                ds for ds in expert_review.dimension_scores
                if ds.score < 4.0
            ]
            for ds in low_dims:
                suggestions.append(
                    f"Improve {ds.dimension.value.replace('_', ' ')}: {ds.rationale}"
                )
            if expert_review.requires_iteration:
                suggestions.append("Apply iteration based on reviewer notes before compile phase.")

        # De-duplicate suggestions while preserving order
        deduped: List[str] = []
        seen = set()
        for s in suggestions:
            if s not in seen:
                deduped.append(s)
                seen.add(s)
        return deduped
