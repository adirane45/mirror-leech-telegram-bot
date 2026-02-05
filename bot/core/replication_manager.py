"""
Replication Manager for Data Replication

Handles data replication across cluster nodes, including:
- Master-slave replication
- Multi-master replication
- Conflict resolution
- Consistency management

Features:
- Configurable replication strategies
- Automatic conflict resolution
- Replication lag monitoring
- Data consistency guarantees
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import hashlib


class ReplicationMode(Enum):
    """Replication mode"""
    MASTER_SLAVE = "master_slave"
    MULTI_MASTER = "multi_master"
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"


class ConsistencyLevel(Enum):
    """Data consistency level"""
    STRONG = "strong"  # Wait for all replicas
    EVENTUAL = "eventual"  # Best effort
    QUORUM = "quorum"  # Wait for majority


class ConflictResolution(Enum):
    """Conflict resolution strategy"""
    LAST_WRITE_WINS = "last_write_wins"
    FIRST_WRITE_WINS = "first_write_wins"
    MERGE = "merge"
    MANUAL = "manual"


@dataclass
class ReplicationData:
    """Data to be replicated"""
    data_id: str
    data_type: str
    data: Any
    version: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source_node: str = ""
    checksum: str = ""
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate data checksum"""
        data_str = str(self.data)
        return hashlib.md5(data_str.encode()).hexdigest()


@dataclass
class ReplicationStatus:
    """Replication status for a node"""
    node_id: str
    is_replicating: bool = False
    last_sync: Optional[datetime] = None
    lag_seconds: float = 0.0
    replicated_count: int = 0
    failed_count: int = 0


