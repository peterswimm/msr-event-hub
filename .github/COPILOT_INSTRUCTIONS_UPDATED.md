# MSR Event Agent Chat & Bridge - Copilot Instructions

## Project Context: MSR Event Hub Platform

This project is part of the **MSR Event Hub Platform** - a scalable internal platform that augments MSR events with digital experiences for organizers, presenters, and attendees. The Event Hub extends research event impact across time and geography by providing centralized discovery, collaboration, and follow-up capabilities.

### Project Scope
- **msr-event-agent-chat**: AI chat/copilot experience for attendees to explore event content, discover research, and get personalized recommendations
- **msr-event-agent-bridge**: Backend integration layer connecting the Event Hub platform with AI agents, knowledge bases, and content enrichment services

### Key Design Constraints
- **Access Control**: Restricted to users with @microsoft.com credentials; external users cannot sign in
- **Data Integration**: Office 365 data is NOT accessible unless explicit admin consent + Copilot integration is enabled
- **Multi-tenancy**: Platform supports multiple events and programs (MSR India, Project Green, RRS, Cambridge, etc.)
- **Phases**: MVP (MSR India - late Jan), Project Green (March), Cambridge (April), MSR Concierge (June)

---

## Core Data Models

### Research Project
```
├─ Code repos
├─ Papers  
├─ Research talks/sessions
└─ Related links
```

### Poster (Event Context)
```
Core Identity:
  ├─ Title (string)
  ├─ Abstract (text)
  ├─ Poster asset (PDF/image URL)
  └─ Thumbnail image

Event Context:
  ├─ Location (room, booth, floor)
  ├─ Theme/track (enum)
  └─ Related event

People & Contact:
  ├─ Team (array of Person)
  └─ Contact (primary contact)

Related Assets:
  ├─ Videos (array of URLs)
  ├─ Slide decks (array of URLs)
  ├─ Code repos (array of URLs)
  ├─ Research papers (array of URLs)
  └─ Other links (array of URLs)

Poster Knowledge (AI-enriched):
  ├─ How poster is organized (text)
  ├─ What's new here (text)
  ├─ What evidence supports ideas (text)
  ├─ What could come next (text)
  └─ Maturity signal (exploratory|validated|pilot-ready)
```

### Session (Talks/Workshops/Keynotes)
```
Core Identity:
  ├─ Session title (string)
  ├─ Session abstract (text)
  ├─ Session type (talk|keynote|workshop|panel|lightning)
  └─ Recording URL (if available)

Event Context:
  ├─ Event name (string)
  ├─ Date & time (string)
  ├─ Duration (string)
  ├─ Location (string)
  └─ Related theme/track (enum)

People & Roles:
  ├─ Speakers (array of Person)
  ├─ Moderator/chair (Person)
  └─ Contact (primary follow-up)

Related Assets:
  ├─ Slide decks (array of URLs)
  ├─ Related posters (array of IDs/URLs)
  ├─ Related papers (array of URLs)
  ├─ Code repos (array of URLs)
  └─ Other related links (array of URLs)

Session Knowledge (AI-enriched):
  ├─ How session is structured (text)
  ├─ What's new or emphasized (text)
  ├─ What evidence/examples are used (text)
  ├─ Key questions discussed (text)
  ├─ What could come next (text)
  └─ Maturity signal (exploratory|validated|pilot-ready)
```

---

## AI/Chat Integration Patterns

### Attendee Chat Experience (msr-event-agent-chat)
The chat agent helps attendees discover and explore research by:

1. **Pre-Event**: Help plan visit, preview content, generate personalized guide
2. **During-Event**: Answer questions about projects/sessions, provide recommendations, help navigate
3. **Post-Event**: Summarize research, suggest follow-up content, enable cross-event discovery

### Key Chat Actions & Handlers
- **Browse**: browse_all, show_featured, recent_projects
- **Filter**: By status, team size, audience, location, equipment, recording, research area
- **Search**: Keyword search (local), researcher search (with Foundry delegation)
- **Navigate**: View project, back to results, find similar, category select
- **AI Features**:
  - Project agent: Synthesize structured summaries + FAQ (Heilmeier catechism)
  - Recommendations: Personalized project/session suggestions
  - Cross-event discovery: Explore related research across events

