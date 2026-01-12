#!/usr/bin/env bash
# Quick Reference Card - Knowledge Agent API (Phase C)
# Save as: QUICKSTART.sh or view as reference

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          Knowledge Agent POC - Quick Reference (Phase C)      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "📌 GETTING STARTED"
echo "─────────────────────────────────────────────────────────────────"
echo "1. Install dependencies:"
echo "   pip install fastapi uvicorn"
echo ""
echo "2. Run the server (development):"
echo "   python3 run_server.py --reload"
echo ""
echo "3. Open API documentation:"
echo "   http://localhost:8000/docs"
echo ""

echo "📌 PROGRAMMATIC USAGE"
echo "─────────────────────────────────────────────────────────────────"
cat << 'PYTHON'
from main import ApplicationContext
from core.event_models import Event, EventType, EventStatus
from projects.models import ProjectDefinition

# Initialize
ctx = ApplicationContext()

# Create event
event = Event(
    id="evt_001",
    display_name="Research Summit",
    event_type=EventType.CONFERENCE,
    status=EventStatus.PLANNING,
    odata_type="#microsoft.graph.event",
)
ctx.event_repo.create(event)

# Create project (event-scoped)
project = ProjectDefinition(
    id="proj_001",
    event_id="evt_001",
    name="Knowledge Extraction",
    research_area="AI/ML",
    odata_type="#microsoft.graph.project",
)
ctx.project_repo.create(project)

# List projects in event
projects = ctx.project_repo.list_by_event("evt_001")
PYTHON
echo ""

echo "📌 API ENDPOINTS"
echo "─────────────────────────────────────────────────────────────────"
echo "GET    /health                              Health check"
echo "GET    /v1/events                           List events"
echo "POST   /v1/events                           Create event"
echo "GET    /v1/events/{eventId}/sessions        List sessions"
echo "GET    /v1/events/{eventId}/projects        List projects"
echo "POST   /v1/events/{eventId}/projects        Create project"
echo "GET    /v1/events/{eventId}/projects/{id}/knowledge  List artifacts"
echo ""

echo "📌 RUNNING EXAMPLES"
echo "─────────────────────────────────────────────────────────────────"
echo "Run programmatic example:"
echo "  python3 example_usage.py"
echo ""
echo "Run with custom port:"
echo "  python3 run_server.py --port 9000"
echo ""
echo "Run with custom data directory:"
echo "  python3 run_server.py --data ./my_data"
echo ""
echo "Run with debug logging:"
echo "  python3 run_server.py --log-level debug"
echo ""

echo "📌 TESTING"
echo "─────────────────────────────────────────────────────────────────"
echo "Run Phase B tests:"
echo "  pytest tests/test_phase_b.py -v"
echo ""
echo "Run Phase C integration tests:"
echo "  pytest tests/test_integration_phase_c.py -v"
echo ""
echo "Run all tests:"
echo "  pytest tests/ -v --ignore=tests/test_integration_e2e.py --ignore=tests/test_modern_agents.py"
echo ""

echo "📌 FILE STORAGE"
echo "─────────────────────────────────────────────────────────────────"
echo "Data is stored in JSON files under ./data/"
echo ""
echo "Structure:"
echo "  ./data/events/          # Event entities"
echo "  ./data/sessions/        # Session entities"
echo "  ./data/projects/        # Projects (event-scoped)"
echo "  ./data/artifacts/       # Knowledge artifacts (draft)"
echo "  ./data/published/       # Published knowledge (approved)"
echo ""

echo "📌 KEY CONCEPTS"
echo "─────────────────────────────────────────────────────────────────"
echo "Event-Scoped (Phase B):"
echo "  Projects belong to events, not standalone"
echo "  Query: GET /v1/events/{eventId}/projects"
echo ""
echo "Knowledge Workflow:"
echo "  Extract → Draft (KnowledgeArtifact) → Approve → Publish"
echo ""
echo "Graph Alignment:"
echo "  All responses include @odata.type, @odata.etag"
echo "  Familiar to Teams/Microsoft 365 developers"
echo ""

echo "📌 ARCHITECTURE"
echo "─────────────────────────────────────────────────────────────────"
echo "Read the full architecture guide:"
echo "  ARCHITECTURE.md"
echo ""
echo "Read Phase C implementation details:"
echo "  PHASE_C_SUMMARY.md"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        For more info, see: README.md, ARCHITECTURE.md         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
