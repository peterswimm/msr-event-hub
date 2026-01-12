# MSR Event Hub

**A scalable platform for MSR internal events and lecture series**

**Status**: Production-Ready Platform (Phase E Complete + Modern Frontend)  
**Branch**: `main`
**Frontend**: React 18.2 + Vite 7.3 + Fluent UI v9 (Modern UI)

---

## 📋 Overview

The **MSR Event Hub** is a digital platform that augments MSR events with experiences that help **organizers** run programs smoothly, help **presenters** publish and refine research assets, and help **attendees** discover and follow up on research—before, during, and long after events conclude.

### Platform Capabilities
- **Event Management**: Multi-event homepage, event-specific sites with agendas, sessions, and posters
- **Poster/Project Hub**: Structured project pages with bookmarking, QR codes, and rich asset links
- **Knowledge Extraction**: AI-powered ingestion from papers, talks, and code repositories
- **Discovery & Chat**: Cross-event exploration with AI-assisted search and recommendations (Modern React UI)
- **Admin Tools**: Self-service content management for organizers and presenters
- **Modern Frontend**: React 18 + Vite + Fluent UI v9 with dark theme, fully env-configurable

### Core Audiences
- **Organizers**: Reduce friction for setup, planning, content validation, and reporting
- **Presenters**: Submit, refine, and publish high-quality digital assets
- **Attendees**: Better discovery and follow-up (search, bookmarks, personalized guides)

---

## 🏗️ Platform Structure

```
msr-event-hub/
├── web/chat/                # Modern React frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── components/      # React components (BrandHeader, HeroCards, MessageInput, etc.)
│   │   ├── clients/         # API clients (azureOpenAI, hubChat)
│   │   ├── types/           # TypeScript types (messages)
│   │   ├── App.tsx          # Main app component
│   │   ├── main.tsx         # Entry point with theme provider
│   │   └── styles.css       # Global styles (dark theme)
│   ├── .env.example         # Environment configuration template
│   └── package.json         # Frontend dependencies
│
├── api/                     # REST API endpoints
│   ├── v1_events.py         # Event management
│   ├── v1_projects.py       # Project/poster endpoints
│   ├── chat_routes.py       # Chat/streaming endpoints
│   └── v1_workflows.py      # Workflow orchestration
│
├── agents/                  # Knowledge extraction agents
│   ├── paper_agent.py       # Research paper analysis
│   ├── talk_agent.py        # Session/talk extraction
│   └── repository_agent.py  # Code repo analysis
│
├── infra/                   # Production infrastructure
│   ├── database/            # PostgreSQL models
│   ├── auth/                # JWT authentication
│   ├── config/              # Configuration management
│   └── monitoring/          # Logging and metrics
│
├── async_execution/         # Background job processing
│   ├── celery_config.py
│   └── async_routes.py
│
├── analytics/               # Metrics and dashboards
│   └── analytics_routes.py
│
├── knowledge_graph/         # Neo4j graph database
│   └── graph_routes.py
│
├── workflows/               # Event and evaluation workflows
│   ├── sequential_workflow.py
│   └── project_compilation.py
│
└── documentation/           # Complete documentation
    ├── README.md            # Documentation index
    ├── QUICKSTART.md        # 5-minute setup
    ├── ARCHITECTURE.md      # System design
    └── docs/                # Additional guides
```

---

## 🚀 Quick Start

### 1. Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your Azure OpenAI and database credentials
```

### 3. Initialize Frontend

```bash
cd web/chat
npm install
cp .env.example .env
# Edit .env with VITE_* variables (see below)
```

### 4. Run the Platform

```bash
# From project root: starts both backend API and frontend
.\start.ps1   # Windows PowerShell
# or
./start.sh    # Linux/macOS

# Access the UI at http://localhost:5173
# API Documentation at http://localhost:8000/docs
```

### 5. Frontend Environment Configuration

The frontend uses environment variables for complete customization:

```env
# API Configuration
VITE_CHAT_API_BASE=/api                           # Hub proxy endpoint
VITE_AOAI_ENDPOINT=https://xxx.openai.azure.com   # Direct Azure OpenAI (optional)
VITE_AOAI_DEPLOYMENT=gpt-4                        # Deployment name
VITE_AOAI_API_VERSION=2024-02-15-preview          # API version
VITE_AOAI_KEY=your-key                            # API key (dev only!)

