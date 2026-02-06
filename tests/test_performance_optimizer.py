"""
Test suite for Performance Optimizer
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from bot.core.performance_optimizer import (
    PerformanceOptimizer, ResourceMetric, PerformanceSnapshot, OptimizationRecommendation,
    OptimizerMetrics, PerformanceOptimizationListener,
    OptimizationStrategy, ResourceType, ScalingAction
)


class MockPerformanceListener(PerformanceOptimizationListener):
    """Test listener implementation"""
    
    def __init__(self):
        self.metrics_collected = []
        self.thresholds_exceeded = []
        self.recommendations_made = []
        self.scaling_actions = []
    
    async def on_metric_collected(self, metric: ResourceMetric) -> None:
        self.metrics_collected.append(metric)
    
    async def on_threshold_exceeded(self, metric: ResourceMetric) -> None:
        self.thresholds_exceeded.append(metric)
    
    async def on_recommendation_made(self, recommendation: OptimizationRecommendation) -> None:
        self.recommendations_made.append(recommendation)
    
    async def on_scaling_action(self, action: ScalingAction, node_id: str) -> None:
        self.scaling_actions.append((action, node_id))


@pytest.fixture
def performance_optimizer():
    """Get performance optimizer instance"""
    optimizer = PerformanceOptimizer.get_instance()
    # Reset state
    optimizer.enabled = False
    optimizer.node_id = ""
    optimizer.snapshots.clear()
    optimizer.metrics.clear()
    optimizer.recommendations.clear()
    optimizer.scaling_history.clear()
    optimizer.peers.clear()
    optimizer.listeners.clear()
    optimizer.optimizer_metrics = OptimizerMetrics()
    
    yield optimizer
    
    # Cleanup
    try:
        asyncio.run(optimizer.stop())
    except:
        pass
    optimizer.enabled = False


class TestPerformanceOptimizerBasic:
    """Test basic optimizer functionality"""
    
    @pytest.mark.asyncio
    async def test_singleton_instance(self, performance_optimizer):
        """Test singleton pattern"""
        o1 = PerformanceOptimizer.get_instance()
        o2 = PerformanceOptimizer.get_instance()
        assert o1 is o2
    
    @pytest.mark.asyncio
    async def test_start_stop(self, performance_optimizer):
        """Test start and stop"""
        optimizer = performance_optimizer
        assert not optimizer.enabled
        
        assert await optimizer.start("test-node")
        assert optimizer.enabled
        assert optimizer.node_id == "test-node"
        assert optimizer.strategy == OptimizationStrategy.BALANCED
        
        assert await optimizer.stop()
        assert not optimizer.enabled
    
    @pytest.mark.asyncio
    async def test_start_with_strategy(self, performance_optimizer):
        """Test start with specific strategy"""
        optimizer = performance_optimizer
        
        assert await optimizer.start("node1", OptimizationStrategy.AGGRESSIVE)
        assert optimizer.strategy == OptimizationStrategy.AGGRESSIVE
    
    @pytest.mark.asyncio
    async def test_is_enabled(self, performance_optimizer):
        """Test is_enabled check"""
        optimizer = performance_optimizer
        assert not await optimizer.is_enabled()
        
        await optimizer.start()
        assert await optimizer.is_enabled()


class TestMetricsCollection:
    """Test metrics collection"""
    
    @pytest.mark.asyncio
    async def test_record_metric(self, performance_optimizer):
        """Test recording metric"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        metric = ResourceMetric(
            resource_type=ResourceType.CPU,
            value=0.5,
            node_id="node1"
        )
        
        assert await optimizer.record_metric(metric)
        assert optimizer.optimizer_metrics.metrics_collected == 1
    
    @pytest.mark.asyncio
    async def test_record_multiple_metrics(self, performance_optimizer):
        """Test recording multiple metrics"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        for i in range(5):
            metric = ResourceMetric(
                resource_type=ResourceType.MEMORY,
                value=0.3 + (i * 0.1),
                node_id=f"node{i}"
            )
            await optimizer.record_metric(metric)
        
        assert optimizer.optimizer_metrics.metrics_collected == 5
    
    @pytest.mark.asyncio
    async def test_record_snapshot(self, performance_optimizer):
        """Test recording snapshot"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        snapshot = PerformanceSnapshot(
            node_id="node1",
            cpu_usage=0.4,
            memory_usage=0.5
        )
        
        assert await optimizer.record_snapshot(snapshot)
        assert "node1" in optimizer.snapshots
        assert len(optimizer.snapshots["node1"]) == 1
    
    @pytest.mark.asyncio
    async def test_snapshot_limit(self, performance_optimizer):
        """Test snapshots are limited to 100 per node"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        for i in range(150):
            snapshot = PerformanceSnapshot(
                node_id="node1",
                cpu_usage=0.3,
                active_tasks=i
            )
            await optimizer.record_snapshot(snapshot)
        
        # Should keep only 100
        assert len(optimizer.snapshots["node1"]) == 100
    
    @pytest.mark.asyncio
    async def test_get_latest_snapshot(self, performance_optimizer):
        """Test getting latest snapshot"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        snapshots = []
        for i in range(3):
            snapshot = PerformanceSnapshot(
                node_id="node1",
                cpu_usage=0.2 + (i * 0.1),
                active_tasks=i
            )
            await optimizer.record_snapshot(snapshot)
            snapshots.append(snapshot)
        
        latest = await optimizer.get_latest_snapshot("node1")
        assert latest is not None
        assert latest.active_tasks == 2
    
    @pytest.mark.asyncio
    async def test_get_node_snapshots(self, performance_optimizer):
        """Test getting node snapshots"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        for i in range(5):
            snapshot = PerformanceSnapshot(node_id="node1")
            await optimizer.record_snapshot(snapshot)
        
        snapshots = await optimizer.get_node_snapshots("node1", 3)
        assert len(snapshots) == 3


class TestThresholds:
    """Test threshold management"""
    
    @pytest.mark.asyncio
    async def test_set_cpu_threshold(self, performance_optimizer):
        """Test setting CPU threshold"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        assert await optimizer.set_threshold(ResourceType.CPU, 0.9)
        assert optimizer.cpu_threshold == 0.9
    
    @pytest.mark.asyncio
    async def test_set_memory_threshold(self, performance_optimizer):
        """Test setting memory threshold"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        assert await optimizer.set_threshold(ResourceType.MEMORY, 0.75)
        assert optimizer.memory_threshold == 0.75
    
    @pytest.mark.asyncio
    async def test_invalid_threshold(self, performance_optimizer):
        """Test invalid threshold value"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        assert not await optimizer.set_threshold(ResourceType.CPU, 1.5)
        assert not await optimizer.set_threshold(ResourceType.CPU, -0.1)
    
    @pytest.mark.asyncio
    async def test_threshold_exceeded(self, performance_optimizer):
        """Test threshold exceeded detection"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        listener = MockPerformanceListener()
        await optimizer.add_listener(listener)
        
        # Record metric exceeding threshold
        metric = ResourceMetric(
            resource_type=ResourceType.CPU,
            value=0.9,
            threshold=0.8,
            node_id="node1"
        )
        
        await optimizer.record_metric(metric)
        await asyncio.sleep(0.1)
        
        assert len(listener.thresholds_exceeded) > 0


class TestOptimizationStrategy:
    """Test optimization strategy"""
    
    @pytest.mark.asyncio
    async def test_get_strategy(self, performance_optimizer):
        """Test getting strategy"""
        optimizer = performance_optimizer
        await optimizer.start("node1", OptimizationStrategy.AGGRESSIVE)
        
        strategy = await optimizer.get_strategy()
        assert strategy == OptimizationStrategy.AGGRESSIVE
    
    @pytest.mark.asyncio
    async def test_set_strategy(self, performance_optimizer):
        """Test setting strategy"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        assert await optimizer.set_strategy(OptimizationStrategy.CONSERVATIVE)
        assert optimizer.strategy == OptimizationStrategy.CONSERVATIVE


