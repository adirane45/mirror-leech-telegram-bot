"""
Replication Sync Engine - Handles synchronization and change propagation

Responsibilities:
- Batching and sending replication changes
- Synchronization with peer nodes
- Incremental sync based on checkpoints
- Replication lag monitoring
- Log compaction and cleanup
"""

import asyncio
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any

from .replication_models import (
    ReplicationLog,
    SyncCheckpoint,
    ReplicationLag,
    ReplicationMetrics,
    ReplicationEventListener,
)


class ReplicationSyncEngine:
    """Manages synchronization and change replication"""
    
    def __init__(self, 
                 replication_log: List[ReplicationLog],
                 local_state: Dict[str, Any],
                 peer_nodes: Dict[str, Dict[str, Any]],
                 metrics: ReplicationMetrics,
                 listeners: Optional[List[ReplicationEventListener]] = None):
        """Initialize sync engine"""
        self.replication_log = replication_log
        self.local_state = local_state
        self.peer_nodes = peer_nodes
        self.pending_replication: Dict[str, List[ReplicationLog]] = {}
        self.sync_checkpoints: Dict[str, SyncCheckpoint] = {}
        self.metrics = metrics
        self.listeners = listeners or []
        
        self.batch_size = 100
        self.sync_interval = 5
        self.lag_check_interval = 2
        self.log_retention_hours = 24
        
        # Background tasks
        self._replication_task: Optional[asyncio.Task] = None
        self._lag_monitor_task: Optional[asyncio.Task] = None
        self._log_cleanup_task: Optional[asyncio.Task] = None
        
        self.enabled = False
    
    async def start(self) -> bool:
        """Start sync engine"""
        if self.enabled:
            return True
        
        try:
            self.enabled = True
            self._replication_task = asyncio.create_task(self._replication_loop())
            self._lag_monitor_task = asyncio.create_task(self._lag_monitor_loop())
            self._log_cleanup_task = asyncio.create_task(self._log_cleanup_loop())
            return True
        except Exception:
            self.enabled = False
            return False
    
    async def stop(self) -> bool:
        """Stop sync engine"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            
            for task in [self._replication_task, self._lag_monitor_task, self._log_cleanup_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            return True
        except Exception:
            return False
    
    async def queue_change_for_replication(self, log_entry: ReplicationLog) -> None:
        """Queue a change to be replicated to all peers"""
        self.metrics.total_changes += 1
        self.metrics.pending_changes += 1
        
        for node_id in self.peer_nodes:
            if node_id not in self.pending_replication:
                self.pending_replication[node_id] = []
            self.pending_replication[node_id].append(log_entry)
    
    async def sync_with_node(self, node_id: str) -> bool:
        """
        Perform full synchronization with a specific node
        
        Sends all pending changes in batches
        """
        if not self.enabled:
            return False
        
        try:
            if node_id not in self.pending_replication:
                self.pending_replication[node_id] = []
            
            pending = self.pending_replication[node_id]
            
            # Send in batches
            for i in range(0, len(pending), self.batch_size):
                batch = pending[i:i + self.batch_size]
                # In real implementation, send over network
                await asyncio.sleep(0.01)  # Simulate network latency
            
            # Update checkpoint
            checkpoint = SyncCheckpoint(
                node_id=node_id,
                last_synced_sequence=len(self.replication_log),
                synced_keys=len(self.local_state)
            )
            self.sync_checkpoints[node_id] = checkpoint
            
            # Clear pending
            self.pending_replication[node_id] = []
            
            for listener in self.listeners:
                await listener.on_sync_completed(node_id)
            
            return True
        except Exception:
            return False
    
    async def incremental_sync(self, node_id: str) -> bool:
        """
        Perform incremental sync - only send changes since last sync
        """
        if node_id not in self.sync_checkpoints:
            return await self.sync_with_node(node_id)
        
        checkpoint = self.sync_checkpoints[node_id]
        last_seq = checkpoint.last_synced_sequence
        
        # Get changes since last checkpoint
        new_changes = [
            log for log in self.replication_log
            if log.sequence_number > last_seq
        ]
        
        if not new_changes:
            return True
        
        # Send incremental changes in batches
        for i in range(0, len(new_changes), self.batch_size):
            batch = new_changes[i:i + self.batch_size]
            await asyncio.sleep(0.01)
        
        # Update checkpoint
        checkpoint.last_synced_sequence = len(self.replication_log)
        checkpoint.synced_keys = len(self.local_state)
        
        return True
    
    async def force_sync_all_nodes(self) -> bool:
        """Force synchronization with all peer nodes"""
        try:
            for node_id in self.peer_nodes:
                await self.sync_with_node(node_id)
            return True
        except Exception:
            return False
    
    async def _replication_loop(self) -> None:
        """Background loop for batching and sending replications"""
        while self.enabled:
            try:
                # Send pending changes to each peer in batches
                for node_id, pending_changes in self.pending_replication.items():
                    if pending_changes:
                        batch = pending_changes[:self.batch_size]
                        await asyncio.sleep(0.01)  # Simulate network send
                
                await asyncio.sleep(self.sync_interval)
            except Exception:
                await asyncio.sleep(self.sync_interval)
    
    async def _lag_monitor_loop(self) -> None:
        """Background loop for monitoring replication lag"""
        while self.enabled:
            try:
                # Calculate lag for each peer
                total_lag = 0
                in_sync_count = 0
                
                for node_id, pending in self.pending_replication.items():
                    lag = len(pending) * 10  # Estimate: 10ms per pending operation
                    total_lag += lag
                    
                    if lag == 0:
                        in_sync_count += 1
                    
                    # Check for critical lag
                    if lag > 30000:  # >30s
                        for listener in self.listeners:
                            await listener.on_lag_critical(node_id, lag)
                
                # Update metrics
                self.metrics.replication_lag_ms = total_lag // max(len(self.peer_nodes), 1)
                self.metrics.nodes_in_sync = in_sync_count
                self.metrics.total_nodes = len(self.peer_nodes)
                
                # Calculate average lag
                if self.peer_nodes:
                    self.metrics.avg_lag_ms = total_lag / len(self.peer_nodes)
                
                await asyncio.sleep(self.lag_check_interval)
            except Exception:
                await asyncio.sleep(self.lag_check_interval)
    
    async def _log_cleanup_loop(self) -> None:
        """Background loop for cleaning up old log entries"""
        while self.enabled:
            try:
                # Cleanup every hour
                await asyncio.sleep(3600)
                await self.clear_replication_log()
            except Exception:
                await asyncio.sleep(3600)
    
    async def clear_replication_log(self) -> int:
        """Clear old replication log entries"""
        cutoff = datetime.now(UTC) - timedelta(hours=self.log_retention_hours)
        initial_count = len(self.replication_log)
        
        # Remove old entries (in-place modification)
        to_keep = [
            log for log in self.replication_log
            if log.timestamp > cutoff
        ]
        
        removed_count = initial_count - len(to_keep)
        if removed_count > 0:
            self.replication_log[:] = to_keep
        
        return removed_count
    
    async def get_pending_changes_count(self, node_id: Optional[str] = None) -> int:
        """Get count of pending changes"""
        if node_id:
            return len(self.pending_replication.get(node_id, []))
        return sum(len(changes) for changes in self.pending_replication.values())
    
    def _classify_lag(self, lag_ms: int) -> str:
        """Classify lag level"""
        if lag_ms < 100:
            return ReplicationLag.MINIMAL.value
        elif lag_ms < 1000:
            return ReplicationLag.LOW.value
        elif lag_ms < 5000:
            return ReplicationLag.MEDIUM.value
        elif lag_ms < 30000:
            return ReplicationLag.HIGH.value
        else:
            return ReplicationLag.CRITICAL.value

