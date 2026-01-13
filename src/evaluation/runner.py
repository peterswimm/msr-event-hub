"""
Evaluation runner for knowledge extraction agents.

Orchestrates:
- Test dataset loading
- Agent execution across test cases
- Evaluator execution
- Results aggregation and reporting
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from azure.ai.evaluation import AzureOpenAIModelConfiguration, evaluate

from config import get_settings
from .evaluators import (
    ExtractionQualityEvaluator,
    StructureCompletenessEvaluator,
    SourceFidelityEvaluator,
)

logger = logging.getLogger(__name__)


class EvaluationRunner:
    """
    Run comprehensive evaluation of knowledge extraction agents.
    
    Usage:
        runner = EvaluationRunner(agent=my_agent)
        results = await runner.run_evaluation(
            test_dataset="./evaluation/datasets/papers_test.jsonl",
            run_name="paper_extraction_v1"
        )
    """
    
    def __init__(
        self,
        agent: Any,  # ModernKnowledgeAgent instance
        model_config: Optional[AzureOpenAIModelConfiguration] = None,
    ):
        """
        Initialize evaluation runner.
        
        Args:
            agent: The knowledge extraction agent to evaluate
            model_config: Azure OpenAI config for prompt-based evaluators
        """
        self.agent = agent
        self.settings = get_settings()
        self.model_config = model_config or self._default_model_config()
        
        # Initialize evaluators
        self.evaluators = {
            "structure_completeness": StructureCompletenessEvaluator(),
            "extraction_quality": ExtractionQualityEvaluator(),
            "source_fidelity": SourceFidelityEvaluator(self.model_config),
        }
    
    def _default_model_config(self) -> AzureOpenAIModelConfiguration:
        """Create default model configuration for evaluators."""
        # Use Azure OpenAI endpoint (not Foundry project endpoint)
        if not self.settings.azure_openai_endpoint:
            raise ValueError(
                "Azure OpenAI endpoint required for evaluation. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY in environment."
            )
        
        return AzureOpenAIModelConfiguration(
            azure_deployment=self.settings.foundry_model_deployment,
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_key,
            api_version=self.settings.azure_openai_api_version,
        )
    
    async def run_evaluation(
        self,
        test_dataset: str,
        run_name: Optional[str] = None,
        save_results: bool = True,
    ) -> Dict[str, Any]:
        """
        Run full evaluation pipeline.
        
        Steps:
        1. Load test dataset (JSONL format)
        2. Run agent on each test case to collect responses
        3. Run all evaluators using evaluate() API
        4. Save results
        
        Args:
            test_dataset: Path to JSONL test dataset
            run_name: Optional name for this evaluation run
            save_results: Whether to save results to disk
            
        Returns:
            Dict with evaluation results and metrics
        """
        run_name = run_name or f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting evaluation run: {run_name}")
        
        # Step 1: Collect agent responses
        logger.info("Step 1: Running agent on test dataset...")
        agent_responses_file = await self._collect_agent_responses(
            test_dataset, run_name
        )
        
        # Step 2: Run evaluation using Azure AI evaluate() API
        logger.info("Step 2: Running evaluators...")
        eval_results = self._run_evaluators(agent_responses_file, run_name)
        
        # Step 3: Generate report
        logger.info("Step 3: Generating evaluation report...")
        report = self._generate_report(eval_results, run_name)
        
        if save_results:
            report_path = self._save_report(report, run_name)
            logger.info(f"✓ Evaluation complete. Report saved to: {report_path}")
        
        return report
    
    async def _collect_agent_responses(
        self,
        test_dataset: str,
        run_name: str
    ) -> str:
        """
        Run agent on test dataset and collect responses.
        
        Creates a new JSONL file with original test data plus agent responses.
        
        Args:
            test_dataset: Path to test dataset
            run_name: Name for this run
            
        Returns:
            Path to responses file
        """
        # Load test cases
        test_cases = []
        with open(test_dataset, 'r', encoding='utf-8') as f:
            for line in f:
                test_cases.append(json.loads(line))
        
        logger.info(f"Loaded {len(test_cases)} test cases")
        
        # Run agent on each case
        responses = []
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"Processing test case {i}/{len(test_cases)}...")
            
            try:
                # Extract input text
                source_text = test_case.get("source_text", "")
                
                # Run agent
                artifact = await self.agent.extract_async(source_text)
                
                # Combine test case with agent response
                response_record = {
                    **test_case,
                    "agent_response": artifact.model_dump(),
                }
                responses.append(response_record)
                
            except Exception as e:
                logger.error(f"Error processing test case {i}: {e}")
                # Still include the test case but mark as error
                responses.append({
                    **test_case,
                    "agent_response": {"error": str(e)},
                })
        
        # Save responses to JSONL
        output_dir = self.settings.get_evaluation_dir(run_name)
        responses_file = output_dir / "agent_responses.jsonl"
        
        with open(responses_file, 'w', encoding='utf-8') as f:
            for response in responses:
                f.write(json.dumps(response) + '\n')
        
        logger.info(f"Agent responses saved to: {responses_file}")
        return str(responses_file)
    
    def _run_evaluators(
        self,
        agent_responses_file: str,
        run_name: str
    ) -> Dict[str, Any]:
        """
        Run all evaluators using Azure AI evaluate() API.
        
        Args:
            agent_responses_file: Path to JSONL with agent responses
            run_name: Name for this run
            
        Returns:
            Evaluation results from evaluate() API
        """
        output_dir = self.settings.get_evaluation_dir(run_name)
        
        # Configure evaluator column mappings
        evaluator_config = {
            "structure_completeness": {
                "column_mapping": {
                    "extracted_artifact": "${data.agent_response}"
                }
            },
            "extraction_quality": {
                "column_mapping": {
                    "extracted_artifact": "${data.agent_response}"
                }
            },
            "source_fidelity": {
                "column_mapping": {
                    "source_text": "${data.source_text}",
                    "extracted_artifact": "${data.agent_response}"
                }
            },
        }
        
        # Run evaluation
        logger.info("Running Azure AI evaluation...")
        results = evaluate(
            data=agent_responses_file,
            evaluators=self.evaluators,
            evaluator_config=evaluator_config,
            output_path=str(output_dir / "evaluation_results")
        )
        
        return results
    
    def _generate_report(
        self,
        eval_results: Dict[str, Any],
        run_name: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report.
        
        Args:
            eval_results: Results from evaluate() API
            run_name: Name for this run
            
        Returns:
            Formatted report dict
        """
        # Extract metrics from results
        metrics = eval_results.get("metrics", {})
        
        report = {
            "run_name": run_name,
            "timestamp": datetime.now().isoformat(),
            "agent_name": self.agent.agent_name,
            "metrics": metrics,
            "summary": {
                "total_cases": eval_results.get("rows_processed", 0),
                "avg_structure_score": metrics.get("structure_completeness_score", 0),
                "avg_field_coverage": metrics.get("field_coverage_percent", 0),
            }
        }
        
        return report
    
    def _save_report(self, report: Dict[str, Any], run_name: str) -> str:
        """Save evaluation report as JSON."""
        output_dir = self.settings.get_evaluation_dir(run_name)
        report_file = output_dir / "evaluation_report.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dumps(report, f, indent=2)
        
        return str(report_file)
