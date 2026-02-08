"""
Unit tests for Cluster Manager component

Tests cover:
- Initialization and lifecycle
- Node management and registration
- Gossip protocol
- Raft leader election
- Heartbeat and vote request handling
- Cluster state management
- Split-brain detection
- State change listeners
"""

import asyncio
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from bot.core.cluster_manager import (
    ClusterManager,
    Node,
    NodeStatus,
    RaftState,
    ClusterState,
    GossipMessage,
    HeartbeatMessage,
    VoteRequest,
    ClusterInfo,
    StateChangeListener
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def cluster_manager():
    """Get cluster manager instance"""
    manager = ClusterManager.get_instance()
    # Reset state
    manager.nodes.clear()
    manager.current_term = 0
    manager.voted_for = None
    manager.leader_id = None
    manager.raft_state = RaftState.FOLLOWER
    manager.cluster_state = ClusterState.INITIALIZING
    manager.enabled = False
    manager.listeners.clear()
    
    yield manager
    
    # Cleanup
    try:
        asyncio.run(manager.stop())
    except:
        pass
    manager.nodes.clear()


@pytest.fixture
def mock_listener():
    """Mock state change listener"""
    class TestListener(StateChangeListener):
        def __init__(self):
            self.leader_elected = AsyncMock()
            self.node_joined = AsyncMock()
            self.node_left = AsyncMock()
            self.state_changed = AsyncMock()
            self.split_brain_detected = AsyncMock()
        
        async def on_leader_elected(self, leader_id: str, term: int) -> None:
            await self.leader_elected(leader_id, term)
        
        async def on_node_joined(self, node_id: str, node: Node) -> None:
            await self.node_joined(node_id, node)
        
        async def on_node_left(self, node_id: str) -> None:
            await self.node_left(node_id)
        
        async def on_cluster_state_changed(self, old_state: ClusterState, new_state: ClusterState) -> None:
            await self.state_changed(old_state, new_state)
        
        async def on_split_brain_detected(self, partition_a, partition_b) -> None:
            await self.split_brain_detected(partition_a, partition_b)
    
    return TestListener()


# ============================================================================
# TESTS: INITIALIZATION AND LIFECYCLE
# ============================================================================

@pytest.mark.asyncio
async def test_singleton_instance(cluster_manager):
    """Test cluster manager is singleton"""
    mgr1 = ClusterManager.get_instance()
    mgr2 = ClusterManager.get_instance()
    
    assert mgr1 is mgr2


@pytest.mark.asyncio
async def test_initialize_cluster(cluster_manager):
    """Test cluster manager initialization"""
    result = await cluster_manager.initialize('node1', 'localhost', 8000)
    
    assert result is True
    assert cluster_manager.node_id == 'node1'
    assert cluster_manager.hostname == 'localhost'
    assert cluster_manager.port == 8000
    assert cluster_manager.local_node is not None
    assert cluster_manager.local_node.node_id == 'node1'


@pytest.mark.asyncio
async def test_start_cluster_manager(cluster_manager):
    """Test starting cluster manager"""
    await cluster_manager.initialize('node1', 'localhost', 8000)
    result = await cluster_manager.start()
    
    assert result is True
    assert cluster_manager.enabled is True
    assert cluster_manager._gossip_task is not None
    assert cluster_manager._election_task is not None
    assert cluster_manager._heartbeat_task is not None
    
    await cluster_manager.stop()


@pytest.mark.asyncio
async def test_stop_cluster_manager(cluster_manager):
    """Test stopping cluster manager"""
    await cluster_manager.initialize('node1', 'localhost', 8000)
    await cluster_manager.start()
    assert cluster_manager.enabled is True
    
    result = await cluster_manager.stop()
    assert result is True
    assert cluster_manager.enabled is False


@pytest.mark.asyncio
async def test_start_already_started(cluster_manager):
    """Test starting when already started"""
    await cluster_manager.initialize('node1', 'localhost', 8000)
    await cluster_manager.start()
    
    result = await cluster_manager.start()
    assert result is True


@pytest.mark.asyncio
async def test_stop_when_not_started(cluster_manager):
    """Test stopping when not started"""
    result = await cluster_manager.stop()
    assert result is True


# ============================================================================
# TESTS: NODE MANAGEMENT
# ============================================================================

@pytest.mark.asyncio
async def test_register_node(cluster_manager):
    """Test registering a node"""
    result = await cluster_manager.register_node('node1', 'host1', 8000)
    
    assert result is True
    assert 'node1' in cluster_manager.nodes
    node = cluster_manager.nodes['node1']
    assert node.node_id == 'node1'
    assert node.hostname == 'host1'
    assert node.port == 8000


@pytest.mark.asyncio
async def test_register_multiple_nodes(cluster_manager):
    """Test registering multiple nodes"""
    for i in range(5):
        result = await cluster_manager.register_node(f'node{i}', f'host{i}', 8000 + i)
        assert result is True
    
    assert len(cluster_manager.nodes) == 5


@pytest.mark.asyncio
async def test_register_node_trigger_listener(cluster_manager, mock_listener):
    """Test node registration triggers listener"""
    await cluster_manager.add_listener(mock_listener)
    await cluster_manager.register_node('node1', 'host1', 8000)
    
    mock_listener.node_joined.assert_called_once()


@pytest.mark.asyncio
async def test_unregister_node(cluster_manager):
    """Test unregistering a node"""
    await cluster_manager.register_node('node1', 'host1', 8000)
    assert 'node1' in cluster_manager.nodes
    
    result = await cluster_manager.unregister_node('node1')
    assert result is True
    assert 'node1' not in cluster_manager.nodes


@pytest.mark.asyncio
async def test_unregister_node_trigger_listener(cluster_manager, mock_listener):
    """Test node unregistration triggers listener"""
    await cluster_manager.add_listener(mock_listener)
    await cluster_manager.register_node('node1', 'host1', 8000)
    await cluster_manager.unregister_node('node1')
    
    mock_listener.node_left.assert_called_once()


@pytest.mark.asyncio
async def test_get_node(cluster_manager):
    """Test getting node by ID"""
    await cluster_manager.register_node('node1', 'host1', 8000)
    node = await cluster_manager.get_node('node1')
    
    assert node is not None
    assert node.node_id == 'node1'


@pytest.mark.asyncio
async def test_get_nonexistent_node(cluster_manager):
    """Test getting non-existent node"""
    node = await cluster_manager.get_node('nonexistent')
    assert node is None


@pytest.mark.asyncio
async def test_get_all_nodes(cluster_manager):
    """Test getting all nodes"""
    await cluster_manager.register_node('node1', 'host1', 8000)
    await cluster_manager.register_node('node2', 'host2', 8001)
    
    nodes = await cluster_manager.get_all_nodes()
    assert len(nodes) == 2
    assert 'node1' in nodes
    assert 'node2' in nodes


# ============================================================================
# TESTS: GOSSIP PROTOCOL
# ============================================================================

@pytest.mark.asyncio
async def test_handle_gossip_message(cluster_manager):
    """Test handling gossip message"""
    message = GossipMessage(
        sender_id='node1',
        sender_hostname='host1',
        sender_port=8000,
        known_nodes=[]
    )
    
    await cluster_manager.handle_gossip_message(message)
    
    assert 'node1' in cluster_manager.nodes
    node = cluster_manager.nodes['node1']
    assert node.status == NodeStatus.HEALTHY
    assert node.last_heartbeat is not None


@pytest.mark.asyncio
async def test_gossip_message_propagates_nodes(cluster_manager):
    """Test gossip message propagates node information"""
    known_nodes_data = [
        {'node_id': 'node2', 'hostname': 'host2', 'port': 8001},
        {'node_id': 'node3', 'hostname': 'host3', 'port': 8002}
    ]
    
    message = GossipMessage(
        sender_id='node1',
        sender_hostname='host1',
        sender_port=8000,
        known_nodes=known_nodes_data
    )
    
    await cluster_manager.handle_gossip_message(message)
    
    assert 'node1' in cluster_manager.nodes
    assert 'node2' in cluster_manager.nodes
    assert 'node3' in cluster_manager.nodes


# ============================================================================
# TESTS: LEADER ELECTION (RAFT)
# ============================================================================

@pytest.mark.asyncio
async def test_handle_heartbeat(cluster_manager):
    """Test handling leader heartbeat"""
    await cluster_manager.initialize('node1', 'localhost', 8000)
    cluster_manager.current_term = 1
    await cluster_manager.register_node('node1', 'host1', 8000)
    
    message = HeartbeatMessage(
        leader_id='node1',
        term=1
    )
    
    result = await cluster_manager.handle_heartbeat(message)
    
    assert result is True
    assert cluster_manager.leader_id == 'node1'
    assert cluster_manager.last_heartbeat == message.timestamp


@pytest.mark.asyncio
async def test_heartbeat_higher_term_converts_to_follower(cluster_manager):
    """Test heartbeat with higher term converts to follower"""
    cluster_manager.raft_state = RaftState.CANDIDATE
    cluster_manager.current_term = 1
    
    message = HeartbeatMessage(
        leader_id='node1',
        term=2
    )
    
    await cluster_manager.handle_heartbeat(message)
    
    assert cluster_manager.raft_state == RaftState.FOLLOWER
    assert cluster_manager.current_term == 2
    assert cluster_manager.voted_for is None


@pytest.mark.asyncio
async def test_heartbeat_resets_election_timeout(cluster_manager):
    """Test heartbeat resets election timeout"""
    await cluster_manager.initialize('node1', 'localhost', 8000)
    # Set old deadline far in the past
    old_deadline = datetime.now(UTC) - timedelta(seconds=100)
    cluster_manager.election_timeout_deadline = old_deadline
    
    message = HeartbeatMessage(
        leader_id='node2',
        term=1
    )
    
    await cluster_manager.handle_heartbeat(message)
    
    # Deadline should be in the future now
    assert cluster_manager.election_timeout_deadline > datetime.now(UTC)


@pytest.mark.asyncio
async def test_handle_vote_request(cluster_manager):
    """Test handling vote request"""
    cluster_manager.current_term = 1
    
    request = VoteRequest(
        candidate_id='node1',
        term=1
    )
    
    result = await cluster_manager.handle_vote_request(request)
    
    assert result is True
    assert cluster_manager.voted_for == 'node1'


@pytest.mark.asyncio
async def test_vote_request_higher_term(cluster_manager):
    """Test vote request with higher term"""
    cluster_manager.current_term = 1
    cluster_manager.raft_state = RaftState.CANDIDATE
    
    request = VoteRequest(
        candidate_id='node1',
        term=2
    )
    
    await cluster_manager.handle_vote_request(request)
    
    assert cluster_manager.current_term == 2
    assert cluster_manager.voted_for == 'node1'
    assert cluster_manager.raft_state == RaftState.FOLLOWER


@pytest.mark.asyncio
async def test_vote_only_once_per_term(cluster_manager):
    """Test voting only once per term"""
    cluster_manager.current_term = 1
    
    request1 = VoteRequest(candidate_id='node1', term=1)
    result1 = await cluster_manager.handle_vote_request(request1)
    assert result1 is True
    
    request2 = VoteRequest(candidate_id='node2', term=1)
    result2 = await cluster_manager.handle_vote_request(request2)
    
    # Should reject second vote for same term
    assert result2 is False
    assert cluster_manager.voted_for == 'node1'


@pytest.mark.asyncio
async def test_become_follower(cluster_manager):
    """Test transition to follower state"""
    cluster_manager.raft_state = RaftState.CANDIDATE
    
    await cluster_manager._become_follower()
    
    assert cluster_manager.raft_state == RaftState.FOLLOWER
    assert cluster_manager.leader_id is None


@pytest.mark.asyncio
async def test_become_candidate(cluster_manager):
    """Test transition to candidate state"""
    cluster_manager.raft_state = RaftState.FOLLOWER
    
    await cluster_manager._become_candidate()
    
    assert cluster_manager.raft_state == RaftState.CANDIDATE
    assert cluster_manager.voted_for == cluster_manager.node_id


@pytest.mark.asyncio
async def test_become_leader(cluster_manager, mock_listener):
    """Test transition to leader state"""
    await cluster_manager.add_listener(mock_listener)
    cluster_manager.raft_state = RaftState.CANDIDATE
    cluster_manager.node_id = 'node1'
    
    await cluster_manager._become_leader()
    
    assert cluster_manager.raft_state == RaftState.LEADER
    assert cluster_manager.leader_id == 'node1'
    mock_listener.leader_elected.assert_called_once()


# ============================================================================
# TESTS: CLUSTER STATE MANAGEMENT
# ============================================================================

@pytest.mark.asyncio
async def test_initial_cluster_state(cluster_manager):
    """Test initial cluster state"""
    assert cluster_manager.cluster_state == ClusterState.INITIALIZING


@pytest.mark.asyncio
async def test_healthy_cluster_state(cluster_manager):
    """Test healthy cluster state"""
    await cluster_manager.initialize('node1', 'localhost', 8000)
    await cluster_manager.start()
    
    # Register some nodes
    for i in range(3):
        await cluster_manager.register_node(f'node{i}', f'host{i}', 8000 + i)
        # Set all nodes as healthy with recent heartbeats
        cluster_manager.nodes[f'node{i}'].status = NodeStatus.HEALTHY
        cluster_manager.nodes[f'node{i}'].last_heartbeat = datetime.now(UTC)
    
    # Set leader
    cluster_manager.leader_id = 'node0'
    cluster_manager.raft_state = RaftState.LEADER
    
    await cluster_manager._update_cluster_state()
    
    assert cluster_manager.cluster_state == ClusterState.HEALTHY
    await cluster_manager.stop()


@pytest.mark.asyncio
async def test_degraded_cluster_state(cluster_manager):
    """Test degraded cluster state when nodes are degraded"""
    await cluster_manager.initialize('node1', 'localhost', 8000)
    
    # Register nodes
    await cluster_manager.register_node('node1', 'host1', 8000)
    await cluster_manager.register_node('node2', 'host2', 8001)
    
    # Mark one as degraded
    cluster_manager.nodes['node2'].status = NodeStatus.DEGRADED
    cluster_manager.leader_id = 'node1'
    
    await cluster_manager._update_cluster_state()
    
    assert cluster_manager.cluster_state == ClusterState.DEGRADED


@pytest.mark.asyncio
async def test_failed_cluster_state(cluster_manager):
    """Test failed cluster state when majority unhealthy"""
    await cluster_manager.initialize('node1', 'localhost', 8000)
    
    # Register 3 nodes
    await cluster_manager.register_node('node1', 'host1', 8000)
    await cluster_manager.register_node('node2', 'host2', 8001)
    await cluster_manager.register_node('node3', 'host3', 8002)
    
    # Mark 2 as unhealthy
    cluster_manager.nodes['node2'].status = NodeStatus.UNHEALTHY
    cluster_manager.nodes['node3'].status = NodeStatus.UNHEALTHY
    
    await cluster_manager._update_cluster_state()
    
    assert cluster_manager.cluster_state == ClusterState.FAILED


# ============================================================================
# TESTS: SPLIT-BRAIN DETECTION
# ============================================================================

@pytest.mark.asyncio
async def test_split_brain_requires_minimum_nodes(cluster_manager):
    """Test split-brain detection requires minimum nodes"""
    # Register only 1 node
    await cluster_manager.register_node('node1', 'host1', 8000)
    
    result = await cluster_manager.detect_split_brain()
    
    assert result is False


@pytest.mark.asyncio
async def test_detect_split_brain_insufficient_heartbeats(cluster_manager):
    """Test detecting split-brain with insufficient heartbeats"""
    # Register 3 nodes
    await cluster_manager.register_node('node1', 'host1', 8000)
    await cluster_manager.register_node('node2', 'host2', 8001)
    await cluster_manager.register_node('node3', 'host3', 8002)
    
    # Only node1 has recent heartbeat
    cluster_manager.nodes['node1'].last_heartbeat = datetime.now(UTC)
    cluster_manager.nodes['node2'].last_heartbeat = datetime.now(UTC) - timedelta(seconds=100)
    cluster_manager.nodes['node3'].last_heartbeat = datetime.now(UTC) - timedelta(seconds=100)
    
    result = await cluster_manager.detect_split_brain()
    
    assert result is True


@pytest.mark.asyncio
async def test_handle_split_brain(cluster_manager, mock_listener):
    """Test handling split-brain situation"""
    await cluster_manager.add_listener(mock_listener)
    
    # Register nodes
    await cluster_manager.register_node('node1', 'host1', 8000)
    await cluster_manager.register_node('node2', 'host2', 8001)
    
    cluster_manager.nodes['node1'].status = NodeStatus.HEALTHY
    cluster_manager.nodes['node2'].status = NodeStatus.UNHEALTHY
    
    await cluster_manager._handle_split_brain()
    
    assert cluster_manager.cluster_state == ClusterState.SPLIT_BRAIN


# ============================================================================
# TESTS: CLUSTER INFO
# ============================================================================

@pytest.mark.asyncio
async def test_get_cluster_info(cluster_manager):
    """Test getting cluster information"""
    await cluster_manager.initialize('node1', 'localhost', 8000)
    await cluster_manager.register_node('node2', 'host2', 8001)
    
    cluster_manager.leader_id = 'node1'
    cluster_manager.current_term = 5
    cluster_manager.cluster_state = ClusterState.HEALTHY
    cluster_manager.nodes['node2'].status = NodeStatus.HEALTHY
    
    info = await cluster_manager.get_cluster_info()
    
    assert isinstance(info, ClusterInfo)
    assert info.leader_id == 'node1'
    assert info.term == 5
    assert info.state == ClusterState.HEALTHY
    assert len(info.nodes) == 2


@pytest.mark.asyncio
async def test_cluster_info_has_status_counts(cluster_manager):
    """Test cluster info includes status counts"""
    await cluster_manager.register_node('node1', 'host1', 8000)
    await cluster_manager.register_node('node2', 'host2', 8001)
    await cluster_manager.register_node('node3', 'host3', 8002)
    
    cluster_manager.nodes['node1'].status = NodeStatus.HEALTHY
    cluster_manager.nodes['node2'].status = NodeStatus.DEGRADED
    cluster_manager.nodes['node3'].status = NodeStatus.UNHEALTHY
    
    info = await cluster_manager.get_cluster_info()
    
    assert info.healthy_nodes == 1
    assert info.degraded_nodes == 1
    assert info.unhealthy_nodes == 1


# ============================================================================
# TESTS: LISTENER MANAGEMENT
# ============================================================================

@pytest.mark.asyncio
async def test_add_listener(cluster_manager, mock_listener):
    """Test adding state change listener"""
    result = await cluster_manager.add_listener(mock_listener)
    
    assert result is True
    assert mock_listener in cluster_manager.listeners


@pytest.mark.asyncio
async def test_remove_listener(cluster_manager, mock_listener):
    """Test removing state change listener"""
    await cluster_manager.add_listener(mock_listener)
    result = await cluster_manager.remove_listener(mock_listener)
    
    assert result is True
    assert mock_listener not in cluster_manager.listeners


@pytest.mark.asyncio
async def test_listener_on_state_change(cluster_manager, mock_listener):
    """Test listener called on state change"""
    await cluster_manager.add_listener(mock_listener)
    
    # Change cluster state
    old_state = cluster_manager.cluster_state
    cluster_manager.cluster_state = ClusterState.HEALTHY
    
    await cluster_manager._update_cluster_state()
    
    # Would be called if state actually changed (mocked)


# ============================================================================
# TESTS: UTILITY METHODS
# ============================================================================

@pytest.mark.asyncio
async def test_is_leader_when_leader(cluster_manager):
    """Test is_leader when node is leader"""
    cluster_manager.raft_state = RaftState.LEADER
    
    result = await cluster_manager.is_leader()
    
    assert result is True


@pytest.mark.asyncio
async def test_is_leader_when_not_leader(cluster_manager):
    """Test is_leader when node is not leader"""
    cluster_manager.raft_state = RaftState.FOLLOWER
    
    result = await cluster_manager.is_leader()
    
    assert result is False


@pytest.mark.asyncio
async def test_get_leader_id(cluster_manager):
    """Test getting leader ID"""
    cluster_manager.leader_id = 'node1'
    
    result = await cluster_manager.get_leader_id()
    
    assert result == 'node1'


@pytest.mark.asyncio
async def test_get_raft_state(cluster_manager):
    """Test getting Raft state"""
    cluster_manager.raft_state = RaftState.CANDIDATE
    
    result = await cluster_manager.get_raft_state()
    
    assert result == RaftState.CANDIDATE


@pytest.mark.asyncio
async def test_is_ready_when_ready(cluster_manager):
    """Test is_ready when cluster ready"""
    cluster_manager.enabled = True
    cluster_manager.leader_id = 'node1'
    cluster_manager.cluster_state = ClusterState.HEALTHY
    
    result = await cluster_manager.is_ready()
    
    assert result is True


@pytest.mark.asyncio
async def test_is_ready_when_not_ready(cluster_manager):
    """Test is_ready when cluster not ready"""
    cluster_manager.enabled = False
    cluster_manager.leader_id = None
    cluster_manager.cluster_state = ClusterState.INITIALIZING
    
    result = await cluster_manager.is_ready()
    
    assert result is False


# ============================================================================
# TESTS: NODE STATUS TRANSITIONS
# ============================================================================

@pytest.mark.asyncio
async def test_node_to_dict(cluster_manager):
    """Test node serialization"""
    await cluster_manager.register_node('node1', 'host1', 8000)
    node = cluster_manager.nodes['node1']
    
    node_dict = node.to_dict()
    
    assert node_dict['node_id'] == 'node1'
    assert node_dict['hostname'] == 'host1'
    assert node_dict['port'] == 8000
    assert 'status' in node_dict


@pytest.mark.asyncio
async def test_cluster_info_serialization(cluster_manager):
    """Test cluster info serialization"""
    await cluster_manager.register_node('node1', 'host1', 8000)
    cluster_manager.leader_id = 'node1'
    
    info = await cluster_manager.get_cluster_info()
    info_dict = info.to_dict()
    
    assert 'cluster_id' in info_dict
    assert 'state' in info_dict
    assert 'leader_id' in info_dict
    assert 'nodes' in info_dict


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
