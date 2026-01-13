#!/usr/bin/env python3
"""
CSV Import Script for RRS Event Data
Converts tests/Untitled-1.csv (Redmond Research Showcase) to JSON format
and merges with existing mock_event_data.json

Usage:
    python scripts/import_rrs_csv.py
    
Environment Variables:
    CSV_INPUT_PATH: Path to input CSV file (default: tests/Untitled-1.csv)
    JSON_OUTPUT_PATH: Path to output JSON file (default: data/mock_event_data.json)
    IMPORT_BACKUP: Create backup before overwriting (default: true)
"""

import csv
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def clean_text(text: str) -> str:
    """Clean and normalize text fields."""
    if not text:
        return ""
    return text.strip().replace('\n', ' ').replace('\r', '')


def parse_team_members(team_str: str) -> List[Dict[str, str]]:
    """Parse team members from comma-separated string."""
    if not team_str:
        return []
    
    members = []
    # Split by comma and clean
    for member in team_str.split(','):
        member = member.strip()
        if member and not member.startswith('#'):  # Skip tags like #Inference2030
            # Handle email format or alias
            if '@' in member:
                email = member
                name = member.split('@')[0].replace('.', ' ').title()
            else:
                email = f"{member}@microsoft.com"
                name = member.replace('.', ' ').title()
            
            members.append({
                "displayName": name,
                "email": email,
                "role": "Team Member"
            })
    
    return members


def parse_equipment(equipment_str: str) -> List[str]:
    """Parse equipment needs into list."""
    if not equipment_str:
        return ["Standard Setup"]
    
    equipment = []
    
    # Check for common equipment patterns
    if "large display" in equipment_str.lower():
        equipment.append("Large Display")
    if "5 x 2" in equipment_str or "5x2" in equipment_str:
        equipment.append("5x2 Table")
    if "monitor" in equipment_str.lower():
        equipment.append("Monitor")
    if "poster" in equipment_str.lower() and "no poster" not in equipment_str.lower():
        equipment.append("Poster Board")
    if "demo" in equipment_str.lower():
        equipment.append("Demo Setup")
    
    return equipment if equipment else ["Standard Setup"]


def convert_csv_to_projects(csv_path: Path) -> List[Dict[str, Any]]:
    """Convert CSV rows to project JSON objects."""
    projects = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Use tab as delimiter (TSV format)
        reader = csv.DictReader(f, delimiter='\t')
        
        for idx, row in enumerate(reader, start=1):
            # Generate project ID
            project_id = f"rrs-proj-{idx:03d}"
            
            # Map CSV columns to project schema
            title = clean_text(row.get('Project Title', ''))
            if not title:
                continue  # Skip rows without title
            
            description = clean_text(row.get('Brief Project Description', ''))
            research_area = clean_text(row.get('Revised Research Category', ''))
            if not research_area:
                research_area = clean_text(row.get('Original Chosen Research Area', ''))
            
            team_members_str = clean_text(row.get('Team Members', ''))
            team = parse_team_members(team_members_str)
            
            equipment_str = clean_text(row.get('Equipment Needs', ''))
            equipment = parse_equipment(equipment_str)
            
            placement = clean_text(row.get('Placement', 'TBD'))
            
            # Determine if large display is required
            large_display = row.get('Large Display', '').strip() == '1'
            monitors_27 = row.get('27\" Monitors', '').strip()
            requires_monitor = large_display or bool(monitors_27)
            
            # Recording status
            recording_submitted = row.get('Recording Submitted', '')
            recording_link = clean_text(row.get('Recording Link', ''))
            recording_permission = "allowed" if recording_submitted else "pending"
            if "declined" in recording_submitted.lower() or "no" in recording_submitted.lower():
                recording_permission = "not_allowed"
            
            # Communication status
            comms_sent = clean_text(row.get('Communication Sent', ''))
            comms_status = "approved" if comms_sent.lower() in ['confirmed', 'yes'] else "pending"
            
            # Inference 2030 flag
            inference2030 = row.get('Inference2030 Flag', '').strip().upper() == 'TRUE'
            
            # Build project object matching Graph schema
            project = {
                "id": project_id,
                "eventId": "rrs-2025",
                "name": title,
                "description": description,
                "researchArea": research_area,
                "team": team,
                "papers": [],  # Could be extracted from Documentation Links if needed
                "repositories": [],  # Could be extracted from Documentation Links
                "maturity": "prototype",  # Default assumption
                "equipment": equipment,
                "placement": placement,
                "requiresMonitor": requires_monitor,
                "recordingPermission": recording_permission,
                "commsStatus": comms_status,
                "tags": ["RRS 2025"] + (["Inference 2030"] if inference2030 else [])
            }
            
            # Add optional fields
            submitter = clean_text(row.get('Submitter', ''))
            if submitter:
                project["submitter"] = submitter
            
            target_audience = clean_text(row.get('Target People or Teams', ''))
            if target_audience:
                project["targetAudience"] = target_audience
            
            doc_links = clean_text(row.get('Documentation Links', ''))
            if doc_links and doc_links != 'None':
                project["documentationLinks"] = [link.strip() for link in doc_links.split(',')]
            
            projects.append(project)
    
    return projects


