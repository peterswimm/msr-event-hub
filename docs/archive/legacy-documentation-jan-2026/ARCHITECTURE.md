# Knowledge Agent POC - Architecture Overview

## Executive Summary

The Knowledge Agent POC has evolved through three major phases:

- **Phase 1 (Foundation)**: Core domain models, repositories, evaluation framework
- **Phase 2 (Enhancement)**: Compilation, workflows, advanced evaluation
- **Phase B (Architecture)**: Graph-aligned models, event-scoped design, knowledge workflow split
- **Phase C (Integration)**: Complete API server, programmatic access, integration tests

**Current State**: Production-ready application architecture with REST API and programmatic access patterns.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    REST API (FastAPI)                        │
│  GET/POST /v1/events, /v1/events/{id}/projects, etc.        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│            ApplicationContext (Dependency Container)         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │EventRepository│  │ProjectRepository│  │ArtifactRepository│ │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │SessionRepository│  │PublishedKnowledge│  │...         │   │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│              Domain Models (Graph-Aligned)                   │
│  Event ─┬─ Session                                          │
│         └─ Project ─┬─ KnowledgeArtifact (draft)            │
│                     └─ PublishedKnowledge (approved)        │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│           JSON File Persistence (./data)                     │
│  events/ | sessions/ | projects/ | artifacts/ | published/  │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Hierarchy (Event-Scoped, Phase B)

```
Event (evt_001)
├── Session (sess_001)
├── Session (sess_002)
├── Project (proj_001) ← Scoped to event
│   ├── KnowledgeArtifact (artifact_001) [DRAFT]
│   ├── KnowledgeArtifact (artifact_002) [APPROVED]
│   └── PublishedKnowledge (pub_001) ← From approved artifact
└── Project (proj_002)
    └── KnowledgeArtifact (artifact_003) [DRAFT]
```

**Key Pattern**: Everything is now scoped to events. Projects belong to events, not standalone.

---

## API Endpoints

### Events
- `GET /v1/events` - List all events
- `POST /v1/events` - Create event
- `GET /v1/events/{eventId}` - Get event
- `PUT /v1/events/{eventId}` - Update event
- `DELETE /v1/events/{eventId}` - Delete event

### Sessions (Event-Scoped)
- `GET /v1/events/{eventId}/sessions` - List sessions in event
- `POST /v1/events/{eventId}/sessions` - Create session
- `GET /v1/events/{eventId}/sessions/{sessionId}` - Get session

### Projects (Event-Scoped)
- `GET /v1/events/{eventId}/projects` - List projects in event
- `POST /v1/events/{eventId}/projects` - Create project
- `GET /v1/events/{eventId}/projects/{projectId}` - Get project
- `PUT /v1/events/{eventId}/projects/{projectId}` - Update project
- `DELETE /v1/events/{eventId}/projects/{projectId}` - Delete project

### Knowledge (Project-Scoped)
- `GET /v1/events/{eventId}/projects/{projectId}/knowledge` - List artifacts
- `POST /v1/events/{eventId}/projects/{projectId}/knowledge` - Create artifact
- `GET /v1/events/{eventId}/projects/{projectId}/knowledge/{artifactId}` - Get artifact
- `PUT /v1/events/{eventId}/projects/{projectId}/knowledge/{artifactId}/approve` - Approve artifact
- `POST /v1/events/{eventId}/projects/{projectId}/knowledge/{artifactId}/publish` - Publish approved artifact

### System
- `GET /` - Service info
- `GET /health` - Health check
- `GET /docs` - API documentation (Swagger UI)

---

## Response Format (Graph-Aligned)

All responses follow Microsoft Graph conventions:

```json
{
  "@odata.type": "#microsoft.graph.event",
  "@odata.etag": "abc123",
  "id": "evt_001",
  "displayName": "Research Summit",
  "eventType": "researchConference",
  "status": "planning",
  "startDate": "2026-01-15T00:00:00",
  "endDate": "2026-01-17T00:00:00",
  "createdAt": "2025-12-15T10:30:00",
  "updatedAt": "2025-12-15T10:30:00"
}
```

