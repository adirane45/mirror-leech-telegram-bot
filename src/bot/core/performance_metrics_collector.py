"""
Performance Metrics Collector for resource tracking

Implements:
- Resource metrics collection and storage
- Performance snapshot management
- Metrics listener notifications
"""

import asyncio
from datetime import datetime, UTC
from typing import Dict, List, Optional

from .performance_optimizer_models import (
    ResourceMetric,
    PerformanceSnapshot,
    PerformanceOptimizationListener,
)


class PerformanceMetricsCollector:
    """
    Collects and manages performance metrics
    
    Responsible for:
    - Recording individual metrics
    - Managing performance snapshots
    - Threshold violation notifications
    - Background metrics collection loop
    """
    
    def __init__(self):
        self.snapshots: Dict[str, List[PerformanceSnapshot]] = {}
        self.metrics: Dict[str, ResourceMetric] = {}
        self.listeners: List[PerformanceOptimizationListener] = []
        self.enabled = False
        self.node_id = ""
        self.peers = set()
    
    async def record_metric(self, metric: ResourceMetric) -> bool:
        """Record a resource metric"""
        if not self.enabled:
            return False
        
        try:
            self.metrics[f"{metric.node_id}_{metric.resource_type.value}"] = metric
            
            # Track in snapshots
            if metric.node_id not in self.snapshots:
                self.snapshots[metric.node_id] = []
            
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
    
    async def collection_loop(self) -> None:
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
    
    def set_enabled(self, enabled: bool) -> None:
        """Set collector enabled state"""
        self.enabled = enabled
    
    def set_node_info(self, node_id: str, peers: set) -> None:
        """Set node information"""
        self.node_id = node_id
        self.peers = peers
    
    def add_listener(self, listener: PerformanceOptimizationListener) -> None:
        """Add metrics listener"""
        if listener not in self.listeners:
            self.listeners.append(listener)
    
    def clear_metrics(self) -> None:
        """Clear all recorded metrics"""
        self.snapshots.clear()
        self.metrics.clear()
