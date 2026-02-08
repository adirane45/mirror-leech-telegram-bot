"""
Failover Recovery Executor - Handles recovery action execution and tracking

Responsibilities:
- Queuing recovery actions
- Executing recovery operations with retries
- Tracking operation state and metrics
- Managing concurrent recovery limits
"""

import asyncio
from datetime import datetime, UTC
from typing import Dict, List, Optional

from .failover_models import (
    RecoveryState,
    RecoveryAction,
    RecoveryOperation,
    RecoveryMetrics,
    RecoveryHandler,
    DefaultRecoveryHandler,
    FailoverEventListener,
)


class FailoverRecoveryExecutor:
    """Executes recovery actions with tracking and metrics"""
    
    def __init__(self, max_concurrent_recoveries: int = 5, listeners: Optional[List[FailoverEventListener]] = None):
        """Initialize recovery executor"""
        self.operations: Dict[str, RecoveryOperation] = {}
        self.pending_actions: List[RecoveryAction] = []
        self.recovery_queue: asyncio.Queue = asyncio.Queue()
        
        self.max_concurrent_recoveries = max_concurrent_recoveries
        self.default_handler = DefaultRecoveryHandler()
        self.custom_handlers: Dict[str, RecoveryHandler] = {}
        self.listeners = listeners or []
        
        self.metrics = RecoveryMetrics()
        
        self.enabled = False
        self._executor_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
    
    async def start(self) -> bool:
        """Start recovery executor"""
        if self.enabled:
            return True
        
        try:
            self.enabled = True
            self._executor_task = asyncio.create_task(self._recovery_executor_loop())
            self._metrics_task = asyncio.create_task(self._metrics_collector_loop())
            return True
        except Exception:
            self.enabled = False
            return False
    
    async def stop(self) -> bool:
        """Stop recovery executor"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            
            for task in [self._executor_task, self._metrics_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            return True
        except Exception:
            return False
    
    async def queue_recovery_action(self, action: RecoveryAction) -> bool:
        """Queue a recovery action for execution"""
        try:
            self.pending_actions.append(action)
            await self.recovery_queue.put(action)
            return True
        except Exception:
            return False
    
    async def _recovery_executor_loop(self) -> None:
        """Background loop to execute recovery actions"""
        concurrent_count = 0
        
        while self.enabled:
            try:
                # Get next action if under concurrency limit
                if concurrent_count < self.max_concurrent_recoveries:
                    try:
                        action = self.recovery_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        action = None
                        await asyncio.sleep(0.1)
                else:
                    await asyncio.sleep(0.5)
                    continue
                
                if action:
                    concurrent_count += 1
                    asyncio.create_task(self._execute_recovery(action, concurrent_count))
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)
    
    async def _execute_recovery(self, action: RecoveryAction, concurrent_id: int) -> None:
        """Execute a single recovery action"""
        operation = RecoveryOperation(action=action)
        self.operations[operation.operation_id] = operation
        
        try:
            operation.state = RecoveryState.IN_PROGRESS
            operation.started_at = datetime.now(UTC)
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_recovery_started(operation.operation_id)
            
            # Execute with retries
            success = False
            while operation.attempts < action.max_retries and not success:
                operation.attempts += 1
                
                try:
                    result = await asyncio.wait_for(
                        self.default_handler.execute(action),
                        timeout=action.timeout_seconds
                    )
                    success = result
                    
                    if not success and operation.attempts < action.max_retries:
                        await asyncio.sleep(1)  # Back off before retry
                
                except asyncio.TimeoutError:
                    operation.last_error = "Recovery action timed out"
                    operation.state = RecoveryState.TIMEOUT
                except Exception as e:
                    operation.last_error = str(e)
            
            # Update operation state
            if success:
                operation.state = RecoveryState.SUCCEEDED
                self.metrics.successful_operations += 1
            else:
                operation.state = RecoveryState.FAILED
                self.metrics.failed_operations += 1
            
            operation.completed_at = datetime.now(UTC)
            
            # Update metrics
            self.metrics.total_operations += 1
            if operation.started_at and operation.completed_at:
                duration_ms = (operation.completed_at - operation.started_at).total_seconds() * 1000
                old_avg = self.metrics.avg_recovery_time_ms
                self.metrics.avg_recovery_time_ms = (
                    (old_avg * (self.metrics.total_operations - 1) + duration_ms) /
                    self.metrics.total_operations
                )
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_recovery_completed(operation.operation_id, success)
            
            # Clean from pending
            if action in self.pending_actions:
                self.pending_actions.remove(action)
        
        except Exception:
            operation.state = RecoveryState.FAILED
            operation.completed_at = datetime.now(UTC)
            self.metrics.failed_operations += 1
            self.metrics.total_operations += 1
    
    async def _metrics_collector_loop(self) -> None:
        """Background loop to collect metrics"""
        while self.enabled:
            try:
                if self.metrics.total_operations > 0:
                    self.metrics.uptime_percentage = (
                        self.metrics.successful_operations / self.metrics.total_operations * 100
                    )
                
                await asyncio.sleep(5)
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)
    
    async def get_operation_status(self, operation_id: str) -> Optional[RecoveryOperation]:
        """Get status of a recovery operation"""
        return self.operations.get(operation_id)
    
    async def get_active_operations(self) -> Dict[str, RecoveryOperation]:
        """Get all active recovery operations"""
        return {
            op_id: op for op_id, op in self.operations.items()
            if op.state == RecoveryState.IN_PROGRESS
        }
    
    async def get_pending_actions(self) -> List[RecoveryAction]:
        """Get all pending recovery actions"""
        return list(self.pending_actions)
    
    async def get_recovery_metrics(self) -> RecoveryMetrics:
        """Get current recovery metrics"""
        return self.metrics
    
    async def clear_operation_history(self, older_than_hours: int = 24) -> int:
        """Clear old operation history"""
        try:
            from datetime import timedelta
            cutoff = datetime.now(UTC) - timedelta(hours=older_than_hours)
            to_delete = [
                op_id for op_id, op in self.operations.items()
                if op.completed_at and op.completed_at < cutoff
            ]
            
            for op_id in to_delete:
                del self.operations[op_id]
            
            return len(to_delete)
        except Exception:
            return 0
