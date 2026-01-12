# Query Routing Configuration Guide

This guide explains how to configure and tune query routing for the MSR Event Hub chat service. The system implements intelligent routing that handles 70-80% of queries without LLM calls, while delegating complex cases to Azure AI Foundry for multi-agent orchestration.

## Overview

Query routing has three decision points:

1. **Deterministic Classification** (80% of queries)
   - Pattern matching against known intent types
   - Entity extraction (names, categories, dates)
   - Direct database/Neo4j lookup
   - Cost: ~$0, Latency: <100ms
   - No LLM call needed

2. **Foundry Agent Delegation** (15-20% of queries)
   - Low-confidence queries escalated to Azure AI Foundry
   - Multi-agent reasoning with tool orchestration
   - Cost: Azure OpenAI token usage + Foundry overhead
   - Latency: 1-5s (reasoning + tool calls)

3. **Azure OpenAI Fallback** (5-10% of queries)
   - Edge cases, conversational queries
   - Direct streaming from Azure OpenAI
   - Cost: Azure OpenAI token usage
   - Latency: 2-8s

## Feature Flags & Configuration

### Deterministic Routing

```bash
# Enable/disable deterministic routing completely
ENABLE_DETERMINISTIC_ROUTING=true

# Routing strategy (mutually exclusive)
ROUTING_STRATEGY=deterministic_first  # Try deterministic, fallback to LLM (default)
                 # llm_only            # Always use LLM (baseline for A/B testing)
                 # deterministic_only  # Only deterministic, error on low confidence
                 # hybrid              # Confidence-based tiering

# Confidence thresholds (0.0-1.0)
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.8        # Use deterministic if >= this
LLM_ASSIST_CONFIDENCE_THRESHOLD=0.6           # Use LLM assist if in 0.6-0.8 range
```

### Foundry SaaS Orchestration

```bash
# Enable delegation to Foundry for complex queries
DELEGATE_TO_FOUNDRY=false              # Set to true to enable

# Foundry configuration (required if DELEGATE_TO_FOUNDRY=true)
FOUNDRY_ENDPOINT=https://...           # Azure Foundry resource endpoint
FOUNDRY_AGENT_ID=msr-event-orchestrator  # Primary orchestrator agent ID
FOUNDRY_API_VERSION=2025-11-15-preview   # API version

# Confidence threshold for Foundry delegation
FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD=0.8  # Delegate if < this
```

### A/B Testing

```bash
# Enable A/B testing to compare routing strategies
ROUTING_AB_TEST_ENABLED=false

# Ratio of traffic going through deterministic path (0.0-1.0)
AB_TEST_DETERMINISTIC_RATIO=0.5        # 50% deterministic, 50% LLM
```

### Observability

```bash
# Log routing decisions for debugging
LOG_ROUTING_DECISIONS=true

# Emit Prometheus metrics for monitoring
EMIT_ROUTING_METRICS=true
```

### Data Source

```bash
# Use live Event Hub APIs or mock data
EVENT_DATA_SOURCE=api                  # 'api' or 'mock'
MOCK_DATA_PATH=data/mock_event_data.json  # Only used if EVENT_DATA_SOURCE=mock
```

## Routing Strategies

### 1. Deterministic First (RECOMMENDED for production)

```
Query Confidence
    ↓
    ├─ >= 0.8 (high)   → Use deterministic routing (fast, cheap)
    ├─ 0.6-0.8 (medium) → Use deterministic + LLM assist
    └─ < 0.6 (low)     → Use full Azure OpenAI
```

**Configuration:**
```bash
ENABLE_DETERMINISTIC_ROUTING=true
ROUTING_STRATEGY=deterministic_first
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.8
LLM_ASSIST_CONFIDENCE_THRESHOLD=0.6
```

**Result:** 70-80% queries skip AOAI entirely, costs reduced by ~70%

### 2. LLM Only (for baselines/testing)

```
All queries → Azure OpenAI streaming
```

