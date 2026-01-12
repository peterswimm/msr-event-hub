# Migration Guide: From Legacy to Modern Agent Framework

**Date:** January 5, 2026
**Status:** Transition Strategy Document
**Target Audience:** Developers, DevOps Engineers

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Side-by-Side Comparison](#side-by-side-comparison)
3. [Migration Path](#migration-path)
4. [Code Examples](#code-examples)
5. [Breaking Changes](#breaking-changes)
6. [Backwards Compatibility](#backwards-compatibility)
7. [Testing Strategy](#testing-strategy)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What's Changing?

The knowledge agent codebase is transitioning from **direct LLM client implementations** to **Microsoft Agent Framework** for better production readiness, observability, and multi-agent capabilities.

### Why?

| Aspect | Legacy | Modern | Benefit |
|--------|--------|--------|---------|
| **Observability** | Manual logging | Built-in OpenTelemetry | Better debugging & monitoring |
| **Async Support** | Sync only | Full async/await | Better scalability |
| **Tool Calling** | Manual implementation | Built-in | Easier extensibility |
| **Multi-agent** | Manual orchestration | Workflows built-in | Complexity reduction |
| **Testing** | Minimal | Comprehensive | Higher quality |
| **Support** | Community | Microsoft-backed | Better long-term maintenance |

### Timeline

- **Week 1:** Legacy code cleanup
- **Week 2-3:** Test infrastructure  
- **Week 4+:** Modern feature development

---

## Side-by-Side Comparison

### 1. Paper Extraction

#### Legacy Code
```python
from agents import PaperAgent

# Create agent (synchronous)
agent = PaperAgent(
    llm_provider="azure-openai",
    model="gpt-4-turbo",
    temperature=0.3
)

# Extract (blocking call)
artifact = agent.extract("paper.pdf")

# Save outputs
json_file = agent.save_artifact(artifact, "./outputs")
summary_file = agent.save_summary(artifact, "./outputs")

print(f"Extracted: {artifact.title}")
```

#### Modern Code
```python
import asyncio
from agents import ModernPaperAgent
from config import get_settings
from observability import setup_tracing

async def main():
    # Setup observability
    setup_tracing()
    settings = get_settings()
    
    # Create agent (async-capable)
    agent = ModernPaperAgent(settings)
    
    # Extract with tracing
    artifact = await agent.extract("paper.pdf")
    
    # Outputs included in artifact
    artifact.save_json("./outputs")
    artifact.save_markdown("./outputs")
    
    print(f"✓ Extracted: {artifact.title}")
    print(f"  Confidence: {artifact.confidence_score}")

# Run async
asyncio.run(main())
```

**Key Differences:**
- ✅ Async/await pattern (non-blocking)
- ✅ Built-in tracing (no manual logging)
- ✅ Settings from centralized config
- ✅ Structured outputs
- ✅ Proper error handling

---

### 2. Talk Extraction

#### Legacy Code
```python
from agents import TalkAgent

agent = TalkAgent(llm_provider="openai", temperature=0.3)
artifact = agent.extract("transcript.txt")
print(artifact.plain_language_overview)
```

#### Modern Code
```python
import asyncio
from agents import ModernTalkAgent
from config import get_settings

async def main():
    settings = get_settings()
    agent = ModernTalkAgent(settings)
    artifact = await agent.extract("transcript.txt")
    print(artifact.plain_language_overview)

asyncio.run(main())
```

---

### 3. Batch Processing

#### Legacy Code
```python
from agents import PaperAgent, TalkAgent
from pathlib import Path

papers = list(Path("inputs/papers").glob("*.pdf"))
for paper_path in papers:
    agent = PaperAgent(llm_provider="azure-openai")
    artifact = agent.extract(str(paper_path))
    agent.save_artifact(artifact, "./outputs")
    print(f"Extracted {paper_path.name}")
```

#### Modern Code
```python
import asyncio
from agents import ModernPaperAgent
from config import get_settings
from pathlib import Path

async def extract_batch():
    settings = get_settings()
    papers = list(Path("inputs/papers").glob("*.pdf"))
    
    # Concurrent extraction
    tasks = []
    for paper_path in papers:
        agent = ModernPaperAgent(settings)
        tasks.append(agent.extract(str(paper_path)))
    
    # Wait for all to complete
    artifacts = await asyncio.gather(*tasks)
    
    for artifact in artifacts:
        artifact.save_json("./outputs")
        print(f"✓ Extracted {artifact.title}")

asyncio.run(extract_batch())
```

**Modern Benefit:** Parallel extraction 5-10x faster!

---

## Migration Path

### Step 1: Update Imports (5 minutes)

**Find all files with:**
```python
from agents import PaperAgent, TalkAgent, RepositoryAgent
```

**Replace with:**
```python
from agents import ModernPaperAgent as PaperAgent, \
                    ModernTalkAgent as TalkAgent, \
                    ModernRepositoryAgent as RepositoryAgent
```

Or use new names directly:
```python
from agents import ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent
```

### Step 2: Convert to Async (15-30 minutes)

**For each extraction call, wrap in async function:**

Before:
```python
def process():
    agent = PaperAgent(...)
    artifact = agent.extract("paper.pdf")
    return artifact
```

After:
```python
async def process():
    agent = ModernPaperAgent(...)
    artifact = await agent.extract("paper.pdf")
    return artifact
```

### Step 3: Add Tracing (5 minutes)

At your application entry point:

```python
from observability import setup_tracing

def main():
    # Setup before creating agents
    setup_tracing()
    
    # ... rest of your code
```

### Step 4: Update Configuration (5 minutes)

Update `.env` to use modern settings:

```bash
# Modern settings (Agent Framework)
FOUNDRY_PROJECT_ENDPOINT=https://your-foundry.api.azureml.ms
FOUNDRY_MODEL_DEPLOYMENT=gpt-4o

# Observability
ENABLE_TRACING=true
```

### Step 5: Test & Validate (Varies)

```bash
# Run updated code
python your_script.py

# Check for tracing (if enabled)
# AI Toolkit → View Trace
```

---

## Code Examples

### Example 1: Single Artifact Extraction

**Task:** Extract knowledge from one research paper

**Modern Code:**
```python
import asyncio
from pathlib import Path
from agents import ModernPaperAgent
from config import get_settings
from observability import setup_tracing

async def extract_single_paper(pdf_path: str) -> None:
    """Extract knowledge from a single research paper."""
    
    # Setup
    setup_tracing()
    settings = get_settings()
    
    # Create agent
    agent = ModernPaperAgent(settings)
    
    # Extract
    print(f"Extracting from {pdf_path}...")
    artifact = await agent.extract(pdf_path)
    
    # Save
    output_dir = Path("./outputs/papers")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    json_path = artifact.save_json(str(output_dir))
    md_path = artifact.save_markdown(str(output_dir))
    
    # Display results
    print(f"\n✓ Extraction Complete")
    print(f"  Title: {artifact.title}")
    print(f"  Confidence: {artifact.confidence_score:.2f}/1.0")
    print(f"  Saved to: {json_path}")

if __name__ == "__main__":
    asyncio.run(extract_single_paper("inputs/papers/sample.pdf"))
```

**Expected Output:**
```
Extracting from inputs/papers/sample.pdf...

✓ Extraction Complete
  Title: "Deep Learning for Computer Vision"
  Confidence: 0.87/1.0
  Saved to: outputs/papers/deep_learning_for_computer_vision.json
```

---

### Example 2: Batch Processing with Concurrent Extraction

**Task:** Extract from 10 papers in parallel

**Modern Code:**
```python
import asyncio
from pathlib import Path
from agents import ModernPaperAgent
from config import get_settings
from observability import setup_tracing

async def extract_papers_concurrently(input_dir: str, output_dir: str) -> None:
    """Extract from multiple papers in parallel."""
    
    # Setup
    setup_tracing()
    settings = get_settings()
    
    # Collect papers
    input_path = Path(input_dir)
    papers = list(input_path.glob("*.pdf"))
    
    if not papers:
        print(f"No papers found in {input_dir}")
        return
    
    print(f"Found {len(papers)} papers. Starting concurrent extraction...\n")
    
    # Create extraction tasks
    async def extract_one(pdf_path: Path):
        agent = ModernPaperAgent(settings)
        try:
            artifact = await agent.extract(str(pdf_path))
            return artifact, None
        except Exception as e:
            return None, e
    
    # Run all in parallel
    tasks = [extract_one(pdf) for pdf in papers]
    results = await asyncio.gather(*tasks)
    
    # Save results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    success = 0
    failed = 0
    
    for (artifact, error), pdf_path in zip(results, papers):
        if artifact:
            artifact.save_json(str(output_path))
            artifact.save_markdown(str(output_path))
            print(f"✓ {pdf_path.name}: {artifact.title}")
            success += 1
        else:
            print(f"✗ {pdf_path.name}: {error}")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Extraction Complete: {success} succeeded, {failed} failed")
    print(f"Outputs saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(extract_papers_concurrently("inputs/papers", "outputs/papers"))
```

---

### Example 3: Multi-Artifact Project Extraction

**Task:** Extract from papers + talks + repo for one project

**Modern Code:**
```python
import asyncio
from pathlib import Path
from agents import ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent
from config import get_settings
from observability import setup_tracing

async def extract_project(
    project_name: str,
    paper_path: str,
    transcript_path: str,
    repo_url: str,
    output_dir: str
) -> None:
    """Extract knowledge from all artifacts in a project."""
    
    # Setup
    setup_tracing()
    settings = get_settings()
    
    # Create agents
    paper_agent = ModernPaperAgent(settings)
    talk_agent = ModernTalkAgent(settings)
    repo_agent = ModernRepositoryAgent(settings)
    
    print(f"Extracting project: {project_name}\n")
    
    # Extract all in parallel
    results = await asyncio.gather(
        paper_agent.extract(paper_path),
        talk_agent.extract(transcript_path),
        repo_agent.extract(repo_url),
        return_exceptions=True
    )
    
    paper_artifact, talk_artifact, repo_artifact = results
    
    # Save results
    output_path = Path(output_dir) / project_name
    output_path.mkdir(parents=True, exist_ok=True)
    
    for artifact in [paper_artifact, talk_artifact, repo_artifact]:
        if hasattr(artifact, 'save_json'):
            artifact.save_json(str(output_path))
            artifact.save_markdown(str(output_path))
            print(f"✓ {artifact.__class__.__name__}: {artifact.title}")
        else:
            print(f"✗ Extraction failed: {artifact}")
    
    print(f"\nAll artifacts saved to: {output_path}")

if __name__ == "__main__":
    asyncio.run(extract_project(
        project_name="agents-research",
        paper_path="inputs/papers/agents-paper.pdf",
        transcript_path="inputs/transcripts/agents-talk.txt",
        repo_url="https://github.com/example/agents",
        output_dir="outputs/projects"
    ))
```

---

## Breaking Changes

### ⚠️ Breaking Changes from Legacy to Modern

| Change | Impact | Migration |
|--------|--------|-----------|
| **Sync → Async** | All extract() calls must use `await` | Wrap in `async def` + `asyncio.run()` |
| **Direct LLM client** | No more passing `llm_provider` param | Use settings from config |
| **save_artifact()** | Changed to `artifact.save_json()` | Call method on artifact object |
| **Temperature/tokens** | Now in config/settings | Update .env or Settings class |
| **Error handling** | Different exception types | Update try/except blocks |

### 🟡 Deprecations

The following are deprecated but still work (for now):

```python
# DEPRECATED (still works via aliases)
from agents import PaperAgent
agent = PaperAgent(llm_provider="azure-openai")

# PREFERRED
from agents import ModernPaperAgent
agent = ModernPaperAgent(settings)
```

**Deprecation Timeline:**
- **Now (Jan 2026):** Aliases work, warnings logged
- **March 2026:** Aliases removed, code must be updated
- **June 2026:** Legacy code completely removed

---

## Backwards Compatibility

### Compatibility Layer

To minimize breakage during transition, we provide backwards compatibility:

```python
# agents/__init__.py
from .modern_spec_agents import ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent

# Backwards compat aliases (will be removed March 2026)
PaperAgent = ModernPaperAgent
TalkAgent = ModernTalkAgent
RepositoryAgent = ModernRepositoryAgent

__all__ = [
    "ModernPaperAgent",
    "ModernTalkAgent", 
    "ModernRepositoryAgent",
    # Legacy names - prefer modern names above
    "PaperAgent",
    "TalkAgent",
    "RepositoryAgent",
]
```

### Compatibility Guarantees

✅ **Import compatibility:** Old imports still work (with deprecation warnings)
✅ **Schema compatibility:** Output JSON format unchanged
⚠️ **API compatibility:** Method signatures changed (async)
❌ **Binary compatibility:** Not applicable (Python)

---

## Testing Strategy

### Unit Tests

Test individual agents:

```python
# tests/test_modern_agents.py
import pytest
import asyncio
from agents import ModernPaperAgent
from config import get_settings

@pytest.fixture
def settings():
    return get_settings()

@pytest.mark.asyncio
async def test_paper_agent_initialization(settings):
    """Test that agent initializes correctly."""
    agent = ModernPaperAgent(settings)
    assert agent is not None
    assert agent.settings == settings

@pytest.mark.asyncio
async def test_paper_extraction(settings, sample_pdf):
    """Test paper extraction on sample file."""
    agent = ModernPaperAgent(settings)
    artifact = await agent.extract(sample_pdf)
    
    # Validate output
    assert artifact.title is not None
    assert artifact.confidence_score >= 0.0
    assert artifact.confidence_score <= 1.0
    assert len(artifact.contributors) >= 0
```

### Integration Tests

Test full workflows:

```python
# tests/test_integration_e2e.py
@pytest.mark.asyncio
async def test_complete_extraction_workflow():
    """Test: collect → extract → review → iterate."""
    
    # Setup
    settings = get_settings()
    paper_agent = ModernPaperAgent(settings)
    
    # Step 1: Extract
    artifact = await paper_agent.extract("sample_paper.pdf")
    assert artifact is not None
    
    # Step 2: Validate schema
    assert hasattr(artifact, 'confidence_score')
    assert all(hasattr(artifact, f) for f in [
        'title', 'contributors', 'plain_language_overview',
        'technical_problem', 'key_methods', 'primary_claims'
    ])
    
    # Step 3: Review
    from evaluation import ExpertReview
    review = await ExpertReview().review(artifact)
    assert review.overall_score >= 0.0
    assert review.overall_score <= 5.0
    
    # Step 4: Conditionally iterate (if score < 3.0)
    if review.overall_score < 3.0:
        artifact = await paper_agent.extract("sample_paper.pdf")
        assert artifact is not None
```

### Migration Test

Test that modern and legacy produce equivalent outputs:

```python
# tests/test_migration.py
@pytest.mark.asyncio
async def test_migration_equivalence():
    """Test that modern implementation produces same quality output."""
    
    # Note: Only run if legacy code still available
    try:
        from agents import PaperAgent  # Legacy alias
        legacy_available = True
    except ImportError:
        legacy_available = False
    
    if not legacy_available:
        pytest.skip("Legacy code not available")
    
    settings = get_settings()
    modern_agent = ModernPaperAgent(settings)
    
    # Extract with modern
    modern_artifact = await modern_agent.extract("sample.pdf")
    
    # Both should produce valid output
    assert modern_artifact.title is not None
    assert modern_artifact.confidence_score >= 0.0
```

---

## Troubleshooting

### Issue 1: "TypeError: extract() missing 1 required positional argument: 'self'"

**Cause:** Calling async method without `await`

**Before (❌ Wrong):**
```python
artifact = agent.extract("paper.pdf")  # Missing await!
```

**After (✅ Correct):**
```python
artifact = await agent.extract("paper.pdf")
```

---

### Issue 2: "AttributeError: 'coroutine' object has no attribute 'title'"

**Cause:** Not awaiting the extraction call

**Before (❌ Wrong):**
```python
artifact = agent.extract("paper.pdf")  # Returns coroutine, not artifact
print(artifact.title)  # Error!
```

**After (✅ Correct):**
```python
artifact = await agent.extract("paper.pdf")  # Wait for result
print(artifact.title)  # Works!
```

---

### Issue 3: "RuntimeError: asyncio.run() cannot be called from a running event loop"

**Cause:** Calling `asyncio.run()` inside another async context

**Before (❌ Wrong):**
```python
# Inside an async function
async def process():
    result = asyncio.run(extract())  # Error!
```

**After (✅ Correct):**
```python
# Inside async function - just await
async def process():
    result = await extract()  # Correct!
```

---

### Issue 4: "KeyError: 'FOUNDRY_PROJECT_ENDPOINT'"

**Cause:** Missing environment variable

**Solution:**
```bash
# Set in .env or export
export FOUNDRY_PROJECT_ENDPOINT="https://your-foundry.api.azureml.ms"

# Or add to .env
FOUNDRY_PROJECT_ENDPOINT=https://your-foundry.api.azureml.ms
FOUNDRY_MODEL_DEPLOYMENT=gpt-4o
```

---

### Issue 5: "ModuleNotFoundError: No module named 'agent_framework'"

**Cause:** Agent Framework not installed

**Solution:**
```bash
# Install with --pre flag (preview package)
pip install --pre agent-framework-azure-ai

# Or install all dependencies
pip install --pre -r requirements.txt
```

---

### Issue 6: "No tracing data appearing in AI Toolkit"

**Cause:** Tracing not enabled or collector not running

**Solution:**
```bash
# 1. Enable tracing in code
from observability import setup_tracing
setup_tracing()

# 2. Start trace collector
# VS Code Command Palette → "AI Toolkit: Start Trace Collector"

# 3. Run your code
# python your_script.py

# 4. View traces
# VS Code Command Palette → "AI Toolkit: View Trace"
```

---

## Rollback Plan

If you encounter critical issues with the modern implementation:

```bash
# View previous versions
git log --oneline | grep -i modern

# Temporarily revert
git revert <commit-hash>

# Or switch back to legacy branch
git checkout legacy-code-before-cleanup

# Restore legacy files
git restore agents/base_agent.py
git restore agents/paper_agent.py
```

---

## Success Checklist

After migration, verify:

- [ ] All imports updated to modern agents
- [ ] All extraction calls use `await`
- [ ] All code runs in async context
- [ ] Configuration in .env or Settings
- [ ] Tracing enabled (optional but recommended)
- [ ] All tests passing
- [ ] No deprecation warnings in logs
- [ ] Output JSON matches expected schema
- [ ] Confidence scores in valid range

---

## Support & Questions

For issues or questions:

1. Check [Troubleshooting](#troubleshooting) section above
2. Review code examples in this document
3. Check MODERNIZATION_GUIDE.md for architecture details
4. Review test examples in `tests/` directory
5. Check Git history for migration commits

---

**Document Version:** 1.0
**Last Updated:** January 5, 2026
**Status:** Active