# Content Configuration
VITE_SITE_TITLE="MSR Red: Redmond Research Showcase copilot"
VITE_FRONTPAGE_HEADING="Meet MSR Red: Your Guide for the Redmond Research Showcase"
VITE_FRONTPAGE_SUBHEADING="To plan your visit based on your research interests..."
VITE_PROMPT_INSTRUCTION="Get started with an example prompt below or enter your own."
VITE_AI_DISCLAIMER="AI may generate incorrect answers, please check citations for accuracy."

# Hero Cards Configuration (JSON array)
VITE_HERO_CARDS='[{"title":"Help me find projects...","subtitle":"Ask a few questions...","prompt":"..."}]'

# Theme & Links
VITE_THEME=webDark
VITE_FEEDBACK_URL="mailto:feedback@microsoft.com"
```

---

## � Phase B: API Integration & Event-Scoped Architecture

This platform provides a complete REST API with Graph-aligned responses supporting event-scoped project management, poster sessions, and knowledge extraction workflows.

### Run the API Server
```bash
# Development mode (with auto-reload)
python3 run_server.py --reload

# Production mode
python3 run_server.py --port 8000

# With custom data directory
python3 run_server.py --data ./custom_data --port 9000
```

**API Documentation**: http://localhost:8000/docs (Swagger UI)

### Programmatic Usage (without FastAPI)
```python
from main import ApplicationContext
from pathlib import Path

# Initialize
ctx = ApplicationContext(storage_root=Path("./data"))

# Create event
event = Event(
    id="evt_001",
    display_name="Research Summit",
    ...
)
ctx.event_repo.create(event)

# Create event-scoped project
project = ProjectDefinition(
    id="proj_001",
    event_id="evt_001",  # Phase B: Required
    name="Knowledge Extraction",
    ...
)
ctx.project_repo.create(project)
```

See [example_usage.py](example_usage.py) for complete example.

### API Endpoints
- `GET /health` - Health check
- `GET /v1/events` - List events
- `POST /v1/events` - Create event
- `GET /v1/events/{eventId}/sessions` - List event sessions
- `GET /v1/events/{eventId}/projects` - List event projects
- `POST /v1/events/{eventId}/projects` - Create project (event-scoped)
- `GET /v1/events/{eventId}/projects/{projectId}/knowledge` - List artifacts

**All responses follow Microsoft Graph conventions** with @odata.type, @odata.etag, and structured error handling.

---

## 📚 Documentation

- **[Complete Documentation](documentation/README.md)** - Full platform documentation
- **[Quick Start Guide](documentation/QUICKSTART.md)** - 5-minute setup walkthrough
- **[Architecture Overview](documentation/ARCHITECTURE.md)** - System design and components
- **[Deployment Guide](documentation/DEPLOYMENT_CHECKLIST.md)** - Production deployment checklist
- **[API Reference](documentation/docs/README.md)** - API endpoints and examples

---

## ✨ Key Features

### Event Management

- Multi-event homepage with promotion capabilities
- Event-specific sites (home, about, agenda pages)
- Multi-day schedules with tracks and themes
- Session detail pages with asset links

### Poster/Project Hub

- Poster hub pages with optional themes
- Project tiles with rich metadata
- Structured project pages with team info, abstracts, and related links
- QR code generation for bookmarking

### Knowledge Extraction

- AI-powered ingestion from research papers, talks, and repositories
- Structured knowledge artifacts (JSON)
- Heilmeier catechism summaries
- FAQ generation from project assets

### Discovery & Search

- Cross-event exploration
- AI-assisted chat for content discovery
- Bookmarking and personalized guides
- Recommendations based on interests

### Admin Tools

- Event and program management
- Content validation and curation
- Presenter self-service editing
- Engagement analytics and reporting

---

## 🏛️ Platform Architecture

### Production Infrastructure

- **Database**: PostgreSQL 16 with SQLAlchemy 2.0
- **Authentication**: JWT + Bcrypt password hashing
- **Configuration**: Pydantic BaseSettings with environment variables
- **Monitoring**: structlog + Prometheus metrics
- **Async Processing**: Celery 5.3 + Redis 7
- **Knowledge Graph**: Neo4j 5 for recommendations
- **Analytics**: Real-time metrics and dashboards

### API Structure

```
GET  /health                                     # Health check
GET  /v1/events                                  # List events
POST /v1/events                                  # Create event
GET  /v1/events/{eventId}/sessions               # Event sessions
GET  /v1/events/{eventId}/projects               # Event posters/projects
POST /v1/events/{eventId}/projects               # Create project
GET  /v1/events/{eventId}/projects/{projectId}   # Project details
GET  /v1/workflows/projects/{projectId}/evaluate # Start evaluation
```

**All responses follow Microsoft Graph conventions** with `@odata.type`, `@odata.etag`, and structured error handling.

---

## 🚢 Deployment

### Development

```bash
# Run tests
pytest