class TestRecommendations:
    """Test optimization recommendations"""
    
    @pytest.mark.asyncio
    async def test_make_recommendation(self, performance_optimizer):
        """Test making recommendation"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        assert await optimizer._make_recommendation(
            "node1",
            ScalingAction.SCALE_UP,
            ResourceType.CPU,
            "High CPU usage",
            4
        )
        
        assert optimizer.optimizer_metrics.recommendations_made == 1
    
    @pytest.mark.asyncio
    async def test_get_recommendation(self, performance_optimizer):
        """Test getting recommendation"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        await optimizer._make_recommendation(
            "node1",
            ScalingAction.SCALE_UP,
            ResourceType.MEMORY,
            "High memory",
            3
        )
        
        rec_id = list(optimizer.recommendations.keys())[0]
        rec = await optimizer.get_recommendation(rec_id)
        
        assert rec is not None
        assert rec.node_id == "node1"
        assert rec.action == ScalingAction.SCALE_UP
    
    @pytest.mark.asyncio
    async def test_get_recommendations_for_node(self, performance_optimizer):
        """Test getting recommendations for node"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        # Make multiple recommendations
        for i in range(3):
            await optimizer._make_recommendation(
                "node1",
                ScalingAction.SCALE_UP,
                ResourceType.CPU,
                f"Issue {i}",
                2
            )
        
        recommendations = await optimizer.get_recommendations_for_node("node1")
        assert len(recommendations) == 3


class TestAutoScaling:
    """Test auto-scaling functionality"""
    
    @pytest.mark.asyncio
    async def test_execute_scaling_action(self, performance_optimizer):
        """Test executing scaling action"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        assert await optimizer.execute_scaling_action("node1", ScalingAction.SCALE_UP)
        assert optimizer.optimizer_metrics.scaling_actions_taken == 1
        assert len(optimizer.scaling_history) == 1
    
    @pytest.mark.asyncio
    async def test_can_scale_up(self, performance_optimizer):
        """Test can scale up"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        # Should be able to scale up initially
        assert await optimizer.can_scale_up("node1")
        
        # Execute scale up
        for _ in range(3):
            await optimizer.execute_scaling_action("node1", ScalingAction.SCALE_UP)
        
        # Should not be able to scale up more
        assert not await optimizer.can_scale_up("node1")
    
    @pytest.mark.asyncio
    async def test_can_scale_down(self, performance_optimizer):
        """Test can scale down"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        # Should be able to scale down initially
        assert await optimizer.can_scale_down("node1")
        
        # Execute scale down
        await optimizer.execute_scaling_action("node1", ScalingAction.SCALE_DOWN)
        
        # Should not be able to scale down again
        assert not await optimizer.can_scale_down("node1")
    
    @pytest.mark.asyncio
    async def test_scaling_action_listener(self, performance_optimizer):
        """Test scaling action listener"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        listener = MockPerformanceListener()
        await optimizer.add_listener(listener)
        
        await optimizer.execute_scaling_action("node1", ScalingAction.SCALE_UP)
        await asyncio.sleep(0.1)
        
        assert len(listener.scaling_actions) > 0


class TestClusterHealth:
    """Test cluster health evaluation"""
    
    @pytest.mark.asyncio
    async def test_get_node_health(self, performance_optimizer):
        """Test getting node health"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        snapshot = PerformanceSnapshot(
            node_id="node1",
            cpu_usage=0.3,
            memory_usage=0.4,
            network_usage=0.2,
            disk_io_usage=0.1
        )
        await optimizer.record_snapshot(snapshot)
        
        health = await optimizer.get_node_health("node1")
        assert health['node_id'] == "node1"
        assert 'health_score' in health
        assert 'status' in health
        assert health['health_score'] > 0.5  # Should be healthy
    
    @pytest.mark.asyncio
    async def test_node_health_degraded(self, performance_optimizer):
        """Test node health when degraded"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        snapshot = PerformanceSnapshot(
            node_id="node1",
            cpu_usage=0.8,
            memory_usage=0.85,
            network_usage=0.7,
            disk_io_usage=0.6
        )
        await optimizer.record_snapshot(snapshot)
        
        health = await optimizer.get_node_health("node1")
        assert health['status'] in ['degraded', 'critical']
    
    @pytest.mark.asyncio
    async def test_get_cluster_health(self, performance_optimizer):
        """Test getting cluster health"""
        optimizer = performance_optimizer
        await optimizer.start("node1")
        
        # Register peers
        await optimizer.register_peer("node2")
        await optimizer.register_peer("node3")
        
        # Record snapshots for all nodes
        for i in range(1, 4):
            snapshot = PerformanceSnapshot(
                node_id=f"node{i}",
                cpu_usage=0.3,
                memory_usage=0.4
            )
            await optimizer.record_snapshot(snapshot)
        
        health = await optimizer.get_cluster_health()
        assert 'status' in health
        assert 'avg_health' in health
        assert 'nodes_total' in health


class TestPeerManagement:
    """Test peer management"""
    
    @pytest.mark.asyncio
    async def test_register_peer(self, performance_optimizer):
        """Test registering peer"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        assert await optimizer.register_peer("node2")
        assert "node2" in optimizer.peers
    
    @pytest.mark.asyncio
    async def test_multiple_peers(self, performance_optimizer):
        """Test multiple peers"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        for i in range(2, 5):
            await optimizer.register_peer(f"node{i}")
        
        assert len(optimizer.peers) == 3


class TestListeners:
    """Test listener management"""
    
    @pytest.mark.asyncio
    async def test_add_listener(self, performance_optimizer):
        """Test adding listener"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        listener = MockPerformanceListener()
        assert await optimizer.add_listener(listener)
        assert listener in optimizer.listeners
    
    @pytest.mark.asyncio
    async def test_metric_collected_listener(self, performance_optimizer):
        """Test metric collected listener"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        listener = MockPerformanceListener()
        await optimizer.add_listener(listener)
        
        metric = ResourceMetric(
            resource_type=ResourceType.CPU,
            value=0.5,
            node_id="node1"
        )
        
        await optimizer.record_metric(metric)
        await asyncio.sleep(0.1)
        
        assert len(listener.metrics_collected) > 0


class TestMetrics:
    """Test metrics tracking"""
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, performance_optimizer):
        """Test getting metrics"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        metrics = await optimizer.get_metrics()
        assert metrics.metrics_collected == 0
        assert metrics.recommendations_made == 0
    
    @pytest.mark.asyncio
    async def test_metrics_updates(self, performance_optimizer):
        """Test metrics updates"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        # Record metric
        metric = ResourceMetric(
            resource_type=ResourceType.CPU,
            value=0.5,
            node_id="node1"
        )
        await optimizer.record_metric(metric)
        
        metrics = await optimizer.get_metrics()
        assert metrics.metrics_collected == 1
    
    @pytest.mark.asyncio
    async def test_metrics_serialization(self, performance_optimizer):
        """Test metrics can be serialized"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        metrics = await optimizer.get_metrics()
        data = metrics.to_dict()
        
        assert 'metrics_collected' in data
        assert 'recommendations_made' in data
        assert 'last_updated' in data


