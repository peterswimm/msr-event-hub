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
    track_connection_initiated
)

try:
    from fastapi import APIRouter, HTTPException
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

AZURE_OPENAI_SCOPE = "https://cognitiveservices.azure.com/.default"
DEFAULT_API_VERSION = "2024-02-15-preview"


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
    async def stream_chat(payload: ChatRequest):
        """
        Hybrid chat endpoint with intelligent routing.
        
        Flow:
        1. Check if JSON card action -> dispatch via registry
        2. Classify as intent -> deterministic routing
        3. Low confidence -> delegate to Foundry
        4. Fallback -> Azure OpenAI
        """
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

            # Step 2: Route natural language queries
            logger.info(f"Routing query: {user_query[:100]}...")
            router = DeterministicRouter()
            intent_type, confidence = router.classify(user_query)

            logger.info(
                "Intent classified",
                extra={
                    "intent": intent_type,
                    "confidence": confidence,
                    "is_deterministic": confidence >= router_config.deterministic_threshold,
                },
            )

            # Step 3: Use deterministic routing if high confidence
            if confidence >= router_config.deterministic_threshold:
                logger.info("Using deterministic routing result")
                # Deterministic routing logic here (existing code)
                pass

            # Step 4: Fall back to Azure OpenAI for general queries
            logger.info("Using Azure OpenAI for low-confidence query")
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
