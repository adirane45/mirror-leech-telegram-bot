"""
Models and data structures for distributed replication

Includes:
- Replication state enumerations
- Vector clock for causality tracking
- Replication log entries and conflict events
- Synchronization checkpoints
- Performance metrics
- Event listener interface
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict


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
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
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
    local_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    remote_timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    remote_node: str = ""
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
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
    last_checkpoint_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    
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
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    
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