**Configuration:**
```bash
ROUTING_STRATEGY=llm_only
```

**Use case:** Compare against deterministic baseline, measure accuracy delta

### 3. Deterministic Only (for validation)

```
Query Confidence
    ↓
    ├─ >= 0.8 → Use deterministic routing
    └─ < 0.8  → Error (no fallback)
```

**Configuration:**
```bash
ROUTING_STRATEGY=deterministic_only
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.8
```

**Use case:** Test deterministic coverage, identify gaps

### 4. Hybrid with Foundry (for complex tasks)

```
Query Confidence
    ↓
    ├─ >= 0.8          → Deterministic (local execution)
    ├─ 0.6-0.8         → LLM Assist (with deterministic context)
    └─ < 0.8 & Foundry → Delegate to Foundry Agents (multi-agent reasoning)
    └─ < 0.8 & No Foundry → Azure OpenAI
```

**Configuration:**
```bash
ENABLE_DETERMINISTIC_ROUTING=true
ROUTING_STRATEGY=hybrid
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.8
LLM_ASSIST_CONFIDENCE_THRESHOLD=0.6
DELEGATE_TO_FOUNDRY=true
FOUNDRY_ENDPOINT=https://...
FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD=0.8
```

## Deployment Scenarios

### Scenario 1: Development (Local, no backend)

```bash
# Use mock data to avoid backend dependencies
EVENT_DATA_SOURCE=mock
MOCK_DATA_PATH=data/mock_event_data.json

# Disable expensive features
ENABLE_DETERMINISTIC_ROUTING=true
DELEGATE_TO_FOUNDRY=false
```

**Cost:** $0, Latency: <100ms

### Scenario 2: Production Baseline (deterministic only)

```bash
# Pure deterministic routing with OpenAI fallback
ENABLE_DETERMINISTIC_ROUTING=true
ROUTING_STRATEGY=deterministic_first
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.8
EVENT_DATA_SOURCE=api

# Disable Foundry initially
DELEGATE_TO_FOUNDRY=false
```

**Cost:** ~70% cheaper than pure AOAI, Latency: <500ms avg

### Scenario 3: Production with Foundry

```bash
# Deterministic first, delegate complex queries to Foundry
ENABLE_DETERMINISTIC_ROUTING=true
ROUTING_STRATEGY=deterministic_first
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.8
EVENT_DATA_SOURCE=api

# Enable Foundry for 20-30% of queries
DELEGATE_TO_FOUNDRY=true
FOUNDRY_ENDPOINT=https://your-resource.cognitiveservices.azure.com
FOUNDRY_AGENT_ID=msr-event-orchestrator
FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD=0.8
```

**Cost:** 70% cheaper for simple queries, SaaS pricing for complex ones
**Benefit:** Multi-agent orchestration without self-hosting

### Scenario 4: A/B Testing (measure routing effectiveness)

```bash
# Test deterministic vs LLM on same traffic
ROUTING_AB_TEST_ENABLED=true
AB_TEST_DETERMINISTIC_RATIO=0.5      # 50% each path

# Use feature flags to enable/disable components
ENABLE_DETERMINISTIC_ROUTING=true
ROUTING_STRATEGY=deterministic_first
DELEGATE_TO_FOUNDRY=true             # Optional: test Foundry too
```

**Metrics to collect:**
- Latency: avg response time
- Cost: tokens used
- Accuracy: user satisfaction, error rate
- Coverage: % handled by deterministic path

## Intent Classification

The deterministic router recognizes 13 intent types:

