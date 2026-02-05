"""
Failover Manager for Automatic Instance Failover

Handles automatic failover when primary instance fails, including:
- Primary/Secondary role management
- Automatic failover triggers
- State transfer during failover
- Recovery coordination

Features:
- Automatic failover detection
- Configurable failover policies
- State preservation
- Recovery procedures
- Failback support
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class FailoverRole(Enum):
    """Node role in failover configuration"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    STANDBY = "standby"


class FailoverState(Enum):
    """Current failover state"""
    NORMAL = "normal"
    DETECTING = "detecting"
    FAILING_OVER = "failing_over"
    FAILED_OVER = "failed_over"
    RECOVERING = "recovering"
    FAILED = "failed"


@dataclass
class FailoverEvent:
    """Failover event record"""
    event_id: str
    event_type: str  # failover, failback, recovery
    from_node: str
    to_node: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""
    duration_seconds: float = 0.0
    success: bool = True


@dataclass
class FailoverPolicy:
    """Failover policy configuration"""
    auto_failover_enabled: bool = True
    failover_timeout: int = 30  # seconds
    health_check_interval: int = 5  # seconds
    failure_threshold: int = 3  # consecutive failures
    recovery_wait_time: int = 60  # seconds before attempting failback
    max_failover_attempts: int = 3


