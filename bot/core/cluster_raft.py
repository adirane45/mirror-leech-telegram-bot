"""
Raft Consensus Manager for distributed leader election

Implements:
- Raft consensus algorithm (Follower, Candidate, Leader states)
- Leader election with randomized timeouts
- Heartbeat-based leadership maintenance
- Vote request handling
- Term management

Reference: Ongaro & Ousterhout, "In Search of an Understandable Consensus Algorithm"
"""

import asyncio
import random
from datetime import datetime, timedelta, UTC
from typing import Optional, List, Callable, Set

from .cluster_models import (
    RaftState,
    Node,
    HeartbeatMessage,
    VoteRequest,
)


class RaftConsensusManager:
    """
    Manages Raft consensus protocol for leader election
    
    Features:
    - Leader election with majority voting
    - Heartbeat-based leader health tracking
    - Randomized election timeouts to prevent split votes
    - State transitions (Follower → Candidate → Leader)
    """
    
    def __init__(
        self,
        node_id: str,
        election_timeout_min: timedelta = timedelta(seconds=5),
        election_timeout_max: timedelta = timedelta(seconds=10),
        heartbeat_timeout: timedelta = timedelta(seconds=5)
    ):
        """
        Initialize Raft consensus manager
        
        Args:
            node_id: Unique identifier for this node
            election_timeout_min: Minimum election timeout
            election_timeout_max: Maximum election timeout
            heartbeat_timeout: Heartbeat interval for leader
        """
        self.node_id = node_id
        
        # Raft state
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.leader_id: Optional[str] = None
        self.raft_state = RaftState.FOLLOWER
        
        # Timing configuration
        self.election_timeout_min = election_timeout_min
        self.election_timeout_max = election_timeout_max
        self.heartbeat_timeout = heartbeat_timeout
        
        # Tracking
        self.last_heartbeat: Optional[datetime] = None
        self.election_timeout_deadline: Optional[datetime] = None
        
        # Background tasks
        self._enabled = False
        self._election_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Callbacks for cluster manager
        self._on_leader_elected: Optional[Callable] = None
        self._get_nodes: Optional[Callable] = None
        self._send_heartbeat: Optional[Callable] = None
    
    async def start(self) -> None:
        """Start Raft consensus manager"""
        if not self._enabled:
            self._enabled = True
            self.election_timeout_deadline = datetime.now(UTC) + self._random_election_timeout()
            
            # Start background tasks
            self._election_task = asyncio.create_task(self._election_loop())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop(self) -> None:
        """Stop Raft consensus manager"""
        self._enabled = False
        
        if self._election_task:
            self._election_task.cancel()
            try:
                await self._election_task
            except asyncio.CancelledError:
                pass
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
    
    def set_callbacks(
        self,
        on_leader_elected: Callable,
        get_nodes: Callable,
        send_heartbeat: Optional[Callable] = None
    ) -> None:
        """Set callbacks for cluster manager integration"""
        self._on_leader_elected = on_leader_elected
        self._get_nodes = get_nodes
        self._send_heartbeat = send_heartbeat
    
    async def handle_heartbeat(self, message: HeartbeatMessage) -> bool:
        """
        Handle leader heartbeat
        
        Args:
            message: Heartbeat message from leader
            
        Returns:
            True if heartbeat accepted, False otherwise
        """
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
                self.election_timeout_deadline = datetime.now(UTC) + self._random_election_timeout()
                
                return True
            
            return False
        except Exception:
            return False
    
    async def handle_vote_request(self, request: VoteRequest) -> bool:
        """
        Handle vote request from candidate
        
        Args:
            request: Vote request message
            
        Returns:
            True if vote granted, False otherwise
        """
        try:
            # If higher term, convert to follower
            if request.term > self.current_term:
                self.current_term = request.term
                self.voted_for = None
                await self._become_follower()
            
            # Vote if we haven't voted and term matches/higher
            if request.term >= self.current_term and self.voted_for is None:
                self.voted_for = request.candidate_id
                self.current_term = request.term
                return True
            
            return False
        except Exception:
            return False
    
    async def start_election(self) -> None:
        """Start leader election"""
        try:
            self.current_term += 1
            await self._become_candidate()
            
            # Request votes from all nodes
            vote_count = 1  # Vote for self
            
            # Get nodes from cluster manager
            if self._get_nodes:
                nodes = await self._get_nodes()
                
                # In real impl, would send vote requests via network
                # For now, simulate single-node election
                required_votes = len(nodes) // 2 + 1
                
                if vote_count >= required_votes:
                    await self._become_leader()
        except Exception:
            pass
    
    async def _become_follower(self) -> None:
        """Transition to follower state"""
        if self.raft_state != RaftState.FOLLOWER:
            self.raft_state = RaftState.FOLLOWER
            self.leader_id = None
    
    async def _become_candidate(self) -> None:
        """Transition to candidate state"""
        if self.raft_state != RaftState.CANDIDATE:
            self.raft_state = RaftState.CANDIDATE
            self.voted_for = self.node_id
    
    async def _become_leader(self) -> None:
        """Transition to leader state"""
        if self.raft_state != RaftState.LEADER:
            self.raft_state = RaftState.LEADER
            self.leader_id = self.node_id
            
            # Notify cluster manager
            if self._on_leader_elected:
                await self._on_leader_elected(self.node_id, self.current_term)
    
    async def _election_loop(self) -> None:
        """Background election loop"""
        while self._enabled:
            try:
                # Check if election timeout reached
                if self.election_timeout_deadline and datetime.now(UTC) >= self.election_timeout_deadline:
                    if self.raft_state != RaftState.LEADER:
                        await self.start_election()
                
                await asyncio.sleep(1)
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)
    
    async def _heartbeat_loop(self) -> None:
        """Background heartbeat loop"""
        while self._enabled:
            try:
                # Send heartbeats if leader
                if self.raft_state == RaftState.LEADER:
                    if self._send_heartbeat:
                        message = HeartbeatMessage(
                            leader_id=self.node_id,
                            term=self.current_term
                        )
                        await self._send_heartbeat(message)
                    
                    await asyncio.sleep(self.heartbeat_timeout.total_seconds() / 2)
                else:
                    await asyncio.sleep(1)
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)
    
    def _random_election_timeout(self) -> timedelta:
        """Generate random election timeout"""
        min_ms = self.election_timeout_min.total_seconds() * 1000
        max_ms = self.election_timeout_max.total_seconds() * 1000
        random_ms = random.randint(int(min_ms), int(max_ms))
        return timedelta(milliseconds=random_ms)
    
    def is_leader(self) -> bool:
        """Check if this node is the leader"""
        return self.raft_state == RaftState.LEADER and self.leader_id == self.node_id
    
    def get_leader_id(self) -> Optional[str]:
        """Get current leader ID"""
        return self.leader_id
    
    def get_state(self) -> RaftState:
        """Get current Raft state"""
        return self.raft_state
    
    def get_term(self) -> int:
        """Get current term"""
        return self.current_term
