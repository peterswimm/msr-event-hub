# Deterministic Intents with Examples

## 1️⃣ Event Overview
**Purpose:** Display event summary, dates, location, metadata

### Button Event Example
```json
{
  "type": "Action.OpenUrl",
  "title": "Event Details",
  "url": "action://event_overview"
}
```

### Typed Intent Example
```
User: "What is this event?"
Router: "event_overview" (confidence: 0.82)

OR

User: "When is the conference?"
Router: "event_overview" (confidence: 0.78)
```

---

## 2️⃣ Hourly Agenda
**Purpose:** Show hourly session schedule for today

### Button Event Example
```tsx
<MenuItem onClick={() => handleItemClick("hourly_agenda")}>
  Today's Schedule
</MenuItem>
```

**Payload:**
```json
{
  "action": "hourly_agenda",
  "timezone": "PT",
  "max_items": 8
}
```

### Typed Intent Example
```
User: "What sessions are happening today?"
Router: "Not directly matched - falls back to LLM

Better match:
User: "Show me the agenda"
Router: Still LLM (agenda patterns not in deterministic set)

Note: This is typically triggered via button, not typed queries
```

---

## 3️⃣ Presenter Carousel
**Purpose:** Display key presenters/speakers carousel

### Button Event Example
```json
{
  "type": "Action.Execute",
  "title": "See Featured Speakers",
  "verb": "presenter_carousel"
}
```

**Payload:**
```json
{
  "action": "presenter_carousel",
  "max_presenters": 6
}
```

### Typed Intent Example
```
User: "Who are the presenters?"
Router: Falls back to LLM (not in deterministic set)

Better option:
User: (Click "See Featured Speakers" button)
Router: Triggers "presenter_carousel" action directly
```

---

## 4️⃣ Keyword Search
**Purpose:** Full-text search on project names and descriptions

### Button Event Example
```json
{
  "type": "Action.Execute",
  "title": "Search by Topic",
  "verb": "keyword_search",
  "verb_params": {
    "keyword": "${searchInput}"
  }
}
```

**Test Payload:**
```json
{
  "action": "keyword_search",
  "keyword": "learning"
}
```

### Typed Intent Example
```
User: "Find projects about machine learning"
Router: "project_search" (deterministic)
→ Triggers KeywordSearchHandler with keyword="machine learning"

OR

User: "Show me AI projects"
Router: "project_search" (deterministic)
```

---

## 5️⃣ Project Detail
**Purpose:** Retrieve detailed metadata for specific project

### Button Event Example
```tsx
<button onClick={() => {
  dispatch({
    type: "view_project",
    projectId: "proj-neural-ai-2025"
  })
}}>
  View Details
</button>
```

**Payload:**
```json
{
  "action": "view_project",
  "projectId": "proj-1"
}
```

### Typed Intent Example
```
User: "Tell me about the AI Research Assistant project"
Router: "project_detail" (confidence: 0.88)

OR

User: "Details for 'Deep Learning Framework'"
Router: "project_detail" (confidence: 0.85)
```

---

## 6️⃣ People Lookup
**Purpose:** Find people by name in event index

### Button Event Example
```json
{
  "type": "Action.Execute",
  "title": "Browse by Presenter",
  "verb": "researcher_search",
  "verb_params": {
    "researcher": "${presenterName}"
  }
}
```

**Payload:**
```json
{
  "action": "researcher_search",
  "researcher": "Alice"
}
```

### Typed Intent Example
```
User: "Show me projects by Alice Johnson"
Router: "people_lookup" (confidence: 0.90)

OR

User: "What is Bob Chen presenting?"
Router: "people_lookup" (confidence: 0.87)

OR

User: "Jane Smith's poster"
Router: "people_lookup" (confidence: 0.82)
```

---

## 7️⃣ Category Browse
**Purpose:** List research areas and topics

### Button Event Example
```json
{
  "type": "Action.Submit",
  "title": "Browse by Category",
  "data": {
    "action": "category_select",
    "category": "AI"
  }
}
```

**Payload:**
```json
{
  "action": "category_select",
  "category": "AI"
}
```

### Typed Intent Example
```
User: "Which projects are in HCI?"
Router: "category_browse" (confidence: 0.85)

OR

User: "Show me all AI category projects"
Router: "category_browse" (confidence: 0.88)

OR

User: "List projects in the Systems track"
Router: "category_browse" (confidence: 0.81)
```

---

## 8️⃣ Logistics: Equipment
**Purpose:** Show equipment needs, displays, monitors required

### Button Event Example
```json
{
  "type": "Action.Execute",
  "title": "Check Equipment Requirements",
  "verb": "logistics_equipment"
}
```

