"""
Unified chat routes with action registry integration.

This module implements a hybrid chat router that:
1. Detects Adaptive Card actions (JSON format) and dispatches via action registry
2. Routes natural language queries using deterministic intent classification
3. Delegates to Foundry agents for complex reasoning
4. Falls back to Azure OpenAI for general queries
"""

import logging
import os
import json
from typing import Generator, Iterable, List, Optional, Dict, Any
from datetime import datetime
import time
import asyncio

import requests
from azure.identity import DefaultAzureCredential

# Import action system to ensure handlers are registered
from src.api import action_init  # noqa: F401
from src.observability.telemetry import (
    track_model_inference,
    track_user_feedback,
    track_event,
    log_refusal,
    log_edit_action,
    track_event_visit,
    track_connection_initiated,
    track_fallback_event
)
from src.observability.intent_metrics import IntentMetrics
from src.integrations.foundry_wrapper import (
    stream_foundry_response,
    get_foundry_agent,
)

try:
    from fastapi import APIRouter, HTTPException, Request
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # pragma: no cover
    APIRouter = None  # type: ignore
    HTTPException = Exception  # type: ignore
    StreamingResponse = None  # type: ignore
    BaseModel = object  # type: ignore
    Field = lambda *args, **kwargs: None  # type: ignore

logger = logging.getLogger(__name__)
credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)

# Initialize intent metrics tracking (singleton)
intent_metrics = IntentMetrics()

AZURE_OPENAI_SCOPE = "https://cognitiveservices.azure.com/.default"
DEFAULT_API_VERSION = "2024-02-15-preview"
DELEGATE_TO_FOUNDRY = os.getenv("DELEGATE_TO_FOUNDRY", "false").lower() == "true"
FOUNDRY_ALLOW_PER_REQUEST_OVERRIDE = os.getenv("FOUNDRY_ALLOW_PER_REQUEST_OVERRIDE", "true").lower() == "true"
FOUNDRY_REQUIRED_ROLE = os.getenv("FOUNDRY_REQUIRED_ROLE", "")


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str
    adaptive_card: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 400


def _get_required_env(name: str) -> str:
    """Get required environment variable."""
    value = os.getenv(name)
    if not value:
        # Log as refusal for compliance
        log_refusal(
            refusal_reason="missing_configuration",
            query_context=f"Config missing: {name}",
            handler_name="chat_router",
            user_id=None,
            conversation_id=None
        )
        raise HTTPException(status_code=500, detail=f"Missing configuration: {name}")
    return value.rstrip("/")


def _get_bearer_token() -> str:
    """Get Azure bearer token."""
    token = credential.get_token(AZURE_OPENAI_SCOPE)
    return token.token


def _iter_azure_stream(resp: requests.Response) -> Iterable[str]:
    """Iterate over Azure streaming response."""
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        yield raw


def _should_delegate_to_foundry(request: Request) -> tuple[bool, bool]:
    """Determine if this request should delegate to Foundry.

    Returns (delegate_enabled, debug_enabled).
    """
    delegate = DELEGATE_TO_FOUNDRY

    # Per-request opt-in via header or query flag
    if FOUNDRY_ALLOW_PER_REQUEST_OVERRIDE:
        header_flag = request.headers.get("x-delegate-to-foundry", "") == "1"
        query_flag = request.query_params.get("foundry", "") == "1"
        delegate = delegate or header_flag or query_flag

    if not delegate:
        return False, False

    # Require auth context forwarded from bridge
    user_roles = []
    if request.headers.get("x-user-roles"):
        user_roles = [r.strip() for r in request.headers.get("x-user-roles", "").split(",") if r.strip()]

    if FOUNDRY_REQUIRED_ROLE and FOUNDRY_REQUIRED_ROLE not in user_roles:
        return False, False

    if not FOUNDRY_ENDPOINT or not FOUNDRY_AGENT_ID:
        return False, False

    debug_enabled = request.headers.get("x-debug", "") == "1" or request.query_params.get("debug", "") == "1"
    return True, debug_enabled