def merge_with_existing_data(
    new_projects: List[Dict[str, Any]],
    existing_json_path: Path
) -> Dict[str, Any]:
    """Merge new projects with existing event data."""
    
    # Load existing data or create new structure
    if existing_json_path.exists():
        with open(existing_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # Create base structure for RRS event
        data = {
            "event": {
                "id": "rrs-2025",
                "displayName": "Redmond Research Showcase 2025",
                "eventType": "conference",
                "status": "active",
                "startDate": "2025-02-15T09:00:00Z",
                "endDate": "2025-02-15T17:00:00Z",
                "timeZone": "America/Los_Angeles",
                "location": {
                    "displayName": "Microsoft Research - Building 99",
                    "address": {
                        "street": "14820 NE 36th St",
                        "city": "Redmond",
                        "state": "WA",
                        "postalCode": "98052",
                        "countryOrRegion": "United States"
                    }
                }
            },
            "projects": [],
            "sessions": [],
            "people": [],
            "categories": []
        }
    
    # Add new projects (replace existing RRS projects)
    existing_projects = [p for p in data.get("projects", []) if not p.get("id", "").startswith("rrs-")]
    data["projects"] = existing_projects + new_projects
    
    # Extract unique research areas for categories
    categories = set(data.get("categories", []))
    for project in new_projects:
        if project.get("researchArea"):
            categories.add(project["researchArea"])
    data["categories"] = sorted(list(categories))
    
    # Extract unique people from teams
    people_dict = {p["email"]: p for p in data.get("people", [])}
    for project in new_projects:
        for team_member in project.get("team", []):
            email = team_member.get("email")
            if email and email not in people_dict:
                people_dict[email] = {
                    "displayName": team_member.get("displayName", ""),
                    "email": email,
                    "role": "Researcher",
                    "researchAreas": [project.get("researchArea", "")],
                    "projects": [project.get("id")]
                }
    data["people"] = list(people_dict.values())
    
    return data


def main():
    """Main import function."""
    print("=" * 70)
    print("RRS CSV Import Script")
    print("=" * 70)
    
    # Get paths from environment or use defaults
    csv_path = Path(os.getenv('CSV_INPUT_PATH', 'tests/Untitled-1.csv'))
    json_path = Path(os.getenv('JSON_OUTPUT_PATH', 'data/mock_event_data.json'))
    create_backup = os.getenv('IMPORT_BACKUP', 'true').lower() == 'true'
    
    print(f"\nInput CSV: {csv_path}")
    print(f"Output JSON: {json_path}")
    
    # Validate CSV exists
    if not csv_path.exists():
        print(f"\n❌ Error: CSV file not found at {csv_path}")
        return 1
    
    # Create backup if requested
    if create_backup and json_path.exists():
        backup_path = json_path.with_suffix(f'.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        shutil.copy(json_path, backup_path)
        print(f"\n✓ Backup created: {backup_path}")
    
    # Convert CSV to projects
    print(f"\n📄 Reading CSV file...")
    try:
        projects = convert_csv_to_projects(csv_path)
        print(f"✓ Converted {len(projects)} projects from CSV")
    except Exception as e:
        print(f"\n❌ Error parsing CSV: {e}")
        return 1
    
    # Merge with existing data
    print(f"\n🔄 Merging with existing event data...")
    try:
        data = merge_with_existing_data(projects, json_path)
        print(f"✓ Total projects in dataset: {len(data['projects'])}")
        print(f"✓ Total categories: {len(data['categories'])}")
        print(f"✓ Total people: {len(data['people'])}")
    except Exception as e:
        print(f"\n❌ Error merging data: {e}")
        return 1
    
    # Write output
    print(f"\n💾 Writing to {json_path}...")
    try:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✓ Successfully wrote {json_path}")
    except Exception as e:
        print(f"\n❌ Error writing JSON: {e}")
        return 1
    
    print("\n" + "=" * 70)
    print("✅ Import Complete!")
    print("=" * 70)
    print(f"\nImported {len(projects)} RRS projects")
    print(f"Event: {data['event']['displayName']}")
    print(f"Location: {data['event']['location']['displayName']}")
    print(f"\nData ready for mock_data_loader.py and chat queries!")
    
    return 0


if __name__ == "__main__":
    exit(main())
