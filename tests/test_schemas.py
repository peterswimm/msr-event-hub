"""
Tests for knowledge artifact schemas.
Validates that all schema types correctly define and validate knowledge artifacts.
"""

import pytest
from datetime import datetime

from src.core.schemas.base_schema import BaseKnowledgeArtifact, SourceType
from src.core.schemas.paper_schema import PaperKnowledgeArtifact
from src.core.schemas.talk_schema import TalkKnowledgeArtifact
from src.core.schemas.repository_schema import RepositoryKnowledgeArtifact


class TestBaseKnowledgeArtifact:
    """Test BaseKnowledgeArtifact schema validation."""

    def test_base_artifact_creation_minimal(self):
        """Test creating a base artifact with required fields only."""
        artifact = BaseKnowledgeArtifact(
            title="Test Artifact",
            contributors=["Author A"],
            source_type=SourceType.PAPER,
            plain_language_overview="Overview",
            technical_problem_addressed="Problem",
            key_methods_approach="Methods",
            primary_claims_capabilities=["Claim 1"],
            novelty_vs_prior_work="Novelty",
            limitations_constraints=["Limitation"],
            potential_impact="Impact",
            open_questions_future_work=["Question"],
            key_evidence_citations=["Citation"],
            confidence_score=0.85,
        )
        
        assert artifact.title == "Test Artifact"
        assert len(artifact.contributors) == 1
        assert artifact.confidence_score == 0.85
        assert artifact.source_type == SourceType.PAPER

    def test_base_artifact_creation_with_optional_fields(self):
        """Test creating a base artifact with optional fields."""
        artifact = BaseKnowledgeArtifact(
            title="Test Artifact",
            contributors=["Author A", "Author B"],
            source_type=SourceType.PAPER,
            plain_language_overview="Overview",
            technical_problem_addressed="Problem",
            key_methods_approach="Methods",
            primary_claims_capabilities=["Claim 1", "Claim 2"],
            novelty_vs_prior_work="Novelty",
            limitations_constraints=["Limitation 1", "Limitation 2"],
            potential_impact="Impact",
            open_questions_future_work=["Question 1", "Question 2"],
            key_evidence_citations=["Citation 1", "Citation 2"],
            confidence_score=0.85,
            confidence_reasoning="High confidence based on validation",
            provenance={"source": "test", "model": "gpt-4"},
            additional_knowledge={"custom_field": "custom_value"},
        )
        
        assert artifact.title == "Test Artifact"
        assert len(artifact.contributors) == 2
        assert artifact.confidence_reasoning is not None
        assert artifact.provenance["model"] == "gpt-4"

    def test_base_artifact_source_type_enum(self):
        """Test that source_type accepts valid enum values."""
        for source_type in [SourceType.PAPER, SourceType.TALK, SourceType.REPOSITORY]:
            artifact = BaseKnowledgeArtifact(
                title="Test",
                contributors=["Author"],
                source_type=source_type,
                plain_language_overview="Overview",
                technical_problem_addressed="Problem",
                key_methods_approach="Methods",
                primary_claims_capabilities=["Claim"],
                novelty_vs_prior_work="Novelty",
                limitations_constraints=["Limit"],
                potential_impact="Impact",
                open_questions_future_work=["Question"],
                key_evidence_citations=["Citation"],
                confidence_score=0.8,
            )
            assert artifact.source_type == source_type

    def test_base_artifact_to_dict(self):
        """Test conversion to dictionary."""
        artifact = BaseKnowledgeArtifact(
            title="Test Paper",
            contributors=["Author A"],
            source_type=SourceType.PAPER,
            plain_language_overview="Overview",
            technical_problem_addressed="Problem",
            key_methods_approach="Methods",
            primary_claims_capabilities=["Claim"],
            novelty_vs_prior_work="Novelty",
            limitations_constraints=["Limit"],
            potential_impact="Impact",
            open_questions_future_work=["Question"],
            key_evidence_citations=["Citation"],
            confidence_score=0.85,
            provenance={"source": "test"},
        )
        
        artifact_dict = artifact.to_dict()
        assert isinstance(artifact_dict, dict)
        assert artifact_dict["title"] == "Test Paper"
        assert artifact_dict["source_type"] == "paper"
        assert artifact_dict["confidence_score"] == 0.85

    def test_base_artifact_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "title": "Test Paper",
            "contributors": ["Author A"],
            "source_type": "paper",
            "plain_language_overview": "Overview",
            "technical_problem_addressed": "Problem",
            "key_methods_approach": "Methods",
            "primary_claims_capabilities": ["Claim"],
            "novelty_vs_prior_work": "Novelty",
            "limitations_constraints": ["Limit"],
            "potential_impact": "Impact",
            "open_questions_future_work": ["Question"],
            "key_evidence_citations": ["Citation"],
            "confidence_score": 0.85,
        }
        
        artifact = BaseKnowledgeArtifact.from_dict(data)
        assert artifact.title == "Test Paper"
        assert artifact.source_type == SourceType.PAPER
        assert artifact.confidence_score == 0.85


