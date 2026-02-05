"""
Load Balancer for Distributed Request Handling

Distributes requests across multiple servers or instances using
various strategies including round-robin, least connections, and weighted.

Features:
- Multiple load balancing strategies
- Health checking
- Automatic failover
- Session stickiness
- Performance statistics
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum
import random


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_LOADED = "least_loaded"
    WEIGHTED_ROUND_ROBIN = "weighted"
    RANDOM = "random"


class InstanceState(Enum):
    """Instance health state"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    RECOVERING = "recovering"


@dataclass
class InstanceHealth:
    """Track instance health metrics"""
    instance_id: str
    state: InstanceState = InstanceState.HEALTHY
    active_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_check_at: datetime = field(default_factory=datetime.utcnow)
    consecutive_failures: int = 0
    recovery_start: Optional[datetime] = None


class ServerInstance:
    """Represents a server instance"""
    
    def __init__(
        self,
        instance_id: str,
        address: str,
        port: int,
        weight: float = 1.0
    ):
        self.instance_id = instance_id
        self.address = address
        self.port = port
        self.weight = weight
        self.health = InstanceHealth(instance_id)
        
        self.total_connections = 0
        self.response_times: List[float] = []
        self.max_response_times = 100  # Keep last 100
        self.lock = asyncio.Lock()
    
    async def record_request(self, response_time: float, success: bool) -> None:
        """Record request statistics"""
        async with self.lock:
            self.health.total_requests += 1
            self.response_times.append(response_time)
            
            if len(self.response_times) > self.max_response_times:
                self.response_times = self.response_times[-self.max_response_times:]
            
            if self.response_times:
                self.health.avg_response_time = sum(self.response_times) / len(self.response_times)
            
            if not success:
                self.health.failed_requests += 1
                self.health.consecutive_failures += 1
            else:
                self.health.consecutive_failures = 0
    
    def get_url(self) -> str:
        """Get instance URL"""
        return f"http://{self.address}:{self.port}"


