# Application Insights Routing Quality Dashboard

## Overview

All intent routing metrics are tracked in Application Insights via custom events:
- `intent_classification` - Every query classification with confidence and execution path
- `intent_feedback` - User thumbs up/down and corrections

## Key Metrics Dashboard

### 1. Deterministic Coverage (Target: >85%)

**Query:**
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(24h)
| summarize 
    total=count(),
    deterministic=countif(customDimensions.is_deterministic == "True"),
    low_confidence=countif(customDimensions.is_low_confidence == "True")
    by bin(timestamp, 1h)
| project 
    timestamp, 
    deterministic_pct=deterministic*100.0/total, 
    low_confidence_pct=low_confidence*100.0/total,
    total
| order by timestamp desc
```

**Visualization:** Line chart with:
- Y-axis: Percentage (0-100%)
- Lines: deterministic_pct (target: >85%), low_confidence_pct (target: <15%)

---

### 2. Intent Distribution

**Query:**
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(7d)
| summarize count() by tostring(customDimensions.predicted_intent)
| order by count_ desc
| project intent=customDimensions_predicted_intent, queries=count_
```

**Visualization:** Pie chart or bar chart

---

### 3. Average Confidence by Intent

**Query:**
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(7d)
| summarize 
    avg_confidence=avg(customMeasurements.confidence),
    query_count=count()
    by tostring(customDimensions.predicted_intent)
| order by avg_confidence asc
| project 
    intent=customDimensions_predicted_intent, 
    avg_confidence, 
    query_count
```

**Visualization:** Bar chart
**Alert:** avg_confidence < 0.70 for any intent with >10 queries

---

### 4. User Feedback Sentiment

**Query:**
```kusto
customEvents
| where name == "intent_feedback"
| where timestamp > ago(7d)
| summarize 
    positive=countif(customDimensions.feedback_type=="positive"),
    negative=countif(customDimensions.feedback_type=="negative"),
    corrections=countif(customDimensions.feedback_type=="correction"),
    total=count()
| project 
    satisfaction_pct=positive*100.0/total,
    correction_rate=corrections*100.0/total,
    positive,
    negative,
    corrections
```

**Visualization:** KPI tiles
**Target:** satisfaction_pct >80%, correction_rate <10%

---

### 5. Routing Quality Over Time (Hourly)

**Query:**
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(24h)
| summarize 
    avg(customMeasurements.confidence),
    percentile(customMeasurements.confidence, 50),
    percentile(customMeasurements.confidence, 95),
    count()
    by bin(timestamp, 1h)
| order by timestamp desc
```

**Visualization:** Line chart with confidence percentiles

---

### 6. Low Confidence Queries (Needs Attention)

**Query:**
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(24h)
| where customDimensions.is_low_confidence == "True"
| project 
    timestamp,
    query=customDimensions.query_preview,
    intent=customDimensions.predicted_intent,
    confidence=customMeasurements.confidence,
    execution_path=customDimensions.execution_path
| order by timestamp desc
| take 50
```

**Visualization:** Table
**Action:** Review these queries to identify missing patterns

---

### 7. User Corrections (Training Data)

**Query:**
```kusto
customEvents
| where name == "intent_feedback"
| where customDimensions.feedback_type == "correction"
| where timestamp > ago(7d)
| project 
    timestamp,
    query=customDimensions.query_preview,
    corrected_to=customDimensions.corrected_intent
| order by timestamp desc
```

**Visualization:** Table
**Action:** Use corrections to improve patterns weekly

---

### 8. Execution Path Distribution

**Query:**
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(7d)
| summarize count() by tostring(customDimensions.execution_path)
| project 
    path=customDimensions_execution_path, 
    count_,
    percentage=count_*100.0/toscalar(customEvents | where name == "intent_classification" and timestamp > ago(7d) | count)
```

**Visualization:** Donut chart
**Target:** deterministic >85%, llm_assisted <10%, full_llm <10%

---

### 9. Routing Latency

**Query:**
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(24h)
| summarize 
    avg(customMeasurements.latency_ms),
    percentile(customMeasurements.latency_ms, 50),
    percentile(customMeasurements.latency_ms, 95),
    percentile(customMeasurements.latency_ms, 99)
    by bin(timestamp, 1h), tostring(customDimensions.execution_path)
| order by timestamp desc
```

**Visualization:** Line chart by execution path
**Target:** P95 <50ms for deterministic routing

---

### 10. Pattern Match Effectiveness

**Query:**
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(7d)
| extend patterns_count=toint(customDimensions.patterns_matched_count)
| summarize 
    avg_patterns=avg(patterns_count),
    avg_confidence=avg(customMeasurements.confidence)
    by tostring(customDimensions.predicted_intent)
| order by avg_confidence asc
```

