"""
Intent Classification Metrics and Logging for Quality Tracking

Integrates with Application Insights for long-term tracking and dashboards.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from collections import defaultdict, Counter

# Import existing telemetry infrastructure
from src.observability.telemetry import track_event


class IntentMetrics:
    """Track intent classification quality metrics and log to Application Insights."""
    
    def __init__(self):
        # Keep minimal in-memory state for real-time API queries
        self.recent_classifications = []  # Last 100 classifications
        self.max_recent = 100
        
    def log_classification(
        self,
        query: str,
        predicted_intent: str,
        confidence: float,
        patterns_matched: List[str],
        execution_path: str,  # "deterministic", "llm_assisted", "full_llm"
        latency_ms: float = 0
    ):
        """Log intent classification to Application Insights."""
        
        # Track to Application Insights
        track_event(
            "intent_classification",
            properties={
                "query_preview": query[:100],  # Truncated for privacy
                "predicted_intent": predicted_intent,
                "execution_path": execution_path,
                "patterns_matched_count": str(len(patterns_matched)),
                "patterns": ",".join(patterns_matched[:5]),  # First 5 patterns
                "is_deterministic": str(execution_path == "deterministic"),
                "is_low_confidence": str(confidence < 0.6),
            },
            measurements={
                "confidence": confidence,
                "latency_ms": latency_ms,
            }
        )
        
        # Keep recent in memory for quick API queries
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query[:100],
            "intent": predicted_intent,
            "confidence": confidence,
            "execution_path": execution_path,
        }
        self.recent_classifications.append(record)
        
        # Keep only last N records in memory
        if len(self.recent_classifications) > self.max_recent:
            self.recent_classifications.pop(0)
            
    def log_user_feedback(
        self,
        query: str,
        feedback: str,  # "positive", "negative", "correction"
        correction: Optional[str] = None
    ):
        """Log user feedback on routing quality to Application Insights."""
        
        track_event(
            "intent_feedback",
            properties={
                "query_preview": query[:100],
                "feedback_type": feedback,
                "has_correction": str(correction is not None),
                "corrected_intent": correction or "",
            }
        )
        
    def get_coverage_stats(self) -> Dict[str, Any]:
        """Get recent coverage statistics from in-memory data."""
        if not self.recent_classifications:
            return {
                "total_queries": 0,
                "deterministic_coverage": 0.0,
                "low_confidence_rate": 0.0,
                "message": "No recent data. Query Application Insights for historical metrics."
            }
        
        total = len(self.recent_classifications)
        deterministic = sum(1 for c in self.recent_classifications if c["execution_path"] == "deterministic")
        low_conf = sum(1 for c in self.recent_classifications if c["confidence"] < 0.6)
        
        # Intent distribution from recent data
        intent_counts = Counter(c["intent"] for c in self.recent_classifications)
        
        return {
            "total_queries_recent": total,
            "deterministic_coverage": deterministic / total if total > 0 else 0,
            "low_confidence_rate": low_conf / total if total > 0 else 0,
            "top_intents_recent": intent_counts.most_common(5),
            "note": f"Based on last {total} classifications. For full metrics, query Application Insights."
        }
    
    def get_intent_accuracy(self) -> Dict[str, str]:
        """Intent accuracy is tracked in Application Insights."""
        return {
            "message": "Intent accuracy metrics are in Application Insights.",
            "query": "customEvents | where name == 'intent_feedback' | summarize positive=countif(customDimensions.feedback_type=='positive'), negative=countif(customDimensions.feedback_type=='negative') by tostring(customDimensions.predicted_intent)"
        }
    
    def get_pattern_effectiveness(self) -> Dict[str, str]:
        """Pattern effectiveness is tracked in Application Insights."""
        return {
            "message": "Pattern effectiveness metrics are in Application Insights.",
            "query": "customEvents | where name == 'intent_classification' | summarize avg(customMeasurements.confidence), count() by tostring(customDimensions.predicted_intent)"
        }
    
    def generate_report(self) -> str:
        """Generate a quality report from recent data."""
        stats = self.get_coverage_stats()
        
        report = f"""
# Intent Classification Quality Report (Recent Data)
Generated: {datetime.utcnow().isoformat()}

## Recent Coverage Statistics ({stats.get('total_queries_recent', 0)} queries)
- Deterministic Coverage: {stats.get('deterministic_coverage', 0):.1%}
- Low Confidence Rate: {stats.get('low_confidence_rate', 0):.1%}

## Top Intents (Recent)
{chr(10).join(f"- {intent}: {count} queries" for intent, count in stats.get('top_intents_recent', []))}

{stats.get('note', '')}

## Application Insights Queries

For comprehensive metrics, use these KQL queries in Application Insights:

### Deterministic Coverage Over Time
```
customEvents
| where name == "intent_classification"
| summarize 
    total=count(),
    deterministic=countif(customDimensions.is_deterministic == "True"),
    low_confidence=countif(customDimensions.is_low_confidence == "True")
    by bin(timestamp, 1h)
| project timestamp, deterministic_pct=deterministic*100.0/total, low_confidence_pct=low_confidence*100.0/total
```

### Intent Distribution
```
customEvents
| where name == "intent_classification"
| summarize count() by tostring(customDimensions.predicted_intent)
| order by count_ desc
```

### User Feedback by Intent
```
customEvents
| where name == "intent_feedback"
| summarize 
    positive=countif(customDimensions.feedback_type=="positive"),
    negative=countif(customDimensions.feedback_type=="negative"),
    corrections=countif(customDimensions.feedback_type=="correction")
    by tostring(customDimensions.predicted_intent)
```
        """
        
        return report
