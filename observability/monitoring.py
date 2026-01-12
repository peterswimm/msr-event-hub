"""Phase E1.4: Monitoring & Observability.

Structured logging, Prometheus metrics, health checks, performance tracking.
Integrates with application to provide comprehensive monitoring.
"""

import logging
import time
from typing import Optional, Callable, Any, Dict
from functools import wraps
from contextlib import contextmanager
from datetime import datetime

import structlog
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from prometheus_client.core import CounterMetricFamily


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)


class Logger:
    """Structured logger wrapper."""
    
    def __init__(self, name: str):
        """Initialize logger.
        
        Args:
            name: Logger name
        """
        self.logger = structlog.get_logger(name)
    
    def debug(self, msg: str, **kwargs):
        """Log debug message."""
        self.logger.debug(msg, **kwargs)
    
    def info(self, msg: str, **kwargs):
        """Log info message."""
        self.logger.info(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        """Log warning message."""
        self.logger.warning(msg, **kwargs)
    
    def error(self, msg: str, exc_info: bool = False, **kwargs):
        """Log error message."""
        self.logger.error(msg, exc_info=exc_info, **kwargs)
    
    def critical(self, msg: str, exc_info: bool = False, **kwargs):
        """Log critical message."""
        self.logger.critical(msg, exc_info=exc_info, **kwargs)


def get_logger(name: str) -> Logger:
    """Get structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return Logger(name)


# Metrics Registry
class MetricsCollector:
    """Collects application metrics using Prometheus."""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics collector.
        
        Args:
            registry: Prometheus registry (creates new if None)
        """
        self.registry = registry or CollectorRegistry()
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize all metrics."""
        # HTTP Requests
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            registry=self.registry,
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )
        
        # Database Operations
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['operation', 'table'],
            registry=self.registry
        )
        
        self.db_query_duration_seconds = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['operation', 'table'],
            registry=self.registry,
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
        )
        
        # Authentication
        self.auth_attempts_total = Counter(
            'auth_attempts_total',
            'Total authentication attempts',
            ['type', 'result'],  # type: login, register; result: success, failure
            registry=self.registry
        )
        
        self.auth_tokens_active = Gauge(
            'auth_tokens_active',
            'Active authentication tokens',
            registry=self.registry
        )
        
        # Application Health
        self.app_info = Counter(
            'app_info',
            'Application info',
            ['version', 'environment'],
            registry=self.registry
        )
        
        self.app_errors_total = Counter(
            'app_errors_total',
            'Total application errors',
            ['error_type'],
            registry=self.registry
        )
        
        self.app_health_check_failures = Counter(
            'app_health_check_failures',
            'Health check failures',
            ['check_name'],
            registry=self.registry
        )
        
        self.app_uptime_seconds = Gauge(
            'app_uptime_seconds',
            'Application uptime',
            registry=self.registry
        )
        
        # Evaluation Metrics
        self.evaluation_executions_total = Counter(
            'evaluation_executions_total',
            'Total evaluation executions',
            ['status'],  # pending, running, completed, failed
            registry=self.registry
        )
        
        self.evaluation_execution_duration_seconds = Histogram(
            'evaluation_execution_duration_seconds',
            'Evaluation execution duration',
            registry=self.registry,
            buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 900.0, 3600.0)
        )
        
        self.evaluation_quality_score = Gauge(
            'evaluation_quality_score',
            'Latest evaluation quality score',
            registry=self.registry
        )


# Global metrics instance
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get metrics collector instance.
    
    Returns:
        MetricsCollector instance
    """
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


# Timing and Tracing

@contextmanager
def timer(logger: Logger, operation: str, **context):
    """Context manager for timing operations.
    
    Usage:
        with timer(logger, "database_query", table="users"):
            db.query(User).all()
    
    Args:
        logger: Logger instance
        operation: Operation name
        **context: Additional context to log
    """
    start = time.time()
    try:
        yield
        duration = time.time() - start
        logger.info(f"{operation}_success", duration_ms=duration*1000, **context)
    except Exception as e:
        duration = time.time() - start
        logger.error(
            f"{operation}_failed",
            duration_ms=duration*1000,
            error=str(e),
            exc_info=True,
            **context
        )
        raise


def track_performance(logger: Logger, operation: str):
    """Decorator for performance tracking.
    
    Usage:
        @track_performance(logger, "user_registration")
        def register_user(username, email, password):
            ...
    
    Args:
        logger: Logger instance
        operation: Operation name
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.info(
                    f"{operation}_completed",
                    duration_ms=duration*1000,
                    func=func.__name__
                )
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"{operation}_failed",
                    duration_ms=duration*1000,
                    error=str(e),
                    exc_info=True,
                    func=func.__name__
                )
                raise
        return wrapper
    return decorator


# Health Checks

class HealthCheck:
    """Health check for a component."""
    
    def __init__(self, name: str, check_fn: Callable[[], bool]):
        """Initialize health check.
        
        Args:
            name: Health check name
            check_fn: Function that returns True if healthy
        """
        self.name = name
        self.check_fn = check_fn
        self.last_check_time: Optional[datetime] = None
        self.is_healthy = False
        self.error: Optional[str] = None
    
    def check(self) -> Dict[str, Any]:
        """Execute health check.
        
        Returns:
            Health check result
        """
        self.last_check_time = datetime.utcnow()
        try:
            self.is_healthy = self.check_fn()
            self.error = None
            return {
                "name": self.name,
                "status": "healthy" if self.is_healthy else "unhealthy",
                "timestamp": self.last_check_time.isoformat(),
                "error": None
            }
        except Exception as e:
            self.is_healthy = False
            self.error = str(e)
            return {
                "name": self.name,
                "status": "unhealthy",
                "timestamp": self.last_check_time.isoformat(),
                "error": str(e)
            }


class HealthCheckRegistry:
    """Registry of health checks."""
    
    def __init__(self):
        """Initialize health check registry."""
        self.checks: Dict[str, HealthCheck] = {}
    
    def register(self, name: str, check_fn: Callable[[], bool]) -> HealthCheck:
        """Register a health check.
        
        Args:
            name: Health check name
            check_fn: Function that returns True if healthy
            
        Returns:
            HealthCheck instance
        """
        check = HealthCheck(name, check_fn)
        self.checks[name] = check
        return check
    
    def check_all(self) -> Dict[str, Any]:
        """Execute all health checks.
        
        Returns:
            Health check results for all components
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {}
        }
        
        for name, check in self.checks.items():
            result = check.check()
            results["checks"][name] = result
            
            if not check.is_healthy:
                results["status"] = "unhealthy"
        
        return results
    
    def get_status_code(self) -> int:
        """Get HTTP status code for health check.
        
        Returns:
            200 if healthy, 503 if unhealthy
        """
        result = self.check_all()
        return 200 if result["status"] == "healthy" else 503


