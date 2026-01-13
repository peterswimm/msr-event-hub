import logging
import os
import asyncio
import json
from typing import Generator, Iterable, List, Optional, AsyncIterator, Dict, Any
from datetime import datetime

import requests
from azure.identity import DefaultAzureCredential

try:
    from fastapi import APIRouter, HTTPException
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # pragma: no cover - FastAPI optional for non-API runs
    APIRouter = None  # type: ignore
    HTTPException = Exception  # type: ignore
    StreamingResponse = None  # type: ignore
    BaseModel = object  # type: ignore
    Field = lambda *args, **kwargs: None  # type: ignore

logger = logging.getLogger(__name__)
credential = DefaultAzureCredential(exclude_interactive_browser_credential=True)

AZURE_OPENAI_SCOPE = "https://cognitiveservices.azure.com/.default"
DEFAULT_API_VERSION = "2024-02-15-preview"


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(system|user|assistant)$")
    content: str
    # Optional adaptive card attachment for Teams/bot responses
    adaptive_card: Optional[Dict[str, Any]] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 400


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise HTTPException(status_code=500, detail=f"Missing configuration: {name}")
    return value.rstrip("/")


def _get_bearer_token() -> str:
    token = credential.get_token(AZURE_OPENAI_SCOPE)
    return token.token


def _iter_azure_stream(resp: requests.Response) -> Iterable[str]:
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        yield raw


def _forward_stream(payload: ChatRequest) -> Generator[str, None, None]:
    endpoint = _get_required_env("AZURE_OPENAI_ENDPOINT")
    deployment = _get_required_env("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_VERSION", DEFAULT_API_VERSION)

    url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"

    data = {
        "messages": [m.model_dump() for m in payload.messages],
        "temperature": payload.temperature if payload.temperature is not None else 0.3,
        "max_tokens": payload.max_tokens if payload.max_tokens is not None else 400,
        "stream": True,
    }

    headers = {
        "Authorization": f"Bearer {_get_bearer_token()}",
        "Content-Type": "application/json",
    }

    with requests.post(url, headers=headers, json=data, stream=True, timeout=300) as resp:
        if not resp.ok:
            detail = resp.text or resp.reason
            logger.error("Azure OpenAI request failed: %s %s", resp.status_code, detail)
            raise HTTPException(status_code=resp.status_code, detail=detail)

        for line in _iter_azure_stream(resp):
            if not line.startswith("data:"):
                continue
            yield f"{line}\n\n"