def _forward_stream(payload: ChatRequest) -> Generator[str, None, None]:
    """Forward request to Azure OpenAI."""
    endpoint = _get_required_env("AZURE_OPENAI_ENDPOINT")
    deployment = _get_required_env("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_VERSION", DEFAULT_API_VERSION)

    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

    data = {
        "messages": [m.model_dump() for m in payload.messages],
        "temperature": payload.temperature if payload.temperature is not None else 0.3,
        "max_tokens": payload.max_tokens if payload.max_tokens is not None else 400,
        "stream": True,
    }

    headers = {
        "Authorization": f"Bearer {_get_bearer_token()}",
        "Content-Type": "application/json",
    }

    with requests.post(url, headers=headers, json=data, stream=True, timeout=300) as resp:
        if not resp.ok:
            detail = resp.text or resp.reason
            logger.error("Azure OpenAI request failed: %s %s", resp.status_code, detail)
            
            # Log as refusal if it's a content filter (400) or rate limit (429)
            if resp.status_code in (400, 429):
                log_refusal(
                    refusal_reason="azure_openai_filter" if resp.status_code == 400 else "rate_limit",
                    query_context=detail[:200],
                    handler_name="azure_openai_forward",
                    user_id=None,
                    conversation_id=None
                )
            
            raise HTTPException(status_code=resp.status_code, detail=detail)

        for line in _iter_azure_stream(resp):
            if not line.startswith("data:"):
                continue
            yield f"{line}\n\n"


