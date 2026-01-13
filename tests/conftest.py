"""
Pytest configuration and shared fixtures for Knowledge Agent tests.
"""

import pytest
from pathlib import Path
import json
from datetime import datetime


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_paper_path(fixtures_dir):
    """Return path to sample paper PDF."""
    paper_path = fixtures_dir / "sample_paper.pdf"
    # Create a minimal PDF file for testing
    if not paper_path.exists():
        # Create a very basic PDF for testing (won't be parseable but valid structure)
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
5 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Sample Research Paper) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000264 00000 n 
0000000352 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
445
%%EOF"""
        paper_path.write_bytes(pdf_content)
    return paper_path


@pytest.fixture
def sample_transcript_path(fixtures_dir):
    """Return path to sample transcript file."""
    transcript_path = fixtures_dir / "sample_transcript.txt"
    if not transcript_path.exists():
        content = """Transcript: "Building Knowledge Extraction Systems with AI"

Speaker: Dr. Alice Chen
Date: January 2026
Duration: 45 minutes

[00:00] Introduction
Today we're going to talk about building knowledge extraction systems using modern AI techniques.
The problem we're solving is extracting structured knowledge from unstructured research artifacts.

[05:00] The Challenge
Research papers, talks, and code repositories contain valuable knowledge that's locked in unstructured formats.
Current approaches require manual curation, which doesn't scale.

[10:00] Our Approach
We developed a multi-agent system that can extract knowledge from three types of artifacts:
1. Research papers (PDFs)
2. Research talks (transcripts)
3. Code repositories (GitHub)

[15:00] Technical Details
The system uses language models with specialized prompts for each artifact type.
Each agent produces a standardized JSON output with 12 baseline knowledge fields.

[20:00] Results
In our pilot, we extracted knowledge from 100 artifacts with an average quality score of 3.8/5.0.
The system handles edge cases like incomplete papers and non-English transcripts.

[30:00] Challenges
One major challenge was prompt engineering - getting the LLM to extract the right information.
Another was handling PDFs that couldn't be parsed due to image-based content.

[40:00] Future Work
We plan to add support for blog posts, video transcripts, and internal documentation.
We're also exploring knowledge graph integration to link findings across artifacts.