class TestResourceMetricSerialization:
    """Test resource metric serialization"""
    
    def test_metric_to_dict(self):
        """Test metric serialization"""
        metric = ResourceMetric(
            resource_type=ResourceType.CPU,
            value=0.75,
            threshold=0.8,
            node_id="node1"
        )
        
        data = metric.to_dict()
        assert data['resource_type'] == 'cpu'
        assert data['value'] == 0.75
        assert data['exceeds_threshold'] is False
    
    def test_snapshot_to_dict(self):
        """Test snapshot serialization"""
        snapshot = PerformanceSnapshot(
            node_id="node1",
            cpu_usage=0.5,
            memory_usage=0.6
        )
        
        data = snapshot.to_dict()
        assert data['node_id'] == "node1"
        assert data['cpu_usage'] == 0.5
        assert data['memory_usage'] == 0.6
    
    def test_recommendation_to_dict(self):
        """Test recommendation serialization"""
        rec = OptimizationRecommendation(
            node_id="node1",
            action=ScalingAction.SCALE_UP,
            resource_type=ResourceType.CPU,
            reason="High usage",
            priority=4
        )
        
        data = rec.to_dict()
        assert data['node_id'] == "node1"
        assert data['action'] == "scale_up"
        assert data['resource_type'] == "cpu"


