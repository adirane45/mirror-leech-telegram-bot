"""
Distributed State Manager - Data Models, Enums, and Base Classes

Defines:
- Enumerations for state operations (StateUpdateStrategy, LockType, etc.)
- Data classes for state versioning, snapshots, locks
- Abstract base classes for extensibility

Used by: distributed_state_core, distributed_state_locks
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, List, Set, Optional, Any
from abc import ABC, abstractmethod


# ============================================================================
# ENUMERATIONS
# ============================================================================

class StateUpdateStrategy(str, Enum):
    """Strategies for applying state updates"""
    CONSENSUS = "consensus"      # Requires quorum agreement
    OPTIMISTIC = "optimistic"    # Apply immediately, replicate later
    PESSIMISTIC = "pessimistic"  # Lock-based pessimistic updates
    EVENTUAL = "eventual"        # Eventual consistency


class LockType(str, Enum):
    """Types of distributed locks"""
    EXCLUSIVE = "exclusive"      # Only one writer
    SHARED = "shared"           # Multiple readers, no writers
    INTENT_EXCLUSIVE = "intent_exclusive"  # Allows shared reads


class LockState(str, Enum):
    """State of a distributed lock"""
    PENDING = "pending"
    ACQUIRED = "acquired"
    RELEASED = "released"
    CONTESTED = "contested"  # Multiple nodes want lock
    TIMEOUT = "timeout"


class StateReconciliationReason(str, Enum):
    """Reasons for state reconciliation"""
    VERSION_MISMATCH = "version_mismatch"
    RECOVERY = "recovery"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    CONFLICT = "conflict"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class StateVersion:
    """Version information for state"""
    version_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version_number: int = 1
    node_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    changes_count: int = 0
    checksum: str = ""
    parent_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'version_id': self.version_id,
            'version_number': self.version_number,
            'node_id': self.node_id,
            'timestamp': self.timestamp.isoformat(),
            'changes_count': self.changes_count,
            'checksum': self.checksum,
            'parent_version': self.parent_version
        }


@dataclass
class StateSnapshot:
    """Snapshot of state at a point in time"""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: StateVersion = field(default_factory=StateVersion)
    state_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    size_bytes: int = 0
    compressible: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'snapshot_id': self.snapshot_id,
            'version': self.version.to_dict(),
            'state_data': self.state_data,
            'timestamp': self.timestamp.isoformat(),
            'size_bytes': self.size_bytes,
            'compressible': self.compressible
        }


@dataclass
class StateChangeLog:
    """Log entry for a state change"""
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    old_value: Any = None
    new_value: Any = None
    operation_type: str = ""  # SET, DELETE, INCREMENT
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    applied_node: str = ""
    applied_version: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'log_id': self.log_id,
            'key': self.key,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'operation_type': self.operation_type,
            'timestamp': self.timestamp.isoformat(),
            'applied_node': self.applied_node,
            'applied_version': self.applied_version
        }


@dataclass
class LockInfo:
    """Information about a distributed lock"""
    lock_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    lock_type: LockType = LockType.EXCLUSIVE
    owner_node: str = ""
    state: LockState = LockState.PENDING
    acquired_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    contenders: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'lock_id': self.lock_id,
            'key': self.key,
            'lock_type': self.lock_type.value,
            'owner_node': self.owner_node,
            'state': self.state.value,
            'acquired_at': self.acquired_at.isoformat() if self.acquired_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'contenders': list(self.contenders)
        }


@dataclass
class ConsensusProposal:
    """Proposal for state update via consensus"""
    proposal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    value: Any = None
    proposer_node: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    votes_for: Set[str] = field(default_factory=set)
    votes_against: Set[str] = field(default_factory=set)
    state: str = "pending"  # pending, approved, rejected, applied
    consensus_threshold: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'proposal_id': self.proposal_id,
            'key': self.key,
            'value': self.value,
            'proposer_node': self.proposer_node,
            'timestamp': self.timestamp.isoformat(),
            'votes_for': list(self.votes_for),
            'votes_against': list(self.votes_against),
            'state': self.state,
            'consensus_threshold': self.consensus_threshold
        }


@dataclass
class StateReconciliationRequest:
    """Request for state reconciliation"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    initiator_node: str = ""
    target_node: str = ""
    reason: StateReconciliationReason = StateReconciliationReason.SCHEDULED
    local_version: int = 0
    remote_version: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'request_id': self.request_id,
            'initiator_node': self.initiator_node,
            'target_node': self.target_node,
            'reason': self.reason.value,
            'local_version': self.local_version,
            'remote_version': self.remote_version,
            'timestamp': self.timestamp.isoformat(),
            'completed': self.completed
        }


@dataclass
class DistributedStateMetrics:
    """Metrics for distributed state management"""
    total_state_updates: int = 0
    consensual_updates: int = 0
    optimistic_updates: int = 0
    reconciliations: int = 0
    lock_acquisitions: int = 0
    lock_contentions: int = 0
    snapshots_created: int = 0
    state_size_bytes: int = 0
    version_count: int = 0
    average_consistency_lag_ms: float = 0.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'total_state_updates': self.total_state_updates,
            'consensual_updates': self.consensual_updates,
            'optimistic_updates': self.optimistic_updates,
            'reconciliations': self.reconciliations,
            'lock_acquisitions': self.lock_acquisitions,
            'lock_contentions': self.lock_contentions,
            'snapshots_created': self.snapshots_created,
            'state_size_bytes': self.state_size_bytes,
            'version_count': self.version_count,
            'average_consistency_lag_ms': round(self.average_consistency_lag_ms, 2),
            'last_updated': self.last_updated.isoformat()
        }


# ============================================================================
# ABSTRACT BASE CLASSES
# ============================================================================

class DistributedStateProvider(ABC):
    """Abstract provider for distributed state operations"""
    
    @abstractmethod
    async def get_state(self, key: str) -> Any:
        """Get state value for key"""
        pass
    
    @abstractmethod
    async def set_state(self, key: str, value: Any) -> bool:
        """Set state value for key"""
        pass
    
    @abstractmethod
    async def acquire_lock(self, key: str, lock_type: LockType) -> bool:
        """Acquire lock on key"""
        pass
    
    @abstractmethod
    async def release_lock(self, key: str) -> bool:
        """Release lock on key"""
        pass


class StateChangeListener(ABC):
    """Abstract listener for state changes"""
    
    @abstractmethod
    async def on_state_changed(self, key: str, old_value: Any, new_value: Any) -> None:
        """Called when state changes"""
        pass
    
    @abstractmethod
    async def on_reconciliation_started(self, request: StateReconciliationRequest) -> None:
        """Called when reconciliation starts"""
        pass
    
    @abstractmethod
    async def on_reconciliation_completed(self, request: StateReconciliationRequest) -> None:
        """Called when reconciliation completes"""
        pass
    
    @abstractmethod
    async def on_consensus_reached(self, proposal: ConsensusProposal) -> None:
        """Called when consensus is reached"""
        pass
    
    @abstractmethod
    async def on_lock_acquired(self, lock: LockInfo) -> None:
        """Called when lock is acquired"""
        pass
