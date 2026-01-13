"""Filter action handlers."""

import logging
from typing import Dict, Any, Tuple, Optional

from src.api.actions.base import BaseActionHandler
from src.api.actions.decorators import register_action
from src.api.actions.helpers import build_project_carousel, apply_filter, format_project_list
from src.storage.event_data import get_event_data

logger = logging.getLogger(__name__)


@register_action(
    "filter_by_status",
    description="Filter projects by status",
)
class FilterByStatusHandler(BaseActionHandler):
    """Handler for filter_by_status action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute filter_by_status action."""
        try:
            status = payload.get("status", "").lower()
            if not status:
                raise ValueError("Status parameter is required")

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            filtered = apply_filter(
                all_projects,
                lambda p: p.get("status", "").lower() == status,
            )

            logger.info(f"Filter by status '{status}': found {len(filtered)} projects")

            text = f"Found {len(filtered)} {status} project{'s' if len(filtered) != 1 else ''}."
            if filtered:
                text += f"\n{format_project_list(filtered)}"

            return text, None

        except Exception as e:
            logger.error(f"Error in filter_by_status handler: {e}", exc_info=True)
            raise


@register_action(
    "filter_by_team_size",
    description="Filter projects by team size range",
)
class FilterByTeamSizeHandler(BaseActionHandler):
    """Handler for filter_by_team_size action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute filter_by_team_size action."""
        try:
            min_size = payload.get("min", 1)
            max_size = payload.get("max", 1000)

            if min_size > max_size:
                raise ValueError("min cannot be greater than max")

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            filtered = apply_filter(
                all_projects,
                lambda p: min_size <= len(p.get("team", [])) <= max_size,
            )

            logger.info(
                f"Filter by team size {min_size}-{max_size}: found {len(filtered)} projects"
            )

            text = f"Found {len(filtered)} projects with team size {min_size}-{max_size}."
            return text, None

        except Exception as e:
            logger.error(f"Error in filter_by_team_size handler: {e}", exc_info=True)
            raise


@register_action(
    "filter_by_audience",
    description="Filter projects by target audience",
)
class FilterByAudienceHandler(BaseActionHandler):
    """Handler for filter_by_audience action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute filter_by_audience action."""
        try:
            audience = payload.get("audience", "").lower()
            if not audience:
                raise ValueError("Audience parameter is required")

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            filtered = apply_filter(
                all_projects,
                lambda p: audience in p.get("targetAudience", "").lower(),
            )

            logger.info(f"Filter by audience '{audience}': found {len(filtered)} projects")

            text = f"Found {len(filtered)} projects for audience: {audience}."
            return text, None

        except Exception as e:
            logger.error(f"Error in filter_by_audience handler: {e}", exc_info=True)
            raise


@register_action(
    "filter_by_location",
    description="Filter projects by placement location",
)
class FilterByLocationHandler(BaseActionHandler):
    """Handler for filter_by_location action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute filter_by_location action."""
        try:
            location = payload.get("location", "").lower()
            if not location:
                raise ValueError("Location parameter is required")

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            filtered = apply_filter(
                all_projects,
                lambda p: location in p.get("placement", "").lower(),
            )

            logger.info(f"Filter by location '{location}': found {len(filtered)} projects")

            text = f"Found {len(filtered)} projects at {location}."
            return text, None

        except Exception as e:
            logger.error(f"Error in filter_by_location handler: {e}", exc_info=True)
            raise


@register_action(
    "equipment_filter",
    description="Filter projects by equipment needs",
)
class EquipmentFilterHandler(BaseActionHandler):
    """Handler for equipment_filter action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute equipment_filter action."""
        try:
            equipment = payload.get("equipment", "").lower()
            if not equipment:
                raise ValueError("Equipment parameter is required")

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            filtered = apply_filter(
                all_projects,
                lambda p: equipment in ", ".join(p.get("equipment", [])).lower(),
            )

            logger.info(f"Equipment filter '{equipment}': found {len(filtered)} projects")

            text = f"Found {len(filtered)} projects needing {equipment}."
            return text, None

        except Exception as e:
            logger.error(f"Error in equipment_filter handler: {e}", exc_info=True)
            raise


@register_action(
    "recording_filter",
    description="Filter projects by recording availability",
)
class RecordingFilterHandler(BaseActionHandler):
    """Handler for recording_filter action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute recording_filter action."""
        try:
            available = payload.get("available", True)

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            filtered = apply_filter(
                all_projects,
                lambda p: (
                    p.get("recordingPermission", "").lower() == "yes"
                ) == available,
            )

            logger.info(
                f"Recording filter (available={available}): found {len(filtered)} projects"
            )

            availability_text = "available" if available else "not available"
            text = f"Found {len(filtered)} projects with recording {availability_text}."
            return text, None

        except Exception as e:
            logger.error(f"Error in recording_filter handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        context.add_equipment_filter("recording")
        context.conversation_stage = "show_results"


@register_action(
    "filter_by_area",
    description="Filter projects by research area",
)
class FilterByAreaHandler(BaseActionHandler):
    """Handler for filter_by_area action."""

    async def execute(
        self, payload: Dict[str, Any], context: Any
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Execute filter_by_area action."""
        try:
            area = payload.get("area", "").lower()
            if not area:
                raise ValueError("Area parameter is required")

            event_data = get_event_data()
            all_projects = event_data.get("projects", [])

            filtered = apply_filter(
                all_projects,
                lambda p: area in p.get("researchArea", "").lower(),
            )

            logger.info(f"Filter by area '{area}': found {len(filtered)} projects")

            limit = payload.get("limit", 10)
            card = build_project_carousel(
                filtered,
                title=f"Projects in {area}",
                subtitle=f"Showing {min(limit, len(filtered))} of {len(filtered)} projects",
                max_items=limit,
            ) if filtered else None

            text = f"Found {len(filtered)} projects in {area}."
            return text, card

        except Exception as e:
            logger.error(f"Error in filter_by_area handler: {e}", exc_info=True)
            raise

    async def update_context(
        self, payload: Dict[str, Any], context: Any
    ) -> None:
        """Update conversation context."""
        area = payload.get("area", "")
        if area:
            context.add_category(area)
        context.conversation_stage = "show_results"
