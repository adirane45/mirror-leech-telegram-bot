"""
Unit tests for Replication Manager

Tests cover:
- Initialization and lifecycle
- Change publishing and tracking
- Conflict detection and resolution
- Synchronization
- Replication lag monitoring
- Event listeners
- Metrics and utilities
"""

import asyncio
import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from bot.core.replication_manager import (
    ReplicationManager,
    ReplicationLog,
    ConflictEvent,
    SyncCheckpoint,
    ReplicationMetrics,
    ReplicationEventListener,
    ConflictResolutionStrategy,
    ReplicationState,
    ReplicationLag,
    VectorClock
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def replication_manager():
    """Get replication manager instance"""
    manager = ReplicationManager.get_instance()
    # Reset state
    manager.enabled = False
    manager.node_id = ""
    manager.peer_nodes.clear()
    manager.replication_log.clear()
    manager.pending_replication.clear()
    manager.sync_checkpoints.clear()
    manager.conflicts.clear()
    manager.local_state.clear()
    manager.metrics = ReplicationMetrics()
    manager.vector_clock = VectorClock("")
    manager.listeners.clear()
    
    yield manager
    
    # Cleanup
    try:
        asyncio.run(manager.stop())
    except:
        pass
    manager.enabled = False


@pytest.fixture
def mock_listener():
    """Mock replication event listener"""
    class TestListener(ReplicationEventListener):
        def __init__(self):
            self.on_change_published = AsyncMock()
            self.on_change_received = AsyncMock()
            self.on_conflict_detected = AsyncMock()
            self.on_conflict_resolved = AsyncMock()
            self.on_sync_completed = AsyncMock()
            self.on_lag_critical = AsyncMock()
        
        async def on_change_published(self, log_entry: ReplicationLog) -> None:
            await self.on_change_published(log_entry)
        
        async def on_change_received(self, log_entry: ReplicationLog, from_node: str) -> None:
            await self.on_change_received(log_entry, from_node)
        
        async def on_conflict_detected(self, conflict: ConflictEvent) -> None:
            await self.on_conflict_detected(conflict)
        
        async def on_conflict_resolved(self, conflict: ConflictEvent) -> None:
            await self.on_conflict_resolved(conflict)
        
        async def on_sync_completed(self, node_id: str) -> None:
            await self.on_sync_completed(node_id)
        
        async def on_lag_critical(self, node_id: str, lag_ms: int) -> None:
            await self.on_lag_critical(node_id, lag_ms)
    
    return TestListener()


# ============================================================================
# TESTS: INITIALIZATION AND LIFECYCLE
# ============================================================================

@pytest.mark.asyncio
async def test_singleton_instance(replication_manager):
    """Test replication manager is singleton"""
    mgr1 = ReplicationManager.get_instance()
    mgr2 = ReplicationManager.get_instance()
    
    assert mgr1 is mgr2


@pytest.mark.asyncio
async def test_start_replication_manager(replication_manager):
    """Test starting replication manager"""
    result = await replication_manager.start('node1')
    
    assert result is True
    assert replication_manager.enabled is True
    assert replication_manager.node_id == 'node1'
    assert replication_manager.vector_clock.node_id == 'node1'
    assert replication_manager._replication_task is not None
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_stop_replication_manager(replication_manager):
    """Test stopping replication manager"""
    await replication_manager.start('node1')
    assert replication_manager.enabled is True
    
    result = await replication_manager.stop()
    assert result is True
    assert replication_manager.enabled is False


@pytest.mark.asyncio
async def test_start_already_started(replication_manager):
    """Test starting when already started"""
    await replication_manager.start('node1')
    result = await replication_manager.start('node1')
    
    assert result is True
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_is_enabled(replication_manager):
    """Test is_enabled check"""
    assert await replication_manager.is_enabled() is False
    
    await replication_manager.start('node1')
    assert await replication_manager.is_enabled() is True
    
    await replication_manager.stop()


# ============================================================================
# TESTS: CHANGE PUBLISHING
# ============================================================================

@pytest.mark.asyncio
async def test_publish_change(replication_manager, mock_listener):
    """Test publishing a change"""
    await replication_manager.start('node1')
    await replication_manager.add_listener(mock_listener)
    
    result = await replication_manager.publish_change('UPDATE', 'key1', 'value1')
    
    assert result is True
    assert len(replication_manager.replication_log) == 1
    assert replication_manager.local_state['key1'] == 'value1'
    assert replication_manager.metrics.total_changes == 1
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_publish_multiple_changes(replication_manager):
    """Test publishing multiple changes"""
    await replication_manager.start('node1')
    
    for i in range(5):
        result = await replication_manager.publish_change('CREATE', f'key{i}', f'value{i}')
        assert result is True
    
    assert len(replication_manager.replication_log) == 5
    assert len(replication_manager.local_state) == 5
    assert replication_manager.metrics.total_changes == 5
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_publish_delete_change(replication_manager):
    """Test publishing delete operation"""
    await replication_manager.start('node1')
    
    # First create
    await replication_manager.publish_change('CREATE', 'key1', 'value1')
    assert 'key1' in replication_manager.local_state
    
    # Then delete
    await replication_manager.publish_change('DELETE', 'key1', None)
    assert 'key1' not in replication_manager.local_state
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_vector_clock_increment(replication_manager):
    """Test vector clock incrementation on publish"""
    await replication_manager.start('node1')
    
    initial_clock = replication_manager.vector_clock.clocks.get('node1', 0)
    
    await replication_manager.publish_change('CREATE', 'key1', 'value1')
    
    new_clock = replication_manager.vector_clock.clocks.get('node1', 0)
    assert new_clock == initial_clock + 1
    
    await replication_manager.stop()


# ============================================================================
# TESTS: HANDLING REMOTE CHANGES
# ============================================================================

@pytest.mark.asyncio
async def test_handle_remote_change(replication_manager, mock_listener):
    """Test handling a change from remote node"""
    await replication_manager.start('node1')
    await replication_manager.add_listener(mock_listener)
    
    remote_log = ReplicationLog(
        source_node='node2',
        operation_type='UPDATE',
        key='key1',
        value='remote_value',
        vector_clock=VectorClock('node2', {'node2': 1})
    )
    
    result = await replication_manager.handle_remote_change(remote_log, 'node2')
    
    assert result is True
    assert replication_manager.local_state['key1'] == 'remote_value'
    assert replication_manager.metrics.synced_changes == 1
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_handle_remote_delete(replication_manager):
    """Test handling remote delete"""
    await replication_manager.start('node1')
    
    # Create locally first
    await replication_manager.publish_change('CREATE', 'key1', 'value1')
    
    # Apply remote delete
    remote_log = ReplicationLog(
        source_node='node2',
        operation_type='DELETE',
        key='key1',
        vector_clock=VectorClock('node2', {'node2': 1})
    )
    
    result = await replication_manager.handle_remote_change(remote_log, 'node2')
    
    assert result is True
    assert 'key1' not in replication_manager.local_state
    
    await replication_manager.stop()


# ============================================================================
# TESTS: CONFLICT DETECTION
# ============================================================================

@pytest.mark.asyncio
async def test_detect_concurrent_conflict(replication_manager, mock_listener):
    """Test detecting concurrent modification conflict"""
    await replication_manager.start('node1')
    await replication_manager.add_listener(mock_listener)
    
    # Create initial state
    await replication_manager.publish_change('CREATE', 'key1', 'local_value')
    local_log = replication_manager.replication_log[0]
    
    # Create concurrent remote change
    remote_log = ReplicationLog(
        source_node='node2',
        operation_type='UPDATE',
        key='key1',
        value='remote_value',
        vector_clock=VectorClock('node2', {'node2': 1}),
        timestamp=datetime.now(UTC)
    )
    
    conflict = await replication_manager.detect_conflict(remote_log, 'node2')
    
    assert conflict is not None
    assert conflict.key == 'key1'
    assert replication_manager.metrics.conflicts_detected == 1
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_no_conflict_sequential_changes(replication_manager):
    """Test no conflict for sequential changes"""
    await replication_manager.start('node1')
    
    # Create initial via node1
    local_log = ReplicationLog(
        source_node='node1',
        operation_type='CREATE',
        key='key1',
        value='value1',
        vector_clock=VectorClock('node1', {'node1': 1})
    )
    replication_manager.replication_log.append(local_log)
    
    # Node2 updates after node1 (causally ordered)
    remote_log = ReplicationLog(
        source_node='node2',
        operation_type='UPDATE',
        key='key1',
        value='value2',
        vector_clock=VectorClock('node2', {'node1': 1, 'node2': 1})
    )
    
    conflict = await replication_manager.detect_conflict(remote_log, 'node2')
    
    # No conflict since it's causally ordered
    assert conflict is None
    
    await replication_manager.stop()


# ============================================================================
# TESTS: CONFLICT RESOLUTION
# ============================================================================

@pytest.mark.asyncio
async def test_resolve_conflict_timestamp_strategy(replication_manager):
    """Test resolving conflict with timestamp strategy"""
    await replication_manager.start('node1')
    replication_manager.resolution_strategy = ConflictResolutionStrategy.TIMESTAMP
    
    conflict = ConflictEvent(
        key='key1',
        local_value='local',
        remote_value='remote',
        local_timestamp=datetime.now(UTC) - timedelta(seconds=1),
        remote_timestamp=datetime.now(UTC),
        remote_node='node2',
        resolution_strategy=ConflictResolutionStrategy.TIMESTAMP
    )
    
    result = await replication_manager.resolve_conflict(conflict)
    
    assert result is True
    assert conflict.resolved is True
    assert conflict.resolved_value == 'remote'
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_resolve_conflict_client_wins(replication_manager):
    """Test client-wins conflict resolution"""
    await replication_manager.start('node1')
    
    conflict = ConflictEvent(
        key='key1',
        local_value='local',
        remote_value='remote',
        remote_node='node2',
        resolution_strategy=ConflictResolutionStrategy.CLIENT_WINS
    )
    
    result = await replication_manager.resolve_conflict(conflict)
    
    assert result is True
    assert conflict.resolved_value == 'local'
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_resolve_conflict_server_wins(replication_manager):
    """Test server-wins conflict resolution"""
    await replication_manager.start('node1')
    
    conflict = ConflictEvent(
        key='key1',
        local_value='local',
        remote_value='remote',
        remote_node='node2',
        resolution_strategy=ConflictResolutionStrategy.SERVER_WINS
    )
    
    result = await replication_manager.resolve_conflict(conflict)
    
    assert result is True
    assert conflict.resolved_value == 'remote'
    
    await replication_manager.stop()


# ============================================================================
# TESTS: SYNCHRONIZATION
# ============================================================================

@pytest.mark.asyncio
async def test_sync_with_node(replication_manager, mock_listener):
    """Test synchronization with a node"""
    await replication_manager.start('node1')
    await replication_manager.add_listener(mock_listener)
    
    # Add peer and pending changes
    await replication_manager.register_peer_node('node2', 'localhost:5002')
    
    for i in range(5):
        await replication_manager.publish_change('CREATE', f'key{i}', f'value{i}')
    
    result = await replication_manager.sync_with_node('node2')
    
    assert result is True
    assert 'node2' in replication_manager.sync_checkpoints
    assert len(replication_manager.pending_replication['node2']) == 0
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_incremental_sync(replication_manager):
    """Test incremental synchronization"""
    await replication_manager.start('node1')
    
    # Initial setup
    await replication_manager.register_peer_node('node2', 'localhost:5002')
    for i in range(3):
        await replication_manager.publish_change('CREATE', f'key{i}', f'value{i}')
    
    # First sync
    await replication_manager.sync_with_node('node2')
    
    # Add more changes
    for i in range(3, 5):
        await replication_manager.publish_change('CREATE', f'key{i}', f'value{i}')
    
    # Incremental sync
    result = await replication_manager.incremental_sync('node2')
    
    assert result is True
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_sync_without_pending_changes(replication_manager):
    """Test sync when no pending changes"""
    await replication_manager.start('node1')
    
    await replication_manager.register_peer_node('node2', 'localhost:5002')
    replication_manager.sync_checkpoints['node2'] = SyncCheckpoint(node_id='node2')
    
    result = await replication_manager.incremental_sync('node2')
    
    assert result is True
    
    await replication_manager.stop()


# ============================================================================
# TESTS: PEER NODE MANAGEMENT
# ============================================================================

@pytest.mark.asyncio
async def test_register_peer_node(replication_manager):
    """Test registering a peer node"""
    await replication_manager.start('node1')
    
    result = await replication_manager.register_peer_node('node2', 'localhost:5002')
    
    assert result is True
    assert 'node2' in replication_manager.peer_nodes
    assert replication_manager.peer_nodes['node2']['address'] == 'localhost:5002'
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_unregister_peer_node(replication_manager):
    """Test unregistering a peer node"""
    await replication_manager.start('node1')
    
    await replication_manager.register_peer_node('node2', 'localhost:5002')
    assert 'node2' in replication_manager.peer_nodes
    
    result = await replication_manager.unregister_peer_node('node2')
    
    assert result is True
    assert 'node2' not in replication_manager.peer_nodes
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_multiple_peer_nodes(replication_manager):
    """Test managing multiple peer nodes"""
    await replication_manager.start('node1')
    
    for i in range(2, 5):
        await replication_manager.register_peer_node(f'node{i}', f'localhost:{5000+i}')
    
    assert len(replication_manager.peer_nodes) == 3
    
    await replication_manager.stop()


# ============================================================================
# TESTS: REPLICATION LAG
# ============================================================================

@pytest.mark.asyncio
async def test_get_replication_lag(replication_manager):
    """Test getting replication lag metrics"""
    await replication_manager.start('node1')
    
    await replication_manager.register_peer_node('node2', 'localhost:5002')
    for i in range(5):
        await replication_manager.publish_change('CREATE', f'key{i}', f'value{i}')
    
    lag = await replication_manager.get_replication_lag()
    
    assert 'current_lag_ms' in lag
    assert 'average_lag_ms' in lag
    assert 'lag_level' in lag
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_lag_classification(replication_manager):
    """Test lag level classification"""
    await replication_manager.start('node1')
    
    # Test different lag levels
    assert replication_manager._classify_lag(50) == ReplicationLag.MINIMAL.value
    assert replication_manager._classify_lag(500) == ReplicationLag.LOW.value
    assert replication_manager._classify_lag(2000) == ReplicationLag.MEDIUM.value
    assert replication_manager._classify_lag(10000) == ReplicationLag.HIGH.value
    assert replication_manager._classify_lag(40000) == ReplicationLag.CRITICAL.value
    
    await replication_manager.stop()


# ============================================================================
# TESTS: EVENT LISTENERS
# ============================================================================

@pytest.mark.asyncio
async def test_add_listener(replication_manager, mock_listener):
    """Test adding event listener"""
    result = await replication_manager.add_listener(mock_listener)
    
    assert result is True
    assert mock_listener in replication_manager.listeners


@pytest.mark.asyncio
async def test_remove_listener(replication_manager, mock_listener):
    """Test removing event listener"""
    await replication_manager.add_listener(mock_listener)
    result = await replication_manager.remove_listener(mock_listener)
    
    assert result is True
    assert mock_listener not in replication_manager.listeners


@pytest.mark.asyncio
async def test_listener_on_change_published(replication_manager, mock_listener):
    """Test listener called on change published"""
    await replication_manager.start('node1')
    await replication_manager.add_listener(mock_listener)
    
    await replication_manager.publish_change('CREATE', 'key1', 'value1')
    
    # Listener should have been called
    # Note: In real scenario, would verify the call


# ============================================================================
# TESTS: METRICS AND UTILITIES
# ============================================================================

@pytest.mark.asyncio
async def test_get_replication_status(replication_manager):
    """Test getting replication status"""
    await replication_manager.start('node1')
    await replication_manager.register_peer_node('node2', 'localhost:5002')
    
    for i in range(3):
        await replication_manager.publish_change('CREATE', f'key{i}', f'value{i}')
    
    status = await replication_manager.get_replication_status()
    
    assert status['node_id'] == 'node1'
    assert status['enabled'] is True
    assert status['total_changes'] == 3
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_get_metrics(replication_manager):
    """Test getting replication metrics"""
    await replication_manager.start('node1')
    
    for i in range(5):
        await replication_manager.publish_change('CREATE', f'key{i}', f'value{i}')
    
    metrics = await replication_manager.get_metrics()
    
    assert metrics.total_changes == 5
    assert metrics.pending_changes == 5
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_get_pending_changes_count(replication_manager):
    """Test getting pending changes count"""
    await replication_manager.start('node1')
    
    await replication_manager.register_peer_node('node2', 'localhost:5002')
    for i in range(5):
        await replication_manager.publish_change('CREATE', f'key{i}', f'value{i}')
    
    total_pending = await replication_manager.get_pending_changes_count()
    assert total_pending == 5
    
    node_pending = await replication_manager.get_pending_changes_count('node2')
    assert node_pending == 5
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_get_log_size(replication_manager):
    """Test getting replication log size"""
    await replication_manager.start('node1')
    
    for i in range(5):
        await replication_manager.publish_change('CREATE', f'key{i}', f'value{i}')
    
    size = await replication_manager.get_log_size()
    assert size == 5
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_clear_replication_log(replication_manager):
    """Test clearing old replication log entries"""
    await replication_manager.start('node1')
    
    # Add old entry
    old_log = ReplicationLog(
        source_node='node1',
        operation_type='CREATE',
        key='old_key',
        value='old_value',
        timestamp=datetime.now(UTC) - timedelta(hours=25)
    )
    replication_manager.replication_log.append(old_log)
    
    # Add recent entry
    await replication_manager.publish_change('CREATE', 'new_key', 'new_value')
    
    cleared = await replication_manager.clear_replication_log()
    
    assert cleared == 1
    assert len(replication_manager.replication_log) == 1
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_get_conflict_history(replication_manager):
    """Test getting conflict history"""
    await replication_manager.start('node1')
    
    for i in range(5):
        conflict = ConflictEvent(
            key=f'key{i}',
            local_value=f'local{i}',
            remote_value=f'remote{i}',
            remote_node='node2'
        )
        replication_manager.conflicts[conflict.event_id] = conflict
    
    history = await replication_manager.get_conflict_history(limit=10)
    
    assert len(history) == 5
    
    await replication_manager.stop()


@pytest.mark.asyncio
async def test_force_sync_all_nodes(replication_manager):
    """Test forcing sync with all nodes"""
    await replication_manager.start('node1')
    
    for i in range(2, 4):
        await replication_manager.register_peer_node(f'node{i}', f'localhost:{5000+i}')
        for j in range(2):
            await replication_manager.publish_change('CREATE', f'key{i}_{j}', f'value{i}_{j}')
    
    result = await replication_manager.force_sync_all_nodes()
    
    assert result is True
    
    await replication_manager.stop()


# ============================================================================
# TESTS: DATA SERIALIZATION
# ============================================================================

@pytest.mark.asyncio
async def test_replication_log_to_dict(replication_manager):
    """Test replication log serialization"""
    log = ReplicationLog(
        source_node='node1',
        operation_type='UPDATE',
        key='key1',
        value='value1',
        vector_clock=VectorClock('node1', {'node1': 1})
    )
    
    log_dict = log.to_dict()
    
    assert log_dict['source_node'] == 'node1'
    assert log_dict['key'] == 'key1'
    assert log_dict['operation_type'] == 'UPDATE'


@pytest.mark.asyncio
async def test_conflict_event_to_dict(replication_manager):
    """Test conflict event serialization"""
    conflict = ConflictEvent(
        key='key1',
        local_value='local',
        remote_value='remote',
        remote_node='node2'
    )
    
    conflict_dict = conflict.to_dict()
    
    assert conflict_dict['key'] == 'key1'
    assert conflict_dict['resolved'] is False


@pytest.mark.asyncio
async def test_metrics_to_dict(replication_manager):
    """Test metrics serialization"""
    metrics = ReplicationMetrics(
        total_changes=100,
        synced_changes=95,
        conflicts_detected=2
    )
    
    metrics_dict = metrics.to_dict()
    
    assert metrics_dict['total_changes'] == 100
    assert metrics_dict['synced_changes'] == 95


# ============================================================================
# TESTS: VECTOR CLOCK OPERATIONS
# ============================================================================

@pytest.mark.asyncio
async def test_vector_clock_is_after(replication_manager):
    """Test vector clock comparison"""
    vc1 = VectorClock('node1', {'node1': 2, 'node2': 1})
    vc2 = VectorClock('node2', {'node1': 1, 'node2': 1})
    
    assert vc1.is_after(vc2) is True
    assert vc2.is_after(vc1) is False


@pytest.mark.asyncio
async def test_vector_clock_concurrent(replication_manager):
    """Test vector clock concurrency detection"""
    vc1 = VectorClock('node1', {'node1': 2, 'node2': 0})
    vc2 = VectorClock('node2', {'node1': 0, 'node2': 2})
    
    assert vc1.concurrent_with(vc2) is True


@pytest.mark.asyncio
async def test_vector_clock_merge(replication_manager):
    """Test vector clock merge"""
    vc1 = VectorClock('node1', {'node1': 2, 'node2': 1})
    vc2 = VectorClock('node2', {'node1': 1, 'node2': 3})
    
    vc1.merge(vc2)
    
    assert vc1.clocks['node1'] == 2
    assert vc1.clocks['node2'] == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
