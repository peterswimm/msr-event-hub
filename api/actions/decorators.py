"""
Decorators for action handler registration and metadata.

Enables declarative handler registration and feature annotations.
"""

import logging
from typing import Type, Optional
from functools import wraps

logger = logging.getLogger(__name__)


def register_action(
    action_name: str,
    description: Optional[str] = None,
    requires_foundry: bool = False,
):
    """
    Decorator to register an action handler.
    
    Usage:
        @register_action("browse_all", "Display all featured projects")
        class BrowseAllHandler(BaseActionHandler):
            async def execute(self, payload, context):
                ...
    
    Args:
        action_name: Unique action identifier
        description: Human-readable description
        requires_foundry: If True, handler can delegate to Foundry agents
    """

    def decorator(cls: Type) -> Type:
        """Register the handler class."""
        # Import here to avoid circular dependency
        from api.actions.base import get_registry

        handler_instance = cls(action_name)
        registry = get_registry()

        try:
            registry.register(
                action_name,
                handler_instance,
                requires_foundry=requires_foundry,
                description=description,
            )
            logger.info(f"Registered action handler: {action_name}")
        except ValueError as e:
            logger.warning(f"Failed to register handler {action_name}: {e}")

        return cls

    return decorator


def requires_foundry(func):
    """
    Decorator to mark handlers that require Foundry agent capability.
    
    Enables conditional Foundry delegation based on handler complexity.
    
    Usage:
        @requires_foundry
        async def execute(self, payload, context):
            # This handler can delegate to Foundry for reasoning
            ...
    """

    @wraps(func)
    async def wrapper(self, payload, context):
        # Set flag on handler instance
        self._requires_foundry = True
        return await func(self, payload, context)

    return wrapper
