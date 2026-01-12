"""
Adapter to use Azure AI Foundry provider with the core `LLMProvider` Protocol.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
import sys
import os

# Ensure knowledge-agent-poc is on sys.path for direct imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from foundry_provider import AzureAIFoundryProvider
from core_interfaces import LLMProvider


class FoundryProviderAdapter(LLMProvider):
    """Wraps `AzureAIFoundryProvider` to expose a simple `generate()` API.

    `generate(prompt, context)` maps to `extract(system_prompt, user_prompt)`.
    Context keys: `system_prompt` (str), `temperature` (float).
    """

    def __init__(self, provider: AzureAIFoundryProvider) -> None:
        self.provider = provider

    def generate(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        sys_prompt = (context or {}).get("system_prompt", "")
        temperature = float((context or {}).get("temperature", 0.3))

        async def _run() -> str:
            return await self.provider.extract(system_prompt=sys_prompt, user_prompt=prompt, temperature=temperature)

        # Run synchronously for pipeline simplicity
        try:
            return asyncio.run(_run())
        except RuntimeError:
            # If already in an event loop, create a new task and run until complete
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(_run())
