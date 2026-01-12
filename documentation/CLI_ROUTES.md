# CLI Routes

## Interactive chatbot (default)

- Command: `python knowledge_agent_bot.py [--m365]`
- Use when you want a conversational loop for local files or M365-enabled interactions.

## SharePoint pipeline (Tier 2, one-shot)

- Command:

```bash
python knowledge_agent_bot.py --sharepoint-pipeline --site-id <SITE_ID> --file-path "/Shared Documents/file.pdf" --folder-path "/Knowledge Artifacts" [--drive-name <DRIVE>] [--team-id <TEAM>] [--channel-id <CHANNEL>] [--llm-provider azure-openai]
```

- What it does: fetches from SharePoint → runs extraction via KnowledgeExtractionAgent → saves JSON back to SharePoint → optionally posts to Teams.

## OneDrive pipeline (Tier 2, one-shot)

- Command:

```bash
python knowledge_agent_bot.py --onedrive-pipeline --file-path "/Documents/file.pdf" --od-folder-path "/Documents/Knowledge Artifacts" [--team-id <TEAM>] [--channel-id <CHANNEL>] [--llm-provider azure-openai]
```

- What it does: fetches from OneDrive → runs extraction via KnowledgeExtractionAgent → saves JSON back to OneDrive → optionally posts to Teams.

## Examples and quickstarts

- Local examples: `python examples.py`
- M365 examples: `python m365_examples.py`
- Tier 3/4 examples: `python tier3_tier4_examples.py`

## Power Platform API

- Start REST API: `python -m integrations.power_platform_connector`
- Health check: `curl http://localhost:8000/health`

## Foundry/advanced evaluation

- See [tier3_tier4_examples.py](tier3_tier4_examples.py) for Foundry model usage and evaluation stubs.

Notes

- SharePoint pipeline relies on `integrations/m365_adapters.py` and the core `ExtractionPipeline` to reduce bespoke glue code.
- Interactive mode still uses the legacy orchestration; migrate commands incrementally to the pipeline as adapters solidify.
