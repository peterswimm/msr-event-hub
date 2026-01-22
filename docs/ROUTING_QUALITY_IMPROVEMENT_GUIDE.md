# Routing Quality Improvement Guide

## Executive Summary

Your deterministic router currently handles **70-80% of queries** with regex patterns. This guide provides actionable recommendations to:
- **Increase deterministic coverage to 85-90%**
- **Track routing quality with real-time metrics**
- **Implement continuous improvement feedback loops**
- **Add 10 new high-value intents**

---

## 1. Integration: Wire Up Intent Metrics

### Step 1: Update chat_routes.py

Add tracking to your existing `/api/chat` endpoint:

```python
# In src/api/chat_routes.py
from src.observability.intent_metrics import IntentMetrics

# Initialize at module level (singleton)
intent_metrics = IntentMetrics()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    start_time = datetime.now()
    query = request.message
    
    # Step 1: Try deterministic routing
    intent, confidence = deterministic_router.classify(query)
    patterns_matched = deterministic_router.extract_entities(query)
    
    # Determine execution path
    if confidence >= 0.8:
        execution_path = "deterministic"
        response = await handle_deterministic_intent(intent, query)
    elif confidence >= 0.6:
        execution_path = "llm_assisted"
        response = await handle_llm_assisted(intent, query, confidence)
    else:
        execution_path = "full_llm"
        response = await handle_full_llm(query)
    
    # Calculate latency
    latency_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    # Log classification with all details
    intent_metrics.log_classification(
        query=query,
        predicted_intent=intent,
        confidence=confidence,
        patterns_matched=patterns_matched,
        execution_path=execution_path,
        latency_ms=latency_ms
    )
    
    return response
```

### Step 2: Add Feedback Endpoint

Create a new endpoint for users to correct misclassifications:

```python
# In src/api/chat_routes.py

@router.post("/chat/feedback")
async def feedback_endpoint(request: FeedbackRequest):
    """
    User feedback on chat responses.
    
    Request body:
    {
        "query": "original user query",
        "feedback": "positive" | "negative" | "correction",
        "correction": "correct_intent_name"  # optional, for corrections
    }
    """
    intent_metrics.log_user_feedback(
        query=request.query,
        feedback=request.feedback,
        correction=request.correction
    )
    
    return {"status": "feedback_recorded"}
```

### Step 3: Add Metrics Dashboard Endpoint

```python
# In src/api/chat_routes.py

@router.get("/metrics/routing-quality")
async def routing_quality_metrics():
    """
    Get real-time routing quality metrics.
    Returns JSON with coverage stats, intent distribution, and pattern effectiveness.
    """
    coverage = intent_metrics.get_coverage_stats()
    accuracy = intent_metrics.get_intent_accuracy()
    patterns = intent_metrics.get_pattern_effectiveness()
    
    return {
        "coverage": coverage,
        "accuracy_by_intent": accuracy,
        "pattern_effectiveness": patterns,
        "report": intent_metrics.generate_report()
    }
```

### Step 4: Add UI Feedback Buttons

Update your chat UI to collect feedback:

```typescript
// In web/chat/src/components/ChatMessage.tsx

interface ChatMessageProps {
  message: string;
  isUser: boolean;
  query: string; // Original user query
}

export function ChatMessage({ message, isUser, query }: ChatMessageProps) {
  const [feedbackGiven, setFeedbackGiven] = useState(false);
  
  const handleFeedback = async (feedback: 'positive' | 'negative') => {
    await fetch('/api/chat/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, feedback })
    });
    setFeedbackGiven(true);
  };
  
  return (
    <div className={`message ${isUser ? 'user' : 'assistant'}`}>
      <div className="message-content">{message}</div>
      
      {!isUser && !feedbackGiven && (
        <div className="feedback-buttons">
          <button 
            onClick={() => handleFeedback('positive')}
            aria-label="This response was helpful"
          >
            👍
          </button>
          <button 
            onClick={() => handleFeedback('negative')}
            aria-label="This response was not helpful"
          >
            👎
          </button>
        </div>
      )}
    </div>
  );
}
```

---

## 2. Add 10 New High-Value Intents

### Priority 1: Time-Based Schedule (HIGH)

**Why:** Real-time schedule queries are the #1 use case at events.

**Add to router_prompt.py:**

```python
INTENT_PATTERNS = {
    # ... existing intents ...
    
    "time_based_schedule": [
        r"\b(what'?s|what\s+is)\s+(happening|on)\s+(now|next|today|tomorrow)\b",
        r"\bcurrent\s+(session|presentation|talk)\b",
        r"\bup\s+next\b",
        r"\bcoming\s+up\b",
        r"\bthis\s+(morning|afternoon|hour)\b",
        r"\bschedule\s+for\s+(today|tomorrow)\b",
        r"\bat\s+\d{1,2}:\d{2}\b"  # "What's at 2:30?"
    ],
}
```

**Handler implementation:**

