"""
Adaptive Concurrency for Phase 8 Advanced Intelligence

Dynamic thread tuning with PID controller algorithm for real-time optimization.
Automatically adjusts concurrency levels based on system load and performance.

Features:
- PID controller for adaptive tuning
- Real-time performance monitoring
- Thread pool auto-scaling
- Resource utilization optimization
- Feedback loop control
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable, Any
from collections import deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    timestamp: datetime
    active_tasks: int
    queue_size: int
    avg_latency_ms: float
    throughput_per_sec: float
    cpu_usage_percent: float
    memory_usage_percent: float
    error_rate: float


@dataclass
class PIDParameters:
    """PID controller parameters"""
    kp: float = 1.0  # Proportional gain
    ki: float = 0.1  # Integral gain
    kd: float = 0.05  # Derivative gain
    setpoint: float = 0.7  # Target utilization (70%)
    min_output: int = 1  # Minimum concurrency
    max_output: int = 100  # Maximum concurrency


class PIDController:
    """
    PID (Proportional-Integral-Derivative) controller for adaptive tuning.
    
    Adjusts concurrency based on system utilization to maintain optimal performance.
    """
    
    def __init__(self, parameters: PIDParameters):
        """
        Initialize PID controller.
        
        Args:
            parameters: PID parameters (Kp, Ki, Kd, setpoint)
        """
        self.params = parameters
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_time = time.time()
        
        logger.info(
            f"PIDController initialized: Kp={parameters.kp}, "
            f"Ki={parameters.ki}, Kd={parameters.kd}, "
            f"setpoint={parameters.setpoint}"
        )
    
    def compute(self, current_value: float) -> int:
        """
        Compute new control output based on current value.
        
        Args:
            current_value: Current system utilization (0.0 to 1.0)
            
        Returns:
            New concurrency level
        """
        current_time = time.time()
        dt = current_time - self.previous_time
        
        if dt <= 0:
            dt = 0.01  # Prevent division by zero
        
        # Calculate error
        error = self.params.setpoint - current_value
        
        # Proportional term
        p_term = self.params.kp * error
        
        # Integral term
        self.integral += error * dt
        i_term = self.params.ki * self.integral
        
        # Derivative term
        derivative = (error - self.previous_error) / dt
        d_term = self.params.kd * derivative
        
        # Calculate output
        output = p_term + i_term + d_term
        
        # Update state
        self.previous_error = error
        self.previous_time = current_time
        
        # Clamp output to valid range
        concurrency = int(output + (self.params.min_output + self.params.max_output) / 2)
        concurrency = max(self.params.min_output, min(self.params.max_output, concurrency))
        
        logger.debug(
            f"PID compute: error={error:.3f}, P={p_term:.3f}, "
            f"I={i_term:.3f}, D={d_term:.3f}, output={concurrency}"
        )
        
        return concurrency
    
    def reset(self):
        """Reset controller state"""
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_time = time.time()
        logger.debug("PID controller reset")


class AdaptiveThreadPool:
    """
    Thread pool with adaptive concurrency.
    
    Automatically adjusts pool size based on workload and performance metrics.
    """
    
    def __init__(
        self,
        initial_size: int = 10,
        min_size: int = 1,
        max_size: int = 100,
        adjustment_interval_sec: float = 5.0
    ):
        """
        Initialize adaptive thread pool.
        
        Args:
            initial_size: Initial thread pool size
            min_size: Minimum pool size
            max_size: Maximum pool size
            adjustment_interval_sec: How often to adjust size
        """
        self.min_size = min_size
        self.max_size = max_size
        self.current_size = initial_size
        self.adjustment_interval = adjustment_interval_sec
        
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.total_latency_ms = 0.0
        
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.running = False
        
        self._lock = asyncio.Lock()
        
        logger.info(
            f"AdaptiveThreadPool initialized: size={initial_size}, "
            f"range=[{min_size}, {max_size}]"
        )
    
    async def start(self):
        """Start the thread pool"""
        self.running = True
        
        # Start initial workers
        for _ in range(self.current_size):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)
        
        logger.info(f"Thread pool started with {self.current_size} workers")
    
    async def stop(self):
        """Stop the thread pool"""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("Thread pool stopped")
    
    async def submit(self, coro):
        """Submit a coroutine for execution"""
        await self.task_queue.put(coro)
    
    async def _worker(self):
        """Worker coroutine that processes tasks"""
        while self.running:
            try:
                # Get task from queue with timeout
                coro = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                # Execute task
                async with self._lock:
                    self.active_tasks += 1
                
                start_time = time.perf_counter()
                
                try:
                    await coro
                    self.completed_tasks += 1
                except Exception as e:
                    logger.error(f"Task failed: {e}")
                    self.failed_tasks += 1
                
                latency_ms = (time.perf_counter() - start_time) * 1000
                self.total_latency_ms += latency_ms
                
                async with self._lock:
                    self.active_tasks -= 1
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    async def adjust_size(self, new_size: int):
        """
        Adjust pool size.
        
        Args:
            new_size: New pool size
        """
        new_size = max(self.min_size, min(self.max_size, new_size))
        
        if new_size == self.current_size:
            return
        
        if new_size > self.current_size:
            # Add workers
            diff = new_size - self.current_size
            for _ in range(diff):
                worker = asyncio.create_task(self._worker())
                self.workers.append(worker)
            
            logger.info(f"Scaled up: {self.current_size} -> {new_size}")
        else:
            # Remove workers
            diff = self.current_size - new_size
            for _ in range(diff):
                if self.workers:
                    worker = self.workers.pop()
                    worker.cancel()
            
            logger.info(f"Scaled down: {self.current_size} -> {new_size}")
        
        self.current_size = new_size
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        avg_latency = (
            self.total_latency_ms / self.completed_tasks
            if self.completed_tasks > 0 else 0
        )
        
        error_rate = (
            self.failed_tasks / (self.completed_tasks + self.failed_tasks)
            if (self.completed_tasks + self.failed_tasks) > 0 else 0
        )
        
        return {
            "pool_size": self.current_size,
            "active_tasks": self.active_tasks,
            "queue_size": self.task_queue.qsize(),
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "avg_latency_ms": avg_latency,
            "error_rate": error_rate
        }


class AdaptiveConcurrencyController:
    """
    Main controller for adaptive concurrency system.
    
    Uses PID control to dynamically adjust concurrency based on:
    - System utilization
    - Task latency
    - Error rates
    - Resource availability
    """
    
    def __init__(
        self,
        initial_concurrency: int = 10,
        pid_params: Optional[PIDParameters] = None,
        adjustment_interval_sec: float = 5.0
    ):
        """
        Initialize adaptive concurrency controller.
        
        Args:
            initial_concurrency: Initial concurrency level
            pid_params: PID parameters (uses defaults if None)
            adjustment_interval_sec: How often to adjust
        """
        self.pid = PIDController(pid_params or PIDParameters())
        self.thread_pool = AdaptiveThreadPool(
            initial_size=initial_concurrency,
            min_size=self.pid.params.min_output,
            max_size=self.pid.params.max_output,
            adjustment_interval_sec=adjustment_interval_sec
        )
        
        self.adjustment_interval = adjustment_interval_sec
        self.metrics_history: deque = deque(maxlen=100)
        self.adjustment_log: List[Dict] = []
        
        self.running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info("AdaptiveConcurrencyController initialized")
    
    async def start(self):
        """Start the adaptive concurrency system"""
        self.running = True
        
        # Start thread pool
        await self.thread_pool.start()
        
        # Start monitoring loop
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Adaptive concurrency started")
    
    async def stop(self):
        """Stop the adaptive concurrency system"""
        self.running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        await self.thread_pool.stop()
        
        logger.info("Adaptive concurrency stopped")
    
    async def submit_task(self, coro):
        """Submit a task for execution"""
        await self.thread_pool.submit(coro)
    
    async def _monitoring_loop(self):
        """Monitoring loop that adjusts concurrency"""
        while self.running:
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Calculate current utilization
                utilization = self._calculate_utilization(metrics)
                
                # Compute new concurrency level
                new_concurrency = self.pid.compute(utilization)
                
                # Adjust thread pool
                await self.thread_pool.adjust_size(new_concurrency)
                
                # Log adjustment
                self.adjustment_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "utilization": utilization,
                    "old_concurrency": self.thread_pool.current_size,
                    "new_concurrency": new_concurrency,
                    "active_tasks": metrics.active_tasks,
                    "queue_size": metrics.queue_size
                })
                
                # Keep log size manageable
                if len(self.adjustment_log) > 1000:
                    self.adjustment_log.pop(0)
                
                # Wait for next adjustment
                await asyncio.sleep(self.adjustment_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(1)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        pool_metrics = self.thread_pool.get_metrics()
        
        # Calculate throughput
        if self.metrics_history:
            last_metrics = self.metrics_history[-1]
            time_delta = (datetime.now() - last_metrics.timestamp).total_seconds()
            task_delta = self.thread_pool.completed_tasks - last_metrics.active_tasks
            throughput = task_delta / time_delta if time_delta > 0 else 0
        else:
            throughput = 0
        
        # Mock CPU/memory usage (in production, use psutil)
        cpu_usage = min(pool_metrics["active_tasks"] / self.thread_pool.current_size, 1.0) * 100
        memory_usage = 50.0  # Mock value
        
        return PerformanceMetrics(
            timestamp=datetime.now(),
            active_tasks=pool_metrics["active_tasks"],
            queue_size=pool_metrics["queue_size"],
            avg_latency_ms=pool_metrics["avg_latency_ms"],
            throughput_per_sec=throughput,
            cpu_usage_percent=cpu_usage,
            memory_usage_percent=memory_usage,
            error_rate=pool_metrics["error_rate"]
        )
    
    def _calculate_utilization(self, metrics: PerformanceMetrics) -> float:
        """
        Calculate system utilization (0.0 to 1.0).
        
        Combines multiple factors:
        - Task queue size
        - Active tasks vs capacity
        - CPU usage
        - Error rate
        """
        # Queue pressure (0-1)
        queue_pressure = min(metrics.queue_size / 100.0, 1.0)
        
        # Task utilization (0-1)
        task_utilization = (
            metrics.active_tasks / self.thread_pool.current_size
            if self.thread_pool.current_size > 0 else 0
        )
        
        # CPU utilization (0-1)
        cpu_utilization = metrics.cpu_usage_percent / 100.0
        
        # Error penalty
        error_penalty = metrics.error_rate * 0.5
        
        # Combined utilization
        utilization = (
            queue_pressure * 0.3 +
            task_utilization * 0.4 +
            cpu_utilization * 0.3 -
            error_penalty
        )
        
        return max(0.0, min(1.0, utilization))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        pool_metrics = self.thread_pool.get_metrics()
        
        # Recent adjustments
        recent_adjustments = self.adjustment_log[-10:] if self.adjustment_log else []
        
        return {
            "current_concurrency": self.thread_pool.current_size,
            "pool_metrics": pool_metrics,
            "pid_parameters": {
                "kp": self.pid.params.kp,
                "ki": self.pid.params.ki,
                "kd": self.pid.params.kd,
                "setpoint": self.pid.params.setpoint
            },
            "total_adjustments": len(self.adjustment_log),
            "recent_adjustments": recent_adjustments
        }
    
    def tune_pid(self, kp: float, ki: float, kd: float):
        """
        Tune PID parameters.
        
        Args:
            kp: Proportional gain
            ki: Integral gain
            kd: Derivative gain
        """
        self.pid.params.kp = kp
        self.pid.params.ki = ki
        self.pid.params.kd = kd
        self.pid.reset()
        
        logger.info(f"PID tuned: Kp={kp}, Ki={ki}, Kd={kd}")


class WorkloadAnalyzer:
    """
    Analyzes workload patterns to optimize concurrency settings.
    
    Features:
    - Pattern detection (bursty, steady, random)
    - Optimal concurrency recommendations
    - Performance prediction
    """
    
    def __init__(self):
        """Initialize workload analyzer"""
        self.workload_samples:deque = deque(maxlen=1000)
        self.patterns: Dict[str, float] = {}
        
        logger.info("WorkloadAnalyzer initialized")
    
    def record_sample(self, metrics: PerformanceMetrics):
        """Record a workload sample"""
        self.workload_samples.append(metrics)
    
    def analyze_pattern(self) -> str:
        """
        Analyze workload pattern.
        
        Returns:
            Pattern type: 'steady', 'bursty', 'random', or 'unknown'
        """
        if len(self.workload_samples) < 10:
            return "unknown"
        
        # Calculate variance in active tasks
        task_counts = [m.active_tasks for m in self.workload_samples]
        avg = sum(task_counts) / len(task_counts)
        variance = sum((x - avg) ** 2 for x in task_counts) / len(task_counts)
        std_dev = variance ** 0.5
        
        # Classify pattern
        if std_dev < avg * 0.2:
            return "steady"
        elif std_dev > avg * 0.8:
            return "bursty"
        else:
            return "random"
    
    def recommend_concurrency(self) -> int:
        """Recommend optimal concurrency based on pattern"""
        pattern = self.analyze_pattern()
        
        if pattern == "steady":
            # Steady workload: moderate concurrency
            return 20
        elif pattern == "bursty":
            # Bursty workload: high concurrency
            return 50
        else:
            # Random/unknown: conservative
            return 15
    
    def get_analysis(self) -> Dict[str, Any]:
        """Get workload analysis"""
        if not self.workload_samples:
            return {"pattern": "unknown", "samples": 0}
        
        pattern = self.analyze_pattern()
        recommended = self.recommend_concurrency()
        
        return {
            "pattern": pattern,
            "samples": len(self.workload_samples),
            "recommended_concurrency": recommended
        }
