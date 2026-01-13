"""
Base action handler framework and centralized action registry.

Provides abstract base class for all action handlers and singleton registry
for handler dispatching.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ActionMetadata:
    """Metadata for registered actions."""
    name: str
    handler: "BaseActionHandler"
    requires_foundry: bool = False
    description: Optional[str] = None
    supported_platforms: List[str] = field(default_factory=lambda: ["teams", "web"])


class BaseActionHandler(ABC):
    """
    Abstract base class for all action handlers.
    
    All action handlers must inherit from this class and implement
    the execute() method. This enables unified routing, testing,
    and error handling.
    
    Microsoft best practice: Dependency injection pattern.
    """

    def __init__(self, action_name: str):
        """
        Initialize action handler.
        
        Args:
            action_name: Unique identifier for this action (e.g., "browse_all")
        """
        self.action_name = action_name
        self.logger = logging.getLogger(f"{__name__}.{action_name}")

    @abstractmethod
    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute the action and return response.
        
        Args:
            payload: Validated action payload from card action
            context: Current conversation context
            
        Returns:
            Tuple of (response_text, adaptive_card_dict_or_none)
            
        Raises:
            ActionExecutionError: If action execution fails
        """
        pass

    async def validate_input(self, payload: Dict[str, Any]) -> bool:
        """Validate action payload before execution.
        
        Override in subclass for custom validation.
        
        Args:
            payload: Action payload to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context after action execution.
        
        Override in subclass for context updates.
        
        Args:
            payload: Action payload
            context: Conversation context to update
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get handler metadata for introspection."""
        return {
            "name": self.action_name,
            "class": self.__class__.__name__,
            "module": self.__class__.__module__,
        }


class ActionRegistry:
    """
    Centralized registry for action handlers.
    
    Singleton pattern: Use get_registry() to access global instance.
    Enables declarative handler registration and dynamic dispatch.
    
    Example:
        registry = ActionRegistry()
        registry.register("browse_all", BrowseAllHandler())
        text, card = await registry.dispatch("browse_all", payload, context)
    """

    def __init__(self):
        """Initialize empty registry."""
        self._handlers: Dict[str, ActionMetadata] = {}
        self.logger = logging.getLogger(f"{__name__}.ActionRegistry")

    def register(
        self,
        action_name: str,
        handler: BaseActionHandler,
        requires_foundry: bool = False,
        description: Optional[str] = None,
    ) -> None:
        """
        Register an action handler.
        
        Args:
            action_name: Unique action identifier (e.g., "browse_all")
            handler: BaseActionHandler instance
            requires_foundry: Whether action needs Foundry delegation capability
            description: Human-readable description
            
        Raises:
            ValueError: If action_name already registered
        """
        if action_name in self._handlers:
            raise ValueError(f"Action '{action_name}' already registered")

        metadata = ActionMetadata(
            name=action_name,
            handler=handler,
            requires_foundry=requires_foundry,
            description=description,
        )
        self._handlers[action_name] = metadata
        self.logger.info(
            f"Registered action: {action_name} ({handler.__class__.__name__})"
        )

    def unregister(self, action_name: str) -> None:
        """Unregister an action handler (useful for testing)."""
        if action_name in self._handlers:
            del self._handlers[action_name]
            self.logger.info(f"Unregistered action: {action_name}")

    async def dispatch(
        self,
        action_name: str,
        payload: Dict[str, Any],
        context: Any,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Dispatch to registered action handler.
        
        Args:
            action_name: Action to execute
            payload: Action payload
            context: Conversation context
            
        Returns:
            Tuple of (response_text, adaptive_card_dict_or_none)
            
        Raises:
            KeyError: If action not registered
            ActionExecutionError: If handler execution fails
        """
        if action_name not in self._handlers:
            raise KeyError(f"Action '{action_name}' not registered")

        metadata = self._handlers[action_name]
        handler = metadata.handler

        self.logger.debug(f"Dispatching action: {action_name}")

        # Validate input
        if not await handler.validate_input(payload):
            raise ValueError(f"Invalid payload for action '{action_name}'")

        # Execute handler
        try:
            result_text, result_card = await handler.execute(payload, context)

            # Update context
            await handler.update_context(payload, context)

            self.logger.debug(f"Action '{action_name}' completed successfully")
            return result_text, result_card

        except Exception as e:
            self.logger.error(
                f"Action '{action_name}' execution failed: {str(e)}", exc_info=True
            )
            raise

    def get_handler(self, action_name: str) -> Optional[BaseActionHandler]:
        """Get registered handler by name."""
        metadata = self._handlers.get(action_name)
        return metadata.handler if metadata else None

    def list_actions(self) -> Dict[str, Dict[str, Any]]:
        """List all registered actions with metadata."""
        return {
            name: {
                "description": metadata.description,
                "requires_foundry": metadata.requires_foundry,
                "handler_class": metadata.handler.__class__.__name__,
            }
            for name, metadata in self._handlers.items()
        }

    def is_registered(self, action_name: str) -> bool:
        """Check if action is registered."""
        return action_name in self._handlers


# Global singleton instance
_registry: Optional[ActionRegistry] = None


def get_registry() -> ActionRegistry:
    """
    Get the global ActionRegistry singleton.
    
    Returns:
        ActionRegistry: Global registry instance
    """
    global _registry
    if _registry is None:
        _registry = ActionRegistry()
    return _registry
