# MSR Event Hub - Quick Start Guide

Run the complete MSR Event Hub with hybrid query routing, Azure AI Foundry integration, and chat interface.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Azure OpenAI resource (or OpenAI API key)

## Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Minimum required configuration:**

```bash
# Azure OpenAI (for chat)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_VERSION=2024-02-15-preview

# For local dev with mock data (no backend needed)
EVENT_DATA_SOURCE=mock
```

**Optional: Enable Foundry SaaS orchestration**

```bash
DELEGATE_TO_FOUNDRY=true
FOUNDRY_ENDPOINT=https://your-foundry.cognitiveservices.azure.com
FOUNDRY_AGENT_ID=msr-event-orchestrator
```

### 3. Build Frontend (Automatic on first run)

The startup script will automatically build the frontend. To build manually:

```bash
cd web/chat
npm install
npm run build
cd ../..
```

## Running the Server

### Windows (PowerShell)

```powershell
.\start.ps1
```

### Linux/macOS

```bash
chmod +x start.sh
./start.sh
```

### Manual Start

```bash
python main.py
```

## Access the Application

- **Chat Interface**: http://localhost:8000/
- **API Documentation**: http://localhost:8000/docs
- **Routing Config**: http://localhost:8000/api/chat/config

## Features

### Hybrid Query Routing

The system intelligently routes queries:

1. **Deterministic Path (70-80%)** - Pattern matching, <100ms, ~$0 cost
2. **Foundry Delegation (15-20%)** - Multi-agent orchestration for complex queries
3. **Azure OpenAI Fallback (5-10%)** - General conversation

### Feature Flags

Toggle routing behavior via `.env`:

```bash
# Enable/disable deterministic routing
ENABLE_DETERMINISTIC_ROUTING=true

# Routing strategy
ROUTING_STRATEGY=deterministic_first  # or llm_only, deterministic_only, hybrid

# Confidence thresholds
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.8
FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD=0.8

# Enable Foundry SaaS orchestration
DELEGATE_TO_FOUNDRY=false
```

### Mock Data Mode

For development without backend dependencies:

```bash
EVENT_DATA_SOURCE=mock
MOCK_DATA_PATH=data/mock_event_data.json
```

Includes 5 sample projects, 4 sessions, 8 researchers.

## Configuration Reference

### Azure OpenAI (Required)

```bash
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_VERSION=2024-02-15-preview
AZURE_OPENAI_KEY=  # Leave empty for managed identity
```

### Routing Configuration

```bash
ENABLE_DETERMINISTIC_ROUTING=true
ROUTING_STRATEGY=deterministic_first
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.8
LLM_ASSIST_CONFIDENCE_THRESHOLD=0.6
```

### Foundry SaaS (Optional)

```bash
DELEGATE_TO_FOUNDRY=false
FOUNDRY_ENDPOINT=
FOUNDRY_AGENT_ID=msr-event-orchestrator
FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD=0.8
```

### Server Configuration

```bash
PORT=8000         # Server port
HOST=0.0.0.0      # Server host
```

## Troubleshooting

### Frontend not building

```bash
cd web/chat
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Python dependencies missing

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Azure OpenAI authentication errors

**Development:** Set `AZURE_OPENAI_KEY` in `.env`

**Production:** Use managed identity:
```bash
AZURE_OPENAI_KEY=  # Leave empty
az login
```

### Port already in use

Change port in `.env`:
```bash
PORT=8001
```

## Development Workflow

### Run with auto-reload (Python)

```bash
uvicorn main:app --reload --port 8000
```

### Run frontend dev server (separate terminal)

```bash
cd web/chat
npm run dev  # Opens on http://localhost:5173
```

Frontend will proxy API requests to `http://localhost:8000/api`

## Project Structure

```
msr-event-hub/
├── main.py                 # FastAPI application entry point
├── api/                    # API routes
│   ├── chat_routes.py      # Hybrid chat endpoint
│   ├── query_router.py     # Deterministic classification
│   ├── router_config.py    # Feature flags & config
│   └── foundry_client.py   # Foundry SaaS integration
├── web/chat/               # React frontend (Vite + Fluent UI)
│   ├── src/                # React components
│   └── dist/               # Built frontend (served by FastAPI)
├── data/                   # Mock data for development
│   └── mock_event_data.json
├── documentation/          # Guides & architecture docs
├── start.ps1              # Windows startup script
├── start.sh               # Linux/macOS startup script
└── .env.example           # Configuration template
```

## Documentation

- **Query Routing**: [documentation/QUERY_ROUTING_WITH_FOUNDRY.md](documentation/QUERY_ROUTING_WITH_FOUNDRY.md)
- **Event Schema**: [documentation/EVENT_SCHEMA.md](documentation/EVENT_SCHEMA.md)
- **Azure OpenAI Setup**: [documentation/AZURE_OPENAI_SETUP.md](documentation/AZURE_OPENAI_SETUP.md)

## Support

For issues or questions:

1. Check logs: Server outputs detailed routing decisions when `LOG_ROUTING_DECISIONS=true`
2. Verify config: `GET http://localhost:8000/api/chat/config`
3. Review documentation in `documentation/` folder
4. Test with mock data: `EVENT_DATA_SOURCE=mock`

---

**Quick Start (TL;DR)**

```bash
# 1. Setup
cp .env.example .env
# Edit .env: Add AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT

# 2. Run
.\start.ps1  # Windows
# or
./start.sh   # Linux/macOS

# 3. Open browser
# http://localhost:8000/
```