[45:00] Q&A
Questions from the audience about implementation details and deployment.
"""
        transcript_path.write_text(content)
    return transcript_path


@pytest.fixture
def sample_repo_info():
    """Return sample repository metadata."""
    return {
        "url": "https://github.com/example/knowledge-extraction",
        "name": "knowledge-extraction",
        "description": "AI-powered knowledge extraction from research artifacts",
        "language": "Python",
        "stars": 150,
        "topics": ["ai", "knowledge-extraction", "nlp"],
    }


@pytest.fixture
def sample_paper_artifact():
    """Return sample PaperKnowledgeArtifact for testing."""
    from src.core.schemas.paper_schema import PaperKnowledgeArtifact
    
    return PaperKnowledgeArtifact(
        id="test-paper-001",
        title="Building Knowledge Extraction Systems",
        contributors=["Alice Chen", "Bob Smith"],
        plain_language_overview="This paper presents a system for extracting structured knowledge from research artifacts.",
        technical_problem_addressed="Automatic extraction of knowledge from unstructured research documents",
        key_methods_approach="Multi-agent system with specialized LLM prompts for each artifact type",
        primary_claims_capabilities="Can extract 12 baseline knowledge fields with 0.85 average accuracy",
        novelty_vs_prior_work="Improves on prior work by handling multiple artifact types in a unified framework",
        limitations_constraints="Limited to English documents, requires high-quality PDFs",
        potential_impact="Could enable large-scale knowledge graph construction from research literature",
        open_questions_future_work="How to handle non-English documents, multimodal content integration",
        key_evidence_citations="Evaluated on 100 research papers with manual expert validation",
        confidence_score=0.85,
        confidence_reasoning="High confidence based on consistent extraction patterns and expert validation",
        source_type="paper",
        agent_name="ModernPaperAgent",
        extraction_model="gpt-4",
        extraction_date=datetime.now(),
        provenance={
            "source_file": "test-paper.pdf",
            "extraction_timestamp": datetime.now().isoformat(),
            "model_version": "gpt-4",
        },
        additional_knowledge={
            "publication_venue": "ACL 2026",
            "publication_year": 2026,
            "peer_review_status": "accepted",
            "datasets_used": ["Paper100", "ResearchArtifacts"],
            "evaluation_metrics": ["precision", "recall", "f1"],
            "key_results": {"accuracy": 0.85, "coverage": 0.92},
            "influential_prior_work": ["BERT", "GPT-3"],
            "reproducibility_notes": "Code available at GitHub link in paper",
        },
    )


@pytest.fixture
def sample_talk_artifact():
    """Return sample TalkKnowledgeArtifact for testing."""
    from src.core.schemas.talk_schema import TalkKnowledgeArtifact
    
    return TalkKnowledgeArtifact(
        id="test-talk-001",
        title="Building Knowledge Extraction Systems with AI",
        contributors=["Dr. Alice Chen"],
        plain_language_overview="A talk about extracting knowledge from research artifacts using AI.",
        technical_problem_addressed="Unstructured knowledge in research materials",
        key_methods_approach="Multi-agent LLM-based system with specialized prompts",
        primary_claims_capabilities="Can extract structured knowledge with 85% accuracy",
        novelty_vs_prior_work="Unified framework for multiple artifact types",
        limitations_constraints="English-only, requires good document quality",
        potential_impact="Enable knowledge graph construction at scale",
        open_questions_future_work="Multilingual support, knowledge linking",
        key_evidence_citations="100 artifacts evaluated with expert review",
        confidence_score=0.82,
        confidence_reasoning="Based on talk transcript and Q&A validation",
        source_type="talk",
        agent_name="ModernTalkAgent",
        extraction_model="gpt-4",
        extraction_date=datetime.now(),
        provenance={
            "source_file": "transcript.txt",
            "extraction_timestamp": datetime.now().isoformat(),
            "model_version": "gpt-4",
        },
        additional_knowledge={
            "talk_type": "conference",
            "duration_minutes": 45,
            "sections": ["Introduction", "Challenge", "Approach", "Results", "Future Work"],
            "key_segments": {
                "problem_statement": "00:05-00:10",
                "solution_overview": "00:15-00:25",
                "results_discussion": "00:25-00:35",
            },
            "demo_included": False,
            "experimental_results_discussed": ["accuracy: 0.85", "coverage: 0.92"],
            "technical_challenges_mentioned": ["PDF parsing", "prompt engineering"],
            "open_risks": ["Hallucination in LLM outputs"],
            "pending_experiments": ["Multilingual support", "Knowledge graph integration"],
        },
    )


@pytest.fixture
def sample_repository_artifact():
    """Return sample RepositoryKnowledgeArtifact for testing."""
    from src.core.schemas.repository_schema import RepositoryKnowledgeArtifact
    
    return RepositoryKnowledgeArtifact(
        id="test-repo-001",
        title="knowledge-extraction",
        contributors=["Alice Chen", "Bob Smith", "Carol Davis"],
        plain_language_overview="A Python library for extracting structured knowledge from research artifacts.",
        technical_problem_addressed="Automated knowledge extraction from unstructured documents",
        key_methods_approach="Multi-agent system using LLMs with specialized prompts",
        primary_claims_capabilities="Extracts 12 knowledge fields from papers, talks, and repositories",
        novelty_vs_prior_work="First unified framework supporting multiple artifact types",
        limitations_constraints="Requires Python 3.10+, needs high-quality input documents",
        potential_impact="Enables large-scale knowledge graph construction",
        open_questions_future_work="Multilingual support, knowledge linking, custom sources",
        key_evidence_citations="150+ GitHub stars, 100 artifact evaluation study",
        confidence_score=0.88,
        confidence_reasoning="Well-maintained repo with extensive testing and documentation",
        source_type="repository",
        agent_name="ModernRepositoryAgent",
        extraction_model="gpt-4",
        extraction_date=datetime.now(),
        provenance={
            "source_url": "https://github.com/example/knowledge-extraction",
            "extraction_timestamp": datetime.now().isoformat(),
            "model_version": "gpt-4",
        },
        additional_knowledge={
            "artifact_classification": "library",
            "primary_languages": ["Python"],
            "key_frameworks": ["LangChain", "Pydantic"],
            "tech_stack": ["Python 3.10+", "async/await", "pytest"],
            "setup_requirements": ["pip install -r requirements.txt", "configure .env"],
            "key_apis": [
                "ModernPaperAgent.extract()",
                "ModernTalkAgent.extract()",
                "ModernRepositoryAgent.extract()",
            ],
            "maintenance_status": "actively maintained",
            "license": "MIT",
            "documentation_quality": "excellent",
            "test_coverage": "85%",
        },
    )


@pytest.fixture
def settings():
    """Return test settings."""
    from src.config.settings import Settings
    
    settings = Settings()
    # Override with test values if needed
    return settings
