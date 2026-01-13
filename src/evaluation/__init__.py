"""Evaluation framework for knowledge extraction agents."""

from typing import TYPE_CHECKING

# Azure AI Evaluation is optional for unit tests; fall back gracefully when
# the dependency is absent so pure-Python modules (advanced scoring, etc.)
# can be imported without errors.
try:  # pragma: no cover - exercised implicitly via imports
    from .evaluators import (  # type: ignore
        ExtractionQualityEvaluator,
        StructureCompletenessEvaluator,
        SourceFidelityEvaluator,
    )
except ModuleNotFoundError:  # pragma: no cover - dependency guard
    if TYPE_CHECKING:  # keep type checkers happy without runtime import
        from .evaluators import (  # type: ignore
            ExtractionQualityEvaluator,
            StructureCompletenessEvaluator,
            SourceFidelityEvaluator,
        )

try:  # pragma: no cover - dependency guard
    from .runner import EvaluationRunner  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    if TYPE_CHECKING:
        from .runner import EvaluationRunner  # type: ignore
    EvaluationRunner = None  # type: ignore

from .datasets import create_test_dataset, load_test_dataset

__all__ = [
    "ExtractionQualityEvaluator",
    "StructureCompletenessEvaluator",
    "SourceFidelityEvaluator",
    "EvaluationRunner",
    "create_test_dataset",
    "load_test_dataset",
]
