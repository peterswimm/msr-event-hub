# Optional Integrations: Azure AI Foundry & Power Platform

**Status**: Architecture & Integration Patterns
**Date**: December 18, 2025

---

## 🎯 Overview

The Knowledge Agent can optionally integrate with:
- **Azure AI Foundry** - Unified AI development platform
- **Power Automate** - Workflow automation
- **Power Apps** - Custom applications
- **Power BI** - Analytics and dashboards

All integrations are **optional** and can be enabled/disabled per deployment.

---

## 1️⃣ Azure AI Foundry Integration

### Why Azure AI Foundry?

- Unified platform for AI/ML development
- Built-in evaluation and monitoring
- Managed endpoints and deployments
- Agentic capabilities
- Tracing and observability
- Team collaboration features

### Integration Architecture

```
┌─────────────────────────────────────┐
│    Knowledge Agent POC              │
│  (Extraction & Orchestration)       │
└────────────┬────────────────────────┘
             │
      ┌──────▼──────────────────────┐
      │  LLM Provider Layer          │
      │  (Pluggable architecture)    │
      ├──────────────────────────────┤
      │ • Azure OpenAI (current)     │
      │ • OpenAI (current)           │
      │ • Anthropic (current)        │
      │ • Azure AI Foundry (NEW)     │
      └──────┬───────────────────────┘
             │
    ┌────────▼─────────┐
    │                  │
┌───▼─────┐  ┌────────▼──────┐
│ Local   │  │ Azure Cloud    │
│ Models  │  │ (Foundry)      │
└─────────┘  └────────────────┘
```

### Option A: Use Foundry Models

```python
# foundry_provider.py
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import os

class AzureAIFoundryProvider:
    """LLM provider using Azure AI Foundry models"""

    def __init__(
        self,
        project_connection_string: str,
        model_name: str = "gpt-4-turbo"
    ):
        self.client = AIProjectClient.from_connection_string(
            conn_str=project_connection_string,
            credential=DefaultAzureCredential()
        )
        self.model_name = model_name

    async def extract(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3
    ) -> str:
        """Use Foundry model for extraction"""
        response = self.client.agents.create_message(
            model=self.model_name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature
        )
        return response.content

    def get_model_info(self) -> dict:
        """Get info about deployed model"""
        return {
            "provider": "azure-ai-foundry",
            "model": self.model_name,
            "project": self.client.project_name
        }


# Usage in Knowledge Agent
from agents.base_agent import BaseKnowledgeAgent

class PaperAgentWithFoundry(BaseKnowledgeAgent):
    """Paper extraction using Azure AI Foundry"""

    def __init__(
        self,
        foundry_connection_string: str = None,
        use_foundry: bool = False
    ):
        self.use_foundry = use_foundry

        if use_foundry and foundry_connection_string:
            self.llm = AzureAIFoundryProvider(
                project_connection_string=foundry_connection_string
            )
        else:
            # Fall back to existing provider
            self.llm = self._get_default_provider()

    def _get_default_provider(self):
        """Get default LLM provider"""
        provider = os.getenv("LLM_PROVIDER", "azure-openai")
        if provider == "azure-openai":
            return AzureOpenAIProvider()
        elif provider == "openai":
            return OpenAIProvider()
        else:
            return AnthropicProvider()
```

### Option B: Integration with Foundry Projects

