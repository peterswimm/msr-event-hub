"""
POC Runner - Knowledge Extraction POC v1

Main entry point for running the complete POC workflow.
Implements all 7 steps from the specification.

Usage:
    python poc_runner.py
    python poc_runner.py --compile  # Include project compilation
    python poc_runner.py --inputs custom/path --outputs results/
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

from src.workflows.poc_workflow import run_poc_for_project
from src.config.settings import Settings


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Knowledge Extraction POC v1 - Run complete workflow"
    )
    
    parser.add_argument(
        "--inputs",
        type=str,
        default="inputs",
        help="Directory containing input artifacts (default: inputs/)"
    )
    
    parser.add_argument(
        "--outputs",
        type=str,
        default="outputs",
        help="Directory for output artifacts (default: outputs/)"
    )
    
    parser.add_argument(
        "--min-score",
        type=float,
        default=3.0,
        help="Minimum expert review score to pass (1-5, default: 3.0)"
    )
    
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Run project-level compilation (stretch goal)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=2,
        help="Maximum extract-review-iterate cycles (default: 2)"
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()
    
    print("\n" + "="*80)
    print("KNOWLEDGE EXTRACTION POC v1")
    print("="*80)
    print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nConfiguration:")
    print(f"  Inputs Directory:    {args.inputs}")
    print(f"  Outputs Directory:   {args.outputs}")
    print(f"  Minimum Score:       {args.min_score}/5.0")
    print(f"  Max Iterations:      {args.max_iterations}")
    print(f"  Project Compilation: {'Enabled' if args.compile else 'Disabled'}")
    print("="*80)
    
    # Validate inputs directory exists
    inputs_path = Path(args.inputs)
    if not inputs_path.exists():
        print(f"\n❌ ERROR: Inputs directory not found: {args.inputs}")
        print("\nExpected structure:")
        print("  inputs/")
        print("    papers/       # PDF files")
        print("    transcripts/  # TXT files")
        print("    repositories/ # Directory with code repos")
        sys.exit(1)
    
    try:
        # Run POC workflow
        results = await run_poc_for_project(
            inputs_dir=args.inputs,
            outputs_dir=args.outputs,
            minimum_expert_rating=args.min_score,
            compile_projects=args.compile
        )
        
        # Print summary
        print("\n" + "="*80)
        print("WORKFLOW SUMMARY")
        print("="*80)
        print(f"\nProjects Processed:  {len(results['projects'])}")
        print(f"Total Artifacts:     {results['total_artifacts']}")
        print(f"Iterations:          {results['iterations']}")
        print(f"\nOutput Locations:")
        print(f"  Structured Data: {args.outputs}/structured/")
        print(f"  Expert Reviews:  {args.outputs}/reviews/")
        
        if args.compile:
            print(f"  Compilations:    {args.outputs}/structured/*_COMPILED.json")
        
        print("\n✅ POC WORKFLOW COMPLETED SUCCESSFULLY")
        print("="*80)
        print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*80)
        print("❌ ERROR")
        print("="*80)
        print(f"\n{type(e).__name__}: {e}")
        print("\nWorkflow failed. Check logs for details.")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
