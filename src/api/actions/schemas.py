"""
Pydantic schemas for action payload validation.

Validates all card action JSON before dispatching to handlers.
Enables type safety and clear documentation of action parameters.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator


class ActionPayload(BaseModel):
    """Base schema for all action payloads."""

    action: str = Field(..., description="Action type identifier")

    class Config:
        """Allow extra fields for action-specific parameters."""
        extra = "allow"


class BrowseAllPayload(ActionPayload):
    """Schema for browse_all action."""

    action: str = Field("browse_all", description="Must be 'browse_all'")
    limit: int = Field(10, ge=1, le=100, description="Max projects to show")
    offset: int = Field(0, ge=0, description="Pagination offset")


class CarouselPayload(ActionPayload):
    """Schema for carousel/featured projects."""

    action: str = Field(..., pattern="^(featured|carousel)$")
    title: str = Field(..., description="Carousel title")
    subtitle: Optional[str] = None


class FilterPayload(ActionPayload):
    """Base schema for filter actions."""

    action: str = Field(..., description="Filter action type")

    @field_validator("action")
    def validate_filter_action(cls, v):
        valid_filters = [
            "filter_by_status",
            "filter_by_team_size",
            "filter_by_audience",
            "filter_by_location",
            "equipment_filter",
            "recording_filter",
            "show_featured",
        ]
        if v not in valid_filters:
            raise ValueError(f"action must be one of {valid_filters}")
        return v


class StatusFilterPayload(FilterPayload):
    """Schema for filter_by_status action."""

    action: str = Field("filter_by_status")
    status: str = Field(..., description="Project status to filter by")


class TeamSizeFilterPayload(FilterPayload):
    """Schema for filter_by_team_size action."""

    action: str = Field("filter_by_team_size")
    min: int = Field(1, ge=1, description="Minimum team size")
    max: int = Field(1000, ge=1, description="Maximum team size")

    @field_validator("max")
    def validate_max_ge_min(cls, v, info):
        if "min" in info.data and v < info.data["min"]:
            raise ValueError("max must be >= min")
        return v


class AudienceFilterPayload(FilterPayload):
    """Schema for filter_by_audience action."""

    action: str = Field("filter_by_audience")
    audience: str = Field(..., min_length=1, description="Target audience")


class LocationFilterPayload(FilterPayload):
    """Schema for filter_by_location action."""

    action: str = Field("filter_by_location")
    location: str = Field(..., min_length=1, description="Project location/placement")


class EquipmentFilterPayload(FilterPayload):
    """Schema for equipment_filter action."""

    action: str = Field("equipment_filter")
    equipment: str = Field(..., min_length=1, description="Equipment type needed")


class RecordingFilterPayload(FilterPayload):
    """Schema for recording_filter action."""

    action: str = Field("recording_filter")
    available: bool = Field(True, description="Filter by recording availability")


class FeaturedPayload(FilterPayload):
    """Schema for show_featured action."""

    action: str = Field("show_featured")


class SearchPayload(ActionPayload):
    """Base schema for search actions."""

    action: str = Field(..., description="Search action type")

    @field_validator("action")
    def validate_search_action(cls, v):
        valid_searches = ["keyword_search", "researcher_search", "filter_by_area"]
        if v not in valid_searches:
            raise ValueError(f"action must be one of {valid_searches}")
        return v


class KeywordSearchPayload(SearchPayload):
    """Schema for keyword_search action."""

    action: str = Field("keyword_search")
    keyword: str = Field(..., min_length=1, description="Keyword to search for")
    limit: int = Field(10, ge=1, le=100, description="Max results")


class ResearcherSearchPayload(SearchPayload):
    """Schema for researcher_search action."""

    action: str = Field("researcher_search")
    researcher: Optional[str] = Field(None, min_length=1, description="Researcher name")
    limit: int = Field(10, ge=1, le=100, description="Max results")


class AreaFilterPayload(SearchPayload):
    """Schema for filter_by_area action."""

    action: str = Field("filter_by_area")
    area: str = Field(..., min_length=1, description="Research area")
    limit: int = Field(10, ge=1, le=100, description="Max results")


class NavigationPayload(ActionPayload):
    """Base schema for navigation actions."""

    action: str = Field(..., description="Navigation action type")

    @field_validator("action")
    def validate_navigation_action(cls, v):
        valid_navigation = [
            "view_project",
            "back_to_results",
            "find_similar",
            "category_select",
        ]
        if v not in valid_navigation:
            raise ValueError(f"action must be one of {valid_navigation}")
        return v


class ViewProjectPayload(NavigationPayload):
    """Schema for view_project action."""

    action: str = Field("view_project")
    projectId: str = Field(..., description="Project ID to view")


class BackToResultsPayload(NavigationPayload):
    """Schema for back_to_results action."""

    action: str = Field("back_to_results")


class FindSimilarPayload(NavigationPayload):
    """Schema for find_similar action."""

    action: str = Field("find_similar")
    researchArea: str = Field(..., description="Research area for similar projects")


class CategorySelectPayload(NavigationPayload):
    """Schema for category_select action."""

    action: str = Field("category_select")
    category: Optional[str] = Field(None, min_length=1, description="Category name")


class ExperiencePayload(ActionPayload):
    """Base schema for experience actions."""

    action: str = Field(..., description="Experience action type")

    @field_validator("action")
    def validate_experience_action(cls, v):
        valid_experiences = [
            "hourly_agenda",
            "presenter_carousel",
            "bookmark",
            "project_synthesis",
            "organizer_tools",
        ]
        if v not in valid_experiences:
            raise ValueError(f"action must be one of {valid_experiences}")
        return v


class HourlyAgendaPayload(ExperiencePayload):
    """Schema for hourly_agenda action."""

    action: str = Field("hourly_agenda")
    timezone: str = Field("PT", description="Timezone label for display")
    max_items: int = Field(8, ge=1, le=20, description="Max sessions to show")


class PresenterCarouselPayload(ExperiencePayload):
    """Schema for presenter_carousel action."""

    action: str = Field("presenter_carousel")
    max_presenters: int = Field(6, ge=1, le=12, description="Max presenters to show")


class BookmarkPayload(ExperiencePayload):
    """Schema for bookmark action."""

    action: str = Field("bookmark")
    type: Optional[str] = Field(None, description="Item type (project, session, presenter)")
    projectId: Optional[str] = None
    sessionId: Optional[str] = None
    presenter: Optional[str] = None


class ProjectSynthesisPayload(ExperiencePayload):
    """Schema for project_synthesis action."""

    action: str = Field("project_synthesis")


class OrganizerToolsPayload(ExperiencePayload):
    """Schema for organizer_tools action."""

    action: str = Field("organizer_tools")


# Payload type mapping for dynamic validation
PAYLOAD_SCHEMAS = {
    "browse_all": BrowseAllPayload,
    "filter_by_status": StatusFilterPayload,
    "filter_by_team_size": TeamSizeFilterPayload,
    "filter_by_audience": AudienceFilterPayload,
    "filter_by_location": LocationFilterPayload,
    "equipment_filter": EquipmentFilterPayload,
    "recording_filter": RecordingFilterPayload,
    "show_featured": FeaturedPayload,
    "keyword_search": KeywordSearchPayload,
    "researcher_search": ResearcherSearchPayload,
    "filter_by_area": AreaFilterPayload,
    "view_project": ViewProjectPayload,
    "back_to_results": BackToResultsPayload,
    "find_similar": FindSimilarPayload,
    "category_select": CategorySelectPayload,
    "hourly_agenda": HourlyAgendaPayload,
    "presenter_carousel": PresenterCarouselPayload,
    "bookmark": BookmarkPayload,
    "project_synthesis": ProjectSynthesisPayload,
    "organizer_tools": OrganizerToolsPayload,
}


def validate_action_payload(action_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate action payload against schema.
    
    Args:
        action_type: Action identifier
        data: Raw action data
        
    Returns:
        Validated payload dictionary
        
    Raises:
        ValueError: If validation fails
    """
    schema_class = PAYLOAD_SCHEMAS.get(action_type, ActionPayload)
    try:
        validated = schema_class(**data)
        return validated.model_dump()
    except Exception as e:
        raise ValueError(f"Invalid payload for action '{action_type}': {str(e)}")
