# Bot Framework Emulator Setup

This guide shows how to test the Knowledge Extraction Agent using the **Bot Framework Emulator**.

## Prerequisites

- Python 3.10+
- Pip installed
- Bot Framework Emulator (latest) — download from Microsoft
- This repository checked out locally

## Install dependencies

```powershell
# From repo root
pip install -r requirements.txt
```

## Start the local bot server

```powershell
# Runs at http://localhost:3978/api/messages
python bots/bot_server.py
```

> For local testing with the emulator, leave `MicrosoftAppId` and `MicrosoftAppPassword` empty. If you later deploy, set these environment variables for authentication.

## Connect with Bot Framework Emulator

1. Open the Emulator
2. Click **Open Bot**
3. Enter the bot URL: `http://localhost:3978/api/messages`
4. Leave Microsoft App ID/Password blank, and click **Connect**

You should see the bot greet you.

## Try these messages

- Help:
  - `help`
- Paper extraction:
  - `extract paper from inputs/papers/bert-paper.pdf`
- Talk extraction:
  - `extract talk from inputs/transcripts/vision-keynote.txt`
- Repository extraction:
  - `extract repository from inputs/repositories\awesome-vision-lib`
- Status/history:
  - `show recent extractions`

Outputs are saved under `outputs/` as JSON artifacts and Markdown summaries.

## Troubleshooting

- "Cannot connect": ensure the server is listening on `http://localhost:3978/api/messages`.
- File not found: use absolute Windows paths if needed, e.g., `C:\Users\you\project\inputs\papers\file.pdf`.
- Missing packages: re-run `pip install -r requirements.txt`.
- Auth errors: for local development, leave App ID/Password empty in the emulator and do not set the env vars.

## Next steps

- Wire up SharePoint/OneDrive tools and secure auth for enterprise testing.
- Add richer intent parsing or buttons/cards for common actions.
- Deploy the bot to Azure Bot Service when ready.
