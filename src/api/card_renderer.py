"""
Adaptive Card utilities for rendering structured responses.
Supports standalone Adaptive Cards without Bot Framework dependency.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from string import Template


class AdaptiveCardRenderer:
    """Renders Adaptive Cards from templates with data binding."""
    
    def __init__(self, templates_dir: str = ".data/cards"):
        self.templates_dir = Path(templates_dir)
        self._template_cache: Dict[str, Dict[str, Any]] = {}
    
    def _load_template(self, template_name: str) -> Dict[str, Any]:
        """Load and cache a card template."""
        if template_name in self._template_cache:
            return self._template_cache[template_name]
        
        template_path = self.templates_dir / f"{template_name}.json"
        if not template_path.exists():
            raise FileNotFoundError(f"Card template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        self._template_cache[template_name] = template
        return template
    
    def _substitute_variables(self, obj: Any, data: Dict[str, Any]) -> Any:
        """Recursively substitute template variables in JSON structure."""
        if isinstance(obj, dict):
            return {k: self._substitute_variables(v, data) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_variables(item, data) for item in obj]
        elif isinstance(obj, str):
            # Use string.Template for ${variable} substitution
            try:
                template = Template(obj)
                return template.safe_substitute(data)
            except (KeyError, ValueError):
                return obj
        else:
            return obj
    
    def render_project_card(
        self,
        title: str,
        research_area: str,
        description: str,
        team_members: str,
        placement: str = "TBD",
        equipment: str = "Standard",
        details_url: str = "#"
    ) -> Dict[str, Any]:
        """Render a project card with given data."""
        template = self._load_template("project_card_template")
        
        data = {
            "title": title,
            "researchArea": research_area,
            "description": description,
            "teamMembers": team_members,
            "placement": placement,
            "equipment": equipment,
            "detailsUrl": details_url
        }
        
        return self._substitute_variables(template, data)
    
    def render_session_card(
        self,
        title: str,
        session_type: str,
        description: str,
        start_time: str,
        end_time: str,
        speakers: str,
        location: str = "TBD",
        agenda_url: str = "#"
    ) -> Dict[str, Any]:
        """Render a session card with given data."""
        template = self._load_template("session_card_template")
        
        data = {
            "title": title,
            "sessionType": session_type,
            "description": description,
            "startTime": start_time,
            "endTime": end_time,
            "speakers": speakers,
            "location": location,
            "agendaUrl": agenda_url
        }
        
        return self._substitute_variables(template, data)
    
    def render_welcome_card(self) -> Dict[str, Any]:
        """Render the welcome card with action buttons."""
        template = self._load_template("welcome_card_template")
        return template
    
    def render_category_select_card(
        self,
        ai_count: int = 0,
        systems_count: int = 0,
        hci_count: int = 0,
        security_count: int = 0
    ) -> Dict[str, Any]:
        """Render category selection card with project counts."""
        template = self._load_template("category_select_card_template")
        
        data = {
            "ai_count": str(ai_count),
            "systems_count": str(systems_count),
            "hci_count": str(hci_count),
            "security_count": str(security_count)
        }
        
        return self._substitute_variables(template, data)
    
    def render_project_detail_card(
        self,
        project_id: str,
        title: str,
        research_area: str,
        description: str,
        team_members: str,
        placement: str = "TBD",
        equipment: str = "Standard",
        recording_status: str = "Not submitted",
        target_audience: str = "General"
    ) -> Dict[str, Any]:
        """Render a detailed project information card."""
        template = self._load_template("project_detail_card_template")
        
        # Truncate description if too long
        if len(description) > 500:
            description = description[:497] + "..."
        
        data = {
            "projectId": project_id,
            "title": title,
            "researchArea": research_area,
            "description": description,
            "teamMembers": team_members if team_members else "Team info not available",
            "placement": placement,
            "equipment": equipment if equipment else "No special equipment needed",
            "recordingStatus": recording_status,
            "targetAudience": target_audience if target_audience else "General audience"
        }
        
        return self._substitute_variables(template, data)
    
    def create_card_attachment(self, card_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a Bot Framework-compatible card attachment.
        Useful for Teams SDK endpoints and bot responses.
        """
        return {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": card_json
        }


# Singleton instance for convenience
_renderer: Optional[AdaptiveCardRenderer] = None


def get_card_renderer() -> AdaptiveCardRenderer:
    """Get or create the global card renderer instance."""
    global _renderer
    if _renderer is None:
        _renderer = AdaptiveCardRenderer()
    return _renderer