Collections:
```json
{
  "value": [
    { "@odata.type": "#microsoft.graph.event", ... },
    { "@odata.type": "#microsoft.graph.event", ... }
  ],
  "@odata.context": "https://eventhub.internal.microsoft.com/v1/$metadata#events",
  "@odata.nextLink": "https://eventhub.internal.microsoft.com/v1/events?$skip=20"
}
```

Error:
```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Event with id 'evt_001' not found"
  }
}
```

---

## Running the Application

### Option 1: API Server
```bash
# Development (auto-reload)
python3 run_server.py --reload

# Production
python3 run_server.py --port 8000

# Custom configuration
python3 run_server.py --port 9000 --data ./custom_data --log-level debug

# API Documentation
# Open: http://localhost:8000/docs
```

### Option 2: Programmatic Usage
```python
from main import ApplicationContext
from pathlib import Path

# Initialize
ctx = ApplicationContext(storage_root=Path("./data"))

# Create event
event = Event(id="evt_001", display_name="Summit", ...)
ctx.event_repo.create(event)

# Create project (event-scoped)
project = ProjectDefinition(
    id="proj_001",
    event_id="evt_001",  # Phase B: Required
    name="Knowledge Extraction",
    ...
)
ctx.project_repo.create(project)

# List by event
projects = ctx.project_repo.list_by_event("evt_001")
```

### Option 3: Embedded FastAPI
```python
from main import create_app
import uvicorn

app = create_app(storage_root=Path("./my_data"))
uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Knowledge Workflow

### Draft → Approved → Published

```
1. EXTRACTION
   Agent extracts knowledge from source material
   ↓
2. ARTIFACT (KnowledgeArtifact)
   Status: DRAFT
   Properties: title, claims, provenance, methods, impact, limitations
   
3. HUMAN REVIEW
   Expert reviewer evaluates artifact
   ↓
4. APPROVAL
   Artifact marked as APPROVED (approval_status = approved)
   
5. PUBLICATION
   Create PublishedKnowledge record from approved artifact
   Status: APPROVED (already)
   Target audience: Event attendees (safe, vetted content)
   
6. DISTRIBUTION
   PublishedKnowledge served in event materials, APIs, etc.
```

**Storage**:
- Draft artifacts: `/data/artifacts/`
- Published knowledge: `/data/published/`
- Relationship: `PublishedKnowledge.artifact_id` → `KnowledgeArtifact.id`

---

## Testing Strategy

### Test Tiers

**Tier 1: Unit Tests** (Existing)
- Individual model methods
- Repository CRUD operations
- Validation functions

**Tier 2: Integration Tests** (Phase C)
- ApplicationContext wiring
- Event → Project → Knowledge workflows
- Multi-repository interactions
- Persistence to disk

**Tier 3: API Tests** (Future)
- HTTP endpoint behavior
- Request/response serialization
- Error handling
- Authentication/authorization

**Running Tests**:
```bash
# Phase B core models
pytest tests/test_phase_b.py -v

# Phase C integration
pytest tests/test_integration_phase_c.py -v