class FailoverManager:
    """Manages automatic failover between instances"""
    
    _instance: Optional['FailoverManager'] = None
    
    def __init__(self):
        self.enabled = False
        self.current_role = FailoverRole.STANDBY
        self.failover_state = FailoverState.NORMAL
        
        self.policy =FailoverPolicy()
        self.primary_node: Optional[str] = None
        self.secondary_nodes: List[str] = []
        
        self.failure_count = 0
        self.last_failover: Optional[datetime] = None
        self.failover_history: List[FailoverEvent] = []
        self.max_history = 100
        
        self.health_check_task: Optional[asyncio.Task] = None
        self.failover_callbacks: List[Callable] = []
        
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'FailoverManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = FailoverManager()
        return cls._instance
    
    async def enable(
        self,
        role: FailoverRole = FailoverRole.STANDBY,
        policy: Optional[FailoverPolicy] = None
    ) -> bool:
        """Enable failover manager"""
        try:
            async with self.lock:
                self.enabled = True
                self.current_role = role
                
                if policy:
                    self.policy = policy
                
                # Start health check task
                if self.health_check_task is None or self.health_check_task.done():
                    self.health_check_task = asyncio.create_task(self._health_check_loop())
                
                return True
        except Exception as e:
            print(f"Error enabling failover manager: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable failover manager"""
        try:
            async with self.lock:
                self.enabled = False
                
                if self.health_check_task:
                    self.health_check_task.cancel()
                    try:
                        await self.health_check_task
                    except asyncio.CancelledError:
                        pass
                
                return True
        except Exception as e:
            print(f"Error disabling failover manager: {e}")
            return False
    
    async def set_primary(self, node_id: str) -> bool:
        """Set the primary node"""
        try:
            async with self.lock:
                self.primary_node = node_id
                return True
        except Exception as e:
            print(f"Error setting primary: {e}")
            return False
    
    async def add_secondary(self, node_id: str) -> bool:
        """Add a secondary node"""
        try:
            async with self.lock:
                if node_id not in self.secondary_nodes:
                    self.secondary_nodes.append(node_id)
                return True
        except Exception as e:
            print(f"Error adding secondary: {e}")
            return False
    
    async def register_failover_callback(self, callback: Callable) -> None:
        """Register callback to be called during failover"""
        self.failover_callbacks.append(callback)
    
    async def _health_check_loop(self) -> None:
        """Periodically check primary health"""
        while self.enabled:
            try:
                if self.policy.auto_failover_enabled:
                    await self._check_primary_health()
                
                await asyncio.sleep(self.policy.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Health check error: {e}")
                await asyncio.sleep(1)
    
    async def _check_primary_health(self) -> None:
        """Check if primary is healthy"""
        try:
            if not self.primary_node:
                return
            
            # In production, make actual health check call
            # For now, simulate health check
            is_healthy = await self._perform_health_check(self.primary_node)
            
            if not is_healthy:
                self.failure_count += 1
                
                if self.failure_count >= self.policy.failure_threshold:
                    await self._trigger_failover()
            else:
                self.failure_count = 0
        
        except Exception as e:
            print(f"Error checking primary health: {e}")
    
    async def _perform_health_check(self, node_id: str) -> bool:
        """Perform health check on a node"""
        try:
            # In production, make HTTP/RPC call to node
            # For now, simulate health check
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _trigger_failover(self) -> None:
        """Trigger failover to secondary"""
        if self.failover_state != FailoverState.NORMAL:
            return  # Already failing over
        
        try:
            async with self.lock:
                self.failover_state = FailoverState.DETECTING
                
                print(f"Triggering failover from {self.primary_node}")
                
                # Select best secondary
                secondary = await self._select_secondary()
                if not secondary:
                    print("No healthy secondary available")
                    self.failover_state = FailoverState.FAILED
                    return
                
                self.failover_state = FailoverState.FAILING_OVER
                start_time = time.time()
                
                # Execute failover
                success = await self._execute_failover(self.primary_node, secondary)
                
                duration = time.time() - start_time
                
                # Record event
                event = FailoverEvent(
                    event_id=f"failover_{int(time.time())}",
                    event_type="failover",
                    from_node=self.primary_node or "unknown",
                    to_node=secondary,
                    reason=f"Primary health check failed {self.failure_count} times",
                    duration_seconds=duration,
                    success=success
                )
                
                self.failover_history.append(event)
                if len(self.failover_history) > self.max_history:
                    self.failover_history = self.failover_history[-self.max_history:]
                
                if success:
                    # Update roles
                    old_primary = self.primary_node
                    self.primary_node = secondary
                    if old_primary:
                        self.secondary_nodes.append(old_primary)
                    self.secondary_nodes.remove(secondary)
                    
                    self.last_failover = datetime.utcnow()
                    self.failover_state = FailoverState.FAILED_OVER
                    self.failure_count = 0
                    
                    print(f"Failover successful: {secondary} is now primary")
                    
                    # Notify callbacks
                    await self._notify_failover_callbacks(event)
                else:
                    self.failover_state = FailoverState.FAILED
                    print(f"Failover failed")
        
        except Exception as e:
            print(f"Error in failover: {e}")
            self.failover_state = FailoverState.FAILED
    
    async def _select_secondary(self) -> Optional[str]:
        """Select best secondary for failover"""
        try:
            if not self.secondary_nodes:
                return None
            
            # Check health of all secondaries
            healthy_secondaries = []
            for node_id in self.secondary_nodes:
                if await self._perform_health_check(node_id):
                    healthy_secondaries.append(node_id)
            
            if not healthy_secondaries:
                return None
            
            # Return first healthy secondary
            return healthy_secondaries[0]
        
        except Exception as e:
            print(f"Error selecting secondary: {e}")
            return None
    
    async def _execute_failover(self, from_node: str, to_node: str) -> bool:
        """Execute the failover process"""
        try:
            # 1. Notify old primary to stop (if reachable)
            try:
                await self._notify_node_stop(from_node)
            except Exception:
                pass  # Primary may be unreachable
            
            # 2. Transfer state to new primary
            await self._transfer_state(from_node, to_node)
            
            # 3. Promote secondary to primary
            await self._promote_node(to_node)
            
            # 4. Verify new primary is operational
            is_healthy = await self._perform_health_check(to_node)
            
            return is_healthy
        
        except Exception as e:
            print(f"Error executing failover: {e}")
            return False
    
    async def _notify_node_stop(self, node_id: str) -> None:
        """Notify node to stop being primary"""
        # In production, make RPC call
        await asyncio.sleep(0.1)
    
    async def _transfer_state(self, from_node: str, to_node: str) -> None:
        """Transfer state from old primary to new primary"""
        # In production, transfer actual state
        await asyncio.sleep(0.5)
    
    async def _promote_node(self, node_id: str) -> None:
        """Promote node to primary"""
        # In production, notify node of promotion
        await asyncio.sleep(0.1)
    
    async def _notify_failover_callbacks(self, event: FailoverEvent) -> None:
        """Notify registered callbacks of failover"""
        for callback in self.failover_callbacks:
            try:
                await callback(event)
            except Exception as e:
                print(f"Callback error: {e}")
    
    async def attempt_failback(self) -> bool:
        """Attempt to failback to original primary"""
        try:
            if not self.last_failover:
                return False
            
            # Check if enough time has passed
            time_since_failover = (datetime.utcnow() - self.last_failover).total_seconds()
            if time_since_failover < self.policy.recovery_wait_time:
                return False
            
            # Find original primary in secondaries
            if not self.secondary_nodes:
                return False
            
            original_primary = self.secondary_nodes[-1]  # Last added (was old primary)
            
            # Check if original primary is healthy
            if not await self._perform_health_check(original_primary):
                return False
            
            async with self.lock:
                self.failover_state = FailoverState.RECOVERING
                
                # Execute failback
                success = await self._execute_failover(self.primary_node, original_primary)
                
                if success:
                    # Record event
                    event = FailoverEvent(
                        event_id=f"failback_{int(time.time())}",
                        event_type="failback",
                        from_node=self.primary_node or "unknown",
                        to_node=original_primary,
                        reason="Manual failback",
                        success=True
                    )
                    self.failover_history.append(event)
                    
                    # Update roles
                    old_primary = self.primary_node
                    self.primary_node = original_primary
                    if old_primary:
                        self.secondary_nodes.append(old_primary)
                    self.secondary_nodes.remove(original_primary)
                    
                    self.failover_state = FailoverState.NORMAL
                    
                    await self._notify_failover_callbacks(event)
                
                return success
        
        except Exception as e:
            print(f"Error in failback: {e}")
            return False
    
    async def get_failover_status(self) -> Dict[str, Any]:
        """Get current failover status"""
        try:
            async with self.lock:
                return {
                    'enabled': self.enabled,
                    'role': self.current_role.value,
                    'state': self.failover_state.value,
                    'primary_node': self.primary_node,
                    'secondary_nodes': self.secondary_nodes,
                    'failure_count': self.failure_count,
                    'last_failover': (
                        self.last_failover.isoformat()
                        if self.last_failover else None
                    ),
                    'failover_count': len(self.failover_history),
                    'policy': {
                        'auto_failover': self.policy.auto_failover_enabled,
                        'failure_threshold': self.policy.failure_threshold,
                        'health_check_interval': self.policy.health_check_interval
                    }
                }
        except Exception as e:
            print(f"Error getting status: {e}")
            return {'enabled': self.enabled, 'error': str(e)}
    
    async def get_failover_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent failover events"""
        try:
            async with self.lock:
                recent = self.failover_history[-limit:]
                return [
                    {
                        'event_id': event.event_id,
                        'type': event.event_type,
                        'from_node': event.from_node,
                        'to_node': event.to_node,
                        'timestamp': event.timestamp.isoformat(),
                        'reason': event.reason,
                        'duration': event.duration_seconds,
                        'success': event.success
                    }
                    for event in recent
                ]
        except Exception as e:
            print(f"Error getting history: {e}")
            return []
    
    async def reset(self) -> bool:
        """Reset failover manager"""
        try:
            await self.disable()
            self.primary_node = None
            self.secondary_nodes.clear()
            self.failover_history.clear()
            self.failure_count = 0
            self.last_failover = None
            self.failover_state = FailoverState.NORMAL
            return True
        except Exception as e:
            print(f"Error resetting: {e}")
            return False
