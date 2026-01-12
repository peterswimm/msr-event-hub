"""
Centralized configuration management with environment-specific settings.
Replaces scattered .env usage with structured, validated configuration.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation and environment overrides."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    
    # Microsoft Foundry (Azure AI Foundry) Project
    foundry_project_endpoint: Optional[str] = Field(
        default=None,
        description="Microsoft Foundry project endpoint (e.g., https://my-project.api.azureml.ms)"
    )
    foundry_model_deployment: str = Field(
        default="gpt-4o",
        description="Model deployment name in Foundry"
    )
    
    # Legacy Azure OpenAI (direct endpoint - optional)
    azure_openai_endpoint: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_api_version: str = "2024-12-01-preview"
    
    # Agent Framework Settings
    agent_temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    agent_max_tokens: int = Field(default=4096, ge=1, le=128000)
    agent_timeout: int = Field(default=300, ge=1, le=3600)
    
    # Observability
    enable_tracing: bool = True
    
    # POC Workflow Settings
    poc_projects_dir: Path = Path("projects")
    poc_minimum_expert_rating: float = 3.0
    poc_require_human_approval: bool = False
    poc_max_iterations: int = 2
    poc_enable_compilation: bool = False
    otlp_endpoint: str = "http://localhost:4317"  # AI Toolkit gRPC endpoint
    enable_sensitive_data: bool = True  # Capture prompts/completions
    
    # Evaluation
    evaluation_output_dir: str = "./outputs/evaluation"
    evaluation_batch_size: int = 10
    
    # File paths
    inputs_dir: Path = Path("./inputs")
    outputs_dir: Path = Path("./outputs")
    
    # Workflow orchestration
    max_concurrent_agents: int = Field(default=5, ge=1, le=20)
    group_chat_max_rounds: int = Field(default=10, ge=1, le=50)
    
    @field_validator("foundry_project_endpoint", "azure_openai_endpoint")
    @classmethod
    def validate_endpoint(cls, v: Optional[str]) -> Optional[str]:
        """Validate endpoint URLs."""
        if v and not v.startswith(("http://", "https://")):
            raise ValueError("Endpoint must start with http:// or https://")
        return v
    
    @field_validator("inputs_dir", "outputs_dir")
    @classmethod
    def validate_paths(cls, v: Path) -> Path:
        """Ensure directories exist."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    def get_evaluation_dir(self, run_name: Optional[str] = None) -> Path:
        """Get evaluation output directory, optionally with run name."""
        eval_dir = Path(self.evaluation_output_dir)
        if run_name:
            eval_dir = eval_dir / run_name
        eval_dir.mkdir(parents=True, exist_ok=True)
        return eval_dir


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
