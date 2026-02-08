"""
Phase 5: Advanced Analytics Dashboard
Real-time metrics visualization, historical trends, and custom report generation
"""

from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import json
import csv
import io
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class TimeSeries:
    """Time series data"""
    metric_name: str
    points: List[MetricPoint] = field(default_factory=list)
    
    def add_point(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Add data point"""
        point = MetricPoint(
            timestamp=datetime.now(UTC),
            value=value,
            labels=labels or {}
        )
        self.points.append(point)
    
    def get_values(self, start: Optional[datetime] = None, end: Optional[datetime] = None) -> List[float]:
        """Get values in time range"""
        points = self.points
        
        if start:
            points = [p for p in points if p.timestamp >= start]
        if end:
            points = [p for p in points if p.timestamp <= end]
        
        return [p.value for p in points]


@dataclass
class Report:
    """Analytics report"""
    report_id: str
    title: str
    description: str
    metrics: List[str]
    time_range: Tuple[datetime, datetime]
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AdvancedAnalyticsDashboard:
    """
    Advanced Analytics Dashboard
    
    Features:
    - Real-time metrics tracking
    - Historical trends analysis
    - Statistical aggregations (min, max, avg, percentiles)
    - Custom report generation
    - Export to CSV/JSON
    - Metric retention and cleanup
    - Time-based aggregations (hourly, daily, weekly)
    
    Usage:
        dashboard = AdvancedAnalyticsDashboard()
        
        # Track metrics
        dashboard.track_metric("downloads", 1500, {"status": "success"})
        dashboard.track_metric("response_time", 245.5)
        
        # Get statistics
        stats = dashboard.get_metric_stats("response_time", hours=24)
        
        # Generate report
        report = dashboard.generate_report(
            title="Daily Performance",
            metrics=["downloads", "response_time"],
            hours=24
        )
        
        # Export to CSV
        csv_data = dashboard.export_to_csv(report_id=report.report_id)
    """
    
    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
        
        # Time series storage
        self.time_series: Dict[str, TimeSeries] = {}  # metric_name -> TimeSeries
        
        # Reports
        self.reports: Dict[str, Report] = {}  # report_id -> Report
        
        # Real-time counters
        self.counters: Dict[str, float] = defaultdict(float)
        
        # Event history (ring buffer)
        self.event_history: deque = deque(maxlen=10000)
        
        logger.info(f"AdvancedAnalyticsDashboard initialized (retention={retention_days}d)")
    
    # ========================================================================
    # METRIC TRACKING
    # ========================================================================
    
    def track_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Track metric value
        
        Args:
            metric_name: Metric identifier
            value: Metric value
            labels: Optional labels for filtering
        """
        try:
            # Get or create time series
            if metric_name not in self.time_series:
                self.time_series[metric_name] = TimeSeries(metric_name=metric_name)
            
            # Add data point
            self.time_series[metric_name].add_point(value, labels)
            
            # Update counter
            self.counters[metric_name] += value
            
            # Add to event history
            self.event_history.append({
                'timestamp': datetime.now(UTC).isoformat(),
                'metric': metric_name,
                'value': value,
                'labels': labels or {}
            })
            
            logger.debug(f"Metric tracked: {metric_name}={value}")
            
        except Exception as e:
            logger.error(f"Metric tracking error: {e}")
    
    def increment_counter(self, metric_name: str, amount: float = 1.0) -> None:
        """Increment counter metric"""
        self.counters[metric_name] += amount
    
    def set_gauge(self, metric_name: str, value: float) -> None:
        """Set gauge metric (current value)"""
        self.track_metric(metric_name, value)
    
    # ========================================================================
    # STATISTICS & AGGREGATIONS
    # ========================================================================
    
    def get_metric_stats(
        self,
        metric_name: str,
        hours: Optional[int] = None,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for metric
        
        Returns:
            Dict with min, max, avg, median, p95, p99, count
        """
        try:
            if metric_name not in self.time_series:
                return {}
            
            # Calculate time range
            end = datetime.now(UTC)
            start = None
            if hours:
                start = end - timedelta(hours=hours)
            elif days:
                start = end - timedelta(days=days)
            
            # Get values
            values = self.time_series[metric_name].get_values(start, end)
            
            if not values:
                return {}
            
            # Calculate statistics
            stats = {
                'metric': metric_name,
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': statistics.mean(values),
                'median': statistics.median(values),
                'stdev': statistics.stdev(values) if len(values) > 1 else 0,
                'sum': sum(values)
            }
            
            # Calculate percentiles
            if len(values) >= 2:
                sorted_values = sorted(values)
                stats['p50'] = self._percentile(sorted_values, 50)
                stats['p95'] = self._percentile(sorted_values, 95)
                stats['p99'] = self._percentile(sorted_values, 99)
            
            return stats
            
        except Exception as e:
            logger.error(f"Stats calculation error: {e}")
            return {}
    
    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_trend(
        self,
        metric_name: str,
        hours: int = 24,
        buckets: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get trend for metric (aggregated into time buckets)
        
        Args:
            metric_name: Metric to analyze
            hours: Time range in hours
            buckets: Number of time buckets
        
        Returns:
            List of {timestamp, avg, min, max, count}
        """
        try:
            if metric_name not in self.time_series:
                return []
            
            # Calculate time range
            end = datetime.now(UTC)
            start = end - timedelta(hours=hours)
            bucket_size = timedelta(hours=hours / buckets)
            
            # Get all points
            time_series = self.time_series[metric_name]
            points = [p for p in time_series.points if start <= p.timestamp <= end]
            
            # Group into buckets
            trend = []
            for i in range(buckets):
                bucket_start = start + (bucket_size * i)
                bucket_end = bucket_start + bucket_size
                
                bucket_points = [
                    p for p in points 
                    if bucket_start <= p.timestamp < bucket_end
                ]
                
                if bucket_points:
                    values = [p.value for p in bucket_points]
                    trend.append({
                        'timestamp': bucket_start.isoformat(),
                        'avg': statistics.mean(values),
                        'min': min(values),
                        'max': max(values),
                        'count': len(values)
                    })
                else:
                    trend.append({
                        'timestamp': bucket_start.isoformat(),
                        'avg': 0,
                        'min': 0,
                        'max': 0,
                        'count': 0
                    })
            
            return trend
            
        except Exception as e:
            logger.error(f"Trend calculation error: {e}")
            return []
    
    # ========================================================================
    # CUSTOM REPORTS
    # ========================================================================
    
    def generate_report(
        self,
        title: str,
        metrics: List[str],
        description: str = "",
        hours: Optional[int] = None,
        days: Optional[int] = None
    ) -> Report:
        """
        Generate custom analytics report
        
        Args:
            title: Report title
            metrics: List of metrics to include
            description: Report description
            hours: Time range in hours
            days: Time range in days
        
        Returns:
            Report object
        """
        try:
            import secrets
            report_id = secrets.token_urlsafe(16)
            
            # Calculate time range
            end = datetime.now(UTC)
            start = end
            if hours:
                start = end - timedelta(hours=hours)
            elif days:
                start = end - timedelta(days=days)
            else:
                start = end - timedelta(days=1)  # Default: last 24 hours
            
            # Collect data for each metric
            report_data = {}
            for metric_name in metrics:
                # Get statistics
                stats = self.get_metric_stats(
                    metric_name,
                    hours=hours,
                    days=days
                )
                
                # Get trend
                trend = self.get_trend(
                    metric_name,
                    hours=hours or (days * 24 if days else 24),
                    buckets=24
                )
                
                report_data[metric_name] = {
                    'statistics': stats,
                    'trend': trend
                }
            
            # Create report
            report = Report(
                report_id=report_id,
                title=title,
                description=description,
                metrics=metrics,
                time_range=(start, end),
                data=report_data
            )
            
            # Store report
            self.reports[report_id] = report
            
            logger.info(f"Report generated: {title} (id={report_id})")
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            raise
    
    def get_report(self, report_id: str) -> Optional[Report]:
        """Get report by ID"""
        return self.reports.get(report_id)
    
    def list_reports(self, limit: int = 50) -> List[Report]:
        """List recent reports"""
        reports = list(self.reports.values())
        reports.sort(key=lambda r: r.created_at, reverse=True)
        return reports[:limit]
    
    # ========================================================================
    # EXPORT FUNCTIONALITY
    # ========================================================================
    
    def export_to_json(self, report_id: str) -> str:
        """
        Export report to JSON
        
        Returns:
            JSON string
        """
        try:
            report = self.reports.get(report_id)
            if not report:
                raise ValueError(f"Report not found: {report_id}")
            
            export_data = {
                'report_id': report.report_id,
                'title': report.title,
                'description': report.description,
                'created_at': report.created_at.isoformat(),
                'time_range': {
                    'start': report.time_range[0].isoformat(),
                    'end': report.time_range[1].isoformat()
                },
                'metrics': report.metrics,
                'data': report.data
            }
            
            return json.dumps(export_data, indent=2)
            
        except Exception as e:
            logger.error(f"JSON export error: {e}")
            raise
    
    def export_to_csv(self, report_id: str) -> str:
        """
        Export report to CSV
        
        Returns:
            CSV string
        """
        try:
            report = self.reports.get(report_id)
            if not report:
                raise ValueError(f"Report not found: {report_id}")
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Metric', 'Count', 'Min', 'Max', 'Avg', 'Median', 'P95', 'P99'])
            
            # Write data
            for metric_name in report.metrics:
                if metric_name in report.data:
                    stats = report.data[metric_name].get('statistics', {})
                    writer.writerow([
                        metric_name,
                        stats.get('count', 0),
                        stats.get('min', 0),
                        stats.get('max', 0),
                        round(stats.get('avg', 0), 2),
                        round(stats.get('median', 0), 2),
                        round(stats.get('p95', 0), 2),
                        round(stats.get('p99', 0), 2)
                    ])
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"CSV export error: {e}")
            raise
    
    # ========================================================================
    # REAL-TIME DASHBOARD DATA
    # ========================================================================
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get real-time dashboard data
        
        Returns comprehensive dashboard view
        """
        try:
            # Get top metrics by activity
            active_metrics = sorted(
                self.time_series.keys(),
                key=lambda m: len(self.time_series[m].points),
                reverse=True
            )[:10]
            
            # Collect recent stats for active metrics
            metrics_data = {}
            for metric_name in active_metrics:
                metrics_data[metric_name] = self.get_metric_stats(metric_name, hours=1)
            
            # Get recent events
            recent_events = list(self.event_history)[-100:]
            
            return {
                'timestamp': datetime.now(UTC).isoformat(),
                'active_metrics': active_metrics,
                'metrics_data': metrics_data,
                'counters': dict(self.counters),
                'recent_events': recent_events,
                'total_metrics': len(self.time_series),
                'total_data_points': sum(len(ts.points) for ts in self.time_series.values()),
                'reports_generated': len(self.reports)
            }
            
        except Exception as e:
            logger.error(f"Dashboard data error: {e}")
            return {}
    
    # ========================================================================
    # MAINTENANCE
    # ========================================================================
    
    def cleanup_old_data(self) -> int:
        """
        Remove data older than retention period
        
        Returns:
            Number of points removed
        """
        try:
            cutoff = datetime.now(UTC) - timedelta(days=self.retention_days)
            removed = 0
            
            for time_series in self.time_series.values():
                original_count = len(time_series.points)
                time_series.points = [p for p in time_series.points if p.timestamp >= cutoff]
                removed += original_count - len(time_series.points)
            
            logger.info(f"Cleaned up {removed} old data points")
            
            return removed
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            return 0
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            total_points = sum(len(ts.points) for ts in self.time_series.values())
            
            return {
                'total_metrics': len(self.time_series),
                'total_data_points': total_points,
                'total_reports': len(self.reports),
                'event_history_size': len(self.event_history),
                'retention_days': self.retention_days
            }
        except Exception as e:
            logger.error(f"Storage stats error: {e}")
            return {}


# ============================================================================
# SINGLETON
# ============================================================================

_analytics_dashboard: Optional[AdvancedAnalyticsDashboard] = None


def get_analytics_dashboard(retention_days: int = 30) -> AdvancedAnalyticsDashboard:
    """Get analytics dashboard singleton"""
    global _analytics_dashboard
    if _analytics_dashboard is None:
        _analytics_dashboard = AdvancedAnalyticsDashboard(retention_days=retention_days)
    return _analytics_dashboard
