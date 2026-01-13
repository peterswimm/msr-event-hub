"""
Custom function tools for agents.

Function calling allows agents to invoke Python functions
to perform actions like:
- Data extraction
- Calculations
- API calls
- File operations
"""

import logging
from typing import Annotated, Callable, List

logger = logging.getLogger(__name__)


def create_function_tool(func: Callable) -> Callable:
    """
    Wrap a function for use as an agent tool.
    
    The function should:
    1. Have clear docstring (used as description)
    2. Use Annotated types for parameters (used for schema)
    3. Return structured data (str, dict, list, etc.)
    
    Args:
        func: Function to wrap as a tool
        
    Returns:
        Tool-ready function
    """
    # Agent Framework automatically handles function tools
    # Just ensure proper annotations and docstrings
    return func


# Example knowledge extraction tools


def extract_metadata(
    text: Annotated[str, "The text to extract metadata from"],
) -> dict:
    """
    Extract metadata like word count, reading time from text.
    
    Args:
        text: Input text to analyze
        
    Returns:
        Dict with metadata statistics
    """
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    reading_time_minutes = word_count / 200  # Average reading speed
    
    return {
        "word_count": word_count,
        "character_count": char_count,
        "reading_time_minutes": round(reading_time_minutes, 1),
        "estimated_pages": word_count / 250,  # Assuming 250 words per page
    }


def extract_citations(
    text: Annotated[str, "Text containing citations"],
) -> List[str]:
    """
    Extract citation references from academic text.
    
    Args:
        text: Text containing citations
        
    Returns:
        List of citation strings found
    """
    import re
    
    # Simple citation pattern: [Author, Year]
    citation_pattern = r'\[([A-Za-z\s]+,\s*\d{4})\]'
    citations = re.findall(citation_pattern, text)
    
    return citations


def extract_code_blocks(
    text: Annotated[str, "Text containing code blocks"],
) -> List[dict]:
    """
    Extract code blocks from markdown/documentation.
    
    Args:
        text: Text with code blocks
        
    Returns:
        List of dicts with language and code content
    """
    import re
    
    # Match ```language\ncode\n```
    pattern = r'```(\w+)?\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    code_blocks = []
    for language, code in matches:
        code_blocks.append({
            "language": language or "unknown",
            "code": code.strip()
        })
    
    return code_blocks


def calculate_readability(
    text: Annotated[str, "Text to analyze readability"],
) -> dict:
    """
    Calculate readability metrics for text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dict with readability scores
    """
    sentences = text.count('.') + text.count('!') + text.count('?')
    words = len(text.split())
    
    if sentences == 0:
        sentences = 1
    
    avg_sentence_length = words / sentences
    
    # Simple readability assessment
    if avg_sentence_length < 15:
        level = "Easy"
    elif avg_sentence_length < 25:
        level = "Moderate"
    else:
        level = "Complex"
    
    return {
        "average_sentence_length": round(avg_sentence_length, 1),
        "readability_level": level,
        "total_sentences": sentences,
    }


# Pre-configured tool sets for knowledge extraction

def get_text_analysis_tools() -> List[Callable]:
    """Get tools for text analysis."""
    return [
        extract_metadata,
        extract_citations,
        extract_code_blocks,
        calculate_readability,
    ]


# Example: Agent with custom function tools
async def example_agent_with_tools():
    """Example of creating an agent with custom function tools."""
    from agent_framework import ChatAgent
    from agent_framework_azure_ai import AzureAIAgentClient
    from azure.identity import DefaultAzureCredential
    from config import get_settings
    
    settings = get_settings()
    
    # Get tools
    tools = get_text_analysis_tools()
    
    # Create agent with tools
    agent = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="AnalysisAgent",
        ),
        instructions="""You are a text analysis agent.
        
        You have access to tools for:
        - Extracting metadata (word count, reading time)
        - Finding citations
        - Extracting code blocks
        - Calculating readability
        
        Use these tools to provide comprehensive analysis.""",
        tools=tools
    )
    
    # Agent will automatically use tools when appropriate
    thread = agent.get_new_thread()
    
    sample_text = """
    This is a sample research paper [Smith, 2024].
    
    Here's some code:
    ```python
    def hello():
        print("Hello, world!")
    ```
    
    The paper discusses important findings.
    """
    
    task = f"Analyze this text and provide detailed statistics:\n\n{sample_text}"
    
    print("Agent with function tools:\n")
    async for chunk in agent.run_stream(task, thread=thread):
        if chunk.text:
            print(chunk.text, end='', flush=True)
    
    print("\n✓ Analysis complete")


__all__ = [
    "create_function_tool",
    "extract_metadata",
    "extract_citations",
    "extract_code_blocks",
    "calculate_readability",
    "get_text_analysis_tools",
]
