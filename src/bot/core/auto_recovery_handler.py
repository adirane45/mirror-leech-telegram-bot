"""
Auto-Recovery Handler - Automatic recovery for unhealthy components
Monitors health checks and triggers recovery callbacks
- Auto-restart services
- Notify admins
- Attempt recovery before escalation

Enhanced by: justadi
Date: February 8, 2026
"""

from typing import Dict, List, Callable, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import asyncio

from .. import LOGGER


class RecoverySeverity(Enum):
    """Recovery action severity"""
    AUTO_RESTART = "auto_restart"      # Try to restart service
    NOTIFY_ADMIN = "notify_admin"      # Alert admin, requires manual action
    ERROR_LOG = "error_log"            # Just log, no action
    GRACEFUL_RESTART = "graceful_restart"  # Restart with cleanup


class RecoveryAction:
    """Defines a recovery action"""
    
    def __init__(
        self,
        component_id: str,
        component_name: str,
        severity: RecoverySeverity,
        retry_count: int,
        action_fn: Callable,
        max_attempts: int = 3,
    ):
        self.component_id = component_id
        self.component_name = component_name
        self.severity = severity
        self.retry_count = retry_count
        self.action_fn = action_fn
        self.max_attempts = max_attempts
        self.last_attempt: Optional[datetime] = None
        self.success_count = 0
        self.failure_count = 0


