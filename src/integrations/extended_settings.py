"""
Extended Settings for All Optional Integrations

Unified configuration for:
- Azure AI Foundry
- Power Platform (Automate, Apps, BI)
- Microsoft 365
"""

import os
import logging
from enum import Enum
from typing import Optional, List

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers"""
    AZURE_OPENAI = "azure-openai"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_AI_FOUNDRY = "azure-ai-foundry"


class IntegrationMode(Enum):
    """Integration deployment modes"""
    LOCAL_ONLY = "local"
    M365_ONLY = "m365"
    FOUNDRY_ONLY = "foundry"
    POWER_PLATFORM = "power-platform"
    FULL_ENTERPRISE = "full-enterprise"


class ExtendedSettings:
    """Unified settings for all optional integrations

    Manages configuration for:
    - Azure AI Foundry integration
    - Power Automate connector
    - Power Apps API
    - Power BI analytics
    - Microsoft 365 integration
    """

    def __init__(self):
        """Initialize settings from environment variables"""

        # ===== LLM Configuration =====
        self.llm_provider = os.getenv(
            "LLM_PROVIDER",
            LLMProvider.AZURE_OPENAI.value
        )
        self.llm_model = os.getenv("LLM_MODEL", "gpt-4-turbo")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))

        # ===== Azure AI Foundry Settings =====
        self.foundry_enabled = os.getenv(
            "FOUNDRY_ENABLED",
            "false"
        ).lower() == "true"

        self.foundry_connection_string = os.getenv(
            "FOUNDRY_CONNECTION_STRING"
        )

        self.foundry_model = os.getenv(
            "FOUNDRY_MODEL",
            "gpt-4-turbo"
        )

        self.foundry_enable_tracing = os.getenv(
            "FOUNDRY_TRACING",
            "true"
        ).lower() == "true"

        self.foundry_enable_monitoring = os.getenv(
            "FOUNDRY_MONITORING",
            "true"
        ).lower() == "true"

        self.foundry_enable_evaluation = os.getenv(
            "FOUNDRY_EVALUATION",
            "true"
        ).lower() == "true"

        # ===== Power Platform Settings =====
        self.power_platform_enabled = os.getenv(
            "POWER_PLATFORM_ENABLED",
            "false"
        ).lower() == "true"

        self.power_automate_endpoint = os.getenv(
            "POWER_AUTOMATE_ENDPOINT"
        )

        self.power_apps_enabled = os.getenv(
            "POWER_APPS_ENABLED",
            "true"
        ).lower() == "true"

        self.power_bi_enabled = os.getenv(
            "POWER_BI_ENABLED",
            "true"
        ).lower() == "true"

        # ===== Microsoft 365 Settings =====
        self.m365_enabled = os.getenv(
            "M365_ENABLED",
            "false"
        ).lower() == "true"

        self.m365_tenant_id = os.getenv("M365_TENANT_ID")
        self.m365_client_id = os.getenv("M365_CLIENT_ID")
        self.m365_client_secret = os.getenv("M365_CLIENT_SECRET")

        # ===== Integration Mode =====
        self.integration_mode = os.getenv(
            "INTEGRATION_MODE",
            IntegrationMode.FULL_ENTERPRISE.value
        )

        # ===== Deployment Settings =====
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.api_host = os.getenv("API_HOST", "0.0.0.0")
        self.debug_mode = os.getenv("DEBUG", "false").lower() == "true"

        # ===== Storage Settings =====
        self.output_dir = os.getenv(
            "OUTPUT_DIR",
            "./outputs"
        )

        self.artifacts_dir = os.getenv(
            "ARTIFACTS_DIR",
            "./artifacts"
        )

        # ===== Logging =====
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        logger.info(f"Extended settings initialized: {self.integration_mode}")

    # ===== Validation Methods =====

    def validate_foundry_config(self) -> bool:
        """Validate Foundry configuration

        Returns:
            True if Foundry config is valid or disabled
        """
        if not self.foundry_enabled:
            return True

        if not self.foundry_connection_string:
            logger.error("Foundry enabled but no connection string provided")
            return False

        return True

    def validate_power_platform_config(self) -> bool:
        """Validate Power Platform configuration

        Returns:
            True if Power Platform config is valid or disabled
        """
        if not self.power_platform_enabled:
            return True

        # Power Platform is flexible - can work without endpoint
        logger.info("Power Platform configuration valid")
        return True

    def validate_m365_config(self) -> bool:
        """Validate M365 configuration

        Returns:
            True if M365 config is valid or disabled
        """
        if not self.m365_enabled:
            return True

        if not all([self.m365_tenant_id, self.m365_client_id, self.m365_client_secret]):
            logger.error("M365 enabled but missing required credentials")
            return False

        return True

    def validate_all(self) -> bool:
        """Validate all configurations

        Returns:
            True if all active configs are valid
        """
        validations = [
            ("Foundry", self.validate_foundry_config()),
            ("Power Platform", self.validate_power_platform_config()),
            ("M365", self.validate_m365_config())
        ]

        all_valid = all(result for _, result in validations)

        for name, result in validations:
            status = "✓" if result else "✗"
            logger.info(f"{status} {name} configuration")

        return all_valid

    # ===== Query Methods =====

    def get_active_providers(self) -> List[str]:
        """Get list of active integration providers

        Returns:
            List of enabled provider names
        """
        providers = []

        if self.llm_provider == LLMProvider.AZURE_AI_FOUNDRY.value:
            providers.append("foundry")

        if self.foundry_enabled:
            providers.append("foundry-evaluation")
            providers.append("foundry-monitoring")

        if self.m365_enabled:
            providers.append("m365")
            providers.append("sharepoint")
            providers.append("onedrive")
            providers.append("teams")

        if self.power_platform_enabled:
            providers.append("power-automate")

        if self.power_apps_enabled:
            providers.append("power-apps")

        if self.power_bi_enabled:
            providers.append("power-bi")

        return providers

    def get_integration_tier(self) -> str:
        """Get current integration tier

        Returns:
            Tier name: local, enterprise, advanced, or full
        """
        active = self.get_active_providers()

        if len(active) == 0:
            return "local"
        elif self.m365_enabled:
            if self.foundry_enabled or self.power_platform_enabled:
                return "full-enterprise"
            else:
                return "enterprise"
        elif self.foundry_enabled or self.power_platform_enabled:
            return "advanced"
        else:
            return "local"

    def get_capability_summary(self) -> dict:
        """Get summary of enabled capabilities

        Returns:
            Dictionary of capabilities and their status
        """
        return {
            "extraction": {
                "local": True,
                "sharepoint": self.m365_enabled,
                "onedrive": self.m365_enabled,
                "teams": self.m365_enabled
            },
            "llm": {
                "provider": self.llm_provider,
                "foundry_enabled": self.foundry_enabled,
                "foundry_tracing": self.foundry_enable_tracing
            },
            "workflow": {
                "power_automate": self.power_platform_enabled,
                "power_apps": self.power_apps_enabled
            },
            "analytics": {
                "power_bi": self.power_bi_enabled,
                "foundry_evaluation": self.foundry_enable_evaluation
            }
        }

    # ===== Helper Methods =====

    def to_dict(self) -> dict:
        """Convert settings to dictionary

        Returns:
            Dictionary of all settings
        """
        return {
            "llm": {
                "provider": self.llm_provider,
                "model": self.llm_model,
                "temperature": self.temperature
            },
            "foundry": {
                "enabled": self.foundry_enabled,
                "model": self.foundry_model,
                "tracing": self.foundry_enable_tracing,
                "monitoring": self.foundry_enable_monitoring,
                "evaluation": self.foundry_enable_evaluation
            },
            "power_platform": {
                "enabled": self.power_platform_enabled,
                "power_apps": self.power_apps_enabled,
                "power_bi": self.power_bi_enabled
            },
            "m365": {
                "enabled": self.m365_enabled
            },
            "deployment": {
                "mode": self.integration_mode,
                "tier": self.get_integration_tier(),
                "port": self.api_port,
                "host": self.api_host
            }
        }

    def print_summary(self):
        """Print settings summary to console"""
        print("\n" + "=" * 60)
        print("KNOWLEDGE AGENT - EXTENDED SETTINGS")
        print("=" * 60)

        summary = self.to_dict()

        for section, settings in summary.items():
            print(f"\n{section.upper()}:")
            for key, value in settings.items():
                if isinstance(value, bool):
                    status = "✓ Enabled" if value else "✗ Disabled"
                    print(f"  {key}: {status}")
                else:
                    print(f"  {key}: {value}")

        print(f"\nActive Providers: {', '.join(self.get_active_providers())}")
        print(f"Integration Tier: {self.get_integration_tier()}")
        print("=" * 60 + "\n")


# ===== Global Instance =====

_settings_instance: Optional[ExtendedSettings] = None


def get_settings() -> ExtendedSettings:
    """Get or create global settings instance

    Returns:
        ExtendedSettings instance
    """
    global _settings_instance

    if _settings_instance is None:
        _settings_instance = ExtendedSettings()

    return _settings_instance


def load_settings_from_env(env_file: Optional[str] = None) -> ExtendedSettings:
    """Load settings from .env file and environment

    Args:
        env_file: Path to .env file (optional)

    Returns:
        ExtendedSettings instance
    """
    if env_file:
        from pathlib import Path
        if Path(env_file).exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")

    return get_settings()
