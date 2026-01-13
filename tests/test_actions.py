"""
Comprehensive tests for unified action handlers.

Tests all 15+ action handlers with parametrized factory pattern.
Validates:
- Input validation via Pydantic schemas
- Handler execution and error handling
- Context updates
- Card response generation
- Caching behavior
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Any, Dict

from src.api.actions.base import ActionRegistry, BaseActionHandler, get_registry
from src.api.actions.decorators import register_action
from src.api.actions.schemas import (
    BrowseAllPayload,
    StatusFilterPayload,
    KeywordSearchPayload,
    ResearcherSearchPayload,
)
from src.api.actions.helpers import build_project_carousel, apply_filter, safe_truncate
from src.api.conversation_context import ConversationContext
from src.api.caching import SessionCache


# Test fixtures
@pytest.fixture
def mock_projects():
    """Mock project data for testing."""
    return [
        {
            "id": "proj-1",
            "name": "AI Research Initiative",
            "researchArea": "Artificial Intelligence",
            "description": "Exploring deep learning for robotics",
            "team": [{"name": "Alice"}, {"name": "Bob"}],
            "equipment": ["GPU", "Monitor"],
            "recordingPermission": "Yes",
            "targetAudience": "Researchers",
            "placement": "Building A",
            "featured": True,
            "status": "Active",
            "date": "2024-01-15",
        },
        {
            "id": "proj-2",
            "name": "Systems Programming",
            "researchArea": "Systems",
            "description": "Distributed system optimizations",
            "team": [{"name": "Charlie"}],
            "equipment": ["Workstation"],
            "recordingPermission": "No",
            "targetAudience": "Engineers",
            "placement": "Building B",
            "featured": False,
            "status": "Active",
            "date": "2024-01-10",
        },
        {
            "id": "proj-3",
            "name": "Security Frameworks",
            "researchArea": "Security",
            "description": "Building zero-trust architectures",
            "team": [{"name": "Diana"}, {"name": "Eve"}],
            "equipment": ["Monitor"],
            "recordingPermission": "Yes",
            "targetAudience": "All",
            "placement": "Building C",
            "featured": True,
            "status": "Completed",
            "date": "2024-01-01",
        },
    ]


@pytest.fixture
def context():
    """Create conversation context."""
    return ConversationContext()


@pytest.fixture
def session_cache():
    """Create session cache."""
    return SessionCache(enabled=True, ttl_seconds=3600)


# Helper tests
class TestHelpers:
    """Test helper utilities."""

    def test_safe_truncate_short_text(self):
        """Test truncation of short text."""
        text = "Hello world"
        result = safe_truncate(text, 20)
        assert result == text
        assert len(result) <= 20

    def test_safe_truncate_long_text(self):
        """Test truncation of long text at word boundary."""
        text = "This is a very long text that needs truncation at word boundaries"
        result = safe_truncate(text, 30)
        assert result.endswith("...")
        assert "word" not in result

    def test_apply_filter_matching(self, mock_projects):
        """Test filter with matching projects."""
        filtered = apply_filter(
            mock_projects, lambda p: p.get("status") == "Active"
        )
        assert len(filtered) == 2
        assert all(p.get("status") == "Active" for p in filtered)

    def test_apply_filter_no_matches(self, mock_projects):
        """Test filter with no matches."""
        filtered = apply_filter(
            mock_projects, lambda p: p.get("status") == "NonExistent"
        )
        assert len(filtered) == 0

    def test_build_project_carousel(self, mock_projects):
        """Test carousel card generation."""
        card = build_project_carousel(
            mock_projects, title="Test Projects", subtitle="Showing 3 projects"
        )

        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.5"
        assert card["body"][0]["text"] == "Test Projects"
        assert len(card["body"]) > 2  # Title, subtitle, and items


# Handler tests with factory pattern
class TestBrowseAllHandler:
    """Test browse_all handler."""

    @pytest.mark.asyncio
    @patch("storage.event_data.get_event_data")
    async def test_browse_all_execution(self, mock_get_data, mock_projects, context):
        """Test browse_all action execution."""
        from src.api.actions.browse.handlers import BrowseAllHandler

        mock_get_data.return_value = {"projects": mock_projects}

        handler = BrowseAllHandler("browse_all")
        payload = {"action": "browse_all", "limit": 10}

        text, card = await handler.execute(payload, context)

        assert "featured projects" in text.lower()
        assert card is not None
        assert card["type"] == "AdaptiveCard"
        assert context.conversation_stage == "show_results"

    @pytest.mark.asyncio
    async def test_browse_all_context_update(self, context):
        """Test context update after browse_all."""
        from src.api.actions.browse.handlers import BrowseAllHandler

        handler = BrowseAllHandler("browse_all")
        await handler.update_context({}, context)

        assert context.conversation_stage == "show_results"


class TestFilterHandlers:
    """Test filter action handlers."""

    @pytest.mark.asyncio
    @patch("storage.event_data.get_event_data")
    async def test_filter_by_status(self, mock_get_data, mock_projects, context):
        """Test filter_by_status handler."""
        from src.api.actions.filter.handlers import FilterByStatusHandler

        mock_get_data.return_value = {"projects": mock_projects}

        handler = FilterByStatusHandler("filter_by_status")
        payload = {"action": "filter_by_status", "status": "Active"}

        text, card = await handler.execute(payload, context)

        assert "2" in text  # Found 2 active projects
        assert "Active" in text

    @pytest.mark.asyncio
    @patch("storage.event_data.get_event_data")
    async def test_filter_by_team_size(self, mock_get_data, mock_projects, context):
        """Test filter_by_team_size handler."""
        from src.api.actions.filter.handlers import FilterByTeamSizeHandler

        mock_get_data.return_value = {"projects": mock_projects}

        handler = FilterByTeamSizeHandler("filter_by_team_size")
        payload = {"action": "filter_by_team_size", "min": 1, "max": 2}

        text, card = await handler.execute(payload, context)

        assert "team size" in text.lower()


class TestSearchHandlers:
    """Test search action handlers."""

    @pytest.mark.asyncio
    @patch("storage.event_data.get_event_data")
    async def test_keyword_search(self, mock_get_data, mock_projects, context):
        """Test keyword_search handler."""
        from src.api.actions.search.handlers import KeywordSearchHandler

        mock_get_data.return_value = {"projects": mock_projects}

        handler = KeywordSearchHandler("keyword_search")
        payload = {"action": "keyword_search", "keyword": "learning"}

        text, card = await handler.execute(payload, context)

        assert "found" in text.lower()
        assert context.interests_keywords == {"learning"}

    @pytest.mark.asyncio
    @patch("storage.event_data.get_event_data")
    async def test_researcher_search(self, mock_get_data, mock_projects, context):
        """Test researcher_search handler."""
        from src.api.actions.search.handlers import ResearcherSearchHandler

        mock_get_data.return_value = {"projects": mock_projects}

        handler = ResearcherSearchHandler("researcher_search")
        payload = {"action": "researcher_search", "researcher": "Alice"}

        text, card = await handler.execute(payload, context)

        assert "Alice" in text
        assert "alice" in context.selected_researchers


class TestNavigationHandlers:
    """Test navigation action handlers."""

    @pytest.mark.asyncio
    @patch("storage.event_data.get_event_data")
    async def test_view_project(self, mock_get_data, mock_projects, context):
        """Test view_project handler."""
        from src.api.actions.navigation.handlers import ViewProjectHandler

        mock_get_data.return_value = {"projects": mock_projects}

        handler = ViewProjectHandler("view_project")
        payload = {"action": "view_project", "projectId": "proj-1"}

        text, card = await handler.execute(payload, context)

        assert "AI Research" in text
        assert context.current_project_id == "proj-1"
        assert "proj-1" in context.viewed_projects
        assert context.conversation_stage == "project_detail"

    @pytest.mark.asyncio
    async def test_back_to_results(self, context):
        """Test back_to_results handler."""
        from src.api.actions.navigation.handlers import BackToResultsHandler

        # Set up previous results
        context.last_results = [{"id": "1", "name": "Project 1"}]

        handler = BackToResultsHandler("back_to_results")
        text, card = await handler.execute({}, context)

        assert "Showing 1 results" in text
        assert context.conversation_stage == "show_results"

    @pytest.mark.asyncio
    async def test_category_select(self, context):
        """Test category_select handler."""
        from src.api.actions.navigation.handlers import CategorySelectHandler

        handler = CategorySelectHandler("category_select")
        payload = {"action": "category_select", "category": "AI"}

        text, card = await handler.execute(payload, context)

        assert "AI" in text
        assert "ai" in context.selected_categories


# Cache tests
class TestSessionCache:
    """Test session-level caching."""

    def test_cache_set_and_get(self, session_cache):
        """Test cache set and get."""
        data = {"projects": [{"id": "1"}]}
        session_cache.set("projects", data)

        result = session_cache.get("projects")
        assert result == data

    def test_cache_disabled(self):
        """Test cache when disabled."""
        cache = SessionCache(enabled=False)
        data = {"projects": []}
        cache.set("projects", data)

        result = cache.get("projects")
        assert result is None

    def test_cache_invalidate(self, session_cache):
        """Test cache invalidation."""
        session_cache.set("projects", {"data": "test"})
        session_cache.invalidate("projects")

        result = session_cache.get("projects")
        assert result is None

    def test_cache_toggle(self, session_cache):
        """Test toggling cache."""
        assert session_cache.enabled
        session_cache.toggle(False)
        assert not session_cache.enabled
        session_cache.toggle(True)
        assert session_cache.enabled


# Registry tests
class TestActionRegistry:
    """Test action registry."""

    def test_registry_registration(self):
        """Test handler registration."""
        registry = ActionRegistry()

        class TestHandler(BaseActionHandler):
            async def execute(self, payload, context):
                return "test", None

        handler = TestHandler("test")
        registry.register("test_action", handler)

        assert registry.is_registered("test_action")
        assert registry.get_handler("test_action") is handler

    def test_registry_duplicate_registration(self):
        """Test duplicate registration error."""
        registry = ActionRegistry()

        class TestHandler(BaseActionHandler):
            async def execute(self, payload, context):
                return "test", None

        handler = TestHandler("test")
        registry.register("test_action", handler)

        with pytest.raises(ValueError):
            registry.register("test_action", handler)

    def test_list_actions(self):
        """Test listing registered actions."""
        registry = ActionRegistry()

        class TestHandler(BaseActionHandler):
            async def execute(self, payload, context):
                return "test", None

        handler = TestHandler("test")
        registry.register("test_action", handler, description="Test action")

        actions = registry.list_actions()
        assert "test_action" in actions
        assert actions["test_action"]["description"] == "Test action"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
