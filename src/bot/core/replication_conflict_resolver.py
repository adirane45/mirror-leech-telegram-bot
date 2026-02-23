"""
Replication Conflict Resolver - Handles conflict detection and resolution

Responsibilities:
- Detecting conflicts between local and remote changes
- Applying appropriate conflict resolution strategies
- Tracking conflict history and metrics
"""

import asyncio
from typing import Dict, List, Optional, Callable, Any

from .replication_models import (
    ConflictResolutionStrategy,
    ConflictEvent,
    ReplicationLog,
    ReplicationMetrics,
    ReplicationEventListener,
)


class ReplicationConflictResolver:
    """Detects and resolves conflicts in replicated changes"""
    
    def __init__(self, 
                 replication_log: List[ReplicationLog],
                 local_state: Dict[str, Any],
                 metrics: ReplicationMetrics,
                 listeners: Optional[List[ReplicationEventListener]] = None):
        """Initialize conflict resolver"""
        self.replication_log = replication_log
        self.local_state = local_state
        self.conflicts: Dict[str, ConflictEvent] = {}
        self.metrics = metrics
        self.listeners = listeners or []
        self.conflict_resolver: Optional[Callable] = None
        self.resolution_strategy = ConflictResolutionStrategy.VECTOR_CLOCK
    
    async def detect_conflict(
        self,
        remote_log: ReplicationLog,
        from_node: str
    ) -> Optional[ConflictEvent]:
        """
        Detect if there's a conflict with a remote change
        
        Returns ConflictEvent if conflict detected, None otherwise
        """
        key = remote_log.key
        
        # Check if key was modified locally after remote change
        for local_log in self.replication_log:
            if (local_log.key == key and
                local_log.operation_type != "DELETE" and
                remote_log.operation_type != "DELETE"):
                
                # Check if vector clocks are concurrent
                if remote_log.vector_clock.concurrent_with(local_log.vector_clock):
                    # Conflict detected
                    local_value = self.local_state.get(key)
                    
                    conflict = ConflictEvent(
                        key=key,
                        local_value=local_value,
                        remote_value=remote_log.value,
                        local_timestamp=local_log.timestamp,
                        remote_timestamp=remote_log.timestamp,
                        remote_node=from_node,
                        resolution_strategy=self.resolution_strategy
                    )
                    
                    self.conflicts[conflict.event_id] = conflict
                    self.metrics.conflicts_detected += 1
                    
                    for listener in self.listeners:
                        await listener.on_conflict_detected(conflict)
                    
                    return conflict
        
        return None
    
    async def resolve_conflict(self, conflict: ConflictEvent) -> bool:
        """Resolve a detected conflict using configured strategy"""
        try:
            strategy = conflict.resolution_strategy
            
            if strategy == ConflictResolutionStrategy.TIMESTAMP:
                # Last write wins based on timestamp
                if conflict.remote_timestamp > conflict.local_timestamp:
                    conflict.resolved_value = conflict.remote_value
                else:
                    conflict.resolved_value = conflict.local_value
            
            elif strategy == ConflictResolutionStrategy.CLIENT_WINS:
                conflict.resolved_value = conflict.local_value
            
            elif strategy == ConflictResolutionStrategy.SERVER_WINS:
                conflict.resolved_value = conflict.remote_value
            
            elif strategy == ConflictResolutionStrategy.MERGE:
                # Use custom merge function if provided
                if self.conflict_resolver:
                    conflict.resolved_value = await self.conflict_resolver(
                        conflict.local_value,
                        conflict.remote_value
                    )
                else:
                    conflict.resolved_value = conflict.remote_value
            
            elif strategy == ConflictResolutionStrategy.VECTOR_CLOCK:
                conflict.resolved_value = conflict.remote_value
            
            else:
                return False
            
            conflict.resolved = True
            return True
        except Exception:
            return False
    
    async def get_conflict_history(self, limit: int = 100) -> List[ConflictEvent]:
        """Get recent conflicts"""
        return list(self.conflicts.values())[-limit:]
    
    def set_custom_resolver(self, resolver: Callable) -> None:
        """Set custom conflict resolver function"""
        self.conflict_resolver = resolver
    
    def set_resolution_strategy(self, strategy: ConflictResolutionStrategy) -> None:
        """Set the conflict resolution strategy"""
        self.resolution_strategy = strategy
