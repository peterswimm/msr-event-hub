"""
Repository Knowledge Extraction Agent

Extracts structured knowledge from code/model repositories.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess

from ..core.schemas.base_schema import BaseKnowledgeArtifact, SourceType
from ..core.schemas.repository_schema import RepositoryKnowledgeArtifact
from .base_agent import BaseKnowledgeAgent
from ..prompts.repository_prompts import get_repository_prompts


logger = logging.getLogger(__name__)


class RepositoryAgent(BaseKnowledgeAgent):
    """Agent for extracting knowledge from code/model repositories"""

    def __init__(
        self,
        llm_provider: str = "azure-openai",
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 4000,
    ):
        """Initialize RepositoryAgent

        Args:
            llm_provider: LLM provider (azure-openai, openai, or anthropic)
            model: Model name (uses environment defaults if not provided)
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum tokens for LLM response
        """
        super().__init__(
            source_type=SourceType.REPOSITORY,
            llm_provider=llm_provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info(f"Initialized RepositoryAgent with provider={llm_provider}, model={model}")

    def get_prompts(self) -> Dict[str, str]:
        """Get repository extraction prompts"""
        return get_repository_prompts()

    def extract_from_source(self, source_input: str) -> str:
        """Extract information from repository

        Args:
            source_input: Either GitHub URL or local repository path

        Returns:
            Extracted repository information as text
        """
        repo_info = ""

        # Handle GitHub URLs
        if source_input.startswith(("http://", "https://")):
            logger.info(f"Processing GitHub URL: {source_input}")
            repo_info = self._extract_from_github_url(source_input)
        else:
            # Handle local repository
            logger.info(f"Processing local repository: {source_input}")
            repo_info = self._extract_from_local_repo(source_input)

        logger.info(f"Successfully extracted repository info: {len(repo_info)} characters")
        return repo_info

    def _extract_from_github_url(self, url: str) -> str:
        """Extract repository information from GitHub URL

        Args:
            url: GitHub URL

        Returns:
            Repository information as text
        """
        info = f"GitHub Repository: {url}\n\n"

        # Parse GitHub URL
        parts = url.rstrip('/').split('/')
        if len(parts) >= 5:
            owner = parts[-2]
            repo = parts[-1]
            repo_api_url = f"https://api.github.com/repos/{owner}/{repo}"

            try:
                import requests

                # Fetch repository metadata
                logger.debug(f"Fetching GitHub API: {repo_api_url}")
                response = requests.get(repo_api_url, timeout=10)
                response.raise_for_status()
                repo_data = response.json()

                info += "=== Repository Metadata ===\n"
                info += f"Name: {repo_data.get('name', 'Unknown')}\n"
                info += f"Description: {repo_data.get('description', 'No description')}\n"
                info += f"Language: {repo_data.get('language', 'Unknown')}\n"
                info += f"Stars: {repo_data.get('stargazers_count', 0)}\n"
                info += f"Forks: {repo_data.get('forks_count', 0)}\n"
                info += f"Issues: {repo_data.get('open_issues_count', 0)}\n"
                info += f"License: {repo_data.get('license', {}).get('name', 'Unknown')}\n"
                info += f"Last Updated: {repo_data.get('updated_at', 'Unknown')}\n"
                info += f"Topics: {', '.join(repo_data.get('topics', []))}\n"

                # Try to fetch README
                info += "\n=== README Content ===\n"
                try:
                    readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
                    readme_response = requests.get(readme_url, timeout=10)
                    if readme_response.status_code == 200:
                        info += readme_response.text[:5000]  # Limit to 5000 chars
                    else:
                        # Try master branch
                        readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
                        readme_response = requests.get(readme_url, timeout=10)
                        if readme_response.status_code == 200:
                            info += readme_response.text[:5000]
                        else:
                            info += "[README not found]\n"
                except Exception as e:
                    logger.warning(f"Failed to fetch README: {e}")
                    info += f"[Failed to fetch README: {e}]\n"

            except Exception as e:
                logger.warning(f"Failed to fetch GitHub metadata: {e}")
                info += f"[Failed to fetch metadata: {e}]\n"

        return info

    def _extract_from_local_repo(self, repo_path: str) -> str:
        """Extract repository information from local repository

        Args:
            repo_path: Local repository path

        Returns:
            Repository information as text
        """
        repo_dir = Path(repo_path)

        if not repo_dir.exists():
            raise FileNotFoundError(f"Repository not found: {repo_path}")

        info = f"Local Repository: {repo_path}\n\n"

        # Extract README
        readme_files = list(repo_dir.glob("README*")) + list(repo_dir.glob("readme*"))
        if readme_files:
            logger.info(f"Found README: {readme_files[0]}")
            try:
                with open(readme_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    info += f"=== {readme_files[0].name} ===\n"
                    info += content[:5000] + "\n\n"
            except Exception as e:
                logger.warning(f"Failed to read README: {e}")

        # Extract package.json or setup.py or pyproject.toml
        package_files = [
            repo_dir / "package.json",
            repo_dir / "setup.py",
            repo_dir / "pyproject.toml",
            repo_dir / "Cargo.toml",
            repo_dir / "pom.xml",
        ]

        for pkg_file in package_files:
            if pkg_file.exists():
                logger.info(f"Found package file: {pkg_file.name}")
                try:
                    with open(pkg_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        info += f"=== {pkg_file.name} ===\n"
                        info += content[:3000] + "\n\n"
                except Exception as e:
                    logger.warning(f"Failed to read {pkg_file.name}: {e}")

        # Extract requirements files
        req_files = list(repo_dir.glob("requirements*.txt")) + \
                   list(repo_dir.glob("*requirements*.txt"))

        for req_file in req_files:
            if req_file.is_file():
                logger.info(f"Found requirements file: {req_file.name}")
                try:
                    with open(req_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        info += f"=== {req_file.name} ===\n"
                        info += content[:2000] + "\n\n"
                except Exception as e:
                    logger.warning(f"Failed to read {req_file.name}: {e}")

        # List directory structure
        info += "=== Directory Structure ===\n"
        try:
            structure = self._get_directory_structure(repo_dir, max_depth=2)
            info += structure + "\n"
        except Exception as e:
            logger.warning(f"Failed to get directory structure: {e}")

        return info\n\n    def _get_directory_structure(self, path: Path, prefix: str = "", max_depth: int = 2, current_depth: int = 0) -> str:
        """Get directory structure as text

        Args:
            path: Directory path
            prefix: Prefix for tree display
            max_depth: Maximum depth to traverse
            current_depth: Current depth in traversal

        Returns:
            Directory structure as text
        """
        if current_depth >= max_depth:
            return ""

        items = []
        try:
            for item in sorted(path.iterdir()):
                if item.name.startswith('.'):
                    continue
                if item.is_dir():
                    items.append(f"{prefix}{item.name}/")
                    if current_depth < max_depth - 1:
                        items.append(self._get_directory_structure(
                            item, f"{prefix}  ", max_depth, current_depth + 1
                        ))
                else:
                    items.append(f"{prefix}{item.name}")
        except PermissionError:
            pass

        return "\n".join(filter(None, items))\n\n    def parse_extraction_output(self, llm_response: str) -> BaseKnowledgeArtifact:
        """Parse LLM response into RepositoryKnowledgeArtifact

        Args:
            llm_response: LLM response with JSON extraction

        Returns:
            BaseKnowledgeArtifact with combined base and repository-specific fields
        """
        logger.info("Parsing repository extraction output from LLM")

        try:
            # Extract JSON from response
            response_text = llm_response.strip()

            # Try to find JSON block in response
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end == -1:
                    end = len(response_text)
                json_text = response_text[start:end]
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end == -1:
                    end = len(response_text)
                json_text = response_text[start:end]
            else:
                json_text = response_text

            extraction_data = json.loads(json_text.strip())
            logger.info(f"Successfully parsed JSON extraction: {extraction_data.get('title', 'Unknown')}")

            # Extract base fields
            base_artifact = BaseKnowledgeArtifact(
                source_type=SourceType.REPOSITORY,
                title=extraction_data.get("title", "Unknown Repository"),
                contributors=extraction_data.get("contributors", []),
                plain_language_overview=extraction_data.get("plain_language_overview", ""),
                technical_problem_addressed=extraction_data.get("technical_problem_addressed", ""),
                key_methods_approach=extraction_data.get("key_methods_approach", ""),
                primary_claims_capabilities=extraction_data.get("primary_claims_capabilities", []),
                novelty_vs_prior_work=extraction_data.get("novelty_vs_prior_work", ""),
                limitations_constraints=extraction_data.get("limitations_constraints", []),
                potential_impact=extraction_data.get("potential_impact", ""),
                open_questions_future_work=extraction_data.get("open_questions_future_work", []),
                key_evidence_citations=extraction_data.get("key_evidence_citations", []),
                confidence_score=float(extraction_data.get("confidence_score", 0.5)),
                confidence_reasoning=extraction_data.get("confidence_reasoning", ""),
                agent_name="RepositoryAgent",
            )

            # Extract repository-specific fields
            repo_data = extraction_data.get("repository_specific", {})

            repo_artifact = RepositoryKnowledgeArtifact(
                artifact_type=repo_data.get("artifact_type", "framework"),
                primary_purpose=repo_data.get("primary_purpose"),
                intended_users=repo_data.get("intended_users", "developers"),
                primary_languages=repo_data.get("primary_languages", []),
                key_frameworks=repo_data.get("key_frameworks", []),
                supported_platforms=repo_data.get("supported_platforms", []),
                hardware_dependencies=repo_data.get("hardware_dependencies"),
                installation_complexity=repo_data.get("installation_complexity", "medium"),
                setup_prerequisites=repo_data.get("setup_prerequisites", []),
                training_environment=repo_data.get("training_environment"),
                inference_environment=repo_data.get("inference_environment"),
                runtime_dependencies=repo_data.get("runtime_dependencies", []),
                example_use_cases=repo_data.get("example_use_cases", []),
                api_surface_summary=repo_data.get("api_surface_summary"),
                model_or_system_limitations=repo_data.get("model_or_system_limitations", []),
                maintenance_status=repo_data.get("maintenance_status", "active"),
                license=repo_data.get("license"),
                data_usage_constraints=repo_data.get("data_usage_constraints"),
            )

            # Store repository-specific data in additional_knowledge
            base_artifact.additional_knowledge.update({
                "repository_specific": {
                    "artifact_type": repo_artifact.artifact_type,
                    "primary_purpose": repo_artifact.primary_purpose,
                    "intended_users": repo_artifact.intended_users,
                    "primary_languages": repo_artifact.primary_languages,
                    "key_frameworks": repo_artifact.key_frameworks,
                    "supported_platforms": repo_artifact.supported_platforms,
                    "hardware_dependencies": repo_artifact.hardware_dependencies,
                    "installation_complexity": repo_artifact.installation_complexity,
                    "setup_prerequisites": repo_artifact.setup_prerequisites,
                    "training_environment": repo_artifact.training_environment,
                    "inference_environment": repo_artifact.inference_environment,
                    "runtime_dependencies": repo_artifact.runtime_dependencies,
                    "example_use_cases": repo_artifact.example_use_cases,
                    "api_surface_summary": repo_artifact.api_surface_summary,
                    "model_or_system_limitations": repo_artifact.model_or_system_limitations,
                    "maintenance_status": repo_artifact.maintenance_status,
                    "license": repo_artifact.license,
                    "data_usage_constraints": repo_artifact.data_usage_constraints,
                }
            })

            return base_artifact

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON extraction: {e}")
            raise ValueError(f"Invalid JSON in LLM response: {e}") from e
        except Exception as e:
            logger.error(f"Error parsing extraction output: {e}")
            raise\n
