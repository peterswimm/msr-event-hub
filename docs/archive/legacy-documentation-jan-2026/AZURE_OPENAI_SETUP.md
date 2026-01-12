# Azure OpenAI Setup Guide

This guide walks you through setting up Azure OpenAI for the MSR Event Hub, using **managed identity** as the default authentication method for production deployments.

---

## Overview

The Event Hub uses Azure OpenAI for:
- **Chat/knowledge agent** – streaming chat completions for attendees exploring research content
- **AI-assisted content extraction** – generating project summaries, FAQs, and knowledge artifacts

We recommend **managed identity** for all production scenarios to avoid storing secrets in configuration or code.

---

## Prerequisites

- Azure subscription with access to Azure OpenAI Service
- Azure CLI installed and authenticated (`az login`)
- Python 3.10+ (for backend)
- Node.js 18+ (for frontend)
- Appropriate permissions to:
  - Create Azure OpenAI resources
  - Assign role-based access control (RBAC) roles

---

## Step 1: Create Azure OpenAI Resource

### Using Azure Portal

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** → Search for **Azure OpenAI**
3. Fill in the required fields:
   - **Subscription**: Your Azure subscription
   - **Resource group**: Create new or select existing
   - **Region**: Choose a region with GPT-4 availability (e.g., East US, West Europe)
   - **Name**: e.g., `msr-event-hub-openai`
   - **Pricing tier**: Standard S0
4. Click **Review + Create** → **Create**

### Using Azure CLI

```bash
# Set variables
RESOURCE_GROUP="msr-event-hub-rg"
LOCATION="eastus"
AOAI_NAME="msr-event-hub-openai"

# Create resource group (if needed)
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name $AOAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --kind OpenAI \
  --sku S0 \
  --location $LOCATION
```

---

## Step 2: Deploy Models

Deploy the models you need for the Event Hub. We recommend:
- **GPT-4** or **GPT-4 Turbo** for chat and content extraction
- **GPT-3.5 Turbo** for lighter workloads (optional)

### Using Azure Portal

1. Go to your Azure OpenAI resource
2. Navigate to **Model deployments** → **Manage Deployments**
3. Click **Create new deployment**
4. Select:
   - **Model**: `gpt-4` or `gpt-4-turbo`
   - **Deployment name**: e.g., `gpt-4` (use this in your config)
   - **Deployment type**: Standard
5. Click **Create**

### Using Azure CLI

```bash
# Deploy GPT-4
az cognitiveservices account deployment create \
  --name $AOAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4 \
  --model-name gpt-4 \
  --model-version "0613" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard
```

---

## Step 3: Get Endpoint and Deployment Name

### Using Azure Portal

1. Go to your Azure OpenAI resource
2. Click **Keys and Endpoint** in the left menu
3. Copy the **Endpoint** (e.g., `https://msr-event-hub-openai.openai.azure.com/`)
4. Go to **Model deployments** and note your **Deployment name** (e.g., `gpt-4`)

### Using Azure CLI

```bash
# Get endpoint
az cognitiveservices account show \
  --name $AOAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.endpoint" -o tsv

# List deployments
az cognitiveservices account deployment list \
  --name $AOAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "[].name" -o tsv
```

---

## Step 4: Configure Managed Identity (Production)

For production deployments, use **managed identity** to authenticate without storing keys.

### 4.1: Enable System-Assigned Managed Identity

If deploying to Azure App Service, Container Apps, or AKS:

```bash
# For App Service
az webapp identity assign \
  --name your-app-name \
  --resource-group $RESOURCE_GROUP

# For Container Apps
az containerapp identity assign \
  --name your-app-name \
  --resource-group $RESOURCE_GROUP

# Get the principal ID (needed for next step)
PRINCIPAL_ID=$(az webapp identity show \
  --name your-app-name \
  --resource-group $RESOURCE_GROUP \
  --query principalId -o tsv)
```

### 4.2: Assign Cognitive Services User Role

