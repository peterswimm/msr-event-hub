"""
Custom evaluators for knowledge extraction quality assessment.

Combines:
- Built-in Azure AI evaluators (coherence, fluency)
- Custom code-based evaluators (structure completeness)
- Custom prompt-based evaluators (domain fidelity)
"""

import json
import logging
from typing import Any, Dict

from azure.ai.evaluation import AzureOpenAIModelConfiguration

logger = logging.getLogger(__name__)


class StructureCompletenessEvaluator:
    """
    Custom code-based evaluator: Assesses completeness of extracted structure.
    
    Checks that required fields are present and non-empty:
    - title
    - summary
    - key_points (minimum 3)
    - authors/contributors
    - dates
    """
    
    def __init__(self):
        """Initialize evaluator."""
        self.required_fields = [
            "title",
            "summary",
            "key_points",
            "authors",
            "extracted_at"
        ]
    
    def __call__(self, *, extracted_artifact: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Evaluate structure completeness.
        
        Args:
            extracted_artifact: The JSON artifact produced by the agent
            
        Returns:
            Dict with completeness score and details
        """
        missing_fields = []
        incomplete_fields = []
        
        # Check required fields exist
        for field in self.required_fields:
            if field not in extracted_artifact:
                missing_fields.append(field)
            elif not extracted_artifact[field]:
                incomplete_fields.append(field)
        
        # Special check for key_points minimum count
        key_points = extracted_artifact.get("key_points", [])
        if len(key_points) < 3:
            incomplete_fields.append(f"key_points (only {len(key_points)}, need 3+)")
        
        # Calculate score (0-100)
        total_checks = len(self.required_fields) + 1  # +1 for key_points count
        failed_checks = len(missing_fields) + len(incomplete_fields)
        score = ((total_checks - failed_checks) / total_checks) * 100
        
        return {
            "structure_completeness_score": round(score, 2),
            "missing_fields": missing_fields,
            "incomplete_fields": incomplete_fields,
            "has_sufficient_key_points": len(key_points) >= 3,
        }


class ExtractionQualityEvaluator:
    """
    Custom code-based evaluator: Assesses overall extraction quality metrics.
    
    Evaluates:
    - Content length appropriateness
    - Field diversity (number of populated fields)
    - Metadata completeness
    """
    
    def __init__(self):
        """Initialize evaluator."""
        pass
    
    def __call__(self, *, extracted_artifact: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Evaluate extraction quality.
        
        Args:
            extracted_artifact: The JSON artifact produced by the agent
            
        Returns:
            Dict with quality metrics
        """
        # Summary length check (100-500 words is good)
        summary = extracted_artifact.get("summary", "")
        word_count = len(summary.split())
        summary_quality = "good" if 100 <= word_count <= 500 else "needs_improvement"
        
        # Field diversity
        populated_fields = sum(
            1 for v in extracted_artifact.values()
            if v and (not isinstance(v, list) or len(v) > 0)
        )
        total_fields = len(extracted_artifact)
        field_coverage = (populated_fields / total_fields) * 100 if total_fields > 0 else 0
        
        # Key points analysis
        key_points = extracted_artifact.get("key_points", [])
        avg_key_point_length = (
            sum(len(kp.split()) for kp in key_points) / len(key_points)
            if key_points else 0
        )
        
        return {
            "summary_word_count": word_count,
            "summary_quality": summary_quality,
            "field_coverage_percent": round(field_coverage, 2),
            "key_points_count": len(key_points),
            "avg_key_point_words": round(avg_key_point_length, 1),
        }


class SourceFidelityEvaluator:
    """
    Custom prompt-based evaluator: Uses LLM to assess source fidelity.
    
    Evaluates whether extracted content accurately represents the source
    without hallucination or distortion.
    """
    
    def __init__(self, model_config: AzureOpenAIModelConfiguration):
        """
        Initialize with model configuration for LLM-as-judge.
        
        Args:
            model_config: Azure OpenAI configuration for the judge model
        """
        self.model_config = model_config
        # In a real implementation, this would load a .prompty file
        # For now, we'll store the prompt template
        self.prompt_template = """You are evaluating knowledge extraction fidelity.

Source text excerpt:
{source_text}

Extracted summary:
{summary}

Extracted key points:
{key_points}

Evaluate:
1. Does the summary accurately reflect the source content?
2. Are the key points factual and grounded in the source?
3. Are there any hallucinations or unsupported claims?

Return JSON with:
- fidelity_score (1-5, where 5 is perfect fidelity)
- accuracy_issues (list of problems found)
- reasoning (brief explanation)
"""
    
    def __call__(
        self,
        *,
        source_text: str,
        extracted_artifact: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Evaluate source fidelity using LLM judgment.
        
        Args:
            source_text: Original source text
            extracted_artifact: Extracted artifact JSON
            
        Returns:
            Dict with fidelity assessment
        """
        # Format prompt
        summary = extracted_artifact.get("summary", "")
        key_points = "\n".join(f"- {kp}" for kp in extracted_artifact.get("key_points", []))
        
        prompt = self.prompt_template.format(
            source_text=source_text[:2000],  # Truncate for LLM context
            summary=summary,
            key_points=key_points
        )
        
        # In production, this would call the LLM via the model_config
        # For now, return placeholder
        logger.warning("SourceFidelityEvaluator requires LLM call - returning placeholder")
        
        return {
            "fidelity_score": 4,
            "accuracy_issues": [],
            "reasoning": "Placeholder evaluation - implement LLM call for production",
        }
