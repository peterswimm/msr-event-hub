"""FastAPI routes for analytics and metrics."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from analytics import (
    MetricsAggregator, DashboardAPI, ReportGenerator,
    MetricType, MetricsSnapshot, DailyMetricsSummary
)
from infra.database import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def get_metrics_aggregator(db: Session = Depends(get_db)) -> MetricsAggregator:
    """Dependency for MetricsAggregator."""
    return MetricsAggregator(db)


def get_dashboard_api(db: Session = Depends(get_db)) -> DashboardAPI:
    """Dependency for DashboardAPI."""
    return DashboardAPI(db)


def get_report_generator(db: Session = Depends(get_db)) -> ReportGenerator:
    """Dependency for ReportGenerator."""
    return ReportGenerator(db)


@router.get("/metrics/snapshot")
async def record_metric(
    metric_name: str,
    value: float,
    metric_type: str = "gauge",
    aggregator: MetricsAggregator = Depends(get_metrics_aggregator)
) -> dict:
    """Record a metrics snapshot.
    
    Args:
        metric_name: Metric name
        value: Metric value
        metric_type: Type of metric
        aggregator: MetricsAggregator dependency
        
    Returns:
        Snapshot ID and confirmation
    """
    try:
        snapshot_id = aggregator.record_snapshot(
            metric_name=metric_name,
            value=value,
            metric_type=MetricType[metric_type.upper()]
        )
        
        return {
            "snapshot_id": snapshot_id,
            "metric_name": metric_name,
            "value": value,
            "recorded_at": datetime.utcnow().isoformat()
        }
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid metric_type. Must be one of: {', '.join([t.value for t in MetricType])}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{metric_name}")
async def get_metric_history(
    metric_name: str,
    hours: int = 24,
    aggregator: MetricsAggregator = Depends(get_metrics_aggregator)
) -> dict:
    """Get metric history.
    
    Args:
        metric_name: Metric name
        hours: Hours of history
        aggregator: MetricsAggregator dependency
        
    Returns:
        Metric history
    """
    try:
        end = datetime.utcnow()
        start = end - timedelta(hours=hours)
        
        metrics = aggregator.get_metric_range(metric_name, start, end)
        
        return {
            "metric_name": metric_name,
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "hours": hours
            },
            "data_points": len(metrics),
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/realtime")
async def realtime_dashboard(
    dashboard: DashboardAPI = Depends(get_dashboard_api)
) -> dict:
    """Get real-time metrics dashboard.
    
    Args:
        dashboard: DashboardAPI dependency
        
    Returns:
        Real-time dashboard data
    """
    try:
        return dashboard.get_realtime_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/performance")
async def performance_dashboard(
    hours: int = 24,
    dashboard: DashboardAPI = Depends(get_dashboard_api)
) -> dict:
    """Get performance metrics dashboard.
    
    Args:
        hours: Hours to include
        dashboard: DashboardAPI dependency
        
    Returns:
        Performance dashboard data
    """
    try:
        return dashboard.get_performance_dashboard(hours=hours)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/health")
async def health_dashboard(
    dashboard: DashboardAPI = Depends(get_dashboard_api)
) -> dict:
    """Get system health dashboard.
    
    Args:
        dashboard: DashboardAPI dependency
        
    Returns:
        Health status
    """
    try:
        return dashboard.get_health_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/daily")
async def get_daily_report(
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    generator: ReportGenerator = Depends(get_report_generator)
) -> dict:
    """Get daily metrics report.
    
    Args:
        date: Date string (YYYY-MM-DD)
        generator: ReportGenerator dependency
        
    Returns:
        Daily report
    """
    try:
        report_date = datetime.strptime(date, "%Y-%m-%d")
        return generator.generate_daily_report(report_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/weekly")
async def get_weekly_report(
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    generator: ReportGenerator = Depends(get_report_generator)
) -> dict:
    """Get weekly metrics report.
    
    Args:
        end_date: End date string (YYYY-MM-DD)
        generator: ReportGenerator dependency
        
    Returns:
        Weekly report
    """
    try:
        report_end = datetime.strptime(end_date, "%Y-%m-%d")
        return generator.generate_weekly_report(report_end)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/monthly")
async def get_monthly_report(
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)"),
    generator: ReportGenerator = Depends(get_report_generator)
) -> dict:
    """Get monthly metrics report.
    
    Args:
        year: Year
        month: Month (1-12)
        generator: ReportGenerator dependency
        
    Returns:
        Monthly report
    """
    try:
        if not (1 <= month <= 12):
            raise ValueError("Month must be 1-12")
        
        return generator.generate_monthly_report(year, month)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/daily/export")
async def export_daily_report(
    date: str = Query(..., description="Date (YYYY-MM-DD)"),
    format: str = Query("json", description="Export format (json or csv)"),
    generator: ReportGenerator = Depends(get_report_generator)
) -> dict:
    """Export daily report.
    
    Args:
        date: Date string (YYYY-MM-DD)
        format: Export format (json or csv)
        generator: ReportGenerator dependency
        
    Returns:
        Exported report content
    """
    try:
        report_date = datetime.strptime(date, "%Y-%m-%d")
        report = generator.generate_daily_report(report_date)
        
        if format == "csv":
            content = generator.export_report_csv(report, "daily")
            return {"format": "csv", "content": content}
        else:
            content = generator.export_report_json(report)
            return {"format": "json", "content": content}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summaries")
async def get_daily_summaries(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    aggregator: MetricsAggregator = Depends(get_metrics_aggregator)
) -> dict:
    """Get daily metrics summaries.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        aggregator: MetricsAggregator dependency
        
    Returns:
        Daily summaries
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        summaries = aggregator.get_daily_summaries(start, end)
        
        return {
            "period": {
                "start": start.isoformat(),
                "end": end.isoformat()
            },
            "count": len(summaries),
            "summaries": summaries
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
