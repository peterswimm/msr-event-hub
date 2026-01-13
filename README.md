# MSR Event Agent Chat

**AI-Powered Chat & Discovery for MSR Research Events**

**Status**: Production-Ready | **Framework**: FastAPI + React | **Auth**: Azure Managed Identity

---

## 🎯 What This Does

The MSR Event Agent Chat service helps attendees discover and explore research from MSR events through a unified, intelligent interface. It provides:

- **15 unified chat actions** for browsing, filtering, searching, and navigating research projects
- **AI recommendations** and researcher discovery
- **Real-time streaming responses** with rich Adaptive Cards
- **Cross-event knowledge exploration** for researchers
- **Session caching** for responsive interactions
- **Microsoft 365 Copilot** integration ready

### Key Features
✅ Browse, filter, and search 1000+ research projects  
✅ Real-time streaming chat responses  
✅ AI-powered researcher discovery (with Foundry delegation)  
✅ Rich project detail pages with related assets  
✅ Bookmarking and personalized recommendations  
✅ Multi-event support (Redmond, India, Cambridge, etc.)

---

## ⚡ Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your Azure OpenAI endpoint and key
```

### 3. Initialize Database & Start Server
```bash
# Initialize database (first time only)
python -c "from core.database import init_db; init_db()"

# Start FastAPI server
python main.py
# Server runs on http://localhost:8000
```

### 4. Test the API
```bash
# Health check
curl http://localhost:8000/health

# Try a chat action
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "action": "browse_all",
    "payload": {"limit": 10}
  }'

# View interactive API docs
# Open http://localhost:8000/docs in your browser
```

---

## 📚 The 15 Chat Actions

All actions return streaming responses with text + adaptive cards. Below is the complete action reference.

### Browse Actions (3)

Browse and explore research projects with curated views.

| Action | Description | Input | Output |
| --- | --- | --- | --- |
| `browse_all` | Show all projects with pagination | `limit` (int, optional) | Carousel card |
| `show_featured` | Show featured/highlighted projects | none | Carousel card |
| `recent_projects` | Show most recently added projects | none | Carousel card |

**Example**:
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"action": "browse_all", "payload": {"limit": 10}}'
```

### Filter Actions (7)

Filter projects by various criteria. Results appear as carousel cards.

| Action | Filter By | Input Parameter | Example Value |
| --- | --- | --- | --- |
| `filter_by_status` | Project status | `status` | "active", "completed" |
| `filter_by_team_size` | Team size | `min`, `max` | {"min": 2, "max": 5} |
| `filter_by_audience` | Target audience | `audience` | "researchers", "practitioners" |
| `filter_by_location` | Physical location | `location` | "Redmond", "Cambridge" |
| `equipment_filter` | Equipment used | `equipment` | "GPU", "microscope" |
| `recording_filter` | Recording available | `available` | true, false |
| `filter_by_area` | Research area | `area` | "AI", "HCI", "Systems" |

**Example**:
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "action": "filter_by_area",
    "payload": {"area": "AI"}
  }'
```

### Search Actions (2)

Search across project metadata using keywords or researcher names.

| Action | Searches | Input | Special |
| --- | --- | --- | --- |
| `keyword_search` | Project titles, descriptions | `keyword` (string) | Local search |
| `researcher_search` | Researcher names, expertise | `researcher` (string) | Uses Foundry AI |

**Example - Keyword Search**:
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"action": "keyword_search", "payload": {"keyword": "machine learning"}}'
```

**Example - Researcher Search (with Foundry)**:
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"action": "researcher_search", "payload": {"researcher": "John Smith"}}'
```

### Navigate Actions (3)

Navigate through projects and manage browsing context.

| Action | Purpose | Input | Updates Context |
| --- | --- | --- | --- |
| `view_project` | Show project detail | `projectId` (string) | Marks as viewed |
| `back_to_results` | Return to last results | none | Updates stage |
| `find_similar` | Find related projects | `researchArea` (string) | Filters similar |
| `category_select` | Select research category | `category` (string) | Updates filters |

**Example**:
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "action": "view_project",
    "payload": {"projectId": "project-123"}
  }'
```

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Chat Frontend                             │
│           (React 18 + Vite + Fluent UI)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ SSE Streaming
┌────────────────────────▼────────────────────────────────────┐
│           FastAPI Chat Server (Port 8000)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Unified Action Registry                      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐  │   │
│  │  │ Browse  │ │ Filter  │ │ Search  │ │ Navigate │  │   │
│  │  │ Actions │ │ Actions │ │ Actions │ │ Actions  │  │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └──────────┘  │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐   │
│  │         Shared Infrastructure                        │   │
│  │  • Pydantic validation schemas                       │   │
│  │  • Error handling middleware                         │   │
│  │  • SSE response generator                            │   │
│  │  • Session caching (TTL + enable/disable)           │   │
│  │  • Adaptive Card builders                            │   │
│  └──────────────────┬───────────────────────────────────┘   │
│                     │                                        │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────────┐
│         MSR Event Hub Backend                                │
│    (Event data, project metadata, knowledge graph)           │
└─────────────────────────────────────────────────────────────┘
```

### Unified Action System

All 15 chat actions use a consistent pattern:

```
Request JSON
    ↓
