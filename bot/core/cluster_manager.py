"""
Cluster Manager - Distributed node coordination and leader election

Enables:
- Node discovery via gossip protocol
- Leader election using Raft consensus algorithm
- Split-brain detection and resolution
- Health-aware cluster management
- Automatic failover and recovery

Integrates with HealthMonitor for component-level monitoring
"""

import asyncio
import hashlib
import json
import random
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Set, Any
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
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
    timestamp: datetime = field(default_factory=datetime.utcnow)
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


# ============================================================================
# CLUSTER MANAGER
# ============================================================================

class ClusterManager:
    """
    Distributed cluster manager with Raft consensus and gossip protocol
    
    Responsibilities:
    - Node discovery and membership management
    - Leader election via Raft algorithm
    - Heartbeat-based health monitoring
    - Split-brain detection and resolution
    - Cluster state aggregation
    """
    
    _instance: Optional['ClusterManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize cluster manager"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        
        # Cluster configuration
        self.cluster_id = str(uuid.uuid4())
        self.node_id = str(uuid.uuid4())
        self.hostname = 'localhost'
        self.port = 8000
        
        # Node registry
        self.nodes: Dict[str, Node] = {}
        self.local_node: Optional[Node] = None
        
        # Raft state
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.leader_id: Optional[str] = None
        self.raft_state = RaftState.FOLLOWER
        
        # Cluster state
        self.cluster_state = ClusterState.INITIALIZING
        self.nodes_seen_heartbeat: Set[str] = set()
        
        # Timers and configuration
        self.heartbeat_timeout = timedelta(seconds=5)
        self.election_timeout_min = timedelta(seconds=5)
        self.election_timeout_max = timedelta(seconds=10)
        self.gossip_interval = timedelta(seconds=2)
        
        # Last activity tracking
        self.last_heartbeat: Optional[datetime] = None
        self.last_leader_check: Optional[datetime] = None
        self.election_timeout_deadline: Optional[datetime] = None
        
        # Background tasks
        self.enabled = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._gossip_task: Optional[asyncio.Task] = None
        self._election_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        # State change listeners
        self.listeners: List[StateChangeListener] = []
        
        # Split-brain tracking
        self.potential_split_brain = False
        self.split_brain_detection_threshold = 0.5  # Majority threshold
    
    @classmethod
    def get_instance(cls) -> 'ClusterManager':
        """Get singleton instance"""
        return cls()
    
    # ========================================================================
    # INITIALIZATION AND LIFECYCLE
    # ========================================================================
    
    async def initialize(self, node_id: str, hostname: str, port: int) -> bool:
        """Initialize cluster manager with node information"""
        try:
            self.node_id = node_id
            self.hostname = hostname
            self.port = port
            
            # Create local node
            self.local_node = Node(
                node_id=node_id,
                hostname=hostname,
                port=port,
                status=NodeStatus.HEALTHY,
                raft_state=RaftState.FOLLOWER
            )
            self.nodes[node_id] = self.local_node
            
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize cluster manager: {e}")
    
    async def start(self) -> bool:
        """Start cluster management"""
        if self.enabled:
            return True
        
        try:
            self.enabled = True
            
            # Start gossip protocol
            self._gossip_task = asyncio.create_task(self._gossip_loop())
            
            # Start election handler
            self._election_task = asyncio.create_task(self._election_loop())
            
            # Start heartbeat handler
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Start health check
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            # Reset election timeout
            self.election_timeout_deadline = datetime.utcnow() + self._random_election_timeout()
            
            return True
        except Exception as e:
            self.enabled = False
            raise RuntimeError(f"Failed to start cluster manager: {e}")
    
    async def stop(self) -> bool:
        """Stop cluster management"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            
            # Cancel all tasks
            for task in [self._gossip_task, self._election_task, 
                        self._heartbeat_task, self._health_check_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to stop cluster manager: {e}")
    
    # ========================================================================
    # NODE MANAGEMENT
    # ========================================================================
    
    async def register_node(self, node_id: str, hostname: str, port: int) -> bool:
        """Register a node in the cluster"""
        try:
            if node_id not in self.nodes:
                node = Node(node_id=node_id, hostname=hostname, port=port)
                self.nodes[node_id] = node
                
                # Notify listeners
                for listener in self.listeners:
                    await listener.on_node_joined(node_id, node)
            
            return True
        except Exception as e:
            return False
    
    async def unregister_node(self, node_id: str) -> bool:
        """Unregister a node from the cluster"""
        try:
            if node_id in self.nodes:
                del self.nodes[node_id]
                
                # Notify listeners
                for listener in self.listeners:
                    await listener.on_node_left(node_id)
                
                # If leader left, trigger election
                if node_id == self.leader_id:
                    await self._start_election()
            
            return True
        except Exception as e:
            return False
    
    async def get_node(self, node_id: str) -> Optional[Node]:
        """Get node by ID"""
        return self.nodes.get(node_id)
    
    async def get_all_nodes(self) -> Dict[str, Node]:
        """Get all nodes in cluster"""
        return dict(self.nodes)
    
    # ========================================================================
    # GOSSIP PROTOCOL
    # ========================================================================
    
    async def handle_gossip_message(self, message: GossipMessage) -> None:
        """Handle incoming gossip message"""
        try:
            # Register sender if new
            sender_node = self.nodes.get(message.sender_id)
            if not sender_node:
                await self.register_node(message.sender_id, message.sender_hostname, message.sender_port)
                sender_node = self.nodes[message.sender_id]
            
            # Update sender status
            if sender_node:
                sender_node.last_heartbeat = message.timestamp
                sender_node.status = NodeStatus.HEALTHY
            
            # Process known nodes in message
            for node_data in message.known_nodes:
                node_id = node_data.get('node_id')
                if node_id and node_id not in self.nodes:
                    await self.register_node(
                        node_id,
                        node_data.get('hostname', 'unknown'),
                        node_data.get('port', 0)
                    )
        
        except Exception as e:
            pass
    
    async def _gossip_loop(self) -> None:
        """Background gossip protocol loop"""
        while self.enabled:
            try:
                # Create gossip message with known nodes
                known_nodes = [node.to_dict() for node in self.nodes.values()]
                message = GossipMessage(
                    sender_id=self.node_id,
                    sender_hostname=self.hostname,
                    sender_port=self.port,
                    known_nodes=known_nodes
                )
                
                # Simulate sending to random peer
                peer_ids = [nid for nid in self.nodes.keys() if nid != self.node_id]
                if peer_ids:
                    peer_id = random.choice(peer_ids)
                    # In real impl, would send via network
                
                await asyncio.sleep(self.gossip_interval.total_seconds())
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self.gossip_interval.total_seconds())
    
    # ========================================================================
    # RAFT LEADER ELECTION
    # ========================================================================
    
    async def handle_heartbeat(self, message: HeartbeatMessage) -> bool:
        """Handle leader heartbeat"""
        try:
            # If we see higher term, update
            if message.term > self.current_term:
                self.current_term = message.term
                self.voted_for = None
                await self._become_follower()
            
            # Update leader
            if message.term >= self.current_term:
                self.leader_id = message.leader_id
                self.last_heartbeat = message.timestamp
                self.election_timeout_deadline = datetime.utcnow() + self._random_election_timeout()
                
                # Update leader node
                if message.leader_id in self.nodes:
                    self.nodes[message.leader_id].is_leader = True
                    self.nodes[message.leader_id].status = NodeStatus.HEALTHY
                
                await self._update_cluster_state()
                return True
            
            return False
        except Exception:
            return False
    
    async def handle_vote_request(self, request: VoteRequest) -> bool:
        """Handle vote request from candidate"""
        try:
            # If higher term, convert to follower
            if request.term > self.current_term:
                self.current_term = request.term
                self.voted_for = None
                await self._become_follower()
            
            # Vote if we haven't voted and term matches/lower
            if request.term >= self.current_term and self.voted_for is None:
                self.voted_for = request.candidate_id
                self.current_term = request.term
                return True
            
            return False
        except Exception:
            return False
    
    async def _start_election(self) -> None:
        """Start leader election"""
        try:
            self.current_term += 1
            await self._become_candidate()
            
            # Request votes from all nodes
            vote_count = 1  # Vote for self
            for node_id in self.nodes.keys():
                if node_id != self.node_id:
                    # In real impl, would send via network
                    pass
            
            # Simple majority check (would be more complex in real impl)
            required_votes = len(self.nodes) // 2 + 1
            
            if vote_count >= required_votes:
                await self._become_leader()
        except Exception:
            pass
    
    async def _become_follower(self) -> None:
        """Transition to follower state"""
        if self.raft_state != RaftState.FOLLOWER:
            self.raft_state = RaftState.FOLLOWER
            self.leader_id = None
            if self.local_node:
                self.local_node.raft_state = RaftState.FOLLOWER
                self.local_node.is_leader = False
    
    async def _become_candidate(self) -> None:
        """Transition to candidate state"""
        if self.raft_state != RaftState.CANDIDATE:
            self.raft_state = RaftState.CANDIDATE
            self.voted_for = self.node_id
            if self.local_node:
                self.local_node.raft_state = RaftState.CANDIDATE
    
    async def _become_leader(self) -> None:
        """Transition to leader state"""
        if self.raft_state != RaftState.LEADER:
            self.raft_state = RaftState.LEADER
            self.leader_id = self.node_id
            
            if self.local_node:
                self.local_node.raft_state = RaftState.LEADER
                self.local_node.is_leader = True
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_leader_elected(self.node_id, self.current_term)
    
    async def _election_loop(self) -> None:
        """Background election loop"""
        while self.enabled:
            try:
                # Check if election timeout reached
                if self.election_timeout_deadline and datetime.utcnow() >= self.election_timeout_deadline:
                    if self.raft_state != RaftState.LEADER:
                        await self._start_election()
                
                await asyncio.sleep(1)
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)
    
    async def _heartbeat_loop(self) -> None:
        """Background heartbeat loop"""
        while self.enabled:
            try:
                # Send heartbeats if leader
                if self.raft_state == RaftState.LEADER:
                    message = HeartbeatMessage(
                        leader_id=self.node_id,
                        term=self.current_term
                    )
                    
                    # Simulate sending to all peers
                    for node_id in self.nodes.keys():
                        if node_id != self.node_id:
                            pass  # In real impl, would send via network
                
                await asyncio.sleep(self.heartbeat_timeout.total_seconds())
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self.heartbeat_timeout.total_seconds())
    
    # ========================================================================
    # SPLIT-BRAIN DETECTION
    # ========================================================================
    
    async def detect_split_brain(self) -> bool:
        """
        Detect if cluster is split into multiple partitions
        
        Signs of split-brain:
        - Multiple nodes claiming to be leader in different terms
        - Minority partitions without heartbeats from leader
        - Network partition that isolates some nodes
        """
        try:
            if len(self.nodes) < 3:
                return False  # Need at least 3 nodes to detect split-brain
            
            # Get nodes with recent heartbeats
            healthy_nodes = 0
            for node in self.nodes.values():
                if node.last_heartbeat and \
                   datetime.utcnow() - node.last_heartbeat < self.heartbeat_timeout:
                    healthy_nodes += 1
            
            # If less than majority have heartbeats, potential split-brain
            required_healthy = len(self.nodes) / 2
            split_brain_detected = healthy_nodes < required_healthy
            
            if split_brain_detected != self.potential_split_brain:
                self.potential_split_brain = split_brain_detected
                if split_brain_detected:
                    await self._handle_split_brain()
            
            return split_brain_detected
        except Exception:
            return False
    
    async def _handle_split_brain(self) -> None:
        """Handle detected split-brain situation"""
        try:
            # Find partitions
            healthy_nodes = {nid for nid, node in self.nodes.items() 
                           if node.status == NodeStatus.HEALTHY}
            unhealthy_nodes = set(self.nodes.keys()) - healthy_nodes
            
            # Update cluster state
            old_state = self.cluster_state
            self.cluster_state = ClusterState.SPLIT_BRAIN
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_cluster_state_changed(old_state, self.cluster_state)
                await listener.on_split_brain_detected(healthy_nodes, unhealthy_nodes)
        except Exception:
            pass
    
    # ========================================================================
    # CLUSTER STATE MANAGEMENT
    # ========================================================================
    
    async def _update_cluster_state(self) -> None:
        """Update overall cluster state based on node states"""
        try:
            old_state = self.cluster_state
            
            healthy = sum(1 for n in self.nodes.values() if n.status == NodeStatus.HEALTHY)
            degraded = sum(1 for n in self.nodes.values() if n.status == NodeStatus.DEGRADED)
            unhealthy = sum(1 for n in self.nodes.values() if n.status == NodeStatus.UNHEALTHY)
            
            # Determine cluster state
            if unhealthy > 0 and healthy < len(self.nodes) // 2 + 1:
                self.cluster_state = ClusterState.FAILED
            elif await self.detect_split_brain():
                self.cluster_state = ClusterState.SPLIT_BRAIN
            elif degraded > 0:
                self.cluster_state = ClusterState.DEGRADED
            elif self.leader_id:
                self.cluster_state = ClusterState.HEALTHY
            else:
                self.cluster_state = ClusterState.INITIALIZING
            
            if old_state != self.cluster_state:
                for listener in self.listeners:
                    await listener.on_cluster_state_changed(old_state, self.cluster_state)
        
        except Exception:
            pass
    
    async def _health_check_loop(self) -> None:
        """Background health check loop"""
        while self.enabled:
            try:
                # Check node health
                for node_id, node in self.nodes.items():
                    if node_id == self.node_id:
                        continue
                    
                    if node.last_heartbeat:
                        elapsed = datetime.utcnow() - node.last_heartbeat
                        if elapsed > self.heartbeat_timeout * 2:
                            node.status = NodeStatus.UNHEALTHY
                        elif elapsed > self.heartbeat_timeout:
                            node.status = NodeStatus.DEGRADED
                        else:
                            node.status = NodeStatus.HEALTHY
                
                await self._update_cluster_state()
                await asyncio.sleep(2)
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(2)
    
    async def get_cluster_info(self) -> ClusterInfo:
        """Get complete cluster information"""
        nodes_data = [node.to_dict() for node in self.nodes.values()]
        
        healthy = sum(1 for n in self.nodes.values() if n.status == NodeStatus.HEALTHY)
        degraded = sum(1 for n in self.nodes.values() if n.status == NodeStatus.DEGRADED)
        unhealthy = sum(1 for n in self.nodes.values() if n.status == NodeStatus.UNHEALTHY)
        
        return ClusterInfo(
            cluster_id=self.cluster_id,
            state=self.cluster_state,
            leader_id=self.leader_id,
            nodes=nodes_data,
            term=self.current_term,
            healthy_nodes=healthy,
            degraded_nodes=degraded,
            unhealthy_nodes=unhealthy
        )
    
    # ========================================================================
    # LISTENER MANAGEMENT
    # ========================================================================
    
    async def add_listener(self, listener: StateChangeListener) -> bool:
        """Add state change listener"""
        try:
            if listener not in self.listeners:
                self.listeners.append(listener)
            return True
        except Exception:
            return False
    
    async def remove_listener(self, listener: StateChangeListener) -> bool:
        """Remove state change listener"""
        try:
            if listener in self.listeners:
                self.listeners.remove(listener)
            return True
        except Exception:
            return False
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def _random_election_timeout(self) -> timedelta:
        """Generate random election timeout"""
        min_ms = int(self.election_timeout_min.total_seconds() * 1000)
        max_ms = int(self.election_timeout_max.total_seconds() * 1000)
        random_ms = random.randint(min_ms, max_ms)
        return timedelta(milliseconds=random_ms)
    
    async def is_leader(self) -> bool:
        """Check if this node is the leader"""
        return self.raft_state == RaftState.LEADER
    
    async def get_leader_id(self) -> Optional[str]:
        """Get current leader ID"""
        return self.leader_id
    
    async def get_raft_state(self) -> RaftState:
        """Get current Raft state"""
        return self.raft_state
    
    async def is_ready(self) -> bool:
        """Check if cluster is ready for operations"""
        return self.enabled and self.leader_id is not None and \
               self.cluster_state == ClusterState.HEALTHY
