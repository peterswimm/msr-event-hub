"""
Shared utilities for action handlers.

Eliminates code duplication across handlers for common operations:
- Streaming response generation
- Project filtering
- Carousel card building
"""

import json
import logging
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

    # Build project items
    project_items = []
    for idx, proj in enumerate(displayed):
        team = ", ".join(
            [
                m.get("displayName", m.get("name", ""))
                for m in proj.get("team", [])
            ]
        )
        desc = safe_truncate(proj.get("description", ""), 120)

        project_items.append(
            {
                "type": "Container",
                "separator": idx > 0,
                "spacing": "medium",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": proj.get("name", "Untitled"),
                        "size": "medium",
                        "weight": "bolder",
                        "wrap": True,
                        "spacing": "none",
                    },
                    {
                        "type": "TextBlock",
                        "text": proj.get("researchArea", "General"),
                        "size": "small",
                        "color": "accent",
                    },
                    {
                        "type": "TextBlock",
                        "text": desc,
                        "wrap": True,
                        "spacing": "small",
                    },
                    {
                        "type": "TextBlock",
                        "text": f"👥 {team}",
                        "size": "small",
                        "spacing": "small",
                        "isSubtle": True,
                    },
                ],
            }
        )

    # Default subtitle
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
                "title": "With Recording",
                "data": {"action": "recording_filter", "available": "true"},
            },
        ]

    # Build card
    return {
        "type": "AdaptiveCard",
        "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "fallbackText": f"{title} - {len(displayed)} projects",
        "body": [
            {
                "type": "TextBlock",
                "text": title,
                "size": "large",
                "weight": "bolder",
                "spacing": "none",
            },
            {"type": "TextBlock", "text": subtitle, "size": "small", "color": "accent"},
        ]
        + project_items,
        "actions": actions,
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
            "text": "⚠️ Something went wrong",
            "size": "large",
            "weight": "bolder",
            "color": "attention",
        },
        {"type": "TextBlock", "text": error_message, "wrap": True},
    ]

    if action:
        body.append(
            {
                "type": "TextBlock",
                "text": f"Action: {action}",
                "size": "small",
                "isSubtle": True,
            }
        )

    return {
        "type": "AdaptiveCard",
        "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "fallbackText": f"Error: {error_message}",
        "body": body,
        "actions": [
            {
                "type": "Action.Submit",
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
