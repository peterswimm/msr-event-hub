"""
Modern Agent Framework-based knowledge extraction agents.

Replaces direct LLM client usage with Agent Framework for:
- Built-in tracing and observability
- Multi-agent orchestration capabilities
- Tool/function calling support
- Streaming and async by default
"""

import logging
from pathlib import Path
from typing import Optional

from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity import DefaultAzureCredential

from config import get_settings
from core.schemas import BaseKnowledgeArtifact, SourceType
from observability import setup_tracing

logger = logging.getLogger(__name__)


class ModernKnowledgeAgent:
    """
    Base class for knowledge extraction agents using Microsoft Agent Framework.
    
    Key improvements over legacy implementation:
    - Uses Agent Framework for standardized agent interface
    - Automatic tracing and telemetry
    - Async/streaming by default
    - Multi-agent orchestration ready
    - Tool calling support
    """
    
    def __init__(
        self,
        source_type: SourceType,
        agent_name: str,
        instructions: str,
        tools: Optional[list] = None,
    ):
        """
        Initialize modern agent with Agent Framework.
        
        Args:
            source_type: Type of artifact (paper, talk, repository)
            agent_name: Display name for the agent
            instructions: System instructions for the agent
            tools: Optional list of tool functions for function calling
        """
        self.source_type = source_type
        self.agent_name = agent_name
        self.instructions = instructions
        self.settings = get_settings()
        
        # Initialize tracing
        setup_tracing()
        
        # Create Agent Framework client
        self.agent = self._create_agent(tools)
        
        logger.info(f"✓ Initialized {agent_name} with Agent Framework")
    
    def _create_agent(self, tools: Optional[list] = None) -> ChatAgent:
        """Create ChatAgent with AzureAI integration."""
        
        if not self.settings.foundry_project_endpoint:
            raise ValueError(
                "Microsoft Foundry project endpoint not configured. "
                "Set FOUNDRY_PROJECT_ENDPOINT in your environment or .env file."
            )
        
        # Create async Azure AI Agent Client
        client = AzureAIAgentClient(
            project_endpoint=self.settings.foundry_project_endpoint,
            model_deployment_name=self.settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name=self.agent_name,
        )
        
        # Create agent with optional tools
        agent_kwargs = {
            "chat_client": client,
            "instructions": self.instructions,
        }
        
        if tools:
            agent_kwargs["tools"] = tools
        
        return ChatAgent(**agent_kwargs)
    
    async def extract_async(self, input_data: str) -> BaseKnowledgeArtifact:
        """
        Extract knowledge asynchronously (streaming).
        
        Args:
            input_data: Input text or path to process
            
        Returns:
            Structured knowledge artifact
        """
        # Create a new thread for this extraction
        thread = self.agent.get_new_thread()
        
        # Build extraction prompt
        extraction_prompt = self._build_extraction_prompt(input_data)
        
        # Stream response
        full_response = ""
        async for chunk in self.agent.run_stream(extraction_prompt, thread=thread):
            if chunk.text:
                full_response += chunk.text
        
        # Parse response into structured artifact
        artifact = self._parse_response(full_response, input_data)
        
        return artifact
    
    async def extract_sync(self, input_data: str) -> BaseKnowledgeArtifact:
        """
        Extract knowledge synchronously (non-streaming).
        
        Args:
            input_data: Input text or path to process
            
        Returns:
            Structured knowledge artifact
        """
        thread = self.agent.get_new_thread()
        extraction_prompt = self._build_extraction_prompt(input_data)
        
        result = await self.agent.run(extraction_prompt, thread=thread)
        artifact = self._parse_response(result.text, input_data)
        
        return artifact
    
    def _build_extraction_prompt(self, input_data: str) -> str:
        """Build source-specific extraction prompt. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _build_extraction_prompt")
    
    def _parse_response(self, response: str, source_reference: str) -> BaseKnowledgeArtifact:
        """Parse LLM response into structured artifact. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _parse_response")
    
    def save_artifact(self, artifact: BaseKnowledgeArtifact, output_dir: str) -> str:
        """Save artifact as JSON."""
        output_path = Path(output_dir) / "structured"
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{artifact.source_type.value}_{artifact.artifact_id}.json"
        filepath = output_path / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(artifact.model_dump_json(indent=2))
        
        return str(filepath)
    
    def save_summary(self, artifact: BaseKnowledgeArtifact, output_dir: str) -> str:
        """Save human-readable summary."""
        output_path = Path(output_dir) / "summaries"
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"{artifact.source_type.value}_{artifact.artifact_id}_summary.md"
        filepath = output_path / filename
        
        summary = self._format_summary(artifact)
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(summary)
        
        return str(filepath)
    
    def _format_summary(self, artifact: BaseKnowledgeArtifact) -> str:
        """Format artifact as markdown summary."""
        return f"""# {artifact.title}

**Type:** {artifact.source_type.value}
**ID:** {artifact.artifact_id}
**Extracted:** {artifact.extracted_at}

## Summary
{artifact.summary}

## Key Points
{chr(10).join(f"- {point}" for point in artifact.key_points)}

## Source
{artifact.source_reference}
"""


# Export for backward compatibility
__all__ = ["ModernKnowledgeAgent"]
