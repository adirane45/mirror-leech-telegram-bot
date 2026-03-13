"""
Command Failure Monitoring & Alerting System

Tracks command execution health and sends alerts for failures.
Integrates with existing HealthMonitor for component-level recovery.
"""

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, TypeAlias

from .. import LOGGER


class CommandStatus(str, Enum):
    """Command execution status"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"


@dataclass
class CommandExecution:
    """Record of a single command execution"""
    command: str
    user_id: int
    timestamp: datetime
    status: CommandStatus
    duration_ms: float
    error: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class CommandMetrics:
    """Aggregated metrics for a command"""
    command: str
    total_executions: int = 0
    successful: int = 0
    failed: int = 0
    timeout: int = 0
    error: int = 0
    avg_duration_ms: float = 0.0
    last_execution: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_executions == 0:
            return 0.0
        return (self.successful / self.total_executions) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage"""
        return 100.0 - self.success_rate


AlertCallback: TypeAlias = Callable[[str, CommandMetrics, CommandExecution], Awaitable[object]]


class CommandHealthMonitor:
    """Monitor command execution health and track failures"""

    _instance: Optional['CommandHealthMonitor'] = None

    def __new__(cls) -> 'CommandHealthMonitor':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize command health monitor"""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._metrics: Dict[str, CommandMetrics] = defaultdict(
            lambda: CommandMetrics(command='')
        )
        self._recent_executions: Dict[str, list[CommandExecution]] = defaultdict(list)
        self._alert_callbacks: Dict[str, list[AlertCallback]] = defaultdict(list)
        self._failure_threshold = 3  # Consecutive failures before alert
        self._window_minutes = 10  # Time window for metrics
        self._enabled = False

    @classmethod
    def get_instance(cls) -> 'CommandHealthMonitor':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def enable(self) -> None:
        """Enable command health monitoring"""
        self._enabled = True
        LOGGER.info("✅ Command Health Monitor enabled")

    def disable(self) -> None:
        """Disable command health monitoring"""
        self._enabled = False
        LOGGER.info("❌ Command Health Monitor disabled")

    def register_alert_callback(self, command: str, callback: AlertCallback) -> None:
        """
        Register a callback to execute when command fails.

        Callback signature: async def callback(command: str, metrics: CommandMetrics, execution: CommandExecution)
        """
        self._alert_callbacks[command].append(callback)
        LOGGER.debug(f"Registered alert callback for /{command}")

    def set_failure_threshold(self, threshold: int) -> None:
        """Set consecutive failure threshold before alert"""
        self._failure_threshold = threshold

    def _build_execution_record(
        self,
        command: str,
        user_id: int,
        status: CommandStatus,
        duration_ms: float,
        error: Optional[str],
        error_type: Optional[str],
        timestamp: datetime,
    ) -> CommandExecution:
        return CommandExecution(
            command=command,
            user_id=user_id,
            timestamp=timestamp,
            status=status,
            duration_ms=duration_ms,
            error=error,
            error_type=error_type,
        )

    def _get_or_create_metrics(self, command: str) -> CommandMetrics:
        if command not in self._metrics:
            self._metrics[command] = CommandMetrics(command=command)
        return self._metrics[command]

    def _update_status_metrics(
        self,
        metrics: CommandMetrics,
        status: CommandStatus,
        timestamp: datetime,
        duration_ms: float,
        error: Optional[str],
    ) -> None:
        if status == CommandStatus.SUCCESS:
            metrics.successful += 1
            metrics.consecutive_failures = 0
            return

        metrics.consecutive_failures += 1
        metrics.last_failure = timestamp
        if status == CommandStatus.FAILURE:
            metrics.failed += 1
            metrics.last_error = error
        elif status == CommandStatus.TIMEOUT:
            metrics.timeout += 1
            metrics.last_error = f"Timeout (>{duration_ms}ms)"
        elif status == CommandStatus.ERROR:
            metrics.error += 1
            metrics.last_error = error

    def _update_avg_duration(self, metrics: CommandMetrics, duration_ms: float) -> None:
        if metrics.successful <= 0:
            return
        metrics.avg_duration_ms = (
            (metrics.avg_duration_ms * (metrics.total_executions - 1) + duration_ms)
            / metrics.total_executions
        )

    def _trim_old_executions(self, command: str, timestamp: datetime) -> None:
        cutoff = timestamp - timedelta(minutes=self._window_minutes)
        self._recent_executions[command] = [
            e for e in self._recent_executions[command]
            if e.timestamp > cutoff
        ]

    async def record_execution(
        self,
        command: str,
        user_id: int,
        status: CommandStatus,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
        error_type: Optional[str] = None
    ) -> None:
        """Record a command execution"""
        if not self._enabled:
            return

        try:
            timestamp = datetime.now()
            execution = self._build_execution_record(
                command,
                user_id,
                status,
                duration_ms,
                error,
                error_type,
                timestamp,
            )

            metrics = self._get_or_create_metrics(command)

            # Update metrics
            metrics.total_executions += 1
            metrics.last_execution = timestamp

            self._update_status_metrics(
                metrics,
                status,
                timestamp,
                duration_ms,
                error,
            )
            self._update_avg_duration(metrics, duration_ms)

            # Store in recent executions
            self._recent_executions[command].append(execution)

            # Clean old executions (keep only recent)
            self._trim_old_executions(command, timestamp)

            # Trigger alerts if failure threshold exceeded
            if metrics.consecutive_failures >= self._failure_threshold:
                await self._trigger_alert(command, metrics, execution)

            # Log command execution
            LOGGER.debug(
                f"CMD_HEALTH | cmd=/{command} | user={user_id} | "
                f"status={status.value} | duration={duration_ms:.0f}ms | "
                f"success_rate={metrics.success_rate:.1f}%"
            )

        except Exception as e:
            LOGGER.error(f"Error recording command execution: {e}")

    async def _trigger_alert(
        self,
        command: str,
        metrics: CommandMetrics,
        execution: CommandExecution
    ) -> None:
        """Trigger alert callbacks for failed command"""
        if command not in self._alert_callbacks:
            LOGGER.warning(
                f"⚠️ Command /{command} failed {metrics.consecutive_failures} times "
                f"(threshold: {self._failure_threshold}) but no alert callback registered"
            )
            return

        LOGGER.warning(
            f"🚨 ALERT: Command /{command} failed {metrics.consecutive_failures} times. "
            f"Success rate: {metrics.success_rate:.1f}%. Last error: {metrics.last_error}"
        )

        # Execute all callbacks
        tasks = [
            callback(command, metrics, execution)
            for callback in self._alert_callbacks[command]
        ]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def get_metrics(self, command: str) -> Optional[CommandMetrics]:
        """Get metrics for a command"""
        return self._metrics.get(command)

    def get_all_metrics(self) -> Dict[str, CommandMetrics]:
        """Get all command metrics"""
        return dict(self._metrics)

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall command health summary"""
        if not self._metrics:
            return {"status": "no_data", "commands": 0}

        total_commands = len(self._metrics)
        healthy = 0
        degraded = 0
        failing = 0

        for metrics in self._metrics.values():
            if metrics.success_rate >= 95:
                healthy += 1
            elif metrics.success_rate >= 80:
                degraded += 1
            else:
                failing += 1

        return {
            "status": "healthy" if failing == 0 else ("degraded" if degraded > 0 else "failing"),
            "total_commands": total_commands,
            "healthy": healthy,
            "degraded": degraded,
            "failing": failing,
            "timestamp": datetime.now().isoformat()
        }

    def reset_metrics(self, command: Optional[str] = None) -> None:
        """Reset metrics for command or all commands"""
        if command:
            if command in self._metrics:
                self._metrics[command] = CommandMetrics(command=command)
            if command in self._recent_executions:
                self._recent_executions[command] = []
        else:
            self._metrics.clear()
            self._recent_executions.clear()


# Global instance
command_health_monitor = CommandHealthMonitor.get_instance()