### Declarative Agent Pattern
All chat actions use the **Microsoft 365 Agents Toolkit** declarative pattern:
- Handlers registered via `@register_action` decorator
- Compatible with both Teams and Office Copilot
- Supports `@requires_foundry` for reasoning-heavy tasks (e.g., researcher search, recommendations)

---

## Architecture Patterns

### Action Registry Pattern (msr-event-agent-chat)
- **ActionRegistry**: Singleton dispatcher routing action_type → handler
- **BaseActionHandler**: ABC for all 15+ chat handlers
- **@register_action**: Declarative registration with metadata
- **@requires_foundry**: Mark handlers delegating to Foundry agents

### Unified Streaming Response
- SSE (Server-Sent Events) for real-time chat updates
- Async generators eliminate boilerplate across handlers
- Error middleware provides unified exception handling
- Adaptive Cards for rich UI responses

### Session-Level Caching (msr-event-agent-chat)
- In-memory cache with configurable TTL (default 3600s)
- Can be disabled per-session for real-time queries
- Reduces data loads for stateless event content

### Content Enrichment Pipeline (msr-event-agent-bridge)
- Ingest project/session data from Excel, PDFs, links
- AI-assisted enrichment of abstracts, summaries, and knowledge fields
- Link crawling and asset discovery
- Output normalized data for multi-event platform

---

## Copilot Integration Instructions

### For Manifest Files (Teams/M365 Agents Toolkit)
When creating or modifying `manifest.json` or `m365agents.yml`:
1. Determine schema version from the manifest file
2. Invoke `get_schema` tool with appropriate schema type
3. Ensure handlers are declared with correct action references
4. Validate Foundry delegation markers for complex reasoning actions

### For Chat Action Handlers
When generating or modifying handler code:
1. Invoke `get_code_snippets` tool with the action name or handler type
2. Ensure handlers inherit from `BaseActionHandler`
3. Implement `execute(payload, context)` returning `(text, card)` tuple
4. Use shared helpers to avoid duplication
5. Add `@requires_foundry=True` if delegating to Foundry agents

### For Configuration Files
When working with API specs, config files, or schemas:
1. Invoke `get_code_snippets` with the config file name or API name
2. Reference the data models (Poster, Session, Research Project) defined above
3. Ensure multi-event/multi-tenant structure is supported
4. Validate access control (Microsoft-only, no Office 365 without consent)

### For Architecture Decisions
When planning new features or integration points:
1. Consider which phase the feature belongs to (MVP, Project Green, Cambridge, Concierge)
2. Evaluate whether Foundry delegation is appropriate
3. Determine if content enrichment is needed (bridge responsibility)
4. Check if new data model fields are required
5. Ensure backward compatibility with existing events

### For Knowledge & Troubleshooting
- Invoke `get_knowledge` tool for questions about:
  - Building apps/agents for Microsoft 365 or Microsoft 365 Copilot
  - AI-assisted content enrichment patterns
  - Multi-event/multi-tenant architecture
  - Declarative agent manifest design
  - Foundry delegation patterns

- Invoke `troubleshoot` tool for issues with:
  - Teams/M365 Agents Toolkit integration
  - Foundry agent delegation failures
  - Content enrichment pipeline issues
  - Manifest validation or registration

---

## Internal Reference: Naming & Terminology

### Microsoft 365 Agents Toolkit (formerly Teams Toolkit)
| New name | Former name | Context |
|----------|------------|---------|
| Microsoft 365 Agents Toolkit | Teams Toolkit | Product name |
| App Manifest | Teams app manifest | Describes app capabilities |
| Microsoft 365 Agents Playground | Test Tool | Test environment |
| `m365agents.yml` | `teamsapp.yml` | Project config files |
| `@microsoft/m365agentstoolkit-cli` (command `atk`) | `@microsoft/teamsapp-cli` (command `teamsapp`) | CLI tool |

