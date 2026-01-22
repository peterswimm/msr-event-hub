"""
1DS Telemetry instrumentation for Backend API
Tracks copilot operations, data access, and performance metrics
"""

import os
import time
import re
from typing import Dict, Optional, Any
from functools import wraps
from datetime import datetime

try:
    from applicationinsights import TelemetryClient
    from applicationinsights.requests import WSGIApplication
    HAS_APP_INSIGHTS = True
except ImportError:
    TelemetryClient = None  # type: ignore
    WSGIApplication = None  # type: ignore
    HAS_APP_INSIGHTS = False

# Global telemetry client
_telemetry_client: Optional[Any] = None


_PII_PATTERNS = [
    # Email addresses
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.IGNORECASE),
    # Phone numbers (various formats)
    re.compile(r"\b\+?\d[\d\s().-]{7,}\d\b"),
    # URLs
    re.compile(r"https?://\S+", re.IGNORECASE),
    # Credit card numbers (Visa, MC, Amex, Discover)
    re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    # Social Security Numbers (US format: XXX-XX-XXXX)
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    # IP addresses (IPv4 and IPv6)
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b"),
    # Driver's license numbers (various US states, simplified)
    re.compile(r"\b[A-Z]{1,2}\d{5,8}\b"),
    # Passport numbers (alphanumeric, 6-9 characters)
    re.compile(r"\b[A-Z0-9]{6,9}\b(?=\s*(passport|travel))", re.IGNORECASE),
    # Account numbers (bank, credit)
    re.compile(r"\b(?:account|acct)[\s#:]*\d{4,}\b", re.IGNORECASE),
    # API keys and tokens (long alphanumeric strings)
    re.compile(r"\b[A-Za-z0-9]{32,}\b"),
    # Personal names (enhanced - simple heuristic: Title + Capitalized words)
    re.compile(r"\b(Mr|Ms|Mrs|Dr|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b"),
    # Dates of birth (MM/DD/YYYY, DD-MM-YYYY)
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
    # Medical record numbers
    re.compile(r"\b(?:MRN|medical\s+record)[\s#:]*\d{5,}\b", re.IGNORECASE),
]


def _sanitize_text(value: str, max_length: int = 200) -> str:
    """Enhanced PII scrubbing with multiple pattern detection."""
    if not value:
        return ""

    sanitized = value
    
    # Apply each PII pattern
    for pattern in _PII_PATTERNS:
        sanitized = pattern.sub("[REDACTED]", sanitized)
    
    # Additional context-aware sanitization
    # Redact anything that looks like a key-value pair with sensitive keywords
    sensitive_keywords = [
        "password", "passwd", "pwd", "secret", "token", "api_key", "apikey",
        "auth", "credential", "ssn", "social", "dob", "birthdate", "license"
    ]
    
    for keyword in sensitive_keywords:
        # Match patterns like "password: value" or "password=value"
        pattern = re.compile(rf"\b{keyword}[\s:=]+\S+", re.IGNORECASE)
        sanitized = pattern.sub(f"{keyword}=[REDACTED]", sanitized)

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "…"
    
    return sanitized


def initialize_telemetry(instrumentation_key: Optional[str] = None) -> Optional[Any]:
    """
    Initialize 1DS telemetry client.
    
    Args:
        instrumentation_key: Azure Application Insights key
        
    Returns:
        TelemetryClient instance or None if disabled
    """
    global _telemetry_client
    
    if not HAS_APP_INSIGHTS:
        print("[Telemetry] applicationinsights package not installed. Telemetry disabled.")
        return None
    
    key = instrumentation_key or os.getenv("APPINSIGHTS_INSTRUMENTATION_KEY")
    if not key:
        print("[Telemetry] No instrumentation key provided. Telemetry disabled.")
        return None
    
    _telemetry_client = TelemetryClient(key)
    _telemetry_client.context.application.ver = "0.3.0"
    _telemetry_client.context.properties["environment"] = os.getenv("ENVIRONMENT", "dev")
    
    print("[Telemetry] 1DS initialized successfully")
    return _telemetry_client


def get_telemetry_client() -> Optional[Any]:
    """Get the global telemetry client."""
    return _telemetry_client


