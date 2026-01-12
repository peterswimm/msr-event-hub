# MSR Event Hub - Platform Overview

**Last Updated**: January 5, 2026  
**Status**: Production-Ready (Phase E Complete)

---

## Background

### Overview

MSR internal events and lecture series are one of the most effective ways research teams share work, build community, and spark new ideas. But the value of these moments is often constrained by time, geography, and fragmented content. The **MSR Event Hub** is a scalable internal platform that augments MSR events with a digital experience that helps **organizers** run programs smoothly, helps **presenters** publish and refine supporting assets, and helps **attendees** discover and follow up on research—before, during, and long after the event concludes.

### Problem

Today, event content is typically distributed across ad hoc sites, documents, and links, and the "best" knowledge exchange happens only for those who attend in the moment. This creates friction for organizers, increases effort for presenters to publish consistent assets, and leaves attendees with limited ways to capture and revisit what they learned. As a result, high-quality research artifacts created for events often have limited reach and short-lived impact.

By extending the reach of these events across space and time, we increase the durability, discoverability, and impact of MSR research beyond the moment of the event.

---

## Goals & Outcomes

### For the Organization

- Provide a single, central platform for MSR internal events and lecture series, with event-specific sites and reusable platform capabilities
- Create a pathway to integrate event assets into a shared knowledge base that can be explored across events and distributed more broadly as appropriate

### For Organizers

- Reduce friction for organizers (setup, planning, content validation, communications, reporting)

### For Presenters

- Help presenters/research teams submit, refine, and publish high-quality digital assets that represent their work

### For Attendees

- Give attendees a better discovery and follow-up experience (search/browse, bookmarking via QR, personalized guide, revisiting content)
- Extend in-person and virtual events by making the content and experiences available digitally to the broad MSR community
- Create a pathway to integrate event assets into a shared knowledge base that can be explored across events and distributed more broadly as appropriate

---

## Scope & Approach

The platform supports before / during / after event workflows for three primary audiences: program organizers, presenters (research teams), and attendees (researchers and product leaders). The system will evolve from reliable event publishing and administration into richer discovery experiences including AI-assisted ingestion, structured project summaries, and cross-event exploration.

### MVP Focus

The near-term delivery focus is an MVP that meets the needs of MSR India while establishing a scalable baseline platform (improving on the initial RRS proof-of-concept infrastructure). The MVP includes:

- An MSR Events homepage that can promote multiple events (v1 may link to external event sites where needed)
- An MSR India event site with core pages (home, about/logistics, agenda) and support for multi-day schedules, tracks/themes, and session detail pages with links to assets (decks, papers, repos)
- Poster/project experiences (as scoped for the event): poster hub, tiles, and a project detail page with structured fields and related links
- A baseline admin experience functionally equivalent to RRS

### Secondary MVP Capabilities

As time allows, additional capabilities that enhance the experience:

- Presenter self-service edits
- A basic chat/copilot experience
- Project "agent" synthesis for structured summaries/FAQ
- Bookmarking

---

## Feature Areas

### MSR Event Hub

Digital experience that can scale to host multiple event/program sections + provide a central experience to explore cross-event content.

### Event Hub Sections

Section dedicated to a specific event that supports core formats:

- **Poster sessions**: Project hub pages with tiles, detail pages, bookmarking via QR codes
- **Talks + tracks**: Multi-day agendas with sessions, speakers, and asset links
- **Workshops**: Collaborative event formats with structured agendas
- **Lecture series**: Ongoing programs (e.g., Whiteboard Wednesdays, AI & Society Fellows)

### Admin Experiences

- **The entire hub**: Home page programming, creating new events/programs, permissions, etc.
- **Individual events/programs**: Event-specific content management
- **Individual sessions/presentations**: Session detail editing and asset uploads

### AI Tools

Support ingestion, knowledge augmentation and reduce friction for event admins and participants:

- AI-assisted content extraction from papers, talks, and repositories
- Project summaries using Heilmeier catechism framework
- FAQ generation from project assets
- Chat/copilot for content exploration

### MSR Knowledge Agent

AI chat + related digital UX that allows visitors to explore research content cross-event by topic, project, etc.

### Personalization/Recommendations

Proactive and reactive recommendations based on attendee interests, bookmarks, and engagement patterns.

---

## Programs & Events Supported

The platform should evolve and adapt to support any and all MSR events and programs. Initial focus includes:

- **Redmond Research Showcase** (RRS)
- **MSR India TAB**
- **Project Green**
- **Cambridge Research Showcase**
- **MSR East**: TBD
- **MSR Asia TAB** (pending future discussions)
- **Lecture series**: Whiteboard Wednesdays, AI & Society Fellows, Leaders @ Microsoft

---

## Core Entities

### Research Project / Poster

