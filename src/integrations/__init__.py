"""Integration package for Knowledge Agent

Includes:
- Microsoft 365 integration (SharePoint, OneDrive, Teams)
- Azure AI Foundry integration (LLM, monitoring, evaluation)
- Power Platform connectors (Power Automate, Power Apps, Power BI)
"""

# Microsoft 365 (optional - requires graph_auth module)
try:
    from .m365_connector import M365KnowledgeConnector, M365ConnectorError, create_connector
    from .m365_schemas import M365SourceMetadata, M365ArtifactExtension
except ImportError as e:
    import warnings
    warnings.warn(f"M365 integration unavailable: {e}")

# Azure AI Foundry
try:
    from .foundry_provider import AzureAIFoundryProvider, FoundryModelRegistry, create_foundry_provider
    from .foundry_integration import FoundryAgentIntegration, FoundryEvaluation
except ImportError as e:
    import warnings
    warnings.warn(f"Foundry integration unavailable: {e}")

# Power Platform (optional - requires FastAPI)
try:
    from .power_platform_connector import (
        create_power_platform_connector,
        ExtractionRequest,
        ExtractionResponse,
        ArtifactItem,
        ArtifactSearchResult,
        FeedbackRequest
    )
except ImportError as e:
    import warnings
    warnings.warn(f"Power Platform integration unavailable: {e}")

# Extended Settings
from .extended_settings import (
    ExtendedSettings,
    LLMProvider,
    IntegrationMode,
    get_settings,
    load_settings_from_env
)

__all__ = [
    # M365
    'M365KnowledgeConnector',
    'M365ConnectorError',
    'create_connector',
    'M365SourceMetadata',
    'M365ArtifactExtension',
    # Foundry
    'AzureAIFoundryProvider',
    'FoundryModelRegistry',
    'create_foundry_provider',
    'FoundryAgentIntegration',
    'FoundryEvaluation',
    # Power Platform
    'create_power_platform_connector',
    'ExtractionRequest',
    'ExtractionResponse',
    'ArtifactItem',
    'ArtifactSearchResult',
    'FeedbackRequest',
    # Settings
    'ExtendedSettings',
    'LLMProvider',
    'IntegrationMode',
    'get_settings',
    'load_settings_from_env',
]
