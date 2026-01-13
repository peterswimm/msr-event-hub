"""Query Router Integration Tests."""

import pytest
from src.api.query_router import DeterministicRouter


@pytest.fixture
def router():
    return DeterministicRouter()


def test_event_overview_intent(router):
    queries = [
        "What is this event?",
        "When is the event?",
        "Where is the conference?",
        "What's the event schedule?",
    ]
    for query in queries:
        result = router.route(query)
        assert result.intent == "event_overview"
        assert result.confidence >= 0.5


def test_session_lookup_intent(router):
    queries = [
        "Show me sessions about AI",
        "What talks are at 2pm?",
        "Find keynote sessions",
        "Who is speaking tomorrow?",
    ]
    for query in queries:
        result = router.route(query)
        assert result.intent == "session_lookup"
        assert result.confidence >= 0.5


def test_project_search_intent(router):
    queries = [
        "Show me projects about machine learning",
        "Find posters related to HCI",
        "Search for projects on systems",
    ]
    for query in queries:
        result = router.route(query)
        assert result.intent == "project_search"
        assert result.confidence >= 0.5
        assert result.entities["projectTitleQuery"] is not None


def test_project_detail_intent(router):
    queries = [
        "Tell me about the AI Research Assistant project",
        "Details for 'Deep Learning Framework'",
        "Who is on the team for the Quantum Computing poster?",
    ]
    for query in queries:
        result = router.route(query)
        assert result.intent == "project_detail"
        assert result.confidence >= 0.5


def test_people_lookup_intent(router):
    queries = [
        "Show me projects by Alice Johnson",
        "What is Bob Chen presenting?",
        "Jane Smith's poster",
    ]
    for query in queries:
        result = router.route(query)
        assert result.intent == "people_lookup"
        assert result.entities["personQuery"] is not None


def test_category_browse_intent(router):
    queries = [
        "Which projects are in HCI?",
        "Show me all AI category projects",
        "List projects in the Systems track",
    ]
    for query in queries:
        result = router.route(query)
        assert result.intent == "category_browse"
        assert result.entities["categoryQuery"] is not None


def test_logistics_equipment_intent(router):
    queries = [
        "Which booths need a large display?",
        "Show me projects requiring 2 monitors",
        "What equipment does booth 42 need?",
    ]
    for query in queries:
        result = router.route(query)
        assert result.intent == "logistics_equipment"
        assert result.confidence >= 0.5


def test_logistics_placement_intent(router):
    queries = [
        "Where is the AI poster?",
        "What's the placement for booth 15?",
        "Show me the floor plan",
    ]
    for query in queries:
        result = router.route(query)
        assert result.intent == "logistics_placement"
        assert result.confidence >= 0.5


def test_recording_status_intent(router):
    queries = [
        "Do we have a recording link for 'AI Assistant'?",
        "Which projects have submitted recordings?",
        "Is the video edited yet?",
    ]
    for query in queries:
        result = router.route(query)
        assert result.intent == "recording_status"
        assert result.confidence >= 0.5


def test_entity_extraction_quoted_title(router):
    query = 'Show me details for "Deep Learning Framework"'
    result = router.route(query)
    assert result.entities["projectTitleQuery"] == "Deep Learning Framework"


def test_entity_extraction_category(router):
    query = "List all projects in HCI category"
    result = router.route(query)
    assert result.entities["categoryQuery"] == "HCI"


def test_entity_extraction_person(router):
    query = "Show me projects by Alice Johnson"
    result = router.route(query)
    assert result.entities["personQuery"] == "Alice Johnson"


def test_filter_extraction_equipment(router):
    query = "Which booths need a large display and 2 monitors?"
    result = router.route(query)
    assert result.filters["largeDisplay"] is True
    assert result.filters["monitors27"] == 2


def test_query_plan_event_overview(router):
    query = "What is this event?"
    result = router.route(query)
    assert len(result.query_plan) > 0
    assert result.query_plan[0]["endpoint"].startswith("GET /v1/events")


def test_query_plan_project_search(router):
    query = "Show me projects about AI"
    result = router.route(query)
    assert len(result.query_plan) > 0
    assert "projects" in result.query_plan[0]["endpoint"]


def test_deterministic_threshold(router):
    # High confidence query
    query = "Which projects are in HCI?"
    result = router.route(query)
    assert result.is_deterministic()  # Should be > 0.8 confidence

    # Low confidence query
    query = "What do you think about this?"
    result = router.route(query)
    assert not result.is_deterministic()  # Should be < 0.8 confidence
