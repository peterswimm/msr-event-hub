"""
Tests for mock data loader functionality.
"""
import pytest
from pathlib import Path
from api.mock_data_loader import MockDataLoader


@pytest.fixture
def mock_loader():
    """Create mock data loader for testing."""
    data_path = Path(__file__).parent.parent / 'data' / 'mock_event_data.json'
    return MockDataLoader(str(data_path))


def test_get_event(mock_loader):
    """Test retrieving main event information."""
    event = mock_loader.get_event()
    assert event is not None
    assert event['displayName'] == 'MSR Event 2025'
    assert event['eventType'] == 'conference'
    assert 'startDate' in event
    assert 'endDate' in event


def test_get_all_projects(mock_loader):
    """Test retrieving all projects."""
    projects = mock_loader.get_projects()
    assert len(projects) == 5
    assert all('id' in p for p in projects)
    assert all('name' in p for p in projects)


def test_filter_projects_by_research_area(mock_loader):
    """Test filtering projects by research area."""
    ai_projects = mock_loader.get_projects(research_area='Artificial Intelligence')
    assert len(ai_projects) == 1
    assert ai_projects[0]['name'] == 'Neural Code Intelligence'
    
    quantum_projects = mock_loader.get_projects(research_area='Quantum Computing')
    assert len(quantum_projects) == 1
    assert quantum_projects[0]['name'] == 'Quantum Error Correction'


def test_search_projects_by_query(mock_loader):
    """Test searching projects by text query."""
    # Search in name
    results = mock_loader.get_projects(search_query='quantum')
    assert len(results) == 1
    assert 'Quantum' in results[0]['name']
    
    # Search in description
    results = mock_loader.get_projects(search_query='federated learning')
    assert len(results) == 1
    assert 'Privacy-Preserving' in results[0]['name']


def test_filter_projects_by_equipment(mock_loader):
    """Test filtering projects by equipment type."""
    display_projects = mock_loader.get_projects(equipment='Large Display')
    assert len(display_projects) == 2
    project_names = [p['name'] for p in display_projects]
    assert 'Neural Code Intelligence' in project_names
    assert 'Sustainable Cloud Infrastructure' in project_names


def test_filter_projects_by_monitor_requirement(mock_loader):
    """Test filtering projects by monitor requirement."""
    monitor_projects = mock_loader.get_projects(requires_monitor=True)
    assert len(monitor_projects) == 4
    
    no_monitor_projects = mock_loader.get_projects(requires_monitor=False)
    assert len(no_monitor_projects) == 1
    assert no_monitor_projects[0]['name'] == 'Sustainable Cloud Infrastructure'


def test_filter_projects_by_recording_permission(mock_loader):
    """Test filtering projects by recording permission."""
    allowed = mock_loader.get_projects(recording_permission='allowed')
    assert len(allowed) == 3
    
    restricted = mock_loader.get_projects(recording_permission='restricted')
    assert len(restricted) == 1
    assert restricted[0]['name'] == 'Quantum Error Correction'
    
    not_allowed = mock_loader.get_projects(recording_permission='not_allowed')
    assert len(not_allowed) == 1
    assert not_allowed[0]['name'] == 'Privacy-Preserving Machine Learning'


def test_filter_projects_by_comms_status(mock_loader):
    """Test filtering projects by comms status."""
    approved = mock_loader.get_projects(comms_status='approved')
    assert len(approved) == 4
    
    pending = mock_loader.get_projects(comms_status='pending')
    assert len(pending) == 1
    assert pending[0]['name'] == 'Quantum Error Correction'


def test_get_project_by_id(mock_loader):
    """Test retrieving specific project by ID."""
    project = mock_loader.get_project_by_id('proj-001')
    assert project is not None
    assert project['name'] == 'Neural Code Intelligence'
    assert project['researchArea'] == 'Artificial Intelligence'
    
    # Non-existent ID
    project = mock_loader.get_project_by_id('proj-999')
    assert project is None


def test_search_projects_by_name(mock_loader):
    """Test searching projects by name."""
    results = mock_loader.search_projects_by_name('neural')
    assert len(results) == 1
    assert 'Neural' in results[0]['name']
    
    # Partial match
    results = mock_loader.search_projects_by_name('cloud')
    assert len(results) == 1
    assert 'Cloud' in results[0]['name']


