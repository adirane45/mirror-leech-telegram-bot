"""
Performance Profiler - Operation Monitoring and Analysis
Tracks performance metrics and identifies bottlenecks
Safe Innovation Path - Phase 2

Enhanced by: justadi
Date: February 5, 2026
"""

import time
import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import Dict, Optional, List
from datetime import datetime, timedelta, UTC
from collections import defaultdict
import statistics
from logging import getLogger

from .config_manager import Config

LOGGER = getLogger(__name__)


class PerformanceMetric:
    """Represents a single performance metric"""

    def __init__(self, operation: str, duration: float):
        self.operation = operation
        self.duration = duration
        self.timestamp = datetime.now(UTC)


class OperationStats:
    """Statistics for a specific operation"""

    def __init__(self, operation: str):
        self.operation = operation
        self.metrics: List[PerformanceMetric] = []
        self.call_count = 0
        self.total_duration = 0.0

    def add_metric(self, duration: float):
        """Add a performance metric"""
        self.metrics.append(PerformanceMetric(self.operation, duration))
        self.call_count += 1
        self.total_duration += duration

    def get_stats(self) -> Dict:
        """Get statistics for this operation"""
        if not self.metrics:
            return {}

        durations = [m.duration for m in self.metrics]

        return {
            "operation": self.operation,
            "call_count": self.call_count,
            "total_duration": self.total_duration,
            "average_duration": statistics.mean(durations),
            "median_duration": statistics.median(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "std_dev": statistics.stdev(durations) if len(durations) > 1 else 0,
        }


class Profiler:
    """
    Performance profiler for tracking operation metrics
    Can identify slow operations and bottlenecks
    """

    _instance = None
    _enabled = False
    _operation_stats: Dict[str, OperationStats] = {}
    _context_stack: List[tuple] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Profiler, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._operation_stats = {}
            self._context_stack = []
            self._initialized = True

    def enable(self):
        """Enable profiler"""
        self._enabled = getattr(Config, "ENABLE_PROFILER", False)
        
        if self._enabled:
            LOGGER.info("✅ Performance profiler enabled")
        else:
            LOGGER.debug("Performance profiler disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if profiler is enabled"""
        return self._enabled

    @contextmanager
    def profile_sync(self, operation: str):
        """
        Context manager for profiling synchronous operations

        Usage:
            with profiler.profile_sync("operation_name"):
                # code to profile
        """
        if not self._enabled:
            yield
            return

        start_time = time.time()

        try:
            yield
        finally:
            duration = time.time() - start_time
            self._record_metric(operation, duration)

    @asynccontextmanager
    async def profile_async(self, operation: str):
        """
        Context manager for profiling async operations

        Usage:
            async with profiler.profile_async("operation_name"):
                # async code to profile
        """
        if not self._enabled:
            yield
            return

        start_time = time.time()

        try:
            yield
        finally:
            duration = time.time() - start_time
            self._record_metric(operation, duration)

    def _record_metric(self, operation: str, duration: float):
        """Record a performance metric"""
        if operation not in self._operation_stats:
            self._operation_stats[operation] = OperationStats(operation)

        stats = self._operation_stats[operation]
        stats.add_metric(duration)

        # Log if operation is slow (> 5 seconds)
        if duration > 5.0:
            LOGGER.warning(
                f"Slow operation detected: {operation} took {duration:.2f}s"
            )

    def mark_operation(self, operation: str) -> "Timer":
        """
        Create a timer for manual profiling

        Usage:
            timer = profiler.mark_operation("my_operation")
            # ... code to profile
            timer.stop()
        """
        return Timer(self, operation) if self._enabled else DummyTimer()

    def get_stats(self, operation: Optional[str] = None) -> Dict:
        """
        Get statistics

        Args:
            operation: Specific operation to get stats for (None = all)

        Returns:
            Statistics dictionary
        """
        if not self._enabled:
            return {"enabled": False}

        if operation:
            if operation in self._operation_stats:
                stats = self._operation_stats[operation].get_stats()
                return {"enabled": True, "operation": stats} if stats else {"enabled": True}
            return {"enabled": True}

        # Return all stats
        all_stats = {}
        for op, op_stats in self._operation_stats.items():
            stats = op_stats.get_stats()
            if stats:
                all_stats[op] = stats

        return {"enabled": True, "operations": all_stats}

    def get_slow_operations(self, threshold: float = 1.0, limit: int = 10) -> List[Dict]:
        """
        Get operations that exceeded time threshold

        Args:
            threshold: Time threshold in seconds
            limit: Maximum number to return

        Returns:
            List of slow operations sorted by duration
        """
        if not self._enabled:
            return []

        slow_ops = []

        for op_stats in self._operation_stats.values():
            stats = op_stats.get_stats()
            if stats and stats.get("average_duration", 0) > threshold:
                slow_ops.append(stats)

        # Sort by average duration (slowest first)
        slow_ops.sort(key=lambda x: x.get("average_duration", 0), reverse=True)

        return slow_ops[:limit]

    def reset(self, operation: Optional[str] = None):
        """
        Reset statistics

        Args:
            operation: Specific operation to reset (None = all)
        """
        if not self._enabled:
            return

        if operation:
            if operation in self._operation_stats:
                del self._operation_stats[operation]
                LOGGER.debug(f"Reset stats for: {operation}")
        else:
            self._operation_stats.clear()
            LOGGER.debug("Reset all profiler stats")

    def cleanup_old_metrics(self, hours: int = 24) -> int:
        """
        Delete metrics older than specified hours

        Args:
            hours: Hours to keep metrics for

        Returns:
            Number of metrics deleted
        """
        if not self._enabled:
            return 0

        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
        total_deleted = 0

        for op_stats in self._operation_stats.values():
            initial_count = len(op_stats.metrics)

            # Keep only recent metrics
            op_stats.metrics = [
                m for m in op_stats.metrics
                if m.timestamp > cutoff_time
            ]

            deleted = initial_count - len(op_stats.metrics)
            total_deleted += deleted

        return total_deleted


class Timer:
    """Manual timer for profiling"""

    def __init__(self, profiler: Profiler, operation: str):
        self.profiler = profiler
        self.operation = operation
        self.start_time = time.time()

    def stop(self) -> float:
        """Stop timer and record metric"""
        duration = time.time() - self.start_time
        self.profiler._record_metric(self.operation, duration)
        return duration


class DummyTimer:
    """Dummy timer when profiler is disabled"""

    def stop(self) -> float:
        return 0.0


# Singleton instance
profiler = Profiler()
