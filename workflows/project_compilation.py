"""
Project-Level Knowledge Compilation (Stretch Goal)

Implements multi-agent workflow to compile project-level understanding
from individual artifact extractions.

Process:
1. Collator: Aggregate all artifacts for a project
2. Resolver: Identify contradictions, gaps, overlaps
3. Synthesizer: Generate unified project-level knowledge

Uses Group Chat workflow for collaborative compilation.
"""

import json
from typing import List, Dict, Any
from pathlib import Path

from core.schemas.base_schema import BaseKnowledgeArtifact
from workflows.group_chat_workflow import create_group_chat_workflow
from agent_framework import OpenAIChatClient, Agent


# ============================================================================
# COMPILATION AGENTS
# ============================================================================

class CollatorAgent:
    """Aggregates all artifact knowledge for a project."""
    
    async def collate(
        self,
        project_name: str,
        artifacts: List[BaseKnowledgeArtifact]
    ) -> Dict[str, Any]:
        """
        Aggregate artifacts into structured collection.
        
        Args:
            project_name: Name of the project
            artifacts: List of knowledge artifacts
            
        Returns:
            Aggregated project data
        """
        return {
            "project_name": project_name,
            "total_artifacts": len(artifacts),
            "artifact_types": [a.source_type for a in artifacts],
            "all_contributors": list(set(
                contributor
                for artifact in artifacts
                for contributor in artifact.contributors
            )),
            "artifacts": [
                {
                    "title": a.title,
                    "type": a.source_type,
                    "overview": a.plain_language_overview,
                    "technical_problem": a.technical_problem_addressed,
                    "key_methods": a.key_methods_approach,
                    "claims": a.primary_claims_capabilities,
                    "limitations": a.limitations_constraints,
                    "impact": a.potential_impact,
                    "future_work": a.open_questions_future_work
                }
                for a in artifacts
            ]
        }