```python
# foundry_integration.py
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    ToolConnection,
    ConnectionAuthType
)

class FoundryAgentIntegration:
    """Integrate Knowledge Agent with Foundry projects"""

    def __init__(self, project_connection_string: str):
        self.client = AIProjectClient.from_connection_string(
            conn_str=project_connection_string,
            credential=DefaultAzureCredential()
        )

    def register_extraction_tools(self):
        """Register extraction tools in Foundry"""
        tools = [
            {
                "name": "extract_paper_knowledge",
                "description": "Extract knowledge from research papers",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string"},
                        "confidence_threshold": {"type": "number"}
                    },
                    "required": ["pdf_path"]
                }
            },
            {
                "name": "extract_talk_knowledge",
                "description": "Extract knowledge from talks/transcripts",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transcript_path": {"type": "string"}
                    },
                    "required": ["transcript_path"]
                }
            },
            {
                "name": "extract_repository_knowledge",
                "description": "Extract knowledge from repositories",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repo_url": {"type": "string"}
                    },
                    "required": ["repo_url"]
                }
            }
        ]

        # Register in Foundry
        for tool in tools:
            self.client.agents.create_tool(
                name=tool["name"],
                description=tool["description"],
                input_schema=tool["input_schema"]
            )

    def create_foundry_agent(self):
        """Create agentic app in Foundry"""
        agent = self.client.agents.create(
            name="Knowledge Extraction Agent",
            description="Extracts structured knowledge from research artifacts",
            model="gpt-4-turbo",
            tools=[
                "extract_paper_knowledge",
                "extract_talk_knowledge",
                "extract_repository_knowledge"
            ],
            instructions="""You are a knowledge extraction assistant.
Extract structured knowledge from research artifacts including papers, talks, and repositories.
Use the appropriate extraction tool based on the artifact type.
Return structured JSON artifacts with confidence scores."""
        )

        return agent

    def deploy_with_monitoring(self):
        """Deploy agent with Foundry monitoring"""
        deployment = self.client.agents.deploy(
            enable_tracing=True,
            enable_monitoring=True,
            enable_evaluation=True,
            log_artifacts=True
        )

        return deployment
```

### Option C: Use Foundry for Evaluation

```python
# foundry_evaluation.py
from azure.ai.projects import AIProjectClient

class FoundryEvaluation:
    """Use Foundry for agent evaluation"""

    def __init__(self, project_connection_string: str):
        self.client = AIProjectClient.from_connection_string(
            conn_str=project_connection_string,
            credential=DefaultAzureCredential()
        )

    def evaluate_extractions(
        self,
        test_dataset: list,
        metrics: list = None
    ):
        """Evaluate extraction quality using Foundry"""
        if metrics is None:
            metrics = [
                "coherence",           # Does output make sense?
                "groundedness",        # Is it grounded in input?
                "relevance",           # Is it relevant to artifact?
                "accuracy",            # Is extraction accurate?
                "completeness"         # Is extraction complete?
            ]

        results = self.client.evaluations.evaluate(
            agent_id="knowledge-extraction-agent",
            test_data=test_dataset,
            metrics=metrics,
            include_insights=True
        )

        return {
            "scores": results.scores,
            "insights": results.insights,
            "recommendations": results.recommendations
        }

    def get_performance_dashboard(self):
        """Get performance metrics dashboard"""
        return self.client.evaluations.get_dashboard(
            agent_id="knowledge-extraction-agent",
            time_range="last_30_days"
        )
```

---

## 2️⃣ Power Platform Connectors

### Why Power Platform?

- Automate extraction workflows in Power Automate
- Build custom UIs with Power Apps
- Visualize results in Power BI
- Connect to 800+ services out of the box
- No-code/low-code automation

### Power Automate Connector

