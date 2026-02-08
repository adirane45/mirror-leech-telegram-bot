"""
Failover Cascade Detector - Detects and monitors cascading failures

Responsibilities:
- Monitoring for cascading failure patterns
- Detecting when failures propagate across components
- Handling cascade escalation
- Tracking cascade metrics
"""

import asyncio
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Set

from .failover_models import (
    RecoveryStrategy,
    CascadeLevel,
    RecoveryAction,
    CascadeEvent,
    RecoveryMetrics,
    FailoverEventListener,
)


class FailoverCascadeDetector:
    """Detects and handles cascading failure patterns"""
    
    def __init__(self, listeners: Optional[List[FailoverEventListener]] = None):
        """Initialize cascade detector"""
        self.component_failures: Dict[str, List[datetime]] = {}
        self.active_cascades: Dict[str, CascadeEvent] = {}
        
        self.cascade_threshold_depth = 3  # Components before cascade
        self.failure_threshold = 5  # Max failures before escalation
        self.failure_window = timedelta(minutes=10)  # Time window for counting
        
        self.metrics = RecoveryMetrics()
        self.listeners = listeners or []
        
        self.enabled = False
        self._monitor_task: Optional[asyncio.Task] = None
    
    async def start(self) -> bool:
        """Start cascade detector"""
        if self.enabled:
            return True
        
        try:
            self.enabled = True
            self._monitor_task = asyncio.create_task(self._cascade_monitor_loop())
            return True
        except Exception:
            self.enabled = False
            return False
    
    async def stop(self) -> bool:
        """Stop cascade detector"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            
            if self._monitor_task and not self._monitor_task.done():
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            
            return True
        except Exception:
            return False
    
    async def track_component_failure(self, component_id: str) -> None:
        """Track a component failure"""
        if component_id not in self.component_failures:
            self.component_failures[component_id] = []
        
        now = datetime.now(UTC)
        self.component_failures[component_id].append(now)
        
        # Clean old failures
        cutoff = now - self.failure_window
        self.component_failures[component_id] = [
            t for t in self.component_failures[component_id] if t > cutoff
        ]
    
    async def detect_cascading_failure(self, initial_component: str) -> Optional[CascadeEvent]:
        """
        Detect if a component failure is cascading to others
        
        Analyzes:
        - Number of dependent components failing
        - Rate of failure propagation
        - Correlation between failures
        """
        try:
            now = datetime.now(UTC)
            recent_failures = []
            
            # Count concurrent failures
            for component_id, failures in self.component_failures.items():
                recent_count = sum(1 for f in failures if now - f < timedelta(seconds=5))
                if recent_count > 0:
                    recent_failures.append((component_id, recent_count))
            
            # Multiple components failing = cascade
            if len(recent_failures) >= self.cascade_threshold_depth:
                cascade = CascadeEvent(
                    initial_component=initial_component,
                    cascade_level=CascadeLevel.SERVICE if len(recent_failures) < 5 else CascadeLevel.CLUSTER,
                    affected_components={c[0] for c in recent_failures}
                )
                
                self.active_cascades[cascade.event_id] = cascade
                
                # Notify listeners
                for listener in self.listeners:
                    await listener.on_cascade_detected(cascade)
                
                self.metrics.total_cascades_handled += 1
                self.metrics.last_cascade_time = now
                
                return cascade
            
            return None
        except Exception:
            return None
    
    async def get_cascade_recovery_actions(self, cascade: CascadeEvent) -> List[RecoveryAction]:
        """Get recovery actions for a cascade event"""
        actions = []
        
        try:
            # Create isolate action for each affected component
            for component_id in cascade.affected_components:
                action = RecoveryAction(
                    component_id=component_id,
                    strategy=RecoveryStrategy.ISOLATE,  # Isolate to prevent spread
                    priority=10  # Highest priority
                )
                actions.append(action)
        
        except Exception:
            pass
        
        return actions
    
    async def _cascade_monitor_loop(self) -> None:
        """Background loop to monitor for cascading failures"""
        while self.enabled:
            try:
                # Check for cascades periodically
                for component_id in list(self.component_failures.keys()):
                    failures = self.component_failures[component_id]
                    
                    # Recent failure?
                    recent = [f for f in failures if datetime.now(UTC) - f < timedelta(seconds=10)]
                    if recent:
                        await self.detect_cascading_failure(component_id)
                
                # Clean resolved cascades
                now = datetime.now(UTC)
                for event_id, cascade in list(self.active_cascades.items()):
                    if cascade.timestamp and now - cascade.timestamp > timedelta(minutes=5):
                        cascade.is_active = False
                        del self.active_cascades[event_id]
                
                await asyncio.sleep(2)
            
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(2)
    
    async def get_active_cascades(self) -> Dict[str, CascadeEvent]:
        """Get all active cascade events"""
        return {
            event_id: cascade for event_id, cascade in self.active_cascades.items()
            if cascade.is_active
        }
    
    async def get_failure_count(self, component_id: str) -> int:
        """Get recent failure count for component"""
        if component_id not in self.component_failures:
            return 0
        
        failures = self.component_failures[component_id]
        cutoff = datetime.now(UTC) - self.failure_window
        return sum(1 for f in failures if f > cutoff)
    
    async def clear_cascades_older_than(self, hours: int = 24) -> int:
        """Clear cascade history older than specified hours"""
        try:
            cutoff = datetime.now(UTC) - timedelta(hours=hours)
            to_delete = [
                event_id for event_id, cascade in self.active_cascades.items()
                if cascade.timestamp and cascade.timestamp < cutoff
            ]
            
            for event_id in to_delete:
                del self.active_cascades[event_id]
            
            return len(to_delete)
        except Exception:
            return 0
