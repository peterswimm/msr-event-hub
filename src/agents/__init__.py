"""Knowledge extraction agents

Modern implementations using Agent Framework.
Legacy implementations have been removed (base_agent.py, paper_agent.py, talk_agent.py, repository_agent.py).
Use ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent instead.
"""
from .modern_base_agent import ModernBaseAgent
from .modern_spec_agents import ModernPaperAgent, ModernTalkAgent, ModernRepositoryAgent

# Backwards compatibility aliases (deprecated, will be removed March 2026)
BaseKnowledgeAgent = ModernBaseAgent
PaperAgent = ModernPaperAgent
TalkAgent = ModernTalkAgent
RepositoryAgent = ModernRepositoryAgent

__all__ = [
    # Modern implementations (preferred)
    "ModernBaseAgent",
    "ModernPaperAgent",
    "ModernTalkAgent",
    "ModernRepositoryAgent",
    # Backwards compatibility aliases (deprecated)
    "BaseKnowledgeAgent",
    "PaperAgent",
    "TalkAgent",
    "RepositoryAgent",
]