```python
# power_automate_connector.py
"""
Power Automate Connector for Knowledge Agent

This module enables Power Automate flows to trigger knowledge extractions.
Implements the Power Automate Custom Connector API.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os

app = FastAPI(
    title="Knowledge Agent Connector",
    description="Power Automate connector for knowledge extraction"
)


# ========== Models ==========

class ExtractionRequest(BaseModel):
    """Request model for extraction"""
    artifact_type: str  # 'paper', 'talk', 'repository'
    source_location: str  # local path or URL
    save_results: bool = True
    notify_teams: bool = False


class ExtractionResponse(BaseModel):
    """Response model for extraction"""
    success: bool
    title: str
    confidence: float
    overview: str
    artifact_url: str = None
    error: str = None


# ========== Endpoints ==========

@app.post("/extract", response_model=ExtractionResponse)
async def extract_knowledge(request: ExtractionRequest):
    """
    Extract knowledge from artifact

    Callable from Power Automate flows
    """
    from knowledge_agent_bot import KnowledgeExtractionAgent

    agent = KnowledgeExtractionAgent(enable_m365=True)

    try:
        # Route to appropriate extractor
        if request.artifact_type == "paper":
            result = agent.extract_paper_knowledge(request.source_location)
        elif request.artifact_type == "talk":
            result = agent.extract_talk_knowledge(request.source_location)
        elif request.artifact_type == "repository":
            result = agent.extract_repository_knowledge(request.source_location)
        else:
            raise ValueError(f"Unknown artifact type: {request.artifact_type}")

        if not result["success"]:
            raise ValueError(result["error"])

        return ExtractionResponse(
            success=True,
            title=result["title"],
            confidence=result["confidence"],
            overview=result["overview"],
            artifact_url=result["files"]["json"]
        )

    except Exception as e:
        return ExtractionResponse(
            success=False,
            title="",
            confidence=0,
            overview="",
            error=str(e)
        )


@app.get("/extraction-status")
async def get_status():
    """Get extraction history and status"""
    from knowledge_agent_bot import KnowledgeExtractionAgent

    agent = KnowledgeExtractionAgent()
    return agent.get_extraction_status(limit=10)


@app.post("/extract-from-sharepoint")
async def extract_from_sharepoint(
    site_id: str,
    file_path: str,
    notify_teams: bool = False,
    team_id: str = None,
    channel_id: str = None
):
    """Extract from SharePoint - callable from Power Automate"""
    from knowledge_agent_bot import KnowledgeExtractionAgent

    agent = KnowledgeExtractionAgent(enable_m365=True)

    result = agent.extract_from_sharepoint(
        site_id=site_id,
        file_path=file_path,
        save_to_sharepoint=True,
        notify_teams=notify_teams,
        team_id=team_id,
        channel_id=channel_id
    )

    return result


@app.post("/extract-from-onedrive")
async def extract_from_onedrive(file_path: str):
    """Extract from OneDrive - callable from Power Automate"""
    from knowledge_agent_bot import KnowledgeExtractionAgent

    agent = KnowledgeExtractionAgent(enable_m365=True)
    result = agent.extract_from_onedrive(file_path)
    return result


# ========== Metadata Endpoints ==========

@app.get("/schema")
async def get_schema():
    """Get connector schema for Power Automate discovery"""
    return {
        "schemas": {
            "extraction_request": ExtractionRequest.schema(),
            "extraction_response": ExtractionResponse.schema()
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Knowledge Agent"}


# ========== Startup ==========

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Power Automate Flow Example

```json
{
  "name": "Extract Knowledge and Store",
  "triggers": [
    {
      "type": "When a file is created",
      "location": "SharePoint",
      "library": "Research Papers"
    }
  ],
  "actions": [
    {
      "name": "Extract Knowledge",
      "type": "HTTP",
      "method": "POST",
      "uri": "https://your-agent.azurewebsites.net/extract-from-sharepoint",
      "body": {
        "site_id": "@triggerOutputs()['body/SiteId']",
        "file_path": "@triggerOutputs()['body/Path']",
        "notify_teams": true,
        "team_id": "your-team-id",
        "channel_id": "your-channel-id"
      }
    },
    {
      "name": "Parse Response",
      "type": "Parse JSON",
      "inputs": "@body('Extract Knowledge')"
    },
    {
      "name": "Log Results",
      "type": "Create item in list",
      "listName": "Extraction Results",
      "itemProperties": {
        "Title": "@body('Parse Response')['title']",
        "Confidence": "@body('Parse Response')['confidence']",
        "Overview": "@body('Parse Response')['overview']",
        "ArtifactUrl": "@body('Parse Response')['artifact_url']"
      }
    }
  ]
}
```

---

## 3️⃣ Power Apps Integration

### Canvas App for Knowledge Exploration

```python
# power_apps_api.py
"""API endpoints for Power Apps canvas app"""

@app.get("/artifacts")
async def list_artifacts(limit: int = 100, offset: int = 0):
    """List extraction artifacts for Power Apps"""
    # Get artifacts from storage
    artifacts = get_artifacts(limit=limit, offset=offset)
    return {
        "items": artifacts,
        "total": len(artifacts),
        "hasMore": offset + limit < get_total_artifacts()
    }


