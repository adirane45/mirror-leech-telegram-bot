"""
Cluster Manager - Distributed node coordination and leader election

Refactored module structure:
- cluster_models.py: Enums, data classes, abstract listener
- cluster_raft.py: Raft consensus logic for leader election
- cluster_gossip.py: Gossip protocol for node discovery
- cluster_manager.py: Node management and orchestration (this file)

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
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Callable, Set, Any

# Import models from refactored cluster_models module
from .cluster_models import (
    NodeStatus,
    RaftState,
    ClusterState,
    Node,
    GossipMessage,
    HeartbeatMessage,
    VoteRequest,
    ClusterInfo,
    StateChangeListener,
)

# Import specialized managers
from .cluster_raft import RaftConsensusManager
from .cluster_gossip import GossipProtocolManager


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
        
        # Background tasks (for backward compatibility with tests)
        self.enabled = False
        self._health_check_task: Optional[asyncio.Task] = None
        self._gossip_task: Optional[asyncio.Task] = None  # Deprecated, kept for tests
        self._election_task: Optional[asyncio.Task] = None  # Deprecated, kept for tests
        self._heartbeat_task: Optional[asyncio.Task] = None  # Deprecated, kept for tests
        
        # State change listeners
        self.listeners: List[StateChangeListener] = []
        
        # Split-brain tracking
        self.potential_split_brain = False
        self.split_brain_detection_threshold = 0.5  # Majority threshold
        
        # Backward compatibility attributes (delegated to managers)
        self._current_term = 0
        self._voted_for: Optional[str] = None
        self._leader_id: Optional[str] = None
        self._raft_state = RaftState.FOLLOWER
        self._election_timeout_deadline: Optional[datetime] = None
        
        # Specialized managers (initialized in initialize())
        self.raft_manager: Optional[RaftConsensusManager] = None
        self.gossip_manager: Optional[GossipProtocolManager] = None
    
    @classmethod
    def get_instance(cls) -> 'ClusterManager':
        """Get singleton instance"""
        return cls()
    
    # ========================================================================
    # BACKWARD COMPATIBILITY PROPERTIES
    # ========================================================================
    
    @property
    def current_term(self) -> int:
        """Get current Raft term (backward compatibility)"""
        if self.raft_manager:
            return self.raft_manager.get_term()
        return self._current_term
    
    @current_term.setter
    def current_term(self, value: int) -> None:
        """Set current Raft term (backward compatibility for tests)"""
        self._current_term = value
        if self.raft_manager:
            self.raft_manager.current_term = value
    
    @property
    def voted_for(self) -> Optional[str]:
        """Get voted_for node (backward compatibility)"""
        if self.raft_manager:
            return self.raft_manager.voted_for
        return self._voted_for
    
    @voted_for.setter
    def voted_for(self, value: Optional[str]) -> None:
        """Set voted_for node (backward compatibility for tests)"""
        self._voted_for = value
        if self.raft_manager:
            self.raft_manager.voted_for = value
    
    @property
    def leader_id(self) -> Optional[str]:
        """Get leader ID (backward compatibility)"""
        if self.raft_manager:
            return self.raft_manager.get_leader_id()
        return self._leader_id
    
    @leader_id.setter
    def leader_id(self, value: Optional[str]) -> None:
        """Set leader ID (backward compatibility for tests)"""
        self._leader_id = value
        if self.raft_manager:
            self.raft_manager.leader_id = value
    
    @property
    def raft_state(self) -> RaftState:
        """Get Raft state (backward compatibility)"""
        if self.raft_manager:
            return self.raft_manager.get_state()
        return self._raft_state
    
    @raft_state.setter
    def raft_state(self, value: RaftState) -> None:
        """Set Raft state (backward compatibility for tests)"""
        self._raft_state = value
        if self.raft_manager:
            self.raft_manager.raft_state = value
            # When setting to LEADER, also set leader_id automatically
            if value == RaftState.LEADER:
                self.raft_manager.leader_id = self.node_id
    
    @property
    def election_timeout_deadline(self) -> Optional[datetime]:
        """Get election timeout deadline (backward compatibility)"""
        if self.raft_manager:
            return self.raft_manager.election_timeout_deadline
        return self._election_timeout_deadline
    
    @election_timeout_deadline.setter
    def election_timeout_deadline(self, value: Optional[datetime]) -> None:
        """Set election timeout deadline (backward compatibility for tests)"""
        self._election_timeout_deadline = value
        if self.raft_manager:
            self.raft_manager.election_timeout_deadline = value
    
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
            
            # Initialize Raft consensus manager
            self.raft_manager = RaftConsensusManager(
                node_id=node_id,
                election_timeout_min=self.election_timeout_min,
                election_timeout_max=self.election_timeout_max,
                heartbeat_timeout=self.heartbeat_timeout
            )
            
            # Set Raft callbacks
            self.raft_manager.set_callbacks(
                on_leader_elected=self._on_leader_elected,
                get_nodes=self._get_nodes_for_raft
            )
            
            # Initialize Gossip protocol manager
            self.gossip_manager = GossipProtocolManager(
                node_id=node_id,
                hostname=hostname,
                port=port,
                gossip_interval=self.gossip_interval
            )
            
            # Set Gossip callbacks
            self.gossip_manager.set_callbacks(
                get_nodes=self._get_nodes_for_gossip,
                register_node=self.register_node,
                update_node_status=self._update_node_status
            )
            
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize cluster manager: {e}")
    
    # ========================================================================
    # DEPRECATED WRAPPER METHODS (kept for backward compatibility)
    # ========================================================================
    
    async def _become_follower(self) -> None:
        """Deprecated: Use raft_manager.become_follower() instead"""
        if self.raft_manager:
            await self.raft_manager._become_follower()
        else:
            self.raft_state = RaftState.FOLLOWER
    
    async def _become_candidate(self) -> None:
        """Deprecated: Use raft_manager.become_candidate() instead"""
        if self.raft_manager:
            await self.raft_manager._become_candidate()
        else:
            self.raft_state = RaftState.CANDIDATE
    
    async def _become_leader(self) -> None:
        """Deprecated: Use raft_manager.become_leader() instead"""
        if self.raft_manager:
            await self.raft_manager._become_leader()
        else:
            self.raft_state = RaftState.LEADER
    
    async def _start_election(self) -> None:
        """Deprecated: Use raft_manager.start_election() instead"""
        if self.raft_manager:
            await self.raft_manager.start_election()
    
    def _random_election_timeout(self) -> timedelta:
        """Deprecated: Election timeout is handled by raft_manager"""
        min_ms = int(self.election_timeout_min.total_seconds() * 1000)
        max_ms = int(self.election_timeout_max.total_seconds() * 1000)
        random_ms = random.randint(min_ms, max_ms)
        return timedelta(milliseconds=random_ms)
    
    async def start(self) -> bool:
        """Start cluster management"""
        if self.enabled:
            return True
        
        try:
            self.enabled = True
            
            # Start Raft consensus manager
            if self.raft_manager:
                await self.raft_manager.start()
                # For backward compatibility, set task references
                self._election_task = asyncio.current_task()
                self._heartbeat_task = asyncio.current_task()
            
            # Start Gossip protocol manager
            if self.gossip_manager:
                await self.gossip_manager.start()
                # For backward compatibility
                self._gossip_task = asyncio.current_task()
            
            # Start health check
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
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
            
            # Stop Raft consensus manager
            if self.raft_manager:
                await self.raft_manager.stop()
            
            # Stop Gossip protocol manager
            if self.gossip_manager:
                await self.gossip_manager.stop()
            
            # Cancel health check task
            if self._health_check_task and not self._health_check_task.done():
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
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
                leader_id = await self.get_leader_id()
                if self.raft_manager and node_id == leader_id:
                    await self.raft_manager.start_election()
            
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
    # GOSSIP PROTOCOL (Delegated to GossipProtocolManager)
    # ========================================================================
    
    async def handle_gossip_message(self, message: GossipMessage) -> None:
        """Handle incoming gossip message (delegates to gossip manager)"""
        if self.gossip_manager:
            await self.gossip_manager.handle_gossip_message(message)
    
    # ========================================================================
    # RAFT LEADER ELECTION (Delegated to RaftConsensusManager)
    # ========================================================================
    
    async def handle_heartbeat(self, message: HeartbeatMessage) -> bool:
        """Handle leader heartbeat (delegates to raft manager)"""
        if self.raft_manager:
            result = await self.raft_manager.handle_heartbeat(message)
            
            # Sync local state from Raft manager
            if result and self.local_node:
                self.local_node.raft_state = self.raft_manager.get_state()
                self.local_node.is_leader = self.raft_manager.is_leader()
                self.last_heartbeat = message.timestamp  # Sync last_heartbeat
                
                # Update leader node status
                if self.raft_manager.get_leader_id() in self.nodes:
                    self.nodes[self.raft_manager.get_leader_id()].is_leader = True
                    self.nodes[self.raft_manager.get_leader_id()].status = NodeStatus.HEALTHY
                
                await self._update_cluster_state()
            
            return result
        return False
    
    async def handle_vote_request(self, request: VoteRequest) -> bool:
        """Handle vote request from candidate (delegates to raft manager)"""
        if self.raft_manager:
            result = await self.raft_manager.handle_vote_request(request)
            
            # Sync local state from Raft manager
            if self.local_node and result:
                self.local_node.raft_state = self.raft_manager.get_state()
            
            return result
        return False
    
    # ========================================================================
    # MANAGER CALLBACKS AND HELPERS
    # ========================================================================
    
    async def _on_leader_elected(self, leader_id: str, term: int) -> None:
        """Callback when leader is elected (called by RaftConsensusManager)"""
        try:
            # Update local node if it's the new leader
            if leader_id == self.node_id and self.local_node:
                self.local_node.raft_state = RaftState.LEADER
                self.local_node.is_leader = True
            
            # Update leader node
            if leader_id in self.nodes:
                self.nodes[leader_id].is_leader = True
                self.nodes[leader_id].raft_state = RaftState.LEADER
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_leader_elected(leader_id, term)
        except Exception:
            pass
    
    async def _get_nodes_for_raft(self) -> Dict[str, Node]:
        """Get nodes for Raft manager"""
        return self.nodes
    
    async def _get_nodes_for_gossip(self) -> Dict[str, Node]:
        """Get nodes for Gossip manager"""
        return self.nodes
    
    async def _update_node_status(
        self,
        node_id: str,
        status: NodeStatus,
        timestamp: datetime
    ) -> None:
        """Update node status (called by GossipProtocolManager)"""
        try:
            if node_id in self.nodes:
                self.nodes[node_id].status = status
                self.nodes[node_id].last_heartbeat = timestamp
        except Exception:
            pass
            if self.local_node and result:
                self.local_node.raft_state = self.raft_manager.get_state()
            
            return result
        return False
    
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
                   datetime.now(UTC) - node.last_heartbeat < self.heartbeat_timeout:
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
                        elapsed = datetime.now(UTC) - node.last_heartbeat
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
    
    
    async def is_leader(self) -> bool:
        """Check if this node is the leader"""
        if self.raft_manager:
            return self.raft_manager.is_leader()
        return False
    
    async def get_leader_id(self) -> Optional[str]:
        """Get current leader ID"""
        if self.raft_manager:
            return self.raft_manager.get_leader_id()
        return None
    
    async def get_raft_state(self) -> RaftState:
        """Get current Raft state"""
        if self.raft_manager:
            return self.raft_manager.get_state()
        return RaftState.FOLLOWER
    
    async def is_ready(self) -> bool:
        """Check if cluster is ready for operations"""
        leader_id = await self.get_leader_id()
        return self.enabled and leader_id is not None and \
               self.cluster_state == ClusterState.HEALTHY
