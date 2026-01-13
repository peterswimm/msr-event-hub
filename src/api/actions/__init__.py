"""
Unified chat actions system for MSR Event Hub Chat.

Architecture:
- BaseActionHandler: Abstract base for all action handlers
- ActionRegistry: Centralized dispatcher for registered actions
- @register_action: Decorator for handler registration
- @requires_foundry: Marks handlers requiring Foundry agent delegation
- Error handling middleware: Unified exception handling
- Session-level caching: Configurable event data caching

This system enables declarative agent patterns compatible with:
- Microsoft 365 Agents Toolkit (declarative agents)
- AI Foundry agent delegation
- Unified response streaming (SSE format)
"""

from src.api.actions.base import BaseActionHandler, ActionRegistry, get_registry
from src.api.actions.decorators import register_action, requires_foundry
from src.api.actions.schemas import (
    ActionPayload,
    BrowseAllPayload,
    FilterPayload,
    SearchPayload,
    NavigationPayload,
)
from src.api.actions.middleware import ErrorHandlingMiddleware

__all__ = [
    "BaseActionHandler",
    "ActionRegistry",
    "get_registry",
    "register_action",
    "requires_foundry",
    "ActionPayload",
    "BrowseAllPayload",
    "FilterPayload",
    "SearchPayload",
    "NavigationPayload",
    "ErrorHandlingMiddleware",
]