# Verify Phase E components
./verify_phase_e.sh
```

### Production

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Manual setup
./setup_phase_e.sh
python run_server.py --port 8000
```

See [DEPLOYMENT_CHECKLIST.md](documentation/DEPLOYMENT_CHECKLIST.md) for complete production deployment guide.

---

## 📊 Platform Status

**Phase E Complete**: Production-ready with all Tier 1-4 capabilities

- ✅ **E1.1 Database**: PostgreSQL persistence (1,100+ lines, 24 tests)
- ✅ **E1.2 Authentication**: JWT + Bcrypt (850+ lines, 23 tests)
- ✅ **E1.3 Configuration**: Pydantic settings (400+ lines)
- ✅ **E1.4 Monitoring**: structlog + Prometheus (400+ lines, 20 tests)
- ✅ **E2 Async Execution**: Celery + Redis (700+ lines, 30+ tests, 7 routes)
- ✅ **E3 Analytics**: Metrics + dashboards (700+ lines, 35+ tests, 10 routes)
- ✅ **E4 Knowledge Graph**: Neo4j + recommendations (900+ lines, 30+ tests, 11 routes)

**Total**: 5,250+ lines production code, 150+ tests, 35+ API routes

---

## 🗺️ Roadmap

### MVP (MSR India TAB - Late Jan)

- ✅ Event management and admin tools
- ✅ Poster/project hub with bookmarks
- ✅ Session management
- ✅ Knowledge extraction POC
- 🔄 Event-level AI chat

### Project Green (March)

- Lecture series support (Whiteboard Wednesdays)
- Workshop formats
- Research papers integration
- ResNet feed integration

### Cambridge Summerfest (April)

- Multi-site migration (RRS, Asia, Cambridge)
- Program owner reporting
- Participant self-service editing
- AI-powered update suggestions

### MSR Concierge (June)

- Researcher profile management
- Project update feeds
- Visitor recommendations
- Cross-event push notifications

---

## 📄 License

See LICENSE file for details.

### Run Workflow Example
```bash
# Demonstrate end-to-end workflow
python workflow_example.py

# Creates event, project, evaluation execution
# Simulates evaluation and iteration phases
# Shows complete lifecycle with status tracking
```

### Workflow API Endpoints
- `POST /v1/workflows/projects/{projectId}/evaluate` - Start evaluation
- `GET /v1/workflows/executions/{executionId}` - Get execution status
- `GET /v1/workflows/executions/{executionId}/iterations` - Get iteration history
- `POST /v1/workflows/executions/{executionId}/cancel` - Cancel execution
- `POST /v1/workflows/executions/{executionId}/retry` - Retry evaluation
- `GET /v1/workflows/projects/{projectId}/history` - Project evaluation history
- `GET /v1/workflows/configurations` - Available evaluation configurations
- `GET /v1/workflows/metrics/summary` - Workflow statistics

### Programmatic Workflow Usage
```python
from main import ApplicationContext
from core.workflow_status import EvaluationExecutionRepository

# Initialize
ctx = ApplicationContext(storage_root="./data")
exec_repo = EvaluationExecutionRepository()

# Create and track execution
exe = exec_repo.create_execution(
    project_id="proj_001",
    event_id="evt_001",
    configuration="standard"
)

# Progress through phases
exec_repo.mark_started(exe.execution_id)
exec_repo.mark_evaluating(exe.execution_id)
exec_repo.mark_iterating(exe.execution_id, iteration=1)

# Complete with results
exec_repo.mark_completed(
    exe.execution_id,
    final_score=4.2,
    scorecard={...},
    passed=True
)

# Query history
history = exec_repo.list_by_project(project_id)
active = exec_repo.list_active()
```

