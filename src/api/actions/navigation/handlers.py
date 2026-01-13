"""Navigation action handlers."""

import logging
from typing import Dict, Any, Tuple, Optional

from src.api.actions.base import BaseActionHandler
from src.api.actions.decorators import register_action
from src.api.actions.helpers import format_project_list, apply_filter
from src.storage.event_data import get_event_data

logger = logging.getLogger(__name__)


@register_action(
    "view_project",
    description="View detailed information about a specific project",
)
class ViewProjectHandler(BaseActionHandler):
    """Handler for view_project action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute view_project action."""
        try:
            project_id = payload.get("projectId", "")
            if not project_id:
                raise ValueError("projectId parameter is required")

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            project = next(
                (p for p in all_projects if p.get("id") == project_id), None
            )

            if not project:
                logger.warning(f"Project not found: {project_id}")
                return f"Project '{project_id}' not found.", None

            logger.info(f"View project: {project_id}")

            # Build detailed text response
            name = project.get("name", "Untitled")
            area = project.get("researchArea", "General")
            desc = project.get("description", "No description available")
            team = ", ".join(
                [m.get("name", "") for m in project.get("team", [])]
            ) or "No team members listed"
            placement = project.get("placement", "TBD")
            equipment = ", ".join(project.get("equipment", [])) or "Standard"
            recording = project.get("recordingPermission", "Not specified")
            audience = project.get("targetAudience", "General audience")

            text = f"""
📋 **{name}**

🔬 Research Area: {area}
📝 Description: {desc}
👥 Team: {team}
📍 Location: {placement}
🎛️ Equipment: {equipment}
🎥 Recording: {recording}
👨‍👩‍👧‍👦 Audience: {audience}
"""

            return text.strip(), None

        except Exception as e:
            logger.error(f"Error in view_project handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        project_id = payload.get("projectId", "")
        if project_id:
            context.mark_project_viewed(project_id)
        context.conversation_stage = "project_detail"


@register_action(
    "back_to_results",
    description="Return to previous search results",
)
class BackToResultsHandler(BaseActionHandler):
    """Handler for back_to_results action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute back_to_results action."""
        try:
            if not context.last_results:
                return "No previous results available.", None

            logger.info(f"Back to results: {len(context.last_results)} results")

            text = f"📊 Showing {len(context.last_results)} results\n\n"
            text += format_project_list(context.last_results, limit=5)

            return text, None

        except Exception as e:
            logger.error(f"Error in back_to_results handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        context.conversation_stage = "show_results"


@register_action(
    "find_similar",
    description="Find projects similar to current project by research area",
)
class FindSimilarHandler(BaseActionHandler):
    """Handler for find_similar action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute find_similar action."""
        try:
            research_area = payload.get("researchArea", "").lower()
            if not research_area:
                raise ValueError("researchArea parameter is required")

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            similar = apply_filter(
                all_projects,
                lambda p: research_area in p.get("researchArea", "").lower(),
            )[:5]

            logger.info(f"Find similar in '{research_area}': found {len(similar)} projects")

            if not similar:
                return f"No similar projects found in {research_area}.", None

            text = f"🔍 Found {len(similar)} similar projects in {research_area}:\n\n"
            text += format_project_list(similar)

            return text, None

        except Exception as e:
            logger.error(f"Error in find_similar handler: {e}", exc_info=True)
            raise


@register_action(
    "category_select",
    description="Select a research category",
)
class CategorySelectHandler(BaseActionHandler):
    """Handler for category_select action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute category_select action."""
        try:
            category = payload.get("category", "")
            if not category:
                raise ValueError("category parameter is required")

            logger.info(f"Category selected: {category}")
            return f"Category '{category}' selected.", None

        except Exception as e:
            logger.error(f"Error in category_select handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        category = payload.get("category", "")
        if category:
            context.add_category(category)
        context.conversation_stage = "show_results"
