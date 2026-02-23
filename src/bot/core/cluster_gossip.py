"""
Gossip Protocol Manager for distributed node discovery

Implements:
- Eventual consistency through gossip
- Node discovery and status propagation
- Peer-to-peer information sharing
- Automatic cluster membership updates

Reference: Gossip/Epidemic protocols for distributed systems
"""

import asyncio
import random
from datetime import datetime, timedelta, UTC
from typing import Dict, Optional, Callable, List

from .cluster_models import (
    Node,
    NodeStatus,
    GossipMessage,
)


class GossipProtocolManager:
    """
    Manages gossip protocol for node discovery and status sharing
    
    Features:
    - Periodic gossip broadcasting
    - Node discovery through peer messages
    - Status propagation across cluster
    - Randomized peer selection
    """
    
    def __init__(
        self,
        node_id: str,
        hostname: str = "localhost",
        port: int = 8000,
        gossip_interval: timedelta = timedelta(seconds=5)
    ):
        """
        Initialize gossip protocol manager
        
        Args:
            node_id: Unique identifier for this node
            hostname: Hostname of this node
            port: Port of this node
            gossip_interval: How often to send gossip messages
        """
        self.node_id = node_id
        self.hostname = hostname
        self.port = port
        self.gossip_interval = gossip_interval
        
        # Background task
        self._enabled = False
        self._gossip_task: Optional[asyncio.Task] = None
        
        # Callbacks for cluster manager
        self._get_nodes: Optional[Callable] = None
        self._register_node: Optional[Callable] = None
        self._update_node_status: Optional[Callable] = None
        self._send_gossip: Optional[Callable] = None
    
    async def start(self) -> None:
        """Start gossip protocol manager"""
        if not self._enabled:
            self._enabled = True
            self._gossip_task = asyncio.create_task(self._gossip_loop())
    
    async def stop(self) -> None:
        """Stop gossip protocol manager"""
        self._enabled = False
        
        if self._gossip_task:
            self._gossip_task.cancel()
            try:
                await self._gossip_task
            except asyncio.CancelledError:
                pass
    
    def set_callbacks(
        self,
        get_nodes: Callable,
        register_node: Callable,
        update_node_status: Optional[Callable] = None,
        send_gossip: Optional[Callable] = None
    ) -> None:
        """Set callbacks for cluster manager integration"""
        self._get_nodes = get_nodes
        self._register_node = register_node
        self._update_node_status = update_node_status
        self._send_gossip = send_gossip
    
    async def handle_gossip_message(self, message: GossipMessage) -> None:
        """
        Handle incoming gossip message
        
        Args:
            message: Gossip message from peer
        """
        try:
            # Register sender if new
            if self._get_nodes:
                nodes = await self._get_nodes()
                
                if message.sender_id not in nodes:
                    if self._register_node:
                        await self._register_node(
                            message.sender_id,
                            message.sender_hostname,
                            message.sender_port
                        )
            
            # Update sender status
            if self._update_node_status:
                await self._update_node_status(
                    message.sender_id,
                    NodeStatus.HEALTHY,
                    message.timestamp
                )
            
            # Process known nodes in message
            for node_data in message.known_nodes:
                node_id = node_data.get('node_id')
                
                if not node_id or node_id == self.node_id:
                    continue
                
                # Register new nodes
                if self._get_nodes:
                    nodes = await self._get_nodes()
                    
                    if node_id not in nodes:
                        if self._register_node:
                            await self._register_node(
                                node_id,
                                node_data.get('hostname', 'unknown'),
                                node_data.get('port', 0)
                            )
        
        except Exception:
            pass
    
    async def _gossip_loop(self) -> None:
        """Background gossip protocol loop"""
        while self._enabled:
            try:
                # Get current nodes
                if self._get_nodes:
                    nodes = await self._get_nodes()
                    
                    # Create gossip message with known nodes
                    known_nodes = []
                    for node in nodes.values():
                        known_nodes.append(node.to_dict())
                    
                    message = GossipMessage(
                        sender_id=self.node_id,
                        sender_hostname=self.hostname,
                        sender_port=self.port,
                        known_nodes=known_nodes
                    )
                    
                    # Send to random peers
                    if self._send_gossip and len(nodes) > 1:
                        # Select random peers (gossip to subset)
                        peer_nodes = [n for nid, n in nodes.items() if nid != self.node_id]
                        num_peers = min(3, len(peer_nodes))  # Gossip to max 3 peers
                        
                        if peer_nodes:
                            selected_peers = random.sample(peer_nodes, num_peers)
                            for peer in selected_peers:
                                await self._send_gossip(peer, message)
                
                await asyncio.sleep(self.gossip_interval.total_seconds())
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self.gossip_interval.total_seconds())
    
    def get_gossip_interval(self) -> timedelta:
        """Get gossip interval"""
        return self.gossip_interval
    
    def set_gossip_interval(self, interval: timedelta) -> None:
        """Set gossip interval"""
        self.gossip_interval = interval