class TestPaperKnowledgeArtifact:
    """Test PaperKnowledgeArtifact schema extensions."""

    def test_paper_artifact_creation(self):
        """Test creating a paper artifact."""
        artifact = PaperKnowledgeArtifact(
            title="Research Paper",
            contributors=["Author A", "Author B"],
            source_type=SourceType.PAPER,
            plain_language_overview="A research paper",
            technical_problem_addressed="Research problem",
            key_methods_approach="Research methods",
            primary_claims_capabilities=["Finding 1", "Finding 2"],
            novelty_vs_prior_work="Novel approach",
            limitations_constraints=["Limitation"],
            potential_impact="High impact",
            open_questions_future_work=["Future work"],
            key_evidence_citations=["Peer reviewed"],
            confidence_score=0.9,
        )
        
        assert artifact.title == "Research Paper"
        assert artifact.source_type == SourceType.PAPER
        assert artifact.confidence_score == 0.9

    def test_paper_artifact_to_dict(self):
        """Test paper artifact serialization."""
        artifact = PaperKnowledgeArtifact(
            title="Research Paper",
            contributors=["Author A"],
            source_type=SourceType.PAPER,
            plain_language_overview="Overview",
            technical_problem_addressed="Problem",
            key_methods_approach="Methods",
            primary_claims_capabilities=["Claim"],
            novelty_vs_prior_work="Novelty",
            limitations_constraints=["Limit"],
            potential_impact="Impact",
            open_questions_future_work=["Question"],
            key_evidence_citations=["Citation"],
            confidence_score=0.85,
        )
        
        artifact_dict = artifact.to_dict()
        assert artifact_dict["title"] == "Research Paper"
        assert artifact_dict["source_type"] == "paper"


class TestTalkKnowledgeArtifact:
    """Test TalkKnowledgeArtifact schema extensions."""

    def test_talk_artifact_creation(self):
        """Test creating a talk artifact."""
        artifact = TalkKnowledgeArtifact(
            title="Research Talk",
            contributors=["Speaker A"],
            source_type=SourceType.TALK,
            plain_language_overview="A talk overview",
            technical_problem_addressed="Talk problem",
            key_methods_approach="Talk methods",
            primary_claims_capabilities=["Insight 1"],
            novelty_vs_prior_work="Novel talk",
            limitations_constraints=["Talk limit"],
            potential_impact="Talk impact",
            open_questions_future_work=["Talk question"],
            key_evidence_citations=["Talk citation"],
            confidence_score=0.8,
        )
        
        assert artifact.title == "Research Talk"
        assert artifact.source_type == SourceType.TALK
        assert artifact.confidence_score == 0.8

    def test_talk_artifact_to_dict(self):
        """Test talk artifact serialization."""
        artifact = TalkKnowledgeArtifact(
            title="Research Talk",
            contributors=["Speaker"],
            source_type=SourceType.TALK,
            plain_language_overview="Overview",
            technical_problem_addressed="Problem",
            key_methods_approach="Methods",
            primary_claims_capabilities=["Claim"],
            novelty_vs_prior_work="Novelty",
            limitations_constraints=["Limit"],
            potential_impact="Impact",
            open_questions_future_work=["Question"],
            key_evidence_citations=["Citation"],
            confidence_score=0.82,
        )
        
        artifact_dict = artifact.to_dict()
        assert artifact_dict["title"] == "Research Talk"
        assert artifact_dict["source_type"] == "talk"