def get_chat_router():
    """Get FastAPI router for chat endpoints."""
    if APIRouter is None:
        return None

    router = APIRouter(prefix="/api/chat", tags=["Chat"])
    
    # Get rate limiter from app state (set in main.py)
    try:
        from slowapi import Limiter
        from slowapi.util import get_remote_address
        limiter = Limiter(key_func=get_remote_address)
    except ImportError:
        limiter = None
        logger.warning("slowapi not installed - rate limiting disabled")

    def _stream_fallback_message(query: str, context: Any, session_id: str = "fallback"):
        """Stream a graceful fallback message with core chat abilities."""
        from src.observability.telemetry import track_fallback_event
        
        # Log the fallback event
        track_fallback_event(
            original_query=query,
            session_id=session_id,
            foundry_attempt=delegate_to_foundry,
            foundry_failed_reason="foundry_attempt_failed" if delegate_to_foundry else "foundry_disabled",
            conversation_turn=getattr(context, "turn_count", 1),
            user_id=getattr(context, "user_id", None),
            deterministic_confidence=0.0
        )
        
        # Fallback message with core 4 abilities
        fallback_text = """I'm having trouble understanding that query. Let me help you with what I can do:

• **Find research projects** – Search for events by topic, category, or keyword
• **Search for people** – Look up speakers, organizers, and team members  
• **Check event details** – Browse sessions, schedules, and event information
• **Equipment & logistics** – Find presentation requirements and resource information

Try rewording your question or ask me about any of these topics!"""
        
        # Track the fallback event with intent metrics
        intent_metrics.log_fallback(
            query=query,
            session_id=session_id,
            foundry_attempted=delegate_to_foundry,
            foundry_failed_reason="foundry_attempt_failed" if delegate_to_foundry else "foundry_disabled",
            conversation_turn=getattr(context, "turn_count", 1)
        )
        
        # Stream as SSE
        response = {
            "delta": fallback_text,
            "context": context.to_dict(),
            "fallback": True
        }
        yield f"data: {json.dumps(response)}\n\n"
        yield "data: [DONE]\n\n"

    async def handle_card_action_unified(
        action_type: str, card_action: Dict[str, Any], context: Any
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        Unified card action dispatcher using action registry.
        
        Replaces ~500 lines of duplicated handler code with declarative dispatch.
        All handlers are registered via @register_action decorator.
        """
        from src.api.actions.base import get_registry
        from src.api.actions.schemas import validate_action_payload
        from src.api.actions.middleware import ActionExecutionError, ActionValidationError
        from src.api.actions.helpers import build_error_card

        try:
            # Validate action payload against schema
            validated_payload = validate_action_payload(action_type, card_action)

            # Get registry and dispatch to handler
            registry = get_registry()
            if not registry.is_registered(action_type):
                logger.warning(f"Action not registered: {action_type}")
                raise KeyError(f"Action '{action_type}' not registered")

            # Execute handler
            result_text, result_card = await registry.dispatch(
                action_type, validated_payload, context
            )

            logger.debug(f"Action '{action_type}' completed successfully")
            return result_text, result_card

        except (ActionValidationError, ActionExecutionError) as e:
            logger.error(f"Action '{action_type}' failed: {str(e)}")
            error_card = build_error_card(str(e), action_type)
            return str(e), error_card
        except KeyError:
            logger.error(f"Unregistered action: {action_type}")
            error_msg = f"Action '{action_type}' is not available"
            error_card = build_error_card(error_msg, action_type)
            return error_msg, error_card
        except Exception as e:
            logger.error(f"Unexpected error in action '{action_type}': {str(e)}", exc_info=True)
            error_msg = "An unexpected error occurred while processing your request"
            error_card = build_error_card(error_msg, action_type)
            return error_msg, error_card

    @router.get("/health")
    async def chat_health():
        """Health check endpoint for chat service."""
        return {
            "status": "healthy",
            "service": "chat-hybrid-router",
            "timestamp": datetime.now().isoformat(),
        }

    @router.get("/welcome")
    async def welcome():
        """Get welcome message with example prompts."""
        from src.api.card_renderer import get_card_renderer

        renderer = get_card_renderer()
        welcome_card = renderer.render_welcome_card()

        return {
            "message": "",
            "adaptive_card": welcome_card,
        }

    @router.post("/stream")
    async def stream_chat(payload: ChatRequest, request: Request):
        """
        Hybrid chat endpoint with intelligent routing.
        
        Flow:
        1. Check if JSON card action -> dispatch via registry
        2. Classify as intent -> deterministic routing
        3. Low confidence -> delegate to Foundry
        4. Fallback -> Azure OpenAI
        
        Rate Limits (DOSA compliance):
        - 20 requests/minute per IP (chat queries)
        - Fail-closed on rate limit (429 + telemetry)
        \"\"\"
        # Apply rate limiting if available
        if limiter:
            try:
                await limiter.check_request_limit(
                    request=request,
                    endpoint_func=stream_chat,
                    rate_limit=\"20/minute\"
                )
            except Exception:
                pass  # Rate limit handler in main.py will catch
                
        try:
            from src.api.query_router import DeterministicRouter
            from src.api.router_config import router_config
            from src.api.conversation_context import extract_context_from_messages

            # Extract user query
            user_query = payload.messages[-1].content if payload.messages else ""

            if not user_query:
                # Log as refusal for compliance (empty query)
                log_refusal(
                    refusal_reason="empty_query",
                    query_context="",
                    handler_name="chat_router",
                    user_id=context.user_id if hasattr(context, "user_id") else None,
                    conversation_id=getattr(context, "conversation_id", None)
                )
                raise HTTPException(status_code=400, detail="No query provided")

            # Extract conversation context
            context = extract_context_from_messages([m.model_dump() for m in payload.messages])
            context.advance_turn()
            logger.info(f"Conversation context: {context.to_dict()}")

            # Check if Foundry delegation is allowed/requested
            delegate_to_foundry, debug_enabled = _should_delegate_to_foundry(request)

            # Step 1: Check if this is a card action (JSON)
            card_action = None
            try:
                card_action = json.loads(user_query)
                if not isinstance(card_action, dict) or "action" not in card_action:
                    card_action = None
            except (json.JSONDecodeError, ValueError):
                card_action = None

            if card_action:
                action_type = card_action.get("action")
                logger.info(f"Processing card action: {action_type}")
                start_time = time.time()

                try:
                    result_text, result_card = await handle_card_action_unified(
                        action_type, card_action, context
                    )
                    
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Track card action as feature usage
                    track_event(
                        "card_action",
                        properties={
                            "action_type": action_type,
                            "conversation_id": context.conversation_id,
                            "has_card": str(result_card is not None),
                            "success": "true"
                        },
                        measurements={
                            "duration_ms": duration_ms
                        }
                    )

                    logger.info(f"Card action result: text='{result_text}', card={result_card is not None}")
                    if result_card:
                        logger.debug(f"Card keys: {list(result_card.keys())}, size: {len(json.dumps(result_card))} bytes")

                    async def action_response_stream():
                        payload_data = {
                            "delta": result_text,
                        }
                        if result_card:
                            payload_data["adaptive_card"] = result_card
                        payload_data["context"] = context.to_dict()

                        logger.info(f"Streaming payload keys: {list(payload_data.keys())}, has adaptive_card: {'adaptive_card' in payload_data}")
                        
                        # Log the size of what we're sending
                        json_str = json.dumps(payload_data)
                        logger.info(f"Payload JSON size: {len(json_str)} bytes")
                        
                        # Log first 500 chars for debugging
                        logger.debug(f"Payload preview: {json_str[:500]}...")
                        
                        yield f"data: {json_str}\n\n"
                        yield "data: [DONE]\n\n"

                    return StreamingResponse(
                        action_response_stream(), media_type="text/event-stream"
                    )

                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Track failed card action
                    track_event(
                        "card_action",
                        properties={
                            "action_type": action_type,
                            "conversation_id": context.conversation_id,
                            "success": "false",
                            "error": str(e)
                        },
                        measurements={
                            "duration_ms": duration_ms
                        }
                    )
                    
                    logger.error(f"Card action processing failed: {e}", exc_info=True)
                    error_response = {
                        "delta": f"Error processing action: {str(e)}",
                        "context": context.to_dict(),
                    }

                    async def error_stream():
                        yield f"data: {json.dumps(error_response)}\n\n"
                        yield "data: [DONE]\n\n"

                    return StreamingResponse(
                        error_stream(), media_type="text/event-stream"
                    )

            # Foundry override (feature-flagged + per-request opt-in)
            if delegate_to_foundry:
                try:
                    logger.info(f"Delegating to Foundry: query='{user_query[:100]}...', conversation_id={context.conversation_id}")
                    track_event(
                        "foundry_delegate_start",
                        properties={
                            "conversation_id": context.conversation_id,
                            "user_id": getattr(context, "user_id", None),
                            "debug": str(debug_enabled).lower(),
                        },
                    )
                    start_time = time.time()

                    async def foundry_delegated_stream():
                        try:
                            async for chunk in stream_foundry_response(
                                user_query,
                                [m.model_dump() for m in payload.messages],
                                context.to_dict(),
                            ):
                                yield chunk
                            duration_ms = (time.time() - start_time) * 1000
                            track_event(
                                "foundry_delegate_success",
                                properties={
                                    "conversation_id": context.conversation_id,
                                    "debug": str(debug_enabled).lower(),
                                },
                                measurements={"duration_ms": duration_ms},
                            )
                            yield "data: [DONE]\n\n"
                        except Exception as e:
                            duration_ms = (time.time() - start_time) * 1000
                            logger.warning(f"Foundry delegation failed: {e}", exc_info=True)
                            track_event(
                                "foundry_delegate_error",
                                properties={
                                    "conversation_id": context.conversation_id,
                                    "error": str(e)[:200],
                                },
                                measurements={"duration_ms": duration_ms},
                            )
                            # Fallback to Azure OpenAI
                            logger.info("Falling back to Azure OpenAI")
                            track_event(
                                "foundry_delegate_fallback",
                                properties={
                                    "conversation_id": context.conversation_id,
                                    "reason": str(e)[:200],
                                },
                            )
                            for line in _forward_stream(payload):
                                yield line
                            yield "data: [DONE]\n\n"

                    return StreamingResponse(foundry_delegated_stream(), media_type="text/event-stream")
                except Exception as e:
                    logger.error(f"Foundry delegation initialization failed: {e}", exc_info=True)
                    raise HTTPException(status_code=500, detail=f"Foundry delegation error: {str(e)}")

            # Step 2: Route natural language queries
            logger.info(f"Routing query: {user_query[:100]}...")
            router = DeterministicRouter()
            routing_start_time = time.time()
            intent_type, confidence = router.classify(user_query)
            
            # Extract patterns matched for metrics
            patterns_matched = []
            query_lower = user_query.lower()
            if intent_type in router.patterns and intent_type != "unmatched":
                for pattern in router.patterns[intent_type]:
                    if pattern.search(query_lower):
                        patterns_matched.append(pattern.pattern)

            logger.info(
                "Intent classified",
                extra={
                    "intent": intent_type,
                    "confidence": confidence,
                    "is_deterministic": confidence >= router_config.deterministic_threshold,
                },
            )

            # Determine execution path
            if confidence >= router_config.deterministic_threshold:
                execution_path = "deterministic"
            elif confidence >= 0.6:
                execution_path = "llm_assisted"
            else:
                execution_path = "full_llm"

            # === FALLBACK HANDLING ===
            # If query doesn't match any deterministic patterns, attempt Foundry silently
            # Only show fallback message if Foundry fails or is disabled
            if intent_type == "unmatched":
                logger.info(f"Query matched no deterministic patterns, attempting Foundry escalation")
                execution_path = "fallback_attempt"
                
                # Try Foundry if enabled and configured
                if delegate_to_foundry:
                    try:
                        logger.info(f"[Fallback Flow] Attempting Foundry for unmatched query")
                        start_time = time.time()
                        
                        async def fallback_with_foundry_stream():
                            """Attempt Foundry first, show fallback only on failure."""
                            foundry_failed = False
                            foundry_error = None
                            
                            try:
                                async for chunk in stream_foundry_response(
                                    user_query,
                                    [m.model_dump() for m in payload.messages],
                                    context.to_dict(),
                                ):
                                    yield chunk
                                duration_ms = (time.time() - start_time) * 1000
                                logger.info(f"[Fallback Flow] Foundry succeeded in {duration_ms:.0f}ms")
                                track_event(
                                    "fallback_foundry_success",
                                    properties={
                                        "conversation_id": context.conversation_id,
                                        "original_query_length": str(len(user_query)),
                                    },
                                    measurements={"duration_ms": duration_ms}
                                )
                                yield "data: [DONE]\n\n"
                            except Exception as e:
                                foundry_failed = True
                                foundry_error = str(e)
                                duration_ms = (time.time() - start_time) * 1000
                                logger.warning(f"[Fallback Flow] Foundry failed: {e}")
                                track_event(
                                    "fallback_foundry_failed",
                                    properties={
                                        "conversation_id": context.conversation_id,
                                        "error": str(e)[:200],
                                    },
                                    measurements={"duration_ms": duration_ms}
                                )
                                
                                # Show graceful fallback message
                                yield from _stream_fallback_message(user_query, context, session_id="unmatched_foundry_failed")
                        
                        return StreamingResponse(fallback_with_foundry_stream(), media_type="text/event-stream")
                    except Exception as e:
                        logger.error(f"[Fallback Flow] Foundry initialization failed: {e}")
                        # Show fallback message
                        async def fallback_error_stream():
                            yield from _stream_fallback_message(user_query, context, session_id="foundry_init_failed")
                        return StreamingResponse(fallback_error_stream(), media_type="text/event-stream")
                
                else:
                    # Foundry not enabled, show fallback directly
                    logger.info(f"[Fallback Flow] Foundry disabled, showing fallback message")
                    async def fallback_disabled_stream():
                        yield from _stream_fallback_message(user_query, context, session_id="foundry_disabled")
                    return StreamingResponse(fallback_disabled_stream(), media_type="text/event-stream")

            # Step 3: Use deterministic routing if high confidence
            if confidence >= router_config.deterministic_threshold:
                logger.info("Using deterministic routing result")
                # Deterministic routing logic here (existing code)
                pass

            # Step 4: Fall back to Azure OpenAI for general queries
            logger.info(f"Using {execution_path} for query (confidence: {confidence:.2f})")
            start_time = time.time()

            if not os.getenv("AZURE_OPENAI_ENDPOINT") or not os.getenv(
                "AZURE_OPENAI_DEPLOYMENT"
            ):
                log_refusal(
                    refusal_reason="service_unavailable",
                    query_context=user_query[:200],
                    handler_name="chat_routes_stream",
                    user_id=getattr(context, "user_id", None),
                    conversation_id=getattr(context, "conversation_id", None)
                )
                error_msg = (
                    "Azure OpenAI is not configured. To enable AI chat, set "
                    "AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT in your .env file.\n\n"
                    f"Detected intent: {intent_type} (confidence: {confidence:.2f})\n"
                    "Currently running with mock data only."
                )

                async def config_error_stream():
                    yield error_msg

                return StreamingResponse(
                    config_error_stream(), media_type="text/event-stream"
                )

            # Track model inference
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "unknown")
            prompt_tokens = sum(len(m.content.split()) for m in payload.messages)
            
            try:
                stream = _forward_stream(payload)
                
                # Wrap stream to track completion
                async def tracked_stream():
                    completion_tokens = 0
                    try:
                        for chunk in stream:
                            # Estimate tokens (rough approximation)
                            if chunk.startswith("data: ") and not chunk.startswith("data: [DONE]"):
                                completion_tokens += len(chunk.split()) // 4
                            yield chunk
                    finally:
                        duration_ms = (time.time() - start_time) * 1000
                        track_model_inference(
                            model_name=deployment,
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            latency_ms=duration_ms,
                            success=True
                        )
                        
                        # Log intent classification metrics
                        routing_latency_ms = (start_time - routing_start_time) * 1000
                        intent_metrics.log_classification(
                            query=user_query,
                            predicted_intent=intent_type,
                            confidence=confidence,
                            patterns_matched=patterns_matched,
                            execution_path=execution_path,
                            latency_ms=routing_latency_ms
                        )
                
                return StreamingResponse(tracked_stream(), media_type="text/event-stream")
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                track_model_inference(
                    model_name=deployment,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=0,
                    latency_ms=duration_ms,
                    success=False,
                    error_type=type(e).__name__
                )
                raise

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/config")
    async def chat_config():
        """Get chat service configuration and routing status."""
        from src.api.router_config import router_config
        
        return {
            "available": True,
            "routing_threshold": router_config.deterministic_threshold,
            "azure_openai_configured": bool(
                os.getenv("AZURE_OPENAI_ENDPOINT")
                and os.getenv("AZURE_OPENAI_DEPLOYMENT")
            ),
        }
    
    class FeedbackRequest(BaseModel):
        """User feedback model."""
        conversation_id: str
        message_id: str
        rating: str = Field(pattern="^(positive|negative)$")
        comment: Optional[str] = None
        user_id: Optional[str] = None

    class IntentFeedbackRequest(BaseModel):
        """Intent routing quality feedback."""
        query: str
        feedback: str = Field(pattern="^(positive|negative|correction)$")
        correction: Optional[str] = None

    class EventVisit(BaseModel):
        """Event visit tracking payload."""
        event_id: str
        visit_type: str = Field(pattern="^(pre_event|post_event|during_event|general)$")
        session_duration_seconds: Optional[float] = None
        pages_viewed: Optional[int] = None
        event_date: Optional[str] = None
        user_id: Optional[str] = None

    class ConnectionInitiated(BaseModel):
        """Connection/lead initiation tracking payload."""
        event_id: str
        connection_type: str = Field(pattern="^(email_presenter|visit_repo|contact_organizer|linkedin|other)$")
        target_id: Optional[str] = None
        metadata: Optional[Dict[str, str]] = None
        user_id: Optional[str] = None

    class EditAction(BaseModel):
        """AI edit/accept/reject action payload."""
        conversation_id: str
        message_id: str
        action: str = Field(pattern="^(accept|edit|reject)$")
        edit_percentage: Optional[float] = None
        time_since_generation_ms: Optional[float] = None
        user_id: Optional[str] = None
    
    @router.post("/feedback")
    async def submit_feedback(feedback: FeedbackRequest):
        """Submit user feedback for a chat interaction."""
        try:
            track_user_feedback(
                conversation_id=feedback.conversation_id,
                message_id=feedback.message_id,
                rating=feedback.rating,
                user_id=feedback.user_id,
                comment=feedback.comment
            )
            
            return {
                "status": "success",
                "message": "Feedback recorded"
            }
        except Exception as e:
            logger.error(f"Failed to record feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to record feedback")

    @router.post("/intent-feedback")
    async def submit_intent_feedback(feedback: IntentFeedbackRequest):
        """Submit feedback on intent routing quality."""
        try:
            intent_metrics.log_user_feedback(
                query=feedback.query,
                feedback=feedback.feedback,
                correction=feedback.correction
            )
            
            return {
                "status": "success",
                "message": "Intent feedback recorded"
            }
        except Exception as e:
            logger.error(f"Failed to record intent feedback: {e}")
            raise HTTPException(status_code=500, detail="Failed to record intent feedback")

    @router.get("/metrics/routing-quality")
    async def routing_quality_metrics():
        """Get real-time routing quality metrics."""
        try:
            coverage = intent_metrics.get_coverage_stats()
            
            return {
                "coverage": coverage,
                "report": intent_metrics.generate_report(),
                "application_insights": {
                    "message": "For comprehensive metrics, query Application Insights with KQL",
                    "workspace_id": os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "").split("InstrumentationKey=")[-1].split(";")[0] if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") else None
                }
            }
        except Exception as e:
            logger.error(f"Failed to get routing metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get routing metrics")

        return {
            "provider": "hybrid",
            "auth": "managed-identity",
            "endpoint": bool(os.getenv("AZURE_OPENAI_ENDPOINT")),
            "deployment": bool(os.getenv("AZURE_OPENAI_DEPLOYMENT")),
            "apiVersion": os.getenv("AZURE_OPENAI_VERSION", DEFAULT_API_VERSION),
            "capabilities": [
                "Project search and filtering",
                "Team member lookup",
                "Category browsing",
                "Session information",
                "Equipment and logistics",
                "Recording status",
            ],
            "routing": {
                "deterministic_enabled": router_config.enable_deterministic_routing,
                "deterministic_threshold": router_config.deterministic_threshold,
                "foundry_delegation_enabled": router_config.delegate_to_foundry,
                "foundry_delegation_threshold": router_config.foundry_delegation_threshold,
                "foundry_configured": bool(router_config.foundry_endpoint),
            },
        }

    @router.post("/telemetry/event-visit")
    async def track_event_visit_endpoint(payload: EventVisit):
        """Track pre/post/during event visits."""
        track_event_visit(
            event_id=payload.event_id,
            user_id=payload.user_id,
            visit_type=payload.visit_type,
            session_duration_seconds=payload.session_duration_seconds,
            pages_viewed=payload.pages_viewed,
            event_date=payload.event_date,
        )
        return {"status": "ok"}

    @router.post("/telemetry/connection")
    async def track_connection_endpoint(payload: ConnectionInitiated):
        """Track connection/lead initiation (email click, repo visit, contact)."""
        track_connection_initiated(
            event_id=payload.event_id,
            user_id=payload.user_id,
            connection_type=payload.connection_type,
            target_id=payload.target_id,
            metadata=payload.metadata,
        )
        return {"status": "ok"}

    @router.post("/telemetry/edit-action")
    async def track_edit_action_endpoint(payload: EditAction):
        """Track AI response edit/accept/reject actions."""
        log_edit_action(
            conversation_id=payload.conversation_id,
            message_id=payload.message_id,
            action=payload.action,
            user_id=payload.user_id,
            edit_percentage=payload.edit_percentage,
            time_since_generation_ms=payload.time_since_generation_ms,
        )
        return {"status": "ok"}

    @router.get("/actions")
    async def list_actions():
        """List all registered action handlers."""
        from src.api.actions.base import get_registry

        registry = get_registry()
        return {
            "total": len(registry.list_actions()),
            "actions": registry.list_actions(),
        }

    return router
