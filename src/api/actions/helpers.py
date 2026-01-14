"""
Shared utilities for action handlers.

Eliminates code duplication across handlers for common operations:
- Streaming response generation
- Project filtering
- Carousel card building
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, AsyncIterator

logger = logging.getLogger(__name__)


async def create_streaming_response(
    text: str,
    card: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> AsyncIterator[str]:
    """
    Create an async generator for SSE streaming response.
    
    Eliminates ~40 lines of duplicate boilerplate per handler.
    
    Args:
        text: Response text (delta)
        card: Adaptive card dictionary (optional)
        context: Conversation context dict (optional)
        
    Yields:
        SSE formatted data lines
        
    Example:
        response = StreamingResponse(
            create_streaming_response("Found 5 projects", card=my_card),
            media_type="text/event-stream"
        )
    """
    payload = {
        "delta": text,
    }

    if card is not None:
        payload["adaptive_card"] = card

    if context is not None:
        payload["context"] = context

    yield f"data: {json.dumps(payload)}\n\n"
    yield "data: [DONE]\n\n"


def apply_filter(
    projects: List[Dict[str, Any]],
    filter_func: Callable[[Dict[str, Any]], bool],
) -> List[Dict[str, Any]]:
    """
    Apply a filter function to projects list.
    
    Consolidates 7 separate filter implementations into single utility.
    
    Args:
        projects: List of project dictionaries
        filter_func: Function returning True for matching projects
        
    Returns:
        Filtered project list
        
    Example:
        filtered = apply_filter(
            projects,
            lambda p: p.get("status") == "active"
        )
    """
    return [p for p in projects if filter_func(p)]


def safe_text(value: Any, default: str = " ") -> str:
    """
    Safely convert a value to text, ensuring non-empty strings.
    
    Adaptive Cards require all text fields to be non-empty strings.
    Returns a space if the value is None, empty, or False.
    
    Args:
        value: Value to convert
        default: Default value if empty (default is a space)
        
    Returns:
        Non-empty string
    """
    if not value:
        return default
    text = str(value).strip()
    return text if text else default


def safe_truncate(text: str, max_length: int = 120) -> str:
    """
    Safely truncate text at word boundary.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    last_space = truncated.rfind(" ")

    if last_space > 0:
        return truncated[:last_space] + "..."

    return truncated + "..."


