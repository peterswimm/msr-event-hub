"""Project-level compilation utilities.

Produces a deterministic, local-only compiled summary from extracted artifacts.
"""

from __future__ import annotations

from typing import Dict, List, Any

from core.schemas.base_schema import BaseKnowledgeArtifact


def _ensure_list(value: Any) -> List:
    """Normalize incoming values to a list for aggregation."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def compile_project_summary(project_name: str, artifacts: List[BaseKnowledgeArtifact]) -> Dict:
    """Compile a lightweight project summary from artifacts.

    No model calls; purely aggregates existing data for tests and offline use.
    """
    return {
        "project_name": project_name,
        "artifact_count": len(artifacts),
        "sources": [a.source_type for a in artifacts],
        "titles": [a.title for a in artifacts],
        "key_claims": [claim for a in artifacts for claim in _ensure_list(a.primary_claims_capabilities)],
        "key_methods": [m for a in artifacts for m in _ensure_list(a.key_methods_approach)],
        "limitations": [l for a in artifacts for l in _ensure_list(a.limitations_constraints)],
    }
