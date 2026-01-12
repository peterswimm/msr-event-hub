# Quick Start: Modernized Knowledge Agent

## 1. Install Dependencies

```bash
# IMPORTANT: Use --pre flag for Agent Framework preview
pip install --pre agent-framework-azure-ai azure-ai-evaluation azure-identity
```

## 2. Configure Environment

Create/update `.env`:

```bash
# Required: Microsoft Foundry Project
FOUNDRY_PROJECT_ENDPOINT=https://your-project.api.azureml.ms
FOUNDRY_MODEL_DEPLOYMENT=gpt-4o

# Optional: For evaluation judge models
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key

# Observability
ENABLE_TRACING=true
```

## 3. Enable Tracing (Optional but Recommended)

In VS Code:
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Run: **"AI Toolkit: Start Trace Collector"**
3. This starts OTLP collector for trace viewing

## 4. Run Your First Modern Agent

```python
import asyncio
from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity import DefaultAzureCredential
from config import get_settings
from observability import setup_tracing

async def main():
    # Setup
    setup_tracing()  # Initialize observability
    settings = get_settings()
    
    # Create agent
    agent = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="MyAgent",
        ),
        instructions="You are a helpful knowledge extraction agent."
    )
    
    # Run with streaming
    thread = agent.get_new_thread()
    
    print("Agent: ", end="", flush=True)
    async for chunk in agent.run_stream("Hello! What can you do?", thread=thread):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())
```

## 5. View Traces

After running your agent:
1. Press `Ctrl+Shift+P` again
2. Run: **"AI Toolkit: View Trace"**
3. See LLM calls, tokens, latency, and more!

## 6. Try Multi-Agent Workflows

```python
from workflows import create_sequential_workflow

# Create multiple specialized agents
extractor = ChatAgent(...)  # Extracts info
structurer = ChatAgent(...) # Structures data
validator = ChatAgent(...)  # Validates output

# Chain them together
workflow = create_sequential_workflow(
    agents=[extractor, structurer, validator]
)

# Run the workflow
async for message in workflow.run_stream("Process this..."):
    print(message.text)
```

## 7. Add Tool Capabilities

```python
from tools import create_mcp_tools, MICROSOFT_LEARN_MCP

# Give agent access to external tools
tools = create_mcp_tools([MICROSOFT_LEARN_MCP])

agent = ChatAgent(
    chat_client=client,
    instructions="You can search Microsoft documentation.",
    tools=tools  # Now agent can call MCP tools
)
```

## 8. Run Evaluation

```python
from evaluation import EvaluationRunner, create_sample_paper_dataset

# Create test data
test_dataset = create_sample_paper_dataset()

# Run evaluation
runner = EvaluationRunner(agent=my_agent)
results = await runner.run_evaluation(test_dataset)

print(f"Score: {results['summary']['avg_structure_score']}")
```

---

## 🎯 What You Get

✅ **Agent Framework** - Modern agent abstraction  
✅ **Automatic Tracing** - See every LLM call  
✅ **Multi-Agent Workflows** - Sequential, concurrent, group chat  
✅ **Tool Integration** - MCP, function calling  
✅ **Evaluation Framework** - Automated testing  
✅ **Production Ready** - Config management, error handling  

---

## 📚 Learn More

- See [MODERNIZATION_GUIDE.md](MODERNIZATION_GUIDE.md) for full details
- Check `workflows/` for orchestration examples
- Explore `tools/` for MCP and function tools
- Review `evaluation/` for testing patterns

**Happy building! 🚀**
