#!/usr/bin/env python
"""
Command-line interface for Knowledge Agent POC

Extract structured knowledge from papers, talks, and repositories.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from agents import ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent
from src.core.schemas.base_schema import SourceType

# Aliases for cleaner code compatibility
PaperAgent = ModernPaperAgent
TalkAgent = ModernTalkAgent
RepositoryAgent = ModernRepositoryAgent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_paper(
    pdf_path: str,
    output_dir: str = "./outputs",
    llm_provider: str = "azure-openai",
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> None:
    """Extract knowledge from a research paper

    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save outputs
        llm_provider: LLM provider (azure-openai, openai, or anthropic)
        model: Model name (uses environment defaults if not provided)
        temperature: LLM temperature
    """
    logger.info(f"Extracting knowledge from paper: {pdf_path}")

    try:
        agent = PaperAgent(
            llm_provider=llm_provider,
            model=model,
            temperature=temperature,
        )

        artifact = agent.extract(pdf_path)

        # Save outputs
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        json_file = agent.save_artifact(artifact, str(output_path))
        summary_file = agent.save_summary(artifact, str(output_path))

        logger.info(f"✓ Extraction complete")
        logger.info(f"  JSON artifact: {json_file}")
        logger.info(f"  Summary: {summary_file}")

    except Exception as e:
        logger.error(f"Failed to extract paper: {e}")
        sys.exit(1)


def extract_talk(
    transcript_path: str,
    output_dir: str = "./outputs",
    llm_provider: str = "azure-openai",
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> None:
    """Extract knowledge from a talk transcript

    Args:
        transcript_path: Path to transcript file or raw transcript text
        output_dir: Directory to save outputs
        llm_provider: LLM provider (azure-openai, openai, or anthropic)
        model: Model name (uses environment defaults if not provided)
        temperature: LLM temperature
    """
    logger.info(f"Extracting knowledge from talk: {transcript_path}")

    try:
        agent = TalkAgent(
            llm_provider=llm_provider,
            model=model,
            temperature=temperature,
        )

        artifact = agent.extract(transcript_path)

        # Save outputs
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        json_file = agent.save_artifact(artifact, str(output_path))
        summary_file = agent.save_summary(artifact, str(output_path))

        logger.info(f"✓ Extraction complete")
        logger.info(f"  JSON artifact: {json_file}")
        logger.info(f"  Summary: {summary_file}")

    except Exception as e:
        logger.error(f"Failed to extract talk: {e}")
        sys.exit(1)


def extract_repository(
    repo_input: str,
    output_dir: str = "./outputs",
    llm_provider: str = "azure-openai",
    model: Optional[str] = None,
    temperature: float = 0.3,
) -> None:
    """Extract knowledge from a repository

    Args:
        repo_input: GitHub URL or local repository path
        output_dir: Directory to save outputs
        llm_provider: LLM provider (azure-openai, openai, or anthropic)
        model: Model name (uses environment defaults if not provided)
        temperature: LLM temperature
    """
    logger.info(f"Extracting knowledge from repository: {repo_input}")

    try:
        agent = RepositoryAgent(
            llm_provider=llm_provider,
            model=model,
            temperature=temperature,
        )

        artifact = agent.extract(repo_input)

        # Save outputs
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        json_file = agent.save_artifact(artifact, str(output_path))
        summary_file = agent.save_summary(artifact, str(output_path))

        logger.info(f"✓ Extraction complete")
        logger.info(f"  JSON artifact: {json_file}")
        logger.info(f"  Summary: {summary_file}")

    except Exception as e:
        logger.error(f"Failed to extract repository: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Extract structured knowledge from research artifacts"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Paper extraction command
    paper_parser = subparsers.add_parser("paper", help="Extract knowledge from a paper")
    paper_parser.add_argument("pdf", help="Path to PDF file")
    paper_parser.add_argument(
        "--output", "-o", default="./outputs",
        help="Output directory (default: ./outputs)"
    )
    paper_parser.add_argument(
        "--provider", "-p", default="azure-openai",
        help="LLM provider: azure-openai, openai, anthropic (default: azure-openai)"
    )
    paper_parser.add_argument(
        "--model", "-m", default=None,
        help="Model name (uses environment defaults if not specified)"
    )
    paper_parser.add_argument(
        "--temperature", "-t", type=float, default=0.3,
        help="LLM temperature (default: 0.3)"
    )
    paper_parser.set_defaults(func=extract_paper)

    # Talk extraction command
    talk_parser = subparsers.add_parser("talk", help="Extract knowledge from a talk")
    talk_parser.add_argument("transcript", help="Path to transcript file or raw text")
    talk_parser.add_argument(
        "--output", "-o", default="./outputs",
        help="Output directory (default: ./outputs)"
    )
    talk_parser.add_argument(
        "--provider", "-p", default="azure-openai",
        help="LLM provider: azure-openai, openai, anthropic (default: azure-openai)"
    )
    talk_parser.add_argument(
        "--model", "-m", default=None,
        help="Model name (uses environment defaults if not specified)"
    )
    talk_parser.add_argument(
        "--temperature", "-t", type=float, default=0.3,
        help="LLM temperature (default: 0.3)"
    )
    talk_parser.set_defaults(func=extract_talk)

    # Repository extraction command
    repo_parser = subparsers.add_parser("repository", help="Extract knowledge from a repository")
    repo_parser.add_argument("repo", help="GitHub URL or local repository path")
    repo_parser.add_argument(
        "--output", "-o", default="./outputs",
        help="Output directory (default: ./outputs)"
    )
    repo_parser.add_argument(
        "--provider", "-p", default="azure-openai",
        help="LLM provider: azure-openai, openai, anthropic (default: azure-openai)"
    )
    repo_parser.add_argument(
        "--model", "-m", default=None,
        help="Model name (uses environment defaults if not specified)"
    )
    repo_parser.add_argument(
        "--temperature", "-t", type=float, default=0.3,
        help="LLM temperature (default: 0.3)"
    )
    repo_parser.set_defaults(func=extract_repository)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Call appropriate function
    if args.command == "paper":
        args.func(args.pdf, args.output, args.provider, args.model, args.temperature)
    elif args.command == "talk":
        args.func(args.transcript, args.output, args.provider, args.model, args.temperature)
    elif args.command == "repository":
        args.func(args.repo, args.output, args.provider, args.model, args.temperature)


if __name__ == "__main__":
    main()
