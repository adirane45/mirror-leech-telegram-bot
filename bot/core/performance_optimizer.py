"""
Performance Optimizer for resource management and auto-scaling

Implements:
- Resource metrics collection and analysis
- CPU, memory, network utilization tracking
- Performance optimization recommendations
- Auto-scaling decisions
- Threshold-based alerts
"""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Set, Optional, Any, Callable
from abc import ABC, abstractmethod


class OptimizationStrategy(str, Enum):
    """Optimization strategies"""
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    MANUAL = "manual"


class ResourceType(str, Enum):
    """Types of resources"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    STORAGE = "storage"
    DISK_IO = "disk_io"


class ScalingAction(str, Enum):
    """Auto-scaling actions"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_ACTION = "no_action"
    OPTIMIZE = "optimize"


@dataclass
class ResourceMetric:
    """Resource metric at a point in time"""
    resource_type: ResourceType
    value: float  # 0.0-1.0 or other metric value
    threshold: float = 0.8  # Alert threshold
    timestamp: datetime = field(default_factory=datetime.utcnow)
    node_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'resource_type': self.resource_type.value,
            'value': round(self.value, 4),
            'threshold': self.threshold,
            'timestamp': self.timestamp.isoformat(),
            'node_id': self.node_id,
            'exceeds_threshold': self.value > self.threshold
        }


@dataclass
class PerformanceSnapshot:
    """Performance snapshot at a point in time"""
    snapshot_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_usage: float = 0.0
    disk_io_usage: float = 0.0
    active_tasks: int = 0
    response_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'snapshot_id': self.snapshot_id,
            'node_id': self.node_id,
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage': round(self.cpu_usage, 4),
            'memory_usage': round(self.memory_usage, 4),
            'network_usage': round(self.network_usage, 4),
            'disk_io_usage': round(self.disk_io_usage, 4),
            'active_tasks': self.active_tasks,
            'response_time_ms': self.response_time_ms
        }


@dataclass
class OptimizationRecommendation:
    """Recommendation for performance optimization"""
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str = ""
    action: ScalingAction = ScalingAction.NO_ACTION
    resource_type: Optional[ResourceType] = None
    reason: str = ""
    priority: int = 1  # 1=low, 5=critical
    estimated_impact: float = 0.0  # 0.0-1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'recommendation_id': self.recommendation_id,
            'node_id': self.node_id,
            'action': self.action.value,
            'resource_type': self.resource_type.value if self.resource_type else None,
            'reason': self.reason,
            'priority': self.priority,
            'estimated_impact': round(self.estimated_impact, 2),
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class OptimizerMetrics:
    """Metrics for performance optimizer"""
    metrics_collected: int = 0
    recommendations_made: int = 0
    scaling_actions_taken: int = 0
    avg_cpu_usage: float = 0.0
    avg_memory_usage: float = 0.0
    avg_response_time_ms: float = 0.0
    nodes_under_load: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'metrics_collected': self.metrics_collected,
            'recommendations_made': self.recommendations_made,
            'scaling_actions_taken': self.scaling_actions_taken,
            'avg_cpu_usage': round(self.avg_cpu_usage, 4),
            'avg_memory_usage': round(self.avg_memory_usage, 4),
            'avg_response_time_ms': round(self.avg_response_time_ms, 2),
            'nodes_under_load': self.nodes_under_load,
            'last_updated': self.last_updated.isoformat()
        }


class PerformanceOptimizationListener(ABC):
    """Abstract listener for performance events"""
    
    @abstractmethod
    async def on_metric_collected(self, metric: ResourceMetric) -> None:
        """Called when metric collected"""
        pass
    
    @abstractmethod
    async def on_threshold_exceeded(self, metric: ResourceMetric) -> None:
        """Called when threshold exceeded"""
        pass
    
    @abstractmethod
    async def on_recommendation_made(self, recommendation: OptimizationRecommendation) -> None:
        """Called when recommendation made"""
        pass
    
    @abstractmethod
    async def on_scaling_action(self, action: ScalingAction, node_id: str) -> None:
        """Called when scaling action taken"""
        pass


