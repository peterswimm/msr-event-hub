#!/usr/bin/env python
"""Comprehensive validation of Adaptive Cards against official schema 1.5."""
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
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return truncated[:last_space] + "..."
    return truncated + "..."

# Generate the carousel card (matching updated browse_all handler)
event_data = get_event_data()
all_projects = event_data.get("projects", [])

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

# === VALIDATION ===
print("=" * 70)
print("ADAPTIVE CARD 1.5 VALIDATION REPORT")
print("=" * 70)

errors = []
warnings = []
info = []

# 1. Top-level schema validation
print("\n[1] TOP-LEVEL PROPERTIES")
print("-" * 70)

if carousel_card.get("type") != "AdaptiveCard":
    errors.append("Missing or invalid 'type' property (must be 'AdaptiveCard')")
else:
    print("✓ type: AdaptiveCard")

if carousel_card.get("version") != "1.5":
    errors.append(f"Invalid schema version: {carousel_card.get('version')} (must be '1.5')")
else:
    print("✓ version: 1.5")

schema = carousel_card.get("$schema", "")
if "https" not in schema:
    errors.append(f"Schema URL must use HTTPS: {schema}")
elif "adaptive-card.json" not in schema:
    errors.append(f"Invalid schema URL: {schema}")
else:
    print("✓ $schema: HTTPS with adaptive-card.json")

if not carousel_card.get("fallbackText"):
    warnings.append("Missing 'fallbackText' property (accessibility requirement)")
else:
    print(f"✓ fallbackText: {carousel_card.get('fallbackText')[:50]}...")

# 2. Body validation
print("\n[2] BODY STRUCTURE")
print("-" * 70)

body = carousel_card.get("body", [])
if not body:
    errors.append("Body is empty or missing")
else:
    print(f"✓ Body contains {len(body)} items")
    
    # Define valid property sets
    textblock_props = {'type', 'text', 'size', 'weight', 'color', 'wrap', 'spacing', 'isSubtle', 'horizontalAlignment', 'maxLines', 'fontType'}
    container_props = {'type', 'items', 'separator', 'spacing', 'style', 'selectAction', 'rtl', 'bleed', 'backgroundImage'}
    
    # Valid enum values
    valid_sizes = {'default', 'small', 'medium', 'large', 'extraLarge'}
    valid_weights = {'default', 'lighter', 'bolder'}
    valid_colors = {'default', 'dark', 'light', 'accent', 'good', 'warning', 'attention'}
    valid_spacing = {'default', 'none', 'small', 'medium', 'large', 'extraLarge', 'padding'}
    
    for i, item in enumerate(body):
        item_type = item.get("type")
        
        if item_type == "TextBlock":
            # Check properties
            invalid = set(item.keys()) - textblock_props
            if invalid:
                errors.append(f"TextBlock[{i}]: Invalid properties: {invalid}")
            
            # Check enum values
            if item.get("size") and item.get("size") not in valid_sizes:
                errors.append(f"TextBlock[{i}]: Invalid size '{item.get('size')}' (valid: {valid_sizes})")
            if item.get("weight") and item.get("weight") not in valid_weights:
                errors.append(f"TextBlock[{i}]: Invalid weight '{item.get('weight')}' (valid: {valid_weights})")
            if item.get("color") and item.get("color") not in valid_colors:
                errors.append(f"TextBlock[{i}]: Invalid color '{item.get('color')}' (valid: {valid_colors})")
            if item.get("spacing") and item.get("spacing") not in valid_spacing:
                errors.append(f"TextBlock[{i}]: Invalid spacing '{item.get('spacing')}' (valid: {valid_spacing})")
            
            # Check required text property
            if not item.get("text"):
                errors.append(f"TextBlock[{i}]: Missing required 'text' property")
        
        elif item_type == "Container":
            # Check properties
            invalid = set(item.keys()) - container_props
            if invalid:
                errors.append(f"Container[{i}]: Invalid properties: {invalid}")
            
            # Check spacing enum
            if item.get("spacing") and item.get("spacing") not in valid_spacing:
                errors.append(f"Container[{i}]: Invalid spacing '{item.get('spacing')}' (valid: {valid_spacing})")
            
            # Check nested items
            for j, subitem in enumerate(item.get("items", [])):
                subtype = subitem.get("type")
                if subtype == "TextBlock":
                    invalid = set(subitem.keys()) - textblock_props
                    if invalid:
                        errors.append(f"Container[{i}].TextBlock[{j}]: Invalid properties: {invalid}")
                    if subitem.get("size") and subitem.get("size") not in valid_sizes:
                        errors.append(f"Container[{i}].TextBlock[{j}]: Invalid size '{subitem.get('size')}'")
                    if subitem.get("spacing") and subitem.get("spacing") not in valid_spacing:
                        errors.append(f"Container[{i}].TextBlock[{j}]: Invalid spacing '{subitem.get('spacing')}'")

# 3. Actions validation
print("\n[3] ACTIONS")
print("-" * 70)

actions = carousel_card.get("actions", [])
max_actions = 5  # From official host config

if len(actions) > max_actions:
    errors.append(f"Too many actions: {len(actions)} (max allowed: {max_actions})")
else:
    print(f"✓ Actions count: {len(actions)} (max allowed: {max_actions})")

valid_action_types = {'Action.Submit', 'Action.OpenUrl', 'Action.Execute'}
action_props = {'type', 'title', 'data', 'id'}

for i, action in enumerate(actions):
    atype = action.get("type")
    if atype not in valid_action_types:
        errors.append(f"Action[{i}]: Invalid type '{atype}' (valid: {valid_action_types})")
    if not action.get("title"):
        errors.append(f"Action[{i}]: Missing required 'title'")

# 4. JSON serializability
print("\n[4] JSON SERIALIZATION")
print("-" * 70)

try:
    json_str = json.dumps(carousel_card)
    print(f"✓ Card is JSON serializable ({len(json_str)} bytes)")
except Exception as e:
    errors.append(f"JSON serialization failed: {e}")

# === REPORT ===
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

if errors:
    print(f"\n❌ ERRORS ({len(errors)}):")
    for i, err in enumerate(errors, 1):
        print(f"  {i}. {err}")

if warnings:
    print(f"\n⚠️  WARNINGS ({len(warnings)}):")
    for i, warn in enumerate(warnings, 1):
        print(f"  {i}. {warn}")

if not errors:
    print("\n✅ CARD IS VALID!")
    print("\nCard Details:")
    print(f"  - Version: 1.5 (official schema)")
    print(f"  - Actions: {len(actions)} / {max_actions} allowed")
    print(f"  - Body items: {len(body)} (2 headers + {len(project_items)} project cards)")
    print(f"  - Projects displayed: {len(project_items)} of {len(all_projects)} total")
else:
    print(f"\n❌ VALIDATION FAILED: {len(errors)} critical issue(s) found")
    sys.exit(1)

