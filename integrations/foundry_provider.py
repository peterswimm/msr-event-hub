"""
Azure AI Foundry LLM Provider

Provides LLM capabilities using Azure AI Foundry models.
Integrates seamlessly with Knowledge Agent extraction pipeline.
"""

import logging
import json
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

try:
    from azure.ai.projects import AIProjectClient
    from azure.identity import DefaultAzureCredential
    FOUNDRY_AVAILABLE = True
except ImportError:
    FOUNDRY_AVAILABLE = False

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    async def extract(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3
    ) -> str:
        """Extract using LLM"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, str]:
        """Get model information"""
        pass


class AzureAIFoundryProvider(BaseLLMProvider):
    """LLM provider using Azure AI Foundry models

    Supports models deployed in Azure AI Foundry:
    - gpt-4-turbo
    - gpt-4o
    - phi-3
    - mistral
    """

    def __init__(
        self,
        project_connection_string: str,
        model_name: str = "gpt-4-turbo",
        enable_tracing: bool = True
    ):
        """Initialize Foundry provider

        Args:
            project_connection_string: Azure AI Foundry project connection string
            model_name: Model to use (default: gpt-4-turbo)
            enable_tracing: Enable request tracing in Foundry
        """
        if not FOUNDRY_AVAILABLE:
            raise ImportError(
                "azure-ai-projects not installed. "
                "Install with: pip install azure-ai-projects"
            )

        self.project_connection_string = project_connection_string
        self.model_name = model_name
        self.enable_tracing = enable_tracing
        self.client = None

        self._initialize_client()

    def _initialize_client(self):
        """Initialize Foundry client"""
        try:
            self.client = AIProjectClient.from_connection_string(
                conn_str=self.project_connection_string,
                credential=DefaultAzureCredential()
            )
            logger.info(f"Initialized Azure AI Foundry client with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Foundry client: {e}")
            raise

    async def extract(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3
    ) -> str:
        """Extract using Foundry model

        Args:
            system_prompt: System instructions for the model
            user_prompt: User query/document content
            temperature: Model temperature (0.0-1.0)

        Returns:
            Extracted/analyzed content as string
        """
        try:
            if self.client is None:
                self._initialize_client()

            # Create messages in Foundry format
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Call Foundry model
            response = self.client.agents.create_message(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=4096,
                top_p=0.95
            )

            # Extract response content
            result = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"Foundry extraction successful (model: {self.model_name})")
            return result

        except Exception as e:
            logger.error(f"Foundry extraction failed: {e}")
            raise

    def get_model_info(self) -> Dict[str, str]:
        """Get info about deployed model"""
        return {
            "provider": "azure-ai-foundry",
            "model": self.model_name,
            "project": getattr(self.client, 'project_name', 'unknown') if self.client else 'unknown',
            "tracing_enabled": str(self.enable_tracing)
        }


class FoundryModelRegistry:
    """Registry of available Foundry models

    Allows switching between different models based on use case.
    """

    MODELS = {
        "gpt-4-turbo": {
            "description": "High-capability model for complex reasoning",
            "tokens": 128000,
            "use_cases": ["paper_extraction", "complex_reasoning"]
        },
        "gpt-4o": {
            "description": "Optimized GPT-4 variant",
            "tokens": 128000,
            "use_cases": ["paper_extraction", "talk_extraction"]
        },
        "phi-3": {
            "description": "Efficient small language model",
            "tokens": 4096,
            "use_cases": ["quick_extraction", "lightweight"]
        },
        "mistral": {
            "description": "Open-source alternative",
            "tokens": 32000,
            "use_cases": ["general_extraction", "cost_effective"]
        }
    }

    @classmethod
    def get_model(cls, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model information"""
        return cls.MODELS.get(model_name)

    @classmethod
    def get_recommended_model(cls, artifact_type: str) -> str:
        """Get recommended model for artifact type

        Args:
            artifact_type: 'paper', 'talk', or 'repository'

        Returns:
            Recommended model name
        """
        recommendations = {
            "paper": "gpt-4-turbo",  # Complex academic papers
            "talk": "gpt-4o",        # Conversational transcripts
            "repository": "phi-3"    # Code is lightweight
        }
        return recommendations.get(artifact_type, "gpt-4-turbo")

    @classmethod
    def list_models(cls) -> Dict[str, Dict[str, Any]]:
        """List all available models"""
        return cls.MODELS


def create_foundry_provider(
    project_connection_string: str,
    model_name: str = None,
    artifact_type: str = None
) -> AzureAIFoundryProvider:
    """Factory function to create Foundry provider

    Args:
        project_connection_string: Foundry project connection string
        model_name: Specific model name (optional)
        artifact_type: Type of artifact (paper/talk/repository) for auto-selection

    Returns:
        Configured AzureAIFoundryProvider instance
    """
    # Auto-select model if artifact type provided
    if model_name is None and artifact_type:
        model_name = FoundryModelRegistry.get_recommended_model(artifact_type)
    elif model_name is None:
        model_name = "gpt-4-turbo"

    logger.info(f"Creating Foundry provider with model: {model_name}")
    return AzureAIFoundryProvider(
        project_connection_string=project_connection_string,
        model_name=model_name
    )