| Section | Field | Type | What this tells you |
|---------|-------|------|---------------------|
| **Core identity** | Title | String | What the research is about at a glance |
| | Abstract | Text | A concise explanation of the problem, approach, and outcome |
| | Poster | File / URL | The authoritative visual representation of the work |
| | Image | Image / URL | Visual preview for browsing and discovery |
| **Event context** | Location | String | Where to find the poster during the event |
| | Related theme / track | String / Enum | How the poster fits into the event program |
| **People & contact** | Team | Array (Person) | Names, affiliations, optional roles |
| | Contact | Object | Primary contact (email or profile link) |
| **Related links** | Related videos | Array (URL) | Recorded talks, demos, or explainers |
| | Slide deck | Array (URL) | Presentation decks related to the poster |
| | Code repos | Array (URL) | GitHub or internal repo links |
| | Research papers | Array (URL) | Published or preprint papers |
| | Other related links | Array (URL) | Datasets, project sites, blogs, etc. |
| **Poster knowledge** | How the poster is organized | Text | How the authors structured the story |
| | What's new here | Text | Why this work stands out from prior approaches |
| | What evidence supports the ideas | Text | How the insights are grounded or demonstrated |
| | What could come next | Text | Where the work could go and who might care |
| | Maturity signal | Enum | {exploratory, validated, pilot-ready} |

### Session

| Section | Field | Type | What this tells you |
|---------|-------|------|---------------------|
| **Core identity** | Session title | String | What the session is about at a glance |
| | Session abstract | Text | What will be covered and why it matters |
| | Session type | Enum | {talk, keynote, workshop, panel, lightning talk} |
| | Recording | URL | Whether the session can be watched later |
| **Event context** | Event name | String | Programmatic context |
| | Date & time | String | When it occurred |
| | Duration | String | Depth/commitment required |
| | Location | String | Where it took place |
| | Related theme / track | String / Enum | How it fits into the program |
| **People & roles** | Speakers | Array (Person) | Who delivered the session |
| | Moderator / chair | Person | Who guided the session (if applicable) |
| | Contact | Object | Primary follow-up contact |
| **Related assets** | Slide deck | Array (URL) | Supporting material |
| | Related posters | Array (URL / ID) | Connected research artifacts |
| | Related papers | Array (URL) | Formal technical grounding |
| | Code repos | Array (URL) | Runnable or reusable assets |
| | Other related links | Array (URL) | Additional context |
| **Session knowledge** | How the session is structured | Text | How the story unfolds |
| | What's new or emphasized | Text | Key ideas, insights, or perspectives |
| | What evidence or examples are used | Text | How ideas are supported |
| | Key questions discussed | Text | What people were curious about |
| | What could come next | Text | How this might lead to action |
| | Maturity signal | Enum | {exploratory, validated, pilot-ready} |

---

## Platform Roadmap

### MSR India | Late Jan / TBD

**Scope**: MSR India TAB

- MSR Event main hub
- MSRI TAB hub home, agenda, details
- Posters + Sessions
- Bookmarks + QR codes
- Core code base to support multi-event
- AI summary POC for evaluation
- Stretch: MSRI AI chat

### Project Green | March 3

**Scope**: Add Project Green, Whiteboard Wednesdays

- Admin for program owners (WW)
- Lecture series (Whiteboard Weds)
- Workshops (Project Green)
- Research papers POC
- Scale to multi-event
- ResNet feed/integration
- Event level AI chat

### Cambridge Summerfest | April (TBD)

**Scope**: Migrate Redmond + Asia, Add Cambridge

- Program owner reporting
- Edit/upload/review for PG participants
- Push model POC
- AI summary for review/feedback
- Restrict access (page/section level)

### MSR Concierge | June 15

**Scope**: MCR dataset (MSR East?)

- Project, profile editing for researchers
- Project updates
- Add: papers, YouTube Talks, repos
- Recommendations for visitors
- Push model MVP
- MSR AI Concierge
- AI tools for updates – repos, meetings, etc.

---

## MVP Requirements

### Core Features for MVP (Must-haves for MSR India)

#### MSR Events Homepage

- Ability to promote several events, considering scale needed to support list above
- Note: for v1 links will go off to other event sites
- Eventual support for hosting multiple sites

#### MSR India Event Site

**Home page**: Specific layout TBD but modeled after RRS

**About the event page**: Details on the event, logistics, etc.

**Agenda page**: Iteration and expansion of RRS to support a "before" and "after" experience
- Multi-day agendas
- Tracks/themes
- Sessions with data including:
  - Session title, abstract
  - Speaker(s): name, title
  - Date, time, duration, location
  - Links: Decks, related papers, repos, etc.
  - Before: links to Teams call (option) + date, time, location info
  - After: Embed on-demand talk (date still useful, time+location can drop)

**Poster session**:
- Poster hub page with support for themes (optional) as we did for RRS
- Poster tiles, modeled after RRS
- Poster detail page / project page with:
  - Title, abstract
  - Team list: Name, title, image, email
  - Team contact
  - Image (optional), embedded video (optional)
  - Related links to: code repos, PPT decks, research papers, project sites, etc.

