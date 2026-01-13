"""
Mock data loader for local development and testing.
Provides query operations against hardcoded JSON event data.
"""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class MockDataLoader:
    """Load and query mock event data from JSON file."""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path)
        self.data: Dict[str, Any] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Load JSON data from file."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Mock data file not found: {self.data_path}")
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
    
    def get_event(self) -> Optional[Dict[str, Any]]:
        """Get the main event information."""
        return self.data.get('event')
    
    def get_projects(
        self,
        research_area: Optional[str] = None,
        search_query: Optional[str] = None,
        equipment: Optional[str] = None,
        requires_monitor: Optional[bool] = None,
        recording_permission: Optional[str] = None,
        comms_status: Optional[str] = None,
        maturity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query projects with optional filters.
        
        Args:
            research_area: Filter by research area (e.g., "AI", "Quantum Computing")
            search_query: Search in name/description (case-insensitive)
            equipment: Filter by equipment type
            requires_monitor: Filter by monitor requirement
            recording_permission: Filter by recording permission ("allowed", "restricted", "not_allowed")
            comms_status: Filter by comms status ("approved", "pending", "not_submitted")
            maturity: Filter by maturity level
        """
        projects = self.data.get('projects', [])
        
        # Apply filters
        if research_area:
            projects = [p for p in projects if p.get('researchArea', '').lower() == research_area.lower()]
        
        if search_query:
            query = search_query.lower()
            projects = [
                p for p in projects
                if query in p.get('name', '').lower() or query in p.get('description', '').lower()
            ]
        
        if equipment:
            projects = [
                p for p in projects
                if equipment.lower() in [e.lower() for e in p.get('equipment', [])]
            ]
        
        if requires_monitor is not None:
            projects = [p for p in projects if p.get('requiresMonitor') == requires_monitor]
        
        if recording_permission:
            projects = [
                p for p in projects
                if p.get('recordingPermission', '').lower() == recording_permission.lower()
            ]
        
        if comms_status:
            projects = [
                p for p in projects
                if p.get('commsStatus', '').lower() == comms_status.lower()
            ]
        
        if maturity:
            projects = [p for p in projects if p.get('maturity', '').lower() == maturity.lower()]
        
        return projects
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific project by ID."""
        projects = self.data.get('projects', [])
        for project in projects:
            if project.get('id') == project_id:
                return project
        return None
    
    def search_projects_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Search projects by name (case-insensitive partial match)."""
        projects = self.data.get('projects', [])
        name_lower = name.lower()
        return [p for p in projects if name_lower in p.get('name', '').lower()]
    
    def get_sessions(
        self,
        session_type: Optional[str] = None,
        target_audience: Optional[str] = None,
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query sessions with optional filters.
        
        Args:
            session_type: Filter by session type ("keynote", "workshop", "panel", "demo")
            target_audience: Filter by target audience ("general", "technical", "leadership")
            search_query: Search in title/description (case-insensitive)
        """
        sessions = self.data.get('sessions', [])
        
        if session_type:
            sessions = [s for s in sessions if s.get('sessionType', '').lower() == session_type.lower()]
        
        if target_audience:
            sessions = [s for s in sessions if s.get('targetAudience', '').lower() == target_audience.lower()]
        
        if search_query:
            query = search_query.lower()
            sessions = [
                s for s in sessions
                if query in s.get('title', '').lower() or query in s.get('description', '').lower()
            ]
        
        return sessions
    
    def get_session_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific session by ID."""
        sessions = self.data.get('sessions', [])
        for session in sessions:
            if session.get('id') == session_id:
                return session
        return None
    
    def search_people(
        self,
        name: Optional[str] = None,
        research_area: Optional[str] = None,
        role: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search people with optional filters.
        
        Args:
            name: Search by name (case-insensitive partial match)
            research_area: Filter by research area
            role: Filter by role
        """
        people = self.data.get('people', [])
        
        if name:
            name_lower = name.lower()
            people = [p for p in people if name_lower in p.get('displayName', '').lower()]
        
        if research_area:
            area_lower = research_area.lower()
            people = [
                p for p in people
                if area_lower in [a.lower() for a in p.get('researchAreas', [])]
            ]
        
        if role:
            people = [p for p in people if p.get('role', '').lower() == role.lower()]
        
        return people
    
    def get_categories(self) -> List[str]:
        """Get all research area categories."""
        return self.data.get('categories', [])
    
    def get_projects_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all projects in a specific research area category."""
        return self.get_projects(research_area=category)
    
    def get_logistics_summary(self) -> Dict[str, Any]:
        """
        Get summary of logistics information across all projects.
        Useful for equipment inventory, placement maps, recording permissions.
        """
        projects = self.data.get('projects', [])
        
        # Count equipment types
        equipment_counts: Dict[str, int] = {}
        for project in projects:
            for item in project.get('equipment', []):
                equipment_counts[item] = equipment_counts.get(item, 0) + 1
        
        # Count placement zones
        placement_counts: Dict[str, int] = {}
        for project in projects:
            placement = project.get('placement', 'Unknown')
            placement_counts[placement] = placement_counts.get(placement, 0) + 1
        
        # Count recording permissions
        recording_counts = {
            'allowed': len([p for p in projects if p.get('recordingPermission') == 'allowed']),
            'restricted': len([p for p in projects if p.get('recordingPermission') == 'restricted']),
            'not_allowed': len([p for p in projects if p.get('recordingPermission') == 'not_allowed'])
        }
        
        # Count comms status
        comms_counts = {
            'approved': len([p for p in projects if p.get('commsStatus') == 'approved']),
            'pending': len([p for p in projects if p.get('commsStatus') == 'pending']),
            'not_submitted': len([p for p in projects if p.get('commsStatus') == 'not_submitted'])
        }
        
        # Monitor requirements
        monitor_counts = {
            'requires_monitor': len([p for p in projects if p.get('requiresMonitor') == True]),
            'no_monitor': len([p for p in projects if p.get('requiresMonitor') == False])
        }
        
        return {
            'total_projects': len(projects),
            'equipment': equipment_counts,
            'placements': placement_counts,
            'recording_permissions': recording_counts,
            'comms_status': comms_counts,
            'monitor_requirements': monitor_counts
        }


# Global instance (initialized when config loaded)
_mock_loader: Optional[MockDataLoader] = None


def get_mock_loader(data_path: Optional[str] = None) -> MockDataLoader:
    """
    Get or initialize the global mock data loader instance.
    
    Args:
        data_path: Path to mock data JSON file. If not provided, uses default.
    """
    global _mock_loader
    
    if _mock_loader is None:
        if data_path is None:
            # Default to .data/mock_event_data.json relative to this file
            api_dir = Path(__file__).parent
            project_root = api_dir.parent
            data_path = str(project_root / '.data' / 'mock_event_data.json')
        
        _mock_loader = MockDataLoader(data_path)
    
    return _mock_loader