class TestConcurrency:
    """Test concurrent operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_metric_recording(self, performance_optimizer):
        """Test concurrent metric recording"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        metrics = [
            ResourceMetric(
                resource_type=ResourceType.CPU,
                value=0.3 + (i * 0.1),
                node_id=f"node{i}"
            ) for i in range(10)
        ]
        
        # Record concurrently
        results = await asyncio.gather(*[
            optimizer.record_metric(m) for m in metrics
        ])
        
        assert all(results)
        assert optimizer.optimizer_metrics.metrics_collected == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_snapshots(self, performance_optimizer):
        """Test concurrent snapshot recording"""
        optimizer = performance_optimizer
        await optimizer.start()
        
        # Stop background tasks to avoid interference
        if optimizer._collector_task:
            optimizer._collector_task.cancel()
        
        # Clear any existing snapshots
        optimizer.snapshots.clear()
        
        snapshots = [
            PerformanceSnapshot(
                node_id=f"testnode{i}",  # Use distinct node IDs
                cpu_usage=0.3
            ) for i in range(5)
        ]
        
        # Record concurrently
        results = await asyncio.gather(*[
            optimizer.record_snapshot(s) for s in snapshots
        ])
        
        assert all(results)
        # Should have exactly 5 test nodes
        test_nodes = [k for k in optimizer.snapshots.keys() if k.startswith('testnode')]
        assert len(test_nodes) == 5
