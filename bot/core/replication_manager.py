"""
Replication Manager for distributed state synchronization

Implements multi-master replication with:
- Change tracking and incremental sync
- Conflict detection and resolution
- Replication lag monitoring
- Vector clock-based ordering
- State reconciliation
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

class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving replication conflicts"""
    VECTOR_CLOCK = "vector_clock"  # Last write based on vector clocks
    TIMESTAMP = "timestamp"         # Last write based on timestamps
    CLIENT_WINS = "client_wins"     # Client's version always wins
    SERVER_WINS = "server_wins"     # Server's version always wins
    MERGE = "merge"                # Custom merge function
    ABORT = "abort"                # Abort on conflict


class ReplicationState(str, Enum):
    """State of replication for a node"""
    PENDING = "pending"             # Waiting to start replication
    SYNCING = "syncing"            # In-progress initial sync
    IN_SYNC = "in_sync"            # Fully synchronized
    OUT_OF_SYNC = "out_of_sync"    # Behind on updates
    FAILED = "failed"              # Replication failed
    RECOVERING = "recovering"      # Attempting recovery


class ReplicationLag(str, Enum):
    """Severity levels for replication lag"""
    MINIMAL = "minimal"            # <100ms
    LOW = "low"                    # 100ms-1s
    MEDIUM = "medium"              # 1s-5s
    HIGH = "high"                  # 5s-30s
    CRITICAL = "critical"          # >30s


@dataclass
class VectorClock:
    """Vector clock for causality tracking"""
    node_id: str
    clocks: Dict[str, int] = field(default_factory=dict)
    
    def increment(self) -> None:
        """Increment clock for this node"""
        self.clocks[self.node_id] = self.clocks.get(self.node_id, 0) + 1
    
    def merge(self, other: 'VectorClock') -> None:
        """Merge with another vector clock"""
        for node_id, clock in other.clocks.items():
            self.clocks[node_id] = max(self.clocks.get(node_id, 0), clock)
    
    def is_after(self, other: 'VectorClock') -> bool:
        """Check if this clock is after another"""
        is_greater = False
        for node_id in set(self.clocks.keys()) | set(other.clocks.keys()):
            self_val = self.clocks.get(node_id, 0)
            other_val = other.clocks.get(node_id, 0)
            if self_val < other_val:
                return False
            if self_val > other_val:
                is_greater = True
        return is_greater
    
    def concurrent_with(self, other: 'VectorClock') -> bool:
        """Check if clocks are concurrent (incomparable)"""
        self_greater = False
        other_greater = False
        
        for node_id in set(self.clocks.keys()) | set(other.clocks.keys()):
            self_val = self.clocks.get(node_id, 0)
            other_val = other.clocks.get(node_id, 0)
            if self_val > other_val:
                self_greater = True
            if other_val > self_val:
                other_greater = True
        
        return self_greater and other_greater


@dataclass
class ReplicationLog:
    """Entry in replication log"""
    log_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_node: str = ""
    operation_type: str = ""  # CREATE, UPDATE, DELETE
    key: str = ""
    value: Any = None
    old_value: Any = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    vector_clock: VectorClock = field(default_factory=lambda: VectorClock(""))
    sequence_number: int = 0
    applied: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'log_id': self.log_id,
            'source_node': self.source_node,
            'operation_type': self.operation_type,
            'key': self.key,
            'value': self.value,
            'old_value': self.old_value,
            'timestamp': self.timestamp.isoformat(),
            'vector_clock': self.vector_clock.clocks,
            'sequence_number': self.sequence_number,
            'applied': self.applied
        }


