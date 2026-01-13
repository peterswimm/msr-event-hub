"""Example usage of Knowledge Agent API without FastAPI (programmatic).

This demonstrates:
- Creating application context with repositories
- Working with events, sessions, projects, knowledge artifacts
- Saving/loading data from JSON storage
"""

from pathlib import Path
from datetime import datetime, timedelta

from main import ApplicationContext
from core.event_models import Event, Session, EventType, EventStatus, SessionType
from projects.models import ProjectDefinition
from core.knowledge_models import KnowledgeArtifact, PKAProvenance, ApprovalStatus


def example_create_event_and_project():
    """Example: Create an event with a project and knowledge artifacts."""
    
    # Initialize application context (creates ./example_data directory)
    ctx = ApplicationContext(storage_root=Path("./example_data"))
    
    print("=" * 70)
    print("Knowledge Agent API - Programmatic Example")
    print("=" * 70)
    
    # ===== Create Event =====
    print("\n1. Creating Event...")
    event = Event(
        id="evt_jan2026",
        display_name="January 2026 Research Summit",
        description="Quarterly research summit for ML & AI",
        event_type=EventType.RESEARCH_CONFERENCE,
        status=EventStatus.PLANNING,
        start_date=datetime(2026, 1, 15),
        end_date=datetime(2026, 1, 17),
        time_zone="UTC",
        location="Virtual",
        odata_type="#microsoft.graph.event",
    )
    ctx.event_repo.create(event)
    print(f"   ✓ Created event: {event.display_name}")
    
    # ===== Create Sessions =====
    print("\n2. Creating Sessions for the Event...")
    session1 = Session(
        id="sess_001",
        event_id="evt_jan2026",
        title="Knowledge Extraction Keynote",
        session_type=SessionType.KEYNOTE,
        description="Deep dive into modern knowledge extraction techniques",
        start_date_time=datetime(2026, 1, 15, 9, 0),
        end_date_time=datetime(2026, 1, 15, 10, 30),
        location="Ballroom A",
        odata_type="#microsoft.graph.session",
    )
    ctx.session_repo.create(session1)
    print(f"   ✓ Created session: {session1.title}")
    
    # ===== Create Project (event-scoped) =====
    print("\n3. Creating Project (event-scoped)...")
    project = ProjectDefinition(
        id="proj_kex_summit",
        event_id="evt_jan2026",  # Phase B: Now required
        name="Knowledge Extraction from Summit Content",
        description="Extract and structure knowledge from summit sessions",
        research_area="Knowledge Management",
        odata_type="#microsoft.graph.project",
    )
    ctx.project_repo.create(project)
    print(f"   ✓ Created project: {project.name}")
    
    # ===== Create Knowledge Artifacts (draft PKA) =====
    print("\n4. Creating Knowledge Artifacts (draft)...")
    artifact1 = KnowledgeArtifact(
        id="artifact_001",
        project_id="proj_kex_summit",
        title="Modern Knowledge Extraction Techniques",
        plain_language_overview="Survey of state-of-the-art methods for extracting structured knowledge from unstructured text",
        provenance=PKAProvenance(
            agent_name="ExtractionAgent",
            agent_version="1.0.0",
            prompt_version="2.1",
            run_date_time=datetime.now(),
        ),
        approval_status=ApprovalStatus.DRAFT,
        odata_type="#microsoft.graph.knowledgeArtifact",
    )
    ctx.artifact_repo.create(artifact1)
    print(f"   ✓ Created artifact: {artifact1.title}")
    print(f"     Status: {artifact1.approval_status.value}")
    
    # ===== List Projects by Event =====
    print("\n5. Listing Projects in Event...")
    event_projects = ctx.project_repo.list_by_event("evt_jan2026")
    print(f"   ✓ Found {len(event_projects)} projects in event")
    for p in event_projects:
        print(f"     - {p.name}")
    
    # ===== List Sessions by Event =====
    print("\n6. Listing Sessions in Event...")
    event_sessions = ctx.session_repo.list_by_event("evt_jan2026")
    print(f"   ✓ Found {len(event_sessions)} sessions in event")
    for s in event_sessions:
        print(f"     - {s.title}")
    
    # ===== List Artifacts by Status =====
    print("\n7. Listing Artifacts by Status...")
    draft_artifacts = ctx.artifact_repo.list_by_status(ApprovalStatus.DRAFT)
    print(f"   ✓ Found {len(draft_artifacts)} draft artifacts")
    for a in draft_artifacts:
        print(f"     - {a.title} (project: {a.project_id})")
    
    # ===== Health Check =====
    print("\n8. Health Status...")
    health = ctx.get_health_status()
    print(f"   ✓ Status: {health['status']}")
    print(f"   ✓ Storage: {health['storage_root']}")
    
    print("\n" + "=" * 70)
    print("Example complete! Data saved to ./example_data/")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    example_create_event_and_project()
