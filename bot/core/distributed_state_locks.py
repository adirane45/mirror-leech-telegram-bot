"""
Distributed Locking Manager for cluster-wide lock management

Handles:
- Lock acquisition/release
- Lock expiration monitoring
- Contention tracking
- Lock state synchronization
"""

import asyncio
import uuid
from datetime import datetime, timedelta, UTC
from typing import Dict, Optional, List

from .distributed_state_models import LockInfo, LockType, LockState


class DistributedLockManager:
    """
    Manages distributed locks with expiration, contention, and state tracking
    
    Features:
    - Exclusive and shared lock types
    - Lock expiration and timeout handling
    - Contention detection and reporting
    - Metrics tracking for lock operations
    """
    
    def __init__(self, node_id: str, lock_timeout_seconds: int = 30):
        """
        Initialize lock manager
        
        Args:
            node_id: Unique identifier for this node
            lock_timeout_seconds: Lock expiration time in seconds
        """
        self.node_id = node_id
        self.lock_timeout_seconds = lock_timeout_seconds
        self.locks: Dict[str, LockInfo] = {}
        
        # Metrics
        self.lock_acquisitions = 0
        self.lock_contentions = 0
        
        # Background task
        self._lock_monitor_task: Optional[asyncio.Task] = None
        self._enabled = False
        
        # Listeners for lock events
        self._listeners: List = []
    
    async def start(self) -> None:
        """Start lock monitoring background task"""
        if not self._enabled:
            self._enabled = True
            self._lock_monitor_task = asyncio.create_task(self._lock_monitor_loop())
    
    async def stop(self) -> None:
        """Stop lock monitoring background task"""
        self._enabled = False
        if self._lock_monitor_task:
            self._lock_monitor_task.cancel()
            try:
                await self._lock_monitor_task
            except asyncio.CancelledError:
                pass
    
    async def acquire_lock(
        self, 
        key: str, 
        lock_type: LockType = LockType.EXCLUSIVE
    ) -> bool:
        """
        Acquire distributed lock on key
        
        Args:
            key: Resource key to lock
            lock_type: Type of lock (EXCLUSIVE or SHARED)
            
        Returns:
            True if lock acquired, False if contested or unavailable
        """
        if not self._enabled:
            return False
        
        try:
            lock_id = f"lock_{uuid.uuid4().hex[:8]}"
            lock = LockInfo(
                lock_id=lock_id,
                key=key,
                lock_type=lock_type,
                owner_node=self.node_id,
                state=LockState.PENDING,
                expires_at=datetime.now(UTC) + timedelta(seconds=self.lock_timeout_seconds)
            )
            
            # Check for existing exclusive lock
            existing = self.locks.get(key)
            if existing and existing.lock_type == LockType.EXCLUSIVE:
                if existing.owner_node != self.node_id:
                    lock.state = LockState.CONTESTED
                    lock.contenders.add(self.node_id)
                    self.lock_contentions += 1
                    self.locks[key] = lock
                    return False
            
            # Acquire lock
            lock.state = LockState.ACQUIRED
            lock.acquired_at = datetime.now(UTC)
            self.locks[key] = lock
            self.lock_acquisitions += 1
            
            # Notify listeners
            await self._notify_lock_acquired(lock)
            
            return True
        except Exception:
            return False
    
    async def release_lock(self, key: str) -> bool:
        """
        Release distributed lock on key
        
        Args:
            key: Resource key to unlock
            
        Returns:
            True if lock released, False if not owned
        """
        if key not in self.locks:
            return False
        
        try:
            lock = self.locks[key]
            if lock.owner_node != self.node_id:
                return False
            
            lock.state = LockState.RELEASED
            self.locks.pop(key, None)
            
            # Notify listeners
            await self._notify_lock_released(lock)
            
            return True
        except Exception:
            return False
    
    async def get_lock_info(self, key: str) -> Optional[LockInfo]:
        """
        Get information about lock on key
        
        Args:
            key: Resource key
            
        Returns:
            LockInfo if lock exists, None otherwise
        """
        return self.locks.get(key)
    
    async def get_all_locks(self) -> Dict[str, LockInfo]:
        """Get all active locks"""
        return dict(self.locks)
    
    async def clear_locks(self) -> None:
        """Clear all locks (for testing/cleanup)"""
        self.locks.clear()
    
    def add_listener(self, listener) -> None:
        """Add listener for lock events"""
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def remove_listener(self, listener) -> None:
        """Remove listener for lock events"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    async def _notify_lock_acquired(self, lock: LockInfo) -> None:
        """Notify listeners that lock was acquired"""
        for listener in self._listeners:
            if hasattr(listener, 'on_lock_acquired'):
                await listener.on_lock_acquired(lock)
    
    async def _notify_lock_released(self, lock: LockInfo) -> None:
        """Notify listeners that lock was released"""
        for listener in self._listeners:
            if hasattr(listener, 'on_lock_released'):
                await listener.on_lock_released(lock)
    
    async def _lock_monitor_loop(self) -> None:
        """Background loop for monitoring locks"""
        while self._enabled:
            try:
                # Check for expired locks
                expired_keys = []
                for key, lock in self.locks.items():
                    if lock.expires_at and lock.expires_at < datetime.now(UTC):
                        expired_keys.append(key)
                
                # Release expired locks
                for key in expired_keys:
                    self.locks[key].state = LockState.TIMEOUT
                    self.locks.pop(key, None)
                
                await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(5)
    
    def get_metrics(self) -> Dict:
        """Get lock operation metrics"""
        return {
            'lock_acquisitions': self.lock_acquisitions,
            'lock_contentions': self.lock_contentions,
            'active_locks': len(self.locks),
        }
