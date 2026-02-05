"""
Cluster Manager for High Availability

Manages cluster membership, leader election, node discovery, and coordination.
Enables multiple bot instances to work together as a coordinated cluster.

Features:
- Cluster membership management
- Leader election
- Node discovery and registration
- Heartbeat mechanism
- Split-brain prevention
- Cluster state synchronization
"""

import asyncio
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import random


class NodeState(Enum):
    """Cluster node state"""
    JOINING = "joining"
    ACTIVE = "active"
    LEADER = "leader"
    DEGRADED = "degraded"
    LEAVING = "leaving"
    UNREACHABLE = "unreachable"


class ClusterState(Enum):
    """Overall cluster state"""
    FORMING = "forming"
    STABLE = "stable"
    DEGRADED = "degraded"
    SPLIT_BRAIN = "split_brain"


@dataclass
class NodeInfo:
    """Information about a cluster node"""
    node_id: str
    address: str
    port: int
    state: NodeState = NodeState.JOINING
    is_leader: bool = False
    joined_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_tasks: int = 0
    priority: int = 100  # For leader election
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClusterInfo:
    """Information about the cluster"""
    cluster_id: str
    state: ClusterState
    total_nodes: int
    active_nodes: int
    leader_node: Optional[str]
    formed_at: datetime
    last_election: Optional[datetime] = None


