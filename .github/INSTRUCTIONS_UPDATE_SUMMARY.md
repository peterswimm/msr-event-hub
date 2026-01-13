# Copilot Instructions Update Summary

## Overview

Updated copilot instructions for both **msr-event-agent-chat** and **msr-event-agent-bridge** projects to provide clear context on the MSR Event Hub platform, shared data models, architecture patterns, and AI/chat integration strategies.

## What Was Added

### 1. Platform Context

- Clear explanation that these are part of the MSR Event Hub platform
- Vision: Extend research event impact across time and geography
- Key constraints: @microsoft.com-only access, no Office 365 integration without consent

### 2. Shared Data Models

Both instructions now document the complete data structures:

#### Posters

- Core identity (title, abstract, assets)
- Event context (location, track, event)
- People & contact information
- Related assets (videos, decks, papers, code, links)
- **Knowledge fields** (AI-enriched): How organized, what's new, evidence, next steps, maturity

#### Sessions (talks, workshops, panels)

- Core identity, type, recording
- Event context, date/time, location
- Speakers, moderators, contacts
- Related assets
- **Knowledge fields**: Structure, novelty, evidence, questions, next steps, maturity

#### Research Projects

- Meta-container linking related work
- Cross-references (repos, papers, talks, posters)
- Synthesized project knowledge

### 3. Differentiated Responsibilities

#### msr-event-agent-chat (Attendee-focused)

- Chat actions for discovering research
- Filter, search, navigate projects/sessions
- AI recommendations
- Cross-event discovery
- Handler-based architecture with ActionRegistry

#### msr-event-agent-bridge (Content-focused)

- Content enrichment pipeline
- Data ingestion (Excel, PDFs, submissions)
- Link crawling and metadata extraction
- AI-assisted summarization
- Organizer/presenter tools
- Multi-event normalization

### 4. AI Integration Patterns

#### Chat Service

- Uses ActionRegistry for handler dispatch
- Handlers can delegate to Foundry via `@requires_foundry` decorator
- Streaming responses via SSE
- Pydantic validation schemas

#### Bridge Service

- Content enrichment pipeline using Foundry and Azure OpenAI
- Foundry for reasoning-heavy tasks (summarization, insight extraction)
- Azure OpenAI for commodity tasks (keywords, classification)
- Human review guardrails for all AI suggestions

### 5. Development Workflow Guidance

#### Chat Service

- Adding handlers (inherit BaseActionHandler, use decorators)
- Creating Pydantic schemas
- Testing in isolation
- Foundry delegation patterns

#### Bridge Service

- Adding enrichment tasks (input → AI → validation → output)
- Extending for new event formats
- Performance optimization
- Multi-event architecture

### 6. Project Phases & Roadmap

Both documents reference the 4-phase roadmap:

1. **MVP** (MSR India - Late Jan): Posters, sessions, basic chat
2. **Phase 2** (Project Green - March): Workshops, lecture series, papers
3. **Phase 3** (Cambridge - April): Migration, presenter edits, reporting
4. **Phase 4** (Concierge - June): Cross-event, recommendations, AI tools

---

## Key Alignments Between Projects

| Aspect | Chat Service | Bridge Service |
| --- | --- | --- |
| **Data Models** | Consume Posters/Sessions | Produce Posters/Sessions |
| **AI/Foundry** | Delegate reasoning to Foundry | Use Foundry for enrichment |
| **Multi-Event** | Handle multiple events in single chat | Ingest/normalize for multiple events |
| **Content Knowledge** | Surface AI-enriched fields to users | Generate AI-enriched fields |
| **Quality** | Pydantic validation on input | Guardrails on AI output |
| **Architecture** | Handler-based registry | Pipeline-based processors |

---

## Integration Points

### Chat → Bridge Flow

1. User interacts with chat action
2. Chat service queries event data
3. Bridge service provides normalized Poster/Session/Project data

### Bridge → Chat Flow

1. Organizer publishes event content
2. Bridge service enriches and normalizes data
3. Chat service syncs normalized data for attendee access

### External Integrations

Both services integrate with:

- Event Hub knowledge base
- Admin portal
- Microsoft 365 Copilot (via declarative agents)
- Azure Foundry agents
- Content repositories (GitHub, papers, etc.)

---

## Next Steps

### For msr-event-agent-chat

1. ✅ Complete implementation of unified action system
2. Integrate with Bridge service for event data
3. Implement Foundry delegation for recommendations
4. Add cross-event discovery features

### For msr-event-agent-bridge

1. Design content enrichment pipeline
2. Implement ingestion for Excel/PDF
3. Set up Foundry integration for summarization
4. Build organizer approval workflow
5. Implement sync to Chat service

### For Both

1. Align on API contracts (Chat ← Bridge)
2. Define data sync protocols
3. Plan testing with real MSR India event data
4. Document deployment architecture
5. Prepare for Phase 2 expansion (Project Green, Cambridge)

---

## Files Created

| Project | File | Purpose |
| --- | --- | --- |
| chat | `COPILOT_INSTRUCTIONS_UPDATED.md` | Updated instructions with Event Hub context |
| bridge | `COPILOT_INSTRUCTIONS_MSR_EVENT_HUB.md` | Bridge-specific instructions |

---

## Usage

Replace or supplement existing `copilot-instructions.md` files with these updated versions. Both documents:

- Reference Microsoft 365 Agents Toolkit correctly
- Provide data model context
- Guide Copilot tool usage (get_schema, get_code_snippets, get_knowledge, troubleshoot)
- Document architecture patterns
- Include development workflow guidance

---

## Questions for Stakeholders

1. Should these replace the existing copilot-instructions.md files?
2. Should we add additional guidance for specific MSR India event requirements?
3. Are there constraints on Office 365 integration we should highlight?
4. Should we document the exact Foundry models/capabilities being used?
5. What's the timeline for Bridge service implementation?
