"""Handlers for new chat experiences: agenda, presenters, bookmarks, synthesis, organizer tools."""

import logging
import os
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
    "speaker_contact",
    description="Show contact information for a speaker/presenter",
)
class SpeakerContactHandler(BaseActionHandler):
    """Handler for speaker_contact action - returns speaker details and links."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        try:
            name = (payload.get("name") or "").strip().lower()
            if not name:
                return "Please specify a speaker name.", None

            event_data = get_event_data()
            sessions = event_data.get("sessions", [])

            # Find first matching speaker across sessions
            for sess in sessions:
                for sp in sess.get("speakers", []):
                    sp_name = (sp.get("name") or sp.get("displayName") or "").strip().lower()
                    if sp_name and name in sp_name:
                        email = sp.get("email") or "Unavailable"
                        title = sp.get("title") or ""
                        affiliation = sp.get("affiliation") or ""
                        profile = sp.get("profileUrl") or ""
                        msg = f"{sp.get('name')}: {title} — {affiliation}\nEmail: {email}"
                        if profile:
                            msg += f"\nProfile: {profile}"
                        return msg, None

            return f"I couldn't find contact details for '{payload.get('name')}'.", None

        except Exception as e:
            logger.error(f"Error in speaker_contact handler: {e}", exc_info=True)
            raise


@register_action(
    "download_poster_pdf",
    description="Provide a direct download link to the poster PDF",
)
class DownloadPosterPDFHandler(BaseActionHandler):
    """Handler for download_poster_pdf action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        try:
            project_id = payload.get("projectId")
            if not project_id:
                return "Please specify which poster to download.", None

            event_data = get_event_data()
            projects = event_data.get("projects", [])
            for p in projects:
                if p.get("id") == project_id:
                    pdf = p.get("posterUrl")
                    if pdf:
                        return f"Here is the poster PDF:\n{pdf}", None
                    return "This project doesn't have a poster PDF yet.", None

            return "I couldn't find that project.", None
        except Exception as e:
            logger.error(f"Error in download_poster_pdf handler: {e}", exc_info=True)
            raise


@register_action(
    "share_item",
    description="Provide a shareable link for a session or project",
)
class ShareItemHandler(BaseActionHandler):
    """Handler for share_item action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        try:
            entity_id = payload.get("projectId") or payload.get("sessionId")
            if not entity_id:
                return "Please specify what you want to share.", None

            # For MVP, construct a simple internal link pattern
            base = os.getenv("EVENT_SITE_BASE_URL", "https://events.microsoft.com/msr")
            return f"Shareable link:\n{base}/item/{entity_id}", None
        except Exception as e:
            logger.error(f"Error in share_item handler: {e}", exc_info=True)
            raise


@register_action(
    "report_issue",
    description="Open a feedback form to report an issue",
)
class ReportIssueHandler(BaseActionHandler):
    """Handler for report_issue action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        try:
            form_url = os.getenv("EVENT_FEEDBACK_URL", "https://forms.office.com/r/example")
            return (
                "You can report an issue using our feedback form:",
                {
                    "type": "AdaptiveCard",
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "version": "1.5",
                    "body": [
                        {"type": "TextBlock", "text": "Report an issue", "weight": "bolder", "size": "medium"},
                        {"type": "TextBlock", "text": "Help us improve the event experience.", "isSubtle": True}
                    ],
                    "actions": [
                        {"type": "Action.OpenUrl", "title": "Open feedback form", "url": form_url}
                    ]
                }
            )
        except Exception as e:
            logger.error(f"Error in report_issue handler: {e}", exc_info=True)
            raise


@register_action(
    "contact_organizer",
    description="Show organizer contact information",
)
class ContactOrganizerHandler(BaseActionHandler):
    """Handler for contact_organizer action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        try:
            event_data = get_event_data()
            event = event_data.get("event") or {}
            email = event.get("organizerEmail") or os.getenv("EVENT_ORGANIZER_EMAIL", "msri-events@microsoft.com")
            name = event.get("organizerName") or "Event Organizer"
            return f"{name}: {email}", None
        except Exception as e:
            logger.error(f"Error in contact_organizer handler: {e}", exc_info=True)
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
