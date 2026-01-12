"""
Multi-agent orchestration workflows.

Provides pre-built patterns for:
- Sequential: Chain agents in order (writer → reviewer)
- Concurrent: Fan-out/fan-in parallel execution
- Group Chat: Manager-directed multi-agent collaboration
- Handoffs: Agent-to-agent delegation
"""

from .sequential_workflow import create_sequential_workflow
from .concurrent_workflow import create_concurrent_workflow
from .group_chat_workflow import create_group_chat_workflow

__all__ = [
    "create_sequential_workflow",
    "create_concurrent_workflow",
    "create_group_chat_workflow",
]