```python
# In src/api/intent_handlers.py

async def handle_time_based_schedule(query: str, entities: dict) -> dict:
    """
    Handle queries about what's happening now/next/at specific time.
    """
    current_time = datetime.now()
    
    # Extract time references
    if re.search(r"\bnow\b", query, re.IGNORECASE):
        events = await get_events_at_time(current_time)
    elif re.search(r"\bnext\b", query, re.IGNORECASE):
        events = await get_next_events(current_time)
    elif time_match := re.search(r"\bat\s+(\d{1,2}):(\d{2})\b", query):
        hour, minute = time_match.groups()
        target_time = current_time.replace(hour=int(hour), minute=int(minute))
        events = await get_events_at_time(target_time)
    else:
        events = await get_today_schedule()
    
    return {
        "response_type": "timeline",
        "events": events,
        "adaptive_card": render_timeline_card(events)
    }
```

### Priority 2: Related Projects (HIGH)

**Why:** Drives engagement by suggesting similar content users might like.

```python
"related_projects": [
    r"\brelated\s+projects?\b",
    r"\bsimilar\s+(to|projects?)\b",
    r"\blike\s+this\s+project\b",
    r"\bmore\s+projects?\s+like\b",
    r"\balso\s+interested\s+in\b",
    r"\bother\s+projects?\s+in\s+this\s+area\b",
],
```

**Handler:**

```python
async def handle_related_projects(query: str, entities: dict) -> dict:
    """
    Find projects similar to a given project or theme.
    """
    # Extract reference project
    if project_name := entities.get('project_name'):
        reference_project = await get_project(project_name)
        similar_projects = await find_similar_projects(
            category=reference_project.category,
            tags=reference_project.tags,
            exclude_id=reference_project.id,
            limit=5
        )
    else:
        # Use current context or user history
        similar_projects = await get_recommended_projects(entities)
    
    return {
        "response_type": "carousel",
        "projects": similar_projects,
        "adaptive_card": render_project_carousel(similar_projects, "Similar Projects")
    }
```

### Priority 3: Personalized Recommendations (HIGH)

```python
"personalized_recommendations": [
    r"\brecommend\b.*\bproject",
    r"\bsuggest\b.*\bproject",
    r"\bwhat\s+should\s+i\s+(see|visit|check\s+out)\b",
    r"\bbased\s+on\s+my\s+interest",
    r"\bi'?m\s+interested\s+in\b",
],
```

### Priority 4-10: See additional_intents.py

Full implementations in [additional_intents.py](./additional_intents.py).

---

## 3. Pattern Optimization Strategies

### Strategy 1: Expand Synonyms

Many misclassifications happen because patterns don't cover all synonyms.

**Example: project_search currently misses these:**

```python
# BEFORE
"project_search": [
    r"\bprojects?\s+(about|related|on)\b",
    r"\bshow\s+me\s+projects?\b",
]

# AFTER (expanded)
"project_search": [
    r"\bprojects?\s+(about|related|on|regarding|concerning|for)\b",
    r"\b(show|display|find|list|get)\s+me\s+projects?\b",
    r"\bsearch\s+(for\s+)?projects?\b",
    r"\blooking\s+for\s+projects?\b",
    r"\bprojects?\s+(in|under|within)\s+\w+\b",  # "projects in AI"
],
```

**Action:** Review low-confidence queries and add missing synonyms.

### Strategy 2: Entity-Aware Patterns

Patterns that extract entities are more robust.

```python
# BEFORE: Simple keyword matching
r"\brecording\b"

# AFTER: Entity-aware
r"\brecording\s+(link|url|status|submitted)\b"
r"\b(where|when)\s+(is|are)\s+the\s+recording\b"
r"\brecording\s+for\s+(?P<project>\w+)\b"  # Named capture group
```

### Strategy 3: Contextual Boosting

Some patterns should have higher weight based on event context.

```python
# In query_router.py DeterministicRouter class

def classify(self, query: str) -> tuple[str, float]:
    """Enhanced classification with contextual boosting."""
    scores = {}
    
    for intent, patterns in self.patterns.items():
        base_score = self._calculate_pattern_score(query, patterns)
        
        # Apply contextual boosting
        if intent == "time_based_schedule" and self._is_during_event():
            base_score *= 1.2  # Boost time queries during event
        elif intent == "recording_status" and self._is_after_event():
            base_score *= 1.3  # Boost recording queries after event
        
        scores[intent] = min(base_score, 0.95)  # Cap at 0.95
    
    # Return best match
    best_intent = max(scores, key=scores.get)
    return best_intent, scores[best_intent]
```

### Strategy 4: Fuzzy Matching for Typos

Use Levenshtein distance for misspelled keywords.

```python
from fuzzywuzzy import fuzz

def fuzzy_pattern_match(query: str, pattern: str, threshold: int = 85) -> bool:
    """Match pattern with fuzzy string matching."""
    keywords = re.findall(r'\w+', pattern)
    for keyword in keywords:
        for word in query.split():
            if fuzz.ratio(word.lower(), keyword.lower()) >= threshold:
                return True
    return False
```