def track_event(
    name: str,
    properties: Optional[Dict[str, str]] = None,
    measurements: Optional[Dict[str, float]] = None
) -> None:
    """
    Track a custom event.
    
    Args:
        name: Event name
        properties: String properties
        measurements: Numeric measurements
    """
    if not _telemetry_client:
        return
    
    props = properties or {}
    props["timestamp"] = datetime.utcnow().isoformat()
    
    _telemetry_client.track_event(name, props, measurements)


def track_repository_operation(
    operation: str,
    repository: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    success: bool = True,
    duration_ms: Optional[float] = None,
    error_message: Optional[str] = None
) -> None:
    """
    Track repository data operations.
    
    Args:
        operation: CRUD operation (create, read, update, delete, list)
        repository: Repository name (EventRepository, ProjectRepository, etc.)
        entity_type: Type of entity (event, project, session, artifact)
        entity_id: Optional entity ID
        success: Whether operation succeeded
        duration_ms: Operation duration in milliseconds
        error_message: Error message if failed
    """
    track_event(
        "repository_operation",
        properties={
            "operation": operation,
            "repository": repository,
            "entity_type": entity_type,
            "entity_id": entity_id or "N/A",
            "success": str(success),
            "error_message": error_message or "none"
        },
        measurements={
            "duration_ms": duration_ms or 0
        }
    )


def track_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None
) -> None:
    """
    Track API request metrics.
    
    Args:
        method: HTTP method
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: Optional user identifier
    """
    track_event(
        "api_request",
        properties={
            "method": method,
            "path": path,
            "status_code": str(status_code),
            "success": str(200 <= status_code < 400),
            "user_id": user_id or "anonymous"
        },
        measurements={
            "duration_ms": duration_ms
        }
    )


def track_model_inference(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    success: bool = True,
    error_type: Optional[str] = None
) -> None:
    """
    Track AI model inference metrics.
    
    Args:
        model_name: Name of the model used
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        latency_ms: Inference latency in milliseconds
        success: Whether inference succeeded
        error_type: Type of error if failed
    """
    track_event(
        "model_inference",
        properties={
            "model_name": model_name,
            "success": str(success),
            "error_type": error_type or "none"
        },
        measurements={
            "prompt_tokens": float(prompt_tokens),
            "completion_tokens": float(completion_tokens),
            "total_tokens": float(prompt_tokens + completion_tokens),
            "latency_ms": latency_ms
        }
    )


def track_user_feedback(
    conversation_id: str,
    message_id: str,
    rating: str,
    user_id: Optional[str] = None,
    comment: Optional[str] = None
) -> None:
    """
    Track user satisfaction signals.
    
    Args:
        conversation_id: Conversation identifier
        message_id: Message identifier
        rating: User rating (positive/negative)
        user_id: Optional user identifier
        comment: Optional feedback comment
    """
    track_event(
        "user_feedback",
        properties={
            "conversation_id": conversation_id,
            "message_id": message_id,
            "rating": rating,
            "user_id": user_id or "anonymous",
            "has_comment": str(bool(comment)),
            "comment_sanitized": _sanitize_text(comment or "") if comment else ""
        }
    )


def track_event_visit(
    event_id: str,
    user_id: Optional[str] = None,
    visit_type: str = "general",  # "pre_event" | "post_event" | "during_event" | "general"
    session_duration_seconds: Optional[float] = None,
    pages_viewed: Optional[int] = None,
    event_date: Optional[str] = None  # ISO format for timing analysis
) -> None:
    """
    Track event page visits with timing context.
    Differentiates pre/post event visits for KPI tracking.
    
    Args:
        event_id: Event identifier
        user_id: Optional user identifier
        visit_type: Type of visit relative to event date
        session_duration_seconds: Time spent on event page
        pages_viewed: Number of pages viewed in session
        event_date: Event date for relative timing calculation
    """
    track_event(
        "event_visit",
        properties={
            "event_id": event_id,
            "user_id": user_id or "anonymous",
            "visit_type": visit_type,
            "event_date": event_date or "unknown"
        },
        measurements={
            "session_duration_seconds": session_duration_seconds or 0.0,
            "pages_viewed": float(pages_viewed or 1)
        }
    )


