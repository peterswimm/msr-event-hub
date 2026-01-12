import logging
import os
import asyncio
from typing import Generator, Iterable, List, Optional, AsyncIterator

import requests
from azure.identity import DefaultAzureCredential

try:
    from fastapi import APIRouter, HTTPException
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # pragma: no cover - FastAPI optional for non-API runs
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
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 400


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise HTTPException(status_code=500, detail=f"Missing configuration: {name}")
    return value.rstrip("/")


def _get_bearer_token() -> str:
    token = credential.get_token(AZURE_OPENAI_SCOPE)
    return token.token


def _iter_azure_stream(resp: requests.Response) -> Iterable[str]:
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        yield raw


def _forward_stream(payload: ChatRequest) -> Generator[str, None, None]:
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
    if APIRouter is None:
        return None

    router = APIRouter(prefix="/api/chat", tags=["Chat"])

    @router.post("/stream")
    async def stream_chat(payload: ChatRequest):
        """
        Hybrid chat endpoint with intelligent routing:
        1. Try deterministic router first (80% of queries)
        2. For low-confidence queries, delegate to Foundry agents
        3. Fall back to Azure OpenAI for remaining queries
        """
        try:
            # Import here to avoid circular deps and allow optional imports
            from api.query_router import DeterministicRouter
            from api.router_config import router_config
            from api.foundry_client import FoundryClient, FoundryConfig
            
            # Extract user query (last message)
            user_query = payload.messages[-1].content if payload.messages else ""
            
            if not user_query:
                raise HTTPException(status_code=400, detail="No query provided")
            
            # Step 1: Try deterministic routing
            logger.info(f"Routing query: {user_query[:100]}...")
            router = DeterministicRouter()
            intent_type, confidence = router.classify(user_query)
            
            logger.info(
                "Intent classified",
                extra={
                    "intent": intent_type,
                    "confidence": confidence,
                    "is_deterministic": confidence >= router_config.deterministic_threshold
                }
            )
            
            # Step 2: Check if should delegate to Foundry
            if router_config.should_delegate_to_foundry(confidence):
                logger.info(
                    "Delegating to Foundry",
                    extra={
                        "confidence": confidence,
                        "threshold": router_config.foundry_delegation_threshold
                    }
                )
                
                # Delegate to Foundry agents
                try:
                    foundry_config = FoundryConfig(
                        endpoint=router_config.foundry_endpoint,
                        agent_id=router_config.foundry_agent_id
                    )
                    
                    async with FoundryClient(foundry_config) as foundry_client:
                        # Stream response from Foundry
                        async def foundry_stream():
                            async for delta in foundry_client.delegate_to_agent(
                                query=user_query,
                                conversation_history=[m.model_dump() for m in payload.messages[:-1]],
                                context={
                                    "intent": intent.intent_type,
                                    "confidence": intent.confidence
                                }
                            ):
                                yield delta
                        
                        return StreamingResponse(
                            foundry_stream(),
                            media_type="text/event-stream"
                        )
                
                except Exception as e:
                    logger.error(f"Foundry delegation failed, falling back to OpenAI: {e}")
                    # Fall through to Azure OpenAI
            
            # Step 3: Use deterministic result if high confidence
            if confidence >= router_config.deterministic_threshold:
                logger.info("Using deterministic routing result")
                
                # Execute query plan (would call database, knowledge graph, etc.)
                # For now, return mock response
                result_text = f"Found results for intent: {intent_type}\nConfidence: {confidence}"
                
                async def deterministic_stream():
                    yield result_text
                
                return StreamingResponse(
                    deterministic_stream(),
                    media_type="text/event-stream"
                )
            
            # Step 4: Fall back to Azure OpenAI for general queries
            logger.info("Using Azure OpenAI for low-confidence query")
            
            # Check if Azure OpenAI is configured
            if not os.getenv("AZURE_OPENAI_ENDPOINT") or not os.getenv("AZURE_OPENAI_DEPLOYMENT"):
                error_msg = (
                    "Azure OpenAI is not configured. To enable AI chat, set AZURE_OPENAI_ENDPOINT "
                    "and AZURE_OPENAI_DEPLOYMENT in your .env file.\n\n"
                    f"Detected intent: {intent_type} (confidence: {confidence:.2f})\n"
                    "Currently running with mock data only."
                )
                
                async def config_error_stream():
                    yield error_msg
                
                return StreamingResponse(
                    config_error_stream(),
                    media_type="text/event-stream"
                )
            
            stream = _forward_stream(payload)
            return StreamingResponse(stream, media_type="text/event-stream")
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/config")
    async def chat_config():
        """Get chat service configuration and routing status."""
        from api.router_config import router_config
        
        return {
            "provider": "hybrid",
            "auth": "managed-identity",
            "endpoint": bool(os.getenv("AZURE_OPENAI_ENDPOINT")),
            "deployment": bool(os.getenv("AZURE_OPENAI_DEPLOYMENT")),
            "apiVersion": os.getenv("AZURE_OPENAI_VERSION", DEFAULT_API_VERSION),
            "routing": {
                "deterministic_enabled": router_config.enable_deterministic_routing,
                "deterministic_threshold": router_config.deterministic_threshold,
                "foundry_delegation_enabled": router_config.delegate_to_foundry,
                "foundry_delegation_threshold": router_config.foundry_delegation_threshold,
                "foundry_configured": bool(router_config.foundry_endpoint)
            }
        }

    return router
