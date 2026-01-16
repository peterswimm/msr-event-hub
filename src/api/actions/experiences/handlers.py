"""Handlers for new chat experiences: agenda, presenters, bookmarks, synthesis, organizer tools."""

import logging
from typing import Dict, Any, Tuple, Optional

from src.observability.telemetry import track_event

from src.api.actions.base import BaseActionHandler
from src.api.actions.decorators import register_action
from src.api.actions.helpers import build_agenda_card, build_presenter_carousel
from src.storage.event_data import get_event_data

logger = logging.getLogger(__name__)


@register_action(
    "hourly_agenda",
    description="Show hourly agenda with today's sessions",
)
class HourlyAgendaHandler(BaseActionHandler):
    """Handler for hourly_agenda action - displays session schedule."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute hourly_agenda action."""
        try:
            event_data = get_event_data()
            all_sessions = event_data.get("sessions", [])

            logger.info(f"Hourly agenda: loaded {len(all_sessions)} sessions")

            if not all_sessions:
                return "No sessions scheduled at this time.", None

            # Filter for today's sessions (stub: show all for now)
            timezone = payload.get("timezone", "PT")
            max_items = payload.get("max_items", 8)

            card = build_agenda_card(
                all_sessions,
                title="Today's agenda",
                timezone_label=timezone,
                max_items=max_items,
            )

            return f"Here's your agenda with {len(all_sessions)} sessions.", card

        except Exception as e:
            logger.error(f"Error in hourly_agenda handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        context.conversation_stage = "agenda_view"
        logger.debug("Updated context: stage -> agenda_view")


@register_action(
    "presenter_carousel",
    description="Show carousel of key presenters/speakers",
)
class PresenterCarouselHandler(BaseActionHandler):
    """Handler for presenter_carousel action - spotlight on speakers."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute presenter_carousel action."""
        try:
            event_data = get_event_data()
            all_sessions = event_data.get("sessions", [])

            logger.info(f"Presenter carousel: processing {len(all_sessions)} sessions")

            if not all_sessions:
                return "No presenters available yet.", None

            max_presenters = payload.get("max_presenters", 6)

            card = build_presenter_carousel(
                all_sessions,
                max_presenters=max_presenters,
            )

            return "Presenting our featured speakers.", card

        except Exception as e:
            logger.error(f"Error in presenter_carousel handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        context.conversation_stage = "presenter_view"


@register_action(
    "bookmark",
    description="Bookmark intent stub - save item for later (MVP placeholder)",
)
class BookmarkHandler(BaseActionHandler):
    """Handler for bookmark action - MVP stub for saving items."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute bookmark action (stub)."""
        try:
            item_type = payload.get("type", "item")
            item_id = payload.get("projectId") or payload.get("presenter") or payload.get("sessionId")

            track_event(
                "bookmark_action",
                properties={
                    "entity_type": item_type,
                    "entity_id": str(item_id or "unknown"),
                    "user_id": getattr(context, "user_id", "anonymous"),
                    "conversation_id": getattr(context, "conversation_id", "N/A"),
                    "action": "add"
                }
            )

            logger.info(f"Bookmark (stub): type={item_type}, id={item_id}")

            # MVP: just acknowledge, no persistence yet
            return f"✅ Bookmark saved (stub). Item: {item_id or 'unknown'}", None

        except Exception as e:
            logger.error(f"Error in bookmark handler: {e}", exc_info=True)
            raise


@register_action(
    "project_synthesis",
    description="Placeholder for AI-driven project synthesis/recommendations",
)
class ProjectSynthesisHandler(BaseActionHandler):
    """Handler for project_synthesis - aspirational AI synthesis feature."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute project_synthesis action (placeholder)."""
        logger.info("Project synthesis: aspirational feature placeholder")

        return (
            "🔮 **Project synthesis (coming soon)**\n\n"
            "This feature will use AI to analyze your interests and suggest personalized project combinations "
            "and collaboration opportunities.\n\n"
            "For now, try browsing projects by category or use the agenda to plan your visit.",
            None,
        )


@register_action(
    "organizer_tools",
    description="Admin dashboard with system status and organizer tools",
)
class OrganizerToolsHandler(BaseActionHandler):
    """Handler for organizer_tools - admin dashboard with system status."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute organizer_tools action - show admin card."""
        from ...card_renderer import CardRenderer
        
        logger.info("Organizer tools: rendering admin dashboard card")
        
        # Create renderer and render the category_select card (which is now the admin card)
        renderer = CardRenderer()
        admin_card = renderer.render_category_select_card(
            ai_count=0,
            systems_count=0,
            hci_count=0,
            security_count=0
        )

        return (
            "Admin Dashboard - System Status & Organizer Tools",
            admin_card,
        )
