"""
Recommended Additional Intents for MSR Event Hub

These intents fill gaps in the current 15-intent system and handle common query patterns.
"""

# New intents to add to router_prompt.py INTENT_PATTERNS

ADDITIONAL_INTENT_PATTERNS = {
    # 16. Compare projects - "How does project A differ from project B?"
    "project_comparison": [
        r"\bcompare\b.*\bproject",
        r"\bdifference\s+between\b.*\bproject",
        r"\bhow\s+(do|does)\b.*\b(differ|compare)\b",
        r"\bproject\s+a\s+vs\s+project\s+b\b",
        r"\bsimilarities\s+and\s+differences\b",
        r"\bwhich\s+project\s+is\s+better\b"
    ],
    
    # 17. Recommendations - "What projects should I see based on my interests?"
    "personalized_recommendations": [
        r"\brecommend\b.*\bproject",
        r"\bsuggest\b.*\bproject",
        r"\bwhat\s+should\s+i\s+(see|visit|check\s+out)\b",
        r"\bbased\s+on\s+my\s+interest",
        r"\bprojects?\s+(for|about)\s+me\b",
        r"\bpersonalized\s+(list|suggestions?)\b",
        r"\bi'?m\s+interested\s+in\b"
    ],
    
    # 18. Trending/Popular - "What are the most popular projects?"
    "trending_popular": [
        r"\bmost\s+popular\b",
        r"\btrending\b",
        r"\bhot\s+topics?\b",
        r"\bmost\s+viewed\b",
        r"\bhighest\s+rated\b",
        r"\bbest\s+projects?\b",
        r"\btop\s+\d+\s+projects?\b",
        r"\bmust[-\s]see\b"
    ],
    
    # 19. Time-based queries - "What's happening now/next/today?"
    "time_based_schedule": [
        r"\b(what'?s|what\s+is)\s+(happening|on)\s+(now|next|today|tomorrow)\b",
        r"\bcurrent\s+(session|presentation|talk)\b",
        r"\bup\s+next\b",
        r"\bcoming\s+up\b",
        r"\bthis\s+(morning|afternoon|hour)\b",
        r"\bschedule\s+for\s+(today|tomorrow)\b",
        r"\bat\s+\d{1,2}:\d{2}\b"  # "What's at 2:30?"
    ],
    
    # 20. Collaboration/Networking - "I want to collaborate with..."
    "collaboration_networking": [
        r"\bcollaborat(e|ion)\b",
        r"\bpartner\b.*\bproject\b",
        r"\bwork\s+with\b",
        r"\bconnect\s+with\b",
        r"\bnetwork(ing)?\b",
        r"\bmeet\s+the\s+team\b",
        r"\bcontact\s+(info|information)\b",
        r"\bhow\s+to\s+reach\b"
    ],
    
    # 21. Prerequisites/Requirements - "What do I need to know before..."
    "prerequisites": [
        r"\bprerequisite[s]?\b",
        r"\brequirement[s]?\b.*\b(to\s+understand|for)\b",
        r"\bwhat\s+do\s+i\s+need\s+to\s+know\b",
        r"\bbackground\s+knowledge\b",
        r"\btechnical\s+level\b",
        r"\bdifficulty\b",
        r"\bbeginner[-\s]friendly\b",
        r"\badvanced\s+topics?\b"
    ],
    
    # 22. Related/Similar Projects - "Show me similar projects"
    "related_projects": [
        r"\brelated\s+projects?\b",
        r"\bsimilar\s+(to|projects?)\b",
        r"\blike\s+this\s+project\b",
        r"\bmore\s+projects?\s+like\b",
        r"\balso\s+interested\s+in\b",
        r"\bother\s+projects?\s+in\s+this\s+area\b",
        r"\byou\s+might\s+also\s+like\b"
    ],
    
    # 23. Availability/Status - "Is project X available for demo?"
    "availability_status": [
        r"\b(is|are)\b.*\bavailable\b",
        r"\bcan\s+i\s+(see|visit|demo)\b",
        r"\bopen\s+for\s+(demos?|visitors?)\b",
        r"\bwhen\s+can\s+i\s+(see|visit)\b",
        r"\boperating\s+hours\b",
        r"\bqueue\s+(time|length)\b",
        r"\bwait\s+time\b"
    ],
    
    # 24. Historical/Archive - "Past projects from previous years"
    "historical_archive": [
        r"\bprevious\s+(year|event)\b",
        r"\bpast\s+projects?\b",
        r"\barchive[sd]?\b",
        r"\blast\s+year'?s\b",
        r"\b20\d{2}\s+(event|showcase)\b",
        r"\bhistor(y|ical)\b.*\bproject",
        r"\bevolution\s+of\b"
    ],
    
    # 25. Multi-criteria Search - "AI projects with video recordings in Building 99"
    "multi_criteria_search": [
        r"\bprojects?\s+(with|that\s+have)\b.*\band\b.*\b(in|at|with)\b",
        r"\bboth\b.*\band\b",
        r"\ball\s+projects?\s+that\b.*\b(and|also|plus)\b",
        r"\b(filter|narrow)\s+by\b.*\band\b",
        r"\bwith\s+multiple\b.*\brequirements?\b"
    ]
}


