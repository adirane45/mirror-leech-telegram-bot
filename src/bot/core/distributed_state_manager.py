"""
Distributed State Manager for cluster-wide state consistency

Refactored module structure:
- distributed_state_models.py: Enums, data classes, abstract base classes
- distributed_state_locks.py: Lock management implementation
- distributed_state_manager.py: Core manager implementation (this file)

Implements:
- State versioning with changelog
- Consensus-based updates
- Distributed locking (delegated to DistributedLockManager)
- State reconciliation
- Snapshot/restore mechanism
"""

import asyncio
import uuid
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Set, Optional, Any

# Import refactored components from models module
from .distributed_state_models import (
    StateUpdateStrategy,
    LockType,
    LockState,
    StateReconciliationReason,
    StateVersion,
    StateSnapshot,
    StateChangeLog,
    LockInfo,
    ConsensusProposal,
    StateReconciliationRequest,
    DistributedStateMetrics,
    DistributedStateProvider,
    StateChangeListener,
)

# Import lock manager module
from .distributed_state_locks import DistributedLockManager

# Import consensus manager module
from .distributed_state_consensus import DistributedConsensusManager


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
        self.peers: Set[str] = set()
        self.metrics = DistributedStateMetrics()
        self.listeners: List[StateChangeListener] = []
        self.current_version = 1
        self.update_strategy = StateUpdateStrategy.EVENTUAL
        self.consensus_threshold = 0.5
        self.reconciliation_interval = 60
        self.snapshot_retention_count = 10
        
        # Manager instances
        self.lock_manager: Optional[DistributedLockManager] = None
        self.consensus_manager: Optional[DistributedConsensusManager] = None
        
        # Background tasks
        self._reconciliation_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    @property
    def locks(self) -> Dict[str, LockInfo]:
        """Get locks dict from lock manager (backward compatibility)"""
        if self.lock_manager:
            return self.lock_manager.locks
        return {}
    
    @property
    def proposals(self) -> Dict[str, ConsensusProposal]:
        """Get proposals dict from consensus manager (backward compatibility)"""
        if self.consensus_manager:
            return self.consensus_manager.proposals
        return {}
    
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
            
            # Initialize and start lock manager
            self.lock_manager = DistributedLockManager(
                node_id=self.node_id,
                lock_timeout_seconds=30
            )
            self.lock_manager.add_listener(self)
            await self.lock_manager.start()
            
            # Initialize and start consensus manager
            self.consensus_manager = DistributedConsensusManager(
                node_id=self.node_id,
                consensus_threshold=self.consensus_threshold
            )
            self.consensus_manager.add_listener(self)
            # Register existing peers
            for peer in self.peers:
                self.consensus_manager.register_peer(peer)
            await self.consensus_manager.start()
            
            # Start background tasks
            self._reconciliation_task = asyncio.create_task(self._reconciliation_loop())
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
            
            # Stop managers
            if self.lock_manager:
                await self.lock_manager.stop()
            if self.consensus_manager:
                await self.consensus_manager.stop()
            
            # Cancel background tasks
            if self._reconciliation_task:
                self._reconciliation_task.cancel()
            if self._cleanup_task:
                self._cleanup_task.cancel()
            
            await asyncio.sleep(0.1)
            
            return True
        except Exception:
            return False
    
    async def clear_locks(self) -> None:
        """Clear all locks (for testing/cleanup)"""
        if self.lock_manager:
            await self.lock_manager.clear_locks()
    
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
        """Acquire distributed lock on key (delegated to DistributedLockManager)"""
        if not self.enabled or not self.lock_manager:
            return False
        
        result = await self.lock_manager.acquire_lock(key, lock_type)
        
        # Copy metrics from lock manager
        if self.lock_manager:
            lock_metrics = self.lock_manager.get_metrics()
            self.metrics.lock_acquisitions = lock_metrics['lock_acquisitions']
            self.metrics.lock_contentions = lock_metrics['lock_contentions']
        
        return result
    
    async def release_lock(self, key: str) -> bool:
        """Release distributed lock on key (delegated to DistributedLockManager)"""
        if not self.enabled or not self.lock_manager:
            return False
        
        return await self.lock_manager.release_lock(key)
    
    async def get_lock_info(self, key: str) -> Optional[LockInfo]:
        """Get information about lock on key (delegated to DistributedLockManager)"""
        if not self.enabled or not self.lock_manager:
            return None
        
        return await self.lock_manager.get_lock_info(key)
    
    # ========================================================================
    # CONSENSUS-BASED UPDATES
    # ========================================================================
    
    async def _update_with_consensus(
        self,
        key: str,
        value: Any,
        old_value: Any
    ) -> bool:
        """Apply state update using consensus (delegated to DistributedConsensusManager)"""
        if not self.enabled or not self.consensus_manager:
            return False
        
        try:
            # Create proposal
            proposal = await self.consensus_manager.create_proposal(key, value, old_value)
            if not proposal:
                return False
            
            # Check if consensus reached (for single node or auto-approval)
            if await self.consensus_manager.check_consensus(proposal):
                proposal.state = "approved"
                
                # Apply the update
                success = await self._apply_state_update(key, value, old_value)
                
                if success:
                    await self.consensus_manager.mark_proposal_applied(proposal.proposal_id)
                    # Copy metrics from consensus manager
                    if self.consensus_manager:
                        consensus_metrics = self.consensus_manager.get_metrics()
                        self.metrics.consensual_updates = consensus_metrics['consensual_updates']
                
                return success
            
            return False
        except Exception:
            return False
    
    async def vote_on_proposal(
        self,
        proposal_id: str,
        vote_for: bool,
        from_node: str
    ) -> bool:
        """Record vote on a proposal (delegated to DistributedConsensusManager)"""
        if not self.enabled or not self.consensus_manager:
            return False
        
        return await self.consensus_manager.vote_on_proposal(proposal_id, vote_for, from_node)
    
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
            # Sync with consensus manager
            if self.consensus_manager:
                self.consensus_manager.register_peer(peer_id)
            return True
        except Exception:
            return False
    
    async def unregister_peer(self, peer_id: str) -> bool:
        """Unregister peer node"""
        try:
            self.peers.discard(peer_id)
            # Sync with consensus manager
            if self.consensus_manager:
                self.consensus_manager.unregister_peer(peer_id)
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
    
    
    async def _cleanup_loop(self) -> None:
        """Background loop for cleanup"""
        while self.enabled:
            try:
                # Cleanup old change logs
                cutoff = datetime.now(UTC) - timedelta(hours=24)
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