class TestRepositoryKnowledgeArtifact:
    """Test RepositoryKnowledgeArtifact schema extensions."""

    def test_repository_artifact_creation(self):
        """Test creating a repository artifact."""
        artifact = RepositoryKnowledgeArtifact(
            title="test-repo",
            contributors=["Developer A"],
            source_type=SourceType.REPOSITORY,
            plain_language_overview="A code repository",
            technical_problem_addressed="Repo problem",
            key_methods_approach="Repo methods",
            primary_claims_capabilities=["Feature 1"],
            novelty_vs_prior_work="Novel repo",
            limitations_constraints=["Repo limit"],
            potential_impact="Repo impact",
            open_questions_future_work=["Repo question"],
            key_evidence_citations=["Repo citation"],
            confidence_score=0.88,
        )
        
        assert artifact.title == "test-repo"
        assert artifact.source_type == SourceType.REPOSITORY
        assert artifact.confidence_score == 0.88

    def test_repository_artifact_to_dict(self):
        """Test repository artifact serialization."""
        artifact = RepositoryKnowledgeArtifact(
            title="test-repo",
            contributors=["Developer"],
            source_type=SourceType.REPOSITORY,
            plain_language_overview="Overview",
            technical_problem_addressed="Problem",
            key_methods_approach="Methods",
            primary_claims_capabilities=["Capability"],
            novelty_vs_prior_work="Novelty",
            limitations_constraints=["Limit"],
            potential_impact="Impact",
            open_questions_future_work=["Question"],
            key_evidence_citations=["Citation"],
            confidence_score=0.85,
        )
        
        artifact_dict = artifact.to_dict()
        assert artifact_dict["title"] == "test-repo"
        assert artifact_dict["source_type"] == "repository"


class TestSchemaInteroperability:
    """Test that different schema types work correctly."""

    def test_all_artifacts_have_baseline_fields(self):
        """Test that all artifacts have the baseline knowledge fields."""
        baseline_fields = [
            "title", "contributors", "source_type",
            "plain_language_overview", "technical_problem_addressed",
            "key_methods_approach", "primary_claims_capabilities",
            "novelty_vs_prior_work", "limitations_constraints",
            "potential_impact", "open_questions_future_work",
            "key_evidence_citations", "confidence_score",
        ]
        
        # Create one of each artifact type
        artifacts = [
            PaperKnowledgeArtifact(
                title="Paper", contributors=["Author"],
                source_type=SourceType.PAPER,
                plain_language_overview="Ov", technical_problem_addressed="Prob",
                key_methods_approach="Meth", primary_claims_capabilities=["Claim"],
                novelty_vs_prior_work="Nov", limitations_constraints=["Lim"],
                potential_impact="Imp", open_questions_future_work=["Q"],
                key_evidence_citations=["Cite"], confidence_score=0.8,
            ),
            TalkKnowledgeArtifact(
                title="Talk", contributors=["Speaker"],
                source_type=SourceType.TALK,
                plain_language_overview="Ov", technical_problem_addressed="Prob",
                key_methods_approach="Meth", primary_claims_capabilities=["Claim"],
                novelty_vs_prior_work="Nov", limitations_constraints=["Lim"],
                potential_impact="Imp", open_questions_future_work=["Q"],
                key_evidence_citations=["Cite"], confidence_score=0.8,
            ),
            RepositoryKnowledgeArtifact(
                title="Repo", contributors=["Dev"],
                source_type=SourceType.REPOSITORY,
                plain_language_overview="Ov", technical_problem_addressed="Prob",
                key_methods_approach="Meth", primary_claims_capabilities=["Claim"],
                novelty_vs_prior_work="Nov", limitations_constraints=["Lim"],
                potential_impact="Imp", open_questions_future_work=["Q"],
                key_evidence_citations=["Cite"], confidence_score=0.8,
            ),
        ]
        
        for artifact in artifacts:
            for field in baseline_fields:
                assert hasattr(artifact, field), f"Missing field: {field} in {artifact.title}"
                assert getattr(artifact, field) is not None, f"Field is None: {field} in {artifact.title}"

    def test_artifact_serialization_consistency(self):
        """Test that serialization is consistent across artifact types."""
        artifacts = [
            PaperKnowledgeArtifact(
                title="Paper", contributors=["A"],
                source_type=SourceType.PAPER, plain_language_overview="O",
                technical_problem_addressed="P", key_methods_approach="M",
                primary_claims_capabilities=["C"], novelty_vs_prior_work="N",
                limitations_constraints=["L"], potential_impact="I",
                open_questions_future_work=["Q"], key_evidence_citations=["C"],
                confidence_score=0.8,
            ),
            TalkKnowledgeArtifact(
                title="Talk", contributors=["S"],
                source_type=SourceType.TALK, plain_language_overview="O",
                technical_problem_addressed="P", key_methods_approach="M",
                primary_claims_capabilities=["C"], novelty_vs_prior_work="N",
                limitations_constraints=["L"], potential_impact="I",
                open_questions_future_work=["Q"], key_evidence_citations=["C"],
                confidence_score=0.8,
            ),
        ]
        
        for artifact in artifacts:
            artifact_dict = artifact.to_dict()
            assert isinstance(artifact_dict, dict)
            assert "title" in artifact_dict
            assert "source_type" in artifact_dict
            assert "confidence_score" in artifact_dict