def track_connection_initiated(
    event_id: str,
    user_id: Optional[str],
    connection_type: str,  # "email_presenter" | "visit_repo" | "contact_organizer" | "linkedin" | "other"
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> None:
    """
    Track connection/lead initiation events.
    """
    track_event(
        "connection_initiated",
        properties={
            "event_id": event_id,
            "user_id": user_id or "anonymous",
            "connection_type": connection_type,
            "target_id": target_id or "unknown",
            **(metadata or {})
        }
    )

def track_content_submission(
    event_id: str,
    presenter_id: str,
    submission_type: str,  # "abstract" | "slides" | "video" | "bio" | "other"
    file_size_bytes: Optional[int] = None,
    file_format: Optional[str] = None,
    submission_stage: str = "initial",  # "initial" | "revision" | "final"
    success: bool = True,
    error_message: Optional[str] = None
) -> None:
    """
    Track presenter content submissions.
    Monitors abstract/slides/video uploads for platform KPIs.
    
    Args:
        event_id: Event identifier
        presenter_id: Presenter user ID
        submission_type: Type of content submitted
        file_size_bytes: Size of uploaded file
        file_format: File format (pdf, pptx, mp4, etc.)
        submission_stage: Stage of submission workflow
        success: Whether submission succeeded
        error_message: Error details if failed
    """
    track_event(
        "content_submission",
        properties={
            "event_id": event_id,
            "presenter_id": presenter_id,
            "submission_type": submission_type,
            "file_format": file_format or "unknown",
            "submission_stage": submission_stage,
            "success": str(success),
            "error_message": error_message or "none"
        },
        measurements={
            "file_size_mb": float(file_size_bytes or 0) / (1024 * 1024)
        }
    )


def track_admin_action(
    admin_user_id: str,
    action_type: str,  # "create_event" | "edit_event" | "delete_event" | "approve_content" | "send_notification" | "other"
    entity_type: str,  # "event" | "session" | "user" | "project" | "artifact"
    entity_id: str,
    success: bool = True,
    error_message: Optional[str] = None
) -> None:
    """
    Track organizer/admin self-service actions.
    Monitors platform KPI: organizer self-service rate.
    
    Args:
        admin_user_id: Admin/organizer user ID
        action_type: Type of administrative action
        entity_type: Type of entity being modified
        entity_id: Entity identifier
        success: Whether action succeeded
        error_message: Error details if failed
    """
    track_event(
        "admin_action",
        properties={
            "admin_user_id": admin_user_id,
            "action_type": action_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "success": str(success),
            "error_message": error_message or "none",
            "requires_support": str(not success)  # Failed actions may need support intervention
        }
    )


def track_cross_event_interaction(
    user_id: str,
    source_event_id: str,
    target_event_id: str,
    interaction_type: str,  # "viewed_from_related" | "bookmarked_both" | "presenter_overlap" | "topic_similarity"
    similarity_score: Optional[float] = None
) -> None:
    """
    Track cross-event engagement patterns.
    Monitors platform KPI: users engaging with multiple events.
    
    Args:
        user_id: User identifier
        source_event_id: Originating event ID
        target_event_id: Destination event ID
        interaction_type: Type of cross-event interaction
        similarity_score: Similarity score between events (0-1)
    """
    track_event(
        "cross_event_interaction",
        properties={
            "user_id": user_id,
            "source_event_id": source_event_id,
            "target_event_id": target_event_id,
            "interaction_type": interaction_type
        },
        measurements={
            "similarity_score": similarity_score or 0.0
        }
    )


def track_fallback_event(
    original_query: str,
    session_id: str,
    foundry_attempt: bool,
    foundry_failed_reason: Optional[str] = None,
    conversation_turn: int = 0,
    user_id: Optional[str] = None,
    deterministic_confidence: float = 0.0
) -> None:
    """
    Track fallback events when queries don't match deterministic intents.
    
    This event occurs when:
    - Query matches no deterministic patterns (confidence 0.0)
    - Foundry escalation is attempted (foundry_attempt=True)
    - Foundry escalation fails and user gets fallback message
    - Foundry is disabled (foundry_attempt=False, foundry_failed_reason="foundry_disabled")
    
    Used to identify conversations that hit fallback and improve intent coverage.
    
    Args:
        original_query: The query that triggered fallback
        session_id: Session identifier for grouping fallback events
        foundry_attempt: Whether Foundry was attempted (True) or disabled (False)
        foundry_failed_reason: Reason Foundry failed (timeout, empty_response, error, foundry_disabled)
        conversation_turn: Turn number in conversation (1-indexed)
        user_id: Optional user identifier
        deterministic_confidence: Confidence score before fallback (should be ~0.0)
    """
    track_event(
        "fallback_event",
        properties={
            "original_query": _sanitize_text(original_query, max_length=300),
            "session_id": session_id,
            "foundry_attempt": str(foundry_attempt),
            "foundry_failed_reason": foundry_failed_reason or "none",
            "user_id": user_id or "anonymous",
            "occurrence_point": "post_foundry_failure" if foundry_attempt else "foundry_disabled"
        },
        measurements={
            "conversation_turn": float(conversation_turn),
            "deterministic_confidence": deterministic_confidence
        }
    )


def log_refusal(
    refusal_reason: str,
    query_context: str,
    handler_name: Optional[str] = None,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None
) -> None:
    """
    Log AI refusal for compliance tracking.

    Args:
        refusal_reason: Reason for refusal (policy, safety, missing citations)
        query_context: User query or request context (truncated upstream)
        handler_name: Handler or route where refusal occurred
        user_id: Optional user identifier
        conversation_id: Optional conversation identifier
    """
    track_event(
        "ai_content_refusal",
        properties={
            "refusal_reason": refusal_reason,
            "query_context": _sanitize_text(query_context),
            "handler_name": handler_name or "unknown",
            "user_id": user_id or "anonymous",
            "conversation_id": conversation_id or "N/A"
        }
    )


def log_edit_action(
    conversation_id: str,
    message_id: str,
    action: str,
    user_id: Optional[str] = None,
    edit_percentage: Optional[float] = None,
    time_since_generation_ms: Optional[float] = None
) -> None:
    """
    Log edit/accept/reject actions for compliance metrics.

    Args:
        conversation_id: Conversation identifier
        message_id: Message identifier
        action: accept | edit | reject
        user_id: Optional user identifier
        edit_percentage: Percent difference between original and edited
        time_since_generation_ms: Time from generation to action
    """
    track_event(
        "ai_edit_action",
        properties={
            "conversation_id": conversation_id,
            "message_id": message_id,
            "action": action,
            "user_id": user_id or "anonymous",
            "has_significant_edit": str((edit_percentage or 0) > 10.0)
        },
        measurements={
            "edit_percentage": edit_percentage or 0.0,
            "time_since_generation_ms": time_since_generation_ms or 0.0
        }
    )


def track_exception(
    exception: Exception,
    properties: Optional[Dict[str, str]] = None
) -> None:
    """
    Track an exception.
    
    Args:
        exception: Exception object
        properties: Additional properties
    """
    if not _telemetry_client:
        return
    
    props = properties or {}
    props["timestamp"] = datetime.utcnow().isoformat()
    props["exception_type"] = type(exception).__name__
    
    _telemetry_client.track_exception(
        type(exception),
        exception,
        None,  # tb
        props
    )


def telemetry_decorator(operation: str, entity_type: str):
    """
    Decorator to automatically track repository operations.
    
    Usage:
        @telemetry_decorator("create", "event")
        def create_event(self, event):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_msg = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                duration = (time.time() - start_time) * 1000
                
                # Extract entity_id if available
                entity_id = None
                if len(args) > 1:
                    entity_id = getattr(args[1], 'id', None) or (
                        args[1] if isinstance(args[1], str) else None
                    )
                
                track_repository_operation(
                    operation=operation,
                    repository=args[0].__class__.__name__ if args else "Unknown",
                    entity_type=entity_type,
                    entity_id=entity_id,
                    success=success,
                    duration_ms=duration,
                    error_message=error_msg
                )
        
        return wrapper
    return decorator


def flush_telemetry() -> None:
    """Flush telemetry data before shutdown."""
    if not _telemetry_client:
        return
    
    _telemetry_client.flush()
    print("[Telemetry] Flushed successfully")
