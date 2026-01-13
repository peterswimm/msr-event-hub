"""Test dataset utilities for evaluation."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def create_test_dataset(
    test_cases: List[Dict[str, Any]],
    output_path: str,
) -> str:
    """
    Create a test dataset in JSONL format for evaluation.
    
    **IMPORTANT**: Do NOT include timestamp fields in your dataset.
    Fields with timestamp values (e.g., '2025-08-25T11:27:49.437767')
    will cause SDK errors during evaluation.
    
    Required fields in each test case:
    - source_text: The input text to process
    - expected_title: Expected title extraction (optional for validation)
    - expected_key_points_count: Expected number of key points (optional)
    
    Args:
        test_cases: List of test case dictionaries
        output_path: Where to save the JSONL file
        
    Returns:
        Path to created dataset file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Validate and clean test cases
    cleaned_cases = []
    for i, case in enumerate(test_cases):
        # Remove any timestamp fields
        cleaned_case = {
            k: v for k, v in case.items()
            if not isinstance(v, str) or 'T' not in v or ':' not in v
        }
        
        # Ensure required field exists
        if "source_text" not in cleaned_case:
            logger.warning(f"Test case {i} missing 'source_text' field, skipping")
            continue
        
        cleaned_cases.append(cleaned_case)
    
    # Write JSONL
    with open(output_path, 'w', encoding='utf-8') as f:
        for case in cleaned_cases:
            f.write(json.dumps(case) + '\n')
    
    logger.info(f"Created test dataset with {len(cleaned_cases)} cases: {output_path}")
    return str(output_path)


def load_test_dataset(file_path: str) -> List[Dict[str, Any]]:
    """
    Load a test dataset from JSONL format.
    
    Args:
        file_path: Path to JSONL dataset
        
    Returns:
        List of test case dictionaries
    """
    test_cases = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            test_cases.append(json.loads(line))
    
    logger.info(f"Loaded {len(test_cases)} test cases from {file_path}")
    return test_cases


def create_sample_paper_dataset() -> str:
    """Create a sample test dataset for paper extraction."""
    sample_cases = [
        {
            "source_text": """
                Title: Deep Learning for Computer Vision
                
                Abstract: This paper presents a novel approach to image classification
                using convolutional neural networks. We achieve state-of-the-art results
                on ImageNet with an accuracy of 95.2%.
                
                Authors: Jane Smith, John Doe
                Published: 2024
                
                Key contributions include:
                1. Novel CNN architecture
                2. Improved training techniques
                3. Comprehensive evaluation
            """,
            "expected_title": "Deep Learning for Computer Vision",
            "expected_key_points_count": 3,
        },
        {
            "source_text": """
                Title: Transformers for Natural Language Processing
                
                Abstract: We introduce a new attention mechanism that improves
                performance on machine translation tasks by 15% over BERT.
                
                Authors: Alice Johnson, Bob Wilson
                Published: 2024
                
                Main findings:
                - Better context understanding
                - Faster training
                - Lower computational cost
            """,
            "expected_title": "Transformers for Natural Language Processing",
            "expected_key_points_count": 3,
        },
    ]
    
    dataset_path = "./evaluation/datasets/papers_test.jsonl"
    return create_test_dataset(sample_cases, dataset_path)
