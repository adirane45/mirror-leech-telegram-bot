"""
Health Monitor for Cluster Components

Monitors health of all cluster components and nodes, including:
- Node health checks
- Service health monitoring
- Database connectivity checks
- Auto-recovery mechanisms

Features:
- Configurable health checks
- Multi-level health status
- Auto-recovery actions
- Health history tracking
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class HealthStatus(Enum):
    """Health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Component type"""
    NODE = "node"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    STORAGE = "storage"
    API = "api"
    SERVICE = "service"


@dataclass
class HealthCheck:
    """Health check definition"""
    check_id: str
    component_type: ComponentType
    component_name: str
    check_fn: Callable
    interval_seconds: int = 30
    timeout_seconds: int = 5
    failure_threshold: int = 3
    enabled: bool = True


@dataclass
class HealthCheckResult:
    """Health check result"""
    check_id: str
    component_name: str
    status: HealthStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    response_time_ms: float = 0.0
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentHealth:
    """Component health status"""
    component_name: str
    component_type: ComponentType
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    total_checks: int = 0
    failed_checks: int = 0
    average_response_ms: float = 0.0
    recovery_attempts: int = 0


class HealthMonitor:
    """Monitors health of cluster components"""
    
    _instance: Optional['HealthMonitor'] = None
    
    def __init__(self):
        self.enabled = False
        
        # Health checks
        self.health_checks: Dict[str, HealthCheck] = {}
        self.component_health: Dict[str, ComponentHealth] = {}
        
        # Health history
        self.health_history: List[HealthCheckResult] = []
        self.max_history = 1000
        
        # Recovery callbacks
        self.recovery_callbacks: Dict[str, List[Callable]] = {}
        
        # Monitoring tasks
        self.check_tasks: Dict[str, asyncio.Task] = {}
        
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'HealthMonitor':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = HealthMonitor()
        return cls._instance
    
    async def enable(self) -> bool:
        """Enable health monitor"""
        try:
            async with self.lock:
                self.enabled = True
                
                # Start all enabled health checks
                for check_id, check in self.health_checks.items():
                    if check.enabled:
                        await self._start_check(check_id)
                
                return True
        except Exception as e:
            print(f"Error enabling health monitor: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable health monitor"""
        try:
            async with self.lock:
                self.enabled = False
                
                # Stop all check tasks
                for task in self.check_tasks.values():
                    task.cancel()
                
                # Wait for tasks to complete
                if self.check_tasks:
                    await asyncio.gather(
                        *self.check_tasks.values(),
                        return_exceptions=True
                    )
                
                self.check_tasks.clear()
                
                return True
        except Exception as e:
            print(f"Error disabling health monitor: {e}")
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
        """Register a health check"""
        try:
            async with self.lock:
                check = HealthCheck(
                    check_id=check_id,
                    component_type=component_type,
                    component_name=component_name,
                    check_fn=check_fn,
                    interval_seconds=interval_seconds,
                    timeout_seconds=timeout_seconds,
                    failure_threshold=failure_threshold
                )
                
                self.health_checks[check_id] = check
                
                # Initialize component health
                if component_name not in self.component_health:
                    self.component_health[component_name] = ComponentHealth(
                        component_name=component_name,
                        component_type=component_type
                    )
                
                # Start check if monitor is enabled
                if self.enabled:
                    await self._start_check(check_id)
                
                return True
        except Exception as e:
            print(f"Error registering check: {e}")
            return False
    
    async def unregister_health_check(self, check_id: str) -> bool:
        """Unregister a health check"""
        try:
            async with self.lock:
                if check_id in self.health_checks:
                    del self.health_checks[check_id]
                
                # Stop check task
                if check_id in self.check_tasks:
                    self.check_tasks[check_id].cancel()
                    try:
                        await self.check_tasks[check_id]
                    except asyncio.CancelledError:
                        pass
                    del self.check_tasks[check_id]
                
                return True
        except Exception as e:
            print(f"Error unregistering check: {e}")
            return False
    
    async def register_recovery_callback(
        self,
        component_name: str,
        callback: Callable
    ) -> None:
        """Register callback for component recovery"""
        if component_name not in self.recovery_callbacks:
            self.recovery_callbacks[component_name] = []
        self.recovery_callbacks[component_name].append(callback)
    
    async def _start_check(self, check_id: str) -> None:
        """Start health check task"""
        try:
            check = self.health_checks.get(check_id)
            if not check:
                return
            
            # Stop existing task if any
            if check_id in self.check_tasks:
                self.check_tasks[check_id].cancel()
            
            # Start new task
            task = asyncio.create_task(self._check_loop(check_id))
            self.check_tasks[check_id] = task
        
        except Exception as e:
            print(f"Error starting check: {e}")
    
    async def _check_loop(self, check_id: str) -> None:
        """Health check loop"""
        while self.enabled:
            try:
                check = self.health_checks.get(check_id)
                if not check or not check.enabled:
                    break
                
                # Perform health check
                result = await self._perform_check(check)
                
                # Update component health
                await self._update_component_health(check, result)
                
                # Store result
                self.health_history.append(result)
                if len(self.health_history) > self.max_history:
                    self.health_history = self.health_history[-self.max_history:]
                
                # Sleep until next check
                await asyncio.sleep(check.interval_seconds)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Check loop error: {e}")
                await asyncio.sleep(1)
    
    async def _perform_check(self, check: HealthCheck) -> HealthCheckResult:
        """Perform a health check"""
        start_time = time.time()
        
        try:
            # Execute check with timeout
            result = await asyncio.wait_for(
                check.check_fn(),
                timeout=check.timeout_seconds
            )
            
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Parse result
            if isinstance(result, dict):
                status = result.get('status', HealthStatus.HEALTHY)
                details = result.get('details', {})
                error = result.get('error')
            elif isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                details = {}
                error = None
            else:
                status = HealthStatus.HEALTHY
                details = {'result': result}
                error = None
            
            return HealthCheckResult(
                check_id=check.check_id,
                component_name=check.component_name,
                status=status,
                response_time_ms=response_time,
                details=details,
                error=error
            )
        
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_id=check.check_id,
                component_name=check.component_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=f"Timeout after {check.timeout_seconds}s"
            )
        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                check_id=check.check_id,
                component_name=check.component_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                error=str(e)
            )
    
    async def _update_component_health(
        self,
        check: HealthCheck,
        result: HealthCheckResult
    ) -> None:
        """Update component health based on check result"""
        try:
            async with self.lock:
                health = self.component_health.get(check.component_name)
                if not health:
                    return
                
                health.last_check = result.timestamp
                health.total_checks += 1
                
                # Update average response time
                if health.total_checks == 1:
                    health.average_response_ms = result.response_time_ms
                else:
                    health.average_response_ms = (
                        (health.average_response_ms * (health.total_checks - 1) +
                         result.response_time_ms) / health.total_checks
                    )
                
                # Update failure tracking
                if result.status == HealthStatus.UNHEALTHY:
                    health.consecutive_failures += 1
                    health.failed_checks += 1
                    
                    # Trigger recovery if threshold reached
                    if health.consecutive_failures >= check.failure_threshold:
                        await self._trigger_recovery(check.component_name, result)
                else:
                    health.consecutive_failures = 0
                
                # Update overall status
                if health.consecutive_failures >= check.failure_threshold:
                    health.status = HealthStatus.UNHEALTHY
                elif health.consecutive_failures > 0:
                    health.status = HealthStatus.DEGRADED
                else:
                    health.status = HealthStatus.HEALTHY
        
        except Exception as e:
            print(f"Error updating health: {e}")
    
    async def _trigger_recovery(
        self,
        component_name: str,
        result: HealthCheckResult
    ) -> None:
        """Trigger recovery for unhealthy component"""
        try:
            health = self.component_health.get(component_name)
            if not health:
                return
            
            health.recovery_attempts += 1
            
            print(f"Triggering recovery for {component_name}")
            
            # Execute recovery callbacks
            callbacks = self.recovery_callbacks.get(component_name, [])
            for callback in callbacks:
                try:
                    await callback(result)
                except Exception as e:
                    print(f"Recovery callback error: {e}")
        
        except Exception as e:
            print(f"Error triggering recovery: {e}")
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """Get overall cluster health"""
        try:
            async with self.lock:
                healthy_count = sum(
                    1 for h in self.component_health.values()
                    if h.status == HealthStatus.HEALTHY
                )
                degraded_count = sum(
                    1 for h in self.component_health.values()
                    if h.status == HealthStatus.DEGRADED
                )
                unhealthy_count = sum(
                    1 for h in self.component_health.values()
                    if h.status == HealthStatus.UNHEALTHY
                )
                
                total_components = len(self.component_health)
                
                # Determine overall status
                if unhealthy_count > 0:
                    overall_status = HealthStatus.UNHEALTHY
                elif degraded_count > 0:
                    overall_status = HealthStatus.DEGRADED
                elif healthy_count > 0:
                    overall_status = HealthStatus.HEALTHY
                else:
                    overall_status = HealthStatus.UNKNOWN
                
                return {
                    'status': overall_status.value,
                    'total_components': total_components,
                    'healthy': healthy_count,
                    'degraded': degraded_count,
                    'unhealthy': unhealthy_count,
                    'active_checks': len(self.check_tasks),
                    'components': {
                        name: {
                            'type': health.component_type.value,
                            'status': health.status.value,
                            'last_check': (
                                health.last_check.isoformat()
                                if health.last_check else None
                            ),
                            'consecutive_failures': health.consecutive_failures,
                            'total_checks': health.total_checks,
                            'failed_checks': health.failed_checks,
                            'success_rate': (
                                (health.total_checks - health.failed_checks) /
                                health.total_checks * 100
                                if health.total_checks > 0 else 0
                            ),
                            'average_response_ms': health.average_response_ms,
                            'recovery_attempts': health.recovery_attempts
                        }
                        for name, health in self.component_health.items()
                    }
                }
        except Exception as e:
            print(f"Error getting overall health: {e}")
            return {'status': 'unknown', 'error': str(e)}
    
    async def get_component_health(self, component_name: str) -> Optional[Dict[str, Any]]:
        """Get health of specific component"""
        try:
            async with self.lock:
                health = self.component_health.get(component_name)
                if not health:
                    return None
                
                return {
                    'name': health.component_name,
                    'type': health.component_type.value,
                    'status': health.status.value,
                    'last_check': (
                        health.last_check.isoformat()
                        if health.last_check else None
                    ),
                    'consecutive_failures': health.consecutive_failures,
                    'total_checks': health.total_checks,
                    'failed_checks': health.failed_checks,
                    'average_response_ms': health.average_response_ms,
                    'recovery_attempts': health.recovery_attempts
                }
        except Exception as e:
            print(f"Error getting component health: {e}")
            return None
    
    async def get_health_history(
        self,
        component_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get health check history"""
        try:
            async with self.lock:
                history = self.health_history
                
                # Filter by component if specified
                if component_name:
                    history = [
                        r for r in history
                        if r.component_name == component_name
                    ]
                
                # Get most recent
                recent = history[-limit:]
                
                return [
                    {
                        'check_id': r.check_id,
                        'component': r.component_name,
                        'status': r.status.value,
                        'timestamp': r.timestamp.isoformat(),
                        'response_time_ms': r.response_time_ms,
                        'error': r.error,
                        'details': r.details
                    }
                    for r in recent
                ]
        except Exception as e:
            print(f"Error getting history: {e}")
            return []
    
    async def reset(self) -> bool:
        """Reset health monitor"""
        try:
            await self.disable()
            self.health_checks.clear()
            self.component_health.clear()
            self.health_history.clear()
            self.recovery_callbacks.clear()
            return True
        except Exception as e:
            print(f"Error resetting: {e}")
            return False
