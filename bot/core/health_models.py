"""
Health Monitor Models - Data structures for component health monitoring

Includes:
- Health status and component type enumerations
- Health check results and component health dataclasses
- Health check configuration
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Callable, Dict, Optional


# ============================================================================
# ENUMS & TYPES
# ============================================================================

class HealthStatus(str, Enum):
    """Health status of a component"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    """Type of component"""
    NODE = "node"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"
    API = "api"
    SERVICE = "service"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class HealthCheckResult:
    """Result of a health check"""
    status: HealthStatus
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0


@dataclass
class ComponentHealth:
    """Health status of a single component"""
    component_id: str
    component_type: ComponentType
    component_name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: Optional[datetime] = None
    failure_count: int = 0
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0


@dataclass
class HealthCheck:
    """Configuration for a health check"""
    check_id: str
    component_type: ComponentType
    component_name: str
    check_fn: Callable
    interval_seconds: int = 30
    timeout_seconds: int = 5
    failure_threshold: int = 3
    enabled: bool = True
    last_check_time: Optional[datetime] = None
    consecutive_failures: int = 0
