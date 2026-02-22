"""
Resilience & Recovery Patterns for Phase 7

Implements:
- Graceful degradation strategies
- Failover mechanisms
- Data consistency & recovery
- Canary deployments
- Automated rollback
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass, field

from .. import LOGGER


class DeploymentStrategy(str, Enum):
    """Deployment strategies"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    SHADOW = "shadow"


class FailoverState(str, Enum):
    """Failover state"""
    ACTIVE = "active"
    STANDBY = "standby"
    FAILED = "failed"
    RECOVERING = "recovering"


@dataclass
class ServiceInstance:
    """Service instance for failover"""
    name: str
    endpoint: str
    status: FailoverState = FailoverState.STANDBY
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    healthy: bool = False
    error_count: int = 0
    recovery_attempts: int = 0


class FailoverManager:
    """Manage service failover"""
    
    def __init__(self, heartbeat_timeout_seconds: int = 30):
        self.instances: Dict[str, ServiceInstance] = {}
        self.active_instance: Optional[str] = None
        self.heartbeat_timeout = heartbeat_timeout_seconds
    
    def register_instance(self, name: str, endpoint: str) -> None:
        """Register service instance"""
        self.instances[name] = ServiceInstance(name=name, endpoint=endpoint)
    
    def heartbeat(self, instance_name: str, healthy: bool = True) -> None:
        """Record heartbeat"""
        if instance_name not in self.instances:
            return
        
        instance = self.instances[instance_name]
        instance.last_heartbeat = datetime.now(timezone.utc)
        instance.healthy = healthy
        
        if healthy:
            instance.error_count = 0
        else:
            instance.error_count += 1
    
    async def check_health(self) -> Dict[str, Any]:
        """Check health of all instances"""
        now = datetime.now(timezone.utc)
        failed = []
        healthy = []
        
        for name, instance in self.instances.items():
            elapsed = (now - instance.last_heartbeat).total_seconds()
            
            if elapsed > self.heartbeat_timeout or not instance.healthy:
                instance.status = FailoverState.FAILED
                failed.append(name)
            else:
                instance.status = FailoverState.ACTIVE
                healthy.append(name)
        
        # Trigger failover if active is down
        if self.active_instance in failed:
            await self.trigger_failover()
        
        return {
            "healthy": healthy,
            "failed": failed,
            "active": self.active_instance
        }
    
    async def trigger_failover(self) -> bool:
        """Trigger failover to standby instance"""
        # Find healthy alternate
        for name, instance in self.instances.items():
            if name != self.active_instance and instance.healthy:
                old_active = self.active_instance
                self.active_instance = name
                instance.status = FailoverState.ACTIVE
                
                LOGGER.warning(
                    f"Failover triggered: {old_active} -> {name}"
                )
                return True
        
        return False
    
    async def recover_instance(self, instance_name: str) -> bool:
        """Attempt to recover failed instance"""
        if instance_name not in self.instances:
            return False
        
        instance = self.instances[instance_name]
        instance.status = FailoverState.RECOVERING
        instance.recovery_attempts += 1
        
        LOGGER.info(f"Attempting recovery of {instance_name}")
        
        try:
            # Simulate recovery call
            await asyncio.sleep(1)
            instance.healthy = True
            instance.status = FailoverState.STANDBY
            instance.error_count = 0
            return True
        
        except Exception as e:
            LOGGER.error(f"Recovery failed for {instance_name}: {e}")
            instance.status = FailoverState.FAILED
            return False
    
    def get_active_endpoint(self) -> Optional[str]:
        """Get active service endpoint"""
        if not self.active_instance:
            return None
        
        return self.instances[self.active_instance].endpoint