def test_get_all_sessions(mock_loader):
    """Test retrieving all sessions."""
    sessions = mock_loader.get_sessions()
    assert len(sessions) == 4
    assert all('id' in s for s in sessions)
    assert all('title' in s for s in sessions)


def test_filter_sessions_by_type(mock_loader):
    """Test filtering sessions by type."""
    keynotes = mock_loader.get_sessions(session_type='keynote')
    assert len(keynotes) == 1
    assert keynotes[0]['title'] == 'Keynote: The Future of AI Research'
    
    workshops = mock_loader.get_sessions(session_type='workshop')
    assert len(workshops) == 1


def test_filter_sessions_by_audience(mock_loader):
    """Test filtering sessions by target audience."""
    general = mock_loader.get_sessions(target_audience='general')
    assert len(general) == 2
    
    technical = mock_loader.get_sessions(target_audience='technical')
    assert len(technical) == 1


def test_search_sessions(mock_loader):
    """Test searching sessions by query."""
    results = mock_loader.get_sessions(search_query='quantum')
    assert len(results) == 1
    assert 'Quantum' in results[0]['title']


def test_get_session_by_id(mock_loader):
    """Test retrieving specific session by ID."""
    session = mock_loader.get_session_by_id('sess-001')
    assert session is not None
    assert 'Keynote' in session['title']
    
    session = mock_loader.get_session_by_id('sess-999')
    assert session is None


def test_search_people_by_name(mock_loader):
    """Test searching people by name."""
    results = mock_loader.search_people(name='Sarah')
    assert len(results) == 1
    assert results[0]['displayName'] == 'Dr. Sarah Chen'
    
    # Partial match
    results = mock_loader.search_people(name='chen')
    assert len(results) == 1


def test_search_people_by_research_area(mock_loader):
    """Test searching people by research area."""
    ai_people = mock_loader.search_people(research_area='Artificial Intelligence')
    assert len(ai_people) == 2
    names = [p['displayName'] for p in ai_people]
    assert 'Dr. Sarah Chen' in names
    assert 'Alex Rodriguez' in names


def test_search_people_by_role(mock_loader):
    """Test searching people by role."""
    principals = mock_loader.search_people(role='Principal Researcher')
    assert len(principals) == 5
    
    seniors = mock_loader.search_people(role='Senior Researcher')
    assert len(seniors) == 2


def test_get_categories(mock_loader):
    """Test retrieving research area categories."""
    categories = mock_loader.get_categories()
    assert len(categories) == 5
    assert 'Artificial Intelligence' in categories
    assert 'Quantum Computing' in categories
    assert 'Human-Computer Interaction' in categories


def test_get_projects_by_category(mock_loader):
    """Test retrieving projects by category."""
    systems_projects = mock_loader.get_projects_by_category('Systems')
    assert len(systems_projects) == 1
    assert systems_projects[0]['name'] == 'Sustainable Cloud Infrastructure'


def test_get_logistics_summary(mock_loader):
    """Test getting logistics summary across all projects."""
    summary = mock_loader.get_logistics_summary()
    
    assert summary['total_projects'] == 5
    
    # Equipment counts
    assert 'Large Display' in summary['equipment']
    assert summary['equipment']['Large Display'] == 2
    
    # Recording permissions
    assert summary['recording_permissions']['allowed'] == 3
    assert summary['recording_permissions']['restricted'] == 1
    assert summary['recording_permissions']['not_allowed'] == 1
    
    # Comms status
    assert summary['comms_status']['approved'] == 4
    assert summary['comms_status']['pending'] == 1
    
    # Monitor requirements
    assert summary['monitor_requirements']['requires_monitor'] == 4
    assert summary['monitor_requirements']['no_monitor'] == 1


def test_combined_filters(mock_loader):
    """Test combining multiple filters."""
    # Find projects that are AI, require monitors, and allow recording
    results = mock_loader.get_projects(
        research_area='Artificial Intelligence',
        requires_monitor=True,
        recording_permission='allowed'
    )
    assert len(results) == 1
    assert results[0]['name'] == 'Neural Code Intelligence'
    
    # Find projects in HCI with VR equipment
    results = mock_loader.get_projects(
        research_area='Human-Computer Interaction',
        equipment='VR Headsets'
    )
    assert len(results) == 1
    assert results[0]['name'] == 'Accessibility in AR/VR'
