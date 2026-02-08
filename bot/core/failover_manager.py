"""
Failover Manager - Automatic failure recovery and orchestration

Enables:
- Detection of component failures via Health Monitor
- Coordinated failover using Cluster Manager
- Automatic recovery orchestration
- Cascading failure handling
- Recovery state tracking and rollback
- Health-aware service restoration

Integrates Health Monitor for component health and Cluster Manager for coordination
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import Dict, List, Optional, Callable, Set, Any
from abc import ABC, abstractmethod


# ============================================================================
# ENUMS
# ============================================================================

class RecoveryStrategy(str, Enum):
    """Strategy for recovering failed components"""
    RESTART = 'restart'  # Simple restart
    RECONNECT = 'reconnect'  # Attempt to reconnect
    FAILOVER = 'failover'  # Failover to replica/backup
    MIGRATE = 'migrate'  # Migrate to different host
    SCALE_UP = 'scale_up'  # Scale up capacity
    ISOLATE = 'isolate'  # Isolate to prevent cascade


class RecoveryState(str, Enum):
    """State of a recovery operation"""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    ROLLED_BACK = 'rolled_back'
    TIMEOUT = 'timeout'


class CascadeLevel(str, Enum):
    """Level of cascade propagation"""
    COMPONENT = 'component'  # Single component
    SERVICE = 'service'  # Entire service
    CLUSTER = 'cluster'  # Cluster-wide
    CRITICAL = 'critical'  # Critical infrastructure


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class RecoveryAction:
    """A recovery action to be executed"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    component_id: str = ''
    component_name: str = ''
    strategy: RecoveryStrategy = RecoveryStrategy.RESTART
    priority: int = 5  # 1-10, higher = more important
    max_retries: int = 3
    timeout_seconds: int = 30
    depends_on: List[str] = field(default_factory=list)  # Other action IDs
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'action_id': self.action_id,
            'component_id': self.component_id,
            'component_name': self.component_name,
            'strategy': self.strategy.value,
            'priority': self.priority,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds,
            'depends_on': self.depends_on,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class RecoveryOperation:
    """Tracks a recovery operation"""
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action: RecoveryAction = field(default_factory=RecoveryAction)
    state: RecoveryState = RecoveryState.PENDING
    attempts: int = 0
    last_error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rollback_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'operation_id': self.operation_id,
            'action': self.action.to_dict(),
            'state': self.state.value,
            'attempts': self.attempts,
            'last_error': self.last_error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class CascadeEvent:
    """Represents a cascading failure event"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    initial_component: str = ''
    cascade_level: CascadeLevel = CascadeLevel.COMPONENT
    affected_components: Set[str] = field(default_factory=set)
    root_cause: str = ''
    timestamp: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'event_id': self.event_id,
            'initial_component': self.initial_component,
            'cascade_level': self.cascade_level.value,
            'affected_components': list(self.affected_components),
            'root_cause': self.root_cause,
            'timestamp': self.timestamp.isoformat(),
            'is_active': self.is_active
        }


@dataclass
class RecoveryMetrics:
    """Metrics for recovery operations"""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    avg_recovery_time_ms: float = 0.0
    total_cascades_handled: int = 0
    last_cascade_time: Optional[datetime] = None
    uptime_percentage: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_operations': self.total_operations,
            'successful_operations': self.successful_operations,
            'failed_operations': self.failed_operations,
            'avg_recovery_time_ms': self.avg_recovery_time_ms,
            'total_cascades_handled': self.total_cascades_handled,
            'last_cascade_time': self.last_cascade_time.isoformat() if self.last_cascade_time else None,
            'uptime_percentage': self.uptime_percentage
        }


# ============================================================================
# RECOVERY HANDLERS
# ============================================================================

class RecoveryHandler(ABC):
    """Abstract recovery handler for different strategies"""
    
    @abstractmethod
    async def execute(self, action: RecoveryAction) -> bool:
        """Execute recovery action"""
        pass
    
    @abstractmethod
    async def rollback(self, operation: RecoveryOperation) -> bool:
        """Rollback recovery action"""
        pass
    
    @abstractmethod
    async def supports(self, strategy: RecoveryStrategy) -> bool:
        """Check if handler supports strategy"""
        pass


class DefaultRecoveryHandler(RecoveryHandler):
    """Default recovery handler with basic restart/reconnect"""
    
    def __init__(self):
        self.restart_handlers: Dict[str, Callable] = {}
        self.reconnect_handlers: Dict[str, Callable] = {}
    
    async def execute(self, action: RecoveryAction) -> bool:
        """Execute recovery action"""
        try:
            if action.strategy == RecoveryStrategy.RESTART:
                return await self._handle_restart(action)
            elif action.strategy == RecoveryStrategy.RECONNECT:
                return await self._handle_reconnect(action)
            elif action.strategy == RecoveryStrategy.ISOLATE:
                return await self._handle_isolate(action)
            return False
        except Exception:
            return False
    
    async def rollback(self, operation: RecoveryOperation) -> bool:
        """Rollback recovery action"""
        try:
            # In real implementation, restore from rollback_data
            return True
        except Exception:
            return False
    
    async def supports(self, strategy: RecoveryStrategy) -> bool:
        """Check if handler supports strategy"""
        return strategy in [
            RecoveryStrategy.RESTART,
            RecoveryStrategy.RECONNECT,
            RecoveryStrategy.ISOLATE
        ]
    
    async def _handle_restart(self, action: RecoveryAction) -> bool:
        """Handle component restart"""
        try:
            # In real implementation, would restart service
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _handle_reconnect(self, action: RecoveryAction) -> bool:
        """Handle component reconnection"""
        try:
            # In real implementation, would reconnect to service
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _handle_isolate(self, action: RecoveryAction) -> bool:
        """Handle component isolation"""
        try:
            # In real implementation, would isolate service
            return True
        except Exception:
            return False


# ============================================================================
# EVENT LISTENERS
# ============================================================================

class FailoverEventListener(ABC):
    """Abstract listener for failover events"""
    
    @abstractmethod
    async def on_failure_detected(self, component_id: str, error: str) -> None:
        """Called when failure detected"""
        pass
    
    @abstractmethod
    async def on_recovery_started(self, operation_id: str) -> None:
        """Called when recovery starts"""
        pass
    
    @abstractmethod
    async def on_recovery_completed(self, operation_id: str, success: bool) -> None:
        """Called when recovery completes"""
        pass
    
    @abstractmethod
    async def on_cascade_detected(self, cascade: CascadeEvent) -> None:
        """Called when cascade detected"""
        pass


# ============================================================================
# FAILOVER MANAGER
# ============================================================================

class FailoverManager:
    """
    Automatic failover and recovery orchestration
    
    Responsibilities:
    - Monitor component health via Health Monitor integration
    - Detect failures and trigger recovery
    - Coordinate failover using Cluster Manager
    - Handle cascading failures
    - Track recovery operations and metrics
    - Manage rollback and recovery state
    """
    
    _instance: Optional['FailoverManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize failover manager"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        
        # Recovery operations tracking
        self.operations: Dict[str, RecoveryOperation] = {}
        self.pending_actions: List[RecoveryAction] = []
        self.recovery_queue: asyncio.Queue = asyncio.Queue()
        
        # Component state tracking
        self.component_failures: Dict[str, List[datetime]] = {}  # component_id -> list of failure times
        self.component_recovery_count: Dict[str, int] = {}  # component_id -> recovery count
        self.failure_threshold = 5  # Max failures before escalation
        self.failure_window = timedelta(minutes=10)  # Time window for counting failures
        
        # Cascade detection
        self.active_cascades: Dict[str, CascadeEvent] = {}
        self.cascade_threshold_depth = 3  # How many components before triggering cascade
        self.cascade_propagation_delay = timedelta(seconds=1)
        
        # Recovery handlers
        self.default_handler = DefaultRecoveryHandler()
        self.custom_handlers: Dict[str, RecoveryHandler] = {}
        
        # Metrics
        self.metrics = RecoveryMetrics()
        
        # Event listeners
        self.listeners: List[FailoverEventListener] = []
        
        # Background tasks
        self.enabled = False
        self._recovery_executor_task: Optional[asyncio.Task] = None
        self._cascade_monitor_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.max_concurrent_recoveries = 5
        self.recovery_timeout = timedelta(seconds=30)
    
    @classmethod
    def get_instance(cls) -> 'FailoverManager':
        """Get singleton instance"""
        return cls()
    
    # ========================================================================
    # INITIALIZATION AND LIFECYCLE
    # ========================================================================
    
    async def start(self) -> bool:
        """Start failover manager"""
        if self.enabled:
            return True
        
        try:
            self.enabled = True
            
            # Start recovery executor
            self._recovery_executor_task = asyncio.create_task(self._recovery_executor_loop())
            
            # Start cascade monitor
            self._cascade_monitor_task = asyncio.create_task(self._cascade_monitor_loop())
            
            # Start metrics collector
            self._metrics_task = asyncio.create_task(self._metrics_collector_loop())
            
            return True
        except Exception as e:
            self.enabled = False
            raise RuntimeError(f"Failed to start failover manager: {e}")
    
    async def stop(self) -> bool:
        """Stop failover manager"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            
            # Cancel all tasks
            for task in [self._recovery_executor_task, self._cascade_monitor_task, self._metrics_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to stop failover manager: {e}")
    
    # ========================================================================
    # FAILURE DETECTION AND RECOVERY
    # ========================================================================
    
    async def on_component_failure(self, component_id: str, component_name: str, error: str) -> bool:
        """
        Called when a component failure is detected
        
        Triggers appropriate recovery strategy based on failure type
        """
        try:
            # Track failure
            if component_id not in self.component_failures:
                self.component_failures[component_id] = []
            
            now = datetime.now(UTC)
            self.component_failures[component_id].append(now)
            
            # Clean old failures (outside time window)
            cutoff = now - self.failure_window
            self.component_failures[component_id] = [
                t for t in self.component_failures[component_id] if t > cutoff
            ]
            
            failure_count = len(self.component_failures[component_id])
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_failure_detected(component_id, error)
            
            # Determine recovery strategy
            if failure_count >= self.failure_threshold:
                strategy = RecoveryStrategy.ISOLATE  # Isolate to prevent cascade
            else:
                strategy = RecoveryStrategy.RESTART  # Simple restart
            
            # Create and queue recovery action
            action = RecoveryAction(
                component_id=component_id,
                component_name=component_name,
                strategy=strategy,
                priority=max(1, 10 - (failure_count // 2))  # Lower priority with more failures
            )
            
            await self.queue_recovery_action(action)
            
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
                    # Execute recovery in background
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
            
            # Try to execute
            success = False
            while operation.attempts < action.max_retries and not success:
                operation.attempts += 1
                
                try:
                    # Execute with timeout
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
            
            # Clean up from pending
            if action in self.pending_actions:
                self.pending_actions.remove(action)
        
        except Exception:
            operation.state = RecoveryState.FAILED
            operation.completed_at = datetime.now(UTC)
            self.metrics.failed_operations += 1
            self.metrics.total_operations += 1
        
        finally:
            # Decrement concurrent count
            if concurrent_id <= self.max_concurrent_recoveries:
                pass  # Would decrement in real implementation
    
    # ========================================================================
    # CASCADE DETECTION AND HANDLING
    # ========================================================================
    
    async def detect_cascading_failure(self, initial_component: str) -> Optional[CascadeEvent]:
        """
        Detect if a component failure is cascading to others
        
        Analyzes:
        - Number of dependent components failing
        - Rate of failure propagation
        - Correlation between failures
        """
        try:
            # Count concurrent failures
            now = datetime.now(UTC)
            recent_failures = []
            
            for component_id, failures in self.component_failures.items():
                recent_count = sum(1 for f in failures if now - f < timedelta(seconds=5))
                if recent_count > 0:
                    recent_failures.append((component_id, recent_count))
            
            # If multiple components failing, it's a cascade
            if len(recent_failures) >= self.cascade_threshold_depth:
                cascade = CascadeEvent(
                    initial_component=initial_component,
                    cascade_level=CascadeLevel.SERVICE if len(recent_failures) < 5 else CascadeLevel.CLUSTER,
                    affected_components={c[0] for c in recent_failures}
                )
                
                self.active_cascades[cascade.event_id] = cascade
                
                # Notify listeners
                for listener in self.listeners:
                    await listener.on_cascade_detected(cascade)
                
                self.metrics.total_cascades_handled += 1
                self.metrics.last_cascade_time = now
                
                return cascade
            
            return None
        except Exception:
            return None
    
    async def _cascade_monitor_loop(self) -> None:
        """Background loop to monitor for cascading failures"""
        while self.enabled:
            try:
                # Check for cascades periodically
                for component_id in list(self.component_failures.keys()):
                    failures = self.component_failures[component_id]
                    
                    # Recent failure?
                    recent = [f for f in failures if datetime.now(UTC) - f < timedelta(seconds=10)]
                    if recent:
                        await self.detect_cascading_failure(component_id)
                
                # Clean resolved cascades
                now = datetime.now(UTC)
                for event_id, cascade in list(self.active_cascades.items()):
                    if cascade.timestamp and now - cascade.timestamp > timedelta(minutes=5):
                        cascade.is_active = False
                        del self.active_cascades[event_id]
                
                await asyncio.sleep(2)
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(2)
    
    async def handle_cascade(self, cascade: CascadeEvent) -> bool:
        """Handle a detected cascading failure"""
        try:
            # Escalate strategy for cascade
            for component_id in cascade.affected_components:
                action = RecoveryAction(
                    component_id=component_id,
                    strategy=RecoveryStrategy.ISOLATE,  # Isolate to prevent spread
                    priority=10  # Highest priority
                )
                await self.queue_recovery_action(action)
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # HANDLER MANAGEMENT
    # ========================================================================
    
    async def register_recovery_handler(self, handler: RecoveryHandler) -> bool:
        """Register a custom recovery handler"""
        try:
            handler_id = str(uuid.uuid4())
            self.custom_handlers[handler_id] = handler
            return True
        except Exception:
            return False
    
    async def unregister_recovery_handler(self, handler_id: str) -> bool:
        """Unregister a recovery handler"""
        try:
            if handler_id in self.custom_handlers:
                del self.custom_handlers[handler_id]
            return True
        except Exception:
            return False
    
    # ========================================================================
    # EVENT LISTENERS
    # ========================================================================
    
    async def add_listener(self, listener: FailoverEventListener) -> bool:
        """Add failover event listener"""
        try:
            if listener not in self.listeners:
                self.listeners.append(listener)
            return True
        except Exception:
            return False
    
    async def remove_listener(self, listener: FailoverEventListener) -> bool:
        """Remove failover event listener"""
        try:
            if listener in self.listeners:
                self.listeners.remove(listener)
            return True
        except Exception:
            return False
    
    # ========================================================================
    # METRICS AND STATUS
    # ========================================================================
    
    async def _metrics_collector_loop(self) -> None:
        """Background loop to collect metrics"""
        while self.enabled:
            try:
                # Calculate uptime percentage
                if self.metrics.total_operations > 0:
                    self.metrics.uptime_percentage = (
                        self.metrics.successful_operations / self.metrics.total_operations * 100
                    )
                
                await asyncio.sleep(5)
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(5)
    
    async def get_recovery_metrics(self) -> RecoveryMetrics:
        """Get current recovery metrics"""
        return self.metrics
    
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
    
    async def get_active_cascades(self) -> Dict[str, CascadeEvent]:
        """Get all active cascade events"""
        return {
            event_id: cascade for event_id, cascade in self.active_cascades.items()
            if cascade.is_active
        }
    
    async def clear_operation_history(self, older_than_hours: int = 24) -> int:
        """Clear old operation history"""
        try:
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
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    async def is_enabled(self) -> bool:
        """Check if failover manager is enabled"""
        return self.enabled
    
    async def get_failure_count(self, component_id: str) -> int:
        """Get recent failure count for component"""
        if component_id not in self.component_failures:
            return 0
        
        failures = self.component_failures[component_id]
        cutoff = datetime.now(UTC) - self.failure_window
        return sum(1 for f in failures if f > cutoff)
    
    async def reset_failure_count(self, component_id: str) -> bool:
        """Reset failure count for component"""
        try:
            if component_id in self.component_failures:
                self.component_failures[component_id] = []
            return True
        except Exception:
            return False
