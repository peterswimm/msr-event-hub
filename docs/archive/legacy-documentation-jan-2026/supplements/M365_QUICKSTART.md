# Microsoft 365 Integration - Quick Start Guide

**Status**: ✅ Ready to Use
**Date**: December 18, 2025

---

## 🎯 Overview

The Knowledge Agent now integrates with Microsoft 365 to:
- Extract knowledge from SharePoint documents
- Process OneDrive files
- Save artifacts to SharePoint libraries
- Send notifications to Teams channels
- Track provenance and metadata

---

## 🚀 Quick Start

### Step 1: Configure Microsoft Graph Authentication

The Knowledge Agent uses the existing EventKit Graph authentication:

```bash
# Set environment variables (already configured in EventKit)
export GRAPH_TENANT_ID="your-tenant-id"
export GRAPH_CLIENT_ID="your-client-id"
export GRAPH_CLIENT_SECRET="your-client-secret"
```

Or update `.env` file in the root directory.

### Step 2: Test M365 Connection

```python
# Test authentication
from integrations.m365_connector import create_connector

connector = create_connector()
print("✅ Microsoft 365 connection successful!")
```

### Step 3: Extract from SharePoint

```python
from knowledge_agent_bot import KnowledgeExtractionAgent

# Initialize with M365 enabled
agent = KnowledgeExtractionAgent(enable_m365=True)

# Extract from SharePoint document
result = agent.extract_from_sharepoint(
    site_id="contoso.sharepoint.com,abc-123,def-456",
    file_path="/Shared Documents/Research/paper.pdf",
    save_to_sharepoint=True
)

print(f"✅ Extracted: {result['title']}")
print(f"📁 Saved to: {result['sharepoint_urls']['json_url']}")
```

---

## 📋 Required Permissions

Your Azure AD app needs these Microsoft Graph API permissions:

| Permission | Type | Purpose |
|------------|------|---------|
| `Files.Read.All` | Application | Read SharePoint/OneDrive files |
| `Files.ReadWrite.All` | Application | Write artifacts back |
| `Sites.Read.All` | Application | Access SharePoint sites |
| `ChannelMessage.Send` | Application | Post to Teams channels |

Grant permissions in Azure Portal → App Registrations → Your App → API Permissions.

---

## 💡 Usage Examples

### Extract from SharePoint

```python
agent = KnowledgeExtractionAgent(enable_m365=True)

result = agent.extract_from_sharepoint(
    site_id="your-site-id",
    file_path="/Shared Documents/paper.pdf"
)
```

**Get Site ID**:
```python
connector = create_connector()
site = connector.get_site_by_path("contoso.sharepoint.com:/sites/Research")
site_id = site['id']
```

### Extract from OneDrive

```python
result = agent.extract_from_onedrive(
    file_path="/Documents/Research/paper.pdf",
    save_to_onedrive=True
)
```

### Send Teams Notification

```python
result = agent.extract_from_sharepoint(
    site_id="your-site-id",
    file_path="/Shared Documents/paper.pdf",
    notify_teams=True,
    team_id="19:team_abc@thread.tacv2",
    channel_id="19:channel_xyz@thread.tacv2"
)
```

**Get Team/Channel IDs**: Use Microsoft Graph Explorer or Teams admin center.

### Batch Process Library

```python
site_id = "your-site-id"
files = [
    "/Shared Documents/paper1.pdf",
    "/Shared Documents/paper2.pdf",
    "/Shared Documents/paper3.pdf"
]

for file_path in files:
    result = agent.extract_from_sharepoint(site_id, file_path)
    if result["success"]:
        print(f"✅ {result['title']}")
```

---

## 🔧 Configuration

### Initialize Agent with M365

```python
# Basic initialization
agent = KnowledgeExtractionAgent(enable_m365=True)

# With custom settings
from settings import Settings
from integrations.m365_connector import M365KnowledgeConnector

settings = Settings()
connector = M365KnowledgeConnector(settings=settings)

agent = KnowledgeExtractionAgent(
    enable_m365=True,
    m365_connector=connector
)
```

### Artifact Storage Locations

By default, artifacts are saved to:
- **SharePoint**: `/Knowledge Artifacts` library
- **OneDrive**: `/Documents/Knowledge Artifacts` folder

Customize in your code:

```python
connector.upload_file(
    site_id,
    "/Custom/Path",  # Your custom folder
    "artifact.json",
    content
)
```

---

## 📊 Artifact Metadata

Extractions from M365 include provenance metadata:

```json
{
  "success": true,
  "title": "Attention Is All You Need",
  "m365_source": {
    "site_id": "contoso.sharepoint.com,abc-123",
    "file_path": "/Shared Documents/paper.pdf",
    "web_url": "https://contoso.sharepoint.com/...",
    "last_modified": "2025-12-18T10:30:00Z",
    "file_size": 1024000
  },
  "sharepoint_urls": {
    "json_url": "https://contoso.sharepoint.com/.../artifact.json",
    "markdown_url": "https://contoso.sharepoint.com/.../summary.md"
  }
}
```