### Workflow Components
- **ProjectExecutor**: Evaluates projects using HybridEvaluator
- **IterationController**: Manages evaluation iteration cycles
- **HybridEvaluator**: 5-dimension evaluation framework
- **EvaluationExecution**: Complete execution state tracking
- **EvaluationExecutionRepository**: Persistence and history

### Evaluation Dimensions
1. Structure Completeness
2. Extraction Accuracy
3. Fidelity to Source
4. Signal-to-Noise Ratio
5. Reusability for AI

**Quality Threshold**: Default 3.0/5.0, configurable per evaluation

**Configurations**:
- `standard`: 2 max iterations, 3.0 threshold
- `aggressive`: 4 max iterations, 2.5 threshold
- `strict`: 1 max iteration, 4.0 threshold

### Execution Lifecycle
```
pending → running → evaluating → iterating → completed
         ↓
       → running → evaluating → failed
         ↓
       → cancelled
```

See [PHASE_D_SUMMARY.md](PHASE_D_SUMMARY.md) for complete workflow architecture and integration guide.

---

## � Phase E: Production Hardening & Enterprise Features

**New in v0.4.0**: Complete enterprise infrastructure with monitoring, async execution, analytics, and knowledge graph integration.

### Phase E Components

#### E1: Foundation Infrastructure
- **Database Layer** (E1.1): PostgreSQL with SQLAlchemy 2.0 ORM
  - User management with role-based access control (RBAC)
  - Project, artifact, and evaluation repositories
  - Database migrations with Alembic
  
- **Authentication** (E1.2): JWT + Bcrypt
  - Secure password hashing
  - JWT token generation and validation
  - Role-based authorization
  - Token refresh mechanics
  
- **Configuration** (E1.3): Pydantic BaseSettings
  - Environment variable validation
  - Settings by environment (dev/staging/production)
  - Secure secret management
  
- **Monitoring** (E1.4): Observability Stack
  - Structured logging with structlog
  - Prometheus metrics integration
  - Application health checks
  - Performance monitoring

#### E2: Async Job Execution
- **Celery Integration**: Distributed task queue
  - Job enqueueing (evaluate_project, process_artifact_batch, generate_report)
  - Status tracking (PENDING → QUEUED → RUNNING → COMPLETED/FAILED/CANCELLED)
  - Result storage and retrieval
  - Worker management and scaling
  
- **Redis**: In-memory message broker and result backend
  - Sub-1ms task dispatch
  - Distributed job coordination

#### E3: Analytics & Metrics
- **Metrics Collection**: Point-in-time metrics with tags
  - Request counting, database performance, authentication attempts
  - Evaluation metrics, system resource tracking
  
- **Dashboards**: Real-time visualization
  - Realtime dashboard: Current system state
  - Performance dashboard: API latency, throughput, database connections
  - Health dashboard: System health, availability, error rates
  
- **Reports**: Scheduled reporting
  - Daily/weekly/monthly summaries
  - CSV and JSON export
  - Trend analysis

#### E4: Knowledge Graph
- **Neo4j Integration**: Graph database for knowledge relationships
  - Node types: Paper, Author, Technology, Concept, Venue, Project, Artifact, Evaluation
  - Relationship types: RELATED_TO, CITES, AUTHOR, PUBLISHED_IN, USES, IMPLEMENTS, DEPENDS_ON, SIMILAR_TO, DERIVED_FROM, EVALUATES
  
- **Query Capabilities**:
  - Full-text search across nodes
  - Path finding between concepts
  - Connection discovery and traversal
  
- **Recommendations**: Intelligent suggestions
  - Related paper recommendations
  - Technology recommendations
  - Expert finding
  - Similarity calculations

### Quick Start with Docker

```bash
# One-command deployment of entire stack
docker-compose up -d

# Verify services
docker-compose ps

# Check application health
curl http://localhost:8000/api/health

# View logs
docker-compose logs -f app
```

### Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Edit .env with your database, Redis, Neo4j URLs

# 3. Initialize database
alembic upgrade head

# 4. Start application
uvicorn knowledge_agent_bot:app --reload

# 5. Start Celery worker (in another terminal)
celery -A async_execution worker --loglevel=info

# 6. Start Celery beat (in another terminal)
celery -A async_execution beat --loglevel=info
```

### API Endpoints

#### E1: Foundation
- `POST /api/users/register` - Register new user
- `POST /api/users/login` - Login and get JWT token
- `GET /api/users/me` - Get current user profile
- `GET /api/health` - Health check
- `GET /api/metrics` - Current metrics

#### E2: Async Execution
- `POST /api/async/evaluate` - Enqueue project evaluation
- `POST /api/async/batch-process` - Enqueue batch processing
- `POST /api/async/generate-report` - Enqueue report generation
- `GET /api/async/jobs/{id}` - Get job status
- `GET /api/async/jobs` - List all jobs
- `DELETE /api/async/jobs/{id}` - Cancel job
- `GET /api/async/health` - Async execution health

#### E3: Analytics
- `POST /api/analytics/metrics` - Record metric
- `GET /api/analytics/metrics/{name}/history` - Metric history
- `GET /api/analytics/dashboards/realtime` - Realtime dashboard
- `GET /api/analytics/dashboards/performance` - Performance dashboard
- `GET /api/analytics/dashboards/health` - Health dashboard
- `GET /api/analytics/reports/daily` - Daily report
- `GET /api/analytics/reports/weekly` - Weekly report
- `GET /api/analytics/reports/monthly` - Monthly report
- `GET /api/analytics/export` - Export metrics

#### E4: Knowledge Graph
- `POST /api/graph/nodes` - Create node
- `POST /api/graph/edges` - Create edge
- `GET /api/graph/nodes/{id}` - Get node
- `GET /api/graph/search` - Search nodes
- `GET /api/graph/nodes/type/{type}` - Get nodes by type
- `GET /api/graph/paths` - Find path between nodes
- `GET /api/graph/connections/{id}` - Get node connections
- `GET /api/graph/recommendations/papers/{id}` - Paper recommendations
- `GET /api/graph/recommendations/technologies/{id}` - Technology recommendations
- `GET /api/graph/experts` - Find experts
- `GET /api/graph/similarity` - Calculate similarity

### Example: Complete Workflow

```python
from examples.phase_e_api_examples import E1Examples, E2Examples, E3Examples, E4Examples

# E1: Authentication
user_data = E1Examples.user_registration()
login_data = E1Examples.user_login()
token = login_data["access_token"]

# E2: Enqueue async job
job = E2Examples.enqueue_project_evaluation(token, "proj-123")
job_id = job["job_id"]
status = E2Examples.get_job_status(token, job_id)

# E3: Record and view analytics
E3Examples.record_metric(token, "evaluations_completed", 1.0)
dashboard = E3Examples.get_realtime_dashboard(token)

# E4: Query knowledge graph
nodes = E4Examples.search_nodes(token, "security")
recommendations = E4Examples.recommend_papers(token, "paper-1")
```

See [examples/phase_e_api_examples.py](examples/phase_e_api_examples.py) for comprehensive API examples.

### Production Deployment

For Kubernetes deployment, see [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for:
- Docker image building
- Environment configuration
- Database setup and migrations
- Redis configuration
- Neo4j setup
- Monitoring and alerting
- Security hardening
- Performance tuning

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific phase tests
pytest tests/test_e1_database.py -v
pytest tests/test_e1_authentication.py -v
pytest tests/test_e2_async.py -v
pytest tests/test_e3_analytics.py -v
pytest tests/test_e4_knowledge_graph.py -v
pytest tests/test_integration_e1_e4.py -v

# Generate coverage report
pytest --cov=. tests/
```

### Statistics
- **150+ Tests**: Comprehensive coverage for all phases
- **5,250+ Lines**: Production code
- **35+ API Routes**: Full REST API
- **2,000+ Lines**: Documentation

See [PHASE_E_COMPLETION.md](PHASE_E_COMPLETION.md) for detailed completion report.