Grant the managed identity access to the Azure OpenAI resource:

```bash
# Get the Azure OpenAI resource ID
AOAI_ID=$(az cognitiveservices account show \
  --name $AOAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --query id -o tsv)

# Assign the role
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Cognitive Services User" \
  --scope $AOAI_ID
```

### 4.3: Local Development with Azure CLI Credentials

For local development, authenticate with Azure CLI:

```bash
az login
```

The `DefaultAzureCredential` in the code will automatically use your Azure CLI credentials locally and managed identity in production.

---

## Step 5: Configure Backend (Python API)

### 5.1: Update Environment Variables

Copy `.env.example` to `.env` in the hub root:

```bash
cd d:\code\msr-event-hub
cp .env.example .env
```

Edit `.env`:

```dotenv
# LLM Configuration
LLM_PROVIDER=azure-openai

# Azure OpenAI (managed identity by default; leave AZURE_OPENAI_KEY empty in production)
AZURE_OPENAI_ENDPOINT=https://msr-event-hub-openai.openai.azure.com/
AZURE_OPENAI_KEY=
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_VERSION=2024-02-15-preview

# Azure Identity (for managed authentication)
AZURE_TENANT_ID=your-tenant-id
AZURE_SUBSCRIPTION_ID=your-subscription-id
```

**Notes:**
- Leave `AZURE_OPENAI_KEY` **empty** for managed identity authentication
- Only set `AZURE_OPENAI_KEY` for local development if you need to use key-based auth
- `AZURE_OPENAI_VERSION` should match a supported API version (use `2024-02-15-preview` or later for streaming)

### 5.2: Install Dependencies

```bash
pip install -e .
```

### 5.3: Test the Backend API

Start the FastAPI server:

```bash
uvicorn main:app --reload --port 8000
```

Test the chat endpoint:

```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, what can you tell me about MSR events?"}
    ]
  }'
```

You should see streaming SSE events with chat completions.

Check configuration:

```bash
curl http://localhost:8000/api/chat/config
```

---

## Step 6: Configure Frontend (React Chat Client)

### 6.1: Update Environment Variables

Navigate to the web chat directory:

```bash
cd web/chat
```

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
# Preferred: call the hub backend (uses managed identity to reach Azure OpenAI).
VITE_CHAT_API_BASE=/api

# Optional direct Azure OpenAI config for local-only scenarios.
# Do NOT ship secrets to production builds.
VITE_AOAI_ENDPOINT=
VITE_AOAI_DEPLOYMENT=
VITE_AOAI_API_VERSION=
VITE_AOAI_KEY=
```

**For production:** Only set `VITE_CHAT_API_BASE` to point to your hub backend (default: `/api`) or to the bridge/Showcase gateway.

**For local direct testing (not recommended):** You can temporarily set the `VITE_AOAI_*` variables to test the client without the backend, but do not deploy this configuration.

### 6.2: Install Dependencies

```bash
npm install
```

### 6.3: Run Development Server

```bash
npm run dev
```

Open http://localhost:5173 in your browser. The chat UI should connect to your hub backend at `/api/chat/stream`.

### 6.4: Build for Production

```bash
npm run build
```

The production-ready static files will be in `dist/`.

---

## Step 7: Verify the Complete Setup

### 7.1: Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "storage_root": "./data",
  "repositories": {
    "events": "ready",
    "sessions": "ready",
    "projects": "ready",
    "artifacts": "ready",
    "published_knowledge": "ready"
  }
}
```

### 7.2: Chat Configuration Check

```bash
curl http://localhost:8000/api/chat/config
```

Expected response:

```json
{
  "provider": "azure-openai",
  "auth": "managed-identity",
  "endpoint": true,
  "deployment": true,
  "apiVersion": "2024-02-15-preview"
}
```

### 7.3: End-to-End Chat Test

