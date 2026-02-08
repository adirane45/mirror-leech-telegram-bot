"""
Worker Autoscaler - Auto-scale Celery workers based on queue depth
Monitors task queue and auto-spawns/kills workers
- Scale up when queue depth > threshold
- Scale down when idle
- Distribute tasks across optimal workers
- Track performance metrics

Enhanced by: justadi
Date: February 8, 2026
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import subprocess

from .. import LOGGER


class ScalingAction(Enum):
    """Auto-scaling actions"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"


class WorkerPool:
    """Manages Celery worker pool"""
    
    def __init__(self):
        self.min_workers = 2
        self.max_workers = 10
        self.current_workers = 2
        self.scale_factor = 0.75  # Scale when queue depth exceeds this factor
    
    async def get_active_worker_count(self) -> int:
        """Get actual active worker count from Celery"""
        try:
            from .celery_app import celery_app
            stats = celery_app.control.inspect().active()
            return len(stats) if stats else 0
        except Exception as e:
            LOGGER.error(f"Error getting worker count: {e}")
            return self.current_workers
    
    async def scale_workers(self, target_count: int) -> bool:
        """Scale to target worker count"""
        current = await self.get_active_worker_count()
        target = max(self.min_workers, min(self.max_workers, target_count))
        
        if current == target:
            return True
        
        if current < target:
            # Scale up
            workers_to_add = target - current
            LOGGER.info(f"📈 Scaling UP: Adding {workers_to_add} workers (current: {current} → target: {target})")
            return await self._spawn_workers(workers_to_add)
        else:
            # Scale down
            workers_to_remove = current - target
            LOGGER.info(f"📉 Scaling DOWN: Removing {workers_to_remove} workers (current: {current} → target: {target})")
            return await self._remove_workers(workers_to_remove)
    
    async def _spawn_workers(self, count: int) -> bool:
        """Spawn new worker processes"""
        try:
            for i in range(count):
                cmd = [
                    "celery", "-A", "bot.core.celery_app", "worker",
                    "--loglevel=info",
                    "--concurrency=2",
                    "--max-tasks-per-child=100",
                    "-Q", "default,download,upload,high_priority,low_priority",
                ]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            await asyncio.sleep(2)  # Wait for workers to initialize
            self.current_workers += count
            LOGGER.info(f"✅ Successfully spawned {count} workers")
            return True
        except Exception as e:
            LOGGER.error(f"❌ Failed to spawn workers: {e}")
            return False
    
    async def _remove_workers(self, count: int) -> bool:
        """Remove worker processes gracefully"""
        try:
            from .celery_app import celery_app
            active_workers = celery_app.control.inspect().active()
            
            if not active_workers:
                LOGGER.warning("No active workers to remove")
                return False
            
            workers_to_remove = list(active_workers.keys())[:count]
            
            for worker_name in workers_to_remove:
                celery_app.control.shutdown(destination=[worker_name])
            
            await asyncio.sleep(2)  # Wait for shutdown
            self.current_workers = max(self.min_workers, self.current_workers - count)
            LOGGER.info(f"✅ Successfully removed {count} workers")
            return True
        except Exception as e:
            LOGGER.error(f"❌ Failed to remove workers: {e}")
            return False


