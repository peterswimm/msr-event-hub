"""API package with optional FastAPI routers.

Lazily exposes router factories to avoid importing heavy dependencies at
package import time (e.g., azure-ai-evaluation). This keeps startup fast and
prevents unnecessary imports unless a specific router is accessed.
"""

from importlib import import_module
from typing import Any

__all__ = [
    "get_events_router",
    "get_sessions_router",
    "get_projects_router",
    "get_knowledge_router",
    "get_artifacts_router",
    "get_evaluation_router",
    "get_dashboard_router",
    "get_workflow_router",
]

_ROUTER_MODULES = {
    "get_events_router": "src.api.events_routes",
    "get_sessions_router": "src.api.events_routes",
    "get_projects_router": "src.api.projects_routes",
    "get_knowledge_router": "src.api.knowledge_routes",
    "get_artifacts_router": "src.api.artifacts_routes",
    "get_evaluation_router": "src.api.evaluation_routes",
    "get_dashboard_router": "src.api.dashboard_routes",
    "get_workflow_router": "src.api.workflow_routes",
}


def __getattr__(name: str) -> Any:
    """Lazy-import router factories on first access.

    This avoids importing modules with heavy transitive dependencies until the
    attribute is actually requested.
    """
    module_name = _ROUTER_MODULES.get(name)
    if not module_name:
        raise AttributeError(f"module 'src.api' has no attribute '{name}'")
    mod = import_module(module_name)
    return getattr(mod, name)
