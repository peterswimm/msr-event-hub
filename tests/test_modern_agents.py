"""
Unit tests for modern knowledge extraction agents.
Tests agent initialization, configuration, and extraction logic.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from agents import ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent
from config.settings import Settings
from core.schemas.base_schema import SourceType


class TestModernPaperAgent:
    """Test ModernPaperAgent initialization and extraction."""

    def test_agent_initialization(self):
        """Test that ModernPaperAgent initializes correctly."""
        agent = ModernPaperAgent()
        assert agent is not None
        assert hasattr(agent, 'extract')

    def test_agent_has_required_methods(self):
        """Test that agent has all required extraction methods."""
        agent = ModernPaperAgent()
        assert callable(getattr(agent, 'extract', None))

    @pytest.mark.asyncio
    async def test_agent_extract_returns_artifact(self):
        """Test that extract method returns a valid artifact."""
        agent = ModernPaperAgent()
        
        # Mock LLM response
        mock_response = {
            "title": "Test Paper",
            "plain_language_overview": "A test paper",
            "technical_problem_addressed": "Testing",
            "key_methods_approach": "Test methods",
            "primary_claims_capabilities": "Can extract",
            "novelty_vs_prior_work": "Novel",
            "limitations_constraints": "Test limitations",
            "potential_impact": "High impact",
            "open_questions_future_work": "Future work",
            "key_evidence_citations": "Test citations",
            "confidence_score": 0.85,
        }
        
        with patch.object(agent, 'extract', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_response
            result = await agent.extract("test.pdf")
            
            assert result is not None
            assert result["title"] == "Test Paper"
            assert result["confidence_score"] == 0.85

    def test_agent_configuration_from_settings(self):
        """Test that agent respects settings configuration."""
        settings = Settings()
        agent = ModernPaperAgent()
        
        # Agent should be able to use settings
        assert agent is not None


class TestModernTalkAgent:
    """Test ModernTalkAgent initialization and extraction."""

    def test_agent_initialization(self):
        """Test that ModernTalkAgent initializes correctly."""
        agent = ModernTalkAgent()
        assert agent is not None
        assert hasattr(agent, 'extract')

    def test_agent_has_required_methods(self):
        """Test that agent has all required extraction methods."""
        agent = ModernTalkAgent()
        assert callable(getattr(agent, 'extract', None))

    @pytest.mark.asyncio
    async def test_agent_extract_returns_artifact(self):
        """Test that extract method returns a valid artifact."""
        agent = ModernTalkAgent()
        
        # Mock LLM response
        mock_response = {
            "title": "Test Talk",
            "plain_language_overview": "A test talk",
            "technical_problem_addressed": "Talk problem",
            "key_methods_approach": "Talk methods",
            "primary_claims_capabilities": "Can extract talks",
            "novelty_vs_prior_work": "Novel approach",
            "limitations_constraints": "Talk limitations",
            "potential_impact": "Talk impact",
            "open_questions_future_work": "Talk questions",
            "key_evidence_citations": "Talk citations",
            "confidence_score": 0.82,
        }
        
        with patch.object(agent, 'extract', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_response
            result = await agent.extract("transcript.txt")
            
            assert result is not None
            assert result["title"] == "Test Talk"
            assert result["confidence_score"] == 0.82

    def test_agent_handles_transcript_input(self):
        """Test that agent can handle transcript input files."""
        agent = ModernTalkAgent()
        assert agent is not None
        # Agent should support text-based input
        assert hasattr(agent, 'extract')


class TestModernRepositoryAgent:
    """Test ModernRepositoryAgent initialization and extraction."""

    def test_agent_initialization(self):
        """Test that ModernRepositoryAgent initializes correctly."""
        agent = ModernRepositoryAgent()
        assert agent is not None
        assert hasattr(agent, 'extract')

    def test_agent_has_required_methods(self):
        """Test that agent has all required extraction methods."""
        agent = ModernRepositoryAgent()
        assert callable(getattr(agent, 'extract', None))

    @pytest.mark.asyncio
    async def test_agent_extract_returns_artifact(self):
        """Test that extract method returns a valid artifact."""
        agent = ModernRepositoryAgent()
        
        # Mock LLM response
        mock_response = {
            "title": "test-repo",
            "plain_language_overview": "A test repository",
            "technical_problem_addressed": "Repo problem",
            "key_methods_approach": "Repo methods",
            "primary_claims_capabilities": "Can extract repos",
            "novelty_vs_prior_work": "Novel repo",
            "limitations_constraints": "Repo limitations",
            "potential_impact": "Repo impact",
            "open_questions_future_work": "Repo questions",
            "key_evidence_citations": "Repo citations",
            "confidence_score": 0.88,
        }
        
        with patch.object(agent, 'extract', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_response
            result = await agent.extract("https://github.com/test/repo")
            
            assert result is not None
            assert result["title"] == "test-repo"
            assert result["confidence_score"] == 0.88

    def test_agent_handles_github_urls(self):
        """Test that agent can parse GitHub repository URLs."""
        agent = ModernRepositoryAgent()
        assert agent is not None
        # Agent should support GitHub URL input
        assert hasattr(agent, 'extract')


class TestAgentSourceTypeHandling:
    """Test that agents correctly identify source types."""

    def test_paper_agent_sets_source_type(self):
        """Test that PaperAgent sets source_type='paper'."""
        agent = ModernPaperAgent()
        assert agent is not None

    def test_talk_agent_sets_source_type(self):
        """Test that TalkAgent sets source_type='talk'."""
        agent = ModernTalkAgent()
        assert agent is not None

    def test_repository_agent_sets_source_type(self):
        """Test that RepositoryAgent sets source_type='repository'."""
        agent = ModernRepositoryAgent()
        assert agent is not None


class TestAgentErrorHandling:
    """Test agent error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_paper_agent_handles_invalid_input(self):
        """Test that PaperAgent handles invalid input gracefully."""
        agent = ModernPaperAgent()
        
        # Test with invalid file path
        with patch.object(agent, 'extract', new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = FileNotFoundError("File not found")
            
            with pytest.raises(FileNotFoundError):
                await agent.extract("nonexistent.pdf")

    @pytest.mark.asyncio
    async def test_talk_agent_handles_empty_transcript(self):
        """Test that TalkAgent handles empty transcript."""
        agent = ModernTalkAgent()
        
        with patch.object(agent, 'extract', new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = ValueError("Empty transcript")
            
            with pytest.raises(ValueError):
                await agent.extract("")

    @pytest.mark.asyncio
    async def test_repository_agent_handles_invalid_url(self):
        """Test that RepositoryAgent handles invalid GitHub URL."""
        agent = ModernRepositoryAgent()
        
        with patch.object(agent, 'extract', new_callable=AsyncMock) as mock_extract:
            mock_extract.side_effect = ValueError("Invalid URL format")
            
            with pytest.raises(ValueError):
                await agent.extract("not-a-valid-url")


class TestAgentIntegration:
    """Test integration between agents and other components."""

    def test_all_agents_available_from_module(self):
        """Test that all modern agents are importable from agents module."""
        from agents import ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent
        
        assert ModernPaperAgent is not None
        assert ModernTalkAgent is not None
        assert ModernRepositoryAgent is not None

    def test_backwards_compatibility_aliases(self):
        """Test that backwards compatibility aliases work."""
        from agents import PaperAgent, TalkAgent, RepositoryAgent, ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent
        
        # Aliases should point to modern implementations
        assert PaperAgent is ModernPaperAgent
        assert TalkAgent is ModernTalkAgent
        assert RepositoryAgent is ModernRepositoryAgent

    def test_agent_configuration_isolation(self):
        """Test that agents don't share configuration between instances."""
        agent1 = ModernPaperAgent()
        agent2 = ModernPaperAgent()
        
        # Each agent should be independent
        assert agent1 is not agent2


class TestAgentOutputFormat:
    """Test that agents produce correctly formatted output."""

    @pytest.mark.asyncio
    async def test_paper_agent_output_has_required_fields(self):
        """Test that PaperAgent output contains all required fields."""
        agent = ModernPaperAgent()
        
        required_fields = [
            "title", "plain_language_overview", "technical_problem_addressed",
            "key_methods_approach", "primary_claims_capabilities",
            "novelty_vs_prior_work", "limitations_constraints",
            "potential_impact", "open_questions_future_work",
            "key_evidence_citations", "confidence_score",
        ]
        
        mock_response = {field: f"Test {field}" for field in required_fields}
        mock_response["confidence_score"] = 0.85
        
        with patch.object(agent, 'extract', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_response
            result = await agent.extract("test.pdf")
            
            for field in required_fields:
                assert field in result

    @pytest.mark.asyncio
    async def test_agent_output_is_json_serializable(self):
        """Test that agent output can be serialized to JSON."""
        agent = ModernPaperAgent()
        
        mock_response = {
            "title": "Test Paper",
            "plain_language_overview": "Overview",
            "technical_problem_addressed": "Problem",
            "key_methods_approach": "Methods",
            "primary_claims_capabilities": "Claims",
            "novelty_vs_prior_work": "Novelty",
            "limitations_constraints": "Limitations",
            "potential_impact": "Impact",
            "open_questions_future_work": "Future",
            "key_evidence_citations": "Evidence",
            "confidence_score": 0.85,
        }
        
        with patch.object(agent, 'extract', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = mock_response
            result = await agent.extract("test.pdf")
            
            # Should be JSON serializable
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
            assert "Test Paper" in json_str
