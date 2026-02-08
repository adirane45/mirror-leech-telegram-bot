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
from datetime import datetime, UTC
from typing import Dict, List, Set, Optional, Any

# Import models
from .performance_optimizer_models import (
    OptimizationStrategy,
    ResourceType,
    ScalingAction,
    PerformanceSnapshot,
    OptimizationRecommendation,
    OptimizerMetrics,
    PerformanceOptimizationListener,
)

# Import specialized components
from .performance_metrics_collector import PerformanceMetricsCollector
from .performance_scaling_engine import PerformanceScalingEngine


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
        self.peers: Set[str] = set()
        
        # Component delegation
        self.collector = PerformanceMetricsCollector()
        self.scaling_engine = PerformanceScalingEngine()
        
        # Thresholds
        self.cpu_threshold = 0.8
        self.memory_threshold = 0.85
        self.network_threshold = 0.8
        self.disk_io_threshold = 0.75
        
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
            
            # Configure components
            self.collector.set_enabled(True)
            self.collector.set_node_info(self.node_id, self.peers)
            self.scaling_engine.set_enabled(True)
            self.scaling_engine.set_strategy(strategy)
            
            # Start background tasks
            self._collector_task = asyncio.create_task(self.collector.collection_loop())
            self._analyzer_task = asyncio.create_task(
                self.scaling_engine.analysis_loop(
                    self.collector.get_node_snapshots,
                    lambda: [self.node_id] + list(self.peers)
                )
            )
            
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
            self.collector.set_enabled(False)
            self.scaling_engine.set_enabled(False)
            
            if self._collector_task:
                self._collector_task.cancel()
            if self._analyzer_task:
                self._analyzer_task.cancel()
            
            await asyncio.sleep(0.1)
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # METRICS DELEGATION
    # ========================================================================
    
    async def record_metric(self, metric):
        """Record a resource metric"""
        return await self.collector.record_metric(metric)
    
    async def record_snapshot(self, snapshot: PerformanceSnapshot) -> bool:
        """Record performance snapshot"""
        return await self.collector.record_snapshot(snapshot)
    
    async def get_latest_snapshot(self, node_id: str) -> Optional[PerformanceSnapshot]:
        """Get latest performance snapshot for node"""
        return await self.collector.get_latest_snapshot(node_id)
    
    async def get_node_snapshots(self, node_id: str, count: int = 10) -> List[PerformanceSnapshot]:
        """Get last N snapshots for node"""
        return await self.collector.get_node_snapshots(node_id, count)
    
    # ========================================================================
    # AUTO-SCALING DELEGATION
    # ========================================================================
    
    async def execute_scaling_action(self, node_id: str, action: ScalingAction) -> bool:
        """Execute auto-scaling action"""
        return await self.scaling_engine.execute_scaling_action(node_id, action)
    
    async def can_scale_up(self, node_id: str) -> bool:
        """Check if node can scale up"""
        return await self.scaling_engine.can_scale_up(node_id)
    
    async def can_scale_down(self, node_id: str) -> bool:
        """Check if node can scale down"""
        return await self.scaling_engine.can_scale_down(node_id)
    
    # ========================================================================
    # MANAGEMENT
    # ========================================================================
    
    async def register_peer(self, peer_id: str) -> bool:
        """Register peer node"""
        try:
            self.peers.add(peer_id)
            self.collector.set_node_info(self.node_id, self.peers)
            return True
        except Exception:
            return False
    
    async def add_listener(self, listener: PerformanceOptimizationListener) -> bool:
        """Register performance listener"""
        try:
            self.collector.add_listener(listener)
            self.scaling_engine.add_listener(listener)
            return True
        except Exception:
            return False
    
    async def set_strategy(self, strategy: OptimizationStrategy) -> bool:
        """Set optimization strategy"""
        try:
            self.strategy = strategy
            self.scaling_engine.set_strategy(strategy)
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
        return self.scaling_engine.optimizer_metrics
    
    async def get_recommendation(self, recommendation_id: str) -> Optional[OptimizationRecommendation]:
        """Get recommendation by ID"""
        return self.scaling_engine.get_recommendation(recommendation_id)
    
    async def get_recommendations_for_node(self, node_id: str) -> List[OptimizationRecommendation]:
        """Get recommendations for specific node"""
        return self.scaling_engine.get_recommendations_for_node(node_id)
    
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
