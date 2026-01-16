"""
Distributed tracing and observability for agent operations.

Provides comprehensive tracing for:
- Agent execution and decision-making
- LLM calls (prompts, completions, tokens)
- Tool/function calls
- Workflow orchestration
- Performance metrics
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional
from datetime import datetime

try:
    from src.config.settings import get_settings
except ImportError:
    # Fallback if config not available
    def get_settings():
        return None

logger = logging.getLogger(__name__)


class TracingManager:
    """Manage tracing lifecycle and custom spans."""
    
    def __init__(self):
        self.settings = get_settings()
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize OpenTelemetry tracing with Agent Framework."""
        if self._initialized:
            logger.warning("Tracing already initialized")
            return
        
        if not self.settings.enable_tracing:
            logger.info("Tracing disabled in configuration")
            return
        
        try:
            # Agent Framework built-in observability setup
            setup_observability(
                otlp_endpoint=self.settings.otlp_endpoint,
                enable_sensitive_data=self.settings.enable_sensitive_data
            )
            
            self._initialized = True
            logger.info(
                f"✓ Tracing initialized - OTLP endpoint: {self.settings.otlp_endpoint}, "
                f"Sensitive data: {self.settings.enable_sensitive_data}"
            )
            logger.info("View traces in AI Toolkit: Run command 'AI Toolkit: View Trace'")
            
        except Exception as e:
            logger.error(f"Failed to initialize tracing: {e}")
            logger.info("Continuing without tracing...")
    
    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Create a custom span for manual instrumentation.
        
        Note: Agent Framework automatically instruments:
        - Chat client operations
        - Agent execution
        - Workflow orchestration
        
        Use this only for custom business logic not covered by auto-instrumentation.
        """
        # For now, this is a no-op since Agent Framework handles most tracing
        # Can be extended with OpenTelemetry API for custom spans if needed
        try:
            yield
        finally:
            pass


# Global tracing manager instance
_tracing_manager: Optional[TracingManager] = None


def setup_tracing() -> TracingManager:
    """
    Setup and return global tracing manager.
    
    **IMPORTANT**: Before running your application with tracing:
    1. Open VS Code Command Palette (Ctrl+Shift+P / Cmd+Shift+P)
    2. Run: "AI Toolkit: Start Trace Collector"
    3. This starts the OTLP collector at http://localhost:4317
    
    After running your agent:
    4. Run: "AI Toolkit: View Trace" to visualize traces
    
    Returns:
        TracingManager instance
    """
    global _tracing_manager
    
    if _tracing_manager is None:
        _tracing_manager = TracingManager()
        _tracing_manager.initialize()
    
    return _tracing_manager


def get_tracing_manager() -> Optional[TracingManager]:
    """Get the global tracing manager if initialized."""
    return _tracing_manager
