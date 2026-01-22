"""
Adaptive Card utilities for rendering structured responses.
Supports standalone Adaptive Cards without Bot Framework dependency.

Enhanced with:
- Data binding support ($data syntax)
- Conditional rendering ($when property)
- Fallback text for all cards
- Advanced data substitution
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from string import Template
import re


class AdaptiveCardRenderer:
    """Renders Adaptive Cards from templates with advanced data binding and conditional rendering."""
    
    def __init__(self, templates_dir: str = "data/cards"):
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
    
    def _evaluate_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """
        Evaluate a conditional expression.
        Supports: $data.field == "value", $data.field != "value", $data.field, !$data.field
        """
        if not condition:
            return True
        
        # Replace $data.field with actual values
        def replace_data_refs(match):
            field_path = match.group(1)
            value = self._get_nested_value(data, field_path)
            if isinstance(value, str):
                return f'"{value}"'
            elif isinstance(value, bool):
                return str(value)
            elif value is None:
                return 'None'
            else:
                return str(value)
        
        # Replace $data.field references with values
        condition = re.sub(r'\$data\.([a-zA-Z0-9_.]+)', replace_data_refs, condition)
        
        try:
            # Simple safe evaluation for basic comparisons
            # Only allow safe operators: ==, !=, and, or, not, True, False, None
            allowed_tokens = {'==', '!=', 'and', 'or', 'not', 'True', 'False', 'None', '(', ')'}
            tokens = re.findall(r'[a-zA-Z_]+|[!<>=]+|\d+|"[^"]*"', condition)
            
            # Check if all tokens are safe
            for token in tokens:
                if token not in allowed_tokens and not (token.startswith('"') or token.isdigit()):
                    return True  # If unsafe, default to showing the element
            
            # Evaluate the condition
            return eval(condition, {"__builtins__": {}})
        except Exception:
            # If evaluation fails, default to showing the element
            return True
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from data using dot notation (e.g., 'user.name')."""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value
    
    def _substitute_data_binding(self, text: str, data: Dict[str, Any]) -> str:
        """
        Substitute $data.field references with actual values.
        Supports nested paths like $data.user.name
        """
        def replace_binding(match):
            field_path = match.group(1)
            value = self._get_nested_value(data, field_path)
            return str(value) if value is not None else ""
        
        # Replace $data.field with actual values
        return re.sub(r'\$data\.([a-zA-Z0-9_.]+)', replace_binding, text)
    
    def _process_conditional_elements(self, obj: Any, data: Dict[str, Any]) -> Any:
        """
        Process elements with $when property for conditional rendering.
        Elements with $when that evaluate to false are removed.
        """
        if isinstance(obj, dict):
            # Check for $when condition
            if "$when" in obj:
                condition = obj["$when"]
                if not self._evaluate_condition(condition, data):
                    return None  # Remove this element
                # Remove the $when property after evaluation
                obj = {k: v for k, v in obj.items() if k != "$when"}
            
            # Process nested objects
            result = {}
            for k, v in obj.items():
                processed = self._process_conditional_elements(v, data)
                if processed is not None:
                    result[k] = processed
            return result
        elif isinstance(obj, list):
            # Process list items and filter out None values
            return [
                processed
                for item in obj
                if (processed := self._process_conditional_elements(item, data)) is not None
            ]
        else:
            return obj
    
    def _substitute_variables(self, obj: Any, data: Dict[str, Any]) -> Any:
        """
        Recursively substitute template variables in JSON structure.
        Supports both ${variable} and $data.field syntax.
        """
        if isinstance(obj, dict):
            return {k: self._substitute_variables(v, data) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_variables(item, data) for item in obj]
        elif isinstance(obj, str):
            # First, handle $data.field syntax
            result = self._substitute_data_binding(obj, data)
            
            # Then, handle ${variable} syntax for backwards compatibility
            try:
                template = Template(result)
                return template.safe_substitute(data)
            except (KeyError, ValueError):
                return result
        else:
            return obj
    
    def render_with_data(self, template_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render a card template with data binding and conditional rendering.
        
        Args:
            template_name: Name of the template file (without .json extension)
            data: Data dictionary for substitution and conditionals
        
        Returns:
            Rendered card JSON with substitutions applied and conditions evaluated
        """
        template = self._load_template(template_name)
        
        # First, process conditional elements ($when)
        template = self._process_conditional_elements(template, data)
        
        # Then, substitute variables ($data.field and ${variable})
        return self._substitute_variables(template, data)
    
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
        # Always reload welcome card to pick up latest template changes
        self._template_cache.pop("welcome_card_template", None)
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
