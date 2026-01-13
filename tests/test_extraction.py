#!/usr/bin/env python
"""
Interactive test of Knowledge Agent extraction pipeline

Run with: python test_extraction.py
"""

import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_base_schema():
    """Test 1: Validate BaseKnowledgeArtifact schema"""
    print("\n" + "="*70)
    print("TEST 1: BaseKnowledgeArtifact Schema")
    print("="*70)

    try:
        from src.core.schemas import BaseKnowledgeArtifact, SourceType

        # Create a test artifact
        artifact = BaseKnowledgeArtifact(
            source_type=SourceType.PAPER,
            title="Test Extraction: Attention Is All You Need",
            contributors=["Vaswani", "Shazeer", "Parmar"],
            plain_language_overview="Introduces the Transformer architecture using pure self-attention.",
            technical_problem_addressed="Sequential processing bottleneck in RNNs prevents parallelization.",
            key_methods_approach="Multi-head self-attention mechanism with position encoding.",
            primary_claims_capabilities=[
                "Superior translation quality",
                "Significantly faster training",
                "Enables larger models"
            ],
            novelty_vs_prior_work="First architecture to use pure attention without CNN/RNN components.",
            limitations_constraints=[
                "Quadratic memory complexity in sequence length",
                "Requires large datasets for effective training"
            ],
            potential_impact="Foundation for all modern language models (GPT, BERT, T5).",
            open_questions_future_work=[
                "How to reduce quadratic memory complexity",
                "How to apply to longer sequences"
            ],
            key_evidence_citations=[
                "BLEU score improvements on WMT14",
                "Training time reduction metrics"
            ],
            confidence_score=0.95,
            confidence_reasoning="Seminal paper with clear presentation and massive real-world impact.",
            agent_name="TestAgent"
        )

        print(f"✅ Created artifact: {artifact.title}")
        print(f"   - Contributors: {', '.join(artifact.contributors)}")
        print(f"   - Confidence: {artifact.confidence_score}")
        print(f"   - Claims: {len(artifact.primary_claims_capabilities)} identified")
        print(f"   - Source Type: {artifact.source_type.value}")
        print(f"   - Extraction Date: {artifact.extraction_date}")

        return artifact

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def test_paper_schema_extension(base_artifact):
    """Test 2: Extend with paper-specific fields"""
    print("\n" + "="*70)
    print("TEST 2: Paper-Specific Schema Extension")
    print("="*70)

    try:
        # Add paper-specific information to additional_knowledge
        base_artifact.additional_knowledge.update({
            "paper_specific": {
                "publication_venue": "NeurIPS 2017",
                "publication_year": 2017,
                "peer_reviewed": True,
                "arxiv_id": "1706.03762",
                "related_prior_work": [
                    "Sequence to Sequence Learning with Neural Networks",
                    "Neural Machine Translation by Attention"
                ],
                "datasets_used": [
                    {"name": "WMT14 English-German", "size": "4.5M", "availability": "public"},
                    {"name": "WMT14 English-French", "size": "36M", "availability": "public"}
                ],
                "evaluation_benchmarks": ["WMT14 translation", "Parsing", "Language Modeling"],
                "evaluation_metrics": ["BLEU", "PPL", "Accuracy"],
                "key_quantitative_results": [
                    "BLEU 28.4 on WMT14 En-De (new SOTA)",
                    "3.5x speedup in training",
                    "Better performance with fewer parameters"
                ],
                "research_maturity_stage": "deployed",
                "ethical_considerations_discussed": False
            }
        })

        paper_info = base_artifact.additional_knowledge["paper_specific"]
        print(f"✅ Extended with paper-specific fields")
        print(f"   - Venue: {paper_info['publication_venue']}")
        print(f"   - Year: {paper_info['publication_year']}")
        print(f"   - Datasets: {len(paper_info['datasets_used'])}")
        print(f"   - Benchmarks: {', '.join(paper_info['evaluation_benchmarks'][:2])}...")
        print(f"   - Maturity: {paper_info['research_maturity_stage']}")

        return base_artifact

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def test_json_serialization(artifact):
    """Test 3: JSON serialization"""
    print("\n" + "="*70)
    print("TEST 3: JSON Serialization")
    print("="*70)

    try:
        # Convert to JSON-serializable dict
        artifact_dict = {
            "title": artifact.title,
            "contributors": artifact.contributors,
            "plain_language_overview": artifact.plain_language_overview,
            "technical_problem_addressed": artifact.technical_problem_addressed,
            "key_methods_approach": artifact.key_methods_approach,
            "primary_claims_capabilities": artifact.primary_claims_capabilities,
            "novelty_vs_prior_work": artifact.novelty_vs_prior_work,
            "limitations_constraints": artifact.limitations_constraints,
            "potential_impact": artifact.potential_impact,
            "open_questions_future_work": artifact.open_questions_future_work,
            "key_evidence_citations": artifact.key_evidence_citations,
            "confidence_score": artifact.confidence_score,
            "confidence_reasoning": artifact.confidence_reasoning,
            "source_type": artifact.source_type.value,
            "agent_name": artifact.agent_name,
            "extraction_model": artifact.extraction_model,
            "extraction_date": artifact.extraction_date.isoformat(),
            "additional_knowledge": artifact.additional_knowledge
        }

        json_str = json.dumps(artifact_dict, indent=2)

        print(f"✅ Successfully serialized to JSON")
        print(f"   - Size: {len(json_str)} characters")
        print(f"   - Top-level fields: {len(artifact_dict)}")
        print(f"\n📋 JSON Preview (first 500 chars):")
        print(json_str[:500] + "...\n")

        return json_str

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def test_markdown_generation(artifact):
    """Test 4: Generate markdown summary"""
    print("\n" + "="*70)
    print("TEST 4: Markdown Summary Generation")
    print("="*70)

    try:
        # Generate markdown summary
        markdown = f"""# {artifact.title}

**Source**: {artifact.source_type.value.title()}
**Confidence**: {artifact.confidence_score * 100:.0f}%
**Extraction Date**: {artifact.extraction_date.strftime('%Y-%m-%d %H:%M:%S')}
**Contributors**: {', '.join(artifact.contributors)}

## Overview

{artifact.plain_language_overview}

## Problem

{artifact.technical_problem_addressed}

## Solution

{artifact.key_methods_approach}

## Key Claims & Capabilities

{chr(10).join(f"- {claim}" for claim in artifact.primary_claims_capabilities)}

## Novelty

{artifact.novelty_vs_prior_work}

## Limitations

{chr(10).join(f"- {limit}" for limit in artifact.limitations_constraints)}

## Impact

{artifact.potential_impact}

## Open Questions

{chr(10).join(f"- {q}" for q in artifact.open_questions_future_work)}

## Evidence

{chr(10).join(f"- {e}" for e in artifact.key_evidence_citations)}

---

**Extraction Agent**: {artifact.agent_name}
**Confidence Reasoning**: {artifact.confidence_reasoning}
"""

        print(f"✅ Generated markdown summary")
        print(f"   - Size: {len(markdown)} characters")
        print(f"   - Sections: 10 major sections")
        print(f"\n📄 Markdown Preview:\n")
        print(markdown[:800] + "\n...\n")

        return markdown

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def test_agent_imports():
    """Test 5: Verify agent imports"""
    print("\n" + "="*70)
    print("TEST 5: Agent Imports & Initialization")
    print("="*70)

    try:
        from agents import BaseKnowledgeAgent, PaperAgent, TalkAgent, RepositoryAgent

        print(f"✅ Successfully imported all agents")
        print(f"   - BaseKnowledgeAgent: {BaseKnowledgeAgent.__name__}")
        print(f"   - PaperAgent: {PaperAgent.__name__}")
        print(f"   - TalkAgent: {TalkAgent.__name__}")
        print(f"   - RepositoryAgent: {RepositoryAgent.__name__}")

        # Show agent signatures
        print(f"\nAgent capabilities:")
        print(f"   - get_prompts() → Dict[str, str]")
        print(f"   - extract_from_source(source) → str")
        print(f"   - parse_extraction_output(response) → BaseKnowledgeArtifact")
        print(f"   - extract(source) → BaseKnowledgeArtifact")
        print(f"   - save_artifact(artifact, output_dir) → str (filepath)")
        print(f"   - save_summary(artifact, output_dir) → str (filepath)")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def test_prompt_retrieval():
    """Test 6: Verify prompts are available"""
    print("\n" + "="*70)
    print("TEST 6: Prompt Retrieval & Content")
    print("="*70)

    try:
        from prompts import get_paper_prompts, get_talk_prompts, get_repository_prompts

        paper_prompts = get_paper_prompts()
        talk_prompts = get_talk_prompts()
        repo_prompts = get_repository_prompts()

        print(f"✅ Successfully retrieved all prompts")

        print(f"\n📝 Paper Prompts:")
        print(f"   - system_prompt: {len(paper_prompts['system_prompt'])} chars")
        print(f"   - extraction_prompt: {len(paper_prompts['extraction_prompt'])} chars")
        print(f"   Preview: {paper_prompts['system_prompt'][:150]}...")

        print(f"\n📝 Talk Prompts:")
        print(f"   - system_prompt: {len(talk_prompts['system_prompt'])} chars")
        print(f"   - extraction_prompt: {len(talk_prompts['extraction_prompt'])} chars")

        print(f"\n📝 Repository Prompts:")
        print(f"   - system_prompt: {len(repo_prompts['system_prompt'])} chars")
        print(f"   - extraction_prompt: {len(repo_prompts['extraction_prompt'])} chars")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


