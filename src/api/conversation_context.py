"""
Conversation context tracking for multi-turn dialogues.
Maintains state across conversation turns for contextual routing and responses.
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationContext:
    """Tracks conversation state across multiple turns."""
    
    # User interests and preferences
    selected_categories: Set[str] = field(default_factory=set)
    selected_researchers: Set[str] = field(default_factory=set)
    interests_keywords: Set[str] = field(default_factory=set)
    equipment_filters: Set[str] = field(default_factory=set)
    
    # Conversation flow state
    conversation_stage: str = "welcome"  # welcome, ask_interests, show_results, project_detail
    last_results: List[Dict[str, Any]] = field(default_factory=list)
    viewed_projects: Set[str] = field(default_factory=set)
    current_project_id: Optional[str] = None
    
    # Metadata
    turn_count: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dict for serialization."""
        return {
            "selected_categories": list(self.selected_categories),
            "selected_researchers": list(self.selected_researchers),
            "interests_keywords": list(self.interests_keywords),
            "equipment_filters": list(self.equipment_filters),
            "conversation_stage": self.conversation_stage,
            "last_results_count": len(self.last_results),
            "viewed_projects": list(self.viewed_projects),
            "current_project_id": self.current_project_id,
            "turn_count": self.turn_count,
        }
    
    def add_category(self, category: str) -> None:
        """Add a research category interest."""
        self.selected_categories.add(category.lower())
    
    def add_researcher(self, name: str) -> None:
        """Add a researcher interest."""
        self.selected_researchers.add(name.lower())
    
    def add_keyword(self, keyword: str) -> None:
        """Add an interest keyword."""
        self.interests_keywords.add(keyword.lower())
    
    def add_equipment_filter(self, equipment: str) -> None:
        """Add an equipment filter."""
        self.equipment_filters.add(equipment.lower())
    
    def set_results(self, results: List[Dict[str, Any]]) -> None:
        """Update the last query results."""
        self.last_results = results
    
    def mark_project_viewed(self, project_id: str) -> None:
        """Record that user viewed a project."""
        self.viewed_projects.add(project_id)
        self.current_project_id = project_id
    
    def advance_turn(self) -> None:
        """Increment turn counter."""
        self.turn_count += 1
    
    def has_interests(self) -> bool:
        """Check if user has expressed any interests."""
        return bool(
            self.selected_categories 
            or self.selected_researchers 
            or self.interests_keywords
        )
    
    def get_summary(self) -> str:
        """Get a human-readable summary of current context."""
        parts = []
        if self.selected_categories:
            parts.append(f"Categories: {', '.join(sorted(self.selected_categories))}")
        if self.interests_keywords:
            parts.append(f"Keywords: {', '.join(sorted(self.interests_keywords))}")
        if self.selected_researchers:
            parts.append(f"Researchers: {', '.join(sorted(self.selected_researchers))}")
        if self.equipment_filters:
            parts.append(f"Equipment: {', '.join(sorted(self.equipment_filters))}")
        return " | ".join(parts) if parts else "No preferences set"


def extract_context_from_messages(messages: List[Dict[str, str]]) -> ConversationContext:
    """
    Extract conversation context from message history.
    Analyzes previous turns to rebuild context state.
    """
    context = ConversationContext()
    
    # Scan messages for patterns indicating user interests
    for msg in messages:
        if msg.get("role") != "user":
            continue
            
        content = msg.get("content", "").lower()
        
        # Detect category selections
        categories = {
            "artificial intelligence": ["ai", "artificial intelligence", "machine learning", "ml"],
            "systems": ["systems", "networking", "distributed"],
            "hci": ["human-computer", "hci", "interaction", "visualization"],
            "security": ["security", "privacy", "encryption"],
            "data science": ["data science", "analytics", "analytics"],
        }
        
        for category, keywords in categories.items():
            if any(kw in content for kw in keywords):
                context.add_category(category)
        
        # Detect equipment preferences
        equipment_keywords = {
            "large display": ["large display", "display"],
            "monitor": ["monitor", "27\""],
            "recording": ["recording", "video"],
            "technician": ["technician", "tech support"],
        }
        
        for equipment, keywords in equipment_keywords.items():
            if any(kw in content for kw in keywords):
                context.add_equipment_filter(equipment)
    
    return context
