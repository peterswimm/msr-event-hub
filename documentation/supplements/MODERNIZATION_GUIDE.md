# Knowledge Agent POC - Modernized Architecture

## 🚀 What Changed

This workspace has been **comprehensively modernized** for production-ready agentic development with:

### ✅ Modern Agent Framework
- **Before:** Direct LLM client calls (OpenAI, Azure OpenAI)
- **After:** Microsoft Agent Framework with built-in orchestration
- **Benefits:** Multi-agent workflows, automatic tracing, tool calling, streaming

### ✅ Observability & Tracing
- **New:** Distributed tracing with OpenTelemetry
- **New:** Automatic LLM call telemetry (prompts, tokens, latency)
- **New:** Agent decision logging
- **View traces:** AI Toolkit integration

### ✅ Evaluation Framework
- **New:** Automated evaluation with Azure AI Evaluation SDK
- **New:** Built-in + custom evaluators
- **New:** Test datasets and agent runner
- **New:** Regression testing support

### ✅ Multi-Agent Orchestration
- **New:** Sequential workflows (pipeline pattern)
- **New:** Concurrent workflows (fan-out/fan-in)
- **New:** Group chat workflows (manager-directed)
- **New:** Agent-to-agent handoffs

### ✅ Tool Integration
- **New:** MCP (Model Context Protocol) support
- **New:** Function calling with custom tools
- **New:** OpenAPI integration ready

### ✅ Configuration Management
- **New:** `pyproject.toml` for modern Python packaging
- **New:** Structured settings with validation
- **New:** Environment-specific configs

---

## 📁 New Structure

```
knowledge-agent-poc/
├── config/                    # ⭐ NEW: Configuration management
│   ├── __init__.py
│   └── settings.py           # Centralized settings with validation
│
├── observability/            # ⭐ NEW: Tracing & monitoring
│   ├── __init__.py
│   └── tracing.py           # OpenTelemetry setup
│
├── evaluation/               # ⭐ NEW: Evaluation framework
│   ├── __init__.py
│   ├── evaluators.py        # Custom evaluators
│   ├── runner.py            # Evaluation orchestration
│   └── datasets.py          # Test dataset utilities
│
├── workflows/                # ⭐ NEW: Multi-agent patterns
│   ├── __init__.py
│   ├── sequential_workflow.py    # Pipeline pattern
│   ├── concurrent_workflow.py    # Parallel execution
│   └── group_chat_workflow.py    # Manager-directed
│
├── tools/                    # ⭐ NEW: Tool integration
│   ├── __init__.py
│   ├── mcp_tools.py         # Model Context Protocol
│   └── function_tools.py    # Custom function calling
│
├── agents/
│   ├── modern_base_agent.py # ⭐ NEW: Agent Framework base
│   ├── base_agent.py        # Legacy (for reference)
│   ├── paper_agent.py
│   ├── talk_agent.py
│   └── repository_agent.py
│
├── pyproject.toml           # ⭐ NEW: Modern Python config
├── requirements.txt         # ⭐ UPDATED: New dependencies
└── .env                     # ⭐ UPDATE THIS: New config needed
```

---

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
# Install with preview flag (Agent Framework is in preview)
pip install --pre -r requirements.txt

# Or use specific package
pip install --pre agent-framework-azure-ai
```

### 2. Configure Environment

Update your `.env` file with new required settings:

```bash
# Microsoft Foundry (Azure AI Foundry) - REQUIRED
FOUNDRY_PROJECT_ENDPOINT=https://your-project.api.azureml.ms
FOUNDRY_MODEL_DEPLOYMENT=gpt-4o

# Legacy Azure OpenAI (optional - for evaluation judge model)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your-key
AZURE_OPENAI_API_VERSION=2024-12-01-preview

# Agent Settings
AGENT_TEMPERATURE=0.3
AGENT_MAX_TOKENS=4096

# Observability
ENABLE_TRACING=true
OTLP_ENDPOINT=http://localhost:4317
ENABLE_SENSITIVE_DATA=true

# Evaluation
EVALUATION_OUTPUT_DIR=./outputs/evaluation
```

### 3. Start Trace Collector (for observability)

**Before running agents with tracing:**

1. Open VS Code Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Run: **"AI Toolkit: Start Trace Collector"**
3. This starts the OTLP collector at `http://localhost:4317`

**After running agents:**
4. Run: **"AI Toolkit: View Trace"** to visualize traces

---

## 📚 Usage Examples

### Basic Agent (Modern Framework)

```python
import asyncio
from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIAgentClient
from azure.identity import DefaultAzureCredential
from config import get_settings
from observability import setup_tracing

async def main():
    # Setup tracing
    setup_tracing()
    
    settings = get_settings()
    
    # Create agent
    agent = ChatAgent(
        chat_client=AzureAIAgentClient(
            project_endpoint=settings.foundry_project_endpoint,
            model_deployment_name=settings.foundry_model_deployment,
            async_credential=DefaultAzureCredential(),
            agent_name="KnowledgeExtractor",
        ),
        instructions="You extract structured knowledge from text."
    )
    
    # Run with streaming
    thread = agent.get_new_thread()
    async for chunk in agent.run_stream("Extract key points from..."):
        if chunk.text:
            print(chunk.text, end='', flush=True)

asyncio.run(main())
```

