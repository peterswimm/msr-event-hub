"""
Model Context Protocol (MCP) tool integration.

MCP enables agents to connect to external services like:
- Browser automation (Playwright)
- Documentation (Microsoft Learn)
- File systems
- APIs
- Databases
"""

import logging
from dataclasses import dataclass
from typing import Any, List

from agent_framework import MCPStdioTool, MCPStreamableHTTPTool, ToolProtocol

logger = logging.getLogger(__name__)


@dataclass
class MCPToolConfig:
    """Configuration for an MCP tool."""
    name: str
    description: str
    tool_type: str  # "stdio" or "http"
    
    # For stdio tools
    command: str = ""
    args: List[str] = None
    
    # For HTTP tools
    url: str = ""
    
    def __post_init__(self):
        if self.args is None:
            self.args = []


# Pre-configured MCP tools
PLAYWRIGHT_MCP = MCPToolConfig(
    name="Playwright MCP",
    description="Provides browser automation capabilities using Playwright",
    tool_type="stdio",
    command="npx",
    args=["-y", "@playwright/mcp@latest"]
)

MICROSOFT_LEARN_MCP = MCPToolConfig(
    name="Microsoft Learn MCP",
    description="Brings trusted Microsoft documentation directly to agents",
    tool_type="http",
    url="https://learn.microsoft.com/api/mcp"
)

GITHUB_MCP = MCPToolConfig(
    name="GitHub MCP",
    description="Interact with GitHub repositories, issues, and pull requests",
    tool_type="stdio",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"]
)


def create_mcp_tool(config: MCPToolConfig) -> ToolProtocol:
    """
    Create an MCP tool from configuration.
    
    Args:
        config: MCPToolConfig instance
        
    Returns:
        ToolProtocol instance ready to use with agents
    """
    if config.tool_type == "stdio":
        return MCPStdioTool(
            name=config.name,
            description=config.description,
            command=config.command,
            args=config.args
        )
    elif config.tool_type == "http":
        return MCPStreamableHTTPTool(
            name=config.name,
            description=config.description,
            url=config.url
        )
    else:
        raise ValueError(f"Unknown tool type: {config.tool_type}")


def create_mcp_tools(configs: List[MCPToolConfig] = None) -> List[ToolProtocol]:
    """
    Create multiple MCP tools.
    
    Args:
        configs: Optional list of MCPToolConfig. If None, returns common tools.
        
    Returns:
        List of ToolProtocol instances
    """
    if configs is None:
        # Return commonly used MCP tools
        configs = [MICROSOFT_LEARN_MCP]
    
    tools = []
    for config in configs:
        try:
            tool = create_mcp_tool(config)
            tools.append(tool)
            logger.info(f"✓ Created MCP tool: {config.name}")
        except Exception as e:
            logger.error(f"Failed to create MCP tool {config.name}: {e}")
    
    return tools


def create_knowledge_extraction_mcp_tools() -> List[ToolProtocol]:
    """
    Create MCP tools useful for knowledge extraction.
    
    Returns:
        List of configured MCP tools
    """
    return create_mcp_tools([
        MICROSOFT_LEARN_MCP,  # For documentation lookups
        GITHUB_MCP,           # For repository analysis
    ])


# Example: Agent with MCP tools
async def example_agent_with_mcp():
    """Example of creating an agent with MCP tool access."""
    from agent_framework import ChatAgent
    from agent_framework_azure_ai import AzureAIAgentClient
    from azure.identity import DefaultAzureCredential
    from config import get_settings
    
    settings = get_settings()
    
    # Create MCP tools
    mcp_tools = create_knowledge_extraction_mcp_tools()
    
    # Create agent with tools
    agent = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="KnowledgeAgentWithMCP",
        ),
        instructions="""You are a knowledge extraction agent with access to external tools.
        
        You can:
        - Search Microsoft Learn documentation for accurate information
        - Analyze GitHub repositories for code and documentation
        
        Use these tools when you need additional context or verification.""",
        tools=mcp_tools
    )
    
    # Agent can now use MCP tools in its responses
    thread = agent.get_new_thread()
    
    task = "Look up the latest Agent Framework documentation and extract key features"
    
    print("Agent with MCP tools:\n")
    async for chunk in agent.run_stream(task, thread=thread):
        if chunk.text:
            print(chunk.text, end='', flush=True)
        # You can also detect when tools are called
        elif hasattr(chunk, 'raw_representation'):
            raw = chunk.raw_representation
            if (hasattr(raw, 'raw_representation') and 
                hasattr(raw.raw_representation, 'step_details') and
                hasattr(raw.raw_representation.step_details, 'tool_calls')):
                print(f"\n[Tool called: {raw.raw_representation.step_details.tool_calls}]")
    
    print("\n✓ Agent with MCP complete")


__all__ = [
    "MCPToolConfig",
    "create_mcp_tool",
    "create_mcp_tools",
    "create_knowledge_extraction_mcp_tools",
    "PLAYWRIGHT_MCP",
    "MICROSOFT_LEARN_MCP",
    "GITHUB_MCP",
]
