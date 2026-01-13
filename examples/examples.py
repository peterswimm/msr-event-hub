"""
Usage Examples for Knowledge Agent POC

Demonstrates how to use the extraction agents for papers, talks, and repositories.
"""

from agents import PaperAgent, TalkAgent, RepositoryAgent
from pathlib import Path


def example_extract_paper():
    """Example: Extract knowledge from a research paper"""

    # Initialize the agent
    agent = PaperAgent(
        llm_provider="azure-openai",
        # model="gpt-4-turbo",  # Optional: specify model
        temperature=0.3,  # Lower = more deterministic
        max_tokens=4000,
    )

    # Extract from a PDF file
    pdf_path = "path/to/paper.pdf"
    artifact = agent.extract(pdf_path)

    # Access extracted knowledge
    print(f"Title: {artifact.title}")
    print(f"Contributors: {artifact.contributors}")
    print(f"Overview: {artifact.plain_language_overview}")
    print(f"Confidence: {artifact.confidence_score}")

    # Save outputs
    output_dir = "./outputs/papers"
    json_file = agent.save_artifact(artifact, output_dir)
    summary_file = agent.save_summary(artifact, output_dir)

    print(f"Saved to: {json_file}, {summary_file}")


def example_extract_talk():
    """Example: Extract knowledge from a research talk"""

    # Initialize the agent
    agent = TalkAgent(
        llm_provider="openai",  # Using OpenAI instead
        # model="gpt-4",
        temperature=0.3,
    )

    # Extract from a transcript file
    transcript_path = "path/to/transcript.txt"
    artifact = agent.extract(transcript_path)

    # Access extracted knowledge
    print(f"Title: {artifact.title}")
    print(f"Speakers: {artifact.contributors}")
    print(f"Problem: {artifact.technical_problem_addressed}")

    # Access talk-specific information
    talk_info = artifact.additional_knowledge.get("talk_specific", {})
    print(f"Talk Type: {talk_info.get('talk_type')}")
    print(f"Duration: {talk_info.get('duration_minutes')} minutes")
    print(f"Demo Included: {talk_info.get('demo_included')}")

    # Save outputs
    output_dir = "./outputs/talks"
    json_file = agent.save_artifact(artifact, output_dir)
    summary_file = agent.save_summary(artifact, output_dir)


def example_extract_repository():
    """Example: Extract knowledge from a code repository"""

    # Initialize the agent
    agent = RepositoryAgent(
        llm_provider="anthropic",  # Using Anthropic Claude
        # model="claude-3-sonnet-20240229",
        temperature=0.3,
    )

    # Extract from GitHub URL
    repo_url = "https://github.com/owner/repo"
    artifact = agent.extract(repo_url)

    # Access extracted knowledge
    print(f"Repository: {artifact.title}")
    print(f"Overview: {artifact.plain_language_overview}")
    print(f"Primary Capabilities: {artifact.primary_claims_capabilities}")

    # Access repository-specific information
    repo_info = artifact.additional_knowledge.get("repository_specific", {})
    print(f"Languages: {repo_info.get('primary_languages')}")
    print(f"Frameworks: {repo_info.get('key_frameworks')}")
    print(f"License: {repo_info.get('license')}")
    print(f"Maintenance Status: {repo_info.get('maintenance_status')}")

    # Save outputs
    output_dir = "./outputs/repositories"
    json_file = agent.save_artifact(artifact, output_dir)
    summary_file = agent.save_summary(artifact, output_dir)


def example_batch_extraction():
    """Example: Extract knowledge from multiple artifacts"""

    papers = [
        "papers/paper1.pdf",
        "papers/paper2.pdf",
        "papers/paper3.pdf",
    ]

    paper_agent = PaperAgent()
    results = []

    for paper_path in papers:
        try:
            artifact = paper_agent.extract(paper_path)
            results.append({
                "title": artifact.title,
                "confidence": artifact.confidence_score,
                "impact": artifact.potential_impact,
            })

            # Save individually
            paper_agent.save_artifact(artifact, "./outputs/papers")

        except Exception as e:
            print(f"Failed to extract {paper_path}: {e}")

    # Summary of extractions
    print(f"\nExtracted {len(results)} papers")
    for result in results:
        print(f"  - {result['title']} (confidence: {result['confidence']})")


def example_custom_llm_provider():
    """Example: Using custom LLM provider configuration"""

    # Azure OpenAI (requires AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT)
    azure_agent = PaperAgent(
        llm_provider="azure-openai",
        model="gpt-4-turbo",  # Must match Azure deployment name
        temperature=0.2,
        max_tokens=3000,
    )

    # OpenAI (requires OPENAI_API_KEY)
    openai_agent = PaperAgent(
        llm_provider="openai",
        model="gpt-4-turbo-preview",
        temperature=0.3,
    )

    # Anthropic Claude (requires ANTHROPIC_API_KEY)
    anthropic_agent = PaperAgent(
        llm_provider="anthropic",
        model="claude-3-opus-20240229",
        temperature=0.2,
    )

    # All use the same extract() API
    # artifact = agent.extract("path/to/paper.pdf")


def example_error_handling():
    """Example: Proper error handling during extraction"""

    agent = PaperAgent()

    # Handle file not found
    try:
        artifact = agent.extract("nonexistent.pdf")
    except FileNotFoundError as e:
        print(f"File error: {e}")

    # Handle LLM errors
    try:
        artifact = agent.extract("valid_paper.pdf")
    except ValueError as e:
        print(f"Extraction error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def example_access_raw_json():
    """Example: Access raw JSON artifact structure"""
    import json

    agent = PaperAgent()
    artifact = agent.extract("paper.pdf")

    # Convert to JSON for inspection
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
        "additional_knowledge": artifact.additional_knowledge,
    }

    print(json.dumps(artifact_dict, indent=2))


if __name__ == "__main__":
    # Uncomment examples to run:

    # example_extract_paper()
    # example_extract_talk()
    # example_extract_repository()
    # example_batch_extraction()
    # example_custom_llm_provider()
    # example_error_handling()
    # example_access_raw_json()

    print("Examples ready. Uncomment to run.")