# Global health check registry
_health_checks: Optional[HealthCheckRegistry] = None


def get_health_check_registry() -> HealthCheckRegistry:
    """Get health check registry instance.
    
    Returns:
        HealthCheckRegistry instance
    """
    global _health_checks
    if _health_checks is None:
        _health_checks = HealthCheckRegistry()
    return _health_checks


# Application Context Metrics

class ApplicationMetrics:
    """Application-level metrics tracking."""
    
    def __init__(self, logger: Logger, metrics: MetricsCollector):
        """Initialize application metrics.
        
        Args:
            logger: Logger instance
            metrics: MetricsCollector instance
        """
        self.logger = logger
        self.metrics = metrics
        self.start_time = time.time()
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metric.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            status: HTTP status code
            duration: Request duration in seconds
        """
        self.metrics.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.metrics.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_db_query(self, operation: str, table: str, duration: float):
        """Record database query metric.
        
        Args:
            operation: Query operation (select, insert, update, delete)
            table: Table name
            duration: Query duration in seconds
        """
        self.metrics.db_queries_total.labels(
            operation=operation,
            table=table
        ).inc()
        
        self.metrics.db_query_duration_seconds.labels(
            operation=operation,
            table=table
        ).observe(duration)
    
    def record_auth_attempt(self, auth_type: str, success: bool):
        """Record authentication attempt.
        
        Args:
            auth_type: Authentication type (login, register)
            success: Whether authentication succeeded
        """
        result = "success" if success else "failure"
        self.metrics.auth_attempts_total.labels(
            type=auth_type,
            result=result
        ).inc()
    
    def record_error(self, error_type: str):
        """Record application error.
        
        Args:
            error_type: Type of error
        """
        self.metrics.app_errors_total.labels(error_type=error_type).inc()
    
    def record_evaluation_execution(self, status: str, duration: float):
        """Record evaluation execution.
        
        Args:
            status: Execution status (pending, running, completed, failed)
            duration: Execution duration in seconds
        """
        self.metrics.evaluation_executions_total.labels(status=status).inc()
        self.metrics.evaluation_execution_duration_seconds.observe(duration)
    
    def get_uptime_seconds(self) -> float:
        """Get application uptime in seconds.
        
        Returns:
            Uptime in seconds
        """
        return time.time() - self.start_time


# Logging context helpers

def log_request(logger: Logger, method: str, path: str, **kwargs):
    """Log HTTP request.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        **kwargs: Additional context
    """
    logger.info("http_request", method=method, path=path, **kwargs)


def log_response(logger: Logger, method: str, path: str, status: int, duration: float, **kwargs):
    """Log HTTP response.
    
    Args:
        logger: Logger instance
        method: HTTP method
        path: Request path
        status: Response status code
        duration: Response time in seconds
        **kwargs: Additional context
    """
    logger.info(
        "http_response",
        method=method,
        path=path,
        status=status,
        duration_ms=duration*1000,
        **kwargs
    )


def log_error(logger: Logger, error: Exception, context: str, **kwargs):
    """Log error with context.
    
    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Context description
        **kwargs: Additional context
    """
    logger.error(
        "error",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context,
        exc_info=True,
        **kwargs
    )
