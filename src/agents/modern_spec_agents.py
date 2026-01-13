"""
POC Specification-Aligned Agent Implementations

Modern Agent Framework implementations of specialized extraction agents
that use the spec-aligned prompts for comprehensive knowledge extraction.
"""

import json
from pathlib import Path
from typing import Union

from agent_framework import OpenAIChatClient, Agent, StreamableHTTPClient
from src.agents.prompts.spec_prompts import (
    get_paper_prompt,
    get_talk_prompt,
    get_repository_prompt
)
from src.core.schemas.paper_schema import PaperKnowledgeArtifact
from src.core.schemas.talk_schema import TalkKnowledgeArtifact
from src.core.schemas.repository_schema import RepositoryKnowledgeArtifact
from src.config.settings import Settings


class ModernPaperAgent:
    """
    Modern paper extraction agent using Agent Framework.
    Uses spec-aligned prompts for comprehensive extraction.
    """
    
    def __init__(self, settings: Settings = None):
        """Initialize paper agent with Agent Framework."""
        self.settings = settings or Settings()
        
        # Create client
        self.client = OpenAIChatClient(
            model=self.settings.agent_model,
            azure_endpoint=self.settings.foundry_project_endpoint,
            api_version=self.settings.foundry_api_version
        )
        
        # Create agent with spec-aligned instructions
        self.agent = Agent(
            name="PaperExtractionAgent",
            client=self.client,
            instructions=get_paper_prompt()
        )
    
    async def extract(
        self,
        paper_content: Union[str, bytes, Path]
    ) -> PaperKnowledgeArtifact:
        """
        Extract knowledge from research paper.
        
        Args:
            paper_content: Paper content (text, PDF bytes, or file path)
            
        Returns:
            Structured paper knowledge artifact
        """
        # Prepare content
        if isinstance(paper_content, Path):
            with open(paper_content, "rb") as f:
                content = f.read()
        elif isinstance(paper_content, bytes):
            content = paper_content
        else:
            content = paper_content
        
        # Run extraction
        result = await self.agent.run(
            f"Extract knowledge from this research paper:\n\n{content}"
        )
        
        # Parse JSON result
        extracted_data = json.loads(result.content)
        
        # Convert to PaperKnowledgeArtifact
        # In production, would use proper Pydantic validation
        artifact = PaperKnowledgeArtifact(**extracted_data)
        
        return artifact


class ModernTalkAgent:
    """
    Modern talk/transcript extraction agent using Agent Framework.
    Uses spec-aligned prompts for comprehensive extraction.
    """
    
    def __init__(self, settings: Settings = None):
        """Initialize talk agent with Agent Framework."""
        self.settings = settings or Settings()
        
        self.client = OpenAIChatClient(
            model=self.settings.agent_model,
            azure_endpoint=self.settings.foundry_project_endpoint,
            api_version=self.settings.foundry_api_version
        )
        
        self.agent = Agent(
            name="TalkExtractionAgent",
            client=self.client,
            instructions=get_talk_prompt()
        )
    
    async def extract(
        self,
        transcript_content: Union[str, Path]
    ) -> TalkKnowledgeArtifact:
        """
        Extract knowledge from talk transcript.
        
        Args:
            transcript_content: Transcript text or file path
            
        Returns:
            Structured talk knowledge artifact
        """
        # Prepare content
        if isinstance(transcript_content, Path):
            with open(transcript_content, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = transcript_content
        
        # Run extraction
        result = await self.agent.run(
            f"Extract knowledge from this research talk transcript:\n\n{content}"
        )
        
        # Parse JSON result
        extracted_data = json.loads(result.content)
        
        # Convert to TalkKnowledgeArtifact
        artifact = TalkKnowledgeArtifact(**extracted_data)
        
        return artifact


class ModernRepositoryAgent:
    """
    Modern repository extraction agent using Agent Framework.
    Uses spec-aligned prompts for comprehensive extraction.
    """
    
    def __init__(self, settings: Settings = None):
        """Initialize repository agent with Agent Framework."""
        self.settings = settings or Settings()
        
        self.client = OpenAIChatClient(
            model=self.settings.agent_model,
            azure_endpoint=self.settings.foundry_project_endpoint,
            api_version=self.settings.foundry_api_version
        )
        
        # Repository agent can use MCP tools for enhanced code analysis
        self.agent = Agent(
            name="RepositoryExtractionAgent",
            client=self.client,
            instructions=get_repository_prompt()
        )
    
    async def extract(
        self,
        repo_path: Union[str, Path]
    ) -> RepositoryKnowledgeArtifact:
        """
        Extract knowledge from code/model repository.
        
        Args:
            repo_path: Path to repository directory
            
        Returns:
            Structured repository knowledge artifact
        """
        repo_path = Path(repo_path)
        
        # Collect repository information
        repo_info = self._collect_repo_info(repo_path)
        
        # Run extraction
        result = await self.agent.run(
            f"Extract knowledge from this repository:\n\n{json.dumps(repo_info, indent=2)}"
        )
        
        # Parse JSON result
        extracted_data = json.loads(result.content)
        
        # Convert to RepositoryKnowledgeArtifact
        artifact = RepositoryKnowledgeArtifact(**extracted_data)
        
        return artifact
    
    def _collect_repo_info(self, repo_path: Path) -> dict:
        """
        Collect repository information for extraction.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dictionary with repository metadata and content
        """
        info = {
            "name": repo_path.name,
            "path": str(repo_path)
        }
        
        # Collect README
        readme_files = ["README.md", "README.txt", "README"]
        for readme_name in readme_files:
            readme_path = repo_path / readme_name
            if readme_path.exists():
                with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                    info["readme"] = f.read()
                break
        
        # Collect requirements/dependencies
        req_files = ["requirements.txt", "pyproject.toml", "package.json", "Cargo.toml"]
        info["dependencies"] = {}
        for req_file in req_files:
            req_path = repo_path / req_file
            if req_path.exists():
                with open(req_path, "r", encoding="utf-8", errors="ignore") as f:
                    info["dependencies"][req_file] = f.read()
        
        # Collect file structure
        info["file_structure"] = []
        try:
            for item in repo_path.rglob("*"):
                if item.is_file() and not any(
                    part.startswith(".") for part in item.parts
                ):
                    rel_path = item.relative_to(repo_path)
                    info["file_structure"].append(str(rel_path))
        except Exception:
            pass
        
        # Limit to first 100 files
        info["file_structure"] = info["file_structure"][:100]
        
        return info


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def extract_paper(paper_path: Union[str, Path]) -> PaperKnowledgeArtifact:
    """Convenience function to extract from a paper."""
    agent = ModernPaperAgent()
    return await agent.extract(paper_path)


async def extract_talk(transcript_path: Union[str, Path]) -> TalkKnowledgeArtifact:
    """Convenience function to extract from a talk transcript."""
    agent = ModernTalkAgent()
    return await agent.extract(transcript_path)


async def extract_repository(repo_path: Union[str, Path]) -> RepositoryKnowledgeArtifact:
    """Convenience function to extract from a repository."""
    agent = ModernRepositoryAgent()
    return await agent.extract(repo_path)
