"""
Tool integration support for agents.

Provides:
- MCP (Model Context Protocol) tool connections
- OpenAPI tool integration
- Custom function tools
"""

from .mcp_tools import create_mcp_tools, MCPToolConfig
from .function_tools import create_function_tool

__all__ = [
    "create_mcp_tools",
    "MCPToolConfig",
    "create_function_tool",
]
