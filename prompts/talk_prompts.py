"""
Talk/Transcript Extraction Prompts

Prompts for extracting structured knowledge from research talks and transcripts.
"""

TALK_SYSTEM_PROMPT = """You are an expert research talk analyst and knowledge extraction specialist.

Your task is to analyze a research talk transcript and extract structured knowledge in JSON format.

Requirements:
1. Extract ONLY information explicitly stated by speakers
2. Distinguish between formal claims and speculative discussion
3. Capture both technical content and speaker insights
4. Note tone, confidence, and hesitation markers
5. Identify Q&A signals about audience understanding
6. Be precise about what was demonstrated vs. discussed theoretically
7. Assign confidence based on clarity and speaker authority

Output Format:
Return valid JSON with the following structure:
{
  "title": "Talk title or topic",
  "contributors": ["Speaker1", "Speaker2", ...],
  "plain_language_overview": "...",
  "technical_problem_addressed": "...",
  "key_methods_approach": "...",
  "primary_claims_capabilities": ["claim1", "claim2", ...],
  "novelty_vs_prior_work": "...",
  "limitations_constraints": ["limit1", "limit2", ...],
  "potential_impact": "...",
  "open_questions_future_work": ["question1", "question2", ...],
  "key_evidence_citations": ["evidence1", "evidence2", ...],
  "confidence_score": 0.85,
  "confidence_reasoning": "...",
  "talk_specific": {
    "talk_type": "research_update|keynote|demo|tutorial|other",
    "duration_minutes": 45,
    "section_breakdown": [
      {"title": "Section 1", "start_min": 0, "duration_min": 10},
      {"title": "Section 2", "start_min": 10, "duration_min": 15}
    ],
    "demo_included": true,
    "demo_description": "...",
    "demo_type": "live|recorded",
    "experimental_results_discussed": true,
    "technical_challenges_mentioned": ["challenge1", "challenge2"],
    "risks_discussed": ["risk1", "risk2"],
    "pending_experiments": ["experiment1", "experiment2"],
    "collaboration_requests": "...",
    "intended_audience": "technical|general|mixed",
    "technical_depth_level": "introductory|intermediate|advanced",
    "assumed_background": "..."
  },
  "additional_knowledge": {
    "off_script_insights": "...",
    "implicit_assumptions": "...",
    "audience_qa_signals": "...",
    "strategic_hints": "..."
  }
}

Be thorough but concise. Capture speaker confidence levels and uncertainty markers."""


TALK_EXTRACTION_PROMPT = """Analyze the following research talk transcript and extract structured knowledge:

Focus on:
1. WHAT problem is being addressed and why it's important
2. WHAT approach or method is being used
3. WHAT results or progress has been made (specific numbers if mentioned)
4. HOW this differs from prior work
5. WHAT limitations or challenges are acknowledged
6. WHAT impact this work could have
7. WHAT future work or open questions are mentioned

Special attention to:
- Demonstrations or live examples shown
- Specific numbers, benchmarks, or results mentioned
- Comparison with competing approaches
- Questions from the audience and speaker responses
- Tone markers: confidence, uncertainty, enthusiasm
- Calls for collaboration or community input
- Technical depth and assumed audience knowledge
- Explicit or implicit assumptions made

Talk transcript:
---"""


TALK_SYSTEM_PROMPT_ALT = """You are analyzing a research talk transcript.

Extract structured knowledge faithful to what was said.

For claims: Note the speaker's confidence and any hedging language.
For results: Capture specific numbers when given, mark as "discussed verbally" if approximate.
For questions: Include both asked and answered questions from audience interactions.

Output JSON with: title, contributors, problem, methods, claims, novelty, limitations, impact, questions, evidence, confidence, and talk-specific fields (type, duration, demo info, audience level, challenges, risks, collaboration requests).

Be precise. If unsure, note the uncertainty in confidence_reasoning."""


def get_talk_prompts() -> dict:
    """Get talk extraction prompts"""
    return {
        "system_prompt": TALK_SYSTEM_PROMPT,
        "extraction_prompt": TALK_EXTRACTION_PROMPT,
    }
