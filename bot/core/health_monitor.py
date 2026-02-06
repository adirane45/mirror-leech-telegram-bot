"""
Phase 5: Health Monitor

Comprehensive health monitoring system for bot components with:
- Component health checks
- Automatic recovery callbacks
- Health status tracking
- Dashboard integration

All components depend on this for health status visibility.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from logging import getLogger

logger = getLogger(__name__)


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
    timestamp: datetime = field(default_factory=datetime.now)
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


# ============================================================================
# HEALTH MONITOR
# ============================================================================

class HealthMonitor:
    """
    Singleton health monitoring system for bot components.
    
    Monitors health of all components with automatic recovery callbacks.
    """
    
    _instance: Optional['HealthMonitor'] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize health monitor"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._enabled = False
        self._health_checks: Dict[str, HealthCheck] = {}
        self._component_health: Dict[str, ComponentHealth] = {}
        self._recovery_callbacks: Dict[str, List[Callable]] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._last_alert_time: Dict[str, datetime] = {}
        self._check_in_progress: Set[str] = set()

    @classmethod
    def get_instance(cls) -> 'HealthMonitor':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def enable(self) -> bool:
        """Enable health monitoring"""
        try:
            if self._enabled:
                logger.warning("Health Monitor already enabled")
                return True
            
            self._enabled = True
            logger.info("Health Monitor enabled")
            
            # Start background health check loop
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            return True
        except Exception as e:
            logger.error(f"Failed to enable Health Monitor: {e}")
            self._enabled = False
            return False

    async def disable(self) -> bool:
        """Disable health monitoring"""
        try:
            if not self._enabled:
                return True
            
            self._enabled = False
            
            # Cancel health check task
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Health Monitor disabled")
            return True
        except Exception as e:
            logger.error(f"Failed to disable Health Monitor: {e}")
            return False

    async def register_health_check(
        self,
        check_id: str,
        component_type: ComponentType,
        component_name: str,
        check_fn: Callable,
        interval_seconds: int = 30,
        timeout_seconds: int = 5,
        failure_threshold: int = 3
    ) -> bool:
        """
        Register a health check for a component.
        
        Args:
            check_id: Unique check identifier
            component_type: Type of component
            component_name: Human-readable component name
            check_fn: Async function that performs check, returns HealthCheckResult
            interval_seconds: Check interval in seconds
            timeout_seconds: Check timeout in seconds
            failure_threshold: Consecutive failures before UNHEALTHY
            
        Returns:
            True if registered successfully
        """
        try:
            if not callable(check_fn):
                logger.error(f"check_fn for {check_id} is not callable")
                return False
            
            health_check = HealthCheck(
                check_id=check_id,
                component_type=component_type,
                component_name=component_name,
                check_fn=check_fn,
                interval_seconds=interval_seconds,
                timeout_seconds=timeout_seconds,
                failure_threshold=failure_threshold
            )
            
            self._health_checks[check_id] = health_check
            
            # Initialize component health
            self._component_health[check_id] = ComponentHealth(
                component_id=check_id,
                component_type=component_type,
                component_name=component_name,
                status=HealthStatus.UNKNOWN
            )
            
            logger.info(f"Registered health check: {check_id} ({component_name})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register health check {check_id}: {e}")
            return False

    async def register_recovery_callback(
        self,
        component_id: str,
        callback: Callable
    ) -> bool:
        """
        Register a recovery callback for a component.
        
        Callback is called when component becomes UNHEALTHY.
        
        Args:
            component_id: Component identifier
            callback: Async callback function
            
        Returns:
            True if registered successfully
        """
        try:
            if component_id not in self._health_checks:
                logger.warning(f"Component {component_id} not registered")
                return False
            
            if component_id not in self._recovery_callbacks:
                self._recovery_callbacks[component_id] = []
            
            self._recovery_callbacks[component_id].append(callback)
            logger.info(f"Registered recovery callback for {component_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register recovery callback: {e}")
            return False

    async def get_overall_health(self) -> Dict[str, Any]:
        """
        Get overall health status of all components.
        
        Returns:
            {
                'status': 'healthy|degraded|unhealthy',
                'healthy': int (count),
                'total_components': int,
                'components': {
                    'component_id': {
                        'status': '...',
                        'component_type': '...',
                        'component_name': '...',
                        'last_check': '...',
                        'consecutive_failures': int,
                        'latency_ms': float
                    }
                }
            }
        """
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        
        components = {}
        
        for check_id, component in self._component_health.items():
            if component.status == HealthStatus.HEALTHY:
                healthy_count += 1
            elif component.status == HealthStatus.DEGRADED:
                degraded_count += 1
            elif component.status == HealthStatus.UNHEALTHY:
                unhealthy_count += 1
            
            components[check_id] = {
                'status': component.status.value,
                'component_type': component.component_type.value,
                'component_name': component.component_name,
                'last_check': component.last_check.isoformat() if component.last_check else None,
                'consecutive_failures': component.consecutive_failures,
                'latency_ms': component.latency_ms,
                'last_error': component.last_error
            }
        
        # Determine overall status
        total = len(self._component_health)
        if total == 0:
            overall_status = HealthStatus.UNKNOWN
        elif unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            'status': overall_status.value,
            'healthy': healthy_count,
            'degraded': degraded_count,
            'unhealthy': unhealthy_count,
            'total_components': total,
            'timestamp': datetime.now().isoformat(),
            'components': components
        }

    async def get_component_health(self, component_id: str) -> Optional[Dict[str, Any]]:
        """
        Get health status of a specific component.
        
        Args:
            component_id: Component identifier
            
        Returns:
            Component health info or None if not found
        """
        if component_id not in self._component_health:
            return None
        
        component = self._component_health[component_id]
        return {
            'status': component.status.value,
            'component_type': component.component_type.value,
            'component_name': component.component_name,
            'last_check': component.last_check.isoformat() if component.last_check else None,
            'consecutive_failures': component.consecutive_failures,
            'latency_ms': component.latency_ms,
            'failure_count': component.failure_count,
            'last_error': component.last_error,
            'details': component.details
        }

    async def _health_check_loop(self):
        """Background health check loop"""
        logger.info("Starting health check loop")
        
        try:
            while self._enabled:
                try:
                    # Run all health checks
                    tasks = [
                        self._run_health_check(check_id, health_check)
                        for check_id, health_check in self._health_checks.items()
                        if health_check.enabled
                    ]
                    
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Sleep before next round
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in health check loop: {e}")
                    await asyncio.sleep(1)
        
        except asyncio.CancelledError:
            logger.info("Health check loop cancelled")
        except Exception as e:
            logger.error(f"Health check loop error: {e}")

    async def _run_health_check(self, check_id: str, health_check: HealthCheck):
        """Run a single health check"""
        # Skip if check already in progress
        if check_id in self._check_in_progress:
            return
        
        # Check if it's time to run this check
        now = datetime.now()
        if health_check.last_check_time:
            elapsed = (now - health_check.last_check_time).total_seconds()
            if elapsed < health_check.interval_seconds:
                return
        
        self._check_in_progress.add(check_id)
        
        try:
            component = self._component_health[check_id]
            start_time = time.time()
            
            # Run the check with timeout
            try:
                result = await asyncio.wait_for(
                    health_check.check_fn(),
                    timeout=health_check.timeout_seconds
                )
            except asyncio.TimeoutError:
                result = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    error=f"Health check timeout (>{health_check.timeout_seconds}s)"
                )
            except Exception as e:
                result = HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    error=str(e)
                )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Update component health
            component.last_check = now
            component.status = result.status
            component.latency_ms = latency_ms
            component.details = result.details
            
            # Track failures
            if result.status == HealthStatus.HEALTHY:
                component.consecutive_failures = 0
                component.last_error = None
            else:
                component.consecutive_failures += 1
                component.last_error = result.error
                component.failure_count += 1
                
                # Trigger recovery if threshold exceeded
                if component.consecutive_failures >= health_check.failure_threshold:
                    await self._trigger_recovery(check_id, component, result)
            
            # Update check time
            health_check.last_check_time = now
            health_check.consecutive_failures = component.consecutive_failures
            
        except Exception as e:
            logger.error(f"Error running health check {check_id}: {e}")
        finally:
            self._check_in_progress.discard(check_id)

    async def _trigger_recovery(
        self,
        component_id: str,
        component: ComponentHealth,
        result: HealthCheckResult
    ):
        """Trigger recovery callbacks for unhealthy component"""
        # Limit alert frequency (once per minute)
        now = datetime.now()
        last_alert = self._last_alert_time.get(component_id)
        if last_alert and (now - last_alert).total_seconds() < 60:
            return
        
        self._last_alert_time[component_id] = now
        
        logger.warning(
            f"Component {component_id} ({component.component_name}) "
            f"is UNHEALTHY: {result.error}"
        )
        
        # Call recovery callbacks
        if component_id in self._recovery_callbacks:
            for callback in self._recovery_callbacks[component_id]:
                try:
                    logger.info(f"Calling recovery callback for {component_id}")
                    if asyncio.iscoroutinefunction(callback):
                        await callback(result)
                    else:
                        callback(result)
                except Exception as e:
                    logger.error(f"Error in recovery callback: {e}")

    def is_enabled(self) -> bool:
        """Check if health monitor is enabled"""
        return self._enabled

    def get_check_count(self) -> int:
        """Get number of registered health checks"""
        return len(self._health_checks)

    async def get_status_summary(self) -> str:
        """Get human-readable status summary"""
        health = await self.get_overall_health()
        return (
            f"Health Status: {health['status'].upper()} | "
            f"Healthy: {health['healthy']}/{health['total_components']} | "
            f"Enabled: {self._enabled}"
        )
