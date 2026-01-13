"""Tests for advanced evaluation components (scoring, suggestions, hybrid)."""

from src.evaluation.advanced_scoring import AdvancedScorer
from src.evaluation.suggestions import SuggestionEngine
from src.evaluation.hybrid_evaluator import HybridEvaluator
from src.evaluation.expert_review import ExpertReview, DimensionScore, ReviewDimension


def _sample_metrics():
    structure = {
        "structure_completeness_score": 90,
        "missing_fields": [],
        "incomplete_fields": [],
    }
    extraction = {
        "summary_word_count": 200,
        "summary_quality": "good",
        "field_coverage_percent": 75,
        "key_points_count": 4,
        "avg_key_point_words": 12,
    }
    fidelity = {"fidelity_score": 4.5, "accuracy_issues": []}
    return structure, extraction, fidelity


def test_advanced_scorer_passes_with_good_metrics():
    structure, extraction, fidelity = _sample_metrics()
    scorer = AdvancedScorer()
    scorecard = scorer.compute_scores(
        structure_metrics=structure,
        extraction_metrics=extraction,
        fidelity_metrics=fidelity,
    )
    assert scorecard.passed
    assert scorecard.overall_score >= 3.0
    assert scorecard.structure_score >= 3.0
    assert scorecard.fidelity_score >= 3.0


def test_advanced_scorer_fails_on_low_fidelity():
    structure, extraction, fidelity = _sample_metrics()
    fidelity["fidelity_score"] = 2.5
    scorer = AdvancedScorer()
    scorecard = scorer.compute_scores(
        structure_metrics=structure,
        extraction_metrics=extraction,
        fidelity_metrics=fidelity,
    )
    assert not scorecard.passed


def test_suggestion_engine_flags_missing_and_short_summary():
    structure = {
        "structure_completeness_score": 40,
        "missing_fields": ["title", "authors"],
        "incomplete_fields": ["summary"],
    }
    extraction = {
        "summary_word_count": 50,
        "summary_quality": "needs_improvement",
        "field_coverage_percent": 30,
        "key_points_count": 1,
    }
    fidelity = {"fidelity_score": 3.0}

    suggester = SuggestionEngine(min_key_points=3, min_summary_words=120)
    suggestions = suggester.suggest_improvements(
        structure_metrics=structure,
        extraction_metrics=extraction,
        fidelity_metrics=fidelity,
    )

    assert any("Populate missing fields" in s for s in suggestions)
    assert any("Add more key points" in s for s in suggestions)
    assert any("Expand summary" in s for s in suggestions)


def test_suggestions_include_expert_feedback():
    structure, extraction, fidelity = _sample_metrics()
    expert = ExpertReview(
        artifact_title="Test",
        artifact_type="paper",
        reviewer="automated",
        dimension_scores=[
            DimensionScore(
                dimension=ReviewDimension.FACTUAL_ACCURACY,
                score=3.5,
                rationale="Missing citations"
            ),
            DimensionScore(
                dimension=ReviewDimension.COMPLETENESS,
                score=4.5,
                rationale="Good coverage"
            ),
        ],
        overall_score=4.0,
        requires_iteration=True,
    )
    suggester = SuggestionEngine()
    suggestions = suggester.suggest_improvements(
        structure_metrics=structure,
        extraction_metrics=extraction,
        fidelity_metrics=fidelity,
        expert_review=expert,
    )
    assert any("factual accuracy" in s for s in suggestions)
    assert any("iteration" in s.lower() for s in suggestions)


def test_hybrid_evaluator_combines_score_and_suggestions():
    structure, extraction, fidelity = _sample_metrics()
    hybrid = HybridEvaluator()
    result = hybrid.evaluate(
        structure_metrics=structure,
        extraction_metrics=extraction,
        fidelity_metrics=fidelity,
    )
    assert "scorecard" in result
    assert result["passed"] is True
    assert isinstance(result["suggestions"], list)