class WorkerAutoscaler:
    """Singleton worker autoscaler with auto-scaling"""
    
    _instance: Optional['WorkerAutoscaler'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._enabled = False
        self.worker_pool = WorkerPool()
        
        # Queue monitoring
        self.high_queue_threshold = 50  # Tasks in queue
        self.medium_queue_threshold = 25
        self.low_queue_threshold = 5
        
        # Scaling rules
        self.queue_depth_history = []  # Rolling window of queue depths
        self.window_size = 5  # Check last 5 samples
        
        # Metrics
        self.last_scale_action: Optional[ScalingAction] = None
        self.last_scale_time: Optional[datetime] = None
        self.scale_history: List[Dict] = []
        
        # Background task
        self.monitor_task: Optional[asyncio.Task] = None
        
        LOGGER.info("✅ Worker Autoscaler initialized")
    
    @classmethod
    def get_instance(cls) -> 'WorkerAutoscaler':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # ==================== SETUP ====================
    
    async def enable(self, check_interval: float = 30.0) -> bool:
        """
        Enable worker autoscaler with monitoring
        
        Args:
            check_interval: Seconds between scaling checks
        """
        async with self._lock:
            self._enabled = True
            self.monitor_task = asyncio.create_task(
                self._monitor_loop(check_interval)
            )
            LOGGER.info(f"✅ Worker Autoscaler enabled (check interval: {check_interval}s)")
            return True
    
    async def disable(self) -> bool:
        """Disable worker autoscaler"""
        async with self._lock:
            self._enabled = False
            if self.monitor_task:
                self.monitor_task.cancel()
            LOGGER.info("❌ Worker Autoscaler disabled")
            return True
    
    # ==================== MONITORING ====================
    
    async def _monitor_loop(self, interval: float):
        """Background monitoring loop"""
        while self._enabled:
            try:
                await asyncio.sleep(interval)
                await self._check_and_scale()
            except Exception as e:
                LOGGER.error(f"Error in worker autoscaler monitoring: {e}")
    
    async def _get_queue_depth(self) -> int:
        """Get total pending tasks in all queues"""
        try:
            from .celery_app import celery_app
            
            # Get active tasks
            active = celery_app.control.inspect().active()
            active_count = sum(len(tasks) for tasks in active.values()) if active else 0
            
            # Get reserved tasks (queued for execution)
            reserved = celery_app.control.inspect().reserved()
            reserved_count = sum(len(tasks) for tasks in reserved.values()) if reserved else 0
            
            return active_count + reserved_count
        except Exception as e:
            LOGGER.debug(f"Error getting queue depth: {e}")
            return 0
    
    async def _check_and_scale(self):
        """Check queue depth and scale if needed"""
        queue_depth = await self._get_queue_depth()
        self.queue_depth_history.append(queue_depth)
        
        # Keep rolling window
        if len(self.queue_depth_history) > self.window_size:
            self.queue_depth_history.pop(0)
        
        # Get average depth from last window
        avg_depth = sum(self.queue_depth_history) / len(self.queue_depth_history)
        
        # Determine scaling action
        action = self._determine_scaling_action(avg_depth)
        
        if action == ScalingAction.SCALE_UP:
            target_workers = min(
                self.worker_pool.max_workers,
                self.worker_pool.current_workers + 2
            )
            await self.worker_pool.scale_workers(target_workers)
        
        elif action == ScalingAction.SCALE_DOWN:
            target_workers = max(
                self.worker_pool.min_workers,
                self.worker_pool.current_workers - 1
            )
            await self.worker_pool.scale_workers(target_workers)
        
        # Record action
        if action != ScalingAction.MAINTAIN:
            self.last_scale_action = action
            self.last_scale_time = datetime.now()
            self._record_scaling(action, queue_depth, avg_depth)
    
    def _determine_scaling_action(self, avg_queue_depth: float) -> ScalingAction:
        """Determine if we should scale"""
        # Don't scale too frequently (min 5 min between actions)
        if self.last_scale_time:
            elapsed = (datetime.now() - self.last_scale_time).total_seconds()
            if elapsed < 300:
                return ScalingAction.MAINTAIN
        
        # Scale up if average queue depth is high
        if avg_queue_depth >= self.high_queue_threshold:
            LOGGER.warning(f"⚠️  High queue depth: {avg_queue_depth:.1f} (threshold: {self.high_queue_threshold})")
            return ScalingAction.SCALE_UP
        
        # Scale down if average is low and we have extra workers
        if (avg_queue_depth <= self.low_queue_threshold and 
            self.worker_pool.current_workers > self.worker_pool.min_workers):
            LOGGER.info(f"ℹ️  Low queue depth: {avg_queue_depth:.1f} (threshold: {self.low_queue_threshold})")
            return ScalingAction.SCALE_DOWN
        
        return ScalingAction.MAINTAIN
    
    def _record_scaling(self, action: ScalingAction, queue_depth: int, avg_depth: float):
        """Record scaling action in history"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "action": action.value,
            "queue_depth": queue_depth,
            "avg_depth": avg_depth,
            "workers": self.worker_pool.current_workers,
        }
        self.scale_history.append(record)
        
        # Keep last 100 records
        if len(self.scale_history) > 100:
            self.scale_history = self.scale_history[-100:]
        
        LOGGER.info(f"📊 {action.value.upper()}: queue_depth={queue_depth}, avg={avg_depth:.1f}, workers={self.worker_pool.current_workers}")
    
    # ==================== MANUAL CONTROL ====================
    
    async def scale_to(self, target: int) -> bool:
        """Manually scale to target worker count"""
        if not self._enabled:
            LOGGER.warning("Worker autoscaler not enabled")
            return False
        
        return await self.worker_pool.scale_workers(target)
    
    # ==================== STATUS ====================
    
    async def get_status(self) -> Dict[str, Any]:
        """Get worker autoscaler status"""
        current_workers = await self.worker_pool.get_active_worker_count()
        queue_depth = await self._get_queue_depth()
        
        return {
            "enabled": self._enabled,
            "current_workers": current_workers,
            "min_workers": self.worker_pool.min_workers,
            "max_workers": self.worker_pool.max_workers,
            "queue_depth": queue_depth,
            "last_scale_action": self.last_scale_action.value if self.last_scale_action else None,
            "last_scale_time": self.last_scale_time.isoformat() if self.last_scale_time else None,
            "recent_actions": self.scale_history[-5:] if self.scale_history else [],
        }
    
    def set_thresholds(
        self,
        high: int = 50,
        medium: int = 25,
        low: int = 5
    ) -> bool:
        """Adjust scaling thresholds"""
        self.high_queue_threshold = high
        self.medium_queue_threshold = medium
        self.low_queue_threshold = low
        LOGGER.info(f"📊 Scaling thresholds updated: high={high}, medium={medium}, low={low}")
        return True


# Global instance
worker_autoscaler = WorkerAutoscaler.get_instance()
