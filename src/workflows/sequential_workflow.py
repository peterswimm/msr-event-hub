"""
Sequential workflow: Chain agents in order.

Use case: Writer → Reviewer → Editor pipeline
Each agent receives output from the previous agent.
"""

import logging
from typing import List

from agent_framework import ChatAgent, SequentialBuilder, Workflow

logger = logging.getLogger(__name__)


def create_sequential_workflow(
    agents: List[ChatAgent],
    workflow_name: str = "sequential_workflow"
) -> Workflow:
    """
    Create a sequential workflow where agents process in order.
    
    Example use case:
        # Knowledge extraction pipeline
        extractor = ChatAgent(...)  # Extracts raw info
        structurer = ChatAgent(...)  # Structures extracted info
        validator = ChatAgent(...)  # Validates structure
        
        workflow = create_sequential_workflow(
            agents=[extractor, structurer, validator],
            workflow_name="extraction_pipeline"
        )
        
        # Run the workflow
        async for message in workflow.run_stream("Extract knowledge from..."):
            print(message.text)
    
    Args:
        agents: List of ChatAgent instances to chain
        workflow_name: Optional name for the workflow
        
    Returns:
        Workflow instance ready to run
    """
    if len(agents) < 2:
        raise ValueError("Sequential workflow requires at least 2 agents")
    
    logger.info(
        f"Creating sequential workflow '{workflow_name}' with {len(agents)} agents: "
        f"{', '.join(a.name for a in agents if hasattr(a, 'name'))}"
    )
    
    # Build sequential workflow using Agent Framework
    workflow = (
        SequentialBuilder()
        .participants(agents)
        .build()
    )
    
    return workflow


# Example: Knowledge extraction sequential workflow
async def example_extraction_pipeline():
    """Example of extraction, structuring, and validation pipeline."""
    from agent_framework_azure_ai import AzureAIAgentClient
    from azure.identity import DefaultAzureCredential
    from config import get_settings
    
    settings = get_settings()
    
    # Agent 1: Extract raw information
    extractor = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="Extractor",
        ),
        instructions="""You are a knowledge extraction specialist.
        Extract key facts, concepts, and insights from the provided text.
        Focus on completeness - capture all important details."""
    )
    
    # Agent 2: Structure the extracted information
    structurer = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="Structurer",
        ),
        instructions="""You are a knowledge structuring specialist.
        Organize the extracted information into a clear, hierarchical structure.
        Create categories, relationships, and summaries."""
    )
    
    # Agent 3: Validate and refine
    validator = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="Validator",
        ),
        instructions="""You are a knowledge validation specialist.
        Verify the structured knowledge is accurate, complete, and well-formatted.
        Make final refinements and ensure quality."""
    )
    
    # Create workflow
    workflow = create_sequential_workflow(
        agents=[extractor, structurer, validator],
        workflow_name="extraction_pipeline"
    )
    
    # Run workflow
    task = "Extract knowledge from this research paper: [paper text here]"
    
    async for event in workflow.run_stream(task):
        if hasattr(event, 'text') and event.text:
            print(event.text, end='', flush=True)
    print()
    
    logger.info("✓ Extraction pipeline complete")
