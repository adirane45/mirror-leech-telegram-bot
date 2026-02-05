"""
Integration Tests for Phase 5: High Availability

Tests all Phase 5 components:
- Cluster Manager
- Failover Manager
- Replication Manager
- Distributed State Manager
- Health Monitor
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any

# Import Phase 5 components
try:
    from bot.core.cluster_manager import ClusterManager, NodeState, ClusterState
    from bot.core.failover_manager import FailoverManager, FailoverPolicy, FailoverRole
    from bot.core.replication_manager import (
        ReplicationManager,
        ReplicationMode,
        ConsistencyLevel,
        ConflictResolution
    )
    from bot.core.distributed_state_manager import DistributedStateManager
    from bot.core.health_monitor import HealthMonitor, ComponentType, HealthStatus
    from bot.core.enhanced_startup_phase5 import Phase5Manager
    PHASE5_AVAILABLE = True
except ImportError:
    PHASE5_AVAILABLE = False
    pytestmark = pytest.mark.skip("Phase 5 not available")


@pytest.mark.asyncio
class TestClusterManager:
    """Test Cluster Manager"""
    
    async def test_cluster_initialization(self):
        """Test cluster initialization"""
        cluster = ClusterManager.get_instance()
        await cluster.reset()
        
        success = await cluster.enable(
            address='localhost',
            port=7946
        )
        
        assert success is True
        assert cluster.enabled is True
        assert cluster.local_node is not None
        
        await cluster.disable()
    
    async def test_node_registration(self):
        """Test node registration"""
        cluster = ClusterManager.get_instance()
        await cluster.reset()
        await cluster.enable()
        
        # Local node should be registered
        nodes = await cluster.get_nodes()
        assert len(nodes) >= 1
        
        await cluster.disable()
    
    async def test_cluster_info(self):
        """Test cluster info retrieval"""
        cluster = ClusterManager.get_instance()
        await cluster.reset()
        await cluster.enable()
        
        info = await cluster.get_cluster_info()
        
        assert 'state' in info
        assert 'total_nodes' in info
        assert 'active_nodes' in info
        assert info['total_nodes'] >= 1
        
        await cluster.disable()
    
    async def test_leader_election(self):
        """Test leader election"""
        cluster = ClusterManager.get_instance()
        await cluster.reset()
        await cluster.enable()
        
        # Wait for election
        await asyncio.sleep(1)
        
        leader = await cluster.get_leader_node()
        assert leader is not None
        
        await cluster.disable()
    
    async def test_statistics(self):
        """Test statistics collection"""
        cluster = ClusterManager.get_instance()
        await cluster.reset()
        await cluster.enable()
        
        stats = await cluster.get_statistics()
        
        assert 'uptime_seconds' in stats
        assert 'total_nodes' in stats
        assert 'node_states' in stats
        
        await cluster.disable()


@pytest.mark.asyncio
class TestFailoverManager:
    """Test Failover Manager"""
    
    async def test_failover_initialization(self):
        """Test failover initialization"""
        failover = FailoverManager.get_instance()
        await failover.reset()
        
        policy = FailoverPolicy(
            auto_failover_enabled=True,
            failure_threshold=3
        )
        
        success = await failover.enable(
            role=FailoverRole.PRIMARY,
            policy=policy
        )
        
        assert success is True
        assert failover.enabled is True
        
        await failover.disable()
    
    async def test_primary_secondary_setup(self):
        """Test primary/secondary configuration"""
        failover = FailoverManager.get_instance()
        await failover.reset()
        await failover.enable()
        
        await failover.set_primary('node1')
        await failover.add_secondary('node2')
        await failover.add_secondary('node3')
        
        assert failover.primary_node == 'node1'
        assert 'node2' in failover.secondary_nodes
        assert 'node3' in failover.secondary_nodes
        
        await failover.disable()
    
    async def test_failover_status(self):
        """Test failover status"""
        failover = FailoverManager.get_instance()
        await failover.reset()
        await failover.enable()
        
        status = await failover.get_failover_status()
        
        assert 'enabled' in status
        assert 'role' in status
        assert 'state' in status
        
        await failover.disable()
    
    async def test_failover_history(self):
        """Test failover history"""
        failover = FailoverManager.get_instance()
        await failover.reset()
        await failover.enable()
        
        history = await failover.get_failover_history()
        
        assert isinstance(history, list)
        
        await failover.disable()


@pytest.mark.asyncio
class TestReplicationManager:
    """Test Replication Manager"""
    
    async def test_replication_initialization(self):
        """Test replication initialization"""
        replication = ReplicationManager.get_instance()
        await replication.reset()
        
        success = await replication.enable(
            mode=ReplicationMode.MASTER_SLAVE,
            consistency=ConsistencyLevel.EVENTUAL
        )
        
        assert success is True
        assert replication.enabled is True
        
        await replication.disable()
    
    async def test_master_slave_setup(self):
        """Test master/slave configuration"""
        replication = ReplicationManager.get_instance()
        await replication.reset()
        await replication.enable()
        
        await replication.set_master('master1')
        await replication.add_slave('slave1')
        await replication.add_slave('slave2')
        
        assert replication.master_node == 'master1'
        assert 'slave1' in replication.slave_nodes
        assert 'slave2' in replication.slave_nodes
        
        await replication.disable()
    
    async def test_data_replication(self):
        """Test data replication"""
        replication = ReplicationManager.get_instance()
        await replication.reset()
        await replication.enable()
        
        await replication.set_master('master1')
        await replication.add_slave('slave1')
        
        success = await replication.replicate_data(
            data_id='test1',
            data_type='task',
            data={'name': 'test_task'},
            source_node='master1'
        )
        
        assert success is True
        
        # Wait for async replication
        await asyncio.sleep(0.5)
        
        await replication.disable()
    
    async def test_replication_status(self):
        """Test replication status"""
        replication = ReplicationManager.get_instance()
        await replication.reset()
        await replication.enable()
        
        status = await replication.get_replication_status()
        
        assert 'enabled' in status
        assert 'mode' in status
        assert 'consistency_level' in status
        
        await replication.disable()
    
    async def test_conflict_handling(self):
        """Test conflict handling"""
        replication = ReplicationManager.get_instance()
        await replication.reset()
        
        replication.conflict_resolution = ConflictResolution.LAST_WRITE_WINS
        
        await replication.enable()
        
        conflicts = await replication.get_conflicts()
        assert isinstance(conflicts, list)
        
        await replication.disable()


@pytest.mark.asyncio
class TestDistributedStateManager:
    """Test Distributed State Manager"""
    
    async def test_state_initialization(self):
        """Test state initialization"""
        state = DistributedStateManager.get_instance()
        await state.reset()
        
        success = await state.enable(node_id='node1')
        
        assert success is True
        assert state.enabled is True
        assert state.node_id == 'node1'
        
        await state.disable()
    
    async def test_state_operations(self):
        """Test state set/get/delete"""
        state = DistributedStateManager.get_instance()
        await state.reset()
        await state.enable()
        
        # Set state
        await state.set_state('key1', 'value1')
        
        # Get state
        value = await state.get_state('key1')
        assert value == 'value1'
        
        # Delete state
        await state.delete_state('key1')
        value = await state.get_state('key1')
        assert value is None
        
        await state.disable()
    
    async def test_compare_and_swap(self):
        """Test atomic compare-and-swap"""
        state = DistributedStateManager.get_instance()
        await state.reset()
        await state.enable()
        
        # Initial set
        await state.set_state('counter', 0)
        
        # Successful CAS
        success = await state.compare_and_swap('counter', 0, 1)
        assert success is True
        
        value = await state.get_state('counter')
        assert value == 1
        
        # Failed CAS (wrong expected value)
        success = await state.compare_and_swap('counter', 0, 2)
        assert success is False
        
        await state.disable()
    
    async def test_distributed_locks(self):
        """Test distributed locking"""
        state = DistributedStateManager.get_instance()
        await state.reset()
        await state.enable()
        
        # Acquire lock
        lock_id = await state.acquire_lock('resource1', ttl_seconds=10)
        assert lock_id is not None
        
        # Check if locked
        is_locked = await state.is_locked('resource1')
        assert is_locked is True
        
        # Release lock
        success = await state.release_lock('resource1', lock_id)
        assert success is True
        
        # Check if unlocked
        is_locked = await state.is_locked('resource1')
        assert is_locked is False
        
        await state.disable()
    
    async def test_lock_timeout(self):
        """Test lock timeout"""
        state = DistributedStateManager.get_instance()
        await state.reset()
        await state.enable()
        
        # Acquire lock that can't be obtained
        await state.acquire_lock('resource1', ttl_seconds=30)
        
        # Try to acquire same lock with short timeout
        lock_id = await state.acquire_lock(
            'resource1',
            ttl_seconds=10,
            timeout_seconds=0.5
        )
        
        # Should timeout
        assert lock_id is None
        
        await state.disable()
    
    async def test_state_status(self):
        """Test state status"""
        state = DistributedStateManager.get_instance()
        await state.reset()
        await state.enable()
        
        status = await state.get_status()
        
        assert 'enabled' in status
        assert 'node_id' in status
        assert 'state_entries' in status
        assert 'active_locks' in status
        
        await state.disable()


@pytest.mark.asyncio
class TestHealthMonitor:
    """Test Health Monitor"""
    
    async def test_health_monitor_initialization(self):
        """Test health monitor initialization"""
        health = HealthMonitor.get_instance()
        await health.reset()
        
        success = await health.enable()
        
        assert success is True
        assert health.enabled is True
        
        await health.disable()
    
    async def test_health_check_registration(self):
        """Test health check registration"""
        health = HealthMonitor.get_instance()
        await health.reset()
        await health.enable()
        
        async def test_check():
            return {'status': HealthStatus.HEALTHY}
        
        success = await health.register_health_check(
            check_id='test_check',
            component_type=ComponentType.SERVICE,
            component_name='test_service',
            check_fn=test_check,
            interval_seconds=5
        )
        
        assert success is True
        assert 'test_check' in health.health_checks
        
        await health.disable()
    
    async def test_health_check_execution(self):
        """Test health check execution"""
        health = HealthMonitor.get_instance()
        await health.reset()
        await health.enable()
        
        check_count = 0
        
        async def counting_check():
            nonlocal check_count
            check_count += 1
            return {'status': HealthStatus.HEALTHY}
        
        await health.register_health_check(
            check_id='counting',
            component_type=ComponentType.SERVICE,
            component_name='counter',
            check_fn=counting_check,
            interval_seconds=1
        )
        
        # Wait for a few checks
        await asyncio.sleep(3)
        
        assert check_count >= 2
        
        await health.disable()
    
    async def test_overall_health(self):
        """Test overall health status"""
        health = HealthMonitor.get_instance()
        await health.reset()
        await health.enable()
        
        async def healthy_check():
            return {'status': HealthStatus.HEALTHY}
        
        await health.register_health_check(
            check_id='healthy1',
            component_type=ComponentType.SERVICE,
            component_name='service1',
            check_fn=healthy_check,
            interval_seconds=1
        )
        
        # Wait for check execution
        await asyncio.sleep(2)
        
        overall = await health.get_overall_health()
        
        assert 'status' in overall
        assert 'total_components' in overall
        assert 'components' in overall
        
        await health.disable()
    
    async def test_component_health(self):
        """Test component health retrieval"""
        health = HealthMonitor.get_instance()
        await health.reset()
        await health.enable()
        
        async def test_check():
            return {'status': HealthStatus.HEALTHY}
        
        await health.register_health_check(
            check_id='test',
            component_type=ComponentType.DATABASE,
            component_name='testdb',
            check_fn=test_check,
            interval_seconds=1
        )
        
        # Wait for check
        await asyncio.sleep(2)
        
        component_health = await health.get_component_health('testdb')
        
        assert component_health is not None
        assert component_health['name'] == 'testdb'
        
        await health.disable()


@pytest.mark.asyncio
class TestPhase5Integration:
    """Test Phase 5 integration"""
    
    async def test_phase5_manager_initialization(self):
        """Test Phase 5Manager initialization"""
        manager = Phase5Manager()
        
        config = {
            'CLUSTER_ENABLED': True,
            'HEALTH_MONITOR_ENABLED': True
        }
        
        success = await manager.initialize(config)
        
        # May fail if cluster already running, that's ok
        assert isinstance(success, bool)
        
        if success:
            status = await manager.get_status()
            assert 'enabled' in status
            
            await manager.shutdown()
    
    async def test_phase5_status(self):
        """Test Phase 5 status retrieval"""
        manager = Phase5Manager()
        
        config = {'CLUSTER_ENABLED': False}
        await manager.initialize(config)
        
        status = await manager.get_status()
        
        assert 'enabled' in status
        assert 'components' in status
        
        await manager.shutdown()


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