class ResolverAgent:
    """Identifies contradictions, gaps, and overlaps across artifacts."""
    
    async def resolve(
        self,
        collated_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Identify inconsistencies and gaps.
        
        Args:
            collated_data: Aggregated project data
            
        Returns:
            Resolution analysis
        """
        artifacts = collated_data["artifacts"]
        
        # Find overlapping claims
        all_claims = []
        for artifact in artifacts:
            all_claims.extend(artifact.get("claims", []))
        
        # Find contradictions (simplified heuristic)
        contradictions = []
        # In real implementation, would use LLM to detect semantic contradictions
        
        # Find gaps (what's mentioned but not explained)
        gaps = []
        all_future_work = []
        for artifact in artifacts:
            all_future_work.extend(artifact.get("future_work", []))
        
        # Identify common themes
        common_limitations = []
        for artifact in artifacts:
            common_limitations.extend(artifact.get("limitations", []))
        
        return {
            "contradictions": contradictions,
            "gaps": gaps,
            "common_themes": {
                "shared_future_work": all_future_work,
                "common_limitations": common_limitations
            },
            "cross_references": self._find_cross_references(artifacts)
        }
    
    def _find_cross_references(
        self,
        artifacts: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Find where artifacts reference each other."""
        cross_refs = []
        
        # Simple heuristic: if one artifact's title appears in another's text
        for i, artifact_a in enumerate(artifacts):
            for j, artifact_b in enumerate(artifacts):
                if i != j:
                    title_a = artifact_a.get("title", "").lower()
                    text_b = json.dumps(artifact_b).lower()
                    
                    if title_a in text_b:
                        cross_refs.append({
                            "from": artifact_b.get("title"),
                            "to": artifact_a.get("title"),
                            "type": "mentions"
                        })
        
        return cross_refs


class SynthesizerAgent:
    """Synthesizes unified project-level understanding."""
    
    async def synthesize(
        self,
        collated_data: Dict[str, Any],
        resolution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate unified project knowledge.
        
        Args:
            collated_data: Aggregated artifacts
            resolution: Resolution analysis
            
        Returns:
            Unified project-level knowledge
        """
        artifacts = collated_data["artifacts"]
        
        # Synthesize unified overview
        unified_overview = self._synthesize_overview(artifacts)
        
        # Synthesize technical stack
        unified_technical_problem = self._synthesize_technical_problem(artifacts)
        
        # Synthesize claims
        unified_claims = self._synthesize_claims(artifacts)
        
        # Synthesize limitations
        unified_limitations = self._synthesize_limitations(artifacts, resolution)
        
        # Synthesize impact
        unified_impact = self._synthesize_impact(artifacts)
        
        # Synthesize future directions
        unified_future_work = self._synthesize_future_work(artifacts, resolution)
        
        return {
            "project_name": collated_data["project_name"],
            "unified_overview": unified_overview,
            "unified_technical_problem": unified_technical_problem,
            "unified_claims": unified_claims,
            "unified_limitations": unified_limitations,
            "unified_impact": unified_impact,
            "unified_future_work": unified_future_work,
            "cross_artifact_insights": {
                "cross_references": resolution["cross_references"],
                "common_themes": resolution["common_themes"]
            },
            "compilation_metadata": {
                "artifact_count": len(artifacts),
                "artifact_types": collated_data["artifact_types"],
                "contributors": collated_data["all_contributors"]
            }
        }
    
    def _synthesize_overview(self, artifacts: List[Dict[str, Any]]) -> str:
        """Synthesize unified project overview."""
        overviews = [a.get("overview", "") for a in artifacts if a.get("overview")]
        
        # Simple concatenation (in production, would use LLM)
        return " | ".join(overviews)
    
    def _synthesize_technical_problem(self, artifacts: List[Dict[str, Any]]) -> str:
        """Synthesize unified technical problem statement."""
        problems = [
            a.get("technical_problem", "")
            for a in artifacts
            if a.get("technical_problem")
        ]
        
        return " | ".join(problems)
    
    def _synthesize_claims(self, artifacts: List[Dict[str, Any]]) -> List[str]:
        """Synthesize and deduplicate claims."""
        all_claims = []
        for artifact in artifacts:
            all_claims.extend(artifact.get("claims", []))
        
        # Deduplicate (simple, in production would use semantic deduplication)
        return list(set(all_claims))
    
    def _synthesize_limitations(
        self,
        artifacts: List[Dict[str, Any]],
        resolution: Dict[str, Any]
    ) -> List[str]:
        """Synthesize unified limitations."""
        all_limitations = []
        for artifact in artifacts:
            all_limitations.extend(artifact.get("limitations", []))
        
        # Add common themes
        common_limitations = resolution["common_themes"].get("common_limitations", [])
        all_limitations.extend(common_limitations)
        
        return list(set(all_limitations))
    
    def _synthesize_impact(self, artifacts: List[Dict[str, Any]]) -> str:
        """Synthesize unified impact statement."""
        impacts = [a.get("impact", "") for a in artifacts if a.get("impact")]
        return " | ".join(impacts)
    
    def _synthesize_future_work(
        self,
        artifacts: List[Dict[str, Any]],
        resolution: Dict[str, Any]
    ) -> List[str]:
        """Synthesize unified future work."""
        all_future_work = []
        for artifact in artifacts:
            all_future_work.extend(artifact.get("future_work", []))
        
        # Add gaps as future work
        all_future_work.extend(resolution.get("gaps", []))
        
        return list(set(all_future_work))


# ============================================================================
# MAIN COMPILATION WORKFLOW
# ============================================================================

async def compile_project_knowledge(
    project_name: str,
    artifacts: List[BaseKnowledgeArtifact]
) -> Dict[str, Any]:
    """
    Compile project-level knowledge from individual artifacts.
    
    This is the STRETCH GOAL implementation. Uses a multi-agent
    workflow to aggregate, resolve, and synthesize knowledge.
    
    Args:
        project_name: Name of the project
        artifacts: List of extracted knowledge artifacts
        
    Returns:
        Unified project-level knowledge compilation
    """
    print(f"\n{'='*60}")
    print(f"PROJECT COMPILATION: {project_name}")
    print(f"{'='*60}")
    
    # Step 1: Collate
    print("\nStep 1: Collating artifacts...")
    collator = CollatorAgent()
    collated_data = await collator.collate(project_name, artifacts)
    print(f"  Collated {collated_data['total_artifacts']} artifacts")
    
    # Step 2: Resolve
    print("\nStep 2: Resolving contradictions and gaps...")
    resolver = ResolverAgent()
    resolution = await resolver.resolve(collated_data)
    print(f"  Found {len(resolution['contradictions'])} contradictions")
    print(f"  Found {len(resolution['gaps'])} gaps")
    print(f"  Found {len(resolution['cross_references'])} cross-references")
    
    # Step 3: Synthesize
    print("\nStep 3: Synthesizing unified knowledge...")
    synthesizer = SynthesizerAgent()
    compilation = await synthesizer.synthesize(collated_data, resolution)
    print(f"  Generated unified project knowledge")
    print(f"  Unified claims: {len(compilation['unified_claims'])}")
    print(f"  Unified limitations: {len(compilation['unified_limitations'])}")
    
    print(f"\n{'='*60}")
    print(f"COMPILATION COMPLETE: {project_name}")
    print(f"{'='*60}")
    
    return compilation


# ============================================================================
# ADVANCED: LLM-POWERED COMPILATION (OPTIONAL)
# ============================================================================

async def compile_project_knowledge_with_llm(
    project_name: str,
    artifacts: List[BaseKnowledgeArtifact],
    model: str = "gpt-4"
) -> Dict[str, Any]:
    """
    Advanced compilation using LLM-powered agents in group chat.
    
    This version uses the Agent Framework's GroupChatBuilder
    to orchestrate compilation with LLM-powered reasoning.
    
    Args:
        project_name: Name of project
        artifacts: Knowledge artifacts
        model: LLM model to use
        
    Returns:
        LLM-powered compilation
    """
    # Create LLM-powered agents
    client = OpenAIChatClient(model=model)
    
    collator_agent = Agent(
        name="Collator",
        client=client,
        instructions="""You are a knowledge collation specialist.
        Aggregate all artifacts for a project and identify key themes."""
    )
    
    resolver_agent = Agent(
        name="Resolver",
        client=client,
        instructions="""You are a contradiction resolution specialist.
        Identify inconsistencies, gaps, and overlaps across artifacts."""
    )
    
    synthesizer_agent = Agent(
        name="Synthesizer",
        client=client,
        instructions="""You are a knowledge synthesis specialist.
        Create unified, coherent project-level understanding."""
    )
    
    manager_agent = Agent(
        name="CompilationManager",
        client=client,
        instructions="""You coordinate the compilation process.
        First have Collator aggregate, then Resolver analyze, then Synthesizer unify."""
    )
    
    # Create group chat workflow
    workflow = create_group_chat_workflow(
        participants=[collator_agent, resolver_agent, synthesizer_agent],
        manager=manager_agent,
        max_rounds=10,
        workflow_name=f"compile_{project_name}"
    )
    
    # Prepare input context
    context = {
        "project_name": project_name,
        "artifacts": [a.to_dict() for a in artifacts]
    }
    
    # Run compilation workflow
    result = await workflow.run(json.dumps(context))
    
    # Extract compilation from result
    # (In production, would parse structured output from synthesizer)
    
    return {
        "project_name": project_name,
        "compilation": result,
        "method": "llm_powered_group_chat"
    }
