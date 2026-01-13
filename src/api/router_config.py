"""Query routing configuration and feature flags."""

import os
from enum import Enum


class RoutingStrategy(str, Enum):
    """Routing strategy options."""
    DETERMINISTIC_FIRST = "deterministic_first"  # Try deterministic, fallback to LLM
    LLM_ONLY = "llm_only"                        # Always use LLM (baseline)
    DETERMINISTIC_ONLY = "deterministic_only"    # Only deterministic, error on low confidence
    HYBRID = "hybrid"                            # Smart blend based on confidence


class DataSource(Enum):
    """Event data source for query execution."""
    API = "api"  # Use live Event Hub APIs
    MOCK = "mock"  # Use local hardcoded JSON data


class RouterConfig:
    """Configuration for query routing behavior."""

    def __init__(self):
        # Feature flags
        self.enable_deterministic_routing = self._get_bool_env(
            "ENABLE_DETERMINISTIC_ROUTING", default=True
        )
        self.routing_strategy = self._get_enum_env(
            "ROUTING_STRATEGY", RoutingStrategy, default=RoutingStrategy.DETERMINISTIC_FIRST
        )
        
        # Confidence thresholds
        self.deterministic_threshold = float(
            os.getenv("DETERMINISTIC_CONFIDENCE_THRESHOLD", "0.8")
        )
        self.llm_assist_threshold = float(
            os.getenv("LLM_ASSIST_CONFIDENCE_THRESHOLD", "0.6")
        )
        
        # A/B testing
        self.ab_test_enabled = self._get_bool_env("ROUTING_AB_TEST_ENABLED", default=False)
        self.ab_test_deterministic_ratio = float(
            os.getenv("AB_TEST_DETERMINISTIC_RATIO", "0.5")
        )
        
        # Telemetry
        self.log_routing_decisions = self._get_bool_env(
            "LOG_ROUTING_DECISIONS", default=True
        )
        self.emit_routing_metrics = self._get_bool_env(
            "EMIT_ROUTING_METRICS", default=True
        )
        
        # Data source configuration
        data_source_str = os.getenv('EVENT_DATA_SOURCE', 'api').lower()
        self.event_data_source = DataSource.API if data_source_str == 'api' else DataSource.MOCK
        self.mock_data_path = os.getenv('MOCK_DATA_PATH', 'data/mock_event_data.json')
        
        # Foundry SaaS orchestration for complex queries
        self.delegate_to_foundry = self._get_bool_env('DELEGATE_TO_FOUNDRY', default=False)
        self.foundry_delegation_threshold = float(
            os.getenv('FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD', '0.8')
        )
        self.foundry_endpoint = os.getenv('FOUNDRY_ENDPOINT', '')
        self.foundry_agent_id = os.getenv('FOUNDRY_AGENT_ID', 'msr-event-orchestrator')

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get boolean from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def _get_enum_env(self, key: str, enum_class, default):
        """Get enum from environment variable."""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return enum_class(value)
        except ValueError:
            return default

    def should_use_deterministic(self, confidence: float) -> bool:
        """Decide if deterministic routing should be used based on config and confidence.
        
        Args:
            confidence: Confidence score from intent classifier (0.0 to 1.0)
            
        Returns:
            True if deterministic routing should be used, False otherwise
        """
        if not self.enable_deterministic_routing:
            return False
            
        if self.routing_strategy == RoutingStrategy.LLM_ONLY:
            return False
            
        if self.routing_strategy == RoutingStrategy.DETERMINISTIC_ONLY:
            return True
            
        if self.routing_strategy == RoutingStrategy.DETERMINISTIC_FIRST:
            return confidence >= self.deterministic_threshold
            
        if self.routing_strategy == RoutingStrategy.HYBRID:
            # Hybrid: use deterministic for high confidence, LLM assist for medium, full LLM for low
            return confidence >= self.deterministic_threshold
            
        return False

    def should_use_llm_assist(self, confidence: float) -> bool:
        """Decide if LLM should assist with context from deterministic routing."""
        if not self.enable_deterministic_routing:
            return False
            
        if self.routing_strategy == RoutingStrategy.LLM_ONLY:
            return True
            
        if self.routing_strategy == RoutingStrategy.DETERMINISTIC_ONLY:
            return False
            
        # Use LLM assist for medium confidence queries
        return (
            self.llm_assist_threshold <= confidence < self.deterministic_threshold
        )

    def should_delegate_to_foundry(self, confidence: float) -> bool:
        """
        Decide if low-confidence query should be delegated to Foundry agents.
        
        When Foundry delegation is enabled and confidence is below delegation threshold,
        we skip deterministic routing and AOAI, delegating instead to Foundry's
        multi-agent orchestration service for complex reasoning.
        """
        if not self.delegate_to_foundry:
            return False
        
        if not self.foundry_endpoint:
            return False
        
        # Delegate if confidence is below threshold (hard cases)
        return confidence < self.foundry_delegation_threshold

    def to_dict(self) -> dict:
        """Export config as dictionary for logging."""
        return {
            "enable_deterministic_routing": self.enable_deterministic_routing,
            "routing_strategy": self.routing_strategy.value,
            "deterministic_threshold": self.deterministic_threshold,
            "llm_assist_threshold": self.llm_assist_threshold,
            "ab_test_enabled": self.ab_test_enabled,
            "ab_test_deterministic_ratio": self.ab_test_deterministic_ratio,
            "log_routing_decisions": self.log_routing_decisions,
            "emit_routing_metrics": self.emit_routing_metrics,
            "data_source": self.event_data_source.value,
            "mock_data_path": self.mock_data_path if self.event_data_source == DataSource.MOCK else None,
            "delegate_to_foundry": self.delegate_to_foundry,
            "foundry_delegation_threshold": self.foundry_delegation_threshold,
            "foundry_endpoint": self.foundry_endpoint if self.foundry_endpoint else "NOT_CONFIGURED"
        }


# Global config instance
router_config = RouterConfig()
