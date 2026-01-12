"""
Bot Framework Emulator server for Knowledge Extraction Agent

Runs a local Bot Framework-compatible endpoint at:
    http://localhost:3978/api/messages

Connect using Bot Framework Emulator:
- Open Bot → Bot URL: http://localhost:3978/api/messages
- Leave Microsoft App ID and Password blank for local testing

This bot routes user messages to `KnowledgeExtractionAgent.process_message()`
for guidance, and supports explicit commands for extraction.
"""

import os
import asyncio
from aiohttp import web
from typing import Optional

from botbuilder.core import (
    BotFrameworkAdapterSettings,
    BotFrameworkAdapter,
    TurnContext,
    ActivityHandler,
)
from botbuilder.schema import Activity, ActivityTypes

# Use the conversational agent implemented in the repo
from knowledge_agent_bot import (
    KnowledgeExtractionAgent,
    extract_paper_knowledge,
    extract_talk_knowledge,
    extract_repository_knowledge,
)


class KnowledgeBot(ActivityHandler):
    """Minimal Bot Framework ActivityHandler that delegates to our agent."""

    def __init__(self, default_provider: str = "azure-openai") -> None:
        self.agent = KnowledgeExtractionAgent(default_llm_provider=default_provider)

    async def on_message_activity(self, turn_context: TurnContext):
        text = (turn_context.activity.text or "").strip()
        lower = text.lower()

        # Direct extraction commands
        # Patterns:
        #   "extract paper from <path>"
        #   "extract talk from <path>"
        #   "extract repository from <url_or_path>"
        if lower.startswith("extract paper from "):
            path = text[len("extract paper from "):].strip()
            response = extract_paper_knowledge(path)
            await turn_context.send_activity(response)
            return

        if lower.startswith("extract talk from "):
            path = text[len("extract talk from "):].strip()
            response = extract_talk_knowledge(path)
            await turn_context.send_activity(response)
            return

        if lower.startswith("extract repository from "):
            repo = text[len("extract repository from "):].strip()
            response = extract_repository_knowledge(repo)
            await turn_context.send_activity(response)
            return

        # Fallback to conversational helper
        reply = self.agent.process_message(text)
        await turn_context.send_activity(reply)


# Adapter and web server setup
APP_ID = os.environ.get("MicrosoftAppId", "")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)
BOT = KnowledgeBot()


async def messages(req: web.Request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def aux_func(turn_context: TurnContext):
        await BOT.on_turn(turn_context)

    await ADAPTER.process_activity(activity, auth_header, aux_func)
    return web.Response(status=201)


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_post("/api/messages", messages)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="localhost", port=3978)