### Typed Intent Example
```
User: "Which booths need a large display?"
Router: "logistics_equipment" (confidence: 0.92)

OR

User: "Show me projects requiring 2 monitors"
Router: "logistics_equipment" (confidence: 0.89)

OR

User: "What equipment does booth 42 need?"
Router: "logistics_equipment" (confidence: 0.86)
```

---

## 9️⃣ Logistics: Format
**Purpose:** Display recording format, video codec, presentation format info

### Button Event Example
```json
{
  "type": "Action.Execute",
  "title": "Recording Format",
  "verb": "logistics_format"
}
```

### Typed Intent Example
```
User: "What recording format is needed?"
Router: "logistics_format" (confidence: 0.90)

OR

User: "What video codec should we use?"
Router: "logistics_format" (confidence: 0.88)

OR

User: "What are the special demo requirements?"
Router: "logistics_format" (confidence: 0.85)
```

---

## 🔟 Recording Status
**Purpose:** Show recording submission status and link

### Button Event Example
```json
{
  "type": "Action.Execute",
  "title": "Recording Status",
  "verb": "recording_status"
}
```

### Typed Intent Example
```
User: "Has the recording been submitted?"
Router: "recording_status" (confidence: 0.89)

OR

User: "Is the video edited?"
Router: "recording_status" (confidence: 0.87)

OR

User: "Where's the recording link?"
Router: "recording_status" (confidence: 0.86)
```

---

## 1️⃣1️⃣ Session Lookup
**Purpose:** Find sessions by speaker, time, or keyword

### Button Event Example
```json
{
  "type": "Action.Execute",
  "title": "Browse Sessions",
  "verb": "session_lookup",
  "verb_params": {
    "speaker": "${speakerName}"
  }
}
```

### Typed Intent Example
```
User: "Show me sessions about AI"
Router: "session_lookup" (confidence: 0.86)

OR

User: "What talks are at 2pm?"
Router: "session_lookup" (confidence: 0.84)

OR

User: "Find keynote sessions"
Router: "session_lookup" (confidence: 0.88)

OR

User: "Who is speaking tomorrow?"
Router: "session_lookup" (confidence: 0.82)
```

---

## 1️⃣2️⃣ Bookmark
**Purpose:** Save items for later (MVP stub - event tracking only)

### Button Event Example
```tsx
<button onClick={() => {
  track_event("bookmark_action", {
    entity_type: "project",
    entity_id: projectId,
    action: "add"
  })
}}>
  ⭐ Save Project
</button>
```

**Payload:**
```json
{
  "action": "bookmark",
  "type": "project",
  "projectId": "proj-123"
}
```

### Typed Intent Example
```
User: "Save this project"
Router: Falls back to LLM (no typed pattern for bookmark)

Better: Use button UI
User: (Clicks ⭐ Save Project button)
Router: Triggers bookmark_action directly
```

---

## 📊 Intent Classification Summary

| Intent | Min Confidence | Typical Typed Pattern | Typical Button | Routes AI |
|--------|---------------|-----------------------|-----------------|-----------|
| event_overview | 0.50 | "What is the event?" | "Event Details" | ✗ No |
| hourly_agenda | N/A | (button triggered) | "Today's Schedule" | ✗ No |
| presenter_carousel | N/A | (button triggered) | "Featured Speakers" | ✗ No |
| keyword_search | 0.60 | "Show me AI projects" | "Search Topic" | ✗ No |
| project_detail | 0.50 | "Details on Project X" | "View Details" | ✗ No |
| people_lookup | 0.60 | "Projects by Alice" | "Browse Presenter" | ✗ No |
| category_browse | 0.50 | "Show HCI projects" | "By Category" | ✗ No |
| logistics_equipment | 0.50 | "Need 2 monitors?" | "Equipment" | ✗ No |
| logistics_format | 0.50 | "Recording format?" | "Format Info" | ✗ No |
| recording_status | 0.50 | "Recording link?" | "Recording Status" | ✗ No |
| session_lookup | 0.50 | "Sessions on AI?" | "Browse Sessions" | ✗ No |
| bookmark | N/A | (button triggered) | "⭐ Save" | ✗ No |

---

## 🔑 Key Patterns

**Typed Intent Triggers:**
- Direct mentions: "Show me", "Find", "Tell me about", "What", "Which"
- Entity references: Project names, people names, categories
- Question markers: "?", "What", "When", "Where"
- Comparatives: "Projects by", "Sessions about", "Details for"

**Button Triggers:**
- Menu items: Hamburger menu navigation
- Action buttons: From Adaptive Cards
- Form submissions: Search/filter inputs
- Direct calls: onClick handlers dispatching actions

**Confidence Thresholds:**
- ≥ 0.75 = **Deterministic routing** (no LLM needed)
- 0.50–0.75 = **Hybrid** (can route to LLM for assistance)
- < 0.50 = **LLM only** (fallback to Azure OpenAI)