**Visualization:** Scatter plot (X=avg_patterns, Y=avg_confidence)
**Insight:** Intents with high pattern matches but low confidence need pattern quality improvement

---

## Alerts to Configure

### 1. Low Deterministic Coverage
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(1h)
| summarize 
    deterministic_pct=countif(customDimensions.is_deterministic == "True")*100.0/count()
| where deterministic_pct < 70
```
**Threshold:** <70% over 1 hour
**Action:** Check for new query patterns or pattern degradation

---

### 2. High Low-Confidence Rate
```kusto
customEvents
| where name == "intent_classification"
| where timestamp > ago(1h)
| summarize 
    low_conf_pct=countif(customDimensions.is_low_confidence == "True")*100.0/count()
| where low_conf_pct > 20
```
**Threshold:** >20% over 1 hour
**Action:** Review recent queries and add missing patterns

---

### 3. Negative Feedback Spike
```kusto
customEvents
| where name == "intent_feedback"
| where timestamp > ago(1h)
| where customDimensions.feedback_type == "negative"
| summarize count()
| where count_ > 10
```
**Threshold:** >10 negative feedbacks in 1 hour
**Action:** Check for recent pattern changes or service issues

---

## Weekly Review Process

### Monday: Review Weekend Data
```kusto
customEvents
| where name == "intent_classification"
| where timestamp between(startofweek(now(-2d)) .. endofweek(now(-2d)))
| summarize 
    queries=count(),
    deterministic_pct=countif(customDimensions.is_deterministic == "True")*100.0/count(),
    low_conf_pct=countif(customDimensions.is_low_confidence == "True")*100.0/count(),
    top_intents=make_list(customDimensions.predicted_intent, 10)
```

### Export Corrections for Pattern Updates
```kusto
customEvents
| where name == "intent_feedback"
| where customDimensions.feedback_type == "correction"
| where timestamp > ago(7d)
| project 
    timestamp,
    query=customDimensions.query_preview,
    corrected_intent=customDimensions.corrected_intent
| order by timestamp desc
```

### Identify Low-Performing Intents
```kusto
let feedback = customEvents
| where name == "intent_feedback"
| where timestamp > ago(7d)
| extend intent=tostring(customDimensions.predicted_intent)
| summarize 
    positive=countif(customDimensions.feedback_type=="positive"),
    negative=countif(customDimensions.feedback_type=="negative")
    by intent;
customEvents
| where name == "intent_classification"
| where timestamp > ago(7d)
| summarize queries=count() by tostring(customDimensions.predicted_intent)
| join kind=leftouter (feedback) on $left.customDimensions_predicted_intent == $right.intent
| extend accuracy=positive*100.0/(positive+negative)
| where accuracy < 70 and (positive+negative) > 5
| project intent=customDimensions_predicted_intent, queries, accuracy, positive, negative
| order by accuracy asc
```

---

## PowerBI Dashboard Template

**Recommended Tiles:**
1. **KPI - Deterministic Coverage** (85% target)
2. **KPI - User Satisfaction** (>80% target)
3. **Line Chart - Coverage Over Time** (24h)
4. **Bar Chart - Intent Distribution** (7d)
5. **Table - Recent Low Confidence Queries** (live)
6. **Scatter Plot - Confidence vs Pattern Matches** (7d)
7. **Donut Chart - Execution Path Distribution** (7d)
8. **Line Chart - Routing Latency P95** (24h)

**Refresh:** Every 5 minutes for real-time monitoring

---

## Quick Health Check

Run this single query for instant health assessment:

```kusto
let time_window = ago(1h);
let classifications = customEvents
    | where name == "intent_classification" and timestamp > time_window;
let feedback = customEvents
    | where name == "intent_feedback" and timestamp > time_window;
print 
    total_queries=toscalar(classifications | count),
    deterministic_pct=toscalar(classifications | summarize countif(customDimensions.is_deterministic == "True")*100.0/count()),
    low_conf_pct=toscalar(classifications | summarize countif(customDimensions.is_low_confidence == "True")*100.0/count()),
    avg_confidence=toscalar(classifications | summarize avg(customMeasurements.confidence)),
    positive_feedback=toscalar(feedback | summarize countif(customDimensions.feedback_type=="positive")),
    negative_feedback=toscalar(feedback | summarize countif(customDimensions.feedback_type=="negative")),
    status=iff(
        toscalar(classifications | summarize countif(customDimensions.is_deterministic == "True")*100.0/count()) > 80,
        "✅ HEALTHY",
        "⚠️ NEEDS ATTENTION"
    )
```

---

## Next Steps

1. **Create Workbook** in Azure Portal > Application Insights > Workbooks
2. **Add Queries** from sections above as tiles
3. **Configure Alerts** for thresholds
4. **Schedule Weekly Review** meeting with team
5. **Export to PowerBI** for executive dashboards
