"""
Distributed State Manager for cluster-wide state consistency

Implements:
- State versioning with changelog
- Consensus-based updates
- Distributed locking
- State reconciliation
- Snapshot/restore mechanism
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Set, Optional, Any, Callable
from abc import ABC, abstractmethod


# ============================================================================
# ENUMS AND DATA CLASSES
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


@dataclass
class StateVersion:
    """Version information for state"""
    version_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version_number: int = 1
    node_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
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
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
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
# ABSTRACT CLASSES
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


# ============================================================================
# DISTRIBUTED STATE MANAGER
# ============================================================================

class DistributedStateManager:
    """
    Manages distributed state with consensus, locking, and reconciliation
    
    Singleton instance managing:
    - State versioning with changelog
    - Consensus-based updates
    - Distributed locking
    - State reconciliation
    - Snapshot/restore mechanism
    """
    
    _instance: Optional['DistributedStateManager'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.enabled = False
        self.node_id = ""
        self.state: Dict[str, Any] = {}
        self.version_history: List[StateVersion] = []
        self.change_log: List[StateChangeLog] = []
        self.snapshots: Dict[str, StateSnapshot] = {}
        self.locks: Dict[str, LockInfo] = {}
        self.proposals: Dict[str, ConsensusProposal] = {}
        self.peers: Set[str] = set()
        self.metrics = DistributedStateMetrics()
        self.listeners: List[StateChangeListener] = []
        self.current_version = 1
        self.update_strategy = StateUpdateStrategy.EVENTUAL
        self.consensus_threshold = 0.5
        self.lock_timeout_seconds = 30
        self.reconciliation_interval = 60
        self.snapshot_retention_count = 10
        
        # Background tasks
        self._reconciliation_task: Optional[asyncio.Task] = None
        self._lock_monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    @classmethod
    def get_instance(cls) -> 'DistributedStateManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def start(self, node_id: str = "") -> bool:
        """Start distributed state manager"""
        if self.enabled:
            return True
        
        try:
            self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
            self.enabled = True
            
            # Initialize root version
            root_version = StateVersion(
                version_number=1,
                node_id=self.node_id,
                checksum=self._calculate_checksum()
            )
            self.version_history.append(root_version)
            
            # Start background tasks
            self._reconciliation_task = asyncio.create_task(self._reconciliation_loop())
            self._lock_monitor_task = asyncio.create_task(self._lock_monitor_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            return True
        except Exception:
            self.enabled = False
            return False
    
    async def stop(self) -> bool:
        """Stop distributed state manager"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            
            # Cancel background tasks
            if self._reconciliation_task:
                self._reconciliation_task.cancel()
            if self._lock_monitor_task:
                self._lock_monitor_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()
            
            await asyncio.sleep(0.1)
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # STATE OPERATIONS
    # ========================================================================
    
    async def get_state(self, key: str) -> Optional[Any]:
        """Get value from state"""
        return self.state.get(key)
    
    async def set_state(self, key: str, value: Any, strategy: Optional[StateUpdateStrategy] = None) -> bool:
        """
        Set state value using specified strategy
        
        Args:
            key: State key
            value: New value
            strategy: Update strategy (uses default if None)
        
        Returns:
            True if update succeeded
        """
        if not self.enabled:
            return False
        
        try:
            strategy = strategy or self.update_strategy
            old_value = self.state.get(key)
            
            if strategy == StateUpdateStrategy.CONSENSUS:
                # Require consensus from peers
                return await self._update_with_consensus(key, value, old_value)
            
            elif strategy == StateUpdateStrategy.PESSIMISTIC:
                # Acquire lock first
                lock_acquired = await self.acquire_lock(key, LockType.EXCLUSIVE)
                if not lock_acquired:
                    return False
                
                result = await self._apply_state_update(key, value, old_value)
                await self.release_lock(key)
                return result
            
            elif strategy == StateUpdateStrategy.OPTIMISTIC:
                # Apply immediately
                return await self._apply_state_update(key, value, old_value)
            
            else:  # EVENTUAL
                # Apply with replication
                return await self._apply_state_update(key, value, old_value)
        
        except Exception:
            return False
    
    async def delete_state(self, key: str) -> bool:
        """Delete state value"""
        if not self.enabled or key not in self.state:
            return False
        
        try:
            old_value = self.state.pop(key, None)
            
            # Log change
            log_entry = StateChangeLog(
                key=key,
                old_value=old_value,
                operation_type='DELETE',
                applied_node=self.node_id,
                applied_version=self.current_version
            )
            self.change_log.append(log_entry)
            self.metrics.total_state_updates += 1
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_state_changed(key, old_value, None)
            
            return True
        except Exception:
            return False
    
    async def increment_state(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment numeric state value"""
        if not self.enabled:
            return None
        
        try:
            current = self.state.get(key, 0)
            new_value = current + amount
            
            success = await self.set_state(key, new_value)
            return new_value if success else None
        except Exception:
            return None
    
    async def _apply_state_update(
        self,
        key: str,
        value: Any,
        old_value: Any
    ) -> bool:
        """Apply state update"""
        try:
            self.state[key] = value
            
            # Log change
            log_entry = StateChangeLog(
                key=key,
                old_value=old_value,
                new_value=value,
                operation_type='SET',
                applied_node=self.node_id,
                applied_version=self.current_version
            )
            self.change_log.append(log_entry)
            self.metrics.total_state_updates += 1
            self.metrics.optimistic_updates += 1
            
            # Update version
            await self._create_new_version()
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_state_changed(key, old_value, value)
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # DISTRIBUTED LOCKING
    # ========================================================================
    
    async def acquire_lock(self, key: str, lock_type: LockType = LockType.EXCLUSIVE) -> bool:
        """
        Acquire distributed lock on key
        """
        if not self.enabled:
            return False
        
        try:
            lock_id = f"lock_{uuid.uuid4().hex[:8]}"
            lock = LockInfo(
                lock_id=lock_id,
                key=key,
                lock_type=lock_type,
                owner_node=self.node_id,
                state=LockState.PENDING,
                expires_at=datetime.utcnow() + timedelta(seconds=self.lock_timeout_seconds)
            )
            
            # Check for existing exclusive lock
            existing = self.locks.get(key)
            if existing and existing.lock_type == LockType.EXCLUSIVE:
                if existing.owner_node != self.node_id:
                    lock.state = LockState.CONTESTED
                    lock.contenders.add(self.node_id)
                    self.metrics.lock_contentions += 1
                    self.locks[key] = lock
                    return False
            
            # Acquire lock
            lock.state = LockState.ACQUIRED
            lock.acquired_at = datetime.utcnow()
            self.locks[key] = lock
            self.metrics.lock_acquisitions += 1
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_lock_acquired(lock)
            
            return True
        except Exception:
            return False
    
    async def release_lock(self, key: str) -> bool:
        """Release distributed lock on key"""
        if key not in self.locks:
            return False
        
        try:
            lock = self.locks[key]
            if lock.owner_node != self.node_id:
                return False
            
            lock.state = LockState.RELEASED
            self.locks.pop(key, None)
            
            return True
        except Exception:
            return False
    
    async def get_lock_info(self, key: str) -> Optional[LockInfo]:
        """Get information about lock on key"""
        return self.locks.get(key)
    
    # ========================================================================
    # CONSENSUS-BASED UPDATES
    # ========================================================================
    
    async def _update_with_consensus(
        self,
        key: str,
        value: Any,
        old_value: Any
    ) -> bool:
        """Apply state update using consensus"""
        try:
            proposal = ConsensusProposal(
                key=key,
                value=value,
                proposer_node=self.node_id,
                consensus_threshold=self.consensus_threshold
            )
            
            self.proposals[proposal.proposal_id] = proposal
            
            # In real scenario, broadcast to peers
            # For now, simulate local consensus
            proposal.votes_for.add(self.node_id)
            
            # Check if consensus reached
            if await self._check_consensus(proposal):
                proposal.state = "approved"
                
                # Apply the update
                success = await self._apply_state_update(key, value, old_value)
                
                if success:
                    proposal.state = "applied"
                    self.metrics.consensual_updates += 1
                
                # Notify listeners
                for listener in self.listeners:
                    await listener.on_consensus_reached(proposal)
                
                return success
            
            return False
        except Exception:
            return False
    
    async def _check_consensus(self, proposal: ConsensusProposal) -> bool:
        """Check if proposal has reached consensus"""
        if not self.peers:
            return True
        
        total_voters = len(self.peers) + 1  # +1 for self
        votes_needed = int(total_voters * proposal.consensus_threshold)
        votes_have = len(proposal.votes_for)
        
        return votes_have >= votes_needed
    
    async def vote_on_proposal(
        self,
        proposal_id: str,
        vote_for: bool,
        from_node: str
    ) -> bool:
        """Record vote on a proposal"""
        if proposal_id not in self.proposals:
            return False
        
        try:
            proposal = self.proposals[proposal_id]
            
            if vote_for:
                proposal.votes_for.add(from_node)
            else:
                proposal.votes_against.add(from_node)
            
            # Check if consensus now reached
            if await self._check_consensus(proposal):
                proposal.state = "approved"
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # VERSIONING
    # ========================================================================
    
    async def _create_new_version(self) -> bool:
        """Create new version after state update"""
        try:
            self.current_version += 1
            
            new_version = StateVersion(
                version_number=self.current_version,
                node_id=self.node_id,
                changes_count=len(self.change_log),
                checksum=self._calculate_checksum(),
                parent_version=self.version_history[-1].version_id if self.version_history else None
            )
            
            self.version_history.append(new_version)
            self.metrics.version_count = len(self.version_history)
            
            return True
        except Exception:
            return False
    
    async def get_current_version(self) -> StateVersion:
        """Get current state version"""
        if self.version_history:
            return self.version_history[-1]
        return StateVersion(version_number=1, node_id=self.node_id)
    
    async def get_version_history(self, limit: int = 100) -> List[StateVersion]:
        """Get version history"""
        return self.version_history[-limit:]
    
    # ========================================================================
    # SNAPSHOTS
    # ========================================================================
    
    async def create_snapshot(self) -> Optional[StateSnapshot]:
        """Create snapshot of current state"""
        if not self.enabled:
            return None
        
        try:
            current_version = await self.get_current_version()
            
            snapshot = StateSnapshot(
                version=current_version,
                state_data=dict(self.state),
                size_bytes=len(str(self.state))
            )
            
            self.snapshots[snapshot.snapshot_id] = snapshot
            self.metrics.snapshots_created += 1
            
            # Cleanup old snapshots
            if len(self.snapshots) > self.snapshot_retention_count:
                oldest_id = min(
                    self.snapshots.keys(),
                    key=lambda id: self.snapshots[id].timestamp
                )
                self.snapshots.pop(oldest_id, None)
            
            return snapshot
        except Exception:
            return None
    
    async def restore_from_snapshot(self, snapshot_id: str) -> bool:
        """Restore state from snapshot"""
        if snapshot_id not in self.snapshots:
            return False
        
        try:
            snapshot = self.snapshots[snapshot_id]
            self.state = dict(snapshot.state_data)
            self.current_version = snapshot.version.version_number
            
            return True
        except Exception:
            return False
    
    async def get_snapshots(self) -> List[StateSnapshot]:
        """Get list of snapshots"""
        return list(self.snapshots.values())
    
    # ========================================================================
    # STATE RECONCILIATION
    # ========================================================================
    
    async def reconcile_with_peer(
        self,
        peer_id: str,
        remote_version: int
    ) -> bool:
        """Reconcile state with peer"""
        if not self.enabled:
            return False
        
        try:
            request = StateReconciliationRequest(
                initiator_node=self.node_id,
                target_node=peer_id,
                reason=StateReconciliationReason.VERSION_MISMATCH,
                local_version=self.current_version,
                remote_version=remote_version
            )
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_reconciliation_started(request)
            
            # In real scenario, exchange state changes
            await asyncio.sleep(0.01)
            
            request.completed = True
            self.metrics.reconciliations += 1
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_reconciliation_completed(request)
            
            return True
        except Exception:
            return False
    
    async def get_state_delta(self, since_version: int) -> List[StateChangeLog]:
        """Get state changes since version"""
        return [
            log for log in self.change_log
            if log.applied_version > since_version
        ]
    
    # ========================================================================
    # MANAGEMENT AND MONITORING
    # ========================================================================
    
    async def register_peer(self, peer_id: str) -> bool:
        """Register peer node"""
        try:
            self.peers.add(peer_id)
            return True
        except Exception:
            return False
    
    async def unregister_peer(self, peer_id: str) -> bool:
        """Unregister peer node"""
        try:
            self.peers.discard(peer_id)
            return True
        except Exception:
            return False
    
    async def add_listener(self, listener: StateChangeListener) -> bool:
        """Register state change listener"""
        try:
            self.listeners.append(listener)
            return True
        except Exception:
            return False
    
    async def remove_listener(self, listener: StateChangeListener) -> bool:
        """Unregister state change listener"""
        try:
            self.listeners.remove(listener)
            return True
        except Exception:
            return False
    
    async def get_metrics(self) -> DistributedStateMetrics:
        """Get state management metrics"""
        return self.metrics
    
    async def get_state_info(self) -> Dict[str, Any]:
        """Get information about current state"""
        return {
            'node_id': self.node_id,
            'enabled': self.enabled,
            'state_keys': len(self.state),
            'current_version': self.current_version,
            'total_changes': len(self.change_log),
            'active_locks': len(self.locks),
            'pending_proposals': len([p for p in self.proposals.values() if p.state == 'pending']),
            'snapshots': len(self.snapshots),
            'peers': list(self.peers)
        }
    
    async def get_change_log(self, limit: int = 100) -> List[StateChangeLog]:
        """Get recent change log entries"""
        return self.change_log[-limit:]
    
    async def is_enabled(self) -> bool:
        """Check if state manager is enabled"""
        return self.enabled
    
    # ========================================================================
    # BACKGROUND LOOPS
    # ========================================================================
    
    async def _reconciliation_loop(self) -> None:
        """Background loop for periodic reconciliation"""
        while self.enabled:
            try:
                # Periodically reconcile with peers
                for peer_id in list(self.peers):
                    await self.reconcile_with_peer(peer_id, self.current_version)
                
                await asyncio.sleep(self.reconciliation_interval)
            except Exception:
                await asyncio.sleep(self.reconciliation_interval)
    
    async def _lock_monitor_loop(self) -> None:
        """Background loop for monitoring locks"""
        while self.enabled:
            try:
                # Check for expired locks
                expired_keys = []
                for key, lock in self.locks.items():
                    if lock.expires_at and lock.expires_at < datetime.utcnow():
                        expired_keys.append(key)
                
                # Release expired locks
                for key in expired_keys:
                    self.locks[key].state = LockState.TIMEOUT
                    self.locks.pop(key, None)
                
                await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(5)
    
    async def _cleanup_loop(self) -> None:
        """Background loop for cleanup"""
        while self.enabled:
            try:
                # Cleanup old change logs
                cutoff = datetime.utcnow() - timedelta(hours=24)
                self.change_log = [
                    log for log in self.change_log
                    if log.timestamp > cutoff
                ]
                
                # Cleanup old proposals
                self.proposals = {
                    pid: p for pid, p in self.proposals.items()
                    if p.state in ['pending', 'approved']
                }
                
                await asyncio.sleep(3600)
            except Exception:
                await asyncio.sleep(3600)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum of current state"""
        import hashlib
        state_str = str(sorted(self.state.items()))
        return hashlib.md5(state_str.encode()).hexdigest()
    
    async def clear_all_state(self) -> bool:
        """Clear all state (use with caution)"""
        try:
            self.state.clear()
            self.change_log.clear()
            self.locks.clear()
            self.proposals.clear()
            self.snapshots.clear()
            
            await self._create_new_version()
            
            return True
        except Exception:
            return False
    
    async def get_state_size(self) -> int:
        """Get approximate size of state in bytes"""
        return len(str(self.state))
    
    async def validate_state_consistency(self) -> bool:
        """Validate state consistency"""
        try:
            current_checksum = self._calculate_checksum()
            current_version = await self.get_current_version()
            
            return current_checksum == current_version.checksum
        except Exception:
            return False