---

## 🎬 Complete Workflow Example

```python
from knowledge_agent_bot import KnowledgeExtractionAgent

# Initialize
agent = KnowledgeExtractionAgent(enable_m365=True)

# Configure
config = {
    "site_id": "contoso.sharepoint.com,abc-123,def-456",
    "team_id": "19:team_abc@thread.tacv2",
    "channel_id": "19:channel_xyz@thread.tacv2"
}

# Extract from SharePoint
result = agent.extract_from_sharepoint(
    site_id=config["site_id"],
    file_path="/Shared Documents/Research/new_paper.pdf",
    save_to_sharepoint=True,  # Save artifacts to SharePoint
    notify_teams=True,          # Post to Teams
    team_id=config["team_id"],
    channel_id=config["channel_id"]
)

if result["success"]:
    print(f"✅ Extracted: {result['title']}")
    print(f"📊 Confidence: {result['confidence']:.0%}")
    print(f"💾 Artifacts: {result['sharepoint_urls']['json_url']}")
    print(f"✉️ Teams: Notified")
else:
    print(f"❌ Failed: {result['error']}")
```

---

## 🔍 Troubleshooting

### Authentication Errors

```
M365ConnectorError: Authentication failed
```

**Solution**: Check your Graph credentials in settings:
```python
from settings import Settings
settings = Settings()
print(settings.validate_graph_ready())
```

### Permission Errors

```
M365ConnectorError: Access denied: Insufficient permissions
```

**Solution**: Grant required permissions in Azure Portal and admin consent.

### File Not Found

```
M365ConnectorError: Resource not found
```

**Solution**: Verify site ID and file path:
```python
connector = create_connector()

# List all sites
sites = connector._make_request("GET", "sites?search=*")

# List files in a drive
files = connector._make_request("GET", f"sites/{site_id}/drive/root/children")
```

---

## 📁 File Structure

```
knowledge-agent-poc/
├── integrations/
│   ├── __init__.py
│   ├── m365_connector.py       # M365 integration
│   └── m365_schemas.py          # M365 metadata schemas
├── knowledge_agent_bot.py       # Agent with M365 support
├── knowledge_agent.json         # Agent definition (updated)
├── m365_examples.py             # Usage examples
└── M365_QUICKSTART.md          # This file

# Parent EventKit infrastructure:
../graph_auth.py                 # Authentication (reused)
../graph_service.py              # Graph API (reused)
../settings.py                   # Configuration
```

---

## 🧪 Testing

### Test Authentication

```python
from integrations.m365_connector import create_connector

connector = create_connector()
print("✅ Connected")
```

### Test SharePoint Access

```python
site = connector.get_site_by_path("contoso.sharepoint.com:/sites/Research")
print(f"Site: {site['displayName']}")
```

### Test File Download

```python
content = connector.download_file(site_id, "/Shared Documents/test.pdf")
print(f"Downloaded {len(content)} bytes")
```

### Run Examples

```bash
cd knowledge-agent-poc
python m365_examples.py
```

---

## 🚢 Deployment

### Local Development

```bash
# Enable M365 integration
python knowledge_agent_bot.py --m365
```

### Bot Framework Integration

```python
from knowledge_agent_bot import KnowledgeExtractionAgent

# In bot handler
class KnowledgeBotHandler(ActivityHandler):
    def __init__(self):
        self.agent = KnowledgeExtractionAgent(enable_m365=True)

    async def on_message_activity(self, turn_context: TurnContext):
        message = turn_context.activity.text
        response = self.agent.process_message(message)
        await turn_context.send_activity(Activity(text=response))
```

### Azure Bot Service

1. Deploy EventKit with M365-enabled Knowledge Agent
2. Configure Graph credentials in Azure App Settings
3. Test in Bot Framework Emulator
4. Deploy to Teams

---

## 📚 Additional Resources

- [M365 Integration Examples](m365_examples.py) - 8 detailed examples
- [M365 Expansion Roadmap](M365_EXPANSION.md) - Future features
- [Bot Integration Guide](BOT_INTEGRATION.md) - Bot Framework setup
- [EventKit Documentation](../docs/) - Parent project docs

---

## ✅ Next Steps

1. ✅ Configure Graph authentication
2. ✅ Test M365 connection
3. ✅ Extract from SharePoint document
4. ✅ Save artifacts to SharePoint
5. ✅ Send Teams notification
6. Run batch processing
7. Build custom workflows
8. Deploy to production

---

**Status**: 🎯 Ready for Production Use
**Microsoft 365 Integration**: ✅ Complete

For questions or issues, see the troubleshooting section above or check the examples in `m365_examples.py`.