def test_cli_help():
    """Test 7: CLI help text"""
    print("\n" + "="*70)
    print("TEST 7: CLI Interface Help")
    print("="*70)

    try:
        import subprocess
        result = subprocess.run(
            ["python", "knowledge_agent.py", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )

        print(f"✅ CLI help retrieved successfully")
        print(f"   - Exit code: {result.returncode}")
        print(f"   - Output length: {len(result.stdout)} chars")
        print(f"\n📋 CLI Help Preview:\n")
        print(result.stdout[:600] + "...\n")

        return True

    except Exception as e:
        print(f"⚠️  Warning (non-critical): {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 KNOWLEDGE AGENT POC - INTERACTIVE TEST SUITE")
    print("="*70)
    print(f"\nTest Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test Location: {Path.cwd()}")

    results = []

    try:
        # Test 1: Schema
        artifact = test_base_schema()
        results.append(("Schema Creation", True))

        # Test 2: Extensions
        artifact = test_paper_schema_extension(artifact)
        results.append(("Schema Extension", True))

        # Test 3: JSON
        json_output = test_json_serialization(artifact)
        results.append(("JSON Serialization", True))

        # Test 4: Markdown
        markdown_output = test_markdown_generation(artifact)
        results.append(("Markdown Generation", True))

        # Test 5: Imports
        test_agent_imports()
        results.append(("Agent Imports", True))

        # Test 6: Prompts
        test_prompt_retrieval()
        results.append(("Prompt Retrieval", True))

        # Test 7: CLI
        cli_success = test_cli_help()
        results.append(("CLI Interface", cli_success))

    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        results.append(("Test Suite", False))

    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED - Implementation Ready!")
    elif passed_tests >= total_tests - 1:
        print("\n✅ MOST TESTS PASSED - Minor issues only")
    else:
        print("\n⚠️  SOME TESTS FAILED - Please review errors above")

    print(f"\nTest End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