@app.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Get artifact details for Power Apps"""
    artifact = get_artifact_by_id(artifact_id)
    return {
        "id": artifact_id,
        "title": artifact["title"],
        "overview": artifact["plain_language_overview"],
        "methods": artifact["key_methods_approach"],
        "impact": artifact["potential_impact"],
        "confidence": artifact["confidence_score"],
        "source": artifact["m365_source"]
    }


@app.get("/search")
async def search_artifacts(query: str, limit: int = 20):
    """Search artifacts - for Power Apps search box"""
    results = search_in_artifacts(query, limit=limit)
    return {"results": results}


@app.post("/artifacts/{artifact_id}/feedback")
async def submit_feedback(artifact_id: str, feedback: dict):
    """Submit feedback on extraction quality"""
    # Store feedback for improvement
    store_feedback(artifact_id, feedback)
    return {"success": True, "message": "Feedback stored"}
```

### Power BI Integration

```python
# power_bi_connector.py
"""Export extraction data to Power BI"""

def export_to_power_bi(artifact_id: str):
    """Export artifact data for Power BI visualization"""
    artifact = get_artifact_by_id(artifact_id)

    return {
        "id": artifact_id,
        "title": artifact["title"],
        "confidence": artifact["confidence_score"],
        "type": artifact["source_type"],
        "extraction_date": artifact["extraction_date"],
        "contributor_count": len(artifact["contributors"]),
        "overview_length": len(artifact["plain_language_overview"]),
        "model_used": artifact["extraction_model"],
        "has_m365_source": bool(artifact.get("m365_source"))
    }


def batch_export_to_power_bi(filter_by: dict = None):
    """Batch export for Power BI dataset"""
    artifacts = get_all_artifacts(filter_by)
    return [export_to_power_bi(a["id"]) for a in artifacts]
```

---

## 4️⃣ Unified Configuration

```python
# extended_settings.py
"""Extended settings for Foundry and Power Platform"""

from enum import Enum
from typing import Optional

class LLMProvider(Enum):
    """Available LLM providers"""
    AZURE_OPENAI = "azure-openai"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_AI_FOUNDRY = "azure-ai-foundry"


class IntegrationMode(Enum):
    """Integration modes"""
    LOCAL_ONLY = "local"
    M365_ONLY = "m365"
    FOUNDRY_ONLY = "foundry"
    POWER_PLATFORM = "power-platform"
    FULL_ENTERPRISE = "full-enterprise"


class ExtendedSettings:
    """Settings for all optional integrations"""

    def __init__(self):
        # LLM Settings
        self.llm_provider = os.getenv(
            "LLM_PROVIDER",
            LLMProvider.AZURE_OPENAI.value
        )

        # Azure AI Foundry Settings
        self.foundry_enabled = os.getenv("FOUNDRY_ENABLED", "false").lower() == "true"
        self.foundry_connection_string = os.getenv("FOUNDRY_CONNECTION_STRING")
        self.foundry_model = os.getenv("FOUNDRY_MODEL", "gpt-4-turbo")
        self.foundry_enable_tracing = os.getenv("FOUNDRY_TRACING", "true").lower() == "true"

        # Power Platform Settings
        self.power_platform_enabled = os.getenv("POWER_PLATFORM_ENABLED", "false").lower() == "true"
        self.power_automate_endpoint = os.getenv("POWER_AUTOMATE_ENDPOINT")

        # M365 Settings (existing)
        self.m365_enabled = os.getenv("M365_ENABLED", "false").lower() == "true"

        # Integration Mode
        self.integration_mode = os.getenv(
            "INTEGRATION_MODE",
            IntegrationMode.FULL_ENTERPRISE.value
        )

    def get_active_providers(self) -> list:
        """Get list of active providers"""
        providers = []
        if self.llm_provider == LLMProvider.AZURE_AI_FOUNDRY.value:
            providers.append("foundry")
        if self.foundry_enabled:
            providers.append("foundry-evaluation")
        if self.m365_enabled:
            providers.append("m365")
        if self.power_platform_enabled:
            providers.append("power-platform")
        return providers

    def validate_foundry_config(self) -> bool:
        """Validate Foundry configuration"""
        if not self.foundry_enabled:
            return True
        return bool(self.foundry_connection_string)

    def validate_power_platform_config(self) -> bool:
        """Validate Power Platform configuration"""
        if not self.power_platform_enabled:
            return True
        return bool(self.power_automate_endpoint)


# Usage
settings = ExtendedSettings()
print(f"Active integrations: {settings.get_active_providers()}")
```

---

## 5️⃣ Deployment Strategies

### Local Development - All Features

```bash
# .env file
LLM_PROVIDER=azure-openai
FOUNDRY_ENABLED=true
FOUNDRY_CONNECTION_STRING=your-connection-string
M365_ENABLED=true
POWER_PLATFORM_ENABLED=false
INTEGRATION_MODE=full-enterprise
```

```bash
# Run with all features
python knowledge_agent_bot.py --m365 --foundry
```

### Production - Azure Container Instances

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# Install Foundry SDK
RUN pip install azure-ai-projects azure-identity

ENV PORT=8000
EXPOSE 8000

CMD ["python", "power_automate_connector.py"]
```

```bash
# Deploy to Azure
az containerapp up \
  --name knowledge-agent \
  --resource-group my-rg \
  --environment my-env \
  --env-vars \
    FOUNDRY_ENABLED=true \
    FOUNDRY_CONNECTION_STRING=$FOUNDRY_CONNECTION_STRING \
    M365_ENABLED=true
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowledge-agent
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: agent
        image: your-registry/knowledge-agent:latest
        env:
        - name: FOUNDRY_ENABLED
          value: "true"
        - name: M365_ENABLED
          value: "true"
        - name: POWER_PLATFORM_ENABLED
          value: "true"
        - name: INTEGRATION_MODE
          value: "full-enterprise"
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## 6️⃣ Optional Integrations Checklist

### Azure AI Foundry
- [ ] Set up Foundry project
- [ ] Configure connection string
- [ ] Register extraction tools
- [ ] Deploy agentic app
- [ ] Enable tracing/monitoring
- [ ] Run evaluation metrics

### Power Platform
- [ ] Create Power Automate connector
- [ ] Deploy API endpoints
- [ ] Create automation flows
- [ ] Build Power Apps canvas app
- [ ] Set up Power BI dataset
- [ ] Test end-to-end

### Configuration
- [ ] Update settings.py
- [ ] Set environment variables
- [ ] Configure Foundry credentials
- [ ] Enable Power Platform endpoints
- [ ] Set integration mode

---

## 7️⃣ Cost Considerations

| Component | Cost Model | Notes |
|-----------|-----------|-------|
| **Azure OpenAI** | Per 1K tokens | Current default |
| **Azure AI Foundry** | Per deployed model | Optional, premium option |
| **Power Automate** | Per flow run | ~$0.50-2 per 1000 runs |
| **Power Apps** | Per app/user | License-based |
| **Power BI** | Per user | License-based |
| **SharePoint/OneDrive** | Included in M365 | Already paying |
| **Teams** | Included in M365 | Already paying |

**Recommendation**: Start with local extraction, add M365 for enterprise, consider Foundry for high-volume production.

---

## ✅ Summary

The Knowledge Agent supports **optional** integrations:

### Tier 1: Local Only (Current)
- ✅ Extract from local files
- ✅ Save locally
- Perfect for development

### Tier 2: + Microsoft 365 (Recommended)
- ✅ Extract from SharePoint/OneDrive
- ✅ Save to M365 storage
- ✅ Post to Teams
- Perfect for teams

### Tier 3: + Azure AI Foundry (Optional)
- ✅ Use Foundry models
- ✅ Enable monitoring/tracing
- ✅ Run evaluations
- Perfect for production at scale

### Tier 4: + Power Platform (Optional)
- ✅ Power Automate flows
- ✅ Power Apps UI
- ✅ Power BI analytics
- Perfect for business users

**All tiers coexist and can be mixed/matched based on your needs!** 🎯
