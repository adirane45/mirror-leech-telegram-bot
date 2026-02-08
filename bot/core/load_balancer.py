"""
Phase 4: Load Balancer
Distribute requests across multiple bot instances
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime
import logging

from .load_balancer_models import LoadBalancingStrategy, BotInstance

logger = logging.getLogger(__name__)


class LoadBalancer:
    """
    Singleton load balancer for distributed request routing
    """

    _instance: Optional['LoadBalancer'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.enabled = False
        self.instances: Dict[str, BotInstance] = {}
        self.strategy = LoadBalancingStrategy.ROUND_ROBIN
        self.request_handler: Optional[Callable] = None
        
        # Round-robin state
        self.current_index = 0
        
        # Statistics
        self.total_requests = 0
        self.total_successful = 0
        self.total_failed = 0
        
        # Health checking
        self.health_check_interval = 30  # seconds
        self.health_check_timeout = 5  # seconds
        self.health_check_task: Optional[asyncio.Task] = None
        
    @classmethod
    def get_instance(cls) -> 'LoadBalancer':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = LoadBalancer()
        return cls._instance

    async def enable(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN) -> bool:
        """
        Enable the Load Balancer
        
        Args:
            strategy: Load balancing strategy to use
            
        Returns:
            Success status
        """
        async with self._lock:
            self.enabled = True
            self.strategy = strategy
            
            # Start health check task
            if self.health_check_task is None:
                self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info(f"Load Balancer enabled (strategy: {strategy.value})")
            return True

    async def disable(self) -> bool:
        """Disable the Load Balancer"""
        async with self._lock:
            self.enabled = False
            
            # Cancel health check task
            if self.health_check_task:
                self.health_check_task.cancel()
                self.health_check_task = None
            
            logger.info("Load Balancer disabled")
            return True

    async def add_instance(
        self,
        instance_id: str,
        host: str,
        port: int,
        weight: float = 1.0
    ) -> bool:
        """
        Add bot instance to load balancer
        
        Args:
            instance_id: Unique instance identifier
            host: Instance hostname/IP
            port: Instance port
            weight: Load weighting (higher = faster)
            
        Returns:
            Success status
        """
        try:
            instance = BotInstance(
                instance_id=instance_id,
                host=host,
                port=port,
                weight=weight
            )
            self.instances[instance_id] = instance
            logger.info(f"Added instance {instance_id} ({host}:{port}, weight={weight})")
            return True
        except Exception as e:
            logger.error(f"Error adding instance: {e}")
            return False

    async def remove_instance(self, instance_id: str) -> bool:
        """
        Remove bot instance from load balancer
        
        Args:
            instance_id: Instance identifier
            
        Returns:
            Success status
        """
        try:
            if instance_id in self.instances:
                del self.instances[instance_id]
                logger.info(f"Removed instance {instance_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing instance: {e}")
            return False

    def _select_next_instance_roundrobin(self) -> Optional[BotInstance]:
        """Select next instance using round-robin"""
        healthy = [i for i in self.instances.values() if i.is_healthy]
        if not healthy:
            return None
        
        instance = healthy[self.current_index % len(healthy)]
        self.current_index += 1
        return instance

    def _select_next_instance_least_connections(self) -> Optional[BotInstance]:
        """Select instance with least active connections"""
        healthy = [i for i in self.instances.values() if i.is_healthy]
        if not healthy:
            return None
        
        # Prefer instance with lowest connection ratio considering weight
        return min(healthy, key=lambda i: i.connection_ratio)

    def _select_next_instance_weighted(self) -> Optional[BotInstance]:
        """Select instance using weighted distribution"""
        healthy = [i for i in self.instances.values() if i.is_healthy]
        if not healthy:
            return None
        
        # Higher weight = higher chance of selection
        total_weight = sum(i.weight for i in healthy)
        if total_weight == 0:
            return healthy[0]
        
        # Weighted random select
        import random
        pick = random.uniform(0, total_weight)
        current = 0
        
        for instance in healthy:
            current += instance.weight
            if pick <= current:
                return instance
        
        return healthy[-1]

    def _select_next_instance(self) -> Optional[BotInstance]:
        """Select next instance based on strategy"""
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_next_instance_roundrobin()
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._select_next_instance_least_connections()
        elif self.strategy == LoadBalancingStrategy.WEIGHTED:
            return self._select_next_instance_weighted()
        else:
            return self._select_next_instance_roundrobin()

    async def route_request(
        self,
        request_data: Any,
        max_retries: int = 3
    ) -> Tuple[bool, Optional[Any], Optional[str]]:
        """
        Route request to appropriate instance
        
        Args:
            request_data: Request data to process
            max_retries: Maximum retry attempts
            
        Returns:
            Tuple of (success, result, instance_id)
        """
        if not self.enabled:
            logger.warning("Load Balancer not enabled")
            return False, None, None

        self.total_requests += 1
        retries = 0
        
        try:
            while retries < max_retries:
                instance = self._select_next_instance()
                
                if instance is None:
                    logger.error("No healthy instances available")
                    self.total_failed += 1
                    return False, None, None
                
                try:
                    # Mark as active
                    instance.active_connections += 1
                    start_time = time.time()
                    
                    # Call request handler
                    if self.request_handler:
                        result = await self.request_handler(instance, request_data)
                    else:
                        result = {"status": "ok"}
                    
                    # Update statistics
                    elapsed = (time.time() - start_time) * 1000
                    instance.response_time_ms = elapsed
                    instance.total_requests += 1
                    instance.last_request_time = datetime.now()
                    instance.active_connections -= 1
                    
                    self.total_successful += 1
                    logger.debug(f"Request routed to {instance.instance_id} ({elapsed:.0f}ms)")
                    
                    return True, result, instance.instance_id
                    
                except Exception as e:
                    instance.active_connections -= 1
                    instance.failed_requests += 1
                    logger.warning(f"Request failed on {instance.instance_id}: {e}")
                    retries += 1
                    
                    # Mark unhealthy after threshold
                    if instance.failed_requests > 5:
                        instance.is_healthy = False
                        logger.error(f"Instance {instance.instance_id} marked unhealthy")
            
            self.total_failed += 1
            return False, None, None
            
        except Exception as e:
            logger.error(f"Error routing request: {e}")
            self.total_failed += 1
            return False, None, None

    async def _health_check_loop(self) -> None:
        """Background task for periodic health checks"""
        while self.enabled:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    async def _perform_health_checks(self) -> None:
        """Perform health checks on all instances"""
        try:
            for instance_id, instance in self.instances.items():
                try:
                    # Simple health check: verify heartbeat
                    elapsed_since_heartbeat = (datetime.now() - instance.last_heartbeat).total_seconds()
                    
                    if elapsed_since_heartbeat > 60:  # 1 minute without heartbeat
                        instance.is_healthy = False
                        logger.warning(f"Instance {instance_id} health check failed (no heartbeat)")
                    else:
                        instance.is_healthy = True
                        instance.last_heartbeat = datetime.now()
                        
                except Exception as e:
                    logger.error(f"Health check error for {instance_id}: {e}")
                    instance.is_healthy = False
                    
        except Exception as e:
            logger.error(f"Error performing health checks: {e}")

    async def get_instance_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific instance"""
        if instance_id not in self.instances:
            return None
        
        instance = self.instances[instance_id]
        return {
            'instance_id': instance_id,
            'host': instance.host,
            'port': instance.port,
            'is_healthy': instance.is_healthy,
            'weight': instance.weight,
            'active_connections': instance.active_connections,
            'total_requests': instance.total_requests,
            'failed_requests': instance.failed_requests,
            'response_time_ms': instance.response_time_ms,
            'last_request_time': instance.last_request_time.isoformat() if instance.last_request_time else None,
        }

    async def get_all_instances_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all instances"""
        result = {}
        for instance_id in self.instances:
            status = await self.get_instance_status(instance_id)
            if status:
                result[instance_id] = status
        return result

    async def get_statistics(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        healthy_count = sum(1 for i in self.instances.values() if i.is_healthy)
        
        avg_response_time = (
            sum(i.response_time_ms for i in self.instances.values()) / len(self.instances)
            if self.instances else 0.0
        )
        
        return {
            'enabled': self.enabled,
            'strategy': self.strategy.value,
            'total_instances': len(self.instances),
            'healthy_instances': healthy_count,
            'total_requests': self.total_requests,
            'successful_requests': self.total_successful,
            'failed_requests': self.total_failed,
            'success_rate_percent': (
                self.total_successful / self.total_requests * 100
                if self.total_requests > 0 else 0.0
            ),
            'average_response_time_ms': avg_response_time,
        }