def build_project_carousel(
    projects: List[Dict[str, Any]],
    title: str = "Projects",
    subtitle: Optional[str] = None,
    max_items: int = 10,
    actions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Build an Adaptive Card carousel for projects.
    
    Unifies carousel generation for browse_all, researcher_search, category_select.
    
    Args:
        projects: List of project dictionaries
        title: Card title
        subtitle: Optional subtitle (auto-generated if None)
        max_items: Maximum projects to display
        actions: Optional list of action buttons
        
    Returns:
        Adaptive Card dictionary
    """
    # Limit to max_items
    displayed = projects[:max_items]

    # Build carousel pages (one card per project)
    if subtitle is None:
        subtitle = f"Showing {len(displayed)} project{'s' if len(displayed) != 1 else ''}"

    # Default actions
    if actions is None:
        actions = [
            {
                "type": "Action.Submit",
                "title": "Filter by Area",
                "data": {"action": "filter_by_area"},
            },
            {
                "type": "Action.Submit",
                "title": "Recent Updates",
                "data": {"action": "recent_projects"},
            },
            {
                "type": "Action.Submit",
                "title": "Today's Agenda",
                "data": {"action": "hourly_agenda"},
            },
        ]

    # Build carousel pages (one card per project)
    carousel_pages = []
    for idx, proj in enumerate(displayed):
        team = safe_text(", ".join(
            [
                m.get("displayName", m.get("name", ""))
                for m in proj.get("team", [])
            ]
        ), "No team info")
        desc = safe_text(safe_truncate(proj.get("description", ""), 200), "Description unavailable")
        name = safe_text(proj.get("name", ""), "Untitled Project")
        area = safe_text(proj.get("researchArea", ""), "General")
        
        carousel_pages.append({
            "type": "AdaptiveCard",
            "body": [
                {
                    "type": "TextBlock",
                    "text": name,
                    "size": "large",
                    "weight": "bolder",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": area,
                    "size": "small",
                    "color": "accent",
                    "spacing": "small"
                },
                {
                    "type": "TextBlock",
                    "text": desc,
                    "wrap": True,
                    "spacing": "medium"
                },
                {
                    "type": "TextBlock",
                    "text": f"👥 {team}",
                    "size": "small",
                    "spacing": "medium",
                    "isSubtle": True
                }
            ]
        })

    # Build card with Carousel element
    return {
        "type": "AdaptiveCard",
        "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.6",
        "id": "carousel_card",
        "fallbackText": f"{title} - {len(displayed)} projects",
        "body": [
            {
                "type": "TextBlock",
                "id": "carousel_title",
                "text": safe_text(title, "Projects"),
                "size": "large",
                "weight": "bolder",
                "spacing": "none",
            },
            {
                "type": "TextBlock",
                "id": "carousel_subtitle",
                "text": safe_text(subtitle, f"Showing {len(displayed)} project{'s' if len(displayed) != 1 else ''}"),
                "size": "small",
                "color": "accent",
                "spacing": "small"
            },
            {
                "type": "Carousel",
                "id": "projects_carousel",
                "timer": 0,
                "pages": carousel_pages
            }
        ],
        "actions": [
            {**action, "id": f"action_{idx}"} 
            for idx, action in enumerate(actions)
        ],
    }


def build_error_card(
    error_message: str, action: Optional[str] = None
) -> Dict[str, Any]:
    """
    Build an error card for failed actions.
    
    Args:
        error_message: Human-readable error message
        action: Action that failed (optional)
        
    Returns:
        Adaptive Card dictionary
    """
    body = [
        {
            "type": "TextBlock",
            "id": "error_title",
            "text": "⚠️ Something went wrong",
            "size": "large",
            "weight": "bolder",
            "color": "attention",
        },
        {"type": "TextBlock", "id": "error_message", "text": safe_text(error_message, "An error occurred"), "wrap": True},
    ]

    if action:
        body.append(
            {
                "type": "TextBlock",
                "id": "error_action",
                "text": safe_text(f"Action: {action}", " "),
                "size": "small",
                "isSubtle": True,
            }
        )

    return {
        "type": "AdaptiveCard",
        "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "id": "error_card",
        "fallbackText": f"Error: {error_message}",
        "body": body,
        "actions": [
            {
                "type": "Action.Submit",
                "id": "action_try_again",
                "title": "Try Again",
                "data": {"action": "browse_all"},
            },
        ],
    }


def format_project_list(projects: List[Dict[str, Any]], limit: int = 5) -> str:
    """
    Format projects as markdown list for text response.
    
    Args:
        projects: List of projects
        limit: Max projects to list
        
    Returns:
        Markdown formatted list
    """
    if not projects:
        return "No projects found."

    lines = []
    for i, proj in enumerate(projects[:limit], 1):
        name = proj.get("name", "Untitled")
        area = proj.get("researchArea", "General")
        lines.append(f"{i}. **{name}** - {area}")

    if len(projects) > limit:
        lines.append(f"\n... and {len(projects) - limit} more projects")

    return "\n".join(lines)


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    """Safely parse ISO datetime strings including Z suffix."""
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except Exception:
        return None


def _format_time_range(schedule: Dict[str, Any], timezone_label: str = "UTC") -> str:
    """Format start/end time range for display."""
    start_raw = schedule.get("startDate") or schedule.get("startDateTime")
    end_raw = schedule.get("endDate") or schedule.get("endDateTime")

    start_dt = _parse_iso_datetime(start_raw)
    end_dt = _parse_iso_datetime(end_raw)

    if start_dt and end_dt:
        start_str = start_dt.strftime("%I:%M %p").lstrip("0")
        end_str = end_dt.strftime("%I:%M %p").lstrip("0")
        return f"{start_str} - {end_str} {timezone_label}"
    if start_dt:
        start_str = start_dt.strftime("%I:%M %p").lstrip("0")
        return f"{start_str} {timezone_label}"
    return "Time TBC"


def build_agenda_card(
    sessions: List[Dict[str, Any]],
    title: str = "Today's agenda",
    timezone_label: str = "PT",
    max_items: int = 8,
) -> Dict[str, Any]:
    """Build an agenda card using session data."""
    sorted_sessions = sorted(
        sessions,
        key=lambda s: (s.get("schedule", {}).get("startDate") or s.get("schedule", {}).get("startDateTime", "")),
    )
    displayed = sorted_sessions[:max_items]

    items: List[Dict[str, Any]] = []
    for sess in displayed:
        schedule = sess.get("schedule", {})
        time_range = _format_time_range(schedule, timezone_label)
        location = safe_text(schedule.get("location", "Location tbd"), "Location tbd")
        title_text = safe_text(sess.get("title", "Session"), "Session")
        speakers = ", ".join(
            [safe_text(p.get("displayName", p.get("name", "")), "") for p in sess.get("speakers", [])]
        ) or "Speakers tbd"

        items.append(
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": time_range,
                                "size": "small",
                                "color": "accent",
                                "wrap": True,
                            }
                        ],
                        "verticalContentAlignment": "Center",
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": title_text,
                                "weight": "bolder",
                                "wrap": True,
                            },
                            {
                                "type": "TextBlock",
                                "text": f"📍 {location}",
                                "spacing": "small",
                                "wrap": True,
                            },
                            {
                                "type": "TextBlock",
                                "text": f"🎤 {speakers}",
                                "size": "small",
                                "spacing": "none",
                                "wrap": True,
                                "isSubtle": True,
                            },
                        ],
                    },
                ],
                "separator": True,
                "spacing": "medium",
            }
        )

    return {
        "type": "AdaptiveCard",
        "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.6",
        "id": "agenda_card",
        "fallbackText": f"{title} ({len(displayed)} items)",
        "body": [
            {
                "type": "TextBlock",
                "text": safe_text(title, "Agenda"),
                "size": "large",
                "weight": "bolder",
                "spacing": "none",
            },
            {
                "type": "TextBlock",
                "text": f"Next {len(displayed)} sessions — times in {timezone_label}",
                "size": "small",
                "color": "accent",
                "spacing": "small",
            },
            {
                "type": "Container",
                "style": "default",
                "items": items or [
                    {
                        "type": "TextBlock",
                        "text": "No sessions available.",
                        "isSubtle": True,
                    }
                ],
                "spacing": "medium",
            },
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Presenter carousel",
                "data": {"action": "presenter_carousel"},
            },
            {
                "type": "Action.Submit",
                "title": "Organizer tools",
                "data": {"action": "organizer_tools"},
            },
        ],
    }


def build_presenter_carousel(
    sessions: List[Dict[str, Any]],
    max_presenters: int = 6,
) -> Dict[str, Any]:
    """Build a carousel spotlighting presenters derived from sessions."""
    presenters: Dict[str, Dict[str, Any]] = {}
    for sess in sessions:
        schedule = sess.get("schedule", {})
        time_range = _format_time_range(schedule, "PT")
        for person in sess.get("speakers", []):
            name = safe_text(person.get("displayName", person.get("name", "Presenter")), "Presenter")
            presenters.setdefault(name, {"sessions": []})["sessions"].append(
                {
                    "title": safe_text(sess.get("title", "Session"), "Session"),
                    "time": time_range,
                    "location": safe_text(schedule.get("location", "Location tbd"), "Location tbd"),
                }
            )

    spotlight = list(presenters.items())[:max_presenters]
    pages: List[Dict[str, Any]] = []
    for name, info in spotlight:
        session_lines = []
        for slot in info["sessions"][:3]:
            session_lines.append(f"• {slot['title']} ({slot['time']}) — {slot['location']}")
        summary = "\n".join(session_lines) if session_lines else "Sessions coming soon"

        pages.append(
            {
                "type": "AdaptiveCard",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": name,
                        "size": "large",
                        "weight": "bolder",
                        "wrap": True,
                    },
                    {
                        "type": "TextBlock",
                        "text": "Presenter spotlight",
                        "color": "accent",
                        "spacing": "small",
                    },
                    {
                        "type": "TextBlock",
                        "text": summary,
                        "wrap": True,
                        "spacing": "medium",
                    },
                ],
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Bookmark presenter (stub)",
                        "data": {"action": "bookmark", "presenter": name},
                    }
                ],
            }
        )

    return {
        "type": "AdaptiveCard",
        "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.6",
        "id": "presenter_carousel_card",
        "fallbackText": f"Presenter carousel ({len(spotlight)} presenters)",
        "body": [
            {
                "type": "TextBlock",
                "text": "Presenter carousel",
                "size": "large",
                "weight": "bolder",
                "spacing": "none",
            },
            {
                "type": "TextBlock",
                "text": "Preview of key speakers (stub)",
                "size": "small",
                "color": "accent",
                "spacing": "small",
            },
            {
                "type": "Carousel",
                "id": "presenters_carousel",
                "timer": 0,
                "pages": pages or [
                    {
                        "type": "AdaptiveCard",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": "No presenters available yet.",
                                "isSubtle": True,
                            }
                        ],
                    }
                ],
            },
        ],
    }
