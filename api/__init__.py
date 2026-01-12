"""API package with optional FastAPI routers.

Routers are returned as None when FastAPI isn't installed so imports remain
safe in environments without the dependency.

Phase B: Added event-scoped and Graph-aligned routes.
"""

from api.events_routes import get_events_router, get_sessions_router
from api.projects_routes import get_projects_router
from api.knowledge_routes import get_knowledge_router
from api.artifacts_routes import get_artifacts_router
from api.evaluation_routes import get_evaluation_router
from api.dashboard_routes import get_dashboard_router
from api.workflow_routes import get_workflow_router

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