# Intent descriptions for documentation
INTENT_DESCRIPTIONS = {
    "project_comparison": {
        "description": "Compare two or more projects side-by-side",
        "example_queries": [
            "How does the AI Healthcare project differ from the Medical Imaging project?",
            "Compare quantum computing projects",
            "What are the similarities between project A and project B?"
        ],
        "data_sources": ["event_hub_api", "rrs_source_of_truth_table"],
        "response_format": "comparison_table or side_by_side_cards"
    },
    
    "personalized_recommendations": {
        "description": "Suggest projects based on user interests, history, or profile",
        "example_queries": [
            "Recommend projects for someone interested in machine learning",
            "What should I see if I like HCI?",
            "Projects for me based on my previous visits"
        ],
        "data_sources": ["event_hub_api", "user_preferences", "visit_history"],
        "response_format": "ranked_list with reasoning"
    },
    
    "trending_popular": {
        "description": "Show most popular, trending, or highly-rated projects",
        "example_queries": [
            "What are the most popular projects?",
            "Top 5 must-see demos",
            "Trending projects today"
        ],
        "data_sources": ["analytics", "visit_counts", "ratings"],
        "response_format": "ranked_list with metrics (views, ratings, etc.)"
    },
    
    "time_based_schedule": {
        "description": "Schedule queries based on time (now, next, specific time)",
        "example_queries": [
            "What's happening now?",
            "Next session at 2:30 PM",
            "Schedule for today"
        ],
        "data_sources": ["event_hub_api", "live_schedule"],
        "response_format": "timeline or upcoming_events_list"
    },
    
    "collaboration_networking": {
        "description": "Connect users with teams, find collaboration opportunities",
        "example_queries": [
            "I want to collaborate on AI projects",
            "How do I contact the HCI team?",
            "Networking opportunities in systems research"
        ],
        "data_sources": ["event_hub_api", "contact_info", "team_profiles"],
        "response_format": "contact_cards with team info"
    },
    
    "prerequisites": {
        "description": "Technical level, background knowledge, difficulty assessment",
        "example_queries": [
            "What do I need to know before seeing the quantum computing demo?",
            "Is this project beginner-friendly?",
            "Technical prerequisites for AI sessions"
        ],
        "data_sources": ["rrs_source_of_truth_table", "session_metadata"],
        "response_format": "difficulty_badge + knowledge_requirements_list"
    },
    
    "related_projects": {
        "description": "Find similar or related projects based on theme/technology",
        "example_queries": [
            "Show me projects similar to this one",
            "Other projects in this research area",
            "Related demos I might like"
        ],
        "data_sources": ["event_hub_api", "similarity_index"],
        "response_format": "related_projects_carousel"
    },
    
    "availability_status": {
        "description": "Check if projects/demos are available, open hours, wait times",
        "example_queries": [
            "Is the VR demo available now?",
            "When can I visit project X?",
            "Current wait time for popular demos"
        ],
        "data_sources": ["live_status", "queue_system"],
        "response_format": "status_badge + availability_info"
    },
    
    "historical_archive": {
        "description": "Access past events, previous years' projects, archives",
        "example_queries": [
            "What were the AI projects from last year?",
            "2024 showcase archive",
            "How has this research evolved?"
        ],
        "data_sources": ["historical_database", "archive_api"],
        "response_format": "timeline_view or archive_list"
    },
    
    "multi_criteria_search": {
        "description": "Complex searches with multiple filters/constraints",
        "example_queries": [
            "AI projects with video recordings in Building 99",
            "HCI demos that need large displays and are available today",
            "Projects by Microsoft researchers with booth placement"
        ],
        "data_sources": ["event_hub_api", "rrs_source_of_truth_table"],
        "response_format": "filtered_results with applied_filters_summary"
    }
}


# Suggested priority order for implementation
IMPLEMENTATION_PRIORITY = [
    ("time_based_schedule", "HIGH", "Real-time schedule queries are very common at events"),
    ("related_projects", "HIGH", "Drives engagement by suggesting more content"),
    ("personalized_recommendations", "HIGH", "Improves user experience significantly"),
    ("multi_criteria_search", "MEDIUM", "Power users need complex queries"),
    ("trending_popular", "MEDIUM", "Social proof drives attendance"),
    ("availability_status", "MEDIUM", "Reduces frustration with busy demos"),
    ("project_comparison", "LOW", "Nice-to-have for decision-making"),
    ("collaboration_networking", "LOW", "Valuable but niche use case"),
    ("prerequisites", "LOW", "Helps match skill levels"),
    ("historical_archive", "LOW", "Depends on having archive data")
]
