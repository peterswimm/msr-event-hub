# Chat Examples & Workflows

This directory contains example code and sample workflows for the MSR Event Agent Chat system.

---

## 📁 Directory Structure

```
examples/
├── workflows/              # Complex multi-step workflows
├── chat-actions/          # Individual action examples
├── integration/           # Integration patterns
└── README.md             # This file
```

---

## 🔄 Workflows

Complete example workflows that demonstrate end-to-end usage:

### workflow_example.py

**Purpose**: End-to-end project evaluation workflow with iteration

**Key Features**:
- Complete workflow from artifact collection to output
- Shows how to chain multiple operations
- Demonstrates error handling and retries
- Includes progress tracking

**Usage**:
```bash
python examples/workflows/workflow_example.py
# or with custom storage:
python examples/workflows/workflow_example.py --storage-dir ./my_data
```

**What It Does**:
1. Loads research project data
2. Evaluates project quality using AI agents
3. Iterates based on feedback
4. Produces structured output (Heilmeier catechism)

**Key Concepts Shown**:
- Project loading and validation
- Agent-based evaluation
- Iteration and refinement
- Output formatting

### poc_workflow.py

**Purpose**: POC (Proof of Concept) workflow demonstrating knowledge extraction

**Key Features**:
- 7-step knowledge extraction pipeline
- Grouping related artifacts (papers, videos, code)
- AI-powered knowledge synthesis
- Clean separation of concerns

**Usage**:
```bash
python examples/workflows/poc_workflow.py
```

**What It Does**:
1. Collects artifacts (papers, transcripts, code)
2. Groups related artifacts
3. Extracts knowledge from each artifact
4. Synthesizes cross-artifact insights
5. Validates completeness
6. Generates final compilation

**Key Concepts Shown**:
- Multi-artifact processing
- Knowledge graph construction
- Artifact correlation
- Compilation and validation

---

## 💬 Chat Action Examples

Individual examples showing how to use each action type:

### examples.py

**Purpose**: Legacy examples of basic chat actions

**Covers**:
- Action invocation patterns
- Response handling
- Error cases

**Usage**:
```bash
python examples/examples.py
```

### examples_modern.py

**Purpose**: Modern examples using the refactored action system

**Shows**:
- Unified action registry usage
- Pydantic validation
- Async handler execution
- Streaming responses

**Usage**:
```bash
python examples/examples_modern.py
```

### example_usage.py

**Purpose**: Practical usage examples

**Demonstrates**:
- Real-world scenarios
- Common patterns
- Best practices

**Usage**:
```bash
python examples/example_usage.py
```

### refactor_examples.py

**Purpose**: Examples from refactoring process

**Shows**:
- Before/after comparisons
- Code consolidation techniques
- Performance improvements

**Usage**:
```bash
python examples/refactor_examples.py
```

---

## 🔌 Integration Examples

Integration patterns for incorporating chat into other systems:

### m365_examples.py

**Purpose**: Microsoft 365 Copilot integration examples

**Covers**:
- Declarative agent manifest
- Adaptive Card integration
- Teams/Copilot specific patterns
- User context handling

**Key Patterns**:
```python
# 1. Declarative agent registration
@register_action("find_research", "Find research by topic")
class FindResearchHandler(BaseActionHandler):
    async def execute(self, payload, context):
        # Handler implementation
        pass

# 2. Adaptive Card responses
card = {
    "type": "AdaptiveCard",
    "body": [
        {"type": "TextBlock", "text": "Research Results"}
    ]
}

# 3. Context-aware responses
context.user_id  # From Teams/M365
context.conversation_id
context.team_id
```

**Usage**:
```bash
python examples/integration/m365_examples.py
```

---

## 🏃 Quick Run Any Example

### Run All Examples
```bash
for example in examples/*.py; do
  echo "=== Running $example ==="
  python "$example"
done
```

### Run Just Workflows
```bash
python examples/workflows/workflow_example.py
python examples/workflows/poc_workflow.py
```

### Run Integration Examples
```bash
python examples/integration/m365_examples.py
```

---

## 📖 Learning Path

1. **Start with Basic**: Run `example_usage.py` for practical patterns
2. **Learn Actions**: Review `examples_modern.py` for unified action system
3. **Understand Workflows**: Study `workflow_example.py` and `poc_workflow.py`
4. **Integration**: Explore `m365_examples.py` for Teams/Copilot patterns
5. **Deep Dive**: Read code comments and docstrings

---

## 🔑 Key Patterns Shown

### Pattern 1: Using Actions
```python
from api.actions.base import get_registry

registry = get_registry()
text, card = await registry.dispatch(
    action_type="browse_all",
    payload={"limit": 10},
    context=conversation_context
)
```

### Pattern 2: Creating Handlers
```python
from api.actions.decorators import register_action

@register_action("my_action", "Description")
class MyHandler(BaseActionHandler):
    async def execute(self, payload, context):
        result = await self.do_work(payload)
        return "Result text", None
```

### Pattern 3: Error Handling
```python
try:
    text, card = await registry.dispatch(...)
except ActionValidationError as e:
    print(f"Invalid input: {e}")
except ActionExecutionError as e:
    print(f"Execution failed: {e}")
```

### Pattern 4: Streaming Responses
```python
async def streaming_response():
    async for chunk in create_streaming_response(text, card, context):
        yield chunk

return StreamingResponse(streaming_response())
```

---

## 🧪 Testing Examples

### Run Example Tests
```bash
pytest examples/ -v
```

### Test a Specific Example
```bash
pytest examples/workflows/test_workflow.py -v
```

---

## 🔗 Related Resources

- **Main README**: See [../README.md](../README.md) for project overview
- **Action Reference**: See [../QUICK_REFERENCE.md](../QUICK_REFERENCE.md) for all 15 actions
- **Architecture**: See [../UNIFIED_ACTIONS_IMPLEMENTATION.md](../UNIFIED_ACTIONS_IMPLEMENTATION.md) for design patterns
- **API Docs**: Run server and visit http://localhost:8000/docs

---

## 💡 Tips

- **Copy & Modify**: Use these examples as templates for your own code
- **Test First**: Each example is a working, tested piece of code
- **Check Comments**: Code includes detailed comments explaining patterns
- **Compare Versions**: Look at examples.py vs examples_modern.py to see improvements
- **Use IDE Autocomplete**: Copy example code into your IDE for full intellisense

---

## 🚀 Next Steps

1. Pick an example that matches your use case
2. Run it to see it in action
3. Modify it for your scenario
4. Test with your own data
5. Integrate into your application

---

**Questions about examples?** Check the code comments or see main [../README.md](../README.md#-development-guide).
