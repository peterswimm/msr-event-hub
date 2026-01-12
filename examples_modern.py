"""
Example: Complete modern agent workflow with all features.

Demonstrates:
- Agent Framework setup
- Tracing and observability
- Multi-agent workflows
- Tool integration
- Evaluation
"""

import asyncio
import logging

from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity import DefaultAzureCredential

from config import get_settings
from observability import setup_tracing
from workflows import create_sequential_workflow, create_concurrent_workflow
from tools import create_mcp_tools, MICROSOFT_LEARN_MCP, get_text_analysis_tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_agent():
    """Example 1: Basic agent with streaming."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Agent with Streaming")
    print("=" * 60 + "\n")
    
    # Setup
    setup_tracing()
    settings = get_settings()
    
    # Create agent
    agent = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="BasicAgent",
        ),
        instructions="You are a helpful knowledge extraction agent."
    )
    
    # Run with streaming
    thread = agent.get_new_thread()
    
    print("User: Hello! What can you help me with?\n")
    print("Agent: ", end="", flush=True)
    
    async for chunk in agent.run_stream("Hello! What can you help me with?", thread=thread):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    
    print("\n")
    logger.info("✓ Basic agent example complete")


async def example_agent_with_tools():
    """Example 2: Agent with function calling tools."""
    print("\n" + "=" * 60)
    print("Example 2: Agent with Function Tools")
    print("=" * 60 + "\n")
    
    settings = get_settings()
    
    # Get text analysis tools
    tools = get_text_analysis_tools()
    
    # Create agent with tools
    agent = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="ToolAgent",
        ),
        instructions="""You are a text analysis agent with access to tools for:
        - Extracting metadata (word count, reading time)
        - Finding citations
        - Extracting code blocks
        - Calculating readability
        
        Use these tools when analyzing text.""",
        tools=tools
    )
    
    sample_text = """
    This is a sample research paper [Smith, 2024].
    
    Here's some Python code:
    ```python
    def hello():
        print("Hello, world!")
    ```
    
    The paper discusses important findings about AI agents.
    """
    
    thread = agent.get_new_thread()
    
    print(f"User: Analyze this text:\n{sample_text}\n")
    print("Agent: ", end="", flush=True)
    
    async for chunk in agent.run_stream(f"Analyze this text and provide statistics:\n{sample_text}", thread=thread):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    
    print("\n")
    logger.info("✓ Tool agent example complete")


async def example_sequential_workflow():
    """Example 3: Sequential workflow (pipeline)."""
    print("\n" + "=" * 60)
    print("Example 3: Sequential Workflow (Pipeline)")
    print("=" * 60 + "\n")
    
    settings = get_settings()
    
    # Create pipeline agents
    extractor = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="Extractor",
        ),
        instructions="Extract key facts and information. Be thorough."
    )
    
    structurer = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="Structurer",
        ),
        instructions="Organize the extracted information into clear structure."
    )
    
    # Create workflow
    workflow = create_sequential_workflow(
        agents=[extractor, structurer],
        workflow_name="extraction_pipeline"
    )
    
    print("User: Extract and structure knowledge from this text:\n'AI agents are transforming software development.'\n")
    print("Workflow: ", end="", flush=True)
    
    async for message in workflow.run_stream("Extract and structure knowledge from: 'AI agents are transforming software development.'"):
        if hasattr(message, 'text') and message.text:
            print(message.text, end="", flush=True)
    
    print("\n")
    logger.info("✓ Sequential workflow example complete")


async def example_concurrent_workflow():
    """Example 4: Concurrent workflow (parallel processing)."""
    print("\n" + "=" * 60)
    print("Example 4: Concurrent Workflow (Parallel)")
    print("=" * 60 + "\n")
    
    settings = get_settings()
    
    # Create parallel reviewers
    technical_reviewer = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="TechnicalReviewer",
        ),
        instructions="Review from technical perspective. Focus on accuracy."
    )
    
    clarity_reviewer = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="ClarityReviewer",
        ),
        instructions="Review from clarity perspective. Focus on readability."
    )
    
    # Create workflow
    workflow = create_concurrent_workflow(
        agents=[technical_reviewer, clarity_reviewer],
        workflow_name="parallel_review"
    )
    
    print("User: Review this extraction: 'The system uses transformers for NLP tasks.'\n")
    print("Workflow (parallel): ", end="", flush=True)
    
    async for message in workflow.run_stream("Review this extraction: 'The system uses transformers for NLP tasks.'"):
        if hasattr(message, 'text') and message.text:
            print(message.text, end="", flush=True)
    
    print("\n")
    logger.info("✓ Concurrent workflow example complete")


async def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("MODERN KNOWLEDGE AGENT EXAMPLES")
    print("=" * 60)
    
    try:
        # Run examples
        await example_basic_agent()
        await example_agent_with_tools()
        await example_sequential_workflow()
        await example_concurrent_workflow()
        
        print("\n" + "=" * 60)
        print("✓ ALL EXAMPLES COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("- View traces: AI Toolkit -> View Trace")
        print("- Try group chat: workflows/group_chat_workflow.py")
        print("- Add MCP tools: tools/mcp_tools.py")
        print("- Run evaluation: evaluation/runner.py")
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
