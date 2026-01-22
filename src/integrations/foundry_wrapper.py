"""
Integration layer to use Foundry agent in chat_routes.

This bridges the Foundry agent with the existing FastAPI chat endpoint.
"""

import logging
import os
import json
from typing import AsyncGenerator, Optional, Dict, Any

from src.integrations.foundry_agent import create_foundry_agent, FoundryAgent

logger = logging.getLogger(__name__)

# Singleton instance cache
_foundry_agent_instance: Optional[FoundryAgent] = None


async def get_foundry_agent() -> Optional[FoundryAgent]:
    """
    Get or create a Foundry agent instance (singleton pattern).

    Returns:
        FoundryAgent instance if configured, None otherwise.
    """
    global _foundry_agent_instance

    # Check if configured
    endpoint = os.getenv("FOUNDRY_ENDPOINT", "").strip()
    deployment = os.getenv("FOUNDRY_AGENT_DEPLOYMENT", "").strip()

    if not endpoint or not deployment:
        logger.debug("Foundry agent not configured (missing FOUNDRY_ENDPOINT or FOUNDRY_AGENT_DEPLOYMENT)")
        return None

    # Lazy initialization
    if _foundry_agent_instance is None:
        try:
            logger.info(f"Initializing Foundry agent: endpoint={endpoint}, deployment={deployment}")
            _foundry_agent_instance = await create_foundry_agent(
                project_endpoint=endpoint,
                model_deployment=deployment,
            )
            logger.info("Foundry agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Foundry agent: {e}", exc_info=True)
            _foundry_agent_instance = None
            raise

    return _foundry_agent_instance


async def stream_foundry_response(
    user_query: str,
    messages: list[Dict[str, str]],
    context: Optional[Dict[str, Any]] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream response from Foundry agent (for SSE streaming).

    Args:
        user_query: Current user query
        messages: Conversation history
        context: Additional context (conversation_id, user_id, etc.)

    Yields:
        SSE-formatted chunks: "data: {json}\n\n"
    """
    agent = await get_foundry_agent()
    if not agent:
        raise RuntimeError("Foundry agent not initialized")

    try:
        buffer = ""
        async for chunk in agent.stream_chat(user_query, messages, context):
            buffer += chunk
            # Emit chunks in reasonable sizes for streaming
            if len(buffer) > 50:  # Arbitrary threshold
                yield f"data: {json.dumps({'delta': buffer})}\n\n"
                buffer = ""

        # Flush remaining buffer
        if buffer:
            yield f"data: {json.dumps({'delta': buffer})}\n\n"

    except Exception as e:
        logger.error(f"Foundry streaming error: {e}", exc_info=True)
        raise


async def shutdown_foundry_agent() -> None:
    """Cleanup Foundry agent on shutdown."""
    global _foundry_agent_instance
    if _foundry_agent_instance:
        await _foundry_agent_instance.close()
        _foundry_agent_instance = None
        logger.info("Foundry agent shut down")
