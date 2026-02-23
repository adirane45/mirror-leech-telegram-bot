"""
Models and handlers for failover management

Includes:
- Recovery operation enumerations and states
- Cascade event tracking
- Recovery handlers and strategies
- Performance metrics
- Event listener interfaces
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    
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
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
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