┌─ Pydantic Schema Validation ─┐
│ (Ensures type safety)         │
└─────────────┬──────────────────┘
              ↓
┌─ Action Registry Dispatch ─┐
│ (Route to correct handler)  │
└─────────────┬────────────────┘
              ↓
┌─ Handler Execute ────────────────────┐
│ (Business logic for specific action) │
└─────────────┬──────────────────────────┘
              ↓
┌─ Session Cache & Update ─────────┐
│ (Cache results, update context)   │
└─────────────┬────────────────────┘
              ↓
┌─ Error Middleware ────────────────────┐
│ (Catch exceptions, log, return cards) │
└─────────────┬──────────────────────────┘
              ↓
      SSE Response (text + card)
```

### Key Design Patterns

**1. Registry Pattern**: `ActionRegistry` singleton manages all 15 handlers
- Enables dynamic handler dispatch: `registry.dispatch("action_name", payload, context)`
- No hardcoded if/elif chains

**2. Strategy Pattern**: Each handler is independent, reusable strategy
- All inherit `BaseActionHandler` ABC
- Implement `execute()` + optional `update_context()`

**3. Decorator Pattern**: `@register_action` enables declarative registration
- Handlers auto-register on import
- `@requires_foundry=True` marks Foundry-delegated actions

**4. Factory Pattern**: Shared helpers reduce boilerplate
- `create_streaming_response()`: SSE generator factory
- `apply_filter()`: Filter consolidation
- `build_project_carousel()`: Card generation

**5. Middleware Pattern**: Error handling via wrapper
- Catches exceptions, logs context, returns error cards
- Unified error format across all actions

---

## 📁 Project Structure

```
msr-event-agent-chat/
├── api/
│   ├── actions/                    # Unified action system (NEW)
│   │   ├── __init__.py
│   │   ├── base.py                 # ActionRegistry + BaseActionHandler ABC
│   │   ├── schemas.py              # Pydantic validation (15 types)
│   │   ├── helpers.py              # Shared utilities
│   │   ├── decorators.py           # @register_action, @requires_foundry
│   │   ├── middleware.py           # Error handling
│   │   ├── browse/
│   │   │   ├── __init__.py
│   │   │   └── handlers.py         # BrowseAll, ShowFeatured, RecentProjects
│   │   ├── filter/
│   │   │   ├── __init__.py
│   │   │   └── handlers.py         # 7 filter handlers
│   │   ├── search/
│   │   │   ├── __init__.py
│   │   │   └── handlers.py         # Keyword, Researcher (Foundry)
│   │   └── navigation/
│   │       ├── __init__.py
│   │       └── handlers.py         # ViewProject, BackToResults, FindSimilar, etc.
│   ├── caching.py                  # Session cache with TTL (NEW)
│   ├── action_init.py              # Handler initialization (NEW)
│   ├── chat_routes.py              # FastAPI routes (refactored)
│   ├── conversation_context.py     # State management
│   └── card_renderer.py            # Adaptive Card generation
│
├── config/                         # Configuration
├── core/                           # Core business logic
├── tests/
│   ├── test_actions.py             # Comprehensive test suite
│   ├── test_chat_routes.py
│   └── conftest.py                 # Pytest fixtures
│
├── examples/                       # Example code & workflows
│   ├── workflows/
│   │   ├── workflow_example.py
│   │   └── README.md
│   ├── chat-actions/
│   │   └── README.md
│   └── integration/
│       └── README.md
│
├── main.py                         # FastAPI app entry point
├── pyproject.toml                  # Python dependencies
├── pytest.ini                      # Test configuration
├── .env.example                    # Environment template
│
└── docs/                           # Supporting documentation
    ├── ARCHITECTURE.md
    ├── DEPLOYMENT.md
    └── TROUBLESHOOTING.md
```

---

## 🔨 Development Guide

### Adding a New Chat Action (5 minutes)

**Step 1: Create Handler**

```python
# api/actions/myfeature/handlers.py
from api.actions.decorators import register_action
from api.actions.base import BaseActionHandler

@register_action(
    "my_action",
    description="What this action does",
    requires_foundry=False  # Set True if using Foundry reasoning
)
class MyActionHandler(BaseActionHandler):
    
    async def execute(self, payload, context):
        """
        payload: Validated Pydantic model
        context: ConversationContext with session state
        
        Returns: (text, card) tuple
        """
        # Implement your logic
        text = "Result text"
        card = None  # Or Adaptive Card dict
        return text, card
    
    async def update_context(self, payload, context):
        """Optional: Update conversation context"""
        context.conversation_stage = "show_results"
```

**Step 2: Add Pydantic Schema**

```python
# api/actions/schemas.py
class MyActionPayload(BaseModel):
    param1: str
    param2: int = 10  # Optional with default