# All tests
pytest tests/ -v --ignore=tests/test_integration_e2e.py --ignore=tests/test_modern_agents.py
```

---

## File Organization

```
knowledge-agent-poc/
├── core/
│   ├── graph_models.py          # GraphEntity base, OData types
│   ├── event_models.py          # Event, Session (Phase B)
│   ├── knowledge_models.py       # Artifacts, PublishedKnowledge (Phase B)
│   ├── event_repository.py       # EventRepository, SessionRepository (Phase B)
│   └── knowledge_repository.py   # Artifact repos (Phase B)
│
├── projects/
│   ├── models.py               # ProjectDefinition (Phase B: event-scoped)
│   └── repository.py           # ProjectRepository + list_by_event()
│
├── api/
│   ├── __init__.py             # Route exports
│   ├── events_routes.py        # Event/Session handlers (Phase B)
│   ├── knowledge_routes.py     # Knowledge handlers (Phase B)
│   └── projects_routes.py      # Project handlers (event-scoped, Phase B)
│
├── tests/
│   ├── test_phase_b.py         # Phase B core tests (11)
│   └── test_integration_phase_c.py  # Integration tests (12)
│
├── main.py                      # ApplicationContext + FastAPI factory (Phase C)
├── run_server.py               # Server startup script (Phase C)
├── example_usage.py            # Programmatic example (Phase C)
│
└── PHASE_*.md                  # Documentation for each phase
```

---

## Key Concepts

### Graph Alignment
- Responses follow Microsoft Graph conventions
- Every entity has `@odata.type` and `@odata.etag`
- Relationships expressed through IDs and references
- Familiar to Teams/Microsoft 365 developers

### Event-Scoping (Phase B)
- Events are top-level organizational unit
- Projects belong to events (not standalone)
- Sessions belong to events
- All queries can filter by event_id
- Enables multi-tenant-like event management

### Knowledge Workflow Split (Phase B)
- **Draft**: Raw extraction (KnowledgeArtifact)
- **Approved**: Reviewed extraction (approval_status = approved)
- **Published**: Vetted, ready for audience (PublishedKnowledge)
- Allows separation of internal → external knowledge

### Dependency Injection (Phase C)
- ApplicationContext holds all repositories
- Routes depend on repositories through DI
- Enables testing without FastAPI
- Allows embedding in other applications
- Clean separation of concerns

---

## Performance & Scalability Notes

### Current (Phase C)
- **Storage**: JSON files on disk
- **Queries**: Full table scan (no indexing)
- **Concurrency**: Single process only
- **Scale**: Good for 1-100 events, okay for 100-1000 events

### Recommended for Scale
1. **Database**: PostgreSQL or MongoDB
2. **Indexing**: On event_id, project_id, status fields
3. **Caching**: Redis for frequent queries
4. **Async**: Make all repo operations async
5. **Pagination**: Implement skip/take for large result sets

---

## Security Considerations

### Current (Phase C)
- No authentication
- No authorization
- No rate limiting
- All data in plaintext JSON

### Recommended for Production
1. **Authentication**: JWT tokens or OAuth2
2. **Authorization**: Role-based access control (RBAC)
3. **Encryption**: TLS for transit, encryption at rest
4. **Audit**: Log all mutations with user context
5. **Validation**: Request body validation schemas
6. **Rate Limiting**: Per-user request quotas

---

## Development Roadmap

### Phase D: Workflow Integration (Next)
- [ ] Connect ProjectExecutor to ApplicationContext
- [ ] Update IterationController for events
- [ ] Wire evaluation pipeline
- [ ] Batch operation endpoints

### Phase E: Production Hardening
- [ ] Database backend
- [ ] Authentication/authorization
- [ ] Performance optimization
- [ ] Comprehensive error handling

### Phase F: Advanced Features
- [ ] Search/filtering
- [ ] Webhooks/notifications
- [ ] Background job processing
- [ ] Multi-user collaboration

---

## Quick Reference

### Creating an Event and Project
```python
from main import ApplicationContext
from core.event_models import Event, EventType, EventStatus
from projects.models import ProjectDefinition

ctx = ApplicationContext()

# Event
event = Event(
    id="evt_2026",
    display_name="2026 Summit",
    event_type=EventType.CONFERENCE,
    status=EventStatus.PLANNING,
    odata_type="#microsoft.graph.event",
)
ctx.event_repo.create(event)

# Project (scoped to event)
project = ProjectDefinition(
    id="proj_001",
    event_id="evt_2026",  # Phase B!
    name="Knowledge Extraction",
    research_area="AI/ML",
    odata_type="#microsoft.graph.project",
)
ctx.project_repo.create(project)
```

### Starting the Server
```bash
python3 run_server.py --reload
# Visit http://localhost:8000/docs
```

### Testing
```bash
pytest tests/test_phase_b.py tests/test_integration_phase_c.py -v
```

---

**Document Version**: 1.0  
**Last Updated**: January 5, 2026  
**Status**: Complete through Phase C