**Guidance**: Use new names by default; explain rebranding only if it helps user understanding.

### MSR Event Hub Terminology
- **Event Hub**: Entire platform hosting multiple events
- **Event Site**: Dedicated site for specific event (e.g., "MSR India Event Site")
- **Program**: Series of events (e.g., "MSR Lecture Series")
- **Poster Session**: Event experience format featuring research posters
- **Poster Knowledge**: AI-enriched fields describing poster structure, novelty, evidence, next steps

### Project Roles
- **Organizers**: Event planners and administrators
- **Presenters**: Research teams submitting projects/sessions
- **Attendees**: Researchers and product leaders exploring content

---

## Project Phases & Scope

### MVP (MSR India - Late January)
**Scope**: Establish scalable baseline for MSR India TAB
- Event homepage promoting multiple events
- MSR India event site (home, about, agenda)
- Multi-day schedules with tracks/themes
- Poster hub and detail pages
- Session detail pages with asset links
- Baseline admin experience
- **Stretch**: Basic chat/copilot, project agent summaries, bookmarking

### Phase 2: Project Green (March)
**Scope**: Expand to workshops and lecture series
- Project Green workshops
- Whiteboard Wednesdays lecture series
- Research papers integration
- Scale to multi-event architecture

### Phase 3: Cambridge (April)
**Scope**: Add Cambridge Summerfest, migrate RRS
- Program owner reporting
- Presenter self-service edits
- Access restrictions (page/section level)
- AI summaries for content review

### Phase 4: MSR Concierge (June)
**Scope**: Cross-event knowledge and recommendations
- Project and profile editing
- Comprehensive content enrichment (papers, YouTube, repos)
- Visitor recommendations
- AI Concierge for knowledge exploration

---

## Development Guidelines

### When Adding Chat Actions
1. Create handler inheriting `BaseActionHandler`
2. Add Pydantic schema for validation
3. Use shared helpers to reduce code
4. Implement `execute()` and optional `update_context()`
5. Mark with `@register_action` decorator
6. Add comprehensive tests

### When Enriching Content
1. Use content enrichment pipeline in bridge
2. Apply AI-assisted summarization to abstracts
3. Extract and normalize metadata
4. Link crawling for related assets
5. Produce normalized Poster/Session/Project data

### When Extending for New Event Types
1. Ensure multi-tenant data model supports format
2. Add event-specific admin features
3. Reuse existing components (auth, caching, etc.)
4. Test with full event workflow (pre/during/post)

### When Integrating with Foundry
1. Mark handlers with `@requires_foundry=True`
2. Provide clear intent/context for Foundry agents
3. Implement fallback behavior if Foundry unavailable
4. Cache Foundry results to reduce latency
5. Log reasoning for observability

---

## Key References

- **Architecture**: [UNIFIED_ACTIONS_IMPLEMENTATION.md](../../UNIFIED_ACTIONS_IMPLEMENTATION.md)
- **Integration**: [INTEGRATION_GUIDE.md](../../INTEGRATION_GUIDE.md)
- **Quick Reference**: [QUICK_REFERENCE.md](../../QUICK_REFERENCE.md)
- **Data Models**: Appendix B of MSR Event Hub spec
- **Roadmap**: Appendix C of MSR Event Hub spec

---

## Summary of Copilot Best Practices

When working on **msr-event-agent-chat** or **msr-event-agent-bridge**:

✅ **DO**:
- Use `get_schema` tool for manifest changes
- Use `get_code_snippets` for handler/config implementations
- Use `get_knowledge` for architecture and integration questions
- Use `troubleshoot` tool for Teams/Foundry issues
- Reference data models and phases for context
- Apply decorator-based registration patterns
- Test handlers in isolation before integration

❌ **DON'T**:
- Hardcode action routing (use ActionRegistry instead)
- Duplicate filter/streaming logic (use shared helpers)
- Assume Office 365 data is available
- Build single-event-specific features
- Skip Pydantic validation for chat payloads
- Forget about multi-tenant/multi-event requirements
- Modify manifests without schema validation