# Register in PAYLOAD_SCHEMAS dict
PAYLOAD_SCHEMAS["my_action"] = MyActionPayload
```

**Step 3: Import in Initialization**

```python
# api/action_init.py
from api.actions.myfeature.handlers import MyActionHandler
```

That's it! No routing changes needed. The `@register_action` decorator handles everything.

### Testing Your Action

```bash
# Test via API
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"action": "my_action", "payload": {"param1": "test"}}'

# Run unit tests
pytest tests/test_actions.py::TestMyAction -v
```

### Session Caching

```python
from api.caching import get_session_cache

cache = get_session_cache()

# Get cached data
data = cache.get("key")

# Set with custom TTL
cache.set("key", data, ttl_seconds=300)

# Disable caching for real-time data
cache.toggle(False)

# Clear specific entry
cache.invalidate("key")
```

### Using Foundry Delegation

Mark handlers that need reasoning capabilities:

```python
@register_action(
    "advanced_action",
    description="Uses AI reasoning",
    requires_foundry=True  # Delegates to Foundry
)
class AdvancedHandler(BaseActionHandler):
    async def execute(self, payload, context):
        # Foundry agents can handle complex tasks
        pass
```

---

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Action Tests Only
```bash
pytest tests/test_actions.py -v
```

### Test Coverage
```bash
pytest tests/ --cov=api --cov-report=html
# View report at htmlcov/index.html
```

### Example Test
```python
@pytest.mark.asyncio
async def test_browse_all_handler(mock_projects, context):
    handler = BrowseAllHandler("browse_all")
    text, card = await handler.execute({"limit": 5}, context)
    
    assert "projects" in text.lower()
    assert card["type"] == "AdaptiveCard"
    assert context.conversation_stage == "show_results"
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required
AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=deployment-name

# Optional
CACHE_ENABLED=true                    # Enable session caching
CACHE_TTL=3600                        # Cache timeout in seconds
FOUNDRY_ENDPOINT=https://xxx.foundry  # For Foundry delegation
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
```

### Disable Caching Globally

```python
# In main.py before starting server
from api.caching import SessionCache
cache = SessionCache(enabled=False)
```

---

## 🚀 Deployment

### Docker
```bash
# Build image
docker build -t msr-event-chat:latest .

# Run container
docker run -p 8000:8000 \
  -e AZURE_OPENAI_ENDPOINT=xxx \
  -e AZURE_OPENAI_KEY=xxx \
  msr-event-chat:latest
```

### Production Checklist
- [ ] Set all required environment variables
- [ ] Enable HTTPS
- [ ] Configure CORS for frontend domain
- [ ] Set up monitoring/logging
- [ ] Run full test suite
- [ ] Load test with expected concurrency
- [ ] Set up database backups
- [ ] Configure health checks

---

## 📖 Quick Reference

### Common Operations

**Check Handler Registration**
```bash
curl http://localhost:8000/api/chat/actions
```

**Health Check**
```bash
curl http://localhost:8000/health
```

**Get Welcome Message**
```bash
curl http://localhost:8000/api/chat/welcome
```

**View API Docs**
Open http://localhost:8000/docs in browser

### Troubleshooting

**Issue**: Handler not registered
- Verify `import api.action_init` is in main.py before defining routes
- Check that `initialize_action_handlers()` is called
- Look for import errors in logs

**Issue**: Validation errors on payload
- Check QUICK_REFERENCE.md for action schema
- Ensure required fields are present
- Verify field types match (string vs number)

**Issue**: Slow responses
- Check cache is enabled: `CACHE_ENABLED=true`
- Monitor event data load times
- Check Foundry agent latency if using `@requires_foundry`

**Issue**: Out of memory
- Reduce cache TTL: `CACHE_TTL=300`
- Limit concurrent sessions
- Profile memory usage with `memory_profiler`

---

## 📚 Additional Resources

- **Architecture Details**: See [UNIFIED_ACTIONS_IMPLEMENTATION.md](./UNIFIED_ACTIONS_IMPLEMENTATION.md)
- **Integration Steps**: See [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)
- **Examples**: See [examples/README.md](./examples/README.md)
- **Microsoft 365 Integration**: See [.github/COPILOT_INSTRUCTIONS_UPDATED.md](./.github/COPILOT_INSTRUCTIONS_UPDATED.md)

---

## 🔗 Related Projects

- **msr-event-agent-bridge**: Content enrichment & API gateway
- **msr-event-hub**: Main platform (events, projects, knowledge graph)

---

## 📊 Metrics & KPIs

- Action dispatch latency: <100ms (p95)
- Streaming response time: <1s initial, <100ms per chunk
- Cache hit rate: >80% for repeat queries
- Error rate: <0.1%
- Test coverage: >85%

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-action`
2. Implement handler + tests
3. Run `pytest tests/ -v`
4. Submit PR with description

---

## 📝 License

Internal MSR Platform - Microsoft Research

---

**Questions?** Check the docs/, examples/, or troubleshooting section above.
