"""Main application: Event-scoped Knowledge Agent with Graph-aligned architecture (Phase B+).

This module initializes and wires together all repositories, handlers, and routes
for a complete knowledge management system organized around events.

Architecture:
- Event → Sessions, Projects
- Project → Knowledge Artifacts (draft PKA), Published Knowledge (approved)
- Knowledge Artifacts → stored in KnowledgeArtifactRepository
- Published Knowledge → stored in PublishedKnowledgeRepository

All responses follow Microsoft Graph conventions with @odata.type, @odata.etag, etc.
"""

import logging
import os
import time
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, skip

try:
    from fastapi import FastAPI, Depends
    from fastapi.responses import JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from src.core.event_repository import EventRepository, SessionRepository
from src.core.knowledge_repository import KnowledgeArtifactRepository, PublishedKnowledgeRepository
from src.core.projects.repository import ProjectRepository
from src.api.events_routes import get_events_router, get_sessions_router
from src.api.projects_routes import get_projects_router
from src.api.knowledge_routes import get_knowledge_router
from src.api.workflow_routes import get_workflow_router
from src.api.chat_routes import get_chat_router
from src.workflows.project_executor import ProjectExecutor
from src.workflows.iteration_controller import IterationController
from src.evaluation.hybrid_evaluator import HybridEvaluator
from src.api.action_init import initialize_action_handlers
from src.observability.telemetry import (
    initialize_telemetry,
    track_api_request,
    flush_telemetry
)

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class ApplicationContext:
    """Container for all repositories and shared state."""

    def __init__(self, storage_root: Optional[Path] = None):
        """Initialize application context with repositories.
        
        Args:
            storage_root: Root directory for all JSON storage. Defaults to ./data
        """
        self.storage_root = Path(storage_root or "./data")
        self.storage_root.mkdir(exist_ok=True)
        
        # Initialize repositories
        self.event_repo = EventRepository(storage_dir=self.storage_root / "events")
        self.session_repo = SessionRepository(storage_dir=self.storage_root / "sessions")
        self.project_repo = ProjectRepository(storage_dir=self.storage_root / "projects")
        self.artifact_repo = KnowledgeArtifactRepository(storage_dir=self.storage_root / "artifacts")
        self.published_repo = PublishedKnowledgeRepository(storage_dir=self.storage_root / "published")
        
        # Initialize workflow components
        self.evaluator = HybridEvaluator()
        self.executor = ProjectExecutor(
            repository=self.project_repo,
            evaluator=self.evaluator,
            max_iterations=2
        )
        self.iteration_controller = IterationController(
            executor=self.executor,
            max_iterations=2
        )
        
        logger.info(f"✓ Application context initialized with storage root: {self.storage_root}")
        logger.info(f"✓ Workflow components (ProjectExecutor, IterationController) initialized")

    def get_health_status(self) -> dict:
        """Get health status of all repositories."""
        return {
            "status": "healthy",
            "storage_root": str(self.storage_root),
            "repositories": {
                "events": "ready",
                "sessions": "ready",
                "projects": "ready",
                "artifacts": "ready",
                "published_knowledge": "ready",
            }
        }


