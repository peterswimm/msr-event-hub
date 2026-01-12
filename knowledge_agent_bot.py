"""
Knowledge Agent - Conversational interface for knowledge extraction

This agent wraps the Knowledge Agent POC extraction capabilities
in a conversational interface suitable for testing in Bot Framework emulator.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from tempfile import NamedTemporaryFile

# Add knowledge-agent-poc to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from agents import ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent
from core.schemas import BaseKnowledgeArtifact
from core_interfaces import ExtractionPipeline

# Aliases for compatibility
PaperAgent = ModernPaperAgent
TalkAgent = ModernTalkAgent
RepositoryAgent = ModernRepositoryAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeExtractionAgent:
    """Conversational agent for knowledge extraction"""

    def __init__(
        self,
        default_llm_provider: str = "azure-openai",
        output_dir: str = "./outputs",
        enable_m365: bool = False,
        m365_connector: Optional[Any] = None
    ):
        """Initialize the knowledge extraction agent

        Args:
            default_llm_provider: Default LLM provider (azure-openai, openai, anthropic)
            output_dir: Directory to save extraction outputs
            enable_m365: Enable Microsoft 365 integration
            m365_connector: Optional M365KnowledgeConnector instance
        """
        self.default_llm_provider = default_llm_provider
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Track recent extractions
        self.extraction_history: List[Dict[str, Any]] = []

        # Microsoft 365 integration
        self.enable_m365 = enable_m365
        self.m365 = None
        if enable_m365:
            try:
                if m365_connector is None:
                    from integrations.m365_connector import create_connector
                    self.m365 = create_connector()
                else:
                    self.m365 = m365_connector
                logger.info("Microsoft 365 integration enabled")
            except Exception as e:
                logger.error(f"Failed to initialize M365 integration: {e}")
                self.enable_m365 = False

        logger.info(f"Initialized KnowledgeExtractionAgent with provider={default_llm_provider}, m365={enable_m365}")

    def extract_paper_knowledge(
        self,
        pdf_path: str,
        llm_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract knowledge from a research paper

        Args:
            pdf_path: Path to PDF file
            llm_provider: LLM provider to use (overrides default)

        Returns:
            Dict with extraction results
        """
        provider = llm_provider or self.default_llm_provider
        logger.info(f"Extracting knowledge from paper: {pdf_path}")

        try:
            # Validate file exists
            if not Path(pdf_path).exists():
                return {
                    "success": False,
                    "error": f"PDF file not found: {pdf_path}",
                    "suggestion": "Please provide a valid path to a PDF file"
                }

            # Initialize agent
            agent = PaperAgent(llm_provider=provider, temperature=0.3)

            # Extract knowledge
            artifact = agent.extract(pdf_path)

            # Save outputs
            json_file = agent.save_artifact(artifact, str(self.output_dir))
            summary_file = agent.save_summary(artifact, str(self.output_dir))

            # Format response
            result = {
                "success": True,
                "artifact_type": "paper",
                "title": artifact.title,
                "contributors": artifact.contributors,
                "overview": artifact.plain_language_overview,
                "confidence": artifact.confidence_score,
                "files": {
                    "json": json_file,
                    "summary": summary_file
                },
                "extraction_date": artifact.extraction_date.isoformat(),
                "full_artifact": self._artifact_to_dict(artifact)
            }

            # Add to history
            self.extraction_history.append({
                "type": "paper",
                "source": pdf_path,
                "timestamp": datetime.now().isoformat(),
                "title": artifact.title,
                "confidence": artifact.confidence_score
            })

            logger.info(f"Successfully extracted paper: {artifact.title}")
            return result

        except Exception as e:
            logger.error(f"Paper extraction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check the PDF file is valid and readable"
            }

    def extract_talk_knowledge(
        self,
        transcript_path: str,
        llm_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract knowledge from a talk transcript

        Args:
            transcript_path: Path to transcript file or raw text
            llm_provider: LLM provider to use (overrides default)

        Returns:
            Dict with extraction results
        """
        provider = llm_provider or self.default_llm_provider
        logger.info(f"Extracting knowledge from talk: {transcript_path}")

        try:
            # Initialize agent
            agent = TalkAgent(llm_provider=provider, temperature=0.3)

            # Extract knowledge
            artifact = agent.extract(transcript_path)

            # Save outputs
            json_file = agent.save_artifact(artifact, str(self.output_dir))
            summary_file = agent.save_summary(artifact, str(self.output_dir))

            # Format response
            result = {
                "success": True,
                "artifact_type": "talk",
                "title": artifact.title,
                "contributors": artifact.contributors,
                "overview": artifact.plain_language_overview,
                "confidence": artifact.confidence_score,
                "files": {
                    "json": json_file,
                    "summary": summary_file
                },
                "extraction_date": artifact.extraction_date.isoformat(),
                "full_artifact": self._artifact_to_dict(artifact)
            }

            # Add to history
            self.extraction_history.append({
                "type": "talk",
                "source": transcript_path,
                "timestamp": datetime.now().isoformat(),
                "title": artifact.title,
                "confidence": artifact.confidence_score
            })

            logger.info(f"Successfully extracted talk: {artifact.title}")
            return result

        except Exception as e:
            logger.error(f"Talk extraction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check the transcript file is valid and readable"
            }

    def extract_repository_knowledge(
        self,
        repo_input: str,
        llm_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract knowledge from a repository

        Args:
            repo_input: GitHub URL or local repository path
            llm_provider: LLM provider to use (overrides default)

        Returns:
            Dict with extraction results
        """
        provider = llm_provider or self.default_llm_provider
        logger.info(f"Extracting knowledge from repository: {repo_input}")

        try:
            # Initialize agent
            agent = RepositoryAgent(llm_provider=provider, temperature=0.3)

            # Extract knowledge
            artifact = agent.extract(repo_input)

            # Save outputs
            json_file = agent.save_artifact(artifact, str(self.output_dir))
            summary_file = agent.save_summary(artifact, str(self.output_dir))

            # Format response
            result = {
                "success": True,
                "artifact_type": "repository",
                "title": artifact.title,
                "contributors": artifact.contributors,
                "overview": artifact.plain_language_overview,
                "confidence": artifact.confidence_score,
                "files": {
                    "json": json_file,
                    "summary": summary_file
                },
                "extraction_date": artifact.extraction_date.isoformat(),
                "full_artifact": self._artifact_to_dict(artifact)
            }

            # Add to history
            self.extraction_history.append({
                "type": "repository",
                "source": repo_input,
                "timestamp": datetime.now().isoformat(),
                "title": artifact.title,
                "confidence": artifact.confidence_score
            })

            logger.info(f"Successfully extracted repository: {artifact.title}")
            return result

        except Exception as e:
            logger.error(f"Repository extraction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check the repository URL or path is valid"
            }

    # ========== Microsoft 365 Integration Methods ==========

    def extract_from_sharepoint(
        self,
        site_id: str,
        file_path: str,
        llm_provider: Optional[str] = None,
        save_to_sharepoint: bool = True,
        notify_teams: bool = False,
        team_id: Optional[str] = None,
        channel_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract knowledge from SharePoint document

        Args:
            site_id: SharePoint site ID
            file_path: Path to file like "/Shared Documents/paper.pdf"
            llm_provider: LLM provider to use (overrides default)
            save_to_sharepoint: Save artifact back to SharePoint
            notify_teams: Post notification to Teams
            team_id: Teams team ID (required if notify_teams=True)
            channel_id: Teams channel ID (required if notify_teams=True)

        Returns:
            Dict with extraction results including M365 metadata
        """
        if not self.enable_m365:
            return {
                "success": False,
                "error": "Microsoft 365 integration not enabled",
                "suggestion": "Initialize agent with enable_m365=True"
            }

        logger.info(f"Extracting from SharePoint: {site_id}/{file_path}")
        provider = llm_provider or self.default_llm_provider

        try:
            # Download file from SharePoint
            content = self.m365.download_file(site_id, file_path)

            # Get file metadata for provenance
            item = self.m365.get_item_by_path(site_id, file_path)

            # Determine extraction type based on file extension
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.pdf':
                agent = PaperAgent(llm_provider=provider, temperature=0.3)
                # Save to temp file for extraction
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                artifact = agent.extract(tmp_path)
                Path(tmp_path).unlink()  # Clean up

            elif file_ext in ['.txt', '.md']:
                agent = TalkAgent(llm_provider=provider, temperature=0.3)
                text_content = content.decode('utf-8')
                # Save to temp file
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                    tmp.write(text_content)
                    tmp_path = tmp.name
                artifact = agent.extract(tmp_path)
                Path(tmp_path).unlink()

            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_ext}",
                    "suggestion": "Supported types: .pdf, .txt, .md"
                }

            # Save locally
            json_file = agent.save_artifact(artifact, str(self.output_dir))
            summary_file = agent.save_summary(artifact, str(self.output_dir))

            result = {
                "success": True,
                "artifact_type": "sharepoint",
                "title": artifact.title,
                "contributors": artifact.contributors,
                "overview": artifact.plain_language_overview,
                "confidence": artifact.confidence_score,
                "files": {
                    "json": json_file,
                    "summary": summary_file
                },
                "extraction_date": artifact.extraction_date.isoformat(),
                "m365_source": {
                    "site_id": site_id,
                    "file_path": file_path,
                    "web_url": item.get('webUrl', ''),
                    "last_modified": item.get('lastModifiedDateTime', ''),
                    "file_size": item.get('size', 0)
                }
            }

            # Save back to SharePoint if requested
            if save_to_sharepoint:
                try:
                    # Read local files
                    json_content = Path(json_file).read_bytes()
                    md_content = Path(summary_file).read_bytes()

                    # Upload to SharePoint
                    json_result = self.m365.upload_file(
                        site_id,
                        "/Knowledge Artifacts",
                        Path(json_file).name,
                        json_content
                    )
                    md_result = self.m365.upload_file(
                        site_id,
                        "/Knowledge Artifacts",
                        Path(summary_file).name,
                        md_content
                    )

                    result["sharepoint_urls"] = {
                        "json_url": json_result.get('webUrl', ''),
                        "markdown_url": md_result.get('webUrl', '')
                    }
                    logger.info("Saved artifacts to SharePoint")
                except Exception as e:
                    logger.warning(f"Failed to save to SharePoint: {e}")
                    result["sharepoint_error"] = str(e)

            # Send Teams notification if requested
            if notify_teams and team_id and channel_id:
                try:
                    message = self.m365.format_artifact_summary(
                        artifact,
                        include_links=save_to_sharepoint,
                        sharepoint_urls=result.get('sharepoint_urls')
                    )
                    self.m365.post_to_channel(team_id, channel_id, message)
                    result["teams_notification"] = "sent"
                    logger.info("Sent Teams notification")
                except Exception as e:
                    logger.warning(f"Failed to send Teams notification: {e}")
                    result["teams_error"] = str(e)

            # Add to history
            self.extraction_history.append({
                "type": "sharepoint",
                "source": f"{site_id}/{file_path}",
                "timestamp": datetime.now().isoformat(),
                "title": artifact.title,
                "confidence": artifact.confidence_score
            })

            return result

        except Exception as e:
            logger.error(f"SharePoint extraction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check site ID and file path are correct"
            }

    def extract_from_onedrive(
        self,
        file_path: str,
        llm_provider: Optional[str] = None,
        save_to_onedrive: bool = True
    ) -> Dict[str, Any]:
        """Extract knowledge from OneDrive file

        Args:
            file_path: Path to file like "/Documents/paper.pdf"
            llm_provider: LLM provider to use (overrides default)
            save_to_onedrive: Save artifact back to OneDrive

        Returns:
            Dict with extraction results
        """
        if not self.enable_m365:
            return {
                "success": False,
                "error": "Microsoft 365 integration not enabled",
                "suggestion": "Initialize agent with enable_m365=True"
            }

        logger.info(f"Extracting from OneDrive: {file_path}")
        provider = llm_provider or self.default_llm_provider

        try:
            # Download file
            content = self.m365.get_onedrive_file_by_path(file_path)

            # Determine extraction type
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.pdf':
                agent = PaperAgent(llm_provider=provider, temperature=0.3)
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                artifact = agent.extract(tmp_path)
                Path(tmp_path).unlink()

            elif file_ext in ['.txt', '.md']:
                agent = TalkAgent(llm_provider=provider, temperature=0.3)
                text_content = content.decode('utf-8')
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
                    tmp.write(text_content)
                    tmp_path = tmp.name
                artifact = agent.extract(tmp_path)
                Path(tmp_path).unlink()

            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_ext}",
                    "suggestion": "Supported types: .pdf, .txt, .md"
                }

            # Save locally
            json_file = agent.save_artifact(artifact, str(self.output_dir))
            summary_file = agent.save_summary(artifact, str(self.output_dir))

            result = {
                "success": True,
                "artifact_type": "onedrive",
                "title": artifact.title,
                "contributors": artifact.contributors,
                "overview": artifact.plain_language_overview,
                "confidence": artifact.confidence_score,
                "files": {
                    "json": json_file,
                    "summary": summary_file
                }
            }

            # Save back to OneDrive if requested
            if save_to_onedrive:
                try:
                    json_content = Path(json_file).read_bytes()
                    md_content = Path(summary_file).read_bytes()

                    json_result = self.m365.upload_to_onedrive(
                        "/Documents/Knowledge Artifacts",
                        Path(json_file).name,
                        json_content
                    )
                    md_result = self.m365.upload_to_onedrive(
                        "/Documents/Knowledge Artifacts",
                        Path(summary_file).name,
                        md_content
                    )

                    result["onedrive_urls"] = {
                        "json_url": json_result.get('webUrl', ''),
                        "markdown_url": md_result.get('webUrl', '')
                    }
                except Exception as e:
                    logger.warning(f"Failed to save to OneDrive: {e}")
                    result["onedrive_error"] = str(e)

            # Add to history
            self.extraction_history.append({
                "type": "onedrive",
                "source": file_path,
                "timestamp": datetime.now().isoformat(),
                "title": artifact.title,
                "confidence": artifact.confidence_score
            })

            return result

        except Exception as e:
            logger.error(f"OneDrive extraction failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Check file path is correct"
            }

    def get_extraction_status(self, limit: int = 5) -> Dict[str, Any]:
        """Get recent extraction history

        Args:
            limit: Number of recent extractions to return

        Returns:
            Dict with extraction history
        """
        recent = self.extraction_history[-limit:] if self.extraction_history else []

        return {
            "success": True,
            "total_extractions": len(self.extraction_history),
            "recent_extractions": recent,
            "output_directory": str(self.output_dir),
            "m365_enabled": self.enable_m365
        }


class KnowledgeAgentExtractorAdapter:
    """Adapter to reuse KnowledgeExtractionAgent inside the pipeline Protocol."""

    def __init__(self, file_name: str, llm_provider: str = "azure-openai") -> None:
        self.file_name = file_name
        self.llm_provider = llm_provider

    def extract(self, raw: Any, provider: Optional[Any] = None) -> Dict[str, Any]:  # pragma: no cover - integration glue
        suffix = Path(self.file_name).suffix.lower() or ".bin"

        with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            if isinstance(raw, (bytes, bytearray)):
                tmp.write(raw)
            else:
                tmp.write(str(raw).encode("utf-8"))
            tmp_path = tmp.name

        agent = KnowledgeExtractionAgent(default_llm_provider=self.llm_provider)
        if suffix == ".pdf":
            result = agent.extract_paper_knowledge(tmp_path, self.llm_provider)
        else:
            result = agent.extract_talk_knowledge(tmp_path, self.llm_provider)

        if not result.get("success"):
            raise RuntimeError(result.get("error", "Extraction failed"))

        artifact = result["full_artifact"]
        title = artifact.get("title") or Path(self.file_name).stem or "artifact"
        artifact["title"] = title
        artifact["id"] = title.lower().replace(" ", "-")[:80]
        artifact["files"] = result.get("files", {})
        return artifact

    def _artifact_to_dict(self, artifact: BaseKnowledgeArtifact) -> Dict[str, Any]:
        """Convert artifact to dict for JSON serialization"""
        return {
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

    def process_message(self, message: str) -> str:
        """Process a conversational message

        Args:
            message: User message

        Returns:
            Agent response
        """
        message_lower = message.lower()

        # Help request
        if any(word in message_lower for word in ["help", "what can you do", "capabilities"]):
            return """I'm a Knowledge Extraction Agent. I can help you extract structured knowledge from:

📄 **Research Papers** (PDF files)
   - Extract publication details, methods, results, impact
   - Command: "extract paper from [path]"

🎤 **Research Talks** (transcripts)
   - Extract presentation structure, demos, challenges
   - Command: "extract talk from [path]"

💻 **Code Repositories** (GitHub or local)
   - Extract tech stack, setup, APIs, governance
   - Command: "extract repository from [url/path]"

I provide both structured JSON and human-readable summaries with confidence scores.

**Examples**:
- "Extract paper from papers/attention.pdf"
- "Extract talk from transcripts/demo.txt"
- "Extract repository from https://github.com/owner/repo"
- "Show recent extractions"
"""

        # Status check
        if any(word in message_lower for word in ["status", "history", "recent", "show extractions"]):
            status = self.get_extraction_status()
            if status["total_extractions"] == 0:
                return "No extractions yet. Provide a paper, talk, or repository to analyze!"

            response = f"**Extraction History** ({status['total_extractions']} total)\n\n"
            for item in status["recent_extractions"]:
                response += f"- {item['type'].title()}: {item['title']} (confidence: {item['confidence']:.0%})\n"
            return response

        # Detection patterns
        if "paper" in message_lower and "extract" in message_lower:
            return "Please provide the path to the PDF file you'd like to analyze.\n\nExample: `papers/research_paper.pdf`"

        if "talk" in message_lower and "extract" in message_lower:
            return "Please provide the path to the transcript file you'd like to analyze.\n\nExample: `transcripts/talk.txt`"

        if "repository" in message_lower and "extract" in message_lower:
            return "Please provide the GitHub URL or local path to the repository you'd like to analyze.\n\nExample: `https://github.com/owner/repo`"

        # Default response
        return """I can extract structured knowledge from research artifacts. Try:

- "Extract paper from [pdf_path]"
- "Extract talk from [transcript_path]"
- "Extract repository from [github_url]"
- "Show recent extractions"
- "Help" for more information
"""


# Tool function implementations for agent framework
def extract_paper_knowledge(pdf_path: str, llm_provider: str = "azure-openai") -> str:
    """Tool function: Extract knowledge from paper"""
    agent = KnowledgeExtractionAgent(default_llm_provider=llm_provider)
    result = agent.extract_paper_knowledge(pdf_path)

    if result["success"]:
        return f"""✅ Successfully extracted paper knowledge

**Title**: {result['title']}
**Contributors**: {', '.join(result['contributors'])}
**Confidence**: {result['confidence']:.0%}

**Overview**: {result['overview'][:200]}...

**Files saved**:
- JSON: {result['files']['json']}
- Summary: {result['files']['summary']}
"""
    else:
        return f"❌ Extraction failed: {result['error']}\n\n{result.get('suggestion', '')}"


def extract_talk_knowledge(transcript_path: str, llm_provider: str = "azure-openai") -> str:
    """Tool function: Extract knowledge from talk"""
    agent = KnowledgeExtractionAgent(default_llm_provider=llm_provider)
    result = agent.extract_talk_knowledge(transcript_path)

    if result["success"]:
        return f"""✅ Successfully extracted talk knowledge

**Title**: {result['title']}
**Speakers**: {', '.join(result['contributors'])}
**Confidence**: {result['confidence']:.0%}

**Overview**: {result['overview'][:200]}...

**Files saved**:
- JSON: {result['files']['json']}
- Summary: {result['files']['summary']}
"""
    else:
        return f"❌ Extraction failed: {result['error']}\n\n{result.get('suggestion', '')}"


def extract_repository_knowledge(repo_input: str, llm_provider: str = "azure-openai") -> str:
    """Tool function: Extract knowledge from repository"""
    agent = KnowledgeExtractionAgent(default_llm_provider=llm_provider)
    result = agent.extract_repository_knowledge(repo_input)

    if result["success"]:
        return f"""✅ Successfully extracted repository knowledge

**Repository**: {result['title']}
**Contributors**: {', '.join(result['contributors'])}
**Confidence**: {result['confidence']:.0%}

**Overview**: {result['overview'][:200]}...

**Files saved**:
- JSON: {result['files']['json']}
- Summary: {result['files']['summary']}
"""
    else:
        return f"❌ Extraction failed: {result['error']}\n\n{result.get('suggestion', '')}"


def get_extraction_status(limit: int = 5) -> str:
    """Tool function: Get extraction history"""
    agent = KnowledgeExtractionAgent()
    result = agent.get_extraction_status(limit)

    if result["total_extractions"] == 0:
        return "No extractions yet."

    response = f"**Total extractions**: {result['total_extractions']}\n\n**Recent**:\n"
    for item in result["recent_extractions"]:
        response += f"- {item['type'].title()}: {item['title']} ({item['confidence']:.0%})\n"

    return response


# ========== Microsoft 365 Tool Functions ==========

def extract_from_sharepoint(
    site_id: str,
    file_path: str,
    llm_provider: str = "azure-openai",
    save_to_sharepoint: bool = True,
    notify_teams: bool = False,
    team_id: str = None,
    channel_id: str = None
) -> str:
    """Tool function: Extract knowledge from SharePoint document"""
    agent = KnowledgeExtractionAgent(
        default_llm_provider=llm_provider,
        enable_m365=True
    )
    result = agent.extract_from_sharepoint(
        site_id, file_path, llm_provider,
        save_to_sharepoint, notify_teams, team_id, channel_id
    )

    if result["success"]:
        response = f"""✅ Successfully extracted from SharePoint

**Title**: {result['title']}
**Contributors**: {', '.join(result['contributors'])}
**Confidence**: {result['confidence']:.0%}

**Overview**: {result['overview'][:200]}...

**Source**: {result['m365_source']['web_url']}
**Modified**: {result['m365_source']['last_modified']}
"""
        if 'sharepoint_urls' in result:
            response += f"\n**SharePoint Artifacts**:\n- JSON: {result['sharepoint_urls']['json_url']}\n- Summary: {result['sharepoint_urls']['markdown_url']}\n"
        if result.get('teams_notification') == 'sent':
            response += "\n✉️ Teams notification sent\n"
        return response
    else:
        return f"❌ Extraction failed: {result['error']}\n\n{result.get('suggestion', '')}"


def extract_from_onedrive(
    file_path: str,
    llm_provider: str = "azure-openai",
    save_to_onedrive: bool = True
) -> str:
    """Tool function: Extract knowledge from OneDrive file"""
    agent = KnowledgeExtractionAgent(
        default_llm_provider=llm_provider,
        enable_m365=True
    )
    result = agent.extract_from_onedrive(file_path, llm_provider, save_to_onedrive)

    if result["success"]:
        response = f"""✅ Successfully extracted from OneDrive

**Title**: {result['title']}
**Contributors**: {', '.join(result['contributors'])}
**Confidence**: {result['confidence']:.0%}

**Overview**: {result['overview'][:200]}...

**Local files**:
- JSON: {result['files']['json']}
- Summary: {result['files']['summary']}
"""
        if 'onedrive_urls' in result:
            response += f"\n**OneDrive Artifacts**:\n- JSON: {result['onedrive_urls']['json_url']}\n- Summary: {result['onedrive_urls']['markdown_url']}\n"
        return response
    else:
        return f"❌ Extraction failed: {result['error']}\n\n{result.get('suggestion', '')}"


if __name__ == "__main__":
    # Simple CLI test
    import argparse

    def run_sharepoint_pipeline_cli(cli_args: argparse.Namespace) -> None:
        if not cli_args.site_id or not cli_args.file_path:
            raise SystemExit("--site-id and --file-path are required for --sharepoint-pipeline")

        from integrations.m365_connector import create_connector
        from integrations.m365_adapters import SharePointSource, SharePointSink, TeamsNotifier

        connector = create_connector()
        source = SharePointSource(connector, site_id=cli_args.site_id, drive_name=cli_args.drive_name)
        sink = SharePointSink(
            connector,
            site_id=cli_args.site_id,
            folder_path=cli_args.folder_path,
            drive_name=cli_args.drive_name,
        )

        notifier = None
        if cli_args.team_id or cli_args.channel_id:
            notifier = TeamsNotifier(connector, team_id=cli_args.team_id, channel_id=cli_args.channel_id)

        extractor = KnowledgeAgentExtractorAdapter(
            file_name=Path(cli_args.file_path).name,
            llm_provider=cli_args.llm_provider,
        )

        pipeline = ExtractionPipeline(
            source=source,
            extractor=extractor,
            sink=sink,
            notifier=notifier,
            provider=None,
        )

        artifact = pipeline.run(cli_args.file_path)
        location = artifact.get("location", "(unknown)")
        print("✅ SharePoint pipeline extraction complete")
        print(f"Title: {artifact.get('title', '(unnamed)')}")
        print(f"Location: {location}")
        if notifier:
            print("Teams notification: sent")

    def run_onedrive_pipeline_cli(cli_args: argparse.Namespace) -> None:
        if not cli_args.file_path:
            raise SystemExit("--file-path is required for --onedrive-pipeline")

        from integrations.m365_connector import create_connector
        from integrations.m365_adapters import OneDrivePathSource, OneDriveSink, TeamsNotifier

        connector = create_connector()
        source = OneDrivePathSource(connector)
        sink = OneDriveSink(connector, folder_path=cli_args.od_folder_path)

        notifier = None
        if cli_args.team_id or cli_args.channel_id:
            notifier = TeamsNotifier(connector, team_id=cli_args.team_id, channel_id=cli_args.channel_id)

        extractor = KnowledgeAgentExtractorAdapter(
            file_name=Path(cli_args.file_path).name,
            llm_provider=cli_args.llm_provider,
        )

        pipeline = ExtractionPipeline(
            source=source,
            extractor=extractor,
            sink=sink,
            notifier=notifier,
            provider=None,
        )

        artifact = pipeline.run(cli_args.file_path)
        location = artifact.get("location", "(unknown)")
        print("✅ OneDrive pipeline extraction complete")
        print(f"Title: {artifact.get('title', '(unnamed)')}")
        print(f"Location: {location}")
        if notifier:
            print("Teams notification: sent")

    parser = argparse.ArgumentParser(description="Knowledge Extraction Agent")
    parser.add_argument("--m365", action="store_true", help="Enable Microsoft 365 integration (interactive mode)")
    parser.add_argument("--sharepoint-pipeline", action="store_true", help="Run a one-shot SharePoint → pipeline → SharePoint flow")
    parser.add_argument("--onedrive-pipeline", action="store_true", help="Run a one-shot OneDrive → pipeline → OneDrive flow")
    parser.add_argument("--site-id", help="SharePoint site ID for pipeline source/sink")
    parser.add_argument("--file-path", help="File path in SharePoint (e.g., /Shared Documents/file.pdf)")
    parser.add_argument("--drive-name", help="Optional SharePoint drive name")
    parser.add_argument("--folder-path", default="/Knowledge Artifacts", help="Destination folder path in SharePoint")
    parser.add_argument("--od-folder-path", default="/Documents/Knowledge Artifacts", help="Destination folder path in OneDrive")
    parser.add_argument("--team-id", help="Teams team ID for notifications")
    parser.add_argument("--channel-id", help="Teams channel ID for notifications")
    parser.add_argument("--llm-provider", default="azure-openai", help="LLM provider for pipeline extraction")

    args = parser.parse_args()

    if args.sharepoint_pipeline:
        run_sharepoint_pipeline_cli(args)
        sys.exit(0)

    if args.onedrive_pipeline:
        run_onedrive_pipeline_cli(args)
        sys.exit(0)

    agent = KnowledgeExtractionAgent(enable_m365=args.m365)

    print("Knowledge Extraction Agent initialized")
    if args.m365:
        print("Microsoft 365 integration: ENABLED")
    print("Type 'help' for commands, 'exit' to quit\n")

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if not user_input:
            continue

        response = agent.process_message(user_input)
        print(f"\nAgent: {response}\n")