1. Start the backend: `uvicorn main:app --reload --port 8000`
2. Start the frontend: `cd web/chat && npm run dev`
3. Open http://localhost:5173
4. Send a test message in the chat interface
5. Verify streaming tokens appear in the UI

---

## Troubleshooting

### Error: "Missing configuration: AZURE_OPENAI_ENDPOINT"

**Solution:** Ensure `AZURE_OPENAI_ENDPOINT` is set in your `.env` file (backend root).

### Error: "Azure OpenAI request failed: 401 Unauthorized"

**Causes:**
1. Managed identity not properly configured
2. Missing role assignment (Cognitive Services User)
3. Using key-based auth with invalid/expired key

**Solutions:**
1. Verify managed identity is enabled: `az webapp identity show --name your-app-name --resource-group $RESOURCE_GROUP`
2. Verify role assignment: `az role assignment list --assignee $PRINCIPAL_ID --scope $AOAI_ID`
3. For local dev, ensure `az login` is current: `az account show`

### Error: "Azure OpenAI request failed: 404 Not Found"

**Cause:** Incorrect deployment name or endpoint.

**Solution:** Verify deployment exists:

```bash
az cognitiveservices account deployment list \
  --name $AOAI_NAME \
  --resource-group $RESOURCE_GROUP
```

Ensure `AZURE_OPENAI_DEPLOYMENT` matches the deployment name exactly.

### Error: "Azure OpenAI request failed: 429 Too Many Requests"

**Cause:** Rate limit exceeded.

**Solutions:**
1. Increase deployment capacity (Tokens Per Minute) in Azure Portal
2. Implement retry logic with exponential backoff
3. Consider deploying multiple models and load-balancing

### Frontend: "Configure Azure OpenAI" Warning

**Cause:** Frontend cannot reach the backend, or `VITE_CHAT_API_BASE` is misconfigured.

**Solutions:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `VITE_CHAT_API_BASE` in `web/chat/.env` (should be `/api` for local, or full URL for remote)
3. Verify CORS settings if backend and frontend are on different origins

---

## Production Deployment

### Environment Variables (Backend)

Set these in your Azure App Service / Container Apps configuration:

```bash
az webapp config appsettings set \
  --name your-app-name \
  --resource-group $RESOURCE_GROUP \
  --settings \
    LLM_PROVIDER=azure-openai \
    AZURE_OPENAI_ENDPOINT=https://msr-event-hub-openai.openai.azure.com/ \
    AZURE_OPENAI_DEPLOYMENT=gpt-4 \
    AZURE_OPENAI_VERSION=2024-02-15-preview \
    AZURE_TENANT_ID=your-tenant-id \
    AZURE_SUBSCRIPTION_ID=your-subscription-id
```

**Do not set `AZURE_OPENAI_KEY` in production.**

### Environment Variables (Frontend)

Build the frontend with production config:

```bash
# In web/chat/.env.production
VITE_CHAT_API_BASE=/api
```

Build:

```bash
npm run build
```

Serve the `dist/` folder via your web server, CDN, or the backend itself.

---

## Best Practices

1. **Use managed identity** for all production workloads – never commit keys to source control.
2. **Monitor usage** via Azure Portal → Azure OpenAI → Metrics to track token consumption and set alerts.
3. **Set appropriate rate limits** on deployments to avoid unexpected costs.
4. **Enable logging** and integrate with Application Insights for debugging streaming issues.
5. **Test thoroughly** in a dev/staging environment before deploying to production.
6. **Use separate Azure OpenAI resources** for dev/staging/prod environments.

---

## Additional Resources

- [Azure OpenAI Service Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Managed Identity Documentation](https://learn.microsoft.com/azure/active-directory/managed-identities-azure-resources/overview)
- [FastAPI Streaming Responses](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)

---

## Support

For questions or issues:
- Check the [troubleshooting section](#troubleshooting) above
- Review backend logs: `uvicorn main:app --reload --log-level debug`
- Check browser console for frontend errors
- Open an issue in the repository with detailed error messages and steps to reproduce
