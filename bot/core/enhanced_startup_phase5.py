"""
Enhanced Startup for Phase 5: High Availability

Safely initializes all Phase 5 HA components:
- Cluster Manager
- Failover Manager
- Replication Manager
- Distributed State Manager
- Health Monitor

All components are disabled by default and can be enabled via configuration.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Import configuration
try:
    from config_enhancements_phase5 import (
        get_phase5_config,
        validate_phase5_config
    )
except ImportError:
    print("Warning: Phase 5 configuration not found")
    get_phase5_config = lambda: {}
    validate_phase5_config = lambda x: {'valid': True, 'warnings': [], 'errors': []}

# Import Phase 5 managers
try:
    from bot.core.cluster_manager import ClusterManager
    from bot.core.failover_manager import FailoverManager, FailoverPolicy, FailoverRole
    from bot.core.replication_manager import (
        ReplicationManager,
        ReplicationMode,
        ConsistencyLevel,
        ConflictResolution
    )
    from bot.core.distributed_state_manager import DistributedStateManager
    from bot.core.health_monitor import HealthMonitor, ComponentType, HealthStatus
    PHASE5_AVAILABLE = True
except ImportError as e:
    print(f"Phase 5 components not available: {e}")
    PHASE5_AVAILABLE = False


class Phase5Manager:
    """Manages Phase 5 High Availability components"""
    
    def __init__(self):
        self.enabled = False
        self.config: Dict[str, Any] = {}
        self.managers: Dict[str, Any] = {}
        self.status: Dict[str, Any] = {
            'cluster': False,
            'failover': False,
            'replication': False,
            'distributed_state': False,
            'health_monitor': False
        }
        self.startup_time: Optional[datetime] = None
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize Phase 5 components"""
        try:
            if not PHASE5_AVAILABLE:
                print("Phase 5 not available - skipping")
                return True
            
            self.config = {**get_phase5_config(), **config}
            
            # Validate configuration
            validation = validate_phase5_config(self.config)
            
            if validation['warnings']:
                print("Phase 5 Configuration Warnings:")
                for warning in validation['warnings']:
                    print(f"  - {warning}")
            
            if validation['errors']:
                print("Phase 5 Configuration Errors:")
                for error in validation['errors']:
                    print(f"  - {error}")
                return False
            
            # Initialize components
            success = True
            
            # 1. Cluster Manager
            if self.config.get('CLUSTER_ENABLED'):
                success = await self._init_cluster_manager() and success
            
            # 2. Failover Manager
            if self.config.get('FAILOVER_ENABLED'):
                success = await self._init_failover_manager() and success
            
            # 3. Replication Manager
            if self.config.get('REPLICATION_ENABLED'):
                success = await self._init_replication_manager() and success
            
            # 4. Distributed State Manager
            if self.config.get('DISTRIBUTED_STATE_ENABLED'):
                success = await self._init_distributed_state_manager() and success
            
            # 5. Health Monitor
            if self.config.get('HEALTH_MONITOR_ENABLED'):
                success = await self._init_health_monitor() and success
            
            if success:
                self.enabled = True
                self.startup_time = datetime.utcnow()
                print("Phase 5 initialization completed successfully")
            else:
                print("Phase 5 initialization completed with errors")
                await self.shutdown()
            
            return success
        
        except Exception as e:
            print(f"Error initializing Phase 5: {e}")
            return False
    
    async def _init_cluster_manager(self) -> bool:
        """Initialize Cluster Manager"""
        try:
            print("Initializing Cluster Manager...")
            
            cluster_manager = ClusterManager.get_instance()
            
            address = self.config.get('CLUSTER_ADDRESS', '0.0.0.0')
            port = self.config.get('CLUSTER_PORT', 7946)
            seed_nodes = self.config.get('CLUSTER_SEED_NODES', [])
            node_id = self.config.get('CLUSTER_NODE_ID')
            
            success = await cluster_manager.enable(
                address=address,
                port=port,
                seed_nodes=seed_nodes,
                node_id=node_id
            )
            
            if success:
                self.managers['cluster'] = cluster_manager
                self.status['cluster'] = True
                print(f"  ✓ Cluster Manager enabled on {address}:{port}")
                
                # Join cluster if seed nodes provided
                if seed_nodes:
                    print(f"  → Joining cluster with {len(seed_nodes)} seed nodes")
                    for seed in seed_nodes:
                        try:
                            host, port_str = seed.split(':')
                            await cluster_manager.join_cluster(host, int(port_str))
                        except Exception as e:
                            print(f"  ! Failed to join {seed}: {e}")
            else:
                print("  ✗ Failed to enable Cluster Manager")
            
            return success
        
        except Exception as e:
            print(f"  ✗ Cluster Manager error: {e}")
            return False
    
    async def _init_failover_manager(self) -> bool:
        """Initialize Failover Manager"""
        try:
            print("Initializing Failover Manager...")
            
            failover_manager = FailoverManager.get_instance()
            
            # Create policy from config
            policy = FailoverPolicy(
                auto_failover_enabled=(
                    self.config.get('FAILOVER_MODE') == 'automatic'
                ),
                failover_timeout=self.config.get('FAILOVER_TIMEOUT', 30),
                health_check_interval=self.config.get('FAILOVER_HEALTH_CHECK_INTERVAL', 5),
                failure_threshold=self.config.get('FAILOVER_FAILURE_THRESHOLD', 3),
                recovery_wait_time=self.config.get('FAILOVER_RECOVERY_WAIT_TIME', 60),
                max_failover_attempts=self.config.get('FAILOVER_MAX_ATTEMPTS', 3)
            )
            
            # Determine role
            primary_node = self.config.get('FAILOVER_PRIMARY_NODE')
            secondary_nodes = self.config.get('FAILOVER_SECONDARY_NODES', [])
            
            if primary_node:
                role = FailoverRole.PRIMARY
            elif secondary_nodes:
                role = FailoverRole.SECONDARY
            else:
                role = FailoverRole.STANDBY
            
            success = await failover_manager.enable(role=role, policy=policy)
            
            if success:
                # Configure primary/secondary
                if primary_node:
                    await failover_manager.set_primary(primary_node)
                
                for node in secondary_nodes:
                    await failover_manager.add_secondary(node)
                
                self.managers['failover'] = failover_manager
                self.status['failover'] = True
                print(f"  ✓ Failover Manager enabled (role: {role.value})")
            else:
                print("  ✗ Failed to enable Failover Manager")
            
            return success
        
        except Exception as e:
            print(f"  ✗ Failover Manager error: {e}")
            return False
    
    async def _init_replication_manager(self) -> bool:
        """Initialize Replication Manager"""
        try:
            print("Initializing Replication Manager...")
            
            replication_manager = ReplicationManager.get_instance()
            
            # Parse replication mode
            mode_str = self.config.get('REPLICATION_MODE', 'master_slave')
            mode = (
                ReplicationMode.MULTI_MASTER
                if mode_str == 'multi_master'
                else ReplicationMode.MASTER_SLAVE
            )
            
            # Parse consistency level
            consistency_str = self.config.get('REPLICATION_CONSISTENCY', 'eventual')
            if consistency_str == 'strong':
                consistency = ConsistencyLevel.STRONG
            elif consistency_str == 'quorum':
                consistency = ConsistencyLevel.QUORUM
            else:
                consistency = ConsistencyLevel.EVENTUAL
            
            success = await replication_manager.enable(
                mode=mode,
                consistency=consistency
            )
            
            if success:
                # Configure master/slaves
                master_node = self.config.get('REPLICATION_MASTER_NODE')
                if master_node:
                    await replication_manager.set_master(master_node)
                
                slave_nodes = self.config.get('REPLICATION_SLAVE_NODES', [])
                for node in slave_nodes:
                    await replication_manager.add_slave(node)
                
                # Set conflict resolution
                resolution_str = self.config.get(
                    'REPLICATION_CONFLICT_RESOLUTION',
                    'last_write_wins'
                )
                if resolution_str == 'first_write_wins':
                    replication_manager.conflict_resolution = ConflictResolution.FIRST_WRITE_WINS
                elif resolution_str == 'merge':
                    replication_manager.conflict_resolution = ConflictResolution.MERGE
                elif resolution_str == 'manual':
                    replication_manager.conflict_resolution = ConflictResolution.MANUAL
                else:
                    replication_manager.conflict_resolution = ConflictResolution.LAST_WRITE_WINS
                
                self.managers['replication'] = replication_manager
                self.status['replication'] = True
                print(f"  ✓ Replication Manager enabled (mode: {mode.value})")
            else:
                print("  ✗ Failed to enable Replication Manager")
            
            return success
        
        except Exception as e:
            print(f"  ✗ Replication Manager error: {e}")
            return False
    
    async def _init_distributed_state_manager(self) -> bool:
        """Initialize Distributed State Manager"""
        try:
            print("Initializing Distributed State Manager...")
            
            state_manager = DistributedStateManager.get_instance()
            
            node_id = self.config.get('CLUSTER_NODE_ID')
            
            success = await state_manager.enable(node_id=node_id)
            
            if success:
                self.managers['distributed_state'] = state_manager
                self.status['distributed_state'] = True
                print("  ✓ Distributed State Manager enabled")
            else:
                print("  ✗ Failed to enable Distributed State Manager")
            
            return success
        
        except Exception as e:
            print(f"  ✗ Distributed State Manager error: {e}")
            return False
    
    async def _init_health_monitor(self) -> bool:
        """Initialize Health Monitor"""
        try:
            print("Initializing Health Monitor...")
            
            health_monitor = HealthMonitor.get_instance()
            
            success = await health_monitor.enable()
            
            if success:
                # Register health checks based on config
                if self.config.get('HEALTH_CHECK_NODES'):
                    await self._register_node_health_checks(health_monitor)
                
                if self.config.get('HEALTH_CHECK_DATABASE'):
                    await self._register_database_health_checks(health_monitor)
                
                if self.config.get('HEALTH_CHECK_CACHE'):
                    await self._register_cache_health_checks(health_monitor)
                
                self.managers['health_monitor'] = health_monitor
                self.status['health_monitor'] = True
                print("  ✓ Health Monitor enabled")
            else:
                print("  ✗ Failed to enable Health Monitor")
            
            return success
        
        except Exception as e:
            print(f"  ✗ Health Monitor error: {e}")
            return False
    
    async def _register_node_health_checks(self, health_monitor: HealthMonitor) -> None:
        """Register node health checks"""
        async def check_node_health():
            """Check cluster node health"""
            try:
                if 'cluster' in self.managers:
                    cluster = self.managers['cluster']
                    info = await cluster.get_cluster_info()
                    return {
                        'status': HealthStatus.HEALTHY if info['is_healthy'] else HealthStatus.DEGRADED,
                        'details': info
                    }
                return {'status': HealthStatus.UNKNOWN}
            except Exception:
                return {'status': HealthStatus.UNHEALTHY}
        
        await health_monitor.register_health_check(
            check_id='cluster_nodes',
            component_type=ComponentType.NODE,
            component_name='cluster',
            check_fn=check_node_health,
            interval_seconds=self.config.get('HEALTH_CHECK_INTERVAL', 30)
        )
    
    async def _register_database_health_checks(self, health_monitor: HealthMonitor) -> None:
        """Register database health checks"""
        async def check_database_health():
            """Check database health"""
            try:
                # In production, check actual database connection
                return {'status': HealthStatus.HEALTHY}
            except Exception:
                return {'status': HealthStatus.UNHEALTHY}
        
        await health_monitor.register_health_check(
            check_id='database',
            component_type=ComponentType.DATABASE,
            component_name='mongodb',
            check_fn=check_database_health,
            timeout_seconds=self.config.get('HEALTH_DATABASE_CHECK_TIMEOUT', 5)
        )
    
    async def _register_cache_health_checks(self, health_monitor: HealthMonitor) -> None:
        """Register cache health checks"""
        async def check_cache_health():
            """Check cache health"""
            try:
                # In production, check actual Redis connection
                return {'status': HealthStatus.HEALTHY}
            except Exception:
                return {'status': HealthStatus.UNHEALTHY}
        
        await health_monitor.register_health_check(
            check_id='cache',
            component_type=ComponentType.CACHE,
            component_name='redis',
            check_fn=check_cache_health,
            timeout_seconds=self.config.get('HEALTH_CACHE_CHECK_TIMEOUT', 3)
        )
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Phase 5 status"""
        try:
            status = {
                'enabled': self.enabled,
                'startup_time': (
                    self.startup_time.isoformat()
                    if self.startup_time else None
                ),
                'components': self.status.copy()
            }
            
            # Get detailed status from each manager
            if 'cluster' in self.managers:
                cluster = self.managers['cluster']
                status['cluster_info'] = await cluster.get_cluster_info()
            
            if 'failover' in self.managers:
                failover = self.managers['failover']
                status['failover_status'] = await failover.get_failover_status()
            
            if 'replication' in self.managers:
                replication = self.managers['replication']
                status['replication_status'] = await replication.get_replication_status()
            
            if 'distributed_state' in self.managers:
                state = self.managers['distributed_state']
                status['distributed_state_status'] = await state.get_status()
            
            if 'health_monitor' in self.managers:
                health = self.managers['health_monitor']
                status['health_status'] = await health.get_overall_health()
            
            return status
        
        except Exception as e:
            return {'enabled': self.enabled, 'error': str(e)}
    
    async def shutdown(self) -> bool:
        """Shutdown all Phase 5 components"""
        try:
            print("Shutting down Phase 5 components...")
            
            success = True
            
            # Shutdown in reverse order
            if 'health_monitor' in self.managers:
                await self.managers['health_monitor'].disable()
                print("  ✓ Health Monitor shutdown")
            
            if 'distributed_state' in self.managers:
                await self.managers['distributed_state'].disable()
                print("  ✓ Distributed State Manager shutdown")
            
            if 'replication' in self.managers:
                await self.managers['replication'].disable()
                print("  ✓ Replication Manager shutdown")
            
            if 'failover' in self.managers:
                await self.managers['failover'].disable()
                print("  ✓ Failover Manager shutdown")
            
            if 'cluster' in self.managers:
                await self.managers['cluster'].disable()
                print("  ✓ Cluster Manager shutdown")
            
            self.managers.clear()
            self.status = {key: False for key in self.status}
            self.enabled = False
            
            print("Phase 5 shutdown completed")
            return success
        
        except Exception as e:
            print(f"Error during Phase 5 shutdown: {e}")
            return False


# Singleton instance
_phase5_manager = Phase5Manager()


async def initialize_phase5(config: Dict[str, Any]) -> bool:
    """Initialize Phase 5 High Availability"""
    return await _phase5_manager.initialize(config)


async def get_phase5_status() -> Dict[str, Any]:
    """Get Phase 5 status"""
    return await _phase5_manager.get_status()


async def shutdown_phase5() -> bool:
    """Shutdown Phase 5"""
    return await _phase5_manager.shutdown()