**Admin experience**: Functional equivalent to RRS

### Secondary Features (Aspirational P2s)

- Admin for presenters: Based on team list, presenter can edit details about their poster/presentation, upload content, etc.
- Base chat experience: Built-in chat/copilot with "base information" – abstract level to explore research
- Beta "project agent" experience to build Heilmeier catechism overview based on ingested assets + Project knowledge FAQ
- Bookmarking feature from RRS (via QR code and on site)
- Migrate RRS content to new platform

### Out of Scope for MVP (Backlog)

- Program owner admin and reporting experience
- Cross-event search and chat
- Bookmark 2.0 – options for types (further reading, contact me, etc.)
- Cross-event personalization/recommendations
- Support talk series (kind of a never-ending tab)
- Home page with optional themes, upcoming sessions, on-demand sessions, personal push options

---

## KPIs

### MVP KPIs

| KPI Name | Description | Goal | Metric |
|----------|-------------|------|--------|
| Launch on time for MSR India TAB | Event Hub MVP is live, stable, and usable by organizers, presenters, and attendees by the MSR India TAB start date | Successful, on-schedule launch with no blocking issues | Event site live by agreed launch date; no P0/P1 issues at event start |
| Pre-event unique users | Measure early engagement and planning behavior prior to the event | Majority of attendees engage with the site before the event | % of registered or expected attendees who visit the event site before Day 1 |
| Post-event unique users | Measure follow-up and content durability after the event | Sustained engagement beyond the live event | % of promoted audience that visits the site within X days after event (e.g., 7 / 30 days) |
| Extended-reach users (outside event geo / time zone) | Measure reach beyond in-person or live virtual attendees | Demonstrate value beyond physical or live attendance | % of unique users accessing the site from outside the event's primary geo or time zone |
| Connections / leads initiated | Measure whether the site enables meaningful follow-up and collaboration | Event Hub supports real research connections | Count of contact actions initiated via the site (email clicks, contact links, repo visits, etc.) |

### Platform KPIs

| KPI Name | Description | Goal | Metric |
|----------|-------------|------|--------|
| Events onboarded | Number of MSR events or programs using the Event Hub | Broad adoption across MSR | Count of events launched on the platform per quarter |
| Repeat program usage | Whether programs return to the platform for subsequent events | Event Hub becomes the default solution | % of programs that use the platform more than once |
| Organizer self-service rate | Degree to which events can be launched without engineering support | Reduce operational and engineering overhead | % of events launched without bespoke engineering |
| Post-event content usage | Ongoing engagement with event content after events conclude | Increase durability of research content | % of content views occurring 30+ days post-event |
| Cross-event engagement | Evidence that users explore content beyond a single event | Enable broader discovery and knowledge reuse | % of users who view content from multiple events |

---

## Feature Matrix

### Pre-Event

| Organizers | Presenters (Research Teams) | Attendees (Researchers & Product Leaders) |
|------------|----------------------------|------------------------------------------|
| • Import project data from Excel and assign human-readable project IDs and QR codes<br>• Crawl links to enrich project content<br>• Plan project placement (floor, room, booth)<br>• Curate and validate content<br>• Generate "final" project data just prior to event | • Submit initial project data<br>• Upload poster PDF for AI-assisted update suggestions<br>• Review/approve AI-suggested edits<br>• Make changes to core project data as details evolve<br>• Gain insights + anticipate VIP visitor interests based on "custom guide" data | • Preview event content ahead of time to help plan your visit<br>• Express interests or complete a short profile for recommendations<br>• Generate a custom "guide" based on recommendations for your time at the event |

### During Event

| Organizers | Presenters (Research Teams) | Attendees (Researchers & Product Leaders) |
|------------|----------------------------|------------------------------------------|
| • Manage last-minute changes to project placement and content (updates sync in real-time)<br>• Monitor system stability and usage | • Present research with posters and QR codes<br>• See attendee engagement (which projects are bookmarked) | • Browse and search projects by area, title, location<br>• Scan QR codes to bookmark projects for follow-up<br>• Locate projects within the venue (structured fields + PDF map)<br>• Plan routes across selected projects |

### Post-Event

| Organizers | Presenters (Research Teams) | Attendees (Researchers & Product Leaders) |
|------------|----------------------------|------------------------------------------|
| • Generate engagement reports (views, bookmarks, recommendations used)<br>• Archive content for reuse | • Review attendee engagement data<br>• Follow up on bookmarked projects or interested attendees | • Access a personalized list of bookmarked projects<br>• Revisit project details and resources<br>• Share or reference projects after the event |

---

## Technical Implementation

See [ARCHITECTURE.md](ARCHITECTURE.md) for complete technical design and implementation details.

**Current Status**: Phase E Complete - Production-ready platform with:
- PostgreSQL database persistence
- JWT authentication
- Celery + Redis async execution
- Neo4j knowledge graph
- Prometheus monitoring
- Full REST API with Microsoft Graph conventions