class AutoRecoveryHandler:
    """Singleton auto-recovery handler"""
    
    _instance: Optional['AutoRecoveryHandler'] = None
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
        self._recovery_actions: Dict[str, RecoveryAction] = {}
        self._recovery_history: Dict[str, List[Dict]] = {}
        self._notify_callbacks: List[Callable] = []
        self._recovery_task: Optional[asyncio.Task] = None
        LOGGER.info("✅ Auto-Recovery Handler initialized")
    
    @classmethod
    def get_instance(cls) -> 'AutoRecoveryHandler':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # ==================== SETUP ====================
    
    async def enable(self, notify_callback: Optional[Callable] = None) -> bool:
        """
        Enable auto-recovery
        
        Args:
            notify_callback: Async function(component_id, severity, message) for admin notifications
        """
        async with self._lock:
            self._enabled = True
            if notify_callback:
                self._notify_callbacks.append(notify_callback)
            LOGGER.info("✅ Auto-recovery enabled")
            return True

    async def disable(self) -> bool:
        """Disable auto-recovery"""
        async with self._lock:
            self._enabled = False
            LOGGER.info("❌ Auto-recovery disabled")
            return True
    
    def register_recovery_action(
        self,
        component_id: str,
        component_name: str,
        severity: RecoverySeverity,
        action_fn: Callable,
        max_attempts: int = 3,
    ) -> bool:
        """
        Register recovery action for component
        
        Args:
            component_id: Unique component ID
            component_name: Human-readable name
            severity: Recovery severity level
            action_fn: Async function to execute recovery
            max_attempts: Max recovery attempts before escalating
        """
        action = RecoveryAction(
            component_id=component_id,
            component_name=component_name,
            severity=severity,
            retry_count=0,
            action_fn=action_fn,
            max_attempts=max_attempts,
        )
        self._recovery_actions[component_id] = action
        self._recovery_history[component_id] = []
        LOGGER.info(f"📋 Registered recovery action for {component_name} ({severity.value})")
        return True
    
    # ==================== RECOVERY EXECUTION ====================
    
    async def attempt_recovery(
        self,
        component_id: str,
        error_message: str = "",
        manual_trigger: bool = False,
    ) -> bool:
        """
        Attempt recovery for unhealthy component
        
        Args:
            component_id: Component to recover
            error_message: Description of the problem
            manual_trigger: Whether triggered manually or by health check
            
        Returns:
            Success status
        """
        if not self._enabled:
            LOGGER.warning(f"⚠️  Auto-recovery disabled, skipping recovery for {component_id}")
            return False
        
        async with self._lock:
            action = self._recovery_actions.get(component_id)
            
            if not action:
                LOGGER.error(f"❌ No recovery action registered for {component_id}")
                return False
            
            # Check if max attempts exceeded
            if action.retry_count >= action.max_attempts:
                LOGGER.error(
                    f"❌ Max recovery attempts ({action.max_attempts}) exceeded for "
                    f"{action.component_name}. Escalating to admin."
                )
                await self._escalate_to_admin(
                    component_id,
                    action.component_name,
                    f"Max recovery attempts exceeded. Error: {error_message}"
                )
                return False
            
            action.retry_count += 1
            action.last_attempt = datetime.now()
            
            LOGGER.warning(
                f"🔄 Attempting recovery for {action.component_name} "
                f"(attempt {action.retry_count}/{action.max_attempts}): {error_message}"
            )
            
            try:
                # Execute recovery action
                if asyncio.iscoroutinefunction(action.action_fn):
                    result = await action.action_fn()
                else:
                    result = action.action_fn()
                
                if result or result is None:  # None = success, True = success
                    action.success_count += 1
                    action.retry_count = 0  # Reset counter on success
                    
                    LOGGER.info(
                        f"✅ Recovery SUCCESS for {action.component_name}. "
                        f"Total successes: {action.success_count}"
                    )
                    
                    await self._record_recovery(
                        component_id,
                        action.component_name,
                        True,
                        error_message
                    )
                    return True
                else:
                    action.failure_count += 1
                    LOGGER.error(
                        f"❌ Recovery FAILED for {action.component_name}. "
                        f"Total failures: {action.failure_count}"
                    )
                    
                    # Escalate if too many failures
                    if action.failure_count >= 2:
                        await self._escalate_to_admin(
                            component_id,
                            action.component_name,
                            f"Recovery attempts failing: {error_message}",
                        )
                    
                    await self._record_recovery(
                        component_id,
                        action.component_name,
                        False,
                        error_message
                    )
                    return False
                    
            except Exception as e:
                action.failure_count += 1
                LOGGER.error(
                    f"❌ Recovery EXCEPTION for {action.component_name}: {e}",
                    exc_info=True
                )
                
                await self._escalate_to_admin(
                    component_id,
                    action.component_name,
                    f"Recovery exception: {str(e)}. Original error: {error_message}",
                )
                
                await self._record_recovery(
                    component_id,
                    action.component_name,
                    False,
                    f"Exception: {str(e)}"
                )
                return False
    
    # ==================== ESCALATION ====================
    
    async def _escalate_to_admin(
        self,
        component_id: str,
        component_name: str,
        message: str
    ):
        """Escalate issue to admin"""
        LOGGER.critical(
            f"🚨 ESCALATING to admin: {component_name} - {message}"
        )
        
        # Call all registered notify callbacks
        for callback in self._notify_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(component_id, RecoverySeverity.NOTIFY_ADMIN, message)
                else:
                    callback(component_id, RecoverySeverity.NOTIFY_ADMIN, message)
            except Exception as e:
                LOGGER.error(f"Error in notification callback: {e}")
    
    # ==================== HISTORY & REPORTING ====================
    
    async def _record_recovery(
        self,
        component_id: str,
        component_name: str,
        success: bool,
        error: str
    ):
        """Record recovery attempt in history"""
        history = self._recovery_history.get(component_id, [])
        history.append({
            "timestamp": datetime.now().isoformat(),
            "component": component_name,
            "success": success,
            "error": error,
        })
        
        # Keep last 50 entries per component
        if len(history) > 50:
            history = history[-50:]
        
        self._recovery_history[component_id] = history
    
    def get_recovery_history(self, component_id: str) -> List[Dict]:
        """Get recovery history for component"""
        return self._recovery_history.get(component_id, [])
    
    def get_status(self) -> Dict[str, Any]:
        """Get auto-recovery status"""
        status = {
            "enabled": self._enabled,
            "actions_registered": len(self._recovery_actions),
            "components": {}
        }
        
        for comp_id, action in self._recovery_actions.items():
            status["components"][comp_id] = {
                "name": action.component_name,
                "severity": action.severity.value,
                "retries": action.retry_count,
                "max_retries": action.max_attempts,
                "successes": action.success_count,
                "failures": action.failure_count,
                "last_attempt": action.last_attempt.isoformat() if action.last_attempt else None,
                "healthy": action.retry_count == 0 and action.failure_count == 0,
            }
        
        return status
    
    # ==================== UTILITY ====================
    
    async def reset_component(self, component_id: str) -> bool:
        """Reset recovery counters for component"""
        action = self._recovery_actions.get(component_id)
        if action:
            action.retry_count = 0
            action.failure_count = 0
            action.last_attempt = None
            action.success_count = 0
            LOGGER.info(f"🔄 Reset recovery counters for {action.component_name}")
            return True
        return False


# Global instance
auto_recovery = AutoRecoveryHandler.get_instance()
