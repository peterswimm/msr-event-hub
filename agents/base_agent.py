"""
Base Knowledge Extraction Agent

Abstract base class for all knowledge extraction agents (paper, talk, repository).
Handles LLM integration, schema validation, and output serialization.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
from dotenv import load_dotenv

try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.core.credentials import AzureKeyCredential
except ImportError:
    ChatCompletionsClient = None

from core.schemas import BaseKnowledgeArtifact, SourceType

load_dotenv()
logger = logging.getLogger(__name__)


class BaseKnowledgeAgent(ABC):
    """
    Abstract base class for knowledge extraction agents.

    Subclasses implement:
    - get_prompts(): Define extraction prompts
    - extract_from_source(): Handle source-specific extraction
    - parse_extraction_output(): Parse LLM response into schema
    """

    def __init__(
        self,
        source_type: SourceType,
        llm_provider: str = "azure-openai",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        """
        Initialize base agent.

        Args:
            source_type: Type of artifact (paper, talk, repository)
            llm_provider: LLM provider (azure-openai, openai, anthropic)
            model: Model name (overrides env config)
            temperature: LLM temperature (0.0-1.0)
            max_tokens: Max tokens in response
        """
        self.source_type = source_type
        self.llm_provider = llm_provider
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize LLM client
        self.client = self._initialize_llm_client(model)
        self.model = model or self._get_default_model()

        logger.info(f"Initialized {self.__class__.__name__} with {llm_provider} ({self.model})")

    def _initialize_llm_client(self, model: Optional[str]):
        """Initialize LLM client based on provider"""
        if self.llm_provider == "azure-openai":
            endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_KEY")

            if not endpoint or not api_key:
                raise ValueError(
                    "Azure OpenAI credentials not found. Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY"
                )

            return ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

        elif self.llm_provider == "openai":
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not set")
                return OpenAI(api_key=api_key)
            except ImportError:
                raise ImportError("openai package required for OpenAI provider")

        elif self.llm_provider == "anthropic":
            try:
                import anthropic
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not set")
                return anthropic.Anthropic(api_key=api_key)
            except ImportError:
                raise ImportError("anthropic package required for Anthropic provider")

        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    def _get_default_model(self) -> str:
        """Get default model for this provider"""
        if self.llm_provider == "azure-openai":
            return os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        elif self.llm_provider == "openai":
            return os.getenv("OPENAI_MODEL", "gpt-4")
        elif self.llm_provider == "anthropic":
            return os.getenv("ANTHROPIC_MODEL", "claude-opus-4-1-20250805")
        return "gpt-4"

    @abstractmethod
    def get_prompts(self) -> Dict[str, str]:
        """
        Return extraction prompts for this agent type.

        Returns:
            Dict with keys: system_prompt, extraction_prompt
        """
        pass

    @abstractmethod
    def extract_from_source(self, source_input: Any) -> str:
        """
        Extract text content from source (paper, transcript, repo, etc).

        Args:
            source_input: Source-specific input (file path, URL, text, etc.)

        Returns:
            Extracted text content for LLM processing
        """
        pass

    @abstractmethod
    def parse_extraction_output(self, llm_response: str) -> BaseKnowledgeArtifact:
        """
        Parse LLM response into structured knowledge artifact.

        Args:
            llm_response: Raw LLM response text

        Returns:
            BaseKnowledgeArtifact (or subclass)
        """
        pass

    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call LLM with given prompts.

        Args:
            system_prompt: System context
            user_prompt: User query/extraction prompt

        Returns:
            LLM response text
        """
        try:
            if self.llm_provider == "azure-openai":
                response = self.client.complete(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    model=self.model,
                )
                return response.choices[0].message.content

            elif self.llm_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content

            elif self.llm_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=self.temperature,
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def extract(self, source_input: Any) -> BaseKnowledgeArtifact:
        """
        Main extraction pipeline.

        Args:
            source_input: Source-specific input

        Returns:
            Structured knowledge artifact
        """
        logger.info(f"Starting extraction from {self.source_type.value} source")

        # 1. Extract content from source
        content = self.extract_from_source(source_input)
        logger.info(f"Extracted {len(content)} characters from source")

        # 2. Get prompts for this agent type
        prompts = self.get_prompts()

        # 3. Call LLM
        llm_response = self.call_llm(prompts["system_prompt"], prompts["extraction_prompt"] + "\n\n" + content)
        logger.info(f"LLM response: {len(llm_response)} characters")

        # 4. Parse into structured format
        artifact = self.parse_extraction_output(llm_response)
        logger.info(f"Successfully extracted knowledge artifact: {artifact.title}")

        return artifact

    def save_artifact(self, artifact: BaseKnowledgeArtifact, output_dir: str = "outputs/structured") -> str:
        """
        Save knowledge artifact to JSON file.

        Args:
            artifact: Knowledge artifact
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.source_type.value}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        # Save
        with open(filepath, "w") as f:
            json.dump(artifact.to_dict(), f, indent=2)

        logger.info(f"Saved artifact to {filepath}")
        return filepath

    def save_summary(self, artifact: BaseKnowledgeArtifact, output_dir: str = "outputs/summaries") -> str:
        """
        Save human-readable summary.

        Args:
            artifact: Knowledge artifact
            output_dir: Output directory

        Returns:
            Path to saved file
        """
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.source_type.value}_{timestamp}_summary.md"
        filepath = os.path.join(output_dir, filename)

        # Create summary
        summary = self._generate_summary_markdown(artifact)

        # Save
        with open(filepath, "w") as f:
            f.write(summary)

        logger.info(f"Saved summary to {filepath}")
        return filepath

    def _generate_summary_markdown(self, artifact: BaseKnowledgeArtifact) -> str:
        """Generate human-readable markdown summary"""
        lines = [
            f"# {artifact.title}",
            "",
            f"**Source Type**: {artifact.source_type.value}",
            f"**Contributors**: {', '.join(artifact.contributors)}",
            f"**Confidence**: {artifact.confidence_score:.1%}",
            f"**Extracted**: {artifact.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overview",
            artifact.plain_language_overview,
            "",
            "## Technical Problem",
            artifact.technical_problem_addressed,
            "",
            "## Key Methods",
            artifact.key_methods_approach,
            "",
            "## Primary Claims",
        ]

        for claim in artifact.primary_claims_capabilities:
            lines.append(f"- {claim}")

        lines.extend([
            "",
            "## Novelty",
            artifact.novelty_vs_prior_work,
            "",
            "## Limitations",
        ])

        for limitation in artifact.limitations_constraints:
            lines.append(f"- {limitation}")

        lines.extend([
            "",
            "## Potential Impact",
            artifact.potential_impact,
            "",
            "## Open Questions",
        ])

        for question in artifact.open_questions_future_work:
            lines.append(f"- {question}")

        return "\n".join(lines)
