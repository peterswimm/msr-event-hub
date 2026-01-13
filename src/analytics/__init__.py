"""Phase E3: Analytics & Metrics.

Aggregation, dashboards, and reporting for system metrics and performance analysis.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json

from sqlalchemy import Column, String, DateTime, JSON, Float, Integer
from sqlalchemy.orm import Session

from infra.models import Base
from src.observability.monitoring import ApplicationMetrics, Logger


logger = Logger(__name__)


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"  # Total count
    GAUGE = "gauge"  # Current value
    HISTOGRAM = "histogram"  # Distribution
    SUMMARY = "summary"  # Aggregated stats


class MetricsSnapshot(Base):
    """Model for storing metrics snapshots."""
    __tablename__ = "metrics_snapshots"
    
    id = Column(String(255), primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)
    metric_name = Column(String(255), nullable=False, index=True)
    value = Column(Float, nullable=True)
    tags = Column(JSON, nullable=True)  # {environment, service, version}
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metric_type": self.metric_type,
            "metric_name": self.metric_name,
            "value": self.value,
            "tags": self.tags or {}
        }


class DailyMetricsSummary(Base):
    """Model for daily metrics summaries."""
    __tablename__ = "daily_metrics_summaries"
    
    id = Column(String(255), primary_key=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    
    # Request metrics
    total_requests = Column(Integer, nullable=False, default=0)
    average_request_time = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)  # Percentage
    
    # Database metrics
    total_queries = Column(Integer, nullable=False, default=0)
    average_query_time = Column(Float, nullable=True)
    
    # Authentication metrics
    auth_attempts = Column(Integer, nullable=False, default=0)
    auth_failures = Column(Integer, nullable=False, default=0)
    tokens_issued = Column(Integer, nullable=False, default=0)
    
    # Evaluation metrics
    evaluations_completed = Column(Integer, nullable=False, default=0)
    evaluations_failed = Column(Integer, nullable=False, default=0)
    average_evaluation_score = Column(Float, nullable=True)
    
    # System metrics
    uptime_seconds = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "requests": {
                "total": self.total_requests,
                "average_time_ms": self.average_request_time,
                "error_rate_percent": self.error_rate
            },
            "database": {
                "total_queries": self.total_queries,
                "average_query_time_ms": self.average_query_time
            },
            "authentication": {
                "attempts": self.auth_attempts,
                "failures": self.auth_failures,
                "tokens_issued": self.tokens_issued
            },
            "evaluations": {
                "completed": self.evaluations_completed,
                "failed": self.evaluations_failed,
                "average_score": self.average_evaluation_score
            },
            "system": {
                "uptime_seconds": self.uptime_seconds,
                "memory_usage_mb": self.memory_usage_mb
            }
        }


class MetricsAggregator:
    """Aggregates metrics into snapshots and summaries."""
    
    def __init__(self, db: Session, metrics: ApplicationMetrics = None):
        """Initialize aggregator.
        
        Args:
            db: Database session
            metrics: ApplicationMetrics instance
        """
        self.db = db
        self.metrics = metrics or ApplicationMetrics()
    
    def record_snapshot(
        self,
        metric_name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Dict[str, str] = None
    ) -> str:
        """Record a metrics snapshot.
        
        Args:
            metric_name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Optional tags
            
        Returns:
            Snapshot ID
        """
        import uuid
        
        snapshot_id = str(uuid.uuid4())
        snapshot = MetricsSnapshot(
            id=snapshot_id,
            timestamp=datetime.utcnow(),
            metric_type=metric_type.value,
            metric_name=metric_name,
            value=value,
            tags=tags or {}
        )
        
        self.db.add(snapshot)
        self.db.commit()
        
        logger.info(f"Recorded metric: {metric_name} = {value}", extra={"metric_type": metric_type.value})
        
        return snapshot_id
    
    def get_metric_range(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get metric values within time range.
        
        Args:
            metric_name: Metric name
            start_time: Start time
            end_time: End time
            limit: Maximum results
            
        Returns:
            List of metric snapshots
        """
        snapshots = self.db.query(MetricsSnapshot).filter(
            MetricsSnapshot.metric_name == metric_name,
            MetricsSnapshot.timestamp >= start_time,
            MetricsSnapshot.timestamp <= end_time
        ).order_by(MetricsSnapshot.timestamp.desc()).limit(limit).all()
        
        return [s.to_dict() for s in snapshots]
    
    def calculate_daily_summary(self, date: datetime) -> Dict[str, Any]:
        """Calculate daily metrics summary.
        
        Args:
            date: Date to summarize
            
        Returns:
            Daily summary dictionary
        """
        start = datetime(date.year, date.month, date.day, 0, 0, 0)
        end = start + timedelta(days=1)
        
        # Aggregate metrics for the day
        summaries = self.db.query(MetricsSnapshot).filter(
            MetricsSnapshot.timestamp >= start,
            MetricsSnapshot.timestamp < end
        ).all()
        
        summary_data = {
            "date": start,
            "total_snapshots": len(summaries),
            "metrics_by_name": {}
        }
        
        # Group by metric name
        for snapshot in summaries:
            if snapshot.metric_name not in summary_data["metrics_by_name"]:
                summary_data["metrics_by_name"][snapshot.metric_name] = []
            summary_data["metrics_by_name"][snapshot.metric_name].append(snapshot.value)
        
        # Calculate statistics
        for metric_name, values in summary_data["metrics_by_name"].items():
            if values:
                summary_data["metrics_by_name"][metric_name] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        
        return summary_data
    
    def store_daily_summary(self, summary: DailyMetricsSummary) -> str:
        """Store daily summary in database.
        
        Args:
            summary: Daily summary object
            
        Returns:
            Summary ID
        """
        self.db.add(summary)
        self.db.commit()
        
        logger.info(f"Stored daily summary for {summary.date.date()}")
        
        return summary.id
    
    def get_daily_summaries(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get daily summaries within date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of daily summaries
        """
        summaries = self.db.query(DailyMetricsSummary).filter(
            DailyMetricsSummary.date >= start_date,
            DailyMetricsSummary.date <= end_date
        ).order_by(DailyMetricsSummary.date).all()
        
        return [s.to_dict() for s in summaries]


class DashboardAPI:
    """API for metrics dashboards."""
    
    def __init__(self, db: Session, aggregator: MetricsAggregator = None):
        """Initialize dashboard.
        
        Args:
            db: Database session
            aggregator: MetricsAggregator instance
        """
        self.db = db
        self.aggregator = aggregator or MetricsAggregator(db)
    
    def get_realtime_dashboard(self) -> Dict[str, Any]:
        """Get real-time metrics dashboard.
        
        Returns:
            Current system state
        """
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        
        return {
            "timestamp": now.isoformat(),
            "requests": {
                "total": self.aggregator.get_metric_range("http_requests_total", one_hour_ago, now, limit=1),
                "errors": self.aggregator.get_metric_range("http_errors_total", one_hour_ago, now, limit=1)
            },
            "database": {
                "queries": self.aggregator.get_metric_range("db_queries_total", one_hour_ago, now, limit=1),
                "duration": self.aggregator.get_metric_range("db_query_duration_ms", one_hour_ago, now, limit=1)
            },
            "authentication": {
                "attempts": self.aggregator.get_metric_range("auth_attempts_total", one_hour_ago, now, limit=1),
                "failures": self.aggregator.get_metric_range("auth_failures_total", one_hour_ago, now, limit=1)
            }
        }
    
    def get_performance_dashboard(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics dashboard.
        
        Args:
            hours: Hours to include
            
        Returns:
            Performance metrics
        """
        end = datetime.utcnow()
        start = end - timedelta(hours=hours)
        
        request_times = self.aggregator.get_metric_range("http_request_duration_ms", start, end, limit=1000)
        query_times = self.aggregator.get_metric_range("db_query_duration_ms", start, end, limit=1000)
        
        return {
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "hours": hours
            },
            "request_performance": {
                "samples": len(request_times),
                "metrics": request_times[:10]  # Last 10
            },
            "database_performance": {
                "samples": len(query_times),
                "metrics": query_times[:10]  # Last 10
            }
        }
    
    def get_health_dashboard(self) -> Dict[str, Any]:
        """Get system health dashboard.
        
        Returns:
            System health status
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "components": {
                "api": "operational",
                "database": "operational",
                "authentication": "operational",
                "async_queue": "operational"
            }
        }


class ReportGenerator:
    """Generates reports from metrics data."""
    
    def __init__(self, db: Session, aggregator: MetricsAggregator = None):
        """Initialize report generator.
        
        Args:
            db: Database session
            aggregator: MetricsAggregator instance
        """
        self.db = db
        self.aggregator = aggregator or MetricsAggregator(db)
    
    def generate_daily_report(self, date: datetime) -> Dict[str, Any]:
        """Generate daily metrics report.
        
        Args:
            date: Date for report
            
        Returns:
            Daily report data
        """
        daily_summary = self.db.query(DailyMetricsSummary).filter(
            DailyMetricsSummary.date == date
        ).first()
        
        if not daily_summary:
            return {"date": date.isoformat(), "data": "No data available"}
        
        return {
            "date": date.isoformat(),
            "report_type": "daily",
            "summary": daily_summary.to_dict(),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def generate_weekly_report(self, end_date: datetime) -> Dict[str, Any]:
        """Generate weekly metrics report.
        
        Args:
            end_date: End date for week
            
        Returns:
            Weekly report data
        """
        start_date = end_date - timedelta(days=7)
        
        summaries = self.aggregator.get_daily_summaries(start_date, end_date)
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "report_type": "weekly",
            "daily_summaries": summaries,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def generate_monthly_report(self, year: int, month: int) -> Dict[str, Any]:
        """Generate monthly metrics report.
        
        Args:
            year: Report year
            month: Report month
            
        Returns:
            Monthly report data
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        summaries = self.aggregator.get_daily_summaries(start_date, end_date)
        
        total_requests = sum(s["requests"]["total"] for s in summaries)
        total_errors = sum(
            s["requests"]["total"] * (s["requests"]["error_rate_percent"] / 100)
            for s in summaries if s["requests"]["error_rate_percent"]
        )
        
        return {
            "period": {
                "year": year,
                "month": month,
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "report_type": "monthly",
            "aggregates": {
                "total_requests": int(total_requests),
                "total_errors": int(total_errors),
                "error_rate_percent": (total_errors / total_requests * 100) if total_requests > 0 else 0,
                "daily_count": len(summaries)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def export_report_json(self, report: Dict[str, Any]) -> str:
        """Export report as JSON string.
        
        Args:
            report: Report dictionary
            
        Returns:
            JSON string
        """
        return json.dumps(report, indent=2)
    
    def export_report_csv(self, report: Dict[str, Any], report_type: str = "daily") -> str:
        """Export report as CSV.
        
        Args:
            report: Report dictionary
            report_type: Type of report (daily, weekly, monthly)
            
        Returns:
            CSV string
        """
        if report_type == "daily":
            return self._daily_to_csv(report)
        elif report_type == "weekly":
            return self._weekly_to_csv(report)
        elif report_type == "monthly":
            return self._monthly_to_csv(report)
        else:
            return "Unknown report type"
    
    @staticmethod
    def _daily_to_csv(report: Dict[str, Any]) -> str:
        """Convert daily report to CSV."""
        csv_lines = ["Metric,Value"]
        summary = report.get("summary", {})
        
        for key, value in summary.items():
            if isinstance(value, dict):
                for subkey, subval in value.items():
                    csv_lines.append(f"{key}_{subkey},{subval}")
            else:
                csv_lines.append(f"{key},{value}")
        
        return "\n".join(csv_lines)
    
    @staticmethod
    def _weekly_to_csv(report: Dict[str, Any]) -> str:
        """Convert weekly report to CSV."""
        csv_lines = ["Date,Requests,Errors,ErrorRate,Evaluations,Score"]
        
        for summary in report.get("daily_summaries", []):
            date = summary.get("date", "")
            reqs = summary.get("requests", {}).get("total", 0)
            errs = summary.get("requests", {}).get("total", 0) * (summary.get("requests", {}).get("error_rate_percent", 0) / 100)
            rate = summary.get("requests", {}).get("error_rate_percent", 0)
            evals = summary.get("evaluations", {}).get("completed", 0)
            score = summary.get("evaluations", {}).get("average_score", 0)
            
            csv_lines.append(f"{date},{reqs},{errs},{rate},{evals},{score}")
        
        return "\n".join(csv_lines)
    
    @staticmethod
    def _monthly_to_csv(report: Dict[str, Any]) -> str:
        """Convert monthly report to CSV."""
        csv_lines = ["Metric,Value"]
        agg = report.get("aggregates", {})
        
        for key, value in agg.items():
            csv_lines.append(f"{key},{value}")
        
        return "\n".join(csv_lines)
