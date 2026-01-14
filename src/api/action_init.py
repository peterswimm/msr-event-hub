"""
Quick initialization guide for the unified action system.

This file ensures all action handlers are imported and registered
when the application starts.

Include this import in your FastAPI app initialization:
    from src.api.actions import action_registry
"""

# Import all handler modules to trigger @register_action decorators
# This must be done before the application routes are set up

import logging

logger = logging.getLogger(__name__)


def initialize_action_handlers():
    """Initialize and register all action handlers."""
    logger.info("Initializing action handlers...")

    # Import all handler modules (triggers @register_action decorators)
    try:
        from src.api.actions.browse import handlers as browse_handlers  # noqa: F401
        from src.api.actions.filter import handlers as filter_handlers  # noqa: F401
        from src.api.actions.search import handlers as search_handlers  # noqa: F401
        from src.api.actions.navigation import handlers as nav_handlers  # noqa: F401
        from src.api.actions.experiences import handlers as experience_handlers  # noqa: F401

        from src.api.actions.base import get_registry

        registry = get_registry()
        actions = registry.list_actions()

        logger.info(f"✅ Registered {len(actions)} action handlers:")
        for action_name, metadata in actions.items():
            logger.info(f"  - {action_name}: {metadata.get('handler_class', 'Unknown')}")

    except Exception as e:
        logger.error(f"❌ Failed to initialize action handlers: {e}", exc_info=True)
        raise


# Auto-initialize on import
initialize_action_handlers()
