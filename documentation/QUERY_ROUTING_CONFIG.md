# Query Routing Configuration Guide

## Overview

The Event Hub includes a deterministic query router that handles 70-80% of queries via pattern matching, bypassing the LLM for common lookups. This system is **fully feature-flagged** and can be disabled or tuned via environment variables.

---

## Feature Flags

### `ENABLE_DETERMINISTIC_ROUTING`

**Default:** `true`

Enable or disable deterministic routing entirely.

- `true` – Use pattern-based routing for high-confidence queries
- `false` – Send all queries directly to LLM (baseline mode)

**Use case:** Disable to A/B test full LLM performance vs. hybrid approach.

```bash
ENABLE_DETERMINISTIC_ROUTING=false
```

---

### `ROUTING_STRATEGY`

**Default:** `deterministic_first`

Choose routing strategy:

- `deterministic_first` – Try deterministic routing first; fallback to LLM if confidence is low
- `llm_only` – Always use LLM (ignores deterministic patterns)
- `deterministic_only` – Only use deterministic routing; return error if confidence is low
- `hybrid` – Smart blend: deterministic for high confidence, LLM assist for medium, full LLM for low

**Use case:** Switch between strategies to measure performance, cost, and user satisfaction.

```bash
# Production recommendation
ROUTING_STRATEGY=deterministic_first

# Baseline for comparison
ROUTING_STRATEGY=llm_only

# Development/debugging
ROUTING_STRATEGY=deterministic_only
```

---

### Confidence Thresholds

#### `DETERMINISTIC_CONFIDENCE_THRESHOLD`

**Default:** `0.8`

Minimum confidence score (0.0 to 1.0) required to use deterministic routing.

**Use case:** Lower threshold to route more queries deterministically; raise to be more conservative.

```bash
# More aggressive (route 80%+ of queries)
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.7

# More conservative (route only 60-70%)
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.85
```

#### `LLM_ASSIST_CONFIDENCE_THRESHOLD`

**Default:** `0.6`

Minimum confidence for LLM-assisted mode (where deterministic results are passed as context to LLM for synthesis).

```bash
LLM_ASSIST_CONFIDENCE_THRESHOLD=0.6
```

---

### Telemetry & Logging

#### `LOG_ROUTING_DECISIONS`

**Default:** `true`

Log each routing decision (intent, confidence, strategy, deterministic flag).

```bash
LOG_ROUTING_DECISIONS=true
```

Example log output:
```
INFO: Routed query: intent=project_search, confidence=0.87, strategy=deterministic_first, deterministic=True, entities={'projectTitleQuery': 'machine learning'}
```

#### `EMIT_ROUTING_METRICS`

**Default:** `true`

Emit metrics for telemetry (Prometheus, Application Insights, etc.).

```bash
EMIT_ROUTING_METRICS=true
```

Metrics emitted:
- `query_router_deterministic_count` – Count of deterministic routes
- `query_router_llm_count` – Count of LLM routes
- `query_router_confidence_avg` – Average confidence score
- `query_router_latency_ms` – Routing latency

---

## A/B Testing

### `ROUTING_AB_TEST_ENABLED`

**Default:** `false`

Enable A/B testing mode where a percentage of users get deterministic routing and others get full LLM.

```bash
ROUTING_AB_TEST_ENABLED=true
AB_TEST_DETERMINISTIC_RATIO=0.5
```

#### `AB_TEST_DETERMINISTIC_RATIO`

**Default:** `0.5`

Ratio of users who get deterministic routing (0.0 to 1.0).

- `0.5` – 50% deterministic, 50% LLM
- `0.8` – 80% deterministic, 20% LLM
- `0.2` – 20% deterministic, 80% LLM

**Use case:** Run A/B test to measure which approach delivers better results.

---

## Configuration Scenarios

### Scenario 1: Production (Hybrid Mode)

Maximize deterministic routing for speed/cost; fallback to LLM for complex queries.

```bash
ENABLE_DETERMINISTIC_ROUTING=true
ROUTING_STRATEGY=deterministic_first
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.8
LLM_ASSIST_CONFIDENCE_THRESHOLD=0.6
LOG_ROUTING_DECISIONS=true
EMIT_ROUTING_METRICS=true
```

**Expected behavior:**
- 70-80% of queries routed deterministically (< 50ms response)
- 15-20% get LLM assist (deterministic context + LLM synthesis)
- 5-10% get full LLM treatment (streaming chat)

---

### Scenario 2: Baseline (LLM Only)

Disable deterministic routing to measure baseline LLM performance.

```bash
ENABLE_DETERMINISTIC_ROUTING=false
ROUTING_STRATEGY=llm_only
LOG_ROUTING_DECISIONS=true
EMIT_ROUTING_METRICS=true
```

**Expected behavior:**
- 100% of queries go to LLM
- Higher latency (2-5 seconds per query)
- Higher cost (token usage for every query)
- Useful for comparing quality vs. deterministic approach

---

### Scenario 3: A/B Test

Compare deterministic vs. LLM side-by-side.

```bash
ENABLE_DETERMINISTIC_ROUTING=true
ROUTING_STRATEGY=deterministic_first
ROUTING_AB_TEST_ENABLED=true
AB_TEST_DETERMINISTIC_RATIO=0.5
LOG_ROUTING_DECISIONS=true
EMIT_ROUTING_METRICS=true
```

**Expected behavior:**
- 50% of users get deterministic routing
- 50% get full LLM routing
- Track metrics per cohort to measure:
  - Latency
  - Cost (token usage)
  - User satisfaction (thumbs up/down)
  - Task completion rate

---

### Scenario 4: Debug Mode

