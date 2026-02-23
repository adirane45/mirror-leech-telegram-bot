"""
Performance Profiler
Advanced performance monitoring and bottleneck detection

Phase 4: Performance Optimization
Created by: justadi
Date: February 8, 2026
"""

import time
import logging
import asyncio
import functools
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime
import psutil
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data"""
    name: str
    duration_ms: float
    timestamp: float
    memory_delta_mb: float = 0.0
    cpu_percent: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProfileStats:
    """Aggregated profile statistics"""
    function_name: str
    call_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    p50_time_ms: float = 0.0
    p95_time_ms: float = 0.0
    p99_time_ms: float = 0.0
    error_count: int = 0
    last_called: Optional[float] = None


class PerformanceProfiler:
    """
    Advanced performance profiler with bottleneck detection
    
    Features:
    - Function execution timing
    - Memory usage tracking
    - CPU usage monitoring
    - Slow operation detection
    - Statistical analysis (percentiles)
    - Historical data retention
    """
    
    def __init__(
        self,
        slow_threshold_ms: float = 1000.0,
        retention_size: int = 1000,
        enable_memory_tracking: bool = True,
        enable_cpu_tracking: bool = True
    ):
        self.slow_threshold_ms = slow_threshold_ms
        self.retention_size = retention_size
        self.enable_memory_tracking = enable_memory_tracking
        self.enable_cpu_tracking = enable_cpu_tracking
        
        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=retention_size))
        self.stats: Dict[str, ProfileStats] = {}
        
        # Bottleneck detection
        self.bottlenecks: List[PerformanceMetric] = []
        self.lock = threading.RLock()
        
        logger.info(
            f"PerformanceProfiler initialized (slow_threshold={slow_threshold_ms}ms, "
            f"retention={retention_size}, memory_tracking={enable_memory_tracking}, "
            f"cpu_tracking={enable_cpu_tracking})"
        )
    
    def profile(self, name: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
        """
        Decorator to profile function execution
        
        Usage:
            @profiler.profile(name="my_function")
            def my_function():
                pass
        """
        def decorator(func: Callable) -> Callable:
            func_name = name or f"{func.__module__}.{func.__name__}"
            
            if asyncio.iscoroutinefunction(func):
                @functools.wraps(func)
                async def async_wrapper(*args, **kwargs):
                    return await self._profile_async(func, func_name, context or {}, *args, **kwargs)
                return async_wrapper
            else:
                @functools.wraps(func)
                def sync_wrapper(*args, **kwargs):
                    return self._profile_sync(func, func_name, context or {}, *args, **kwargs)
                return sync_wrapper
        
        return decorator
    
    def _profile_sync(self, func: Callable, func_name: str, ctx: Dict[str, Any], *args, **kwargs):
        """Profile synchronous function"""
        process = psutil.Process()
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024 if self.enable_memory_tracking else 0
        start_cpu = process.cpu_percent() if self.enable_cpu_tracking else 0
        
        error_occurred = False
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error_occurred = True
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = process.memory_info().rss / 1024 / 1024 if self.enable_memory_tracking else 0
            end_cpu = process.cpu_percent() if self.enable_cpu_tracking else 0
            
            metric = PerformanceMetric(
                name=func_name,
                duration_ms=duration_ms,
                timestamp=start_time,
                memory_delta_mb=end_memory - start_memory,
                cpu_percent=end_cpu - start_cpu,
                context=ctx
            )
            
            self._record_metric(metric, error_occurred)
    
    async def _profile_async(self, func: Callable, func_name: str, ctx: Dict[str, Any], *args, **kwargs):
        """Profile asynchronous function"""
        process = psutil.Process()
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024 if self.enable_memory_tracking else 0
        start_cpu = process.cpu_percent() if self.enable_cpu_tracking else 0
        
        error_occurred = False
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            error_occurred = True
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = process.memory_info().rss / 1024 / 1024 if self.enable_memory_tracking else 0
            end_cpu = process.cpu_percent() if self.enable_cpu_tracking else 0
            
            metric = PerformanceMetric(
                name=func_name,
                duration_ms=duration_ms,
                timestamp=start_time,
                memory_delta_mb=end_memory - start_memory,
                cpu_percent=end_cpu - start_cpu,
                context=ctx
            )
            
            self._record_metric(metric, error_occurred)
    
    def _record_metric(self, metric: PerformanceMetric, error: bool = False):
        """Record performance metric"""
        with self.lock:
            # Store metric
            self.metrics[metric.name].append(metric)
            
            # Update stats
            if metric.name not in self.stats:
                self.stats[metric.name] = ProfileStats(function_name=metric.name)
            
            stats = self.stats[metric.name]
            stats.call_count += 1
            stats.total_time_ms += metric.duration_ms
            stats.avg_time_ms = stats.total_time_ms / stats.call_count
            stats.min_time_ms = min(stats.min_time_ms, metric.duration_ms)
            stats.max_time_ms = max(stats.max_time_ms, metric.duration_ms)
            stats.last_called = metric.timestamp
            
            if error:
                stats.error_count += 1
            
            # Update percentiles
            self._update_percentiles(metric.name)
            
            # Detect bottlenecks
            if metric.duration_ms > self.slow_threshold_ms:
                self.bottlenecks.append(metric)
                logger.warning(
                    f"Slow operation detected: {metric.name} took {metric.duration_ms:.2f}ms "
                    f"(threshold: {self.slow_threshold_ms}ms)"
                )
    
    def _update_percentiles(self, func_name: str):
        """Update percentile statistics"""
        metrics_list = list(self.metrics[func_name])
        if not metrics_list:
            return
        
        durations = sorted([m.duration_ms for m in metrics_list])
        stats = self.stats[func_name]
        
        n = len(durations)
        stats.p50_time_ms = durations[int(n * 0.50)] if n > 0 else 0
        stats.p95_time_ms = durations[int(n * 0.95)] if n > 0 else 0
        stats.p99_time_ms = durations[int(n * 0.99)] if n > 0 else 0
    
    def get_stats(self, func_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            if func_name:
                if func_name not in self.stats:
                    return {}
                stats = self.stats[func_name]
                return {
                    "function": stats.function_name,
                    "calls": stats.call_count,
                    "total_time_ms": round(stats.total_time_ms, 2),
                    "avg_time_ms": round(stats.avg_time_ms, 2),
                    "min_time_ms": round(stats.min_time_ms, 2),
                    "max_time_ms": round(stats.max_time_ms, 2),
                    "p50_time_ms": round(stats.p50_time_ms, 2),
                    "p95_time_ms": round(stats.p95_time_ms, 2),
                    "p99_time_ms": round(stats.p99_time_ms, 2),
                    "errors": stats.error_count,
                    "last_called": datetime.fromtimestamp(stats.last_called).isoformat() if stats.last_called else None
                }
            else:
                return {
                    func: self.get_stats(func)
                    for func in self.stats.keys()
                }
    
    def get_bottlenecks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get detected bottlenecks"""
        with self.lock:
            sorted_bottlenecks = sorted(
                self.bottlenecks,
                key=lambda m: m.duration_ms,
                reverse=True
            )[:limit]
            
            return [
                {
                    "function": m.name,
                    "duration_ms": round(m.duration_ms, 2),
                    "memory_delta_mb": round(m.memory_delta_mb, 2),
                    "cpu_percent": round(m.cpu_percent, 2),
                    "timestamp": datetime.fromtimestamp(m.timestamp).isoformat(),
                    "context": m.context
                }
                for m in sorted_bottlenecks
            ]
    
    def get_slowest_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest functions by average execution time"""
        with self.lock:
            sorted_stats = sorted(
                self.stats.values(),
                key=lambda s: s.avg_time_ms,
                reverse=True
            )[:limit]
            
            return [
                {
                    "function": s.function_name,
                    "avg_time_ms": round(s.avg_time_ms, 2),
                    "call_count": s.call_count,
                    "total_time_ms": round(s.total_time_ms, 2),
                    "p95_time_ms": round(s.p95_time_ms, 2),
                    "error_rate": round(s.error_count / s.call_count * 100, 2) if s.call_count > 0 else 0
                }
                for s in sorted_stats
            ]
    
    def clear_metrics(self, func_name: Optional[str] = None):
        """Clear stored metrics"""
        with self.lock:
            if func_name:
                if func_name in self.metrics:
                    self.metrics[func_name].clear()
                if func_name in self.stats:
                    del self.stats[func_name]
            else:
                self.metrics.clear()
                self.stats.clear()
                self.bottlenecks.clear()
        
        logger.info(f"Cleared metrics for: {func_name or 'all functions'}")
    
    def export_report(self) -> Dict[str, Any]:
        """Export comprehensive performance report"""
        with self.lock:
            return {
                "summary": {
                    "total_functions": len(self.stats),
                    "total_calls": sum(s.call_count for s in self.stats.values()),
                    "total_errors": sum(s.error_count for s in self.stats.values()),
                    "total_bottlenecks": len(self.bottlenecks)
                },
                "slowest_functions": self.get_slowest_functions(10),
                "bottlenecks": self.get_bottlenecks(10),
                "all_stats": self.get_stats(),
                "configuration": {
                    "slow_threshold_ms": self.slow_threshold_ms,
                    "retention_size": self.retention_size,
                    "memory_tracking": self.enable_memory_tracking,
                    "cpu_tracking": self.enable_cpu_tracking
                }
            }


# Singleton instance
_profiler_instance: Optional[PerformanceProfiler] = None


def get_profiler(
    slow_threshold_ms: float = 1000.0,
    retention_size: int = 1000,
    enable_memory_tracking: bool = True,
    enable_cpu_tracking: bool = True
) -> PerformanceProfiler:
    """Get singleton profiler instance"""
    global _profiler_instance
    if _profiler_instance is None:
        _profiler_instance = PerformanceProfiler(
            slow_threshold_ms=slow_threshold_ms,
            retention_size=retention_size,
            enable_memory_tracking=enable_memory_tracking,
            enable_cpu_tracking=enable_cpu_tracking
        )
    return _profiler_instance


# Convenience decorator
def profile(name: Optional[str] = None, context: Optional[Dict[str, Any]] = None):
    """
    Convenience decorator for profiling functions
    
    Usage:
        @profile(name="my_function")
        def my_function():
            pass
    """
    profiler = get_profiler()
    return profiler.profile(name=name, context=context)
