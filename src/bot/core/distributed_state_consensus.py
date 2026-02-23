"""
Distributed Consensus Manager for cluster-wide consensus-based updates

Handles:
- Proposal creation and voting
- Consensus threshold checking
- Proposal state management
- Vote tracking and validation
"""

import asyncio
from typing import Dict, Set, Optional, Any, List

from .distributed_state_models import ConsensusProposal


class DistributedConsensusManager:
    """
    Manages distributed consensus proposals and voting
    
    Features:
    - Proposal creation and tracking
    - Vote collection (for/against)
    - Consensus threshold validation
    - Proposal state management (pending/approved/rejected/applied)
    """
    
    def __init__(self, node_id: str, consensus_threshold: float = 0.5):
        """
        Initialize consensus manager
        
        Args:
            node_id: Unique identifier for this node
            consensus_threshold: Percentage of votes needed for consensus (0.0-1.0)
        """
        self.node_id = node_id
        self.consensus_threshold = consensus_threshold
        self.proposals: Dict[str, ConsensusProposal] = {}
        self.peers: Set[str] = set()
        
        # Metrics
        self.consensual_updates = 0
        self.rejected_proposals = 0
        
        # Listeners for consensus events
        self._listeners: List = []
        
        self._enabled = False
    
    async def start(self) -> None:
        """Start consensus manager"""
        self._enabled = True
    
    async def stop(self) -> None:
        """Stop consensus manager"""
        self._enabled = False
    
    def register_peer(self, peer_id: str) -> None:
        """Register a peer node for consensus voting"""
        if peer_id != self.node_id:
            self.peers.add(peer_id)
    
    def unregister_peer(self, peer_id: str) -> None:
        """Unregister a peer node"""
        self.peers.discard(peer_id)
    
    async def create_proposal(
        self,
        key: str,
        value: Any,
        old_value: Any = None
    ) -> Optional[ConsensusProposal]:
        """
        Create a new consensus proposal
        
        Args:
            key: State key being updated
            value: New value to apply
            old_value: Previous value (for validation)
            
        Returns:
            ConsensusProposal if created, None on error
        """
        if not self._enabled:
            return None
        
        try:
            proposal = ConsensusProposal(
                key=key,
                value=value,
                proposer_node=self.node_id,
                consensus_threshold=self.consensus_threshold
            )
            
            self.proposals[proposal.proposal_id] = proposal
            
            # Auto-vote for own proposal
            proposal.votes_for.add(self.node_id)
            
            return proposal
        except Exception:
            return None
    
    async def vote_on_proposal(
        self,
        proposal_id: str,
        vote_for: bool,
        from_node: str
    ) -> bool:
        """
        Record vote on a proposal
        
        Args:
            proposal_id: ID of proposal to vote on
            vote_for: True for approval, False for rejection
            from_node: Node ID casting the vote
            
        Returns:
            True if vote recorded, False on error
        """
        if proposal_id not in self.proposals:
            return False
        
        try:
            proposal = self.proposals[proposal_id]
            
            if vote_for:
                proposal.votes_for.add(from_node)
                # Remove from against if previously voted against
                proposal.votes_against.discard(from_node)
            else:
                proposal.votes_against.add(from_node)
                # Remove from for if previously voted for
                proposal.votes_for.discard(from_node)
            
            # Check if consensus now reached
            if await self.check_consensus(proposal):
                proposal.state = "approved"
            elif await self.check_rejection(proposal):
                proposal.state = "rejected"
                self.rejected_proposals += 1
            
            return True
        except Exception:
            return False
    
    async def check_consensus(self, proposal: ConsensusProposal) -> bool:
        """
        Check if proposal has reached consensus
        
        Args:
            proposal: Proposal to check
            
        Returns:
            True if consensus reached, False otherwise
        """
        if not self.peers:
            # Single node - auto-approve
            return True
        
        total_voters = len(self.peers) + 1  # +1 for self
        votes_needed = int(total_voters * proposal.consensus_threshold)
        votes_have = len(proposal.votes_for)
        
        return votes_have >= votes_needed
    
    async def check_rejection(self, proposal: ConsensusProposal) -> bool:
        """
        Check if proposal has been rejected (too many against votes)
        
        Args:
            proposal: Proposal to check
            
        Returns:
            True if rejected, False otherwise
        """
        if not self.peers:
            return False
        
        total_voters = len(self.peers) + 1  # +1 for self
        # Rejection threshold: more than (1 - consensus_threshold) votes against
        rejection_threshold = 1.0 - proposal.consensus_threshold
        votes_needed = int(total_voters * rejection_threshold) + 1
        votes_against = len(proposal.votes_against)
        
        return votes_against >= votes_needed
    
    async def mark_proposal_applied(self, proposal_id: str) -> bool:
        """
        Mark a proposal as successfully applied
        
        Args:
            proposal_id: ID of proposal
            
        Returns:
            True if marked, False on error
        """
        if proposal_id not in self.proposals:
            return False
        
        try:
            proposal = self.proposals[proposal_id]
            proposal.state = "applied"
            self.consensual_updates += 1
            
            # Notify listeners
            await self._notify_consensus_reached(proposal)
            
            return True
        except Exception:
            return False
    
    def get_proposal(self, proposal_id: str) -> Optional[ConsensusProposal]:
        """Get proposal by ID"""
        return self.proposals.get(proposal_id)
    
    def get_all_proposals(self) -> Dict[str, ConsensusProposal]:
        """Get all proposals"""
        return dict(self.proposals)
    
    def get_pending_proposals(self) -> List[ConsensusProposal]:
        """Get all pending proposals"""
        return [p for p in self.proposals.values() if p.state == "pending"]
    
    def clear_proposals(self) -> None:
        """Clear all proposals (for testing/cleanup)"""
        self.proposals.clear()
    
    def add_listener(self, listener) -> None:
        """Add listener for consensus events"""
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def remove_listener(self, listener) -> None:
        """Remove listener for consensus events"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    async def _notify_consensus_reached(self, proposal: ConsensusProposal) -> None:
        """Notify listeners that consensus was reached"""
        for listener in self._listeners:
            if hasattr(listener, 'on_consensus_reached'):
                await listener.on_consensus_reached(proposal)
    
    def get_metrics(self) -> Dict:
        """Get consensus operation metrics"""
        return {
            'consensual_updates': self.consensual_updates,
            'rejected_proposals': self.rejected_proposals,
            'total_proposals': len(self.proposals),
            'pending_proposals': len(self.get_pending_proposals()),
        }
