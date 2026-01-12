#!/usr/bin/env python
"""
Simple validation that all imports work correctly
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test all package imports"""

    logger.info("Testing imports...")

    try:
        logger.info("  - Importing schemas...")
        from core.schemas import BaseKnowledgeArtifact, SourceType, ResearchMaturityStage
        logger.info("    ✓ BaseKnowledgeArtifact imported")

        logger.info("  - Importing agents...")
        from agents import BaseKnowledgeAgent, PaperAgent, TalkAgent, RepositoryAgent
        logger.info("    ✓ BaseKnowledgeAgent imported")
        logger.info("    ✓ PaperAgent imported")
        logger.info("    ✓ TalkAgent imported")
        logger.info("    ✓ RepositoryAgent imported")

        logger.info("  - Importing prompts...")
        from prompts import get_paper_prompts, get_talk_prompts, get_repository_prompts
        logger.info("    ✓ get_paper_prompts imported")
        logger.info("    ✓ get_talk_prompts imported")
        logger.info("    ✓ get_repository_prompts imported")

        # Verify prompt functions work
        paper_prompts = get_paper_prompts()
        talk_prompts = get_talk_prompts()
        repo_prompts = get_repository_prompts()

        logger.info("    ✓ Prompts retrieved successfully")

        # Check schema instantiation
        artifact = BaseKnowledgeArtifact(
            source_type=SourceType.PAPER,
            title="Test Artifact",
        )
        logger.info("    ✓ BaseKnowledgeArtifact instantiated")

        logger.info("\n✅ All imports successful!")
        return True

    except Exception as e:
        logger.error(f"❌ Import failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