Only use deterministic routing; fail fast if confidence is low.

```bash
ENABLE_DETERMINISTIC_ROUTING=true
ROUTING_STRATEGY=deterministic_only
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.7
LOG_ROUTING_DECISIONS=true
```

**Expected behavior:**
- All queries must match a pattern
- Low-confidence queries return error or "unsupported query" message
- Useful for validating pattern coverage during development

---

## Monitoring Routing Performance

### Key Metrics to Track

1. **Routing Rate**
   - % of queries routed deterministically
   - Target: 70-80%

2. **Latency**
   - Deterministic: < 50ms
   - LLM assist: 500-1000ms
   - Full LLM: 2-5 seconds

3. **Cost**
   - Deterministic: ~$0.0001 per query (DB lookup)
   - LLM: ~$0.01-0.05 per query (token usage)

4. **User Satisfaction**
   - Thumbs up/down feedback per response
   - Task completion rate

5. **Confidence Distribution**
   - Histogram of confidence scores
   - Adjust thresholds based on distribution

### Recommended Alerts

- **Low deterministic rate** (< 60%): Patterns may need tuning
- **High LLM fallback rate** (> 40%): Consider adding more patterns
- **Low average confidence** (< 0.5): Intent classifier needs improvement

---

## Disabling the Router (Full LLM Rollback)

If deterministic routing performs poorly, disable it instantly:

```bash
# Option 1: Disable via env var (no code changes)
ENABLE_DETERMINISTIC_ROUTING=false

# Option 2: Switch to LLM-only strategy
ROUTING_STRATEGY=llm_only
```

Restart the backend service; all queries will go directly to LLM streaming endpoint.

---

## Best Practices

1. **Start with hybrid mode** (`deterministic_first`) in production
2. **Log all routing decisions** during initial rollout
3. **Monitor confidence distribution** and adjust thresholds
4. **Run A/B test** for 2-4 weeks to gather statistically significant data
5. **Keep LLM baseline** as fallback; never break the user experience
6. **Iterate on patterns** based on low-confidence queries in logs

---

## Examples

### Query: "Which projects are in HCI?"

```json
{
  "intent": "category_browse",
  "confidence": 0.95,
  "deterministic": true,
  "route": "GET /v1/events/{eventId}/projects?category=HCI",
  "latency_ms": 35
}
---

## Local Development with Mock Data

For local development without running the full Event Hub backend, use the mock data source:

### Configuration

```bash
# .env
EVENT_DATA_SOURCE=mock
MOCK_DATA_PATH=data/mock_event_data.json
```

### Mock Data Structure

The mock data file (`data/mock_event_data.json`) contains:
- **event**: Main event information (name, dates, location)
- **projects**: Array of 5 sample projects across different research areas
- **sessions**: Array of 4 sample sessions (keynote, workshop, panel, demo)
- **people**: Array of 8 researchers with their roles and research areas
- **categories**: List of research area categories

### Sample Projects

The mock data includes diverse project examples:
1. **Neural Code Intelligence** (AI) - prototype, large display, recording allowed
2. **Quantum Error Correction** (Quantum) - early research, recording restricted
3. **Sustainable Cloud Infrastructure** (Systems) - production, recording allowed
4. **Privacy-Preserving ML** (Security) - prototype, recording not allowed
5. **Accessibility in AR/VR** (HCI) - prototype, VR headsets, recording allowed

### Query Examples with Mock Data

```bash
# These queries will work with mock data:

# Project search
"Show me AI projects"
→ Returns Neural Code Intelligence project

# Equipment queries
"Which projects need large displays?"
→ Returns Neural Code Intelligence and Sustainable Cloud projects

# Recording permissions
"Which projects don't allow recording?"
→ Returns Privacy-Preserving ML project

# People lookup
"Who is Dr. Sarah Chen?"
→ Returns researcher info with Neural Code Intelligence project

# Category browse
"What quantum computing projects do we have?"
→ Returns Quantum Error Correction project
```

### Benefits of Mock Data

- **No Backend Required**: Develop frontend and routing logic without Event Hub API
- **Fast Iteration**: Query responses are instant (no API latency)
- **Offline Development**: Work without network connectivity
- **Consistent Testing**: Deterministic data for testing and demos
- **Easy Customization**: Edit JSON file to add/modify test scenarios

### Switching Between Sources

```bash
# Local development
EVENT_DATA_SOURCE=mock

# Integration testing with live APIs
EVENT_DATA_SOURCE=api

# No code changes needed - just toggle the flag
```

### Extending Mock Data

To add more test scenarios, edit `data/mock_event_data.json`:

```json
{
   "projects": [
      {
         "id": "proj-006",
         "name": "Your New Project",
         "researchArea": "Machine Learning",
         "equipment": ["Demo Laptop"],
         "recordingPermission": "allowed",
         ...
      }
   ]
}
```

The mock data follows the exact schema defined in `documentation/EVENT_SCHEMA.md`.

```

### Query: "Show me projects about machine learning"

```json
{
  "intent": "project_search",
  "confidence": 0.85,
  "deterministic": true,
  "route": "GET /v1/events/{eventId}/projects?keywords=machine+learning",
  "latency_ms": 42
}
```

### Query: "Explain the relationship between these two papers"

```json
{
  "intent": "project_search",
  "confidence": 0.45,
  "deterministic": false,
  "route": "LLM streaming with RAG context",
  "latency_ms": 3200
}
```

---

## Support

For questions about routing configuration:
- Review routing logs: `uvicorn main:app --log-level debug`
- Check metrics dashboard for routing distribution
- Adjust thresholds incrementally (0.05-0.1 changes)
- Report issues with example queries that route incorrectly