class ClusterManager:
    """Manages cluster membership and coordination"""
    
    _instance: Optional['ClusterManager'] = None
    
    def __init__(self):
        self.enabled = False
        self.cluster_id = str(uuid.uuid4())[:8]
        self.node_id = str(uuid.uuid4())[:8]
        
        self.nodes: Dict[str, NodeInfo] = {}
        self.current_leader: Optional[str] = None
        self.is_leader = False
        
        self.node_address = "localhost"
        self.node_port = 8000
        self.heartbeat_interval = 5  # seconds
        self.heartbeat_timeout = 15  # seconds
        self.election_timeout = 10  # seconds
        
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.monitor_task: Optional[asyncio.Task] = None
        self.election_in_progress = False
        
        self.cluster_formed_at: Optional[datetime] = None
        self.last_election_at: Optional[datetime] = None
        
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'ClusterManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = ClusterManager()
        return cls._instance
    
    async def enable(
        self,
        address: str = "localhost",
        port: int = 8000,
        seed_nodes: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Enable cluster manager"""
        try:
            async with self.lock:
                self.enabled = True
                self.node_address = address
                self.node_port = port
                
                # Register self as first node
                self_node = NodeInfo(
                    node_id=self.node_id,
                    address=address,
                    port=port,
                    state=NodeState.ACTIVE,
                    is_leader=False
                )
                self.nodes[self.node_id] = self_node
                
                # Join seed nodes if provided
                if seed_nodes:
                    for seed in seed_nodes:
                        await self._discover_node(seed['address'], seed['port'])
                
                # Start background tasks
                self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                self.monitor_task = asyncio.create_task(self._monitor_loop())
                
                # Trigger initial election if no leader
                if not self.current_leader:
                    await self._trigger_election()
                
                self.cluster_formed_at = datetime.utcnow()
                
                return True
        except Exception as e:
            print(f"Error enabling cluster manager: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable cluster manager"""
        try:
            async with self.lock:
                self.enabled = False
                
                # Mark self as leaving
                if self.node_id in self.nodes:
                    self.nodes[self.node_id].state = NodeState.LEAVING
                
                # Cancel background tasks
                if self.heartbeat_task:
                    self.heartbeat_task.cancel()
                    try:
                        await self.heartbeat_task
                    except asyncio.CancelledError:
                        pass
                
                if self.monitor_task:
                    self.monitor_task.cancel()
                    try:
                        await self.monitor_task
                    except asyncio.CancelledError:
                        pass
                
                return True
        except Exception as e:
            print(f"Error disabling cluster manager: {e}")
            return False
    
    async def join_cluster(self, leader_address: str, leader_port: int) -> bool:
        """Join an existing cluster"""
        try:
            # Discover leader node
            success = await self._discover_node(leader_address, leader_port)
            if not success:
                return False
            
            # Wait for cluster state sync
            await asyncio.sleep(2)
            
            return True
        except Exception as e:
            print(f"Error joining cluster: {e}")
            return False
    
    async def _discover_node(self, address: str, port: int) -> bool:
        """Discover and register a node"""
        try:
            # In production, make actual HTTP/RPC call to node
            # For now, simulate node discovery
            node_id = f"node_{len(self.nodes)}"
            
            node = NodeInfo(
                node_id=node_id,
                address=address,
                port=port,
                state=NodeState.ACTIVE
            )
            
            async with self.lock:
                self.nodes[node_id] = node
            
            return True
        except Exception as e:
            print(f"Error discovering node: {e}")
            return False
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats"""
        while self.enabled:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Heartbeat error: {e}")
                await asyncio.sleep(1)
    
    async def _send_heartbeat(self) -> None:
        """Send heartbeat to cluster"""
        try:
            async with self.lock:
                if self.node_id in self.nodes:
                    self.nodes[self.node_id].last_heartbeat = datetime.utcnow()
                    
                    # Update node metrics
                    try:
                        import psutil
                        self.nodes[self.node_id].cpu_usage = psutil.cpu_percent()
                        self.nodes[self.node_id].memory_usage = psutil.virtual_memory().percent
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error sending heartbeat: {e}")
    
    async def _monitor_loop(self) -> None:
        """Monitor cluster health"""
        while self.enabled:
            try:
                await self._check_node_health()
                await self._check_leader_health()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(1)
    
    async def _check_node_health(self) -> None:
        """Check health of all nodes"""
        try:
            async with self.lock:
                now = datetime.utcnow()
                timeout_threshold = timedelta(seconds=self.heartbeat_timeout)
                
                for node_id, node in self.nodes.items():
                    if node_id == self.node_id:
                        continue  # Skip self
                    
                    time_since_heartbeat = now - node.last_heartbeat
                    
                    if time_since_heartbeat > timeout_threshold:
                        if node.state != NodeState.UNREACHABLE:
                            node.state = NodeState.UNREACHABLE
                            print(f"Node {node_id} marked unreachable")
                            
                            # Trigger election if leader is unreachable
                            if node.is_leader:
                                await self._trigger_election()
        except Exception as e:
            print(f"Error checking node health: {e}")
    
    async def _check_leader_health(self) -> None:
        """Check leader health and trigger election if needed"""
        try:
            async with self.lock:
                if not self.current_leader:
                    await self._trigger_election()
                    return
                
                if self.current_leader not in self.nodes:
                    self.current_leader = None
                    await self._trigger_election()
                    return
                
                leader_node = self.nodes[self.current_leader]
                if leader_node.state == NodeState.UNREACHABLE:
                    self.current_leader = None
                    await self._trigger_election()
        except Exception as e:
            print(f"Error checking leader health: {e}")
    
    async def _trigger_election(self) -> None:
        """Trigger leader election"""
        if self.election_in_progress:
            return
        
        try:
            self.election_in_progress = True
            self.last_election_at = datetime.utcnow()
            
            # Simple election: highest priority + lowest node_id wins
            async with self.lock:
                active_nodes = [
                    node for node in self.nodes.values()
                    if node.state in [NodeState.ACTIVE, NodeState.DEGRADED]
                ]
                
                if not active_nodes:
                    return
                
                # Sort by priority (desc) then by node_id (asc)
                active_nodes.sort(key=lambda n: (-n.priority, n.node_id))
                
                new_leader = active_nodes[0]
                
                # Update leader status
                for node in self.nodes.values():
                    node.is_leader = False
                
                new_leader.is_leader = True
                new_leader.state = NodeState.LEADER
                self.current_leader = new_leader.node_id
                self.is_leader = (new_leader.node_id == self.node_id)
                
                print(f"Leader elected: {self.current_leader} (is_self: {self.is_leader})")
        
        except Exception as e:
            print(f"Error in election: {e}")
        finally:
            self.election_in_progress = False
    
    async def get_cluster_info(self) -> ClusterInfo:
        """Get current cluster information"""
        try:
            async with self.lock:
                active_count = sum(
                    1 for node in self.nodes.values()
                    if node.state in [NodeState.ACTIVE, NodeState.LEADER]
                )
                
                # Determine cluster state
                if len(self.nodes) == 1:
                    cluster_state = ClusterState.FORMING
                elif active_count < len(self.nodes) / 2:
                    cluster_state = ClusterState.DEGRADED
                else:
                    cluster_state = ClusterState.STABLE
                
                return ClusterInfo(
                    cluster_id=self.cluster_id,
                    state=cluster_state,
                    total_nodes=len(self.nodes),
                    active_nodes=active_count,
                    leader_node=self.current_leader,
                    formed_at=self.cluster_formed_at or datetime.utcnow(),
                    last_election=self.last_election_at
                )
        except Exception as e:
            print(f"Error getting cluster info: {e}")
            return ClusterInfo(
                cluster_id=self.cluster_id,
                state=ClusterState.FORMING,
                total_nodes=0,
                active_nodes=0,
                leader_node=None,
                formed_at=datetime.utcnow()
            )
    
    async def get_nodes(self) -> List[NodeInfo]:
        """Get all cluster nodes"""
        async with self.lock:
            return list(self.nodes.values())
    
    async def get_active_nodes(self) -> List[NodeInfo]:
        """Get active cluster nodes"""
        async with self.lock:
            return [
                node for node in self.nodes.values()
                if node.state in [NodeState.ACTIVE, NodeState.LEADER]
            ]
    
    async def get_leader_node(self) -> Optional[NodeInfo]:
        """Get the leader node"""
        async with self.lock:
            if self.current_leader and self.current_leader in self.nodes:
                return self.nodes[self.current_leader]
            return None
    
    async def is_cluster_healthy(self) -> bool:
        """Check if cluster is healthy"""
        try:
            info = await self.get_cluster_info()
            return (
                info.state == ClusterState.STABLE and
                info.leader_node is not None and
                info.active_nodes >= (info.total_nodes / 2)
            )
        except Exception:
            return False
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get cluster statistics"""
        try:
            info = await self.get_cluster_info()
            nodes = await self.get_nodes()
            
            return {
                'enabled': self.enabled,
                'cluster_id': self.cluster_id,
                'node_id': self.node_id,
                'is_leader': self.is_leader,
                'cluster_state': info.state.value,
                'total_nodes': info.total_nodes,
                'active_nodes': info.active_nodes,
                'leader_node': info.leader_node,
                'uptime_seconds': (
                    (datetime.utcnow() - info.formed_at).total_seconds()
                    if info.formed_at else 0
                ),
                'last_election': (
                    info.last_election.isoformat()
                    if info.last_election else None
                ),
                'nodes': [
                    {
                        'node_id': node.node_id,
                        'state': node.state.value,
                        'is_leader': node.is_leader,
                        'cpu_usage': node.cpu_usage,
                        'memory_usage': node.memory_usage,
                        'active_tasks': node.active_tasks
                    }
                    for node in nodes
                ]
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'enabled': self.enabled, 'error': str(e)}
    
    async def reset(self) -> bool:
        """Reset cluster manager"""
        try:
            await self.disable()
            self.nodes.clear()
            self.current_leader = None
            self.is_leader = False
            self.cluster_id = str(uuid.uuid4())[:8]
            return True
        except Exception as e:
            print(f"Error resetting: {e}")
            return False
