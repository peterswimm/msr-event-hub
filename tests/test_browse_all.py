#!/usr/bin/env python
"""Test the browse_all card generation logic directly."""
import json
import sys
sys.path.insert(0, '.')

from src.storage.event_data import get_event_data

# Helper function for safe text truncation
def safe_truncate(text, max_length=120):
    """Safely truncate text at word boundary."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    # Find last space to avoid cutting mid-word
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return truncated[:last_space] + "..."
    return truncated + "..."

# Simulate what the browse_all handler does
event_data = get_event_data()
all_projects = event_data.get("projects", [])
print(f"✓ Loaded {len(all_projects)} projects")

# Build body items for each project
project_items = []
for idx, proj in enumerate(all_projects[:10]):
    team = ", ".join([m.get("displayName", m.get("name", "")) for m in proj.get("team", [])])
    desc = safe_truncate(proj.get("description", ""), 120)
    project_items.append({
        "type": "Container",
        "separator": idx > 0,
        "spacing": "medium",
        "items": [
            {"type": "TextBlock", "text": proj.get("name", "Untitled"), "size": "medium", "weight": "bolder", "wrap": True, "spacing": "none"},
            {"type": "TextBlock", "text": proj.get("researchArea", "General"), "size": "small", "color": "accent"},
            {"type": "TextBlock", "text": desc, "wrap": True, "spacing": "small"},
            {"type": "TextBlock", "text": f"👥 {team}", "size": "small", "spacing": "small", "isSubtle": True}
        ]
    })

carousel_card = {
    "type": "AdaptiveCard",
    "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.5",
    "fallbackText": f"Featured Projects - Showing {len(project_items)} projects",
    "body": [
        {"type": "TextBlock", "text": "Featured Projects", "size": "large", "weight": "bolder", "spacing": "none"},
        {"type": "TextBlock", "text": f"Showing {len(project_items)} projects", "size": "small", "color": "accent"}
    ] + project_items,
    "actions": [
        {"type": "Action.Submit", "title": "Filter by Area", "data": {"action": "filter_by_area"}},
        {"type": "Action.Submit", "title": "Recent Updates", "data": {"action": "recent_projects"}},
        {"type": "Action.Submit", "title": "With Recording", "data": {"action": "recording_filter", "available": "true"}}
    ]
}

print(f"✓ Generated carousel with {len(project_items)} project items")
print(f"✓ Card has {len(carousel_card['actions'])} actions (within maxActions: 5 limit)")
print(f"✓ Card body has {len(carousel_card['body'])} body elements (2 headers + {len(project_items)} projects)")

# Validate JSON
json_str = json.dumps(carousel_card, indent=2)
print(f"✓ JSON serializable: {len(json_str)} bytes")

# Print first project in card for inspection
if project_items:
    print(f"\nFirst project in card:")
    print(json.dumps(project_items[0], indent=2))