@dataclass
class ConflictEvent:
    """When a replication conflict is detected"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    local_value: Any = None
    remote_value: Any = None
    local_timestamp: datetime = field(default_factory=datetime.utcnow)
    remote_timestamp: datetime = field(default_factory=datetime.utcnow)
    remote_node: str = ""
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.VECTOR_CLOCK
    resolved: bool = False
    resolved_value: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'event_id': self.event_id,
            'key': self.key,
            'local_value': self.local_value,
            'remote_value': self.remote_value,
            'local_timestamp': self.local_timestamp.isoformat(),
            'remote_timestamp': self.remote_timestamp.isoformat(),
            'remote_node': self.remote_node,
            'detected_at': self.detected_at.isoformat(),
            'resolution_strategy': self.resolution_strategy.value,
            'resolved': self.resolved,
            'resolved_value': self.resolved_value
        }


@dataclass
class SyncCheckpoint:
    """Track progress of incremental sync"""
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str = ""
    last_synced_sequence: int = 0
    synced_keys: int = 0
    pending_keys: int = 0
    last_checkpoint_time: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'checkpoint_id': self.checkpoint_id,
            'node_id': self.node_id,
            'last_synced_sequence': self.last_synced_sequence,
            'synced_keys': self.synced_keys,
            'pending_keys': self.pending_keys,
            'last_checkpoint_time': self.last_checkpoint_time.isoformat()
        }


@dataclass
class ReplicationMetrics:
    """Replication performance metrics"""
    total_changes: int = 0
    synced_changes: int = 0
    pending_changes: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    replication_lag_ms: int = 0
    avg_lag_ms: float = 0.0
    max_lag_ms: int = 0
    sync_throughput_ops_sec: float = 0.0
    nodes_in_sync: int = 0
    total_nodes: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'total_changes': self.total_changes,
            'synced_changes': self.synced_changes,
            'pending_changes': self.pending_changes,
            'conflicts_detected': self.conflicts_detected,
            'conflicts_resolved': self.conflicts_resolved,
            'replication_lag_ms': self.replication_lag_ms,
            'avg_lag_ms': round(self.avg_lag_ms, 2),
            'max_lag_ms': self.max_lag_ms,
            'sync_throughput_ops_sec': round(self.sync_throughput_ops_sec, 2),
            'nodes_in_sync': self.nodes_in_sync,
            'total_nodes': self.total_nodes,
            'last_updated': self.last_updated.isoformat()
        }


# ============================================================================
# ABSTRACT CLASSES
# ============================================================================

class ReplicationEventListener(ABC):
    """Abstract listener for replication events"""
    
    @abstractmethod
    async def on_change_published(self, log_entry: ReplicationLog) -> None:
        """Called when a change is published"""
        pass
    
    @abstractmethod
    async def on_change_received(self, log_entry: ReplicationLog, from_node: str) -> None:
        """Called when a change is received from remote node"""
        pass
    
    @abstractmethod
    async def on_conflict_detected(self, conflict: ConflictEvent) -> None:
        """Called when a conflict is detected"""
        pass
    
    @abstractmethod
    async def on_conflict_resolved(self, conflict: ConflictEvent) -> None:
        """Called when a conflict is resolved"""
        pass
    
    @abstractmethod
    async def on_sync_completed(self, node_id: str) -> None:
        """Called when sync with node is completed"""
        pass
    
    @abstractmethod
    async def on_lag_critical(self, node_id: str, lag_ms: int) -> None:
        """Called when replication lag becomes critical"""
        pass


# ============================================================================
# REPLICATION MANAGER
# ============================================================================

class ReplicationManager:
    """
    Multi-master replication manager for distributed state synchronization
    
    Singleton instance managing:
    - Change replication across cluster nodes
    - Conflict detection and resolution
    - Incremental sync with change tracking
    - Replication lag monitoring
    - Vector clock-based causality tracking
    """
    
    _instance: Optional['ReplicationManager'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.enabled = False
        self.node_id = ""
        self.peer_nodes: Dict[str, Dict[str, Any]] = {}
        self.replication_log: List[ReplicationLog] = []
        self.pending_replication: Dict[str, List[ReplicationLog]] = {}
        self.sync_checkpoints: Dict[str, SyncCheckpoint] = {}
        self.conflicts: Dict[str, ConflictEvent] = {}
        self.local_state: Dict[str, Any] = {}
        self.metrics = ReplicationMetrics()
        self.vector_clock = VectorClock("")
        self.listeners: List[ReplicationEventListener] = []
        self.conflict_resolver: Optional[Callable] = None
        self.resolution_strategy = ConflictResolutionStrategy.VECTOR_CLOCK
        self.batch_size = 100
        self.sync_interval = 5
        self.lag_check_interval = 2
        self.log_retention_hours = 24
        
        # Background tasks
        self._replication_task: Optional[asyncio.Task] = None
        self._lag_monitor_task: Optional[asyncio.Task] = None
        self._log_cleanup_task: Optional[asyncio.Task] = None
    
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
            
            # Start background tasks
            self._replication_task = asyncio.create_task(self._replication_loop())
            self._lag_monitor_task = asyncio.create_task(self._lag_monitor_loop())
            self._log_cleanup_task = asyncio.create_task(self._log_cleanup_loop())
            
            return True
        except Exception as e:
            self.enabled = False
            return False
    
    async def stop(self) -> bool:
        """Stop replication manager"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            
            # Cancel background tasks
            if self._replication_task:
                self._replication_task.cancel()
            if self._lag_monitor_task:
                self._lag_monitor_task.cancel()
            if self._log_cleanup_task:
                self._log_cleanup_task.cancel()
            
            # Wait for cancellation
            await asyncio.sleep(0.1)
            
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
                timestamp=datetime.utcnow(),
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
            self.metrics.total_changes += 1
            self.metrics.pending_changes += 1
            
            for node_id in self.peer_nodes:
                if node_id not in self.pending_replication:
                    self.pending_replication[node_id] = []
                self.pending_replication[node_id].append(log_entry)
            
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
            conflict = await self.detect_conflict(log_entry, from_node)
            
            if conflict:
                # Handle conflict
                resolved_conflict = await self.resolve_conflict(conflict)
                if resolved_conflict:
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
    # CONFLICT DETECTION AND RESOLUTION
    # ========================================================================
    
    async def detect_conflict(
        self,
        remote_log: ReplicationLog,
        from_node: str
    ) -> Optional[ConflictEvent]:
        """
        Detect if there's a conflict with a remote change
        
        Returns ConflictEvent if conflict detected, None otherwise
        """
        key = remote_log.key
        
        # Check if key was modified locally after remote change
        for local_log in self.replication_log:
            if (local_log.key == key and
                local_log.operation_type != "DELETE" and
                remote_log.operation_type != "DELETE"):
                
                # Check if vector clocks are concurrent
                if remote_log.vector_clock.concurrent_with(local_log.vector_clock):
                    # Conflict detected
                    local_value = self.local_state.get(key)
                    
                    conflict = ConflictEvent(
                        key=key,
                        local_value=local_value,
                        remote_value=remote_log.value,
                        local_timestamp=local_log.timestamp,
                        remote_timestamp=remote_log.timestamp,
                        remote_node=from_node,
                        resolution_strategy=self.resolution_strategy
                    )
                    
                    self.conflicts[conflict.event_id] = conflict
                    self.metrics.conflicts_detected += 1
                    
                    for listener in self.listeners:
                        await listener.on_conflict_detected(conflict)
                    
                    return conflict
        
        return None
    
    async def resolve_conflict(self, conflict: ConflictEvent) -> bool:
        """Resolve a detected conflict"""
        try:
            strategy = conflict.resolution_strategy
            
            if strategy == ConflictResolutionStrategy.TIMESTAMP:
                # Last write wins based on timestamp
                if conflict.remote_timestamp > conflict.local_timestamp:
                    conflict.resolved_value = conflict.remote_value
                else:
                    conflict.resolved_value = conflict.local_value
            
            elif strategy == ConflictResolutionStrategy.CLIENT_WINS:
                conflict.resolved_value = conflict.local_value
            
            elif strategy == ConflictResolutionStrategy.SERVER_WINS:
                conflict.resolved_value = conflict.remote_value
            
            elif strategy == ConflictResolutionStrategy.MERGE:
                # Use custom merge function if provided
                if self.conflict_resolver:
                    conflict.resolved_value = await self.conflict_resolver(
                        conflict.local_value,
                        conflict.remote_value
                    )
                else:
                    conflict.resolved_value = conflict.remote_value
            
            elif strategy == ConflictResolutionStrategy.VECTOR_CLOCK:
                conflict.resolved_value = conflict.remote_value
            
            else:
                return False
            
            conflict.resolved = True
            return True
        except Exception:
            return False
    
    # ========================================================================
    # SYNCHRONIZATION
    # ========================================================================
    
    async def sync_with_node(self, node_id: str) -> bool:
        """
        Perform full synchronization with a specific node
        
        Sends all pending changes in batches
        """
        if not self.enabled:
            return False
        
        try:
            if node_id not in self.pending_replication:
                self.pending_replication[node_id] = []
            
            pending = self.pending_replication[node_id]
            
            # Send in batches
            for i in range(0, len(pending), self.batch_size):
                batch = pending[i:i + self.batch_size]
                # In real implementation, send over network
                await asyncio.sleep(0.01)  # Simulate network latency
            
            # Update checkpoint
            checkpoint = SyncCheckpoint(
                node_id=node_id,
                last_synced_sequence=len(self.replication_log),
                synced_keys=len(self.local_state)
            )
            self.sync_checkpoints[node_id] = checkpoint
            
            # Clear pending
            self.pending_replication[node_id] = []
            
            for listener in self.listeners:
                await listener.on_sync_completed(node_id)
            
            return True
        except Exception:
            return False
    
    async def incremental_sync(self, node_id: str) -> bool:
        """
        Perform incremental sync - only send changes since last sync
        """
        if node_id not in self.sync_checkpoints:
            return await self.sync_with_node(node_id)
        
        checkpoint = self.sync_checkpoints[node_id]
        last_seq = checkpoint.last_synced_sequence
        
        # Get changes since last checkpoint
        new_changes = [
            log for log in self.replication_log
            if log.sequence_number > last_seq
        ]
        
        if not new_changes:
            return True
        
        # Send incremental changes
        for i in range(0, len(new_changes), self.batch_size):
            batch = new_changes[i:i + self.batch_size]
            await asyncio.sleep(0.01)
        
        # Update checkpoint
        checkpoint.last_synced_sequence = len(self.replication_log)
        checkpoint.synced_keys = len(self.local_state)
        
        return True
    
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
            'conflicts': len(self.conflicts),
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
            'lag_level': self._classify_lag(self.metrics.replication_lag_ms),
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
            self.pending_replication[node_id] = []
            return True
        except Exception:
            return False
    
    async def unregister_peer_node(self, node_id: str) -> bool:
        """Unregister a peer node"""
        try:
            self.peer_nodes.pop(node_id, None)
            self.pending_replication.pop(node_id, None)
            self.sync_checkpoints.pop(node_id, None)
            return True
        except Exception:
            return False
    
    async def get_conflict_history(self, limit: int = 100) -> List[ConflictEvent]:
        """Get recent conflicts"""
        return list(self.conflicts.values())[-limit:]
    
    async def add_listener(self, listener: ReplicationEventListener) -> bool:
        """Register a replication event listener"""
        try:
            self.listeners.append(listener)
            return True
        except Exception:
            return False
    
    async def remove_listener(self, listener: ReplicationEventListener) -> bool:
        """Unregister a replication event listener"""
        try:
            self.listeners.remove(listener)
            return True
        except Exception:
            return False
    
    async def clear_replication_log(self) -> int:
        """Clear old replication log entries"""
        cutoff = datetime.utcnow() - timedelta(hours=self.log_retention_hours)
        initial_count = len(self.replication_log)
        
        self.replication_log = [
            log for log in self.replication_log
            if log.timestamp > cutoff
        ]
        
        return initial_count - len(self.replication_log)
    
    # ========================================================================
    # BACKGROUND LOOPS
    # ========================================================================
    
    async def _replication_loop(self) -> None:
        """Background loop for batching and sending replications"""
        while self.enabled:
            try:
                # Send pending changes to each peer in batches
                for node_id, pending_changes in self.pending_replication.items():
                    if pending_changes:
                        # In real implementation, send via network
                        batch = pending_changes[:self.batch_size]
                        # Simulate sending
                        await asyncio.sleep(0.01)
                
                await asyncio.sleep(self.sync_interval)
            except Exception:
                await asyncio.sleep(self.sync_interval)
    
    async def _lag_monitor_loop(self) -> None:
        """Background loop for monitoring replication lag"""
        while self.enabled:
            try:
                # Calculate lag for each peer
                total_lag = 0
                in_sync_count = 0
                
                for node_id, pending in self.pending_replication.items():
                    lag = len(pending) * 10  # Estimate: 10ms per pending operation
                    total_lag += lag
                    
                    if lag == 0:
                        in_sync_count += 1
                    
                    # Check for critical lag
                    if lag > 30000:  # >30s
                        for listener in self.listeners:
                            await listener.on_lag_critical(node_id, lag)
                
                # Update metrics
                self.metrics.replication_lag_ms = total_lag // max(len(self.peer_nodes), 1)
                self.metrics.nodes_in_sync = in_sync_count
                self.metrics.total_nodes = len(self.peer_nodes)
                
                # Calculate average lag
                if self.peer_nodes:
                    self.metrics.avg_lag_ms = total_lag / len(self.peer_nodes)
                
                await asyncio.sleep(self.lag_check_interval)
            except Exception:
                await asyncio.sleep(self.lag_check_interval)
    
    async def _log_cleanup_loop(self) -> None:
        """Background loop for cleaning up old log entries"""
        while self.enabled:
            try:
                # Cleanup every hour
                await asyncio.sleep(3600)
                await self.clear_replication_log()
            except Exception:
                await asyncio.sleep(3600)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def _classify_lag(self, lag_ms: int) -> str:
        """Classify lag level"""
        if lag_ms < 100:
            return ReplicationLag.MINIMAL.value
        elif lag_ms < 1000:
            return ReplicationLag.LOW.value
        elif lag_ms < 5000:
            return ReplicationLag.MEDIUM.value
        elif lag_ms < 30000:
            return ReplicationLag.HIGH.value
        else:
            return ReplicationLag.CRITICAL.value
    
    async def get_pending_changes_count(self, node_id: Optional[str] = None) -> int:
        """Get count of pending changes"""
        if node_id:
            return len(self.pending_replication.get(node_id, []))
        return sum(len(changes) for changes in self.pending_replication.values())
    
    async def get_log_size(self) -> int:
        """Get replication log size"""
        return len(self.replication_log)
    
    async def force_sync_all_nodes(self) -> bool:
        """Force synchronization with all peer nodes"""
        try:
            for node_id in self.peer_nodes:
                await self.sync_with_node(node_id)
            return True
        except Exception:
            return False