---

## �📊 Scope & Constraints

### In Scope (POC v1)
- ✅ Manual artifact selection (3–4 projects)
- ✅ Artifact-level knowledge extraction
- ✅ Prompt-based LLM agents
- ✅ Structured JSON schemas
- ✅ Human expert review
- ✅ Iterative prompt tuning

### Phase B (v0.2.0) New Features
- ✅ Event-scoped project management
- ✅ REST API with FastAPI
- ✅ Graph-aligned responses
- ✅ Knowledge artifact repositories
- ✅ Approved/published knowledge workflow
- ✅ Session management within events

### Out of Scope
- ❌ Model fine-tuning
- ❌ Automated publishing
- ❌ Full knowledge graph
- ❌ Continuous ingestion pipelines
- ❌ MSR-wide deployment

---

## 🎯 Success Metrics

**POC Success Indicators:**
- Expert accuracy rating ≥ 4/5
- High inter-reviewer agreement
- Clear improvement over baseline abstracts
- Successful JSON production across all 3 artifact types
- Feasibility of project-level compilation (stretch goal)

---

## 📝 Knowledge Schema

All agents produce outputs following a **common baseline schema**:

- Title & Contributors
- Plain-language overview
- Technical problem addressed
- Key methods/approach
- Primary claims/capabilities
- Novelty vs. prior work
- Limitations & constraints
- Potential impact
- Open questions/future work
- Key evidence/citations
- Confidence score
- Provenance (agent + source type)

Each agent appends **datatype-specific sections** plus a flexible **Additional/Found Knowledge** section.

### Paper Schema Extension
- Publication & Context (venue, year, peer-review status)
- Data & Evaluation (datasets, benchmarks, metrics)
- Results & Evidence (quantitative results, reproducibility)
- Research Maturity (stage, limitations, ethics)

### Talk Schema Extension
- Presentation Structure (type, duration, sections)
- Demonstration & Evidence (demo included, live vs. recorded)
- Challenges & Forward-Looking Content (technical challenges, next steps)
- Audience & Framing (audience level, assumed knowledge)

### Repository Schema Extension
- Artifact Classification (type, purpose, intended users)
- Technical Stack (languages, frameworks, platforms)
- Operational Details (setup, training/inference, dependencies)
- Usage & Maturity (use cases, API, limitations)
- Governance & Access (license, data constraints)

---

## 🔄 Workflow

1. **Select Artifacts**: Choose 3–4 RRS projects with overlapping artifacts
2. **Collect Inputs**: Gather papers, transcripts, and repos
3. **Design Schemas**: Define v1 schema for each artifact type
4. **Run Extraction**: Execute agents to generate structured outputs
5. **Expert Review**: Assess quality, accuracy, completeness
6. **Iterate**: Refine prompts and schemas based on feedback
7. **Finalize**: Produce final v1 knowledge artifacts

---

## 🎨 Stretch Goal – Project-Level Compilation

Explore collating paper, talk, and repo knowledge JSON into a single project-level knowledge base:

- Synthesized project overview
- Project-level knowledge FAQ
- Resolution of conflicts/overlaps

**Success** = Technical feasibility demonstrated (not production-ready)

---

## 📖 Related Documentation

- [DECISION_GUIDE.md](../docs/DECISION_GUIDE.md) - General project guidance
- [docs/UNIFIED_ADAPTER_ARCHITECTURE.md](../docs/UNIFIED_ADAPTER_ARCHITECTURE.md) - EventKit adapter pattern
- Parent project: [EventKit on main branch](https://github.com/peterswimm/event-agent-december)

---

## 🛠️ Development Notes

- **LLMs Only**: No model fine-tuning; prompt engineering only
- **Iterative**: Expect multiple refinement cycles
- **Human-First**: All AI outputs are drafts requiring human review
- **Source Attribution**: All claims must reference original sources
- **Opt-In**: Only projects with explicit approval are included

---

## 📞 Feedback & Iteration

This is a living POC. Feedback from expert reviewers will drive:
- Prompt refinement
- Schema improvements
- New extraction capabilities
- Integration insights

---

**Last Updated**: December 18, 2025
**Status**: Active Development
**Branch**: poc1219