| Intent | Pattern Examples | Tools Used |
|--------|------------------|-----------|
| **event_overview** | "Tell me about MSR", "event summary" | Event metadata |
| **session_lookup** | "Find session about AI", "when is keynote?" | Session search |
| **project_search** | "AI projects", "show me quantum computing" | Project database |
| **project_detail** | "Details on Neural Code Intelligence" | Project metadata |
| **people_lookup** | "Who is Dr. Sarah Chen?", "find team members" | People index |
| **category_browse** | "What research areas?", "list topics" | Category enum |
| **logistics_format** | "Recording format?", "what video codec?" | Project artifacts |
| **logistics_equipment** | "What equipment needed?", "displays required?" | Equipment list |
| **logistics_placement** | "Where is the demo?", "booth location?" | Placement map |
| **recording_status** | "Can I record?", "recording allowed?" | Recording permissions |
| **comms_status** | "Communications approved?", "media rights?" | Comms status |
| **target_audience** | "Who should attend?", "technical level?" | Audience metadata |
| **admin_audit** | "Show me all events", "audit log" | Admin data |

**Confidence scoring:**
- Pattern match + entity presence: 0.8-1.0
- Partial match + context: 0.6-0.8
- Ambiguous or conversational: <0.6

## Monitoring & Tuning

### Check Routing Status

```bash
# Verify current configuration
curl http://localhost:8000/api/chat/config

# Response:
{
  "routing": {
    "deterministic_enabled": true,
    "deterministic_threshold": 0.8,
    "foundry_delegation_enabled": true,
    "foundry_delegation_threshold": 0.8,
    "foundry_configured": true
  }
}
```

### View Routing Decisions

Enable logging to see routing decisions:

```bash
# In .env
LOG_ROUTING_DECISIONS=true

# In application logs, look for:
# Intent classified: intent=project_search, confidence=0.92, is_deterministic=true
# Delegating to Foundry: confidence=0.45, threshold=0.8
```

### Metrics

**Available in Prometheus:**
- `routing_decisions_total{intent_type, route_type}` - Routing distribution
- `routing_latency_ms{route_type}` - Latency per route (deterministic vs AOAI)
- `routing_confidence_avg{intent_type}` - Average confidence by intent

### A/B Test Analysis

Compare two strategies over 7 days:

```
Deterministic Path (50% of traffic):
  - Avg latency: 95ms
  - Cost: $15
  - Accuracy: 94%

LLM Path (50% of traffic):
  - Avg latency: 3,200ms
  - Cost: $250
  - Accuracy: 96%
```

**Decision:** Deterministic is 16x faster and 17x cheaper with only 2% accuracy loss.
**Action:** Increase deterministic_first ratio to 80%.

### Tuning Thresholds

Start conservative, measure, adjust:

```bash
# Conservative (more LLM calls, higher quality, higher cost)
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.9
FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD=0.85

# Aggressive (more deterministic, lower cost, possible accuracy loss)
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.7
FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD=0.7

# Balanced (default, good for most cases)
DETERMINISTIC_CONFIDENCE_THRESHOLD=0.8
FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD=0.8
```

**Measure before/after:**
1. Change threshold
2. Collect metrics for 24-48 hours
3. Compare latency, cost, accuracy
4. Keep or revert

## Example Queries & Expected Routes

### Query: "Show me AI projects"

```json
{
  "intent": "project_search",
  "confidence": 0.95,
  "deterministic": true,
  "route": "Database lookup → Neo4j search",
  "latency_ms": 42
}
```

### Query: "What's the project about privacy?"

```json
{
  "intent": "project_search",
  "confidence": 0.78,
  "deterministic": false,
  "route": "LLM with RAG context + deterministic results",
  "latency_ms": 1200
}
```

### Query: "Explain the relationship between these two papers"

```json
{
  "intent": "project_search",
  "confidence": 0.45,
  "deterministic": false,
  "route": "Foundry multi-agent reasoning (if enabled) or LLM streaming",
  "latency_ms": 3200
}
```

---

## Support

For questions about routing configuration:
- Review routing logs: `LOG_ROUTING_DECISIONS=true` in .env
- Check config endpoint: `GET /api/chat/config`
- Adjust thresholds incrementally (0.05-0.1 changes)
- Test changes with A/B testing before rolling out
- Report misclassified queries to improve patterns
