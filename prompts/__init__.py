"""LLM prompt engineering for knowledge extraction"""
from .paper_prompts import get_paper_prompts
from .talk_prompts import get_talk_prompts
from .repository_prompts import get_repository_prompts

__all__ = [
    "get_paper_prompts",
    "get_talk_prompts",
    "get_repository_prompts",
]
