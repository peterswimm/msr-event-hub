"""Browse and carousel action handlers."""

import logging
from typing import Dict, Any, Tuple, Optional

from api.actions.base import BaseActionHandler
from api.actions.decorators import register_action
from api.actions.helpers import build_project_carousel, apply_filter
from api.caching import get_session_cache
from storage.event_data import get_event_data

logger = logging.getLogger(__name__)


@register_action(
    "browse_all",
    description="Display all or featured projects with carousel card",
)
class BrowseAllHandler(BaseActionHandler):
    """Handler for browse_all action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute browse_all action."""
        try:
            cache = get_session_cache()
            
            # Try to get from cache first
            projects = cache.get("projects")
            if projects is None:
                # Load fresh from storage
                event_data = get_event_data()
                projects = event_data.get("projects", [])
                # Cache for future requests
                cache.set("projects", {"list": projects})
            else:
                projects = projects.get("list", [])

            logger.info(f"Browse all: loaded {len(projects)} projects")

            # Build carousel card
            limit = payload.get("limit", 10)
            card = build_project_carousel(
                projects,
                title="Featured Projects",
                subtitle=f"Showing {min(limit, len(projects))} of {len(projects)} projects",
                max_items=limit,
            )

            return f"Browsing {len(projects)} featured projects.", card

        except Exception as e:
            logger.error(f"Error in browse_all handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        context.conversation_stage = "show_results"
        logger.debug("Updated context: stage -> show_results")


@register_action(
    "show_featured",
    description="Show only featured/highlighted projects",
)
class ShowFeaturedHandler(BaseActionHandler):
    """Handler for show_featured action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute show_featured action."""
        try:
            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            # Filter for featured projects
            featured = apply_filter(
                all_projects, lambda p: p.get("featured", False)
            )

            logger.info(f"Show featured: found {len(featured)} projects")

            if not featured:
                return "No featured projects available at this time.", None

            card = build_project_carousel(
                featured,
                title="Featured Projects",
                subtitle=f"Showing {len(featured)} featured project{'s' if len(featured) != 1 else ''}",
            )

            return f"Found {len(featured)} featured projects.", card

        except Exception as e:
            logger.error(f"Error in show_featured handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        context.conversation_stage = "show_results"


@register_action(
    "recent_projects",
    description="Show recently added projects sorted by date",
)
class RecentProjectsHandler(BaseActionHandler):
    """Handler for recent_projects action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute recent_projects action."""
        try:
            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            # Filter projects with dates and sort
            dated_projects = [p for p in all_projects if p.get("date")]
            recent = sorted(dated_projects, key=lambda p: p.get("date"), reverse=True)

            limit = payload.get("limit", 10)
            recent = recent[:limit]

            logger.info(f"Recent projects: found {len(recent)} projects")

            if not recent:
                return "No recently added projects found.", None

            card = build_project_carousel(
                recent,
                title="Recent Projects",
                subtitle=f"Showing {len(recent)} recently added project{'s' if len(recent) != 1 else ''}",
            )

            return f"Found {len(recent)} recently added projects.", card

        except Exception as e:
            logger.error(f"Error in recent_projects handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        context.conversation_stage = "show_results"