---

## 4. Quality Monitoring Dashboard

### Daily Monitoring (Automated)

Create a scheduled job to check routing health:

```python
# In scripts/daily_routing_report.py

import schedule
import time
from src.observability.intent_metrics import IntentMetrics

def generate_daily_report():
    metrics = IntentMetrics()
    report = metrics.generate_report()
    
    # Check for anomalies
    coverage = metrics.get_coverage_stats()
    if coverage['deterministic_coverage'] < 0.70:
        send_alert("⚠️ Deterministic coverage dropped below 70%!")
    
    if coverage['low_confidence_rate'] > 0.20:
        send_alert("⚠️ Low confidence rate above 20%!")
    
    # Export to monitoring system
    export_to_application_insights(coverage)
    
    # Email report to team
    send_email_report(report)

# Run every day at 9 AM
schedule.every().day.at("09:00").do(generate_daily_report)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Grafana Dashboard (Visualization)

Create a Grafana dashboard with these panels:

1. **Deterministic Coverage %** (target: >80%)
2. **Intent Distribution** (pie chart)
3. **Low Confidence Rate** (target: <15%)
4. **Response Time P50/P95** (latency tracking)
5. **User Feedback Sentiment** (positive vs negative)
6. **Pattern Hit Rate** (which patterns are most effective)

**Sample Application Insights Query:**

```kusto
customMetrics
| where name == "routing_classification"
| extend execution_path = tostring(customDimensions.execution_path)
| summarize 
    deterministic_pct = countif(execution_path == "deterministic") * 100.0 / count(),
    avg_confidence = avg(value),
    low_confidence_pct = countif(value < 0.6) * 100.0 / count()
| project timestamp=now(), deterministic_pct, avg_confidence, low_confidence_pct
```

---

## 5. Continuous Improvement Process

### Weekly Review Cycle

1. **Monday:** Review weekend event data
   - Export corrections: `metrics.export_training_data()`
   - Identify top 10 misclassified queries
   
2. **Tuesday:** Pattern updates
   - Add new regex patterns for common failures
   - Deploy to staging environment
   
3. **Wednesday:** Validation
   - Run test suite with historical queries
   - Measure accuracy improvement
   
4. **Thursday:** Production deployment
   - Deploy updated patterns
   - Monitor metrics for regressions
   
5. **Friday:** Report and planning
   - Generate weekly report
   - Plan next week's improvements

### Regression Testing

Create a test suite with known queries:

```python
# In tests/test_routing_regression.py

import pytest
from src.api.query_router import DeterministicRouter

# Golden dataset of queries -> expected intent
GOLDEN_QUERIES = [
    ("What projects are about AI?", "project_search", 0.85),
    ("Show me sessions at 2:30 PM", "time_based_schedule", 0.90),
    ("Where is the recording link?", "recording_status", 0.88),
    ("What's happening now?", "time_based_schedule", 0.92),
    ("Find projects similar to HoloLens", "related_projects", 0.86),
    # ... add 100+ queries
]

@pytest.mark.parametrize("query,expected_intent,min_confidence", GOLDEN_QUERIES)
def test_routing_regression(query, expected_intent, min_confidence):
    router = DeterministicRouter()
    intent, confidence = router.classify(query)
    
    assert intent == expected_intent, f"Expected {expected_intent}, got {intent}"
    assert confidence >= min_confidence, f"Confidence {confidence} below threshold"
```

---

## 6. Expected Impact

| Metric | Current | Target (3 months) |
|--------|---------|-------------------|
| Deterministic Coverage | 70-80% | **85-90%** |
| Avg Confidence Score | ~0.75 | **0.82** |
| Low Confidence Rate | 20-30% | **<15%** |
| User Satisfaction | Unknown | **>85%** |
| Response Latency P95 | ~500ms | **<400ms** |

---

## 7. Quick Start Checklist

- [ ] Integrate `IntentMetrics` into `chat_routes.py`
- [ ] Add `/chat/feedback` endpoint
- [ ] Add `/metrics/routing-quality` endpoint
- [ ] Add feedback buttons to chat UI
- [ ] Implement top 3 new intents (time_based, related_projects, recommendations)
- [ ] Expand synonyms in existing patterns
- [ ] Set up daily automated report
- [ ] Create Grafana dashboard
- [ ] Build golden query test suite (100+ queries)
- [ ] Schedule weekly review meetings

---

## 8. Resources

- **Intent Metrics Class:** `src/observability/intent_metrics.py`
- **Additional Intents:** `src/api/additional_intents.py`
- **Current Patterns:** `src/api/router_prompt.py`
- **Router Logic:** `src/api/query_router.py`

---

**Next Steps:** Start with the "Quick Start Checklist" above. Prioritize adding the top 3 new intents first, then integrate metrics tracking.
