"""
Error handling middleware for action handlers.

Provides unified exception handling and error response generation
for all action types.
"""

import json
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ActionExecutionError(Exception):
    """Raised when action execution fails."""

    def __init__(self, action: str, message: str, original_error: Optional[Exception] = None):
        self.action = action
        self.message = message
        self.original_error = original_error
        super().__init__(f"Action '{action}' failed: {message}")


class ActionValidationError(Exception):
    """Raised when action payload validation fails."""

    def __init__(self, action: str, message: str):
        self.action = action
        self.message = message
        super().__init__(f"Invalid payload for action '{action}': {message}")


class ErrorHandlingMiddleware:
    """
    Middleware for unified error handling across all actions.
    
    Catches exceptions from handlers and returns standardized error responses.
    
    Usage:
        @ErrorHandlingMiddleware()
        async def my_action(payload, context):
            ...
    """

    def __init__(self, return_error_card: bool = True):
        """
        Initialize middleware.
        
        Args:
            return_error_card: If True, generate error card on failure
        """
        self.return_error_card = return_error_card
        self.logger = logger

    def __call__(self, func: Callable) -> Callable:
        """
        Decorate async function with error handling.
        
        Args:
            func: Async function to wrap
            
        Returns:
            Wrapped function
        """

        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ActionValidationError as e:
                self.logger.warning(f"Validation error in action '{e.action}': {e.message}")
                error_msg = f"Invalid input: {e.message}"
                error_card = self._build_error_card(e.action, error_msg) if self.return_error_card else None
                return error_msg, error_card
            except ActionExecutionError as e:
                self.logger.error(
                    f"Execution error in action '{e.action}': {e.message}",
                    exc_info=e.original_error,
                )
                error_msg = f"Failed to execute action. Please try again."
                error_card = self._build_error_card(e.action, error_msg) if self.return_error_card else None
                return error_msg, error_card
            except Exception as e:
                action_name = kwargs.get("action_name", "unknown")
                self.logger.error(
                    f"Unexpected error in action '{action_name}': {str(e)}",
                    exc_info=True,
                )
                error_msg = "An unexpected error occurred. Please try again."
                error_card = self._build_error_card(action_name, error_msg) if self.return_error_card else None
                return error_msg, error_card

        return wrapper

    @staticmethod
    def _build_error_card(action: str, message: str) -> dict:
        """Build an error Adaptive Card."""
        return {
            "type": "AdaptiveCard",
            "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
            "version": "1.5",
            "fallbackText": f"Error: {message}",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "⚠️ Error",
                    "size": "large",
                    "weight": "bolder",
                    "color": "attention",
                },
                {"type": "TextBlock", "text": message, "wrap": True},
                {
                    "type": "TextBlock",
                    "text": f"Action: {action}",
                    "size": "small",
                    "isSubtle": True,
                },
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "Try Again",
                    "data": {"action": "browse_all"},
                },
            ],
        }
