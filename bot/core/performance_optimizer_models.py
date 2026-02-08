"""
Performance Optimizer Models - Data structures for resource management and auto-scaling

Includes:
- Optimization strategy and resource type enumerations
- Performance metrics and recommendations dataclasses
- Performance listener interface
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, Optional, Any


# ============================================================================
# ENUMS
# ============================================================================

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


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class ResourceMetric:
    """Resource metric at a point in time"""
    resource_type: ResourceType
    value: float  # 0.0-1.0 or other metric value
    threshold: float = 0.8  # Alert threshold
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
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
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
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
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
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
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    
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


# ============================================================================
# ABSTRACT LISTENERS
# ============================================================================

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