def create_app(storage_root: Optional[Path] = None) -> Optional[FastAPI]:
    """Create and configure the FastAPI application.
    
    Args:
        storage_root: Root directory for data storage. Defaults to ./data
        
    Returns:
        Configured FastAPI app or None if FastAPI not available
    """
    if not HAS_FASTAPI:
        logger.warning("FastAPI not available; cannot create web application")
        return None

    logger.info("="*60)
    logger.info("Creating FastAPI application...")
    
    # Initialize telemetry
    initialize_telemetry(os.getenv("APPINSIGHTS_INSTRUMENTATION_KEY"))

    app = FastAPI(
        title="MSR Event Hub API",
        description="Event-scoped knowledge management with hybrid query routing and multi-agent orchestration",
        version="0.3.0",
        docs_url="/docs",
        openapi_url="/openapi.json"
    )
    
    # Telemetry middleware
    @app.middleware("http")
    async def telemetry_middleware(request, call_next):
        """Track API request metrics."""
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        track_api_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        return response
    
    # Initialize application context
    ctx = ApplicationContext(storage_root=storage_root)
    
    # Dependency: get application context
    def get_context() -> ApplicationContext:
        return ctx
    
    # ===== Static Files & Frontend =====
    
    # Check if frontend build exists
    frontend_path = Path(__file__).parent / "web" / "chat" / "dist"
    if frontend_path.exists():
        logger.info(f"✓ Serving frontend from: {frontend_path}")
        
        # Serve static assets
        app.mount("/assets", StaticFiles(directory=str(frontend_path / "assets")), name="assets")
        
        # Serve index.html for root and SPA routes
        @app.get("/")
        async def serve_root():
            """Serve the chat frontend."""
            index_file = frontend_path / "index.html"
            if index_file.exists():
                return FileResponse(index_file)
            return JSONResponse(
                status_code=404,
                content={"error": "Frontend not built. Run: cd web/chat && npm run build"}
            )
        
        @app.get("/favicon.ico")
        async def serve_favicon():
            """Serve favicon."""
            favicon_file = frontend_path / "favicon.ico"
            if favicon_file.exists():
                return FileResponse(favicon_file)
            return JSONResponse(status_code=404, content={"error": "Not found"})
    else:
        logger.warning(f"Frontend not found at: {frontend_path}")
        logger.warning("To enable chat UI, run: cd web/chat && npm install && npm run build")
        
        @app.get("/")
        async def serve_root_fallback():
            """Fallback root endpoint when frontend not built."""
            return {
                "message": "MSR Event Hub API",
                "version": "0.3.0",
                "docs": "/docs",
                "frontend_status": "not_built",
                "frontend_instructions": "cd web/chat && npm install && npm run build"
            }
    
    # ===== Health Check =====
    @app.get("/health")
    async def health_check(context: ApplicationContext = Depends(get_context)):
        """Health check endpoint."""
        return context.get_health_status()
    
    # ===== Root Endpoint =====
    @app.get("/")
    async def root():
        """API root endpoint with basic info."""
        return {
            "service": "Knowledge Agent API",
            "version": "0.3.0",
            "phase": "C (Data Layer & Frontend Separation)",
            "endpoints": {
                "health": "/health",
                "docs": "/docs",
                "v1_events": "/v1/events",
                "v1_projects": "/v1/events/{eventId}/projects",
                "v1_knowledge": "/v1/events/{eventId}/projects/{projectId}/knowledge",
                "data_events": "/data/events",
                "data_projects": "/data/projects",
                "data_sessions": "/data/sessions",
                "data_artifacts": "/data/artifacts"
            },
            "phases": {
                "phase_1": "Bridge TypeScript fixes (complete)",
                "phase_2": "Webchat atomic component (complete)",
                "phase_3": "Data layer pure CRUD endpoints (in progress)",
                "phase_4": "Frontend deployment & CORS (planned)"
            }
        }
    
    # ===== Register Routers =====
    
    # Import data routers for Phase 3 pure CRUD endpoints
    try:
        from src.api.data import (
            get_data_events_router,
            get_data_projects_router,
            get_data_sessions_router,
            get_data_artifacts_router
        )
    except ImportError:
        logger.warning("Data routers not available - Phase 3 not fully initialized")
        get_data_events_router = None
        get_data_projects_router = None
        get_data_sessions_router = None
        get_data_artifacts_router = None
    
    # Data layer routers (/data/* endpoints - Phase 3)
    if get_data_events_router:
        data_events_router = get_data_events_router(repo=ctx.event_repo)
        if data_events_router:
            app.include_router(data_events_router)
            logger.info("✓ Data events router registered at /data/events")
    
    if get_data_projects_router:
        data_projects_router = get_data_projects_router(repo=ctx.project_repo)
        if data_projects_router:
            app.include_router(data_projects_router)
            logger.info("✓ Data projects router registered at /data/projects")
    
    if get_data_sessions_router:
        data_sessions_router = get_data_sessions_router(repo=ctx.session_repo)
        if data_sessions_router:
            app.include_router(data_sessions_router)
            logger.info("✓ Data sessions router registered at /data/sessions")
    
    if get_data_artifacts_router:
        data_artifacts_router = get_data_artifacts_router(repo=ctx.artifact_repo)
        if data_artifacts_router:
            app.include_router(data_artifacts_router)
            logger.info("✓ Data artifacts router registered at /data/artifacts")
    
    # Event & Session routes
    events_router = get_events_router(repo=ctx.event_repo)
    if events_router:
        app.include_router(events_router)
        logger.info("✓ Events router registered")
    
    sessions_router = get_sessions_router()
    if sessions_router:
        app.include_router(sessions_router)
        logger.info("✓ Sessions router registered")
    
    # Project routes (event-scoped)
    projects_router = get_projects_router(repo=ctx.project_repo)
    if projects_router:
        app.include_router(projects_router)
        logger.info("✓ Projects router registered")
    
    # Knowledge routes (artifact & published)
    knowledge_router = get_knowledge_router()
    if knowledge_router:
        app.include_router(knowledge_router)
        logger.info("✓ Knowledge router registered")
    
    # Workflow routes (evaluation & iteration)
    workflow_router = get_workflow_router()
    if workflow_router:
        app.include_router(workflow_router)
        logger.info("✓ Workflow router registered")

    chat_router = get_chat_router()
    if chat_router:
        app.include_router(chat_router)
        logger.info("✓ Chat router registered")
    
    # ===== Error Handlers =====
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        """Global exception handler with Graph error format."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": f"An error occurred: {str(exc)}"
                }
            }
        )
    
    logger.info("✓ FastAPI application created successfully")
    return app


def main():
    """Entry point for running the application."""
    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI is required to run the API server. "
            "Install with: pip install fastapi uvicorn"
        )
    
    import uvicorn
    import os
    
    app = create_app()
    if app is None:
        raise RuntimeError("Failed to create FastAPI application")
    
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting MSR Event Hub API server on {host}:{port}")
    logger.info(f"API Documentation: http://localhost:{port}/docs")
    logger.info(f"Chat Interface: http://localhost:{port}/")
    logger.info("="*60)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
