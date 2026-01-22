"""
Foundry Agent for streaming chat with conversation context.

Integrates with Microsoft Foundry (Azure AI Foundry) using Agent Framework v2.
Supports multi-turn conversations, conversation context, and SSE streaming.
"""

import logging
import json
from typing import AsyncGenerator, Optional, Dict, Any
from dataclasses import dataclass

from azure.identity.aio import DefaultAzureCredential
from agent_framework_azure_ai import AzureAIClient

logger = logging.getLogger(__name__)


@dataclass
class FoundryAgentConfig:
    """Configuration for Foundry Agent."""
    project_endpoint: str
    model_deployment: str
    agent_name: str = "EventHubChatAgent"
    instructions: Optional[str] = None


class FoundryAgent:
    """Foundry-based chat agent with streaming support."""

    def __init__(self, config: FoundryAgentConfig):
        """Initialize Foundry agent."""
        self.config = config
        self.client: Optional[AzureAIClient] = None
        self.agent = None

    async def initialize(self) -> None:
        """Initialize the Foundry agent (async context setup)."""
        if self.client is not None:
            return  # Already initialized

        try:
            credential = DefaultAzureCredential()
            self.client = AzureAIClient(
                project_endpoint=self.config.project_endpoint,
                model_deployment_name=self.config.model_deployment,
                credential=credential,
            )

            # Create or retrieve agent
            self.agent = await self.client.create_agent(
                name=self.config.agent_name,
                instructions=self.config.instructions or self._get_default_instructions(),
            )
            logger.info(f"Foundry agent '{self.config.agent_name}' initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Foundry agent: {e}", exc_info=True)
            raise

    async def stream_chat(
        self,
        user_query: str,
        messages: list[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response from Foundry agent.

        Args:
            user_query: The user's current message
            messages: Conversation history (list of {role, content} dicts)
            context: Additional context (conversation_id, user_id, etc.)

        Yields:
            Streamed response chunks (delta text)
        """
        if not self.agent:
            await self.initialize()

        try:
            # Build system context from conversation history and context
            system_prompt = self._build_system_prompt(messages, context)

            # Log delegation start
            logger.info(
                f"Foundry delegation: query='{user_query[:100]}...', "
                f"history_len={len(messages)}, context={context}"
            )

            # Stream response from agent
            async for chunk in self.agent.run_stream(
                f"{system_prompt}\n\nUser: {user_query}",
            ):
                if chunk.text:
                    # Yield delta (just the text content)
                    yield chunk.text
        except Exception as e:
            logger.error(f"Foundry agent stream failed: {e}", exc_info=True)
            raise

    async def close(self) -> None:
        """Clean up resources."""
        if self.client:
            await self.client.close()
            self.client = None
            self.agent = None

    def _build_system_prompt(
        self, messages: list[Dict[str, str]], context: Optional[Dict[str, Any]]
    ) -> str:
        """Build system prompt from conversation history and context."""
        history_context = ""

        # Include recent conversation history for context
        recent_messages = messages[-4:] if len(messages) > 4 else messages
        if recent_messages:
            history_context = "Recent conversation:\n"
            for msg in recent_messages:
                role = msg.get("role", "unknown").title()
                content = msg.get("content", "")[:200]
                history_context += f"  {role}: {content}\n"

        # Include additional context
        context_info = ""
        if context:
            if isinstance(context, dict):
                if "conversation_id" in context:
                    context_info += f"[Conversation ID: {context['conversation_id']}]\n"
                if "user_id" in context:
                    context_info += f"[User: {context['user_id']}]\n"

        return f"""You are a helpful AI assistant for the Redmond Research Showcase 2025.
{history_context}
{context_info}
Provide helpful, accurate responses based on the context provided."""

    def _get_default_instructions(self) -> str:
        """Get default agent instructions."""
        return """You are a helpful AI assistant for the Redmond Research Showcase 2025.
Your role is to help users discover and explore research projects, answer questions about events, and provide information about speakers and research themes.

Guidelines:
- Be friendly and professional
- Provide accurate information about projects and events
- If unsure, suggest the user visit the official website
- Keep responses concise but informative
- Support both natural language queries and structured searches"""


async def create_foundry_agent(
    project_endpoint: str, model_deployment: str
) -> FoundryAgent:
    """
    Factory function to create and initialize a Foundry agent.

    Args:
        project_endpoint: Foundry project endpoint URL
        model_deployment: Deployed model name

    Returns:
        Initialized FoundryAgent instance
    """
    config = FoundryAgentConfig(
        project_endpoint=project_endpoint,
        model_deployment=model_deployment,
    )
    agent = FoundryAgent(config)
    await agent.initialize()
    return agent
