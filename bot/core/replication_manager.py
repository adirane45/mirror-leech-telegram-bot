"""
Replication Manager - Multi-master replication (REFACTORED)

Implements multi-master replication with:
- Change tracking and incremental sync
- Conflict detection and resolution
- Replication lag monitoring
- Vector clock-based ordering
- State reconciliation
"""

import asyncio
import uuid
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, Callable

from .replication_models import (
    ConflictResolutionStrategy,
    ReplicationState,
    ReplicationLog,
    ConflictEvent,
    VectorClock,
    SyncCheckpoint,
    ReplicationMetrics,
    ReplicationEventListener,
)

from .replication_conflict_resolver import ReplicationConflictResolver
from .replication_sync_engine import ReplicationSyncEngine


class ReplicationManager:
    """
    Multi-master replication manager (main orchestrator)
    
    Responsibilities:
    - Coordinate change tracking and publishing
    - Integrate conflict resolver and sync engine
    - Manage local state and vector clocks
    - Expose unified public API
    """
    
    _instance: Optional['ReplicationManager'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.enabled = False
        self.node_id = ""
        self.peer_nodes: Dict[str, Dict[str, Any]] = {}
        self.replication_log: List[ReplicationLog] = []
        self.sync_checkpoints: Dict[str, SyncCheckpoint] = {}
        self.local_state: Dict[str, Any] = {}
        self.metrics = ReplicationMetrics()
        self.vector_clock = VectorClock("")
        self.listeners: List[ReplicationEventListener] = []
        
        # Initialize specialized components
        self.conflict_resolver = ReplicationConflictResolver(
            replication_log=self.replication_log,
            local_state=self.local_state,
            metrics=self.metrics,
            listeners=self.listeners
        )
        
        self.sync_engine = ReplicationSyncEngine(
            replication_log=self.replication_log,
            local_state=self.local_state,
            peer_nodes=self.peer_nodes,
            metrics=self.metrics,
            listeners=self.listeners
        )
    
    @classmethod
    def get_instance(cls) -> 'ReplicationManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def start(self, node_id: str = "") -> bool:
        """Start replication manager"""
        if self.enabled:
            return True
        
        try:
            self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
            self.vector_clock.node_id = self.node_id
            self.enabled = True
            
            # Start sync engine
            await self.sync_engine.start()
            
            return True
        except Exception:
            self.enabled = False
            return False
    
    async def stop(self) -> bool:
        """Stop replication manager"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            await self.sync_engine.stop()
            return True
        except Exception:
            return False
    
    async def is_enabled(self) -> bool:
        """Check if replication is enabled"""
        return self.enabled
    
    # ========================================================================
    # CHANGE TRACKING AND PUBLISHING
    # ========================================================================
    
    async def publish_change(
        self,
        operation_type: str,
        key: str,
        value: Any,
        old_value: Optional[Any] = None
    ) -> bool:
        """
        Publish a local change to replicate to other nodes
        
        Args:
            operation_type: CREATE, UPDATE, DELETE
            key: Key for the changed data
            value: New value
            old_value: Old value (for UPDATE/DELETE)
        
        Returns:
            True if change was published
        """
        if not self.enabled:
            return False
        
        try:
            # Increment local clock
            self.vector_clock.increment()
            
            # Create log entry
            log_entry = ReplicationLog(
                source_node=self.node_id,
                operation_type=operation_type,
                key=key,
                value=value,
                old_value=old_value,
                timestamp=datetime.now(UTC),
                vector_clock=VectorClock(self.node_id, dict(self.vector_clock.clocks)),
                sequence_number=len(self.replication_log)
            )
            
            # Add to local log
            self.replication_log.append(log_entry)
            
            # Update local state
            if operation_type == "DELETE":
                self.local_state.pop(key, None)
            else:
                self.local_state[key] = value
            
            # Queue for replication to all peers
            await self.sync_engine.queue_change_for_replication(log_entry)
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_change_published(log_entry)
            
            return True
        except Exception:
            return False
    
    async def handle_remote_change(
        self,
        log_entry: ReplicationLog,
        from_node: str
    ) -> bool:
        """
        Handle a change received from a remote node
        
        Checks for conflicts and applies if no conflict or after resolution
        """
        if not self.enabled:
            return False
        
        try:
            # Update vector clock
            self.vector_clock.merge(log_entry.vector_clock)
            
            # Check for conflicts
            conflict = await self.conflict_resolver.detect_conflict(log_entry, from_node)
            
            if conflict:
                # Resolve conflict
                resolved = await self.conflict_resolver.resolve_conflict(conflict)
                if resolved:
                    self.metrics.conflicts_resolved += 1
                    for listener in self.listeners:
                        await listener.on_conflict_resolved(conflict)
                    # Apply resolved value
                    if log_entry.operation_type != "DELETE":
                        self.local_state[log_entry.key] = conflict.resolved_value
                return True
            
            # Apply change
            log_entry.applied = True
            self.replication_log.append(log_entry)
            
            if log_entry.operation_type == "DELETE":
                self.local_state.pop(log_entry.key, None)
            else:
                self.local_state[log_entry.key] = log_entry.value
            
            self.metrics.synced_changes += 1
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_change_received(log_entry, from_node)
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # SYNCHRONIZATION
    # ========================================================================
    
    async def sync_with_node(self, node_id: str) -> bool:
        """Perform full synchronization with a specific node"""
        return await self.sync_engine.sync_with_node(node_id)
    
    async def incremental_sync(self, node_id: str) -> bool:
        """Perform incremental sync with a specific node"""
        return await self.sync_engine.incremental_sync(node_id)
    
    async def force_sync_all_nodes(self) -> bool:
        """Force synchronization with all peer nodes"""
        return await self.sync_engine.force_sync_all_nodes()
    
    # ========================================================================
    # MONITORING AND MANAGEMENT
    # ========================================================================
    
    async def get_replication_status(self) -> Dict[str, Any]:
        """Get overall replication status"""
        return {
            'node_id': self.node_id,
            'enabled': self.enabled,
            'total_changes': self.metrics.total_changes,
            'pending_changes': self.metrics.pending_changes,
            'conflicts': len(self.conflict_resolver.conflicts),
            'in_sync_nodes': self.metrics.nodes_in_sync,
            'lag_ms': self.metrics.replication_lag_ms,
            'peers': list(self.peer_nodes.keys())
        }
    
    async def get_replication_lag(self) -> Dict[str, Any]:
        """Get replication lag metrics"""
        return {
            'current_lag_ms': self.metrics.replication_lag_ms,
            'average_lag_ms': round(self.metrics.avg_lag_ms, 2),
            'max_lag_ms': self.metrics.max_lag_ms,
            'lag_level': self.sync_engine._classify_lag(self.metrics.replication_lag_ms),
            'last_updated': self.metrics.last_updated.isoformat()
        }
    
    async def get_metrics(self) -> ReplicationMetrics:
        """Get replication metrics"""
        return self.metrics
    
    async def register_peer_node(self, node_id: str, address: str) -> bool:
        """Register a peer node for replication"""
        try:
            self.peer_nodes[node_id] = {
                'address': address,
                'state': ReplicationState.PENDING,
                'last_sync': None
            }
            self.sync_engine.pending_replication[node_id] = []
            return True
        except Exception:
            return False
    
    async def unregister_peer_node(self, node_id: str) -> bool:
        """Unregister a peer node"""
        try:
            self.peer_nodes.pop(node_id, None)
            self.sync_engine.pending_replication.pop(node_id, None)
            self.sync_engine.sync_checkpoints.pop(node_id, None)
            return True
        except Exception:
            return False
    
    async def get_conflict_history(self, limit: int = 100) -> List[ConflictEvent]:
        """Get recent conflicts"""
        return await self.conflict_resolver.get_conflict_history(limit)
    
    async def add_listener(self, listener: ReplicationEventListener) -> bool:
        """Register a replication event listener"""
        try:
            if listener not in self.listeners:
                self.listeners.append(listener)
            return True
        except Exception:
            return False
    
    async def remove_listener(self, listener: ReplicationEventListener) -> bool:
        """Unregister a replication event listener"""
        try:
            if listener in self.listeners:
                self.listeners.remove(listener)
            return True
        except Exception:
            return False
    
    async def clear_replication_log(self) -> int:
        """Clear old replication log entries"""
        return await self.sync_engine.clear_replication_log()
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    def set_custom_conflict_resolver(self, resolver: Callable) -> None:
        """Set custom conflict resolver function"""
        self.conflict_resolver.set_custom_resolver(resolver)
    
    def set_conflict_resolution_strategy(self, strategy: ConflictResolutionStrategy) -> None:
        """Set the conflict resolution strategy"""
        self.conflict_resolver.set_resolution_strategy(strategy)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    async def get_pending_changes_count(self, node_id: Optional[str] = None) -> int:
        """Get count of pending changes"""
        return await self.sync_engine.get_pending_changes_count(node_id)
    
    async def get_log_size(self) -> int:
        """Get replication log size"""
        return len(self.replication_log)