### Sequential Workflow (Pipeline)

```python
from workflows import create_sequential_workflow

# Create pipeline: Extract → Structure → Validate
workflow = create_sequential_workflow(
    agents=[extractor, structurer, validator],
    workflow_name="extraction_pipeline"
)

# Run pipeline
async for message in workflow.run_stream("Process this paper..."):
    print(message.text)
```

### Concurrent Workflow (Parallel)

```python
from workflows import create_concurrent_workflow

# Multiple perspectives simultaneously
workflow = create_concurrent_workflow(
    agents=[technical_reviewer, domain_expert, user_reviewer],
    workflow_name="parallel_review"
)

async for message in workflow.run_stream("Review this extraction..."):
    print(message.text)
```

### Group Chat (Manager-Directed)

```python
from workflows import create_group_chat_workflow

participants = {
    "researcher": researcher_agent,
    "analyzer": analyzer_agent,
    "synthesizer": synthesizer_agent,
}

workflow = create_group_chat_workflow(
    participants=participants,
    max_rounds=10,
    workflow_name="collaborative_extraction"
)

async for message in workflow.run_stream("Extract knowledge..."):
    print(message.text)
```

### Agent with MCP Tools

```python
from tools import create_mcp_tools, MICROSOFT_LEARN_MCP, GITHUB_MCP

# Add external tool access
mcp_tools = create_mcp_tools([MICROSOFT_LEARN_MCP, GITHUB_MCP])

agent = ChatAgent(
    chat_client=client,
    instructions="You can search docs and analyze repos.",
    tools=mcp_tools  # Agent can now call external tools
)
```

### Agent with Function Tools

```python
from tools import get_text_analysis_tools

# Add custom Python functions
tools = get_text_analysis_tools()  # metadata, citations, code blocks

agent = ChatAgent(
    chat_client=client,
    instructions="You can analyze text structure.",
    tools=tools  # Agent can call Python functions
)
```

### Evaluation

```python
from evaluation import EvaluationRunner, create_test_dataset

# Create test dataset
test_dataset = create_test_dataset(
    test_cases=[
        {"source_text": "...", "expected_title": "..."},
        # more cases...
    ],
    output_path="./evaluation/datasets/test.jsonl"
)

# Run evaluation
runner = EvaluationRunner(agent=my_agent)
results = await runner.run_evaluation(
    test_dataset=test_dataset,
    run_name="paper_extraction_v1"
)

print(f"Avg structure score: {results['metrics']['structure_completeness_score']}")
```

---

## 🔄 Migration from Legacy Code

### Legacy Pattern (OLD)
```python
# Direct LLM client usage
from openai import AzureOpenAI

client = AzureOpenAI(...)
response = client.chat.completions.create(...)
```

### Modern Pattern (NEW)
```python
# Agent Framework
from agent_framework import ChatAgent
from agent_framework_azure_ai import AzureAIAgentClient

agent = ChatAgent(chat_client=AzureAIAgentClient(...))
result = await agent.run("query")  # Automatic tracing, tools, etc.
```

---

## 🎯 Key Benefits

| Feature | Before | After |
|---------|--------|-------|
| **Agent Framework** | ❌ Manual LLM calls | ✅ Standardized agent interface |
| **Tracing** | ❌ None | ✅ Automatic with OpenTelemetry |
| **Multi-Agent** | ❌ Manual coordination | ✅ Built-in patterns (sequential, concurrent, group chat) |
| **Tool Calling** | ❌ Manual | ✅ MCP + function calling support |
| **Evaluation** | ❌ Manual testing | ✅ Automated framework with metrics |
| **Config** | ❌ Scattered .env | ✅ Structured + validated |

---

## 📖 Additional Resources

- **Agent Framework Docs:** [github.com/microsoft/agent-framework](https://github.com/microsoft/agent-framework)
- **Azure AI Evaluation:** [Azure SDK Docs](https://learn.microsoft.com/azure/ai-services/)
- **MCP Protocol:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **AI Toolkit:** VS Code extension for tracing & debugging

---

## 🚦 Next Steps

1. **Update .env** with Foundry endpoint and credentials
2. **Install dependencies** with `--pre` flag
3. **Start trace collector** in AI Toolkit
4. **Run example** from `workflows/` to test setup
5. **Create evaluation dataset** for your agents
6. **Explore MCP tools** for external integrations

---

## 💡 Tips

- **Always use async/await:** Agent Framework is async-first
- **Stream by default:** Use `run_stream()` for better UX
- **Enable tracing:** View traces in AI Toolkit for debugging
- **Test with evaluation:** Catch regressions early
- **Use workflows:** Don't coordinate manually - use patterns

---

**Your workspace is now optimized for production-ready agentic development! 🎉**
