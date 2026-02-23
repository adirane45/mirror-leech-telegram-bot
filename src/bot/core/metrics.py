"""
Prometheus Metrics - Performance and Health Monitoring
Exposes metrics for Prometheus scraping
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

from prometheus_client import (
    Counter, Gauge, Histogram, Summary,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from typing import Optional
import time
import psutil

from .. import LOGGER
from .config_manager import Config


class MetricsCollector:
    """
    Collects and exposes Prometheus metrics
    Transparent to existing code - can be disabled via config
    """
    
    def __init__(self):
        self._enabled = False
        self._registry = CollectorRegistry()
        
        # ==================== DOWNLOAD METRICS ====================
        self.downloads_total = Counter(
            'mltb_downloads_total',
            'Total number of downloads',
            ['status', 'source_type'],
            registry=self._registry
        )
        
        self.download_size_bytes = Histogram(
            'mltb_download_size_bytes',
            'Download size distribution in bytes',
            ['source_type'],
            buckets=[1e6, 10e6, 100e6, 500e6, 1e9, 5e9, 10e9, 50e9],
            registry=self._registry
        )
        
        self.download_duration_seconds = Histogram(
            'mltb_download_duration_seconds',
            'Download duration in seconds',
            ['source_type'],
            buckets=[10, 30, 60, 300, 600, 1800, 3600, 7200],
            registry=self._registry
        )
        
        self.download_speed_bytes_per_second = Gauge(
            'mltb_download_speed_bytes_per_second',
            'Current download speed in bytes per second',
            ['task_id'],
            registry=self._registry
        )
        
        self.active_downloads = Gauge(
            'mltb_active_downloads',
            'Number of currently active downloads',
            registry=self._registry
        )
        
        # ==================== UPLOAD METRICS ====================
        self.uploads_total = Counter(
            'mltb_uploads_total',
            'Total number of uploads',
            ['status', 'destination'],
            registry=self._registry
        )
        
        self.upload_size_bytes = Histogram(
            'mltb_upload_size_bytes',
            'Upload size distribution in bytes',
            ['destination'],
            buckets=[1e6, 10e6, 100e6, 500e6, 1e9, 5e9, 10e9, 50e9],
            registry=self._registry
        )
        
        self.upload_duration_seconds = Histogram(
            'mltb_upload_duration_seconds',
            'Upload duration in seconds',
            ['destination'],
            buckets=[10, 30, 60, 300, 600, 1800, 3600, 7200],
            registry=self._registry
        )
        
        self.active_uploads = Gauge(
            'mltb_active_uploads',
            'Number of currently active uploads',
            registry=self._registry
        )
        
        # ==================== TASK METRICS ====================
        self.tasks_total = Counter(
            'mltb_tasks_total',
            'Total number of tasks',
            ['type', 'status'],
            registry=self._registry
        )
        
        self.active_tasks = Gauge(
            'mltb_active_tasks',
            'Number of currently active tasks',
            ['type'],
            registry=self._registry
        )
        
        self.queued_tasks = Gauge(
            'mltb_queued_tasks',
            'Number of tasks in queue',
            ['queue_name'],
            registry=self._registry
        )
        
        self.task_processing_time = Summary(
            'mltb_task_processing_seconds',
            'Task processing time in seconds',
            ['task_type'],
            registry=self._registry
        )
        
        # ==================== USER METRICS ====================
        self.active_users = Gauge(
            'mltb_active_users',
            'Number of active users',
            registry=self._registry
        )
        
        self.commands_total = Counter(
            'mltb_commands_total',
            'Total number of commands executed',
            ['command', 'user_type'],
            registry=self._registry
        )
        
        self.user_requests = Counter(
            'mltb_user_requests_total',
            'Total user requests',
            ['user_id', 'request_type'],
            registry=self._registry
        )
        
        # ==================== SYSTEM METRICS ====================
        self.cpu_usage_percent = Gauge(
            'mltb_cpu_usage_percent',
            'CPU usage percentage',
            registry=self._registry
        )
        
        self.memory_usage_bytes = Gauge(
            'mltb_memory_usage_bytes',
            'Memory usage in bytes',
            registry=self._registry
        )
        
        self.memory_usage_percent = Gauge(
            'mltb_memory_usage_percent',
            'Memory usage percentage',
            registry=self._registry
        )
        
        self.disk_usage_bytes = Gauge(
            'mltb_disk_usage_bytes',
            'Disk usage in bytes',
            ['mount_point'],
            registry=self._registry
        )
        
        self.disk_usage_percent = Gauge(
            'mltb_disk_usage_percent',
            'Disk usage percentage',
            ['mount_point'],
            registry=self._registry
        )
        
        self.network_sent_bytes = Counter(
            'mltb_network_sent_bytes_total',
            'Total bytes sent over network',
            registry=self._registry
        )
        
        self.network_received_bytes = Counter(
            'mltb_network_received_bytes_total',
            'Total bytes received over network',
            registry=self._registry
        )
        
        # ==================== ERROR METRICS ====================
        self.errors_total = Counter(
            'mltb_errors_total',
            'Total number of errors',
            ['error_type', 'severity'],
            registry=self._registry
        )
        
        self.api_errors = Counter(
            'mltb_api_errors_total',
            'API errors',
            ['service', 'error_code'],
            registry=self._registry
        )
        
        # ==================== CACHE METRICS ====================
        self.cache_hits = Counter(
            'mltb_cache_hits_total',
            'Cache hits',
            ['cache_type'],
            registry=self._registry
        )
        
        self.cache_misses = Counter(
            'mltb_cache_misses_total',
            'Cache misses',
            ['cache_type'],
            registry=self._registry
        )
        
        # ==================== APPLICATION METRICS ====================
        self.app_info = Gauge(
            'mltb_app_info',
            'Application information',
            ['version', 'python_version'],
            registry=self._registry
        )
        
        self.uptime_seconds = Gauge(
            'mltb_uptime_seconds',
            'Application uptime in seconds',
            registry=self._registry
        )
        
        self._start_time = time.time()
        
    def enable(self):
        """Enable metrics collection"""
        self._enabled = getattr(Config, 'ENABLE_METRICS', False)
        if self._enabled:
            LOGGER.info("✅ Prometheus metrics enabled")
            self._update_app_info()
        else:
            LOGGER.info("Prometheus metrics disabled")
    
    def _update_app_info(self):
        """Update application info metric"""
        import sys
        version = "3.1.0"  # Updated version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.app_info.labels(version=version, python_version=python_version).set(1)
    
    def is_enabled(self) -> bool:
        """Check if metrics are enabled"""
        return self._enabled
    
    # ==================== RECORDING METHODS ====================
    
    def record_download(self, source_type: str, size: int, duration: float, status: str = "success"):
        """Record a download"""
        if not self._enabled:
            return
        
        self.downloads_total.labels(status=status, source_type=source_type).inc()
        self.download_size_bytes.labels(source_type=source_type).observe(size)
        self.download_duration_seconds.labels(source_type=source_type).observe(duration)
    
    def record_upload(self, destination: str, size: int, duration: float, status: str = "success"):
        """Record an upload"""
        if not self._enabled:
            return
        
        self.uploads_total.labels(status=status, destination=destination).inc()
        self.upload_size_bytes.labels(destination=destination).observe(size)
        self.upload_duration_seconds.labels(destination=destination).observe(duration)
    
    def record_command(self, command: str, user_type: str = "user"):
        """Record a command execution"""
        if not self._enabled:
            return
        
        self.commands_total.labels(command=command, user_type=user_type).inc()
    
    def record_error(self, error_type: str, severity: str = "error"):
        """Record an error"""
        if not self._enabled:
            return
        
        self.errors_total.labels(error_type=error_type, severity=severity).inc()
    
    def record_cache_hit(self, cache_type: str = "redis"):
        """Record a cache hit"""
        if not self._enabled:
            return
        
        self.cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str = "redis"):
        """Record a cache miss"""
        if not self._enabled:
            return
        
        self.cache_misses.labels(cache_type=cache_type).inc()
    
    # ==================== SYSTEM MONITORING ====================
    
    def update_system_metrics(self):
        """Update system resource metrics"""
        if not self._enabled:
            return
        
        try:
            # CPU
            self.cpu_usage_percent.set(psutil.cpu_percent(interval=1))
            
            # Memory
            mem = psutil.virtual_memory()
            self.memory_usage_bytes.set(mem.used)
            self.memory_usage_percent.set(mem.percent)
            
            # Disk
            disk = psutil.disk_usage('/')
            self.disk_usage_bytes.labels(mount_point='/').set(disk.used)
            self.disk_usage_percent.labels(mount_point='/').set(disk.percent)
            
            # Network
            net = psutil.net_io_counters()
            self.network_sent_bytes.inc(net.bytes_sent)
            self.network_received_bytes.inc(net.bytes_recv)
            
            # Uptime
            self.uptime_seconds.set(time.time() - self._start_time)
            
        except Exception as e:
            LOGGER.debug(f"Error updating system metrics: {e}")
    
    # ==================== METRICS EXPORT ====================
    
    def generate_metrics(self) -> bytes:
        """Generate Prometheus metrics in text format"""
        if not self._enabled:
            return b"# Metrics disabled\n"
        
        # Update system metrics before generating
        self.update_system_metrics()
        
        return generate_latest(self._registry)
    
    def get_content_type(self) -> str:
        """Get content type for metrics endpoint"""
        return CONTENT_TYPE_LATEST


# Global metrics instance
metrics = MetricsCollector()
