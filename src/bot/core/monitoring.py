"""
Monitoring & Observability Enhancements for Phase 7

Implements:
- Enhanced metrics collection
- Distributed tracing
- Log aggregation support
- Health check endpoints
- SLA monitoring
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of health check"""
    status: HealthStatus
    timestamp: datetime
    checks: Dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "checks": self.checks,
            "issues": self.issues,
        }


class SystemHealthMonitor:
    """Monitor overall system health"""

    def __init__(self) -> None:
        self.health_checks: Dict[str, Dict[str, Any]] = {}
        self.last_check_time: Optional[datetime] = None
        self.check_interval = 30  # Seconds

    async def register_check(
        self,
        name: str,
        check_func: Callable[[], Any | Awaitable[Any]],
        critical: bool = False
    ) -> None:
        """Register a health check"""
        self.health_checks[name] = {
            "func": check_func,
            "critical": critical,
            "last_result": None,
            "last_check": None,
        }

    async def run_all_checks(self) -> HealthCheckResult:
        """Run all health checks"""
        checks = {}
        issues = []
        critical_failed = False

        for name, check_info in self.health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_info["func"]):
                    result = await check_info["func"]()
                else:
                    result = check_info["func"]()

                checks[name] = {
                    "status": "ok" if result else "failed",
                    "result": result,
                }

                check_info["last_result"] = result
                check_info["last_check"] = datetime.now(timezone.utc)

                if not result and check_info["critical"]:
                    critical_failed = True
                    issues.append(f"Critical check failed: {name}")

            except Exception as e:
                checks[name] = {
                    "status": "error",
                    "error": str(e),
                }
                issues.append(f"Check error: {name} - {e}")

                if check_info["critical"]:
                    critical_failed = True

        # Determine overall status
        if critical_failed:
            status = HealthStatus.UNHEALTHY
        elif issues:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        self.last_check_time = datetime.now(timezone.utc)

        return HealthCheckResult(
            status=status,
            timestamp=self.last_check_time,
            checks=checks,
            issues=issues
        )

    async def get_status(self) -> Dict[str, Any]:
        """Get current health status"""
        result = await self.run_all_checks()
        return result.to_dict()


class SLAMonitor:
    """Monitor Service Level Agreements"""

    def __init__(self) -> None:
        self.slas: Dict[str, Dict[str, float]] = {}
        self.violations: list[Dict[str, Any]] = []

    def register_sla(
        self,
        name: str,
        target_uptime: float = 0.99,
        max_response_time_ms: int = 1000,
        error_rate_threshold: float = 0.01
    ) -> None:
        """Register SLA"""
        self.slas[name] = {
            "target_uptime": target_uptime,
            "max_response_time_ms": max_response_time_ms,
            "error_rate_threshold": error_rate_threshold,
            "current_uptime": 0,
            "avg_response_time": 0,
            "error_rate": 0,
        }

    def record_request(
        self,
        sla_name: str,
        response_time_ms: float,
        success: bool
    ) -> bool:
        """Record request metrics"""
        if sla_name not in self.slas:
            return False

        sla = self.slas[sla_name]

        # Check violations
        violation = False

        if response_time_ms > sla["max_response_time_ms"]:
            violation = True
            self.violations.append({
                "sla": sla_name,
                "type": "response_time",
                "threshold": sla["max_response_time_ms"],
                "actual": response_time_ms,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        return not violation

    def get_sla_status(self) -> Dict[str, Any]:
        """Get SLA status"""
        status = {}

        for sla_name, sla in self.slas.items():
            status[sla_name] = {
                "target_uptime": sla["target_uptime"],
                "max_response_time_ms": sla["max_response_time_ms"],
                "violations": len([
                    v for v in self.violations
                    if v["sla"] == sla_name
                ])
            }

        return status


class DistributedTracer:
    """Support distributed tracing"""

    def __init__(self) -> None:
        self.traces: Dict[str, Dict[str, Any]] = {}
        self.trace_id_counter = 0

    def start_trace(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a trace"""
        self.trace_id_counter += 1
        trace_id = f"trace-{self.trace_id_counter}"

        self.traces[trace_id] = {
            "operation": operation,
            "start_time": datetime.now(timezone.utc),
            "spans": [],
            "metadata": metadata or {},
            "status": "running"
        }

        return trace_id

    def add_span(
        self,
        trace_id: str,
        span_name: str,
        duration_ms: float,
        status: str = "success"
    ) -> None:
        """Add span to trace"""
        if trace_id not in self.traces:
            return

        self.traces[trace_id]["spans"].append({
            "name": span_name,
            "duration_ms": duration_ms,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def end_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """End a trace"""
        if trace_id not in self.traces:
            return None

        trace = self.traces[trace_id]
        trace["end_time"] = datetime.now(timezone.utc)
        trace["status"] = "completed"

        total_duration = (
            trace["end_time"] - trace["start_time"]
        ).total_seconds() * 1000

        trace["total_duration_ms"] = total_duration

        return trace


# Global instances
health_monitor = SystemHealthMonitor()
sla_monitor = SLAMonitor()
distributed_tracer = DistributedTracer()
