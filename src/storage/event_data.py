"""
Event data loader for MSR Event Hub.
Provides access to mock project data from JSON files.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from functools import lru_cache


class EventDataLoader:
    """Loads and provides access to event and project data."""
    
    def __init__(self, data_dir: str = ".data"):
        self.data_dir = Path(data_dir)
        self._data_cache: Dict[str, Any] = {}
    
    def _load_json_file(self, filename: str) -> Dict[str, Any]:
        """Load a JSON file from the data directory."""
        if filename in self._data_cache:
            return self._data_cache[filename]
        
        file_path = self.data_dir / filename
        if not file_path.exists():
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._data_cache[filename] = data
            return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load {filename}: {e}")
            return {}
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """Get all projects from mock_event_data.json."""
        data = self._load_json_file("mock_event_data.json")
        return data.get("projects", [])
    
    def get_sessions(self) -> List[Dict[str, Any]]:
        """Get all sessions from mock_event_data.json."""
        data = self._load_json_file("mock_event_data.json")
        return data.get("sessions", [])
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all event data."""
        return self._load_json_file("mock_event_data.json")
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific project by ID."""
        projects = self.get_projects()
        for project in projects:
            if project.get("id") == project_id:
                return project
        return None
    
    def filter_projects_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Filter projects by research area/category."""
        projects = self.get_projects()
        category_lower = category.lower()
        
        filtered = []
        for project in projects:
            area = project.get("researchArea", "").lower()
            if category_lower in area:
                filtered.append(project)
        
        return filtered
    
    def filter_projects_by_team_member(self, name: str) -> List[Dict[str, Any]]:
        """Filter projects by team member name."""
        projects = self.get_projects()
        name_lower = name.lower()
        
        filtered = []
        for project in projects:
            team = project.get("team", [])
            for member in team:
                member_name = member.get("name", "").lower()
                if name_lower in member_name:
                    filtered.append(project)
                    break
        
        return filtered
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """Search projects by keyword in title or description."""
        projects = self.get_projects()
        query_lower = query.lower()
        
        filtered = []
        for project in projects:
            title = project.get("name", "").lower()
            desc = project.get("description", "").lower()
            area = project.get("researchArea", "").lower()
            
            if query_lower in title or query_lower in desc or query_lower in area:
                filtered.append(project)
        
        return filtered
    
    def get_category_counts(self) -> Dict[str, int]:
        """Get project counts by research area."""
        projects = self.get_projects()
        counts: Dict[str, int] = {}
        
        for project in projects:
            area = project.get("researchArea", "Other")
            counts[area] = counts.get(area, 0) + 1
        
        return counts


# Global singleton instance
_event_data_loader: Optional[EventDataLoader] = None


@lru_cache(maxsize=1)
def get_event_data_loader() -> EventDataLoader:
    """Get or create the global event data loader instance."""
    global _event_data_loader
    if _event_data_loader is None:
        _event_data_loader = EventDataLoader()
    return _event_data_loader


def get_event_data() -> Dict[str, Any]:
    """Convenience function to get all event data."""
    loader = get_event_data_loader()
    return loader.get_all_data()