class PerformanceOptimizer:
    """
    Monitors and optimizes cluster performance
    
    Singleton instance managing:
    - Resource metrics collection
    - Performance analysis
    - Optimization recommendations
    - Auto-scaling decisions
    - Alert thresholds
    """
    
    _instance: Optional['PerformanceOptimizer'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.enabled = False
        self.node_id = ""
        self.strategy = OptimizationStrategy.BALANCED
        self.snapshots: Dict[str, List[PerformanceSnapshot]] = {}  # node_id -> list
        self.metrics: Dict[str, ResourceMetric] = {}
        self.recommendations: Dict[str, OptimizationRecommendation] = {}
        self.scaling_history: List[tuple[str, ScalingAction, datetime]] = []  # (node_id, action, timestamp)
        self.peers: Set[str] = set()
        self.listeners: List[PerformanceOptimizationListener] = []
        self.optimizer_metrics = OptimizerMetrics()
        
        # Thresholds
        self.cpu_threshold = 0.8
        self.memory_threshold = 0.85
        self.network_threshold = 0.8
        self.disk_io_threshold = 0.75
        
        # Scaling limits
        self.max_scale_up_count = 3
        self.min_scale_down_count = 1
        self.scale_cooldown_seconds = 300
        
        # Background tasks
        self._collector_task: Optional[asyncio.Task] = None
        self._analyzer_task: Optional[asyncio.Task] = None
    
    @classmethod
    def get_instance(cls) -> 'PerformanceOptimizer':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def start(self, node_id: str = "", strategy: OptimizationStrategy = OptimizationStrategy.BALANCED) -> bool:
        """Start performance optimizer"""
        if self.enabled:
            return True
        
        try:
            self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
            self.strategy = strategy
            self.enabled = True
            
            # Start background tasks
            self._collector_task = asyncio.create_task(self._collection_loop())
            self._analyzer_task = asyncio.create_task(self._analysis_loop())
            
            return True
        except Exception:
            self.enabled = False
            return False
    
    async def stop(self) -> bool:
        """Stop performance optimizer"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            
            if self._collector_task:
                self._collector_task.cancel()
            if self._analyzer_task:
                self._analyzer_task.cancel()
            
            await asyncio.sleep(0.1)
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # METRICS COLLECTION
    # ========================================================================
    
    async def record_metric(self, metric: ResourceMetric) -> bool:
        """Record a resource metric"""
        if not self.enabled:
            return False
        
        try:
            self.metrics[f"{metric.node_id}_{metric.resource_type.value}"] = metric
            
            # Track in snapshots
            if metric.node_id not in self.snapshots:
                self.snapshots[metric.node_id] = []
            
            self.optimizer_metrics.metrics_collected += 1
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_metric_collected(metric)
            
            # Check threshold
            if metric.value > metric.threshold:
                for listener in self.listeners:
                    await listener.on_threshold_exceeded(metric)
            
            return True
        except Exception:
            return False
    
    async def record_snapshot(self, snapshot: PerformanceSnapshot) -> bool:
        """Record performance snapshot"""
        if not self.enabled:
            return False
        
        try:
            if snapshot.node_id not in self.snapshots:
                self.snapshots[snapshot.node_id] = []
            
            self.snapshots[snapshot.node_id].append(snapshot)
            
            # Keep only last 100 snapshots per node
            if len(self.snapshots[snapshot.node_id]) > 100:
                self.snapshots[snapshot.node_id].pop(0)
            
            return True
        except Exception:
            return False
    
    async def get_latest_snapshot(self, node_id: str) -> Optional[PerformanceSnapshot]:
        """Get latest performance snapshot for node"""
        if node_id not in self.snapshots or not self.snapshots[node_id]:
            return None
        return self.snapshots[node_id][-1]
    
    async def get_node_snapshots(self, node_id: str, count: int = 10) -> List[PerformanceSnapshot]:
        """Get last N snapshots for node"""
        if node_id not in self.snapshots:
            return []
        return self.snapshots[node_id][-count:]
    
    # ========================================================================
    # PERFORMANCE ANALYSIS
    # ========================================================================
    
    async def _collection_loop(self) -> None:
        """Background loop for metrics collection"""
        while self.enabled:
            try:
                # In real implementation, would collect from actual nodes
                # For now, simulate collection
                for peer in [self.node_id] + list(self.peers):
                    snapshot = PerformanceSnapshot(
                        node_id=peer,
                        cpu_usage=0.3,
                        memory_usage=0.4,
                        network_usage=0.2
                    )
                    await self.record_snapshot(snapshot)
                
                await asyncio.sleep(10)
            except Exception:
                await asyncio.sleep(10)
    
    async def _analysis_loop(self) -> None:
        """Background loop for performance analysis"""
        while self.enabled:
            try:
                # Analyze metrics and make recommendations
                for node_id in [self.node_id] + list(self.peers):
                    snapshots = await self.get_node_snapshots(node_id, 5)
                    if snapshots:
                        await self._analyze_node_performance(node_id, snapshots)
                
                self.optimizer_metrics.last_updated = datetime.utcnow()
                await asyncio.sleep(15)
            except Exception:
                await asyncio.sleep(15)
    
    async def _analyze_node_performance(self, node_id: str, snapshots: List[PerformanceSnapshot]) -> None:
        """Analyze performance of a node"""
        if not snapshots:
            return
        
        try:
            # Calculate averages
            avg_cpu = sum(s.cpu_usage for s in snapshots) / len(snapshots)
            avg_memory = sum(s.memory_usage for s in snapshots) / len(snapshots)
            avg_response = sum(s.response_time_ms for s in snapshots) / len(snapshots)
            
            # Update metrics
            self.optimizer_metrics.avg_cpu_usage = avg_cpu
            self.optimizer_metrics.avg_memory_usage = avg_memory
            self.optimizer_metrics.avg_response_time_ms = avg_response
            
            if avg_cpu > self.cpu_threshold or avg_memory > self.memory_threshold:
                self.optimizer_metrics.nodes_under_load += 1
            
            # Make recommendations
            if avg_cpu > 0.9 or avg_memory > 0.9:
                await self._make_recommendation(
                    node_id,
                    ScalingAction.SCALE_UP,
                    ResourceType.CPU if avg_cpu > avg_memory else ResourceType.MEMORY,
                    "High utilization detected",
                    5
                )
            elif avg_cpu < 0.2 and avg_memory < 0.2:
                await self._make_recommendation(
                    node_id,
                    ScalingAction.SCALE_DOWN,
                    None,
                    "Low utilization detected",
                    2
                )
        except Exception:
            pass
    
    async def _make_recommendation(
        self,
        node_id: str,
        action: ScalingAction,
        resource_type: Optional[ResourceType],
        reason: str,
        priority: int
    ) -> bool:
        """Make optimization recommendation"""
        try:
            recommendation = OptimizationRecommendation(
                node_id=node_id,
                action=action,
                resource_type=resource_type,
                reason=reason,
                priority=priority,
                estimated_impact=0.3 + (priority * 0.1)
            )
            
            self.recommendations[recommendation.recommendation_id] = recommendation
            self.optimizer_metrics.recommendations_made += 1
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_recommendation_made(recommendation)
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # AUTO-SCALING
    # ========================================================================
    
    async def execute_scaling_action(self, node_id: str, action: ScalingAction) -> bool:
        """Execute auto-scaling action"""
        if not self.enabled:
            return False
        
        try:
            self.scaling_history.append((node_id, action, datetime.utcnow()))
            self.optimizer_metrics.scaling_actions_taken += 1
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_scaling_action(action, node_id)
            
            return True
        except Exception:
            return False
    
    async def can_scale_up(self, node_id: str) -> bool:
        """Check if node can scale up"""
        try:
            # Count recent scale ups
            cutoff = datetime.utcnow() - timedelta(seconds=self.scale_cooldown_seconds)
            recent_scale_ups = sum(
                1 for n, a, ts in self.scaling_history
                if n == node_id and a == ScalingAction.SCALE_UP and ts > cutoff
            )
            return recent_scale_ups < self.max_scale_up_count
        except Exception:
            return False
    
    async def can_scale_down(self, node_id: str) -> bool:
        """Check if node can scale down"""
        try:
            # Count recent scale downs
            cutoff = datetime.utcnow() - timedelta(seconds=self.scale_cooldown_seconds)
            recent_scale_downs = sum(
                1 for n, a, ts in self.scaling_history
                if n == node_id and a == ScalingAction.SCALE_DOWN and ts > cutoff
            )
            return recent_scale_downs < self.min_scale_down_count
        except Exception:
            return False
    
    # ========================================================================
    # MANAGEMENT
    # ========================================================================
    
    async def register_peer(self, peer_id: str) -> bool:
        """Register peer node"""
        try:
            self.peers.add(peer_id)
            return True
        except Exception:
            return False
    
    async def add_listener(self, listener: PerformanceOptimizationListener) -> bool:
        """Register performance listener"""
        try:
            self.listeners.append(listener)
            return True
        except Exception:
            return False
    
    async def set_strategy(self, strategy: OptimizationStrategy) -> bool:
        """Set optimization strategy"""
        try:
            self.strategy = strategy
            return True
        except Exception:
            return False
    
    async def set_threshold(self, resource_type: ResourceType, threshold: float) -> bool:
        """Set alert threshold for resource"""
        if not 0.0 <= threshold <= 1.0:
            return False
        
        try:
            if resource_type == ResourceType.CPU:
                self.cpu_threshold = threshold
            elif resource_type == ResourceType.MEMORY:
                self.memory_threshold = threshold
            elif resource_type == ResourceType.NETWORK:
                self.network_threshold = threshold
            elif resource_type == ResourceType.DISK_IO:
                self.disk_io_threshold = threshold
            return True
        except Exception:
            return False
    
    async def get_metrics(self) -> OptimizerMetrics:
        """Get optimizer metrics"""
        return self.optimizer_metrics
    
    async def get_recommendation(self, recommendation_id: str) -> Optional[OptimizationRecommendation]:
        """Get recommendation by ID"""
        return self.recommendations.get(recommendation_id)
    
    async def get_recommendations_for_node(self, node_id: str) -> List[OptimizationRecommendation]:
        """Get recommendations for specific node"""
        return [r for r in self.recommendations.values() if r.node_id == node_id]
    
    async def is_enabled(self) -> bool:
        """Check if optimizer is enabled"""
        return self.enabled
    
    async def get_strategy(self) -> OptimizationStrategy:
        """Get current strategy"""
        return self.strategy
    
    async def get_node_health(self, node_id: str) -> Dict[str, Any]:
        """Get overall health of node"""
        snapshot = await self.get_latest_snapshot(node_id)
        if not snapshot:
            return {'node_id': node_id, 'status': 'unknown'}
        
        # Calculate health score (0.0-1.0, higher is better)
        health = 1.0
        health -= snapshot.cpu_usage * 0.3
        health -= snapshot.memory_usage * 0.3
        health -= snapshot.network_usage * 0.2
        health -= snapshot.disk_io_usage * 0.2
        
        return {
            'node_id': node_id,
            'health_score': max(0.0, health),
            'status': 'healthy' if health > 0.7 else 'degraded' if health > 0.4 else 'critical'
        }
    
    async def get_cluster_health(self) -> Dict[str, Any]:
        """Get overall cluster health"""
        nodes = [self.node_id] + list(self.peers)
        healths = []
        
        for node_id in nodes:
            health = await self.get_node_health(node_id)
            healths.append(health)
        
        if not healths:
            return {'status': 'unknown', 'avg_health': 0.0}
        
        avg_health = sum(h.get('health_score', 0.0) for h in healths) / len(healths)
        
        return {
            'status': 'healthy' if avg_health > 0.7 else 'degraded' if avg_health > 0.4 else 'critical',
            'avg_health': round(avg_health, 4),
            'nodes_total': len(nodes),
            'nodes_healthy': sum(1 for h in healths if h.get('status') == 'healthy')
        }
