"""
Foundry Agent Service client for delegating complex queries to SaaS orchestration.
Handles agent-to-agent messaging, streaming responses, and managed identity auth.
"""
import os
import json
import logging
from typing import AsyncIterator, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

import aiohttp
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


@dataclass
class FoundryConfig:
    """Configuration for Foundry Agent Service."""
    endpoint: str
    agent_id: str
    api_version: str = "2025-11-15-preview"
    max_retries: int = 2
    request_timeout_seconds: int = 30


class FoundryClient:
    """
    Client for delegating queries to Foundry Agent Service.
    
    Supports:
    - Agent delegation with natural language routing
    - Streaming responses via Server-Sent Events
    - Managed identity authentication
    - Error handling and retries
    """
    
    def __init__(self, config: FoundryConfig):
        self.config = config
        self.credential = DefaultAzureCredential()
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    async def _get_access_token(self) -> str:
        """
        Get access token for Azure authentication.
        Uses managed identity (DefaultAzureCredential) for production,
        falls back to user auth in development.
        """
        scope = "https://cognitiveservices.azure.com/.default"
        token = self.credential.get_token(scope)
        return token.token
    
    async def delegate_to_agent(
        self,
        query: str,
        conversation_history: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Delegate query to Foundry primary agent with streaming response.
        
        Args:
            query: User question or task description
            conversation_history: Prior messages in conversation [{"role": "user"|"assistant", "content": "..."}]
            context: Additional context (project_id, session_id, filters, etc.)
        
        Yields:
            Text deltas from agent response (tokens/chunks)
        
        Raises:
            FoundryDelegationError: If agent service returns error
            FoundryTimeoutError: If request exceeds timeout
        """
        if not self._session:
            raise RuntimeError("Client not initialized. Use 'async with FoundryClient(...) as client'")
        
        try:
            # Build request payload
            messages = conversation_history or []
            messages.append({"role": "user", "content": query})
            
            # Add context as system message if provided
            system_content = self._build_system_prompt(context)
            
            payload = {
                "messages": messages,
                "system": system_content,
                "max_tokens": 2048,
                "temperature": 0.7
            }
            
            # Get auth token
            token = await self._get_access_token()
            
            # Build URL for agent streaming endpoint
            url = (
                f"{self.config.endpoint}/agents/{self.config.agent_id}:chat/stream"
                f"?api-version={self.config.api_version}"
            )
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            }
            
            logger.info(
                f"Delegating to Foundry agent {self.config.agent_id}",
                extra={
                    "query_length": len(query),
                    "has_context": context is not None,
                    "agent_id": self.config.agent_id
                }
            )
            
            # Stream response
            async with self._session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.request_timeout_seconds)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Foundry agent error: {response.status}",
                        extra={"error_detail": error_text}
                    )
                    raise FoundryDelegationError(
                        f"Agent service returned {response.status}: {error_text}"
                    )
                
                # Stream Server-Sent Events
                async for line in response.content:
                    if not line:
                        continue
                    
                    line_str = line.decode('utf-8').strip()
                    
                    # Skip SSE comment lines
                    if line_str.startswith(':'):
                        continue
                    
                    # Parse "data: ..." format
                    if line_str.startswith('data:'):
                        data_str = line_str[5:].strip()
                        
                        # Check for stream end marker
                        if data_str == '[DONE]':
                            break
                        
                        try:
                            # Parse JSON event
                            event = json.loads(data_str)
                            
                            # Extract delta from event
                            if 'delta' in event:
                                delta = event['delta']
                                if isinstance(delta, dict) and 'content' in delta:
                                    content = delta['content']
                                    if content:
                                        yield content
                            elif 'content' in event:
                                # Some versions return content directly
                                yield event['content']
                        
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse SSE event: {data_str}")
                            continue
        
        except asyncio.TimeoutError:
            logger.error("Foundry agent delegation timeout")
            raise FoundryTimeoutError(
                f"Agent service did not respond within {self.config.request_timeout_seconds}s"
            )
        
        except aiohttp.ClientError as e:
            logger.error(f"Foundry client error: {str(e)}")
            raise FoundryDelegationError(f"Network error contacting agent service: {str(e)}")
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """
        Fetch agent metadata (name, description, tools, capabilities).
        Useful for validation and logging.
        """
        if not self._session:
            raise RuntimeError("Client not initialized")
        
        try:
            token = await self._get_access_token()
            
            url = (
                f"{self.config.endpoint}/agents/{self.config.agent_id}"
                f"?api-version={self.config.api_version}"
            )
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json"
            }
            
            async with self._session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to fetch agent info: {response.status}")
                    return {}
        
        except Exception as e:
            logger.error(f"Error fetching agent info: {str(e)}")
            return {}
    
    def _build_system_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """
        Build system prompt that provides agent with context about the MSR event.
        """
        base_prompt = (
            "You are a helpful research event assistant for Microsoft Research (MSR). "
            "You help users find information about research projects, events, sessions, and people. "
            "Provide accurate, concise answers and cite specific project/session names when relevant."
        )
        
        if not context:
            return base_prompt
        
        # Add context about current event/project
        context_parts = [base_prompt]
        
        if 'event_name' in context:
            context_parts.append(f"Current event: {context['event_name']}")
        
        if 'project_id' in context:
            context_parts.append(f"Focused on project: {context['project_id']}")
        
        if 'research_areas' in context:
            areas_str = ", ".join(context['research_areas'])
            context_parts.append(f"Available research areas: {areas_str}")
        
        if 'available_tools' in context:
            tools_str = ", ".join(context['available_tools'])
            context_parts.append(f"Tools: {tools_str}")
        
        return "\n".join(context_parts)


class FoundryDelegationError(Exception):
    """Raised when agent delegation fails."""
    pass


class FoundryTimeoutError(FoundryDelegationError):
    """Raised when agent delegation times out."""
    pass


# Global client instance
_foundry_client: Optional[FoundryClient] = None


async def get_foundry_client(config: Optional[FoundryConfig] = None) -> FoundryClient:
    """
    Get or initialize Foundry client.
    
    Args:
        config: FoundryConfig instance. If None, loads from environment.
    
    Returns:
        Initialized FoundryClient
    """
    global _foundry_client
    
    if _foundry_client is None:
        if config is None:
            config = FoundryConfig(
                endpoint=os.getenv(
                    "FOUNDRY_ENDPOINT",
                    "https://YOUR_FOUNDRY_ENDPOINT.cognitiveservices.azure.com"
                ),
                agent_id=os.getenv(
                    "FOUNDRY_AGENT_ID",
                    "msr-event-orchestrator"
                ),
                api_version=os.getenv("FOUNDRY_API_VERSION", "2025-11-15-preview"),
                max_retries=int(os.getenv("FOUNDRY_MAX_RETRIES", "2")),
                request_timeout_seconds=int(os.getenv("FOUNDRY_TIMEOUT_SECONDS", "30"))
            )
        
        _foundry_client = FoundryClient(config)
    
    return _foundry_client


async def close_foundry_client():
    """Close global client."""
    global _foundry_client
    if _foundry_client:
        await _foundry_client.__aexit__(None, None, None)
        _foundry_client = None
