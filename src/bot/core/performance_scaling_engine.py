"""
Performance Scaling Engine for optimization and auto-scaling

Implements:
- Performance analysis of nodes
- Optimization recommendations generation
- Auto-scaling decisions and execution
- Scaling history tracking
"""

import asyncio
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional

from .performance_optimizer_models import (
    OptimizationStrategy,
    ResourceType,
    ScalingAction,
    PerformanceSnapshot,
    OptimizationRecommendation,
    OptimizerMetrics,
    PerformanceOptimizationListener,
)


class PerformanceScalingEngine:
    """
    Analyzes performance and makes scaling decisions
    
    Responsible for:
    - Performance analysis of nodes
    - Optimization recommendations
    - auto-scaling action execution
    - Scaling history and cooldown management
    """
    
    def __init__(self):
        self.recommendations: Dict[str, OptimizationRecommendation] = {}
        self.scaling_history: List[tuple[str, ScalingAction, datetime]] = []
        self.optimizer_metrics = OptimizerMetrics()
        self.listeners: List[PerformanceOptimizationListener] = []
        self.enabled = False
        self.strategy = OptimizationStrategy.BALANCED
        
        # Scaling limits
        self.max_scale_up_count = 3
        self.min_scale_down_count = 1
        self.scale_cooldown_seconds = 300
    
    async def analyze_node_performance(
        self,
        node_id: str,
        snapshots: List[PerformanceSnapshot]
    ) -> None:
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
            
            # Check thresholds (using fixed values for now)
            cpu_threshold = 0.8
            memory_threshold = 0.85
            
            if avg_cpu > cpu_threshold or avg_memory > memory_threshold:
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
    
    async def execute_scaling_action(self, node_id: str, action: ScalingAction) -> bool:
        """Execute auto-scaling action"""
        if not self.enabled:
            return False
        
        try:
            self.scaling_history.append((node_id, action, datetime.now(UTC)))
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
            cutoff = datetime.now(UTC) - timedelta(seconds=self.scale_cooldown_seconds)
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
            cutoff = datetime.now(UTC) - timedelta(seconds=self.scale_cooldown_seconds)
            recent_scale_downs = sum(
                1 for n, a, ts in self.scaling_history
                if n == node_id and a == ScalingAction.SCALE_DOWN and ts > cutoff
            )
            return recent_scale_downs < self.min_scale_down_count
        except Exception:
            return False
    
    async def analysis_loop(self, get_snapshots_fn, node_ids_fn) -> None:
        """Background loop for performance analysis"""
        while self.enabled:
            try:
                # Get node list
                node_ids = node_ids_fn()
                
                # Analyze metrics and make recommendations
                for node_id in node_ids:
                    snapshots = await get_snapshots_fn(node_id, 5)
                    if snapshots:
                        await self.analyze_node_performance(node_id, snapshots)
                
                self.optimizer_metrics.last_updated = datetime.now(UTC)
                await asyncio.sleep(15)
            except Exception:
                await asyncio.sleep(15)
    
    def set_enabled(self, enabled: bool) -> None:
        """Set engine enabled state"""
        self.enabled = enabled
    
    def set_strategy(self, strategy: OptimizationStrategy) -> None:
        """Set optimization strategy"""
        self.strategy = strategy
    
    def add_listener(self, listener: PerformanceOptimizationListener) -> None:
        """Add scaling listener"""
        if listener not in self.listeners:
            self.listeners.append(listener)
    
    def get_recommendation(self, recommendation_id: str) -> Optional[OptimizationRecommendation]:
        """Get recommendation by ID"""
        return self.recommendations.get(recommendation_id)
    
    def get_recommendations_for_node(self, node_id: str) -> List[OptimizationRecommendation]:
        """Get recommendations for specific node"""
        return [r for r in self.recommendations.values() if r.node_id == node_id]
