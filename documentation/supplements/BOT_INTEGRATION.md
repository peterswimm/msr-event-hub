# Knowledge Agent - Bot Framework Integration Guide

**Status**: Ready for Bot Framework Emulator Testing
**Date**: December 18, 2025

---

## 🤖 What Was Created

### 1. Agent Definition (`knowledge_agent.json`)
- Agent metadata and capabilities
- Tool definitions for extraction functions
- Model configuration
- Instructions for conversational behavior

### 2. Agent Implementation (`knowledge_agent_bot.py`)
- `KnowledgeExtractionAgent` class - Main agent logic
- Tool function implementations
- Conversational message processing
- Extraction history tracking

---

## 🚀 Quick Start - Test in Bot Emulator

### Option 1: Direct Bot Integration

If you want to integrate with the existing EventKit bot infrastructure:

```bash
# 1. Copy agent files to parent directory
cd d:\code\event-agent-example
cp knowledge-agent-poc/knowledge_agent.json .
cp knowledge-agent-poc/knowledge_agent_bot.py .

# 2. Update bot_server.py or bot_handler.py to use KnowledgeExtractionAgent

# 3. Start the bot server
python bot_server.py
```

### Option 2: Standalone Bot Server

Create a simple bot server for the Knowledge Agent:

```python
# knowledge_bot_server.py
from botbuilder.core import BotFrameworkAdapter, TurnContext
from botbuilder.schema import Activity
from aiohttp import web
import sys

sys.path.insert(0, 'knowledge-agent-poc')
from knowledge_agent_bot import KnowledgeExtractionAgent

# Initialize agent
agent = KnowledgeExtractionAgent()

# Bot adapter
adapter = BotFrameworkAdapter(
    app_id="",  # Empty for local testing
    app_password=""
)

async def on_message(turn_context: TurnContext):
    """Handle incoming messages"""
    user_message = turn_context.activity.text
    response = agent.process_message(user_message)
    await turn_context.send_activity(Activity(text=response))

async def messages(req):
    """Bot endpoint"""
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def call_fun(turn_context: TurnContext):
        await on_message(turn_context)

    await adapter.process_activity(activity, auth_header, call_fun)
    return web.Response(status=200)

# Start server
app = web.Application()
app.router.add_post("/api/messages", messages)
web.run_app(app, host="localhost", port=3978)
```

### Option 3: Test Agent Directly (CLI)

```bash
cd knowledge-agent-poc
python knowledge_agent_bot.py
```

Then interact:
```
You: help
Agent: [shows capabilities]

You: extract paper from papers/sample.pdf
Agent: [extracts and returns results]
```

---

## 🔧 Integration with EventKit

To integrate with your existing EventKit agent infrastructure:

### 1. Add Knowledge Agent to Agent Framework

```python
# In agent.py or similar
from knowledge_agent_poc.knowledge_agent_bot import (
    extract_paper_knowledge,
    extract_talk_knowledge,
    extract_repository_knowledge,
    get_extraction_status
)

# Register tools
KNOWLEDGE_TOOLS = [
    {
        "name": "extract_paper_knowledge",
        "function": extract_paper_knowledge,
        "description": "Extract knowledge from research paper PDF"
    },
    {
        "name": "extract_talk_knowledge",
        "function": extract_talk_knowledge,
        "description": "Extract knowledge from talk transcript"
    },
    {
        "name": "extract_repository_knowledge",
        "function": extract_repository_knowledge,
        "description": "Extract knowledge from repository"
    },
    {
        "name": "get_extraction_status",
        "function": get_extraction_status,
        "description": "Get recent extraction history"
    }
]
```

### 2. Update Agent Declaration

Merge `knowledge_agent.json` into your existing `agent.json` or create a separate agent profile.

### 3. Add to Adapter

If using the unified adapter architecture:

```python
from adapters.foundry_adapter import FoundryAdapter

adapter = FoundryAdapter()
adapter.register_tools(KNOWLEDGE_TOOLS)
```

---

## 💬 Sample Conversations

### Example 1: Extract Paper
```
User: I have a research paper I'd like you to analyze
Agent: Great! I can extract structured knowledge from research papers.
       Please provide the path to the PDF file.

User: papers/attention_is_all_you_need.pdf
Agent: ✅ Successfully extracted paper knowledge

       Title: Attention Is All You Need
       Contributors: Vaswani, Shazeer, Parmar, et al.
       Confidence: 95%

       Overview: Introduces the Transformer architecture...

       Files saved:
       - JSON: outputs/artifact_20251218_103000.json
       - Summary: outputs/artifact_20251218_103000.md
```