def get_chat_router():
    if APIRouter is None:
        return None

    router = APIRouter(prefix="/api/chat", tags=["Chat"])

    async def handle_card_action_unified(action_type: str, card_action: Dict[str, Any], context: Any):
        """
        Unified card action dispatcher using action registry.
        
        Replaces ~500 lines of duplicated handler code with declarative dispatch.
        All handlers are registered via @register_action decorator.
        """
        from src.api.actions.base import get_registry
        from src.api.actions.schemas import validate_action_payload
        from src.api.actions.middleware import ActionExecutionError, ActionValidationError
        
        try:
            # Validate action payload against schema
            validated_payload = validate_action_payload(action_type, card_action)
            
            # Get registry and dispatch to handler
            registry = get_registry()
            if not registry.is_registered(action_type):
                logger.warning(f"Action not registered: {action_type}")
                raise KeyError(f"Action '{action_type}' not registered")
            
            # Execute handler
            result_text, result_card = await registry.dispatch(
                action_type, 
                validated_payload, 
                context
            )
            
            logger.debug(f"Action '{action_type}' completed successfully")
            return result_text, result_card
            
        except (ActionValidationError, ActionExecutionError) as e:
            logger.error(f"Action '{action_type}' failed: {str(e)}")
            # Build error card
            from src.api.actions.helpers import build_error_card
            error_card = build_error_card(str(e), action_type)
            return str(e), error_card
        except KeyError as e:
            logger.error(f"Unregistered action: {action_type}")
            error_msg = f"Action '{action_type}' is not available"
            from src.api.actions.helpers import build_error_card
            error_card = build_error_card(error_msg, action_type)
            return error_msg, error_card
        except Exception as e:
            logger.error(f"Unexpected error in action '{action_type}': {str(e)}", exc_info=True)
            error_msg = "An unexpected error occurred while processing your request"
            from src.api.actions.helpers import build_error_card
            error_card = build_error_card(error_msg, action_type)
            return error_msg, error_card
        # All card actions now handled via registry
            
        elif action_type == "researcher_search":
            researcher = card_action.get("researcher", "")
            filtered = [p for p in all_projects if any(researcher.lower() in m.get("name", "").lower() for m in p.get("team", []))]
            logger.info(f"Researcher search: {researcher}, found {len(filtered)} projects.")
            result_text = f"Found {len(filtered)} projects for researcher: {researcher}."
            result_card = generate_carousel_card(filtered, title=f"Research by {researcher}", subtitle=f"Showing {len(filtered)} projects")
            context.conversation_stage = "show_results"
            
        elif action_type == "category_select":
            category = card_action.get("category", "")
            filtered = [p for p in all_projects if category.lower() in p.get("researchArea", "").lower()]
            logger.info(f"Category selected: {category}, found {len(filtered)} projects.")
            result_text = f"Found {len(filtered)} projects in {category}."
            result_card = generate_carousel_card(filtered, title=category, subtitle=f"Showing {len(filtered)} projects")
            context.add_category(category)
            context.conversation_stage = "show_results"
            
        elif action_type == "recording_filter":
            filtered = [p for p in all_projects if p.get("recordingPermission") == "Yes" or p.get("recordingPermission") == "true"]
            logger.info(f"Recording filter applied, found {len(filtered)} projects.")
            result_text = f"Found {len(filtered)} projects with recording available."
            result_card = generate_carousel_card(filtered, title="Projects with Recording", subtitle=f"Showing {len(filtered)} projects")
            context.add_equipment_filter("recording")
            context.conversation_stage = "show_results"
            
        elif action_type == "recent_projects":
            import datetime
            recent = sorted(
                [p for p in all_projects if p.get("date")],
                key=lambda p: p.get("date"),
                reverse=True
            )[:10]
            logger.info(f"Recent projects query, found {len(recent)} projects.")
            result_text = f"Found {len(recent)} recently added projects."
            result_card = generate_carousel_card(recent, title="Recent Projects", subtitle=f"Showing {len(recent)} projects")
            context.conversation_stage = "show_results"
            
        else:
            logger.warning(f"Unhandled card action: {action_type}")
            result_text = f"Action '{action_type}' not yet implemented."
            context.conversation_stage = "show_results"
        
        # Log context update
        logger.info(f"Updated context: {context.to_dict()}")
        
        # Return standardized response
        return result_text, result_card

        """Generate an Adaptive Card carousel for a list of projects."""
        def safe_truncate(text, max_length=120):
            if len(text) <= max_length:
                return text
            truncated = text[:max_length]
            last_space = truncated.rfind(' ')
            if last_space > 0:
                return truncated[:last_space] + "..."
            return truncated + "..."
        
        project_items = []
        for idx, proj in enumerate(projects[:10]):
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
            "fallbackText": f"{title} - Showing {len(project_items)} projects",
            "body": [
                {"type": "TextBlock", "text": title, "size": "large", "weight": "bolder", "spacing": "none"},
                {"type": "TextBlock", "text": subtitle or f"Showing {len(project_items)} projects", "size": "small", "color": "accent"}
            ] + project_items,
            "actions": [
                {"type": "Action.Submit", "title": "Filter by Area", "data": {"action": "filter_by_area"}},
                {"type": "Action.Submit", "title": "Recent Updates", "data": {"action": "recent_projects"}},
                {"type": "Action.Submit", "title": "With Recording", "data": {"action": "recording_filter", "available": "true"}}
            ]
        }
        return carousel_card

    @router.get("/health")
    async def chat_health():
        """Health check endpoint for chat service."""
        return {
            "status": "healthy",
            "service": "chat-hybrid-router",
            "timestamp": datetime.now().isoformat()
        }

    @router.get("/welcome")
    async def welcome():
        """Get welcome message with example prompts and adaptive card."""
        from src.api.card_renderer import get_card_renderer
        
        renderer = get_card_renderer()
        welcome_card = renderer.render_welcome_card()
        
        return {
            "message": "Welcome to MSR Event Hub Chat! 🎓",
            "description": "I can help you explore research projects, find sessions, and learn about the Redmond Research Showcase.",
            "examples": [
                {
                    "title": "Find AI projects",
                    "prompt": "Show me all artificial intelligence projects"
                },
                {
                    "title": "Search by team member",
                    "prompt": "What projects is Alice working on?"
                },
                {
                    "title": "Browse by category",
                    "prompt": "List all systems and networking projects"
                },
                {
                    "title": "Equipment requirements",
                    "prompt": "Which projects need a large display?"
                },
                {
                    "title": "Recording status",
                    "prompt": "Which projects have recording available?"
                }
            ],
            "adaptive_card": welcome_card
        }

    @router.post("/stream")
    async def stream_chat(payload: ChatRequest):
        """
        Hybrid chat endpoint with intelligent routing:
        1. Try deterministic router first (80% of queries)
        2. For low-confidence queries, delegate to Foundry agents
        3. Fall back to Azure OpenAI for remaining queries
        """
        try:
            # Import here to avoid circular deps and allow optional imports
            from src.api.query_router import DeterministicRouter
            from src.api.router_config import router_config
            from src.api.foundry_client import FoundryClient, FoundryConfig
            from src.api.conversation_context import extract_context_from_messages
            from src.storage.event_data import get_event_data
            
            # Extract user query (last message)
            user_query = payload.messages[-1].content if payload.messages else ""
            
            if not user_query:
                raise HTTPException(status_code=400, detail="No query provided")
            
            # Extract conversation context from message history
            context = extract_context_from_messages([m.model_dump() for m in payload.messages])
            context.advance_turn()
            logger.info(f"Conversation context: {context.to_dict()}")
            
            # Step 1: Check if this is a card action (JSON format)
            card_action = None
            try:
                card_action = json.loads(user_query)
                if isinstance(card_action, dict) and "action" in card_action:
                    logger.info(f"Card action detected: {card_action.get('action')}")
                else:
                    card_action = None
            except (json.JSONDecodeError, ValueError):
                card_action = None
            
            # Handle specific card actions
            if card_action:
                action_type = card_action.get("action")
                logger.info(f"Processing card action: {action_type}")
                
                try:
                    result_text, result_card = await handle_card_action_unified(
                        action_type, card_action, context
                    )
                    
                    async def action_response_stream():
                        payload_data = {
                            "delta": result_text,
                        }
                        if result_card:
                            payload_data["adaptive_card"] = result_card
                        payload_data["context"] = context.to_dict()
                        
                        yield f"data: {json.dumps(payload_data)}\n\n"
                        yield "data: [DONE]\n\n"
                    
                    return StreamingResponse(
                        action_response_stream(),
                        media_type="text/event-stream"
                    )
                    
                except Exception as e:
                    logger.error(f"Card action processing failed: {e}", exc_info=True)
                    error_response = {
                        "delta": f"Error processing action: {str(e)}",
                        "context": context.to_dict()
                    }
                    
                    async def error_stream():
                        yield f"data: {json.dumps(error_response)}\n\n"
                        yield "data: [DONE]\n\n"
                    
                    return StreamingResponse(
                        error_stream(),
                        media_type="text/event-stream"
                    )
                    # ...existing code for view_project...
                    project_id = card_action.get("projectId")
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    project = next((p for p in all_projects if p.get("id") == project_id), None)
                    if project:
                        from src.api.card_renderer import get_card_renderer
                        renderer = get_card_renderer()
                        team = ", ".join([m.get("name", "") for m in project.get("team", [])])
                        equipment = ", ".join(project.get("equipment", [])) if project.get("equipment") else "Standard"
                        detail_card = renderer.render_project_detail_card(
                            project_id=project_id,
                            title=project.get("name", "Untitled"),
                            research_area=project.get("researchArea", "General"),
                            description=project.get("description", "No description available"),
                            team_members=team,
                            placement=project.get("placement", "TBD"),
                            equipment=equipment,
                            recording_status=project.get("recordingPermission", "Not specified"),
                            target_audience=project.get("targetAudience", "General audience")
                        )
                        context.mark_project_viewed(project_id)
                        context.conversation_stage = "project_detail"
                        logger.info(f"Project viewed: {project_id}")
                        logger.info(f"Updated context: {context.to_dict()}")
                        result_text = f"📋 {project.get('name', 'Project Details')}"
                        async def detail_stream():
                            data = {
                                "delta": result_text,
                                "adaptive_card": detail_card,
                                "context": context.to_dict()
                            }
                            yield f"data: {json.dumps(data)}\n\n"
                            yield "data: [DONE]\n\n"
                        return StreamingResponse(
                            detail_stream(),
                            media_type="text/event-stream"
                        )
                elif action_type == "back_to_results":
                    if context.last_results:
                        result_text = f"📊 Showing {len(context.last_results)} results\n\n"
                        for i, proj in enumerate(context.last_results[:5], 1):
                            result_text += f"{i}. **{proj.get('name', 'Untitled')}** - {proj.get('researchArea', 'General')}\n"
                        async def results_stream():
                            data = {"delta": result_text}
                            yield f"data: {json.dumps(data)}\n\n"
                            yield "data: [DONE]\n\n"
                        return StreamingResponse(
                            results_stream(),
                            media_type="text/event-stream"
                        )
                elif action_type == "find_similar":
                    research_area = card_action.get("researchArea", "")
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    similar = [p for p in all_projects if research_area.lower() in p.get("researchArea", "").lower()][:5]
                    result_text = f"🔍 Found {len(similar)} similar projects in {research_area}:\n\n"
                    for i, proj in enumerate(similar, 1):
                        result_text += f"{i}. **{proj.get('name', 'Untitled')}**\n"
                    async def similar_stream():
                        data = {"delta": result_text}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(
                        similar_stream(),
                        media_type="text/event-stream"
                    )
                # --- New handlers for all card actions ---
                elif action_type == "category_select":
                    selected_category = card_action.get("category")
                    if selected_category:
                        context.add_category(selected_category)
                        context.conversation_stage = "show_results"
                        logger.info(f"Category selected: {selected_category}")
                        logger.info(f"Updated context: {context.to_dict()}")
                        # Optionally, return a new card or results here
                        result_text = f"Category '{selected_category}' selected."
                    else:
                        logger.warning("category_select action received without category")
                        result_text = "No category provided."
                    async def category_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(
                        category_stream(),
                        media_type="text/event-stream"
                    )
                elif action_type == "browse_all":
                    from src.storage.event_data import get_event_data
                    import datetime
                    
                    logger.info("Browse all projects action triggered.")
                    event_data = get_event_data()
                    logger.info(f"Event data keys: {list(event_data.keys())}")
                    all_projects = event_data.get("projects", [])
                    logger.info(f"Total projects loaded: {len(all_projects)}")
                    
                    # Helper function for safe text truncation
                    def safe_truncate(text, max_length=120):
                        """Safely truncate text at word boundary."""
                        if len(text) <= max_length:
                            return text
                        truncated = text[:max_length]
                        # Find last space to avoid cutting mid-word
                        last_space = truncated.rfind(' ')
                        if last_space > 0:
                            return truncated[:last_space] + "..."
                        return truncated + "..."
                    
                    # Compose a proper card with project list
                    carousel_card = None
                    try:
                        # Build body items for each project
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
                        context.conversation_stage = "show_results"
                        logger.info(f"Generated carousel card with {len(project_items)} projects")
                        logger.info(f"Updated context: {context.to_dict()}")
                    except Exception as e:
                        logger.error(f"Error generating carousel card: {e}", exc_info=True)
                        # Fallback simple card
                        carousel_card = {
                            "type": "AdaptiveCard",
                            "$schema": "https://adaptivecards.io/schemas/adaptive-card.json",
                            "version": "1.5",
                            "fallbackText": f"Featured Projects - Found {len(all_projects)} projects",
                            "body": [
                                {"type": "TextBlock", "text": "Featured Projects", "size": "large", "weight": "bolder", "spacing": "none"},
                                {"type": "TextBlock", "text": f"Found {len(all_projects)} projects", "wrap": True}
                            ]
                        }
                    
                    # Return the card response
                    async def browse_all_stream():
                        data = {"delta": "Browsing featured projects.", "adaptive_card": carousel_card, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(
                        browse_all_stream(),
                        media_type="text/event-stream"
                    )
                # --- New filter/browse actions ---
                elif action_type == "filter_by_status":
                    status = card_action.get("status")
                    from src.storage.event_data import get_event_data
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    filtered = [p for p in all_projects if p.get("status", "").lower() == status.lower()]
                    logger.info(f"Filtering by status: {status}, found {len(filtered)} projects.")
                    result_text = f"Found {len(filtered)} {status} projects."
                    async def status_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(status_stream(), media_type="text/event-stream")
                elif action_type == "equipment_filter":
                    equipment = card_action.get("equipment", "")
                    from src.storage.event_data import get_event_data
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    filtered = [p for p in all_projects if equipment.lower() in ", ".join(p.get("equipment", [])).lower()]
                    logger.info(f"Filtering by equipment: {equipment}, found {len(filtered)} projects.")
                    result_text = f"Found {len(filtered)} projects needing {equipment}."
                    async def equipment_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(equipment_stream(), media_type="text/event-stream")
                elif action_type == "filter_by_team_size":
                    min_size = card_action.get("min", 1)
                    max_size = card_action.get("max", 1000)
                    from src.storage.event_data import get_event_data
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    filtered = [p for p in all_projects if min_size <= len(p.get("team", [])) <= max_size]
                    logger.info(f"Filtering by team size: {min_size}-{max_size}, found {len(filtered)} projects.")
                    result_text = f"Found {len(filtered)} projects with team size {min_size}-{max_size}."
                    async def team_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(team_stream(), media_type="text/event-stream")
                elif action_type == "recording_filter":
                    available = card_action.get("available", "true").lower() == "true"
                    from src.storage.event_data import get_event_data
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    filtered = [p for p in all_projects if (p.get("recordingPermission", "").lower() == "yes") == available]
                    logger.info(f"Filtering by recording availability: {available}, found {len(filtered)} projects.")
                    result_text = f"Found {len(filtered)} projects with recording {'available' if available else 'not available'}."
                    async def recording_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(recording_stream(), media_type="text/event-stream")
                elif action_type == "filter_by_audience":
                    audience = card_action.get("audience", "")
                    from src.storage.event_data import get_event_data
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    filtered = [p for p in all_projects if audience.lower() in p.get("targetAudience", "").lower()]
                    logger.info(f"Filtering by audience: {audience}, found {len(filtered)} projects.")
                    result_text = f"Found {len(filtered)} projects for audience: {audience}."
                    async def audience_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(audience_stream(), media_type="text/event-stream")
                elif action_type == "filter_by_location":
                    location = card_action.get("location", "")
                    from src.storage.event_data import get_event_data
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    filtered = [p for p in all_projects if location.lower() in p.get("placement", "").lower()]
                    logger.info(f"Filtering by location: {location}, found {len(filtered)} projects.")
                    result_text = f"Found {len(filtered)} projects at {location}."
                    async def location_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(location_stream(), media_type="text/event-stream")
                elif action_type == "show_featured":
                    from src.storage.event_data import get_event_data
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    featured = [p for p in all_projects if p.get("featured", False)]
                    logger.info(f"Showing featured projects, found {len(featured)}.")
                    result_text = f"Found {len(featured)} featured projects."
                    async def featured_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(featured_stream(), media_type="text/event-stream")
                elif action_type == "recent_projects":
                    from src.storage.event_data import get_event_data
                    import datetime
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    # Assume 'date' field exists and is ISO format
                    recent = sorted(
                        [p for p in all_projects if p.get("date")],
                        key=lambda p: p.get("date"),
                        reverse=True
                    )[:5]
                    logger.info(f"Showing recent projects, found {len(recent)}.")
                    result_text = f"Found {len(recent)} recently added projects."
                    async def recent_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(recent_stream(), media_type="text/event-stream")
                elif action_type == "keyword_search":
                    keyword = card_action.get("keyword", "")
                    from src.storage.event_data import get_event_data
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    filtered = [p for p in all_projects if keyword.lower() in p.get("description", "").lower() or keyword.lower() in p.get("name", "").lower()]
                    logger.info(f"Keyword search: {keyword}, found {len(filtered)} projects.")
                    result_text = f"Found {len(filtered)} projects for keyword: {keyword}."
                    async def keyword_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(keyword_stream(), media_type="text/event-stream")
                elif action_type == "researcher_search":
                    researcher = card_action.get("researcher", "")
                    from src.storage.event_data import get_event_data
                    event_data = get_event_data()
                    all_projects = event_data.get("projects", [])
                    filtered = [p for p in all_projects if any(researcher.lower() in m.get("name", "").lower() for m in p.get("team", []))]
                    logger.info(f"Researcher search: {researcher}, found {len(filtered)} projects.")
                    
                    context.conversation_stage = "show_results"
                    logger.info(f"Updated context: {context.to_dict()}")
                    
                    result_text = f"Found {len(filtered)} projects for researcher: {researcher}."
                    result_card = generate_carousel_card(filtered, title="Research by " + researcher, subtitle=f"Showing {len(filtered)} projects")
                    
                    async def researcher_stream():
                        data = {"delta": result_text, "adaptive_card": result_card, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(researcher_stream(), media_type="text/event-stream")
                    context.conversation_stage = "show_results"
                    logger.info("Browse all projects action triggered.")
                    logger.info(f"Updated context: {context.to_dict()}")
                    async def browse_all_stream():
                        data = {"delta": "Browsing featured projects.", "adaptive_card": carousel_card, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(
                        browse_all_stream(),
                        media_type="text/event-stream"
                    )
                elif action_type == "researcher_search":
                    researcher = card_action.get("researcher")
                    if researcher:
                        context.add_researcher(researcher)
                        context.conversation_stage = "show_results"
                        logger.info(f"Researcher selected: {researcher}")
                        logger.info(f"Updated context: {context.to_dict()}")
                        result_text = f"Researcher '{researcher}' selected."
                    else:
                        logger.warning("researcher_search action received without researcher")
                        result_text = "No researcher provided."
                    async def researcher_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(
                        researcher_stream(),
                        media_type="text/event-stream"
                    )
                elif action_type == "recording_filter":
                    context.add_equipment_filter("recording")
                    context.conversation_stage = "show_results"
                    logger.info("Recording filter action triggered.")
                    logger.info(f"Updated context: {context.to_dict()}")
                    result_text = "Recording filter applied."
                    async def recording_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(
                        recording_stream(),
                        media_type="text/event-stream"
                    )
                else:
                    logger.warning(f"Unhandled card action: {action_type} | Payload: {card_action}")
                    result_text = f"Unhandled card action: {action_type}"
                    async def unhandled_stream():
                        data = {"delta": result_text, "context": context.to_dict()}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    return StreamingResponse(
                        unhandled_stream(),
                        media_type="text/event-stream"
                    )
            
            # Step 2: Try deterministic routing for non-card queries
            logger.info(f"Routing query: {user_query[:100]}...")
            router = DeterministicRouter()
            intent_type, confidence = router.classify(user_query)
            
            logger.info(
                "Intent classified",
                extra={
                    "intent": intent_type,
                    "confidence": confidence,
                    "is_deterministic": confidence >= router_config.deterministic_threshold
                }
            )
            
            # Step 2: Check if should delegate to Foundry
            if router_config.should_delegate_to_foundry(confidence):
                logger.info(
                    "Delegating to Foundry",
                    extra={
                        "confidence": confidence,
                        "threshold": router_config.foundry_delegation_threshold
                    }
                )
                
                # Delegate to Foundry agents
                try:
                    foundry_config = FoundryConfig(
                        endpoint=router_config.foundry_endpoint,
                        agent_id=router_config.foundry_agent_id
                    )
                    
                    async with FoundryClient(foundry_config) as foundry_client:
                        # Stream response from Foundry
                        async def foundry_stream():
                            async for delta in foundry_client.delegate_to_agent(
                                query=user_query,
                                conversation_history=[m.model_dump() for m in payload.messages[:-1]],
                                context={
                                    "intent": intent.intent_type,
                                    "confidence": intent.confidence
                                }
                            ):
                                yield delta
                        
                        return StreamingResponse(
                            foundry_stream(),
                            media_type="text/event-stream"
                        )
                
                except Exception as e:
                    logger.error(f"Foundry delegation failed, falling back to OpenAI: {e}")
                    # Fall through to Azure OpenAI
            
            # Step 3: Use deterministic result if high confidence
            if confidence >= router_config.deterministic_threshold:
                logger.info("Using deterministic routing result")
                
                # Import data access
                from src.storage.event_data import get_event_data
                
                # Get project data
                event_data = get_event_data()
                all_projects = event_data.get("projects", [])
                
                # Filter projects based on intent and query
                matching_projects = []
                query_lower = user_query.lower()
                
                # For general/conversational queries, provide a helpful interactive response
                if intent_type in ["general", "help", "conversational"] or "help me" in query_lower or "ask" in query_lower:
                    result_text = """I'd be happy to help you find projects! 🎓

To match you with relevant projects, I can search by:

**Research Areas:**
• 🤖 Artificial Intelligence & Machine Learning
• 💻 Systems & Networking
• 🖥️ Human-Computer Interaction
• 🔒 Security & Privacy
• 📊 Data Science & Analytics

**Or tell me:**
• Specific technologies or topics you're interested in
• Researchers or team members you'd like to work with
• Equipment needs (e.g., large displays, recording capabilities)

What would you like to explore first?"""
                    
                    async def conversational_stream():
                        # Format as SSE with proper JSON
                        data = {"delta": result_text}
                        yield f"data: {json.dumps(data)}\n\n"
                        yield "data: [DONE]\n\n"
                    
                    return StreamingResponse(
                        conversational_stream(),
                        media_type="text/event-stream"
                    )
                
                if intent_type == "project_search":
                    # Search for AI/ML projects or general keywords
                    keywords = ["ai", "artificial intelligence", "machine learning", "ml", "neural", "deep learning"]
                    for project in all_projects:
                        title = project.get("name", "").lower()
                        desc = project.get("description", "").lower()
                        area = project.get("researchArea", "").lower()
                        if any(kw in title or kw in desc or kw in area for kw in keywords):
                            matching_projects.append(project)
                            if len(matching_projects) >= 5:
                                break
                
                elif intent_type == "category_browse":
                    # Filter by research area
                    for project in all_projects:
                        area = project.get("researchArea", "")
                        if "AI" in area or "Artificial Intelligence" in area:
                            matching_projects.append(project)
                            if len(matching_projects) >= 5:
                                break
                
                elif intent_type == "people_lookup":
                    # Search by team member name
                    # Extract possible names from query
                    for project in all_projects:
                        team = project.get("team", [])
                        team_names = [m.get("name", "").lower() for m in team]
                        # Simple check if any name fragment in query matches team
                        if any(name_part in " ".join(team_names) for name_part in query_lower.split() if len(name_part) > 2):
                            matching_projects.append(project)
                            if len(matching_projects) >= 5:
                                break
                
                elif intent_type == "equipment_filter":
                    # Filter by equipment requirements
                    for project in all_projects:
                        equipment = project.get("equipment", "").lower()
                        if "display" in query_lower and "display" in equipment:
                            matching_projects.append(project)
                        elif "recording" in query_lower and equipment:
                            matching_projects.append(project)
                        if len(matching_projects) >= 5:
                            break
                
                # Build text response
                if matching_projects:
                    context.set_results(matching_projects)
                    context.conversation_stage = "show_results"
                    
                    result_text = f"✅ Found {len(matching_projects)} matching project(s):\n\n"
                    for i, project in enumerate(matching_projects[:5], 1):
                        name = project.get("name", "Untitled")
                        area = project.get("researchArea", "General")
                        team = ", ".join([m.get("name", "") for m in project.get("team", [])[:2]])
                        result_text += f"{i}. **{name}**\n"
                        result_text += f"   📚 Research Area: {area}\n"
                        result_text += f"   👥 Team: {team}\n"
                        desc = project.get("description", "")[:100]
                        if desc:
                            result_text += f"   📄 {desc}...\n"
                        result_text += f"   [View Details](#{project.get('id')})\n"
                        result_text += "\n"
                else:
                    result_text = f"No projects found matching '{user_query}'. Try browsing by category or searching for specific research areas."
                
                async def deterministic_stream():
                    # Format as SSE with proper JSON, include context
                    data = {
                        "delta": result_text,
                        "context": context.to_dict()
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(
                    deterministic_stream(),
                    media_type="text/event-stream"
                )
            
            # Step 4: Fall back to Azure OpenAI for general queries
            logger.info("Using Azure OpenAI for low-confidence query")
            
            # Check if Azure OpenAI is configured
            if not os.getenv("AZURE_OPENAI_ENDPOINT") or not os.getenv("AZURE_OPENAI_DEPLOYMENT"):
                error_msg = (
                    "Azure OpenAI is not configured. To enable AI chat, set AZURE_OPENAI_ENDPOINT "
                    "and AZURE_OPENAI_DEPLOYMENT in your .env file.\n\n"
                    f"Detected intent: {intent_type} (confidence: {confidence:.2f})\n"
                    "Currently running with mock data only."
                )
                
                async def config_error_stream():
                    yield error_msg
                
                return StreamingResponse(
                    config_error_stream(),
                    media_type="text/event-stream"
                )
            
            stream = _forward_stream(payload)
            return StreamingResponse(stream, media_type="text/event-stream")
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/config")
    async def chat_config():
        """Get chat service configuration and routing status."""
        from src.api.router_config import router_config
        
        return {
            "provider": "hybrid",
            "auth": "managed-identity",
            "endpoint": bool(os.getenv("AZURE_OPENAI_ENDPOINT")),
            "deployment": bool(os.getenv("AZURE_OPENAI_DEPLOYMENT")),
            "apiVersion": os.getenv("AZURE_OPENAI_VERSION", DEFAULT_API_VERSION),
            "capabilities": [
                "Project search and filtering",
                "Team member lookup",
                "Category browsing",
                "Session information",
                "Equipment and logistics",
                "Recording status"
            ],
            "routing": {
                "deterministic_enabled": router_config.enable_deterministic_routing,
                "deterministic_threshold": router_config.deterministic_threshold,
                "foundry_delegation_enabled": router_config.delegate_to_foundry,
                "foundry_delegation_threshold": router_config.foundry_delegation_threshold,
                "foundry_configured": bool(router_config.foundry_endpoint)
            }
        }

    return router
