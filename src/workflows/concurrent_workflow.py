"""
Concurrent workflow: Fan-out/fan-in parallel execution.

Use case: Multiple agents process the same input simultaneously,
results are aggregated (e.g., multiple reviewers, different extractors).
"""

import logging
from typing import Callable, List, Optional

from agent_framework import ChatAgent, ChatMessage, ConcurrentBuilder, Workflow

logger = logging.getLogger(__name__)


def create_concurrent_workflow(
    agents: List[ChatAgent],
    aggregator: Optional[Callable[[List[List[ChatMessage]]], List[ChatMessage]]] = None,
    workflow_name: str = "concurrent_workflow"
) -> Workflow:
    """
    Create a concurrent workflow where agents process simultaneously.
    
    Example use case:
        # Multiple reviewers evaluate independently
        reviewer1 = ChatAgent(...)  # Technical reviewer
        reviewer2 = ChatAgent(...)  # Domain expert
        reviewer3 = ChatAgent(...)  # User perspective
        
        workflow = create_concurrent_workflow(
            agents=[reviewer1, reviewer2, reviewer3],
            workflow_name="parallel_review"
        )
        
        # All reviewers process simultaneously
        async for message in workflow.run_stream("Review this artifact..."):
            print(message.text)
    
    Args:
        agents: List of ChatAgent instances to run in parallel
        aggregator: Optional function to combine agent outputs
                   Default: returns last message from each agent
        workflow_name: Optional name for the workflow
        
    Returns:
        Workflow instance ready to run
    """
    if len(agents) < 2:
        raise ValueError("Concurrent workflow requires at least 2 agents")
    
    logger.info(
        f"Creating concurrent workflow '{workflow_name}' with {len(agents)} agents: "
        f"{', '.join(a.name for a in agents if hasattr(a, 'name'))}"
    )
    
    # Build concurrent workflow using Agent Framework
    builder = ConcurrentBuilder().participants(agents)
    
    if aggregator:
        builder = builder.aggregator(aggregator)
    
    workflow = builder.build()
    
    return workflow


# Example: Multi-perspective knowledge extraction
async def example_multi_extractor():
    """Example of concurrent extraction from different perspectives."""
    from agent_framework_azure_ai import AzureAIAgentClient
    from azure.identity import DefaultAzureCredential
    from config import get_settings
    
    settings = get_settings()
    
    # Agent 1: Technical extractor
    technical_extractor = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="TechnicalExtractor",
        ),
        instructions="""Extract technical details, methods, algorithms, and implementations.
        Focus on how things work and technical specifications."""
    )
    
    # Agent 2: Impact extractor
    impact_extractor = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="ImpactExtractor",
        ),
        instructions="""Extract impact, applications, and real-world implications.
        Focus on why this matters and what problems it solves."""
    )
    
    # Agent 3: Novelty extractor
    novelty_extractor = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="NoveltyExtractor",
        ),
        instructions="""Extract novel contributions and innovations.
        Focus on what's new and different from prior work."""
    )
    
    # Optional: Custom aggregator that summarizes all perspectives
    def multi_perspective_aggregator(results: List[List[ChatMessage]]) -> List[ChatMessage]:
        """Combine multiple perspectives into comprehensive summary."""
        all_text = []
        for messages in results:
            if messages:
                all_text.append(messages[-1].text)
        
        combined = f"""## Multi-Perspective Knowledge Extraction

### Technical Perspective
{all_text[0] if len(all_text) > 0 else 'N/A'}

### Impact Perspective
{all_text[1] if len(all_text) > 1 else 'N/A'}

### Novelty Perspective
{all_text[2] if len(all_text) > 2 else 'N/A'}
"""
        return [ChatMessage(role="assistant", text=combined)]
    
    # Create workflow
    workflow = create_concurrent_workflow(
        agents=[technical_extractor, impact_extractor, novelty_extractor],
        aggregator=multi_perspective_aggregator,
        workflow_name="multi_perspective_extraction"
    )
    
    # Run workflow (all agents process simultaneously)
    task = "Analyze this research paper: [paper text here]"
    
    async for event in workflow.run_stream(task):
        if hasattr(event, 'text') and event.text:
            print(event.text, end='', flush=True)
    print()
    
    logger.info("✓ Multi-perspective extraction complete")