class LoadBalancer:
    """Load balancer for distributing requests"""
    
    _instance: Optional['LoadBalancer'] = None
    
    def __init__(self):
        self.enabled = False
        self.instances: Dict[str, ServerInstance] = {}
        self.strategy = LoadBalancingStrategy.ROUND_ROBIN
        
        self.round_robin_index = 0
        self.request_handler: Optional[Callable] = None
        
        self.health_check_interval = 10  # seconds
        self.health_check_timeout = 5  # seconds
        self.failure_threshold = 3
        self.recovery_threshold = 5
        
        self.total_requests = 0
        self.failed_requests = 0
        self.session_sessions: Dict[str, str] = {}  # session_id -> instance_id
        
        self.health_check_task: Optional[asyncio.Task] = None
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'LoadBalancer':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = LoadBalancer()
        return cls._instance
    
    async def enable(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN) -> bool:
        """Enable load balancer"""
        try:
            async with self.lock:
                self.enabled = True
                self.strategy = strategy
                
                # Start health check task
                if self.health_check_task is None or self.health_check_task.done():
                    self.health_check_task = asyncio.create_task(self._health_check_loop())
                
                return True
        except Exception as e:
            print(f"Error enabling load balancer: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable load balancer"""
        try:
            async with self.lock:
                self.enabled = False
                
                if self.health_check_task:
                    self.health_check_task.cancel()
                    try:
                        await self.health_check_task
                    except asyncio.CancelledError:
                        pass
                    self.health_check_task = None
                
                return True
        except Exception as e:
            print(f"Error disabling load balancer: {e}")
            return False
    
    async def add_instance(
        self,
        instance_id: str,
        address: str,
        port: int,
        weight: float = 1.0
    ) -> bool:
        """Add instance to load balancer"""
        if not self.enabled:
            return False
        
        try:
            async with self.lock:
                if instance_id not in self.instances:
                    instance = ServerInstance(instance_id, address, port, weight)
                    self.instances[instance_id] = instance
                    return True
                return False
        except Exception as e:
            print(f"Error adding instance: {e}")
            return False
    
    async def remove_instance(self, instance_id: str) -> bool:
        """Remove instance from load balancer"""
        try:
            async with self.lock:
                if instance_id in self.instances:
                    del self.instances[instance_id]
                    
                    # Remove from session map
                    self.session_sessions = {
                        sid: iid for sid, iid in self.session_sessions.items()
                        if iid != instance_id
                    }
                    return True
                return False
        except Exception as e:
            print(f"Error removing instance: {e}")
            return False
    
    async def get_instance(
        self,
        session_id: Optional[str] = None
    ) -> Optional[ServerInstance]:
        """Get next instance based on strategy"""
        if not self.enabled or not self.instances:
            return None
        
        try:
            async with self.lock:
                # Check session stickiness
                if session_id and session_id in self.session_sessions:
                    instance_id = self.session_sessions[session_id]
                    if instance_id in self.instances:
                        return self.instances[instance_id]
                
                # Get healthy instances
                healthy = [
                    inst for inst in self.instances.values()
                    if inst.health.state in [InstanceState.HEALTHY, InstanceState.DEGRADED]
                ]
                
                if not healthy:
                    # Use all if none healthy (last resort)
                    healthy = list(self.instances.values())
                
                if not healthy:
                    return None
                
                # Select based on strategy
                selected = None
                
                if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                    selected = healthy[self.round_robin_index % len(healthy)]
                    self.round_robin_index += 1
                
                elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                    selected = min(healthy, key=lambda x: x.health.active_connections)
                
                elif self.strategy == LoadBalancingStrategy.LEAST_LOADED:
                    selected = min(healthy, key=lambda x: x.health.avg_response_time)
                
                elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                    # Weighted selection
                    total_weight = sum(x.weight for x in healthy)
                    choice = random.uniform(0, total_weight)
                    current = 0
                    for inst in healthy:
                        current += inst.weight
                        if choice <= current:
                            selected = inst
                            break
                
                elif self.strategy == LoadBalancingStrategy.RANDOM:
                    selected = random.choice(healthy)
                
                if selected and session_id:
                    self.session_sessions[session_id] = selected.instance_id
                
                return selected
        except Exception as e:
            print(f"Error getting instance: {e}")
            return None
    
    async def route_request(
        self,
        data: Any,
        session_id: Optional[str] = None
    ) -> Tuple[bool, Any, Optional[str]]:
        """Route request to selected instance"""
        if not self.enabled or not self.request_handler:
            return False, None, None
        
        try:
            instance = await self.get_instance(session_id)
            
            if not instance:
                return False, None, None
            
            # Record request start
            instance.health.active_connections += 1
            self.total_requests += 1
            
            start_time = time.time()
            
            try:
                # Call request handler
                result = await self.request_handler(instance, data)
                response_time = time.time() - start_time
                
                # Record success
                await instance.record_request(response_time, True)
                instance.health.active_connections -= 1
                
                return True, result, instance.instance_id
            
            except Exception as e:
                response_time = time.time() - start_time
                
                # Record failure
                await instance.record_request(response_time, False)
                instance.health.active_connections -= 1
                self.failed_requests += 1
                
                # Update instance health
                if instance.health.consecutive_failures >= self.failure_threshold:
                    instance.health.state = InstanceState.UNHEALTHY
                
                raise e
        
        except Exception as e:
            print(f"Request routing error: {e}")
            return False, None, None
    
    async def _health_check_loop(self) -> None:
        """Periodically check instance health"""
        while self.enabled:
            try:
                async with self.lock:
                    for instance in self.instances.values():
                        await self._check_instance_health(instance)
                
                await asyncio.sleep(self.health_check_interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Health check error: {e}")
                await asyncio.sleep(5)
    
    async def _check_instance_health(self, instance: ServerInstance) -> None:
        """Check single instance health"""
        try:
            # Simple health check - can be overridden
            if instance.health.consecutive_failures >= self.failure_threshold:
                if instance.health.state != InstanceState.UNHEALTHY:
                    instance.health.state = InstanceState.UNHEALTHY
                    instance.health.recovery_start = datetime.utcnow()
            
            elif instance.health.state == InstanceState.UNHEALTHY:
                if instance.health.recovery_start:
                    recovery_time = (datetime.utcnow() - instance.health.recovery_start).total_seconds()
                    if recovery_time >= self.recovery_threshold:
                        instance.health.state = InstanceState.HEALTHY
                        instance.health.consecutive_failures = 0
                        instance.health.recovery_start = None
            
            instance.health.last_check_at = datetime.utcnow()
        
        except Exception as e:
            print(f"Health check failed for {instance.instance_id}: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        try:
            async with self.lock:
                instance_stats = {}
                
                for instance in self.instances.values():
                    instance_stats[instance.instance_id] = {
                        'state': instance.health.state.value,
                        'active_connections': instance.health.active_connections,
                        'total_requests': instance.health.total_requests,
                        'failed_requests': instance.health.failed_requests,
                        'avg_response_time': round(instance.health.avg_response_time, 3),
                        'error_rate': round(
                            (instance.health.failed_requests / instance.health.total_requests * 100)
                            if instance.health.total_requests > 0 else 0,
                            2
                        )
                    }
                
                return {
                    'enabled': self.enabled,
                    'strategy': self.strategy.value,
                    'total_instances': len(self.instances),
                    'total_requests': self.total_requests,
                    'failed_requests': self.failed_requests,
                    'failure_rate': round(
                        (self.failed_requests / self.total_requests * 100)
                        if self.total_requests > 0 else 0,
                        2
                    ),
                    'instances': instance_stats
                }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'error': str(e)}
    
    async def reset(self) -> bool:
        """Reset load balancer"""
        try:
            await self.disable()
            self.instances.clear()
            self.session_sessions.clear()
            self.total_requests = 0
            self.failed_requests = 0
            return True
        except Exception as e:
            print(f"Error resetting: {e}")
            return False