class GracefulDegradation:
    """Graceful degradation strategies"""
    
    def __init__(self):
        self.feature_flags: Dict[str, bool] = {}
        self.degraded_features: set = set()
        self.fallback_handlers: Dict[str, Callable] = {}
    
    def register_feature(self, name: str, enabled: bool = True) -> None:
        """Register feature flag"""
        self.feature_flags[name] = enabled
    
    def register_fallback(
        self,
        feature_name: str,
        handler: Callable
    ) -> None:
        """Register fallback handler"""
        self.fallback_handlers[feature_name] = handler
    
    def is_enabled(self, feature_name: str) -> bool:
        """Check if feature is enabled"""
        return self.feature_flags.get(feature_name, True)
    
    def degrade_feature(self, feature_name: str) -> None:
        """Mark feature as degraded"""
        self.degraded_features.add(feature_name)
        self.feature_flags[feature_name] = False
        
        LOGGER.warning(f"Feature degraded: {feature_name}")
    
    def restore_feature(self, feature_name: str) -> None:
        """Restore degraded feature"""
        if feature_name in self.degraded_features:
            self.degraded_features.discard(feature_name)
            self.feature_flags[feature_name] = True
            
            LOGGER.info(f"Feature restored: {feature_name}")
    
    async def handle_degraded_request(
        self,
        feature_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Handle request for degraded feature"""
        if feature_name in self.fallback_handlers:
            handler = self.fallback_handlers[feature_name]
            
            if asyncio.iscoroutinefunction(handler):
                return await handler(*args, **kwargs)
            else:
                return handler(*args, **kwargs)
        
        return None


@dataclass
class DeploymentVersion:
    """Deployment version"""
    version: str
    timestamp: datetime
    status: str = "pending"  # pending, active, rolled_back
    health_score: float = 0.0
    error_count: int = 0
    rollback_reason: Optional[str] = None


class CanaryDeployment:
    """Manage canary deployments"""
    
    def __init__(self, initial_traffic_percent: int = 5):
        self.versions: Dict[str, DeploymentVersion] = {}
        self.active_version: Optional[str] = None
        self.canary_version: Optional[str] = None
        self.current_traffic_percent = 100
        self.canary_traffic_percent = initial_traffic_percent
        self.health_threshold = 0.95
    
    def deploy_canary(
        self,
        version: str,
        traffic_percent: int = 5
    ) -> None:
        """Deploy new version as canary"""
        self.canary_version = version
        self.canary_traffic_percent = traffic_percent
        self.current_traffic_percent = 100 - traffic_percent
        
        self.versions[version] = DeploymentVersion(
            version=version,
            timestamp=datetime.now(timezone.utc),
            status="pending"
        )
        
        LOGGER.info(f"Canary deployed: {version} ({traffic_percent}%)")
    
    def record_canary_metric(
        self,
        success: bool,
        response_time_ms: float
    ) -> None:
        """Record metric for canary"""
        if not self.canary_version:
            return
        
        version = self.versions[self.canary_version]
        
        if not success:
            version.error_count += 1
        
        # Calculate health (0-1)
        version.health_score = max(
            0,
            1 - (version.error_count / 100)
        )
    
    async def promote_canary(self) -> bool:
        """Promote canary to main"""
        if not self.canary_version:
            return False
        
        canary = self.versions[self.canary_version]
        
        if canary.health_score < self.health_threshold:
            LOGGER.error(
                f"Canary health too low: {canary.health_score}"
            )
            return False
        
        old_active = self.active_version
        self.active_version = self.canary_version
        self.canary_version = None
        self.current_traffic_percent = 100
        
        if old_active:
            self.versions[old_active].status = "rolled_back"
        
        canary.status = "active"
        
        LOGGER.info(f"Canary promoted to main: {self.active_version}")
        return True
    
    async def rollback(self, reason: str) -> bool:
        """Rollback deployment"""
        if not self.canary_version:
            return False
        
        canary = self.versions[self.canary_version]
        canary.status = "rolled_back"
        canary.rollback_reason = reason
        
        self.canary_version = None
        self.current_traffic_percent = 100
        self.canary_traffic_percent = 0
        
        LOGGER.warning(f"Rollback initiated: {reason}")
        return True


class DataConsistencyManager:
    """Ensure data consistency across instances"""
    
    def __init__(self):
        self.consistency_checks: Dict[str, Callable] = {}
        self.last_check: Dict[str, datetime] = {}
    
    def register_consistency_check(
        self,
        name: str,
        check_func: Callable
    ) -> None:
        """Register consistency check"""
        self.consistency_checks[name] = check_func
    
    async def verify_consistency(self) -> Dict[str, bool]:
        """Verify data consistency"""
        results = {}
        
        for name, check_func in self.consistency_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                results[name] = result
                self.last_check[name] = datetime.now(timezone.utc)
                
                if not result:
                    LOGGER.warning(f"Consistency check failed: {name}")
            
            except Exception as e:
                results[name] = False
                LOGGER.error(f"Consistency check error {name}: {e}")
        
        return results
    
    async def trigger_reconciliation(self) -> None:
        """Trigger data reconciliation"""
        LOGGER.info("Starting data reconciliation")
        # Implementation specific to use case


# Global instances
failover_manager = FailoverManager()
graceful_degradation = GracefulDegradation()
canary_deployment = CanaryDeployment()
data_consistency = DataConsistencyManager()
