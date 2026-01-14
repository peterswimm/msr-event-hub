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

import requests
from azure.identity import DefaultAzureCredential

# Import action system to ensure handlers are registered
from src.api import action_init  # noqa: F401

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
            "message": "Welcome to MSR Event Hub Chat! 🎓",
            "description": "I can help you explore research projects, find sessions, and learn about the Redmond Research Showcase.",
            "examples": [
                {"title": "Find AI projects", "prompt": "Show me all artificial intelligence projects"},
                {"title": "Search by team member", "prompt": "What projects is Alice working on?"},
                {"title": "Browse by category", "prompt": "List all systems and networking projects"},
                {"title": "Equipment requirements", "prompt": "Which projects need a large display?"},
                {"title": "Recording status", "prompt": "Which projects have recording available?"},
            ],
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

                try:
                    result_text, result_card = await handle_card_action_unified(
                        action_type, card_action, context
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

            if not os.getenv("AZURE_OPENAI_ENDPOINT") or not os.getenv(
                "AZURE_OPENAI_DEPLOYMENT"
            ):
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

            stream = _forward_stream(payload)
            return StreamingResponse(stream, media_type="text/event-stream")

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/config")
    async def chat_config():
        """Get chat service configuration and routing status."""
        from src.api.router_config import router_config

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