### Example 2: Extract Talk
```
User: analyze this talk transcript: transcripts/demo_2024.txt
Agent: ✅ Successfully extracted talk knowledge

       Title: AI Foundation Models Demo
       Speakers: Smith, Johnson
       Confidence: 88%

       Overview: Demonstrates new capabilities in...
```

### Example 3: Extract Repository
```
User: extract repository from https://github.com/microsoft/semantic-kernel
Agent: ✅ Successfully extracted repository knowledge

       Repository: semantic-kernel
       Contributors: Microsoft
       Confidence: 92%

       Overview: SDK for integrating LLMs with applications...
```

### Example 4: Check Status
```
User: show my recent extractions
Agent: Total extractions: 3

       Recent:
       - Paper: Attention Is All You Need (95%)
       - Talk: AI Foundation Models Demo (88%)
       - Repository: semantic-kernel (92%)
```

---

## 🧪 Testing in Bot Framework Emulator

### 1. Install Bot Framework Emulator
Download from: https://github.com/Microsoft/BotFramework-Emulator/releases

### 2. Start Bot Server
```bash
python knowledge_bot_server.py
```

### 3. Connect Emulator
- Open Bot Framework Emulator
- Click "Open Bot"
- Enter: `http://localhost:3978/api/messages`
- Leave App ID and Password empty (local testing)
- Click "Connect"

### 4. Test Conversations
Send messages like:
- "help"
- "what can you do?"
- "extract paper from papers/sample.pdf"
- "show recent extractions"

---

## 📋 Agent Capabilities

The Knowledge Agent provides:

### Tools
- `extract_paper_knowledge` - PDF analysis
- `extract_talk_knowledge` - Transcript analysis
- `extract_repository_knowledge` - Repository analysis
- `get_extraction_status` - History tracking

### Conversational Features
- Natural language understanding
- Helpful guidance and suggestions
- Error handling with recovery suggestions
- Extraction history tracking
- Human-readable summaries

### Outputs
- Structured JSON artifacts
- Markdown summaries
- Confidence assessments
- Provenance tracking

---

## 🔐 Configuration

### Environment Variables
```bash
# .env file
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_MODEL=gpt-4-turbo

# Or
OPENAI_API_KEY=your_key

# Or
ANTHROPIC_API_KEY=your_key
```

### Bot Configuration
```python
# In knowledge_agent_bot.py
agent = KnowledgeExtractionAgent(
    default_llm_provider="azure-openai",  # or "openai" or "anthropic"
    output_dir="./outputs"
)
```

---

## 📁 File Structure

```
knowledge-agent-poc/
├── knowledge_agent.json         # Agent definition (NEW)
├── knowledge_agent_bot.py       # Bot implementation (NEW)
├── agents/                      # Extraction agents
├── core/schemas/                # Data schemas
├── prompts/                     # LLM prompts
└── outputs/                     # Extraction results

# To integrate with EventKit:
d:\code\event-agent-example/
├── knowledge_agent.json         # Copy here
├── knowledge_agent_bot.py       # Copy here
├── bot_server.py               # Update to use Knowledge Agent
└── agent.json                   # Update with new tools
```

---

## 🎯 Next Steps

1. **Test Standalone**: Run `python knowledge_agent_bot.py` for CLI testing
2. **Create Bot Server**: Use the standalone bot server template above
3. **Test in Emulator**: Connect Bot Framework Emulator to test conversations
4. **Integrate with EventKit**: Merge tools into existing agent framework
5. **Deploy**: Deploy as Azure Bot Service or other hosting

---

## 💡 Tips

### For Bot Emulator Testing
- Keep sample files ready (papers, transcripts, repos)
- Test error cases (missing files, invalid paths)
- Try natural language variations
- Check extraction history

### For Production
- Add authentication for bot endpoints
- Implement rate limiting
- Add user context/sessions
- Store extraction history in database
- Add retry logic for LLM calls

---

## 📞 Agent Commands

Natural language commands the agent understands:

- "help" / "what can you do"
- "extract paper from [path]"
- "extract talk from [path]"
- "extract repository from [url]"
- "show recent extractions"
- "status" / "history"

---

**Status**: ✅ Ready for Bot Testing
**Next**: Start bot server and test in Bot Framework Emulator

