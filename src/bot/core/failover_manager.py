"""
Failover Manager - Automatic failure recovery and orchestration (REFACTORED)

Enables:
- Detection of component failures via Health Monitor
- Coordinated failover using Cluster Manager
- Automatic recovery orchestration
- Cascading failure handling
- Recovery state tracking and rollback
- Health-aware service restoration

Integrates Health Monitor for component health and Cluster Manager for coordination
"""

import asyncio
from datetime import datetime, UTC
from typing import Dict, List, Optional

# Import models from failover_models module
from .failover_models import (
    RecoveryStrategy,
    RecoveryState,
    CascadeLevel,
    RecoveryAction,
    RecoveryOperation,
    CascadeEvent,
    RecoveryMetrics,
    RecoveryHandler,
    DefaultRecoveryHandler,
    FailoverEventListener,
)

# Import refactored components
from .failover_recovery_executor import FailoverRecoveryExecutor
from .failover_cascade_detector import FailoverCascadeDetector


class FailoverManager:
    """
    Automatic failover and recovery orchestration (main orchestrator)
    
    Responsibilities:
    - Coordinate failure detection and recovery
    - Integrate recovery executor and cascade detector
    - Manage component failure tracking
    - Expose unified public API
    """
    
    _instance: Optional['FailoverManager'] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize failover manager"""
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        
        # Event listeners
        self.listeners: List[FailoverEventListener] = []
        
        # Initialize specialized components
        self.recovery_executor = FailoverRecoveryExecutor(
            max_concurrent_recoveries=5,
            listeners=self.listeners
        )
        
        self.cascade_detector = FailoverCascadeDetector(
            listeners=self.listeners
        )

        # Backward-compatible attribute aliases
        self.operations = self.recovery_executor.operations
        self.pending_actions = self.recovery_executor.pending_actions
        self.custom_handlers = self.recovery_executor.custom_handlers
        self._recovery_executor_task = self.recovery_executor._executor_task
        self._cascade_monitor_task = self.cascade_detector._monitor_task
        self.component_failures = self.cascade_detector.component_failures
        self.active_cascades = self.cascade_detector.active_cascades
        self._metrics = self.recovery_executor.metrics
        self.cascade_detector.metrics = self._metrics
        
        # Configuration
        self.failure_threshold = 5
        self.enabled = False

    @property
    def metrics(self) -> RecoveryMetrics:
        """Expose recovery metrics for compatibility"""
        return self._metrics

    @metrics.setter
    def metrics(self, value: RecoveryMetrics) -> None:
        self._metrics = value
        self.recovery_executor.metrics = value
        self.cascade_detector.metrics = value
    
    @classmethod
    def get_instance(cls) -> 'FailoverManager':
        """Get singleton instance"""
        return cls()
    
    # ========================================================================
    # INITIALIZATION AND LIFECYCLE
    # ========================================================================
    
    async def start(self) -> bool:
        """Start failover manager"""
        if self.enabled:
            return True
        
        try:
            self.enabled = True
            
            # Start recovery executor
            await self.recovery_executor.start()
            self._recovery_executor_task = self.recovery_executor._executor_task
            
            # Start cascade detector
            await self.cascade_detector.start()
            self._cascade_monitor_task = self.cascade_detector._monitor_task
            
            return True
        except Exception:
            self.enabled = False
            return False
    
    async def stop(self) -> bool:
        """Stop failover manager"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            
            # Stop both components
            await self.recovery_executor.stop()
            await self.cascade_detector.stop()
            self._recovery_executor_task = None
            self._cascade_monitor_task = None
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # FAILURE DETECTION AND RECOVERY
    # ========================================================================
    
    async def on_component_failure(self, component_id: str, component_name: str, error: str) -> bool:
        """
        Called when a component failure is detected
        
        Triggers appropriate recovery strategy based on failure type
        """
        try:
            # Track failure in cascade detector
            await self.cascade_detector.track_component_failure(component_id)
            
            # Get failure count
            failure_count = await self.cascade_detector.get_failure_count(component_id)
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_failure_detected(component_id, error)
            
            # Determine recovery strategy
            if failure_count >= self.failure_threshold:
                strategy = RecoveryStrategy.ISOLATE  # Isolate to prevent cascade
            else:
                strategy = RecoveryStrategy.RESTART  # Simple restart
            
            # Create and queue recovery action
            action = RecoveryAction(
                component_id=component_id,
                component_name=component_name,
                strategy=strategy,
                priority=max(1, 10 - (failure_count // 2))
            )
            
            await self.recovery_executor.queue_recovery_action(action)
            
            # Check for cascades
            await self.cascade_detector.detect_cascading_failure(component_id)
            
            return True
        except Exception:
            return False

    def record_failure(self, component_id: str) -> bool:
        """Compatibility wrapper for recording failures"""
        try:
            # Track failures synchronously for benchmark compatibility
            now = datetime.now(UTC)
            failures = self.cascade_detector.component_failures.setdefault(component_id, [])
            failures.append(now)
            return True
        except Exception:
            return False

    def is_component_failed(self, component_id: str) -> bool:
        """Compatibility wrapper to check component failure status"""
        try:
            failures = self.cascade_detector.component_failures.get(component_id, [])
            cutoff = datetime.now(UTC) - self.cascade_detector.failure_window
            recent = [f for f in failures if f > cutoff]
            return len(recent) > 0
        except Exception:
            return False

    async def attempt_recovery(self, component_id: str) -> bool:
        """Compatibility wrapper to attempt recovery"""
        try:
            action = RecoveryAction(
                component_id=component_id,
                strategy=RecoveryStrategy.RESTART,
                priority=5
            )
            return await self.recovery_executor.queue_recovery_action(action)
        except Exception:
            return False
    
    # ========================================================================
    # CASCADE DETECTION AND HANDLING
    # ========================================================================
    
    async def detect_cascading_failure(self, initial_component: str) -> Optional[CascadeEvent]:
        """Detect if a component failure is cascading to others"""
        cascade = await self.cascade_detector.detect_cascading_failure(initial_component)
        
        if cascade:
            # Queue recovery actions for cascade
            actions = await self.cascade_detector.get_cascade_recovery_actions(cascade)
            for action in actions:
                await self.recovery_executor.queue_recovery_action(action)
        
        return cascade
    
    async def handle_cascade(self, cascade: CascadeEvent) -> bool:
        """Handle a detected cascading failure"""
        try:
            actions = await self.cascade_detector.get_cascade_recovery_actions(cascade)
            for action in actions:
                await self.recovery_executor.queue_recovery_action(action)
            return True
        except Exception:
            return False
    
    # ========================================================================
    # HANDLER MANAGEMENT
    # ========================================================================
    
    async def register_recovery_handler(self, handler: RecoveryHandler) -> bool:
        """Register a custom recovery handler"""
        try:
            self.recovery_executor.custom_handlers[str(id(handler))] = handler
            return True
        except Exception:
            return False
    
    async def unregister_recovery_handler(self, handler_id: str) -> bool:
        """Unregister a recovery handler"""
        try:
            if handler_id in self.recovery_executor.custom_handlers:
                del self.recovery_executor.custom_handlers[handler_id]
            return True
        except Exception:
            return False
    
    # ========================================================================
    # EVENT LISTENERS
    # ========================================================================
    
    async def add_listener(self, listener: FailoverEventListener) -> bool:
        """Add failover event listener"""
        try:
            if listener not in self.listeners:
                self.listeners.append(listener)
                # Update both components
                if listener not in self.recovery_executor.listeners:
                    self.recovery_executor.listeners.append(listener)
                if listener not in self.cascade_detector.listeners:
                    self.cascade_detector.listeners.append(listener)
            return True
        except Exception:
            return False
    
    async def remove_listener(self, listener: FailoverEventListener) -> bool:
        """Remove failover event listener"""
        try:
            if listener in self.listeners:
                self.listeners.remove(listener)
                if listener in self.recovery_executor.listeners:
                    self.recovery_executor.listeners.remove(listener)
                if listener in self.cascade_detector.listeners:
                    self.cascade_detector.listeners.remove(listener)
            return True
        except Exception:
            return False
    
    # ========================================================================
    # METRICS AND STATUS
    # ========================================================================
    
    async def get_recovery_metrics(self) -> RecoveryMetrics:
        """Get current recovery metrics"""
        return await self.recovery_executor.get_recovery_metrics()
    
    async def get_operation_status(self, operation_id: str) -> Optional[RecoveryOperation]:
        """Get status of a recovery operation"""
        return await self.recovery_executor.get_operation_status(operation_id)
    
    async def get_active_operations(self) -> Dict[str, RecoveryOperation]:
        """Get all active recovery operations"""
        return await self.recovery_executor.get_active_operations()
    
    async def get_pending_actions(self) -> List[RecoveryAction]:
        """Get all pending recovery actions"""
        return await self.recovery_executor.get_pending_actions()
    
    async def get_active_cascades(self) -> Dict[str, CascadeEvent]:
        """Get all active cascade events"""
        return await self.cascade_detector.get_active_cascades()
    
    async def clear_operation_history(self, older_than_hours: int = 24) -> int:
        """Clear old operation history"""
        return await self.recovery_executor.clear_operation_history(older_than_hours)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    async def is_enabled(self) -> bool:
        """Check if failover manager is enabled"""
        return self.enabled
    
    async def get_failure_count(self, component_id: str) -> int:
        """Get recent failure count for component"""
        return await self.cascade_detector.get_failure_count(component_id)
    
    async def reset_failure_count(self, component_id: str) -> bool:
        """Reset failure count for component"""
        try:
            if component_id in self.cascade_detector.component_failures:
                self.cascade_detector.component_failures[component_id] = []
            return True
        except Exception:
            return False
    
    # ========================================================================
    # QUEUE RECOVERY ACTION (public API)
    # ========================================================================
    
    async def queue_recovery_action(self, action: RecoveryAction) -> bool:
        """Queue a recovery action for execution"""
        return await self.recovery_executor.queue_recovery_action(action)
