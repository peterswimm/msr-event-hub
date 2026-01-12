"""
POC Workflow Manager

Implements the 7-step POC workflow from the specification:
1. Collect Artifacts
2. Define Projects
3. Assign Agents
4. Extract Knowledge
5. Expert Review
6. Iterate if Needed
7. Output (Stretch: Compile Project Knowledge)
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from agents import ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent
from core.schemas.base_schema import BaseKnowledgeArtifact
from core.schemas.paper_schema import PaperKnowledgeArtifact
from core.schemas.talk_schema import TalkKnowledgeArtifact
from core.schemas.repository_schema import RepositoryKnowledgeArtifact
from evaluation.expert_review import ExpertReview, ReviewDimension, run_expert_review
from workflows.project_compilation import compile_project_knowledge


class POCWorkflowManager:
    """Manages the complete POC workflow from artifact collection to output."""
    
    def __init__(
        self,
        inputs_dir: Path,
        outputs_dir: Path,
        minimum_expert_rating: float = 3.0,
        require_human_approval: bool = False,
        max_iterations: int = 2
    ):
        """
        Initialize POC workflow manager.
        
        Args:
            inputs_dir: Directory containing input artifacts
            outputs_dir: Directory for output artifacts
            minimum_expert_rating: Minimum acceptable expert review score (1-5)
            require_human_approval: Whether human approval is required
            max_iterations: Maximum extract-review-iterate cycles
        """
        self.inputs_dir = Path(inputs_dir)
        self.outputs_dir = Path(outputs_dir)
        self.minimum_expert_rating = minimum_expert_rating
        self.require_human_approval = require_human_approval
        self.max_iterations = max_iterations
        
        # Create output directories
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        (self.outputs_dir / "structured").mkdir(exist_ok=True)
        (self.outputs_dir / "reviews").mkdir(exist_ok=True)
        
    # ========================================================================
    # STEP 1: Collect Artifacts
    # ========================================================================
    
    def step_1_collect_artifacts(self) -> Dict[str, List[Path]]:
        """
        Collect all artifacts from inputs directory.
        
        Returns:
            Dictionary mapping artifact type to list of file paths
        """
        print("\n=== STEP 1: Collect Artifacts ===")
        
        artifacts = {
            "papers": list((self.inputs_dir / "papers").glob("*.pdf")),
            "talks": list((self.inputs_dir / "transcripts").glob("*.txt")),
            "repositories": list((self.inputs_dir / "repositories").glob("*"))
        }
        
        # Filter to directories for repos
        artifacts["repositories"] = [
            p for p in artifacts["repositories"] if p.is_dir()
        ]
        
        print(f"Found {len(artifacts['papers'])} papers")
        print(f"Found {len(artifacts['talks'])} talk transcripts")
        print(f"Found {len(artifacts['repositories'])} repositories")
        
        return artifacts
    
    # ========================================================================
    # STEP 2: Define Projects
    # ========================================================================
    
    def step_2_define_projects(
        self,
        artifacts: Dict[str, List[Path]]
    ) -> Dict[str, Dict[str, List[Path]]]:
        """
        Group artifacts into projects.
        
        For POC v1, we use simple heuristic: artifacts with same name prefix
        belong to the same project.
        
        Args:
            artifacts: Dictionary of artifact type to file paths
            
        Returns:
            Dictionary mapping project name to artifact groups
        """
        print("\n=== STEP 2: Define Projects ===")
        
        projects = {}
        
        # Simple heuristic: group by name prefix
        # Example: "project-a_paper.pdf", "project-a_transcript.txt" -> "project-a"
        
        for artifact_type, files in artifacts.items():
            for file_path in files:
                # Extract project name (everything before first underscore or hyphen)
                name = file_path.stem
                project_name = name.split('_')[0].split('-')[0]
                
                if project_name not in projects:
                    projects[project_name] = {
                        "papers": [],
                        "talks": [],
                        "repositories": []
                    }
                
                projects[project_name][artifact_type].append(file_path)
        
        print(f"Identified {len(projects)} projects:")
        for project_name, project_artifacts in projects.items():
            total = sum(len(v) for v in project_artifacts.values())
            print(f"  - {project_name}: {total} artifacts")
        
        return projects
    
    # ========================================================================
    # STEP 3: Assign Agents
    # ========================================================================
    
    def step_3_assign_agents(self) -> Dict[str, Any]:
        """
        Create specialized extraction agents.
        
        Returns:
            Dictionary mapping artifact type to agent instance
        """
        print("\n=== STEP 3: Assign Agents ===")
        
        agents = {
            "papers": ModernPaperAgent(),
            "talks": ModernTalkAgent(),
            "repositories": ModernRepositoryAgent()
        }
        
        print("Created specialized agents:")
        print("  - ModernPaperAgent for research papers")
        print("  - ModernTalkAgent for talk transcripts")
        print("  - ModernRepositoryAgent for code/model repos")
        
        return agents
    
    # ========================================================================
    # STEP 4: Extract Knowledge
    # ========================================================================
    
    async def step_4_extract_knowledge(
        self,
        projects: Dict[str, Dict[str, List[Path]]],
        agents: Dict[str, Any]
    ) -> Dict[str, List[BaseKnowledgeArtifact]]:
        """
        Run extraction agents on all artifacts.
        
        Args:
            projects: Project definitions with artifacts
            agents: Dictionary of agent instances
            
        Returns:
            Dictionary mapping project name to list of extracted knowledge artifacts
        """
        print("\n=== STEP 4: Extract Knowledge ===")
        
        all_extractions = {}
        
        for project_name, project_artifacts in projects.items():
            print(f"\nProcessing project: {project_name}")
            project_extractions = []
            
            # Process papers
            for paper_path in project_artifacts["papers"]:
                print(f"  Extracting: {paper_path.name}")
                with open(paper_path, "rb") as f:
                    content = f.read()
                
                result = await agents["papers"].extract(content)
                project_extractions.append(result)
            
            # Process talks
            for talk_path in project_artifacts["talks"]:
                print(f"  Extracting: {talk_path.name}")
                with open(talk_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                result = await agents["talks"].extract(content)
                project_extractions.append(result)
            
            # Process repositories
            for repo_path in project_artifacts["repositories"]:
                print(f"  Extracting: {repo_path.name}")
                result = await agents["repositories"].extract(repo_path)
                project_extractions.append(result)
            
            all_extractions[project_name] = project_extractions
            print(f"  Extracted {len(project_extractions)} artifacts for {project_name}")
        
        return all_extractions
    
    # ========================================================================
    # STEP 5: Expert Review
    # ========================================================================
    
    async def step_5_expert_review(
        self,
        extractions: Dict[str, List[BaseKnowledgeArtifact]]
    ) -> Dict[str, List[ExpertReview]]:
        """
        Run expert review on all extractions.
        
        Args:
            extractions: Extracted knowledge artifacts by project
            
        Returns:
            Dictionary mapping project name to list of expert reviews
        """
        print("\n=== STEP 5: Expert Review ===")
        
        all_reviews = {}
        
        for project_name, artifacts in extractions.items():
            print(f"\nReviewing project: {project_name}")
            project_reviews = []
            
            for artifact in artifacts:
                print(f"  Reviewing: {artifact.title}")
                review = await run_expert_review(artifact)
                project_reviews.append(review)
                
                # Save review
                review_path = (
                    self.outputs_dir / "reviews" / 
                    f"{project_name}_{artifact.title}_review.json"
                )
                with open(review_path, "w") as f:
                    json.dump(review.to_dict(), f, indent=2)
                
                print(f"    Overall Score: {review.overall_score:.1f}/5.0")
            
            all_reviews[project_name] = project_reviews
        
        return all_reviews
    
    # ========================================================================
    # STEP 6: Iterate if Needed
    # ========================================================================
    
    async def step_6_iterate(
        self,
        extractions: Dict[str, List[BaseKnowledgeArtifact]],
        reviews: Dict[str, List[ExpertReview]],
        agents: Dict[str, Any],
        iteration: int
    ) -> Dict[str, List[BaseKnowledgeArtifact]]:
        """
        Re-extract artifacts that didn't meet quality threshold.
        
        Args:
            extractions: Current extractions
            reviews: Expert reviews
            agents: Agent instances
            iteration: Current iteration number
            
        Returns:
            Updated extractions after iteration
        """
        print(f"\n=== STEP 6: Iterate (Round {iteration}) ===")
        
        updated_extractions = {}
        
        for project_name in extractions.keys():
            artifacts = extractions[project_name]
            project_reviews = reviews[project_name]
            updated_artifacts = []
            
            for artifact, review in zip(artifacts, project_reviews):
                if review.overall_score >= self.minimum_expert_rating:
                    print(f"  ✓ {artifact.title} passed (score: {review.overall_score:.1f})")
                    updated_artifacts.append(artifact)
                else:
                    print(f"  ✗ {artifact.title} needs improvement (score: {review.overall_score:.1f})")
                    print(f"    Weakest dimension: {review.get_weakest_dimension()}")
                    
                    # Re-extract with feedback
                    # In real implementation, would pass review feedback to agent
                    # For now, just re-run extraction
                    print(f"    Re-extracting with feedback...")
                    # TODO: Implement re-extraction with feedback
                    updated_artifacts.append(artifact)  # Placeholder
            
            updated_extractions[project_name] = updated_artifacts
        
        return updated_extractions
    
    # ========================================================================
    # STEP 7: Output & Stretch Goal
    # ========================================================================
    
    async def step_7_output(
        self,
        extractions: Dict[str, List[BaseKnowledgeArtifact]],
        compile_projects: bool = False
    ) -> Dict[str, Any]:
        """
        Save extractions and optionally compile project-level knowledge.
        
        Args:
            extractions: Final extractions by project
            compile_projects: Whether to run project-level compilation
            
        Returns:
            Dictionary with output paths and compilation results
        """
        print("\n=== STEP 7: Output ===")
        
        results = {
            "extractions": {},
            "compilations": {}
        }
        
        # Save individual extractions
        for project_name, artifacts in extractions.items():
            project_dir = self.outputs_dir / "structured" / project_name
            project_dir.mkdir(exist_ok=True)
            
            for artifact in artifacts:
                output_path = project_dir / f"{artifact.title}.json"
                with open(output_path, "w") as f:
                    json.dump(artifact.to_dict(), f, indent=2)
                
                print(f"  Saved: {output_path}")
            
            results["extractions"][project_name] = [
                str(project_dir / f"{a.title}.json") for a in artifacts
            ]
        
        # STRETCH GOAL: Project-level compilation
        if compile_projects:
            print("\n=== STRETCH: Compiling Project-Level Knowledge ===")
            
            for project_name, artifacts in extractions.items():
                print(f"\nCompiling project: {project_name}")
                
                compilation = await compile_project_knowledge(
                    project_name=project_name,
                    artifacts=artifacts
                )
                
                # Save compilation
                compilation_path = (
                    self.outputs_dir / "structured" / 
                    f"{project_name}_COMPILED.json"
                )
                with open(compilation_path, "w") as f:
                    json.dump(compilation, f, indent=2)
                
                print(f"  Saved compilation: {compilation_path}")
                results["compilations"][project_name] = str(compilation_path)
        
        return results
    
    # ========================================================================
    # MAIN WORKFLOW
    # ========================================================================
    
    async def run_poc_workflow(
        self,
        compile_projects: bool = False
    ) -> Dict[str, Any]:
        """
        Execute complete POC workflow.
        
        Args:
            compile_projects: Whether to run project compilation (stretch goal)
            
        Returns:
            Dictionary with workflow results and output paths
        """
        print("\n" + "="*60)
        print("POC WORKFLOW - Knowledge Extraction POC v1")
        print("="*60)
        
        # Step 1: Collect artifacts
        artifacts = self.step_1_collect_artifacts()
        
        # Step 2: Define projects
        projects = self.step_2_define_projects(artifacts)
        
        # Step 3: Assign agents
        agents = self.step_3_assign_agents()
        
        # Step 4-6: Extract-Review-Iterate loop
        extractions = await self.step_4_extract_knowledge(projects, agents)
        
        iteration = 1
        while iteration <= self.max_iterations:
            reviews = await self.step_5_expert_review(extractions)
            
            # Check if all artifacts meet threshold
            all_passed = all(
                review.overall_score >= self.minimum_expert_rating
                for project_reviews in reviews.values()
                for review in project_reviews
            )
            
            if all_passed or iteration == self.max_iterations:
                print(f"\n{'='*60}")
                if all_passed:
                    print("All artifacts passed expert review!")
                else:
                    print(f"Max iterations ({self.max_iterations}) reached.")
                print(f"{'='*60}")
                break
            
            # Iterate
            extractions = await self.step_6_iterate(
                extractions, reviews, agents, iteration
            )
            iteration += 1
        
        # Step 7: Output
        results = await self.step_7_output(extractions, compile_projects)
        
        print("\n" + "="*60)
        print("POC WORKFLOW COMPLETE")
        print("="*60)
        
        return {
            "projects": list(projects.keys()),
            "total_artifacts": sum(len(v) for v in extractions.values()),
            "iterations": iteration,
            "output_paths": results
        }


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def run_poc_for_project(
    inputs_dir: str = "inputs",
    outputs_dir: str = "outputs",
    minimum_expert_rating: float = 3.0,
    compile_projects: bool = False
) -> Dict[str, Any]:
    """
    Run complete POC workflow with default settings.
    
    Args:
        inputs_dir: Directory with input artifacts
        outputs_dir: Directory for outputs
        minimum_expert_rating: Minimum acceptable review score (1-5)
        compile_projects: Whether to compile project-level knowledge
        
    Returns:
        Workflow results
    """
    workflow = POCWorkflowManager(
        inputs_dir=Path(inputs_dir),
        outputs_dir=Path(outputs_dir),
        minimum_expert_rating=minimum_expert_rating
    )
    
    return await workflow.run_poc_workflow(compile_projects=compile_projects)
