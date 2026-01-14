"""
1DS Telemetry instrumentation for Backend API
Tracks copilot operations, data access, and performance metrics
"""

import os
import time
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
            "has_comment": str(bool(comment))
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