class TestEdgeCases:
    """Test edge cases in schema validation."""

    def test_empty_contributors_list(self):
        """Test artifact with empty contributors list."""
        artifact = BaseKnowledgeArtifact(
            title="Test",
            contributors=[],  # Empty list
            source_type=SourceType.PAPER,
            plain_language_overview="O",
            technical_problem_addressed="P",
            key_methods_approach="M",
            primary_claims_capabilities=["C"],
            novelty_vs_prior_work="N",
            limitations_constraints=["L"],
            potential_impact="I",
            open_questions_future_work=["Q"],
            key_evidence_citations=["C"],
            confidence_score=0.5,
        )
        assert len(artifact.contributors) == 0

    def test_artifact_with_dict_provenance(self):
        """Test that provenance dict is handled correctly."""
        provenance = {
            "source_file": "test.pdf",
            "model": "gpt-4",
            "timestamp": datetime.now().isoformat(),
        }
        artifact = BaseKnowledgeArtifact(
            title="Test",
            contributors=["A"],
            source_type=SourceType.PAPER,
            plain_language_overview="O",
            technical_problem_addressed="P",
            key_methods_approach="M",
            primary_claims_capabilities=["C"],
            novelty_vs_prior_work="N",
            limitations_constraints=["L"],
            potential_impact="I",
            open_questions_future_work=["Q"],
            key_evidence_citations=["C"],
            confidence_score=0.5,
            provenance=provenance,
        )
        assert artifact.provenance["source_file"] == "test.pdf"
        assert artifact.provenance["model"] == "gpt-4"

    def test_artifact_with_complex_additional_knowledge(self):
        """Test flexible additional_knowledge field."""
        artifact = BaseKnowledgeArtifact(
            title="Test",
            contributors=["A"],
            source_type=SourceType.PAPER,
            plain_language_overview="O",
            technical_problem_addressed="P",
            key_methods_approach="M",
            primary_claims_capabilities=["C"],
            novelty_vs_prior_work="N",
            limitations_constraints=["L"],
            potential_impact="I",
            open_questions_future_work=["Q"],
            key_evidence_citations=["C"],
            confidence_score=0.5,
            additional_knowledge={
                "custom_field": "value",
                "metrics": {"precision": 0.95, "recall": 0.87},
                "tags": ["ml", "nlp", "vision"],
            },
        )
        assert artifact.additional_knowledge["custom_field"] == "value"
        assert artifact.additional_knowledge["metrics"]["precision"] == 0.95
        assert len(artifact.additional_knowledge["tags"]) == 3

    def test_artifact_timestamps(self):
        """Test timestamp handling."""
        artifact = BaseKnowledgeArtifact(
            title="Test",
            contributors=["A"],
            source_type=SourceType.PAPER,
            plain_language_overview="O",
            technical_problem_addressed="P",
            key_methods_approach="M",
            primary_claims_capabilities=["C"],
            novelty_vs_prior_work="N",
            limitations_constraints=["L"],
            potential_impact="I",
            open_questions_future_work=["Q"],
            key_evidence_citations=["C"],
            confidence_score=0.5,
        )
        assert artifact.created_at is not None
        assert isinstance(artifact.created_at, datetime)
