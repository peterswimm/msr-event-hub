#!/usr/bin/env python
"""Quick test of Knowledge Agent - outputs to test_results.txt"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

output = []

try:
    output.append("=" * 70)
    output.append("🧪 KNOWLEDGE AGENT POC - QUICK TEST")
    output.append("=" * 70)

    # Test 1: Import schemas
    output.append("\n[TEST 1] Importing schemas...")
    try:
        from core.schemas import BaseKnowledgeArtifact, SourceType, ResearchMaturityStage
        output.append("✅ Schema imports successful")
    except Exception as e:
        output.append(f"❌ Schema import failed: {e}")
        raise

    # Test 2: Create artifact
    output.append("\n[TEST 2] Creating BaseKnowledgeArtifact...")
    try:
        artifact = BaseKnowledgeArtifact(
            source_type=SourceType.PAPER,
            title="Test Artifact",
            contributors=["Author1", "Author2"],
            plain_language_overview="Test overview",
            confidence_score=0.85
        )
        output.append(f"✅ Artifact created: {artifact.title}")
        output.append(f"   - Type: {artifact.source_type.value}")
        output.append(f"   - Confidence: {artifact.confidence_score}")
    except Exception as e:
        output.append(f"❌ Artifact creation failed: {e}")
        raise

    # Test 3: Import agents
    output.append("\n[TEST 3] Importing agents...")
    try:
        from agents import BaseKnowledgeAgent, PaperAgent, TalkAgent, RepositoryAgent
        output.append("✅ Agent imports successful")
        output.append("   - BaseKnowledgeAgent")
        output.append("   - PaperAgent")
        output.append("   - TalkAgent")
        output.append("   - RepositoryAgent")
    except Exception as e:
        output.append(f"❌ Agent import failed: {e}")
        raise

    # Test 4: Import prompts
    output.append("\n[TEST 4] Importing prompts...")
    try:
        from prompts import get_paper_prompts, get_talk_prompts, get_repository_prompts
        output.append("✅ Prompt imports successful")

        p_prompts = get_paper_prompts()
        t_prompts = get_talk_prompts()
        r_prompts = get_repository_prompts()

        output.append(f"   - Paper prompts: {len(p_prompts)} templates")
        output.append(f"   - Talk prompts: {len(t_prompts)} templates")
        output.append(f"   - Repository prompts: {len(r_prompts)} templates")
    except Exception as e:
        output.append(f"❌ Prompt import failed: {e}")
        raise

    # Test 5: JSON serialization
    output.append("\n[TEST 5] JSON serialization...")
    try:
        import json
        artifact_dict = {
            "title": artifact.title,
            "contributors": artifact.contributors,
            "confidence_score": artifact.confidence_score,
            "source_type": artifact.source_type.value
        }
        json_str = json.dumps(artifact_dict)
        output.append(f"✅ JSON serialization successful")
        output.append(f"   - Size: {len(json_str)} chars")
    except Exception as e:
        output.append(f"❌ JSON serialization failed: {e}")
        raise

    # Test 6: Schema extension
    output.append("\n[TEST 6] Schema extension...")
    try:
        artifact.additional_knowledge.update({
            "paper_specific": {
                "publication_venue": "NeurIPS",
                "publication_year": 2024,
                "peer_reviewed": True
            }
        })
        output.append("✅ Schema extension successful")
        output.append(f"   - Added paper_specific fields")
    except Exception as e:
        output.append(f"❌ Schema extension failed: {e}")
        raise

    # Summary
    output.append("\n" + "=" * 70)
    output.append("📊 TEST RESULTS")
    output.append("=" * 70)
    output.append("\n✅ ALL TESTS PASSED!")
    output.append("\n🎉 Knowledge Agent POC is ready to use!")
    output.append("\nNext steps:")
    output.append("  1. python knowledge_agent.py paper <input.pdf> --output ./outputs")
    output.append("  2. python knowledge_agent.py talk <transcript.txt> --output ./outputs")
    output.append("  3. python knowledge_agent.py repository <github_url> --output ./outputs")

except Exception as e:
    output.append(f"\n❌ TEST FAILED: {e}")
    import traceback
    output.append(traceback.format_exc())

# Write results
output_text = "\n".join(output)
print(output_text)

with open("test_results.txt", "w") as f:
    f.write(output_text)

print("\n📄 Results saved to: test_results.txt")
