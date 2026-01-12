# Event Hub Schema Reference

Complete schema definitions for all core entities in the MSR Event Hub platform.

---

## Table of Contents

- [Event](#event)
- [Session](#session)
- [Project](#project)
- [Person (Team Member)](#person-team-member)
- [Knowledge Artifact](#knowledge-artifact)
- [Published Knowledge](#published-knowledge)

---

## Event

The top-level container for a research event, lecture series, or program.

### Schema

```typescript
interface Event {
  // Graph metadata (Microsoft Graph conventions)
  "@odata.type": "#microsoft.graph.event";
  "@odata.etag": string;
  id: string;
  
  // Core identity
  displayName: string;
  description?: string;
  eventType: "researchShowcase" | "tab" | "workshop" | "lectureSeries" | "other";
  status: "draft" | "published" | "archived";
  
  // Schedule
  startDate?: string; // ISO 8601 date-time
  endDate?: string;   // ISO 8601 date-time
  timeZone: string;   // IANA time zone (e.g., "America/New_York")
  location?: string;  // Physical or virtual location
  
  // Metadata
  createdAt: string;  // ISO 8601 date-time
  updatedAt: string;  // ISO 8601 date-time
}
```

### Example

```json
{
  "@odata.type": "#microsoft.graph.event",
  "@odata.etag": "W/\"abc123\"",
  "id": "msri-tab-2026",
  "displayName": "MSR India TAB 2026",
  "description": "Annual Technical Advisory Board meeting for MSR India",
  "eventType": "tab",
  "status": "published",
  "startDate": "2026-01-27T09:00:00Z",
  "endDate": "2026-01-28T17:00:00Z",
  "timeZone": "Asia/Kolkata",
  "location": "MSR India, Bangalore",
  "createdAt": "2025-11-01T10:00:00Z",
  "updatedAt": "2026-01-05T14:30:00Z"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `@odata.type` | string | Yes | Entity type identifier (always `#microsoft.graph.event`) |
| `@odata.etag` | string | Yes | Version identifier for optimistic concurrency |
| `id` | string | Yes | Unique identifier (lowercase, kebab-case recommended) |
| `displayName` | string | Yes | Human-readable event name |
| `description` | string | No | Full description of the event |
| `eventType` | enum | Yes | Type of event (see enum values below) |
| `status` | enum | Yes | Lifecycle state (see enum values below) |
| `startDate` | string | No | Event start date/time (ISO 8601) |
| `endDate` | string | No | Event end date/time (ISO 8601) |
| `timeZone` | string | Yes | IANA time zone identifier (default: "UTC") |
| `location` | string | No | Physical venue or virtual platform |
| `createdAt` | string | Yes | Creation timestamp (ISO 8601) |
| `updatedAt` | string | Yes | Last modification timestamp (ISO 8601) |

### Enums

**EventType**
- `researchShowcase` – Research showcase events (e.g., RRS, Cambridge Showcase)
- `tab` – Technical Advisory Board meetings
- `workshop` – Workshop events (e.g., Project Green)
- `lectureSeries` – Ongoing lecture series (e.g., Whiteboard Wednesdays)
- `other` – Other event types

**EventStatus**
- `draft` – Event is being planned, not yet visible to attendees
- `published` – Event is live and visible
- `archived` – Event has concluded and is archived

---

## Session

A session within an event (talk, keynote, workshop, panel, poster session, etc.).

### Schema

```typescript
interface Session {
  // Graph metadata
  "@odata.type": "#microsoft.graph.session";
  "@odata.etag": string;
  id: string;
  
  // Event context
  eventId: string; // Reference to parent Event
  
  // Core identity
  title: string;
  sessionType: "talk" | "keynote" | "workshop" | "panel" | "lightningTalk" | "posterSession" | "other";
  description?: string;
  
  // Schedule
  startDateTime?: string; // ISO 8601 date-time
  endDateTime?: string;   // ISO 8601 date-time
  location?: string;      // Room, stage, or virtual link
  
  // People & roles
  speakers?: Person[];    // Primary presenters
  moderator?: Person;     // Session chair or moderator
  
  // Related assets
  slideDeck?: string[];       // URLs to presentation slides
  recording?: string;         // URL to video recording
  relatedPosters?: string[];  // IDs of related Project entities
  relatedPapers?: string[];   // URLs or DOIs of related papers
  codeRepos?: string[];       // GitHub or internal repo URLs
  otherLinks?: string[];      // Additional resources
  
  // Session knowledge (optional enrichment)
  sessionStructure?: string;    // How the session is organized
  keyInsights?: string;         // What's new or emphasized
  evidenceProvided?: string;    // What evidence or examples are used
  keyQuestions?: string;        // What questions were discussed
  futureDirections?: string;    // What could come next
  maturitySignal?: "exploratory" | "validated" | "pilot-ready";
  
  // Metadata
  createdAt: string;
  updatedAt: string;
}

interface Person {
  name: string;
  email?: string;
  title?: string;        // Job title
  affiliation?: string;  // Organization
  profileUrl?: string;   // LinkedIn, homepage, etc.
  imageUrl?: string;     // Profile photo URL
}
```

### Example

```json
{
  "@odata.type": "#microsoft.graph.session",
  "@odata.etag": "W/\"def456\"",
  "id": "session-ai-agents-keynote",
  "eventId": "msri-tab-2026",
  "title": "The Future of AI Agents in Research",
  "sessionType": "keynote",
  "description": "Exploring how AI agents are transforming research workflows",
  "startDateTime": "2026-01-27T09:30:00Z",
  "endDateTime": "2026-01-27T10:30:00Z",
  "location": "Main Auditorium",
  "speakers": [
    {
      "name": "Dr. Jane Smith",
      "email": "jsmith@microsoft.com",
      "title": "Principal Researcher",
      "affiliation": "Microsoft Research"
    }
  ],
  "slideDeck": ["https://example.com/slides.pdf"],
  "recording": "https://example.com/recording.mp4",
  "keyInsights": "AI agents can reduce research overhead by 40%",
  "maturitySignal": "validated",
  "createdAt": "2025-12-01T10:00:00Z",
  "updatedAt": "2026-01-05T14:30:00Z"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventId` | string | Yes | ID of the parent Event |
| `title` | string | Yes | Session title |
| `sessionType` | enum | Yes | Type of session (see enum values below) |
| `description` | string | No | Session abstract or description |
| `startDateTime` | string | No | Session start time (ISO 8601) |
| `endDateTime` | string | No | Session end time (ISO 8601) |
| `location` | string | No | Physical room, stage, or virtual meeting link |
| `speakers` | Person[] | No | List of presenters |
| `moderator` | Person | No | Session chair or moderator |
| `slideDeck` | string[] | No | URLs to presentation materials |
| `recording` | string | No | URL to video recording |
| `relatedPosters` | string[] | No | IDs of related Project/Poster entities |
| `relatedPapers` | string[] | No | URLs or DOIs of academic papers |
| `codeRepos` | string[] | No | GitHub or code repository URLs |
| `otherLinks` | string[] | No | Additional resources |

### Enums

**SessionType**
- `talk` – Standard research talk
- `keynote` – Keynote presentation
- `workshop` – Interactive workshop
- `panel` – Panel discussion
- `lightningTalk` – Short 5-10 minute talk
- `posterSession` – Poster presentation session
- `other` – Other session types

---

## Project

A research project or poster, typically associated with an event.

### Schema

```typescript
interface Project {
  // Graph metadata
  "@odata.type": "#microsoft.graph.project";
  "@odata.etag": string;
  id: string;
  
  // Event context
  eventId: string; // Reference to parent Event
  
  // Core identity
  name: string;           // Project title
  description: string;    // Abstract or overview
  researchArea: string;   // Research domain (e.g., "AI", "HCI", "Systems")
  
  // Visual assets
  posterUrl?: string;     // PDF of poster
  imageUrl?: string;      // Preview image for browsing
  
  // Event context
  location?: string;      // Booth number, room, floor
  theme?: string;         // Event track or theme
  
  // People & contact
  team: Person[];         // Team members
  contactEmail?: string;  // Primary contact
  
  // Related links
  videos?: string[];      // Demo or explainer videos
  slideDecks?: string[];  // Presentation decks
  papers: PaperReference[];        // Academic papers
  talks: TalkReference[];          // Related talks
  repositories: RepositoryReference[]; // Code repositories
  otherLinks?: string[];  // Datasets, project sites, blogs
  
  // Project knowledge (optional enrichment)
  posterOrganization?: string; // How the poster is organized
  novelty?: string;            // What's new here
  evidence?: string;           // What evidence supports the ideas
  futureWork?: string;         // What could come next
  maturityStage: "exploratory" | "validated" | "deployed";
  
  // Project metadata
  objectives?: string[];  // High-level goals
  keywords?: string[];    // Tags for discovery
  status: string;         // Workflow state (e.g., "created", "reviewed", "published")
  
  // Knowledge artifacts (internal)
  draftArtifacts?: string[];      // IDs of KnowledgeArtifact entities
  publishedKnowledge?: string;    // ID of PublishedKnowledge entity
  
  // Quality metrics (internal)
  qualityMetrics?: {
    totalArtifacts: number;
    artifactsReviewed: number;
    averageConfidence: number;
    averageCoverage: number;
    lastUpdated?: string; // ISO 8601
  };
  
  // Execution config (internal)
  executionConfig?: {
    extractionAgentType: string;
    maxIterations: number;
    qualityThreshold: number;
    parallelization: boolean;
    timeoutSeconds: number;
  };
  
  // Metadata
  createdAt: string;
  updatedAt: string;
}

interface PaperReference {
  id: string;
  title: string;
  authors: string[];
  publicationVenue: string;
  publicationYear: number;
  doiOrUrl: string;
  abstract?: string;
}

interface TalkReference {
  id: string;
  title: string;
  speaker: string;
  eventName: string;
  eventDate: string;  // ISO 8601 date
  videoUrl?: string;
  slidesUrl?: string;
  summary?: string;
}

interface RepositoryReference {
  id: string;
  name: string;
  url: string;
  language: string;
  description?: string;
  stars?: number;
  lastUpdated?: string; // ISO 8601 date
}
```

### Example

```json
{
  "@odata.type": "#microsoft.graph.project",
  "@odata.etag": "W/\"ghi789\"",
  "id": "project-ai-research-assistant",
  "eventId": "msri-tab-2026",
  "name": "AI Research Assistant for Literature Review",
  "description": "An agentic system that helps researchers discover and synthesize relevant papers",
  "researchArea": "Artificial Intelligence",
  "posterUrl": "https://example.com/posters/ai-assistant.pdf",
  "imageUrl": "https://example.com/images/ai-assistant-preview.jpg",
  "location": "Booth 42",
  "theme": "AI Tools",
  "team": [
    {
      "name": "Alice Johnson",
      "email": "alice@microsoft.com",
      "title": "Research Intern",
      "affiliation": "Microsoft Research"
    },
    {
      "name": "Bob Chen",
      "email": "bob@microsoft.com",
      "title": "Principal Researcher",
      "affiliation": "Microsoft Research"
    }
  ],
  "contactEmail": "alice@microsoft.com",
  "papers": [
    {
      "id": "paper-1",
      "title": "Agentic Literature Discovery",
      "authors": ["Johnson, A.", "Chen, B."],
      "publicationVenue": "AAAI 2026",
      "publicationYear": 2026,
      "doiOrUrl": "https://doi.org/10.1000/xyz123"
    }
  ],
  "repositories": [
    {
      "id": "repo-1",
      "name": "ai-research-assistant",
      "url": "https://github.com/microsoft/ai-research-assistant",
      "language": "Python",
      "description": "AI-powered research assistant",
      "stars": 342
    }
  ],
  "keywords": ["AI", "agents", "literature review", "research tools"],
  "maturityStage": "validated",
  "status": "published",
  "createdAt": "2025-11-15T10:00:00Z",
  "updatedAt": "2026-01-05T14:30:00Z"
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventId` | string | Yes | ID of the parent Event |
| `name` | string | Yes | Project title |
| `description` | string | Yes | Abstract or project overview |
| `researchArea` | string | Yes | Research domain or area |
| `posterUrl` | string | No | URL to poster PDF |
| `imageUrl` | string | No | Preview image for browsing/tiles |
| `location` | string | No | Physical location at event (booth, room) |
| `theme` | string | No | Event track or theme |
| `team` | Person[] | Yes | Team members (at least one required) |
| `contactEmail` | string | No | Primary contact for follow-up |
| `papers` | PaperReference[] | No | Related academic papers |
| `talks` | TalkReference[] | No | Related talks or presentations |
| `repositories` | RepositoryReference[] | No | Code repositories |
| `maturityStage` | enum | Yes | Research maturity level |

### Enums

**MaturityStage**
- `exploratory` – Early-stage research
- `validated` – Research validated with evidence
- `deployed` – Research in production use

---

## Person (Team Member)

Represents a person associated with a session or project.

### Schema

```typescript
interface Person {
  name: string;
  email?: string;
  title?: string;        // Job title
  affiliation?: string;  // Organization
  role?: string;         // Role in project (e.g., "Lead", "Contributor")
  profileUrl?: string;   // LinkedIn, homepage, etc.
  imageUrl?: string;     // Profile photo URL
}
```

### Example

```json
{
  "name": "Dr. Jane Smith",
  "email": "jsmith@microsoft.com",
  "title": "Principal Researcher",
  "affiliation": "Microsoft Research",
  "role": "Lead",
  "profileUrl": "https://linkedin.com/in/janesmith",
  "imageUrl": "https://example.com/photos/jsmith.jpg"
}
```

---

## Knowledge Artifact

Draft knowledge extracted from research artifacts (internal entity for AI-assisted workflows).

### Schema

```typescript
interface KnowledgeArtifact {
  // Graph metadata
  "@odata.type": "#microsoft.graph.knowledgeArtifact";
  "@odata.etag": string;
  id: string;
  
  // Context
  projectId: string;
  sourceType: "paper" | "talk" | "repository";
  sourceUrl: string;
  
  // Extracted content
  summary: string;
  keyFindings: string[];
  methodology?: string;
  limitations?: string;
  futureWork?: string;
  
  // Quality metrics
  confidenceScore: number;  // 0.0 to 1.0
  coverageScore: number;    // 0.0 to 1.0
  
  // Workflow
  approvalStatus: "pending" | "approved" | "rejected";
  reviewedBy?: string;
  reviewedAt?: string; // ISO 8601
  
  // Metadata
  createdAt: string;
  updatedAt: string;
}
```

---

## Published Knowledge

Approved, attendee-safe knowledge about a project (public-facing entity).

### Schema

```typescript
interface PublishedKnowledge {
  // Graph metadata
  "@odata.type": "#microsoft.graph.publishedKnowledge";
  "@odata.etag": string;
  id: string;
  
  // Context
  projectId: string;
  
  // Public-facing content
  summary: string;
  keyTakeaways: string[];
  researchHighlights: string;
  practicalApplications?: string;
  futureDirections?: string;
  
  // FAQ (optional)
  faq?: Array<{
    question: string;
    answer: string;
  }>;
  
  // Metadata
  publishedAt: string; // ISO 8601
  publishedBy: string; // User who approved publication
  version: number;
  
  createdAt: string;
  updatedAt: string;
}
```

---

## API Conventions

All entities follow **Microsoft Graph conventions**:

1. **OData annotations**: All entities include `@odata.type` and `@odata.etag`
2. **Field naming**: camelCase in JSON, snake_case in Python
3. **Timestamps**: ISO 8601 format (e.g., `2026-01-05T14:30:00Z`)
4. **IDs**: Lowercase, kebab-case recommended (e.g., `msri-tab-2026`)
5. **Error responses**: Follow Graph error format:
   ```json
   {
     "error": {
       "code": "notFound",
       "message": "Event not found"
     }
   }
   ```

---

## API Endpoints

### Events
- `GET /v1/events` – List all events
- `GET /v1/events/{eventId}` – Get event details
- `POST /v1/events` – Create event
- `PATCH /v1/events/{eventId}` – Update event
- `DELETE /v1/events/{eventId}` – Delete event

### Sessions
- `GET /v1/events/{eventId}/sessions` – List sessions for event
- `GET /v1/events/{eventId}/sessions/{sessionId}` – Get session details
- `POST /v1/events/{eventId}/sessions` – Create session
- `PATCH /v1/events/{eventId}/sessions/{sessionId}` – Update session
- `DELETE /v1/events/{eventId}/sessions/{sessionId}` – Delete session

### Projects
- `GET /v1/events/{eventId}/projects` – List projects for event
- `GET /v1/events/{eventId}/projects/{projectId}` – Get project details
- `POST /v1/events/{eventId}/projects` – Create project
- `PATCH /v1/events/{eventId}/projects/{projectId}` – Update project
- `DELETE /v1/events/{eventId}/projects/{projectId}` – Delete project

### Knowledge
- `GET /v1/events/{eventId}/projects/{projectId}/knowledge/artifacts` – List draft artifacts
- `GET /v1/events/{eventId}/projects/{projectId}/knowledge/published` – Get published knowledge
- `POST /v1/events/{eventId}/projects/{projectId}/knowledge/artifacts` – Create artifact
- `PATCH /v1/events/{eventId}/projects/{projectId}/knowledge/artifacts/{artifactId}/approve` – Approve artifact
- `PUT /v1/events/{eventId}/projects/{projectId}/knowledge/published` – Publish knowledge

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-08 | Initial schema definition |

---

## Support

For schema questions or issues, refer to:
- [MSR_EVENT_HUB_OVERVIEW.md](MSR_EVENT_HUB_OVERVIEW.md) for requirements
- [ARCHITECTURE.md](ARCHITECTURE.md) for technical implementation
- [AZURE_OPENAI_SETUP.md](AZURE_OPENAI_SETUP.md) for AI integration
