"""
Cluster Manager Models - Data structures for distributed cluster coordination

Contains:
- Enums for node, Raft, and cluster states
- Data classes for nodes, messages, and cluster info
- Abstract listener interface for state changes
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from abc import ABC, abstractmethod


# ============================================================================
# ENUMS
# ============================================================================

class NodeStatus(str, Enum):
    """Node health status in the cluster"""
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'
    DISCONNECTED = 'disconnected'
    UNKNOWN = 'unknown'


class RaftState(str, Enum):
    """Raft consensus state"""
    FOLLOWER = 'follower'
    CANDIDATE = 'candidate'
    LEADER = 'leader'


class ClusterState(str, Enum):
    """Overall cluster health state"""
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    SPLIT_BRAIN = 'split_brain'
    FAILED = 'failed'
    INITIALIZING = 'initializing'


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Node:
    """Cluster node representation"""
    node_id: str
    hostname: str
    port: int
    status: NodeStatus = NodeStatus.UNKNOWN
    last_heartbeat: Optional[datetime] = None
    raft_state: RaftState = RaftState.FOLLOWER
    term: int = 0
    voted_for: Optional[str] = None
    is_leader: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'node_id': self.node_id,
            'hostname': self.hostname,
            'port': self.port,
            'status': self.status.value,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'raft_state': self.raft_state.value,
            'term': self.term,
            'voted_for': self.voted_for,
            'is_leader': self.is_leader
        }


@dataclass
class GossipMessage:
    """Gossip protocol message for node discovery"""
    sender_id: str
    sender_hostname: str
    sender_port: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    known_nodes: List[Dict[str, Any]] = field(default_factory=list)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'sender_id': self.sender_id,
            'sender_hostname': self.sender_hostname,
            'sender_port': self.sender_port,
            'timestamp': self.timestamp.isoformat(),
            'known_nodes': self.known_nodes,
            'message_id': self.message_id
        }


@dataclass
class HeartbeatMessage:
    """Raft heartbeat message"""
    leader_id: str
    term: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'leader_id': self.leader_id,
            'term': self.term,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id
        }


@dataclass
class VoteRequest:
    """Raft vote request message"""
    candidate_id: str
    term: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'candidate_id': self.candidate_id,
            'term': self.term,
            'timestamp': self.timestamp.isoformat(),
            'message_id': self.message_id
        }


@dataclass
class ClusterInfo:
    """Complete cluster information snapshot"""
    cluster_id: str
    state: ClusterState
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    leader_id: Optional[str] = None
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    term: int = 0
    healthy_nodes: int = 0
    degraded_nodes: int = 0
    unhealthy_nodes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'cluster_id': self.cluster_id,
            'state': self.state.value,
            'timestamp': self.timestamp.isoformat(),
            'leader_id': self.leader_id,
            'nodes': self.nodes,
            'term': self.term,
            'healthy_nodes': self.healthy_nodes,
            'degraded_nodes': self.degraded_nodes,
            'unhealthy_nodes': self.unhealthy_nodes,
            'total_nodes': len(self.nodes)
        }


# ============================================================================
# STATE CHANGE LISTENERS
# ============================================================================

class StateChangeListener(ABC):
    """Abstract listener for cluster state changes"""
    
    @abstractmethod
    async def on_leader_elected(self, leader_id: str, term: int) -> None:
        """Called when leader elected"""
        pass
    
    @abstractmethod
    async def on_node_joined(self, node_id: str, node: Node) -> None:
        """Called when node joins cluster"""
        pass
    
    @abstractmethod
    async def on_node_left(self, node_id: str) -> None:
        """Called when node leaves cluster"""
        pass
    
    @abstractmethod
    async def on_cluster_state_changed(self, old_state: ClusterState, new_state: ClusterState) -> None:
        """Called when cluster state changes"""
        pass
    
    @abstractmethod
    async def on_split_brain_detected(self, partition_a: Set[str], partition_b: Set[str]) -> None:
        """Called when split-brain detected"""
        pass
