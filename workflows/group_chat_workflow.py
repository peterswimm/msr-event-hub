"""
Group Chat workflow: Manager-directed multi-agent collaboration.

Use case: Manager agent coordinates multiple specialists,
selecting who speaks next based on the conversation state.
"""

import logging
from typing import Dict, Optional

from agent_framework import ChatAgent, GroupChatBuilder, Workflow

logger = logging.getLogger(__name__)


def create_group_chat_workflow(
    participants: Dict[str, ChatAgent],
    manager: Optional[ChatAgent] = None,
    manager_instructions: Optional[str] = None,
    max_rounds: Optional[int] = None,
    workflow_name: str = "group_chat_workflow"
) -> Workflow:
    """
    Create a group chat workflow with manager-directed orchestration.
    
    The manager agent decides which participant speaks next based on:
    - Conversation history
    - Participant descriptions
    - Task requirements
    
    Example use case:
        # Coordinator manages specialists
        manager = ChatAgent(...)  # Decides who speaks next
        
        participants = {
            "researcher": ChatAgent(...),  # Gathers facts
            "analyzer": ChatAgent(...),    # Analyzes findings
            "writer": ChatAgent(...),      # Synthesizes final output
        }
        
        workflow = create_group_chat_workflow(
            participants=participants,
            manager=manager,
            max_rounds=10,
            workflow_name="research_collaboration"
        )
        
        # Manager orchestrates the conversation
        async for message in workflow.run_stream("Research topic X..."):
            print(message.text)
    
    Args:
        participants: Dict mapping names to ChatAgent instances
        manager: Optional manager agent for speaker selection
                If None, uses default manager with LLM-based selection
        manager_instructions: Optional custom instructions for manager
        max_rounds: Optional limit on conversation rounds
        workflow_name: Optional name for the workflow
        
    Returns:
        Workflow instance ready to run
    """
    if len(participants) < 2:
        raise ValueError("Group chat requires at least 2 participants")
    
    logger.info(
        f"Creating group chat workflow '{workflow_name}' with "
        f"{len(participants)} participants: {', '.join(participants.keys())}"
    )
    
    # Build group chat using Agent Framework
    builder = GroupChatBuilder()
    
    # Add participants
    builder = builder.participants(**participants)
    
    # Configure manager
    if manager:
        builder = builder.set_manager(
            manager=manager,
            display_name="Manager"
        )
    else:
        # Use default manager with custom instructions if provided
        from agent_framework_azure_ai import AzureAIAgentClient
        from azure.identity import DefaultAzureCredential
        from config import get_settings
        
        settings = get_settings()
        
        default_manager = AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="GroupChatManager",
        ).create_agent(
            instructions=manager_instructions or _default_manager_instructions()
        )
        
        builder = builder.set_manager(
            manager=default_manager,
            display_name="Coordinator"
        )
    
    # Set max rounds if specified
    if max_rounds:
        builder = builder.max_rounds(max_rounds)
    
    workflow = builder.build()
    
    return workflow


def _default_manager_instructions() -> str:
    """Default instructions for group chat manager."""
    return """You are coordinating a team of specialists to accomplish the user's task.

Your role:
1. Review the conversation history
2. Determine which specialist should speak next
3. Decide when the task is complete

Guidelines:
- Start with information gathering (researchers)
- Then move to analysis and synthesis
- Only finish after all necessary specialists have contributed
- Allow for iterative refinement if needed

Be strategic in your orchestration to produce comprehensive results."""


# Example: Knowledge extraction collaboration
async def example_extraction_group_chat():
    """Example of coordinated knowledge extraction."""
    from agent_framework_azure_ai import AzureAIAgentClient
    from azure.identity import DefaultAzureCredential
    from config import get_settings
    
    settings = get_settings()
    
    # Create specialized agents
    researcher = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="Researcher",
        ),
        name="Researcher",
        description="Gathers facts and information from source material",
        instructions="""Extract factual information, data points, and key details.
        Provide comprehensive notes that others can build upon."""
    )
    
    analyzer = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="Analyzer",
        ),
        name="Analyzer",
        description="Analyzes patterns and relationships in gathered information",
        instructions="""Analyze the information gathered by the researcher.
        Identify patterns, connections, and key themes."""
    )
    
    synthesizer = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="Synthesizer",
        ),
        name="Synthesizer",
        description="Creates final structured knowledge artifact",
        instructions="""Synthesize the research and analysis into a final knowledge artifact.
        Create clear structure with title, summary, and key points."""
    )
    
    # Create group chat workflow
    participants = {
        "researcher": researcher,
        "analyzer": analyzer,
        "synthesizer": synthesizer,
    }
    
    workflow = create_group_chat_workflow(
        participants=participants,
        max_rounds=8,
        workflow_name="knowledge_extraction_collaboration"
    )
    
    # Run workflow (manager orchestrates the conversation)
    task = "Extract and structure knowledge from this research paper: [paper text]"
    
    print("Starting collaborative knowledge extraction...\n")
    
    async for event in workflow.run_stream(task):
        if hasattr(event, 'text') and event.text:
            print(event.text, end='', flush=True)
    print()
    
    logger.info("✓ Collaborative extraction complete")


# Export
__all__ = [
    "create_group_chat_workflow",
    "example_extraction_group_chat",
]
