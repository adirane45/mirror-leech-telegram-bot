"""
Tests for Phase 5 Enhanced Startup Module (Consolidated)
Tests for all Phase 1-5 features now consolidated in enhanced_startup.py
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import patch, MagicMock, AsyncMock

from bot.core.enhanced_startup import (
    initialize_phase5_services,
    shutdown_phase5_services,
    get_phase5_status,
    get_phase5_detailed_status,
    phase5_health_check,
    PHASE5_CONFIG,
    Phase5Status,
    _phase5_status
)


@pytest.fixture
def phase5_status():
    """Fixture to provide clean Phase5Status instance"""
    status = Phase5Status()
    # Reset global status before each test
    _phase5_status.enabled = False
    _phase5_status.initialized_at = None
    _phase5_status.components.clear()
    _phase5_status.errors.clear()
    return status


class TestPhase5Status:
    """Test Phase5Status class"""
    
    def test_initial_state(self, phase5_status):
        """Test initial status state"""
        assert phase5_status.enabled is False
        assert phase5_status.initialized_at is None
        assert len(phase5_status.components) == 0
        assert len(phase5_status.errors) == 0
    
    def test_to_dict(self, phase5_status):
        """Test status serialization"""
        phase5_status.enabled = True
        phase5_status.initialized_at = datetime(2026, 2, 6, 12, 0, 0)
        phase5_status.components = {'health_monitor': True, 'cluster_manager': False}
        phase5_status.errors = {'cluster_manager': 'Connection failed'}
        
        result = phase5_status.to_dict()
        
        assert result['enabled'] is True
        assert result['initialized_at'] == '2026-02-06T12:00:00'
        assert result['total_components'] == 2
        assert result['active_components'] == 1
        assert result['failed_components'] == 1
    
    def test_to_dict_no_timestamp(self, phase5_status):
        """Test serialization without timestamp"""
        result = phase5_status.to_dict()
        assert result['initialized_at'] is None


class TestInitializePhase5:
    """Test Phase 5 initialization"""
    
    @pytest.mark.asyncio
    async def test_disabled_by_default(self):
        """Test Phase 5 is disabled by default"""
        result = await initialize_phase5_services()
        
        assert result['success'] is True
        assert result['enabled'] is False
        assert 'disabled' in result['message'].lower()
    
    @pytest.mark.asyncio
    async def test_disabled_explicitly(self):
        """Test explicit disable via config"""
        config = {'ENABLE_PHASE5': False}
        result = await initialize_phase5_services(config)
        
        assert result['success'] is True
        assert result['enabled'] is False
    
    @pytest.mark.asyncio
    async def test_health_monitor_only(self):
        """Test initialization with only health monitor"""
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health:
            mock_instance = AsyncMock()
            mock_health.get_instance.return_value = mock_instance
            
            config = {
                'ENABLE_PHASE5': True,
                'ENABLE_HEALTH_MONITOR': True,
                'ENABLE_CLUSTER_MANAGER': False,
                'ENABLE_FAILOVER_MANAGER': False,
                'ENABLE_REPLICATION_MANAGER': False,
                'ENABLE_DISTRIBUTED_STATE': False,
                'ENABLE_TASK_COORDINATOR': False,
                'ENABLE_PERFORMANCE_OPTIMIZER': False,
                'ENABLE_API_GATEWAY': False
            }
            
            result = await initialize_phase5_services(config)
            
            assert result['success'] is True
            assert result['enabled'] is True
            assert result['components']['health_monitor'] is True
            mock_instance.enable.assert_called_once()  # Health monitor uses enable()
    
    @pytest.mark.asyncio
    async def test_all_components_enabled(self):
        """Test initialization with all components"""
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health, \
             patch('bot.core.enhanced_startup.ClusterManager') as mock_cluster, \
             patch('bot.core.enhanced_startup.FailoverManager') as mock_failover, \
             patch('bot.core.enhanced_startup.ReplicationManager') as mock_replication, \
             patch('bot.core.enhanced_startup.DistributedStateManager') as mock_state, \
             patch('bot.core.enhanced_startup.TaskCoordinator') as mock_coordinator, \
             patch('bot.core.enhanced_startup.PerformanceOptimizer') as mock_optimizer, \
             patch('bot.core.enhanced_startup.ApiGateway') as mock_gateway:
            
            # Setup all mocks
            for mock in [mock_health, mock_cluster, mock_failover, mock_replication,
                        mock_state, mock_coordinator, mock_optimizer, mock_gateway]:
                mock_instance = AsyncMock()
                mock.get_instance.return_value = mock_instance
            
            config = {
                'ENABLE_PHASE5': True,
                'ENABLE_HEALTH_MONITOR': True,
                'ENABLE_CLUSTER_MANAGER': True,
                'ENABLE_FAILOVER_MANAGER': True,
                'ENABLE_REPLICATION_MANAGER': True,
                'ENABLE_DISTRIBUTED_STATE': True,
                'ENABLE_TASK_COORDINATOR': True,
                'ENABLE_PERFORMANCE_OPTIMIZER': True,
                'ENABLE_API_GATEWAY': True,
                'CLUSTER_NODE_ID': 'test-node',
                'CLUSTER_NODES': ['node2:7946'],
                'CLUSTER_BIND_ADDRESS': '0.0.0.0',
                'CLUSTER_BIND_PORT': 7946
            }
            
            result = await initialize_phase5_services(config)
            
            assert result['success'] is True
            assert result['enabled'] is True
            assert len(result['components']) == 8
            assert all(result['components'].values())
    
    @pytest.mark.asyncio
    async def test_component_failure(self):
        """Test handling of component initialization failure"""
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health:
            mock_instance = AsyncMock()
            mock_instance.enable = AsyncMock()
            mock_instance.enable.side_effect = Exception("Connection refused")
            mock_health.get_instance.return_value = mock_instance
            
            config = {
                'ENABLE_PHASE5': True,
                'ENABLE_HEALTH_MONITOR': True,
                'ENABLE_CLUSTER_MANAGER': False,
                'ENABLE_FAILOVER_MANAGER': False,
                'ENABLE_REPLICATION_MANAGER': False,
                'ENABLE_DISTRIBUTED_STATE': False,
                'ENABLE_TASK_COORDINATOR': False,
                'ENABLE_PERFORMANCE_OPTIMIZER': False,
                'ENABLE_API_GATEWAY': False
            }
            
            result = await initialize_phase5_services(config)
            
            assert result['success'] is False
            assert result['components']['health_monitor'] is False
            assert len(result['errors']) > 0
            assert 'Connection refused' in result['errors'][0]
    
    @pytest.mark.asyncio
    async def test_partial_initialization(self):
        """Test partial initialization with some components failing"""
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health, \
             patch('bot.core.enhanced_startup.TaskCoordinator') as mock_coordinator:
            
            # Health monitor succeeds
            mock_health_instance = AsyncMock()
            mock_health_instance.enable = AsyncMock()  # Health monitor uses enable()
            mock_health.get_instance.return_value = mock_health_instance
            
            # Task coordinator fails
            mock_coordinator_instance = AsyncMock()
            mock_coordinator_instance.start.side_effect = Exception("Task coordinator error")
            mock_coordinator.get_instance.return_value = mock_coordinator_instance
            
            config = {
                'ENABLE_PHASE5': True,
                'ENABLE_HEALTH_MONITOR': True,
                'ENABLE_TASK_COORDINATOR': True,
                'ENABLE_CLUSTER_MANAGER': False,
                'ENABLE_FAILOVER_MANAGER': False,
                'ENABLE_REPLICATION_MANAGER': False,
                'ENABLE_DISTRIBUTED_STATE': False,
                'ENABLE_PERFORMANCE_OPTIMIZER': False,
                'ENABLE_API_GATEWAY': False
            }
            
            result = await initialize_phase5_services(config)
            
            assert result['components']['health_monitor'] is True
            assert result['components']['task_coordinator'] is False
            assert len(result['errors']) == 1
    
    @pytest.mark.asyncio
    async def test_config_override(self):
        """Test configuration override"""
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health:
            mock_instance = AsyncMock()
            mock_instance.enable = AsyncMock()  # Health monitor uses enable()
            mock_health.get_instance.return_value = mock_instance
            
            custom_config = {
                'ENABLE_PHASE5': True,
                'ENABLE_HEALTH_MONITOR': True,
                'HEALTH_CHECK_INTERVAL': 60,  # Override default
                'ENABLE_CLUSTER_MANAGER': False,
                'ENABLE_FAILOVER_MANAGER': False,
                'ENABLE_REPLICATION_MANAGER': False,
                'ENABLE_DISTRIBUTED_STATE': False,
                'ENABLE_TASK_COORDINATOR': False,
                'ENABLE_PERFORMANCE_OPTIMIZER': False,
                'ENABLE_API_GATEWAY': False
            }
            
            result = await initialize_phase5_services(custom_config)
            
            assert result['success'] is True
            # Health monitor interval is set as an attribute, not passed to enable()
            mock_instance.enable.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cluster_node_parsing(self):
        """Test cluster node address parsing"""
        with patch('bot.core.enhanced_startup.ClusterManager') as mock_cluster:
            mock_instance = AsyncMock()
            mock_cluster.get_instance.return_value = mock_instance
            
            config = {
                'ENABLE_PHASE5': True,
                'ENABLE_CLUSTER_MANAGER': True,
                'CLUSTER_NODE_ID': 'node-1',
                'CLUSTER_NODES': ['node-2:7946', 'node-3:7947'],
                'CLUSTER_BIND_ADDRESS': '0.0.0.0',
                'CLUSTER_BIND_PORT': 7946,
                'ENABLE_HEALTH_MONITOR': False,
                'ENABLE_FAILOVER_MANAGER': False,
                'ENABLE_REPLICATION_MANAGER': False,
                'ENABLE_DISTRIBUTED_STATE': False,
                'ENABLE_TASK_COORDINATOR': False,
                'ENABLE_PERFORMANCE_OPTIMIZER': False,
                'ENABLE_API_GATEWAY': False
            }
            
            result = await initialize_phase5_services(config)
            
            assert result['success'] is True
            # Verify cluster manager was started
            assert mock_instance.start.called


class TestShutdownPhase5:
    """Test Phase 5 shutdown"""
    
    @pytest.mark.asyncio
    async def test_shutdown_when_disabled(self):
        """Test shutdown when Phase 5 not enabled"""
        _phase5_status.enabled = False  # Ensure it's disabled
        result = await shutdown_phase5_services()
        
        assert result['success'] is True
        assert 'message' in result
        assert 'not enabled' in result['message'].lower()
    
    @pytest.mark.asyncio
    async def test_shutdown_all_components(self):
        """Test shutdown of all components"""
        # Setup: Initialize components
        _phase5_status.enabled = True
        _phase5_status.components = {
            'health_monitor': True,
            'cluster_manager': True,
            'failover_manager': True,
            'replication_manager': True,
            'distributed_state_manager': True,
            'task_coordinator': True,
            'performance_optimizer': True,
            'api_gateway': True
        }
        
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health, \
             patch('bot.core.enhanced_startup.ClusterManager') as mock_cluster, \
             patch('bot.core.enhanced_startup.FailoverManager') as mock_failover, \
             patch('bot.core.enhanced_startup.ReplicationManager') as mock_replication, \
             patch('bot.core.enhanced_startup.DistributedStateManager') as mock_state, \
             patch('bot.core.enhanced_startup.TaskCoordinator') as mock_coordinator, \
             patch('bot.core.enhanced_startup.PerformanceOptimizer') as mock_optimizer, \
             patch('bot.core.enhanced_startup.ApiGateway') as mock_gateway:
            
            # Setup all mocks
            for mock in [mock_health, mock_cluster, mock_failover, mock_replication,
                        mock_state, mock_coordinator, mock_optimizer, mock_gateway]:
                mock_instance = AsyncMock()
                mock.get_instance.return_value = mock_instance
            
            result = await shutdown_phase5_services()
            
            assert result['success'] is True
            assert len(result['components']) == 8
            assert all(result['components'].values())
            
            # Verify all stop/disable methods were called
            for mock in [mock_cluster, mock_failover, mock_replication,
                        mock_state, mock_coordinator, mock_optimizer, mock_gateway]:
                mock.get_instance.return_value.stop.assert_called_once()
            
            # Health monitor uses disable()
            mock_health.get_instance.return_value.disable.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown_with_failure(self):
        """Test shutdown when a component fails"""
        _phase5_status.enabled = True
        _phase5_status.components = {
            'health_monitor': True,
            'task_coordinator': True
        }
        
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health, \
             patch('bot.core.enhanced_startup.TaskCoordinator') as mock_coordinator:
            
            # Health monitor shutdown succeeds
            mock_health_instance = AsyncMock()
            mock_health_instance.disable = AsyncMock()  # Health monitor uses disable()
            mock_health.get_instance.return_value = mock_health_instance
            
            # Task coordinator shutdown fails
            mock_coordinator_instance = AsyncMock()
            mock_coordinator_instance.stop.side_effect = Exception("Shutdown error")
            mock_coordinator.get_instance.return_value = mock_coordinator_instance
            
            result = await shutdown_phase5_services()
            
            assert result['success'] is False
            assert result['components']['health_monitor'] is True
            assert result['components']['task_coordinator'] is False
            assert len(result['errors']) > 0
    
    @pytest.mark.asyncio
    async def test_shutdown_clears_status(self):
        """Test shutdown clears global status"""
        _phase5_status.enabled = True
        _phase5_status.components = {'health_monitor': True}
        _phase5_status.errors = {'cluster': 'Error'}
        
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health:
            mock_instance = AsyncMock()
            mock_health.get_instance.return_value = mock_instance
            
            await shutdown_phase5_services()
            
            assert _phase5_status.enabled is False
            assert len(_phase5_status.components) == 0
            assert len(_phase5_status.errors) == 0


class TestGetPhase5Status:
    """Test status retrieval functions"""
    
    def test_get_status_disabled(self):
        """Test get_phase5_status when disabled"""
        _phase5_status.enabled = False
        
        result = get_phase5_status()
        
        assert result['enabled'] is False
        assert result['total_components'] == 0
    
    def test_get_status_enabled(self):
        """Test get_phase5_status when enabled"""
        _phase5_status.enabled = True
        _phase5_status.initialized_at = datetime(2026, 2, 6, 12, 0, 0)
        _phase5_status.components = {
            'health_monitor': True,
            'cluster_manager': True,
            'task_coordinator': True
        }
        _phase5_status.errors = {'failover': 'Error'}
        
        result = get_phase5_status()
        
        assert result['enabled'] is True
        assert result['initialized_at'] == '2026-02-06T12:00:00'
        assert result['total_components'] == 3
        assert result['active_components'] == 3
        assert result['failed_components'] == 1
    
    @pytest.mark.asyncio
    async def test_get_detailed_status_disabled(self):
        """Test get_phase5_detailed_status when disabled"""
        _phase5_status.enabled = False
        
        result = await get_phase5_detailed_status()
        
        assert result['enabled'] is False
        assert 'not initialized' in result['message'].lower()
    
    @pytest.mark.asyncio
    async def test_get_detailed_status_with_health_monitor(self):
        """Test detailed status with health monitor"""
        _phase5_status.enabled = True
        _phase5_status.initialized_at = datetime.now(UTC)
        _phase5_status.components = {'health_monitor': True}
        
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health:
            mock_instance = MagicMock()
            mock_instance.components = {
                'comp1': MagicMock(status=MagicMock(value='healthy')),
                'comp2': MagicMock(status=MagicMock(value='unhealthy'))
            }
            mock_health.get_instance.return_value = mock_instance
            
            result = await get_phase5_detailed_status()
            
            assert result['enabled'] is True
            assert 'health_monitor' in result['components']
            assert result['components']['health_monitor']['active'] is True
            assert result['components']['health_monitor']['components'] == 2
            assert result['components']['health_monitor']['unhealthy'] == 1
    
    @pytest.mark.asyncio
    async def test_get_detailed_status_exception_handling(self):
        """Test detailed status handles component exceptions"""
        _phase5_status.enabled = True
        _phase5_status.components = {'health_monitor': True}
        
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health:
            mock_health.get_instance.side_effect = Exception("Not available")
            
            result = await get_phase5_detailed_status()
            
            assert result['enabled'] is True
            assert result['components']['health_monitor']['active'] is False


class TestPhase5HealthCheck:
    """Test Phase 5 health check function"""
    
    @pytest.mark.asyncio
    async def test_health_check_disabled(self):
        """Test health check when Phase 5 disabled"""
        _phase5_status.enabled = False
        
        result = await phase5_health_check()
        
        assert result['healthy'] is True
        assert result['enabled'] is False
    
    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self):
        """Test health check with all components healthy"""
        _phase5_status.enabled = True
        _phase5_status.components = {
            'health_monitor': True,
            'cluster_manager': True,
            'task_coordinator': True
        }
        _phase5_status.errors = {}
        
        result = await phase5_health_check()
        
        assert result['healthy'] is True
        assert result['enabled'] is True
        assert len(result['components']) == 3
        assert all(result['components'].values())
        assert len(result['issues']) == 0
    
    @pytest.mark.asyncio
    async def test_health_check_with_errors(self):
        """Test health check with component errors"""
        _phase5_status.enabled = True
        _phase5_status.components = {
            'health_monitor': True,
            'cluster_manager': True
        }
        _phase5_status.errors = {
            'cluster_manager': 'Connection timeout'
        }
        
        result = await phase5_health_check()
        
        assert result['healthy'] is False
        assert result['enabled'] is True
        assert result['components']['health_monitor'] is True
        assert result['components']['cluster_manager'] is False
        assert len(result['issues']) == 1
        assert 'Connection timeout' in result['issues'][0]


class TestConfiguration:
    """Test configuration handling"""
    
    def test_default_config(self):
        """Test default configuration values"""
        assert PHASE5_CONFIG['ENABLE_PHASE5'] is False
        assert PHASE5_CONFIG['ENABLE_HEALTH_MONITOR'] is True
        assert PHASE5_CONFIG['HEALTH_CHECK_INTERVAL'] == 30
        assert PHASE5_CONFIG['CLUSTER_MIN_NODES'] == 2
    
    def test_failover_defaults(self):
        """Test failover configuration defaults"""
        assert PHASE5_CONFIG['FAILOVER_ROLE'] == 'PRIMARY'
        assert PHASE5_CONFIG['FAILOVER_AUTO_ENABLED'] is True
        assert PHASE5_CONFIG['FAILOVER_FAILURE_THRESHOLD'] == 3
    
    def test_replication_defaults(self):
        """Test replication configuration defaults"""
        assert PHASE5_CONFIG['REPLICATION_STRATEGY'] == 'MASTER_SLAVE'
        assert PHASE5_CONFIG['REPLICATION_CONFLICT_RESOLUTION'] == 'TIMESTAMP'
    
    def test_optimizer_defaults(self):
        """Test optimizer configuration defaults"""
        assert PHASE5_CONFIG['OPTIMIZER_STRATEGY'] == 'BALANCED'
        assert PHASE5_CONFIG['OPTIMIZER_AUTO_SCALING'] is False


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """Test complete initialization and shutdown cycle"""
        with patch('bot.core.enhanced_startup.HealthMonitor') as mock_health:
            mock_instance = AsyncMock()
            mock_instance.enable = AsyncMock()  # Health monitor uses enable()
            mock_instance.disable = AsyncMock()  # Health monitor uses disable()
            mock_health.get_instance.return_value = mock_instance
            
            config = {
                'ENABLE_PHASE5': True,
                'ENABLE_HEALTH_MONITOR': True,
                'ENABLE_CLUSTER_MANAGER': False,
                'ENABLE_FAILOVER_MANAGER': False,
                'ENABLE_REPLICATION_MANAGER': False,
                'ENABLE_DISTRIBUTED_STATE': False,
                'ENABLE_TASK_COORDINATOR': False,
                'ENABLE_PERFORMANCE_OPTIMIZER': False,
                'ENABLE_API_GATEWAY': False
            }
            
            # Initialize
            init_result = await initialize_phase5_services(config)
            assert init_result['success'] is True
            
            # Get status
            status = get_phase5_status()
            assert status['enabled'] is True
            
            # Health check
            health = await phase5_health_check()
            # When properly initialized, health should be enabled
            assert health['enabled'] is True
            
            # Shutdown
            shutdown_result = await shutdown_phase5_services()
            assert shutdown_result['success'] is True
            
            # Verify status cleared
            final_status = get_phase5_status()
            assert final_status['enabled'] is False
