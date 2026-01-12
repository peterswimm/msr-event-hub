"""Tests for Phase E3: Analytics & Metrics."""

import pytest
from datetime import datetime, timedelta
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from analytics import (
    MetricsAggregator, DashboardAPI, ReportGenerator,
    MetricType, MetricsSnapshot, DailyMetricsSummary
)
from infra.database import Base


@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def aggregator(test_db):
    """Create MetricsAggregator fixture."""
    return MetricsAggregator(test_db)


@pytest.fixture
def dashboard(test_db):
    """Create DashboardAPI fixture."""
    return DashboardAPI(test_db)


@pytest.fixture
def report_generator(test_db):
    """Create ReportGenerator fixture."""
    return ReportGenerator(test_db)


class TestMetricsSnapshot:
    """Test MetricsSnapshot model."""
    
    def test_snapshot_creation(self, test_db):
        """Test creating snapshot."""
        snapshot = MetricsSnapshot(
            id="snap-1",
            timestamp=datetime.utcnow(),
            metric_type=MetricType.GAUGE.value,
            metric_name="cpu_usage",
            value=45.5
        )
        test_db.add(snapshot)
        test_db.commit()
        
        retrieved = test_db.query(MetricsSnapshot).filter(
            MetricsSnapshot.id == "snap-1"
        ).first()
        assert retrieved.metric_name == "cpu_usage"
        assert retrieved.value == 45.5
    
    def test_snapshot_with_tags(self, test_db):
        """Test snapshot with tags."""
        tags = {"service": "api", "environment": "production"}
        snapshot = MetricsSnapshot(
            id="snap-2",
            timestamp=datetime.utcnow(),
            metric_type=MetricType.COUNTER.value,
            metric_name="requests_total",
            value=1000,
            tags=tags
        )
        test_db.add(snapshot)
        test_db.commit()
        
        retrieved = test_db.query(MetricsSnapshot).filter(
            MetricsSnapshot.id == "snap-2"
        ).first()
        assert retrieved.tags == tags
    
    def test_snapshot_to_dict(self, test_db):
        """Test converting snapshot to dict."""
        snapshot = MetricsSnapshot(
            id="snap-3",
            timestamp=datetime.utcnow(),
            metric_type=MetricType.HISTOGRAM.value,
            metric_name="request_duration",
            value=125.3
        )
        test_db.add(snapshot)
        test_db.commit()
        
        snapshot_dict = snapshot.to_dict()
        assert snapshot_dict["metric_name"] == "request_duration"
        assert snapshot_dict["value"] == 125.3
        assert snapshot_dict["metric_type"] == MetricType.HISTOGRAM.value


class TestDailyMetricsSummary:
    """Test DailyMetricsSummary model."""
    
    def test_summary_creation(self, test_db):
        """Test creating daily summary."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        summary = DailyMetricsSummary(
            id="summary-1",
            date=today,
            total_requests=1000,
            average_request_time=125.5,
            error_rate=2.5,
            total_queries=5000,
            average_query_time=25.3
        )
        test_db.add(summary)
        test_db.commit()
        
        retrieved = test_db.query(DailyMetricsSummary).filter(
            DailyMetricsSummary.id == "summary-1"
        ).first()
        assert retrieved.total_requests == 1000
        assert retrieved.error_rate == 2.5
    
    def test_summary_to_dict(self, test_db):
        """Test converting summary to dict."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        summary = DailyMetricsSummary(
            id="summary-2",
            date=today,
            total_requests=500,
            auth_attempts=100,
            evaluations_completed=50
        )
        test_db.add(summary)
        test_db.commit()
        
        summary_dict = summary.to_dict()
        assert summary_dict["requests"]["total"] == 500
        assert summary_dict["authentication"]["attempts"] == 100
        assert summary_dict["evaluations"]["completed"] == 50


