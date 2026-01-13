"""
Integration tests for hybrid routing (deterministic + Foundry delegation).
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from src.api.router_config import RouterConfig, RoutingStrategy, DataSource


class TestHybridRouting:
    """Test deterministic-first routing with Foundry delegation fallback."""

    def test_router_config_foundry_flags(self):
        """Test that Foundry configuration flags load correctly."""
        with patch.dict(os.environ, {
            'DELEGATE_TO_FOUNDRY': 'true',
            'FOUNDRY_ENDPOINT': 'https://test.cognitiveservices.azure.com',
            'FOUNDRY_AGENT_ID': 'test-agent',
            'FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD': '0.75'
        }):
            config = RouterConfig()
            assert config.delegate_to_foundry is True
            assert config.foundry_endpoint == 'https://test.cognitiveservices.azure.com'
            assert config.foundry_agent_id == 'test-agent'
            assert config.foundry_delegation_threshold == 0.75

    def test_router_config_foundry_disabled_by_default(self):
        """Test that Foundry delegation is disabled by default."""
        with patch.dict(os.environ, {}, clear=False):
            config = RouterConfig()
            assert config.delegate_to_foundry is False

    def test_should_delegate_to_foundry_when_low_confidence(self):
        """Test delegation when confidence is below threshold."""
        with patch.dict(os.environ, {
            'DELEGATE_TO_FOUNDRY': 'true',
            'FOUNDRY_ENDPOINT': 'https://test.cognitiveservices.azure.com',
            'FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD': '0.8'
        }):
            config = RouterConfig()
            
            # Low confidence should delegate
            assert config.should_delegate_to_foundry(0.5) is True
            assert config.should_delegate_to_foundry(0.79) is True
            
            # High confidence should not delegate
            assert config.should_delegate_to_foundry(0.8) is False
            assert config.should_delegate_to_foundry(0.95) is False

    def test_should_not_delegate_when_disabled(self):
        """Test that delegation respects DELEGATE_TO_FOUNDRY flag."""
        with patch.dict(os.environ, {
            'DELEGATE_TO_FOUNDRY': 'false',
            'FOUNDRY_ENDPOINT': 'https://test.cognitiveservices.azure.com'
        }):
            config = RouterConfig()
            # Should never delegate even with low confidence
            assert config.should_delegate_to_foundry(0.1) is False

    def test_should_not_delegate_without_endpoint(self):
        """Test that delegation requires Foundry endpoint configured."""
        with patch.dict(os.environ, {
            'DELEGATE_TO_FOUNDRY': 'true',
            'FOUNDRY_ENDPOINT': ''  # No endpoint
        }):
            config = RouterConfig()
            # Should not delegate without endpoint
            assert config.should_delegate_to_foundry(0.1) is False

    def test_deterministic_threshold_takes_priority(self):
        """Test that high-confidence results skip Foundry."""
        with patch.dict(os.environ, {
            'ENABLE_DETERMINISTIC_ROUTING': 'true',
            'DETERMINISTIC_CONFIDENCE_THRESHOLD': '0.8',
            'DELEGATE_TO_FOUNDRY': 'true',
            'FOUNDRY_ENDPOINT': 'https://test.cognitiveservices.azure.com'
        }):
            config = RouterConfig()
            
            # High confidence: use deterministic (never delegate)
            assert config.should_use_deterministic(0.85) is True
            assert config.should_delegate_to_foundry(0.85) is False

    def test_routing_strategy_hybrid_mode(self):
        """Test HYBRID routing strategy with confidence tiers."""
        with patch.dict(os.environ, {
            'ENABLE_DETERMINISTIC_ROUTING': 'true',
            'ROUTING_STRATEGY': 'hybrid',
            'DETERMINISTIC_CONFIDENCE_THRESHOLD': '0.8',
            'LLM_ASSIST_CONFIDENCE_THRESHOLD': '0.6',
            'DELEGATE_TO_FOUNDRY': 'true',
            'FOUNDRY_ENDPOINT': 'https://test.cognitiveservices.azure.com'
        }):
            config = RouterConfig()
            
            # High confidence (>0.8): deterministic
            assert config.should_use_deterministic(0.85) is True
            
            # Medium confidence (0.6-0.8): LLM assist with context
            assert config.should_use_deterministic(0.7) is False
            assert config.should_use_llm_assist(0.7) is True
            
            # Low confidence (<0.6): delegate to Foundry
            assert config.should_delegate_to_foundry(0.5) is True

    def test_config_to_dict_includes_foundry_settings(self):
        """Test that config.to_dict() includes Foundry configuration."""
        with patch.dict(os.environ, {
            'DELEGATE_TO_FOUNDRY': 'true',
            'FOUNDRY_ENDPOINT': 'https://test.cognitiveservices.azure.com',
            'FOUNDRY_AGENT_ID': 'my-agent'
        }):
            config = RouterConfig()
            config_dict = config.to_dict()
            
            assert config_dict['delegate_to_foundry'] is True
            assert config_dict['foundry_endpoint'] == 'https://test.cognitiveservices.azure.com'
            assert 'foundry_delegation_threshold' in config_dict

    def test_foundry_config_object(self):
        """Test FoundryConfig dataclass initialization."""
        from src.api.foundry_client import FoundryConfig
        
        config = FoundryConfig(
            endpoint='https://test.cognitiveservices.azure.com',
            agent_id='test-agent'
        )
        
        assert config.endpoint == 'https://test.cognitiveservices.azure.com'
        assert config.agent_id == 'test-agent'
        assert config.api_version == '2025-11-15-preview'
        assert config.max_retries == 2
        assert config.request_timeout_seconds == 30


class TestRoutingFlowIntegration:
    """Test end-to-end routing decision flow."""

    def test_confidence_based_routing_path(self):
        """Test that routing path depends on confidence score."""
        with patch.dict(os.environ, {
            'ENABLE_DETERMINISTIC_ROUTING': 'true',
            'DETERMINISTIC_CONFIDENCE_THRESHOLD': '0.8',
            'DELEGATE_TO_FOUNDRY': 'true',
            'FOUNDRY_ENDPOINT': 'https://test.cognitiveservices.azure.com',
            'FOUNDRY_DELEGATION_CONFIDENCE_THRESHOLD': '0.8'
        }):
            config = RouterConfig()
            
            # Test high confidence: deterministic path
            assert config.should_use_deterministic(0.9) is True
            
            # Test medium confidence: LLM assist path
            assert config.should_use_deterministic(0.7) is False
            assert config.should_use_llm_assist(0.7) is True
            assert config.should_delegate_to_foundry(0.7) is False
            
            # Test low confidence: Foundry delegation path
            assert config.should_delegate_to_foundry(0.5) is True

    def test_a_b_testing_with_foundry(self):
        """Test that A/B testing works with Foundry delegation."""
        with patch.dict(os.environ, {
            'ENABLE_DETERMINISTIC_ROUTING': 'true',
            'ROUTING_AB_TEST_ENABLED': 'true',
            'AB_TEST_DETERMINISTIC_RATIO': '0.5',
            'DELEGATE_TO_FOUNDRY': 'true',
            'FOUNDRY_ENDPOINT': 'https://test.cognitiveservices.azure.com'
        }):
            config = RouterConfig()
            
            assert config.ab_test_enabled is True
            assert config.ab_test_deterministic_ratio == 0.5

    def test_data_source_selection(self):
        """Test data source selection (API vs mock)."""
        with patch.dict(os.environ, {
            'EVENT_DATA_SOURCE': 'mock',
            'MOCK_DATA_PATH': 'custom/path.json'
        }):
            config = RouterConfig()
            
            assert config.event_data_source == DataSource.MOCK
            assert config.mock_data_path == 'custom/path.json'
        
        with patch.dict(os.environ, {
            'EVENT_DATA_SOURCE': 'api'
        }):
            config = RouterConfig()
            assert config.event_data_source == DataSource.API


class TestFoundryClientConfiguration:
    """Test Foundry client initialization and configuration."""

    def test_foundry_client_manages_auth(self):
        """Test that FoundryClient handles managed identity authentication."""
        from src.api.foundry_client import FoundryClient, FoundryConfig
        
        config = FoundryConfig(
            endpoint='https://test.cognitiveservices.azure.com',
            agent_id='test-agent'
        )
        
        # Client should be creatable (actual auth happens on use)
        client = FoundryClient(config)
        assert client.config.endpoint == 'https://test.cognitiveservices.azure.com'
        assert client.config.agent_id == 'test-agent'

    def test_foundry_endpoint_validation(self):
        """Test that missing Foundry config prevents delegation."""
        with patch.dict(os.environ, {
            'DELEGATE_TO_FOUNDRY': 'true',
            'FOUNDRY_ENDPOINT': ''  # Missing
        }):
            config = RouterConfig()
            
            # Should not delegate without endpoint
            assert config.should_delegate_to_foundry(0.1) is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
