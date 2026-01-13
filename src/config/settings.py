"""
Centralized configuration management with environment-specific settings.
Replaces scattered .env usage with structured, validated configuration.

Features:
- Environment-based configuration validation
- Key Vault integration for secrets (not stored in environment)
- Pydantic BaseSettings for type safety
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings with Key Vault integration.
    
    Settings are split into two categories:
    1. Non-sensitive config (stored in .env) - public URLs, feature flags, etc.
    2. Secrets (stored in Key Vault) - API keys, passwords, encryption keys
    
    Secrets are retrieved on-demand via Key Vault client. No secrets are
    stored in environment variables or files.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    
    # ========================================
    # AZURE KEY VAULT CONFIGURATION
    # ========================================
    # Key Vault URL where all secrets are stored
    key_vault_url: Optional[str] = Field(
        default=None,
        description="Azure Key Vault URL (e.g., https://kv-xxx.vault.azure.net/)"
    )
    azure_tenant_id: Optional[str] = None
    
    # ========================================
    # NON-SENSITIVE APPLICATION CONFIG
    # ========================================
    
    # Microsoft Foundry (Azure AI Foundry) Project
    foundry_project_endpoint: Optional[str] = Field(
        default=None,
        description="Microsoft Foundry project endpoint (e.g., https://my-project.api.azureml.ms)"
    )
    foundry_model_deployment: str = Field(
        default="gpt-4o",
        description="Model deployment name in Foundry"
    )
    
    # Azure OpenAI Endpoints (NOT secrets - just service endpoints)
    # The actual API key is stored in Key Vault
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-12-01-preview"
    
    # Internal cache for retrieved secrets (populated by property methods)
    _azure_openai_key: Optional[str] = None
    _database_connection_string: Optional[str] = None
    _encryption_master_key: Optional[str] = None
    _redis_password: Optional[str] = None
    
    # Agent Framework Settings
    agent_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    agent_max_tokens: int = Field(default=4096, ge=1, le=128000)
    agent_timeout: int = Field(default=300, ge=1, le=3600)
    
    # Observability
    enable_tracing: bool = True
    otlp_endpoint: str = "http://localhost:4317"
    enable_sensitive_data: bool = True
    
    # POC Workflow Settings
    poc_projects_dir: Path = Path("projects")
    poc_minimum_expert_rating: float = 3.0
    poc_require_human_approval: bool = False
    poc_max_iterations: int = 2
    poc_enable_compilation: bool = False
    
    # Evaluation
    evaluation_output_dir: str = "./outputs/evaluation"
    evaluation_batch_size: int = 10
    
    # File paths
    inputs_dir: Path = Path("./inputs")
    outputs_dir: Path = Path("./outputs")
    
    # Workflow orchestration
    max_concurrent_agents: int = Field(default=5, ge=1, le=20)
    group_chat_max_rounds: int = Field(default=10, ge=1, le=50)
    
    # ========================================
    # SECRET PROPERTIES (Retrieved from Key Vault on-demand)
    # ========================================
    
    @property
    def azure_openai_key(self) -> str:
        """
        Get Azure OpenAI API key from Key Vault.
        
        Retrieved on first access and cached in _azure_openai_key.
        Not cached across property access for highly sensitive keys.
        
        Returns:
            API key string
        
        Raises:
            ValueError: If Key Vault URL not configured or secret not found
        """
        if not self._azure_openai_key and self.key_vault_url:
            from .key_vault import get_key_vault_manager
            kv = get_key_vault_manager(self.key_vault_url)
            self._azure_openai_key = kv.get_secret("azure-openai-api-key")
        return self._azure_openai_key or ""
    
    @property
    def database_connection_string(self) -> str:
        """
        Get PostgreSQL connection string from Key Vault.
        
        Includes password securely retrieved from vault.
        
        Returns:
            PostgreSQL connection string
        
        Raises:
            ValueError: If Key Vault URL not configured or secret not found
        """
        if not self._database_connection_string and self.key_vault_url:
            from .key_vault import get_key_vault_manager
            kv = get_key_vault_manager(self.key_vault_url)
            self._database_connection_string = kv.get_secret("database-connection-string")
        return self._database_connection_string or ""
    
    @property
    def encryption_master_key(self) -> str:
        """
        Get master encryption key from Key Vault.
        
        IMPORTANT: This key is NOT cached to minimize sensitive data
        in memory. Each call retrieves fresh from Key Vault.
        
        Returns:
            Encryption key string
        
        Raises:
            ValueError: If Key Vault URL not configured or secret not found
        """
        if self.key_vault_url:
            from .key_vault import get_key_vault_manager
            kv = get_key_vault_manager(self.key_vault_url)
            # Do not cache encryption keys - retrieve fresh each time
            return kv.get_secret("encryption-master-key", use_cache=False)
        return ""
    
    @property
    def redis_password(self) -> str:
        """
        Get Redis password from Key Vault.
        
        Returns:
            Redis authentication password
        
        Raises:
            ValueError: If Key Vault URL not configured or secret not found
        """
        if not self._redis_password and self.key_vault_url:
            from .key_vault import get_key_vault_manager
            kv = get_key_vault_manager(self.key_vault_url)
            self._redis_password = kv.get_secret("redis-password")
        return self._redis_password or ""
    
    # ========================================
    # VALIDATORS
    # ========================================
    
    @field_validator("foundry_project_endpoint", "azure_openai_endpoint")
    @classmethod
    def validate_endpoint(cls, v: Optional[str]) -> Optional[str]:
        """Validate endpoint URLs start with http:// or https://."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Endpoint must start with http:// or https://")
        return v
    
    @field_validator("inputs_dir", "outputs_dir")
    @classmethod
    def validate_paths(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_evaluation_dir(self, run_name: Optional[str] = None) -> Path:
        """Get evaluation output directory, optionally with run name."""
        eval_dir = Path(self.evaluation_output_dir)
        if run_name:
            eval_dir = eval_dir / run_name
        eval_dir.mkdir(parents=True, exist_ok=True)
        return eval_dir
    
    def clear_secret_cache(self) -> None:
        """
        Clear cached secrets (useful for testing or forced rotation).
        
        Warning: This only clears cached values in this instance.
        To rotate secrets, also update Key Vault directly.
        """
        self._azure_openai_key = None
        self._database_connection_string = None
        self._redis_password = None
        
        if self.key_vault_url:
            from .key_vault import get_key_vault_manager
            kv = get_key_vault_manager(self.key_vault_url)
            kv.clear_cache()
        
        logger.info("Secret cache cleared")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