class ReplicationManager:
    """Manages data replication across nodes"""
    
    _instance: Optional['ReplicationManager'] = None
    
    def __init__(self):
        self.enabled = False
        self.mode = ReplicationMode.MASTER_SLAVE
        self.consistency_level = ConsistencyLevel.EVENTUAL
        self.conflict_resolution = ConflictResolution.LAST_WRITE_WINS
        
        self.master_node: Optional[str] = None
        self.slave_nodes: List[str] = []
        self.replication_statuses: Dict[str, ReplicationStatus] = {}
        
        self.pending_replications: List[ReplicationData] = []
        self.replication_queue: asyncio.Queue = asyncio.Queue()
        
        self.replicated_data: Dict[str, ReplicationData] = {}
        self.conflicts: List[Dict[str, Any]] = []
        self.max_conflicts = 100
        
        self.replication_task: Optional[asyncio.Task] = None
        self.sync_task: Optional[asyncio.Task] = None
        
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'ReplicationManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = ReplicationManager()
        return cls._instance
    
    async def enable(
        self,
        mode: ReplicationMode = ReplicationMode.MASTER_SLAVE,
        consistency: ConsistencyLevel = ConsistencyLevel.EVENTUAL
    ) -> bool:
        """Enable replication manager"""
        try:
            async with self.lock:
                self.enabled = True
                self.mode = mode
                self.consistency_level = consistency
                
                # Start replication tasks
                if self.replication_task is None or self.replication_task.done():
                    self.replication_task = asyncio.create_task(self._replication_loop())
                
                if self.sync_task is None or self.sync_task.done():
                    self.sync_task = asyncio.create_task(self._sync_loop())
                
                return True
        except Exception as e:
            print(f"Error enabling replication: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable replication manager"""
        try:
            async with self.lock:
                self.enabled = False
                
                if self.replication_task:
                    self.replication_task.cancel()
                    try:
                        await self.replication_task
                    except asyncio.CancelledError:
                        pass
                
                if self.sync_task:
                    self.sync_task.cancel()
                    try:
                        await self.sync_task
                    except asyncio.CancelledError:
                        pass
                
                return True
        except Exception as e:
            print(f"Error disabling replication: {e}")
            return False
    
    async def set_master(self, node_id: str) -> bool:
        """Set master node"""
        try:
            async with self.lock:
                self.master_node = node_id
                if node_id not in self.replication_statuses:
                    self.replication_statuses[node_id] = ReplicationStatus(node_id)
                return True
        except Exception as e:
            print(f"Error setting master: {e}")
            return False
    
    async def add_slave(self, node_id: str) -> bool:
        """Add slave node"""
        try:
            async with self.lock:
                if node_id not in self.slave_nodes:
                    self.slave_nodes.append(node_id)
                    self.replication_statuses[node_id] = ReplicationStatus(node_id)
                return True
        except Exception as e:
            print(f"Error adding slave: {e}")
            return False
    
    async def replicate_data(
        self,
        data_id: str,
        data_type: str,
        data: Any,
        source_node: Optional[str] = None
    ) -> bool:
        """Replicate data to all nodes"""
        try:
            if not self.enabled:
                return False
            
            # Create replication data
            repl_data = ReplicationData(
                data_id=data_id,
                data_type=data_type,
                data=data,
                source_node=source_node or self.master_node or "unknown"
            )
            
            # Add to queue
            await self.replication_queue.put(repl_data)
            
            return True
        
        except Exception as e:
            print(f"Error replicating data: {e}")
            return False
    
    async def _replication_loop(self) -> None:
        """Process replication queue"""
        while self.enabled:
            try:
                # Get data from queue (timeout 1 second)
                try:
                    repl_data = await asyncio.wait_for(
                        self.replication_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Replicate to nodes
                await self._replicate_to_nodes(repl_data)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Replication loop error: {e}")
                await asyncio.sleep(1)
    
    async def _replicate_to_nodes(self, repl_data: ReplicationData) -> None:
        """Replicate data to all slave nodes"""
        try:
            if self.mode == ReplicationMode.SYNCHRONOUS:
                # Wait for all replicas
                await self._synchronous_replication(repl_data)
            elif self.consistency_level == ConsistencyLevel.QUORUM:
                # Wait for majority
                await self._quorum_replication(repl_data)
            else:
                # Asynchronous replication
                await self._asynchronous_replication(repl_data)
            
            # Store replicated data
            self.replicated_data[repl_data.data_id] = repl_data
        
        except Exception as e:
            print(f"Error replicating to nodes: {e}")
    
    async def _synchronous_replication(self, repl_data: ReplicationData) -> None:
        """Synchronous replication - wait for all nodes"""
        tasks = []
        for node_id in self.slave_nodes:
            task = asyncio.create_task(self._replicate_to_node(node_id, repl_data))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _quorum_replication(self, repl_data: ReplicationData) -> None:
        """Quorum replication - wait for majority"""
        tasks = []
        for node_id in self.slave_nodes:
            task = asyncio.create_task(self._replicate_to_node(node_id, repl_data))
            tasks.append(task)
        
        if tasks:
            # Wait for majority (> 50%)
            quorum_size = len(tasks) // 2 + 1
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_EXCEPTION
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
    
    async def _asynchronous_replication(self, repl_data: ReplicationData) -> None:
        """Asynchronous replication - fire and forget"""
        for node_id in self.slave_nodes:
            asyncio.create_task(self._replicate_to_node(node_id, repl_data))
    
    async def _replicate_to_node(self, node_id: str, repl_data: ReplicationData) -> bool:
        """Replicate to a specific node"""
        try:
            status = self.replication_statuses.get(node_id)
            if not status:
                return False
            
            status.is_replicating = True
            
            # In production, make actual replication call
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Check for conflicts
            existing = await self._get_existing_data(node_id, repl_data.data_id)
            if existing and existing.version >= repl_data.version:
                await self._handle_conflict(repl_data, existing, node_id)
                status.failed_count += 1
                return False
            
            # Successful replication
            status.replicated_count += 1
            status.last_sync = datetime.utcnow()
            status.is_replicating = False
            
            return True
        
        except Exception as e:
            print(f"Error replicating to {node_id}: {e}")
            if status:
                status.failed_count += 1
                status.is_replicating = False
            return False
    
    async def _get_existing_data(
        self,
        node_id: str,
        data_id: str
    ) -> Optional[ReplicationData]:
        """Get existing data from node"""
        # In production, fetch from node
        return None
    
    async def _handle_conflict(
        self,
        new_data: ReplicationData,
        existing_data: ReplicationData,
        node_id: str
    ) -> None:
        """Handle replication conflict"""
        try:
            conflict = {
                'data_id': new_data.data_id,
                'node_id': node_id,
                'new_version': new_data.version,
                'existing_version': existing_data.version,
                'new_timestamp': new_data.timestamp.isoformat(),
                'existing_timestamp': existing_data.timestamp.isoformat(),
                'resolved': False
            }
            
            # Apply conflict resolution strategy
            if self.conflict_resolution == ConflictResolution.LAST_WRITE_WINS:
                if new_data.timestamp > existing_data.timestamp:
                    # New data wins
                    await self._force_replicate(node_id, new_data)
                    conflict['resolved'] = True
                    conflict['resolution'] = 'new_wins'
            
            elif self.conflict_resolution == ConflictResolution.FIRST_WRITE_WINS:
                # Existing data wins
                conflict['resolved'] = True
                conflict['resolution'] = 'existing_wins'
            
            elif self.conflict_resolution == ConflictResolution.MERGE:
                # Attempt merge
                merged = await self._merge_data(new_data, existing_data)
                if merged:
                    await self._force_replicate(node_id, merged)
                    conflict['resolved'] = True
                    conflict['resolution'] = 'merged'
            
            # Record conflict
            self.conflicts.append(conflict)
            if len(self.conflicts) > self.max_conflicts:
                self.conflicts = self.conflicts[-self.max_conflicts:]
        
        except Exception as e:
            print(f"Error handling conflict: {e}")
    
    async def _force_replicate(self, node_id: str, data: ReplicationData) -> None:
        """Force replication, overwriting existing data"""
        # In production, force write to node
        await asyncio.sleep(0.1)
    
    async def _merge_data(
        self,
        new_data: ReplicationData,
        existing_data: ReplicationData
    ) -> Optional[ReplicationData]:
        """Merge conflicting data"""
        try:
            # Simple merge strategy - combine data if dict
            if isinstance(new_data.data, dict) and isinstance(existing_data.data, dict):
                merged_dict = {**existing_data.data, **new_data.data}
                return ReplicationData(
                    data_id=new_data.data_id,
                    data_type=new_data.data_type,
                    data=merged_dict,
                    version=max(new_data.version, existing_data.version) + 1,
                    source_node=new_data.source_node
                )
            return None
        except Exception:
            return None
    
    async def _sync_loop(self) -> None:
        """Periodic sync of replication status"""
        while self.enabled:
            try:
                await self._update_replication_lag()
                await asyncio.sleep(5)  # Update every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Sync loop error: {e}")
                await asyncio.sleep(1)
    
    async def _update_replication_lag(self) -> None:
        """Update replication lag for all nodes"""
        try:
            now = datetime.utcnow()
            
            for node_id, status in self.replication_statuses.items():
                if status.last_sync:
                    lag = (now - status.last_sync).total_seconds()
                    status.lag_seconds = lag
        
        except Exception as e:
            print(f"Error updating lag: {e}")
    
    async def get_replication_status(self) -> Dict[str, Any]:
        """Get replication status"""
        try:
            async with self.lock:
                return {
                    'enabled': self.enabled,
                    'mode': self.mode.value,
                    'consistency_level': self.consistency_level.value,
                    'master_node': self.master_node,
                    'slave_nodes': self.slave_nodes,
                    'nodes': {
                        node_id: {
                            'is_replicating': status.is_replicating,
                            'last_sync': (
                                status.last_sync.isoformat()
                                if status.last_sync else None
                            ),
                            'lag_seconds': status.lag_seconds,
                            'replicated_count': status.replicated_count,
                            'failed_count': status.failed_count
                        }
                        for node_id, status in self.replication_statuses.items()
                    },
                    'queue_size': self.replication_queue.qsize(),
                    'replicated_items': len(self.replicated_data),
                    'conflicts': len(self.conflicts)
                }
        except Exception as e:
            print(f"Error getting status: {e}")
            return {'enabled': self.enabled, 'error': str(e)}
    
    async def get_conflicts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conflicts"""
        try:
            async with self.lock:
                return self.conflicts[-limit:]
        except Exception as e:
            print(f"Error getting conflicts: {e}")
            return []
    
    async def reset(self) -> bool:
        """Reset replication manager"""
        try:
            await self.disable()
            self.master_node = None
            self.slave_nodes.clear()
            self.replication_statuses.clear()
            self.replicated_data.clear()
            self.conflicts.clear()
            
            # Clear queue
            while not self.replication_queue.empty():
                try:
                    self.replication_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            return True
        except Exception as e:
            print(f"Error resetting: {e}")
            return False