class TestMetricsAggregator:
    """Test MetricsAggregator."""
    
    def test_record_snapshot(self, aggregator, test_db):
        """Test recording snapshot."""
        snap_id = aggregator.record_snapshot(
            metric_name="memory_usage",
            value=512.5,
            metric_type=MetricType.GAUGE
        )
        
        assert snap_id is not None
        
        snapshot = test_db.query(MetricsSnapshot).filter(
            MetricsSnapshot.id == snap_id
        ).first()
        assert snapshot.metric_name == "memory_usage"
        assert snapshot.value == 512.5
    
    def test_record_snapshot_with_tags(self, aggregator, test_db):
        """Test recording snapshot with tags."""
        tags = {"host": "server-1", "region": "us-west"}
        
        snap_id = aggregator.record_snapshot(
            metric_name="disk_usage",
            value=256.0,
            metric_type=MetricType.GAUGE,
            tags=tags
        )
        
        snapshot = test_db.query(MetricsSnapshot).filter(
            MetricsSnapshot.id == snap_id
        ).first()
        assert snapshot.tags == tags
    
    def test_get_metric_range(self, aggregator, test_db):
        """Test getting metric range."""
        now = datetime.utcnow()
        
        for i in range(5):
            snapshot = MetricsSnapshot(
                id=f"snap-range-{i}",
                timestamp=now - timedelta(hours=i),
                metric_type=MetricType.GAUGE.value,
                metric_name="test_metric",
                value=float(i * 10)
            )
            test_db.add(snapshot)
        test_db.commit()
        
        start = now - timedelta(hours=6)
        end = now + timedelta(hours=1)
        metrics = aggregator.get_metric_range("test_metric", start, end)
        
        assert len(metrics) == 5
        assert all(m["metric_name"] == "test_metric" for m in metrics)
    
    def test_calculate_daily_summary(self, aggregator, test_db):
        """Test calculating daily summary."""
        today = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
        
        for i in range(10):
            snapshot = MetricsSnapshot(
                id=f"daily-snap-{i}",
                timestamp=today - timedelta(hours=i % 24),
                metric_type=MetricType.GAUGE.value,
                metric_name=f"metric_{i % 3}",
                value=float(i * 5)
            )
            test_db.add(snapshot)
        test_db.commit()
        
        summary = aggregator.calculate_daily_summary(today)
        assert summary["total_snapshots"] > 0
        assert "metrics_by_name" in summary
    
    def test_store_daily_summary(self, aggregator, test_db):
        """Test storing daily summary."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        summary = DailyMetricsSummary(
            id="store-summary-1",
            date=today,
            total_requests=2000,
            average_request_time=150.0
        )
        
        summary_id = aggregator.store_daily_summary(summary)
        assert summary_id == "store-summary-1"
        
        retrieved = test_db.query(DailyMetricsSummary).filter(
            DailyMetricsSummary.id == summary_id
        ).first()
        assert retrieved.total_requests == 2000


class TestDashboardAPI:
    """Test DashboardAPI."""
    
    def test_realtime_dashboard(self, dashboard):
        """Test realtime dashboard."""
        dash = dashboard.get_realtime_dashboard()
        
        assert "timestamp" in dash
        assert "requests" in dash
        assert "database" in dash
        assert "authentication" in dash
    
    def test_performance_dashboard(self, dashboard):
        """Test performance dashboard."""
        dash = dashboard.get_performance_dashboard(hours=24)
        
        assert "period" in dash
        assert dash["period"]["hours"] == 24
        assert "request_performance" in dash
        assert "database_performance" in dash
    
    def test_health_dashboard(self, dashboard):
        """Test health dashboard."""
        dash = dashboard.get_health_dashboard()
        
        assert dash["status"] == "healthy"
        assert "components" in dash
        assert "api" in dash["components"]


class TestReportGenerator:
    """Test ReportGenerator."""
    
    def test_generate_daily_report(self, report_generator, test_db):
        """Test generating daily report."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        summary = DailyMetricsSummary(
            id="daily-report-1",
            date=today,
            total_requests=1500,
            average_request_time=130.0
        )
        test_db.add(summary)
        test_db.commit()
        
        report = report_generator.generate_daily_report(today)
        
        assert "date" in report
        assert "report_type" in report
        assert report["report_type"] == "daily"
    
    def test_generate_weekly_report(self, report_generator, test_db):
        """Test generating weekly report."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(7):
            summary = DailyMetricsSummary(
                id=f"weekly-{i}",
                date=today - timedelta(days=i),
                total_requests=1000 + i * 100
            )
            test_db.add(summary)
        test_db.commit()
        
        report = report_generator.generate_weekly_report(today)
        
        assert report["report_type"] == "weekly"
        assert "daily_summaries" in report
        assert "period" in report
    
    def test_generate_monthly_report(self, report_generator, test_db):
        """Test generating monthly report."""
        today = datetime.utcnow()
        
        for i in range(30):
            summary = DailyMetricsSummary(
                id=f"monthly-{i}",
                date=today - timedelta(days=i),
                total_requests=1000
            )
            test_db.add(summary)
        test_db.commit()
        
        report = report_generator.generate_monthly_report(today.year, today.month)
        
        assert report["report_type"] == "monthly"
        assert "aggregates" in report
        assert "total_requests" in report["aggregates"]
    
    def test_export_report_json(self, report_generator):
        """Test exporting report as JSON."""
        report = {
            "date": "2024-01-01",
            "requests": 1000,
            "errors": 25
        }
        
        json_str = report_generator.export_report_json(report)
        
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["date"] == "2024-01-01"
    
    def test_export_report_csv(self, report_generator):
        """Test exporting report as CSV."""
        report = {
            "summary": {
                "requests": {
                    "total": 1000
                },
                "errors": 25
            }
        }
        
        csv_str = report_generator.export_report_csv(report, "daily")
        
        assert isinstance(csv_str, str)
        assert "Metric,Value" in csv_str


class TestMetricTypes:
    """Test MetricType enum."""
    
    def test_all_metric_types(self):
        """Test all metric types."""
        types = [
            MetricType.COUNTER,
            MetricType.GAUGE,
            MetricType.HISTOGRAM,
            MetricType.SUMMARY
        ]
        assert len(types) == 4
    
    def test_metric_type_values(self):
        """Test metric type values."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.SUMMARY.value == "summary"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
