"""
Distributed State Manager for Cluster-Wide State

Manages distributed state across cluster nodes, including:
- Distributed locks
- Shared configuration
- Atomic operations
- State consistency

Features:
- Distributed locking with TTL
- Version vectors for consistency
- Atomic compare-and-swap
- State synchronization
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import uuid


class LockState(Enum):
    """Lock state"""
    UNLOCKED = "unlocked"
    LOCKED = "locked"
    EXPIRED = "expired"


@dataclass
class DistributedLock:
    """Distributed lock"""
    lock_id: str
    resource_key: str
    owner_node: str
    acquired_at: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: int = 30
    state: LockState = LockState.LOCKED
    
    @property
    def is_expired(self) -> bool:
        """Check if lock is expired"""
        elapsed = (datetime.utcnow() - self.acquired_at).total_seconds()
        return elapsed >= self.ttl_seconds
    
    @property
    def remaining_ttl(self) -> float:
        """Get remaining TTL in seconds"""
        elapsed = (datetime.utcnow() - self.acquired_at).total_seconds()
        return max(0, self.ttl_seconds - elapsed)


@dataclass
class StateEntry:
    """State entry with versioning"""
    key: str
    value: Any
    version: int = 1
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: str = ""


@dataclass
class VersionVector:
    """Version vector for consistency"""
    node_versions: Dict[str, int] = field(default_factory=dict)
    
    def increment(self, node_id: str) -> None:
        """Increment version for node"""
        self.node_versions[node_id] = self.node_versions.get(node_id, 0) + 1
    
    def merge(self, other: 'VersionVector') -> None:
        """Merge with another version vector"""
        for node_id, version in other.node_versions.items():
            self.node_versions[node_id] = max(
                self.node_versions.get(node_id, 0),
                version
            )
    
    def is_concurrent(self, other: 'VersionVector') -> bool:
        """Check if two version vectors are concurrent"""
        self_greater = False
        other_greater = False
        
        all_nodes = set(self.node_versions.keys()) | set(other.node_versions.keys())
        
        for node in all_nodes:
            self_v = self.node_versions.get(node, 0)
            other_v = other.node_versions.get(node, 0)
            
            if self_v > other_v:
                self_greater = True
            elif other_v > self_v:
                other_greater = True
        
        return self_greater and other_greater


class DistributedStateManager:
    """Manages distributed state across cluster"""
    
    _instance: Optional['DistributedStateManager'] = None
    
    def __init__(self):
        self.enabled = False
        self.node_id: Optional[str] = None
        
        # Distributed state
        self.state: Dict[str, StateEntry] = {}
        self.version_vectors: Dict[str, VersionVector] = {}
        
        # Distributed locks
        self.locks: Dict[str, DistributedLock] = {}
        self.lock_waiters: Dict[str, List[asyncio.Future]] = {}
        
        # Synchronization
        self.sync_interval = 5  # seconds
        self.sync_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'DistributedStateManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = DistributedStateManager()
        return cls._instance
    
    async def enable(self, node_id: Optional[str] = None) -> bool:
        """Enable distributed state manager"""
        try:
            async with self.lock:
                self.enabled = True
                self.node_id = node_id or str(uuid.uuid4())
                
                # Start background tasks
                if self.sync_task is None or self.sync_task.done():
                    self.sync_task = asyncio.create_task(self._sync_loop())
                
                if self.cleanup_task is None or self.cleanup_task.done():
                    self.cleanup_task = asyncio.create_task(self._cleanup_loop())
                
                return True
        except Exception as e:
            print(f"Error enabling distributed state: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable distributed state manager"""
        try:
            async with self.lock:
                self.enabled = False
                
                if self.sync_task:
                    self.sync_task.cancel()
                    try:
                        await self.sync_task
                    except asyncio.CancelledError:
                        pass
                
                if self.cleanup_task:
                    self.cleanup_task.cancel()
                    try:
                        await self.cleanup_task
                    except asyncio.CancelledError:
                        pass
                
                # Release all locks held by this node
                await self._release_all_locks()
                
                return True
        except Exception as e:
            print(f"Error disabling distributed state: {e}")
            return False
    
    # ===== State Operations =====
    
    async def set_state(self, key: str, value: Any) -> bool:
        """Set state value"""
        try:
            async with self.lock:
                if not self.enabled:
                    return False
                
                # Get existing entry
                existing = self.state.get(key)
                new_version = existing.version + 1 if existing else 1
                
                # Create new entry
                entry = StateEntry(
                    key=key,
                    value=value,
                    version=new_version,
                    updated_by=self.node_id or "unknown"
                )
                
                self.state[key] = entry
                
                # Update version vector
                if key not in self.version_vectors:
                    self.version_vectors[key] = VersionVector()
                self.version_vectors[key].increment(self.node_id or "unknown")
                
                return True
        except Exception as e:
            print(f"Error setting state: {e}")
            return False
    
    async def get_state(self, key: str) -> Optional[Any]:
        """Get state value"""
        try:
            async with self.lock:
                entry = self.state.get(key)
                return entry.value if entry else None
        except Exception as e:
            print(f"Error getting state: {e}")
            return None
    
    async def delete_state(self, key: str) -> bool:
        """Delete state value"""
        try:
            async with self.lock:
                if key in self.state:
                    del self.state[key]
                if key in self.version_vectors:
                    del self.version_vectors[key]
                return True
        except Exception as e:
            print(f"Error deleting state: {e}")
            return False
    
    async def compare_and_swap(
        self,
        key: str,
        expected: Any,
        new_value: Any
    ) -> bool:
        """Atomic compare-and-swap operation"""
        try:
            async with self.lock:
                if not self.enabled:
                    return False
                
                entry = self.state.get(key)
                
                # Check if current value matches expected
                current = entry.value if entry else None
                if current != expected:
                    return False
                
                # Set new value
                new_version = entry.version + 1 if entry else 1
                self.state[key] = StateEntry(
                    key=key,
                    value=new_value,
                    version=new_version,
                    updated_by=self.node_id or "unknown"
                )
                
                # Update version vector
                if key not in self.version_vectors:
                    self.version_vectors[key] = VersionVector()
                self.version_vectors[key].increment(self.node_id or "unknown")
                
                return True
        except Exception as e:
            print(f"Error in compare_and_swap: {e}")
            return False
    
    # ===== Distributed Locks =====
    
    async def acquire_lock(
        self,
        resource_key: str,
        ttl_seconds: int = 30,
        timeout_seconds: float = 10.0
    ) -> Optional[str]:
        """Acquire distributed lock"""
        try:
            if not self.enabled:
                return None
            
            start_time = time.time()
            
            while True:
                async with self.lock:
                    # Check if lock exists and is valid
                    existing_lock = self.locks.get(resource_key)
                    
                    if existing_lock and not existing_lock.is_expired:
                        # Lock is held by another node
                        pass
                    else:
                        # Acquire lock
                        lock_id = str(uuid.uuid4())
                        new_lock = DistributedLock(
                            lock_id=lock_id,
                            resource_key=resource_key,
                            owner_node=self.node_id or "unknown",
                            ttl_seconds=ttl_seconds
                        )
                        self.locks[resource_key] = new_lock
                        
                        # Notify waiters
                        if resource_key in self.lock_waiters:
                            for waiter in self.lock_waiters[resource_key]:
                                if not waiter.done():
                                    waiter.set_result(None)
                            del self.lock_waiters[resource_key]
                        
                        return lock_id
                
                # Check timeout
                if time.time() - start_time >= timeout_seconds:
                    return None
                
                # Wait for lock to be released
                future = asyncio.Future()
                if resource_key not in self.lock_waiters:
                    self.lock_waiters[resource_key] = []
                self.lock_waiters[resource_key].append(future)
                
                try:
                    await asyncio.wait_for(future, timeout=1.0)
                except asyncio.TimeoutError:
                    pass
        
        except Exception as e:
            print(f"Error acquiring lock: {e}")
            return None
    
    async def release_lock(self, resource_key: str, lock_id: str) -> bool:
        """Release distributed lock"""
        try:
            async with self.lock:
                existing_lock = self.locks.get(resource_key)
                
                if not existing_lock:
                    return False
                
                # Verify lock ownership
                if existing_lock.lock_id != lock_id:
                    return False
                
                # Release lock
                del self.locks[resource_key]
                
                # Notify waiters
                if resource_key in self.lock_waiters:
                    for waiter in self.lock_waiters[resource_key]:
                        if not waiter.done():
                            waiter.set_result(None)
                    del self.lock_waiters[resource_key]
                
                return True
        except Exception as e:
            print(f"Error releasing lock: {e}")
            return False
    
    async def extend_lock(self, resource_key: str, lock_id: str, ttl_seconds: int) -> bool:
        """Extend lock TTL"""
        try:
            async with self.lock:
                existing_lock = self.locks.get(resource_key)
                
                if not existing_lock or existing_lock.lock_id != lock_id:
                    return False
                
                # Extend TTL
                existing_lock.acquired_at = datetime.utcnow()
                existing_lock.ttl_seconds = ttl_seconds
                
                return True
        except Exception as e:
            print(f"Error extending lock: {e}")
            return False
    
    async def is_locked(self, resource_key: str) -> bool:
        """Check if resource is locked"""
        try:
            async with self.lock:
                lock = self.locks.get(resource_key)
                return lock is not None and not lock.is_expired
        except Exception:
            return False
    
    async def _release_all_locks(self) -> None:
        """Release all locks held by this node"""
        try:
            locks_to_release = [
                key for key, lock in self.locks.items()
                if lock.owner_node == self.node_id
            ]
            
            for key in locks_to_release:
                del self.locks[key]
        except Exception as e:
            print(f"Error releasing all locks: {e}")
    
    # ===== Synchronization =====
    
    async def _sync_loop(self) -> None:
        """Periodic synchronization with cluster"""
        while self.enabled:
            try:
                await self._sync_with_cluster()
                await asyncio.sleep(self.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Sync loop error: {e}")
                await asyncio.sleep(1)
    
    async def _sync_with_cluster(self) -> None:
        """Synchronize state with cluster"""
        try:
            # In production, fetch state from other nodes
            # and merge using version vectors
            pass
        except Exception as e:
            print(f"Error syncing with cluster: {e}")
    
    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of expired locks"""
        while self.enabled:
            try:
                await self._cleanup_expired_locks()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Cleanup loop error: {e}")
                await asyncio.sleep(1)
    
    async def _cleanup_expired_locks(self) -> None:
        """Clean up expired locks"""
        try:
            async with self.lock:
                expired_keys = [
                    key for key, lock in self.locks.items()
                    if lock.is_expired
                ]
                
                for key in expired_keys:
                    del self.locks[key]
                    
                    # Notify waiters
                    if key in self.lock_waiters:
                        for waiter in self.lock_waiters[key]:
                            if not waiter.done():
                                waiter.set_result(None)
                        del self.lock_waiters[key]
        except Exception as e:
            print(f"Error cleaning up locks: {e}")
    
    # ===== Status and Statistics =====
    
    async def get_status(self) -> Dict[str, Any]:
        """Get distributed state status"""
        try:
            async with self.lock:
                active_locks = [
                    {
                        'resource': lock.resource_key,
                        'owner': lock.owner_node,
                        'remaining_ttl': lock.remaining_ttl,
                        'is_expired': lock.is_expired
                    }
                    for lock in self.locks.values()
                ]
                
                return {
                    'enabled': self.enabled,
                    'node_id': self.node_id,
                    'state_entries': len(self.state),
                    'active_locks': len(self.locks),
                    'lock_waiters': sum(len(w) for w in self.lock_waiters.values()),
                    'locks': active_locks,
                    'sync_interval': self.sync_interval
                }
        except Exception as e:
            print(f"Error getting status: {e}")
            return {'enabled': self.enabled, 'error': str(e)}
    
    async def get_all_state(self) -> Dict[str, Any]:
        """Get all state entries"""
        try:
            async with self.lock:
                return {
                    key: {
                        'value': entry.value,
                        'version': entry.version,
                        'updated_at': entry.updated_at.isoformat(),
                        'updated_by': entry.updated_by
                    }
                    for key, entry in self.state.items()
                }
        except Exception as e:
            print(f"Error getting all state: {e}")
            return {}
    
    async def reset(self) -> bool:
        """Reset distributed state manager"""
        try:
            await self.disable()
            self.state.clear()
            self.version_vectors.clear()
            self.locks.clear()
            self.lock_waiters.clear()
            return True
        except Exception as e:
            print(f"Error resetting: {e}")
            return False
