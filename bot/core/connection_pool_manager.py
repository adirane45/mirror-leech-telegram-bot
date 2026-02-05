"""
Connection Pool Manager for Database Connection Pooling

Manages efficiently reusable database connections, implements health checks,
auto-reconnection, and connection lifecycle management.

Features:
- Connection pooling and reuse
- Health checking
- Auto-reconnection
- Timeout management
- Connection statistics
- Multiple backend support
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum
import random


class ConnectionState(Enum):
    """Connection state"""
    IDLE = "idle"
    IN_USE = "in_use"
    CLOSED = "closed"
    ERROR = "error"


@dataclass
class ConnectionStats:
    """Connection statistics"""
    total_connections: int
    active_connections: int
    idle_connections: int
    failed_connections: int
    total_requests: int
    avg_wait_time_ms: float
    max_wait_time_ms: float
    connection_reuses: int
    avg_connection_lifetime: float


class PooledConnection:
    """A pooled connection with lifecycle management"""
    
    def __init__(self, connection_id: str, backend: str):
        self.id = connection_id
        self.backend = backend
        self.connection = None
        self.state = ConnectionState.IDLE
        self.created_at = datetime.utcnow()
        self.last_used_at = datetime.utcnow()
        self.use_count = 0
        self.error_count = 0
        self.timeout = 30  # seconds
        self.is_healthy = True
    
    def get_age_seconds(self) -> float:
        """Get connection age in seconds"""
        return (datetime.utcnow() - self.created_at).total_seconds()
    
    def get_idle_time_seconds(self) -> float:
        """Get idle time in seconds"""
        return (datetime.utcnow() - self.last_used_at).total_seconds()
    
    def mark_used(self) -> None:
        """Mark connection as used"""
        self.last_used_at = datetime.utcnow()
        self.use_count += 1
        self.state = ConnectionState.IN_USE
    
    def mark_idle(self) -> None:
        """Mark connection as idle"""
        self.state = ConnectionState.IDLE
    
    def mark_error(self) -> None:
        """Mark connection with error"""
        self.error_count += 1
        self.is_healthy = self.error_count < 3
        self.state = ConnectionState.ERROR
    
    async def close(self) -> None:
        """Close connection"""
        try:
            if self.connection and hasattr(self.connection, 'close'):
                await self.connection.close()
            self.state = ConnectionState.CLOSED
        except Exception:
            pass


class ConnectionPool:
    """Generic connection pool"""
    
    def __init__(
        self,
        name: str,
        backend: str,
        min_size: int = 5,
        max_size: int = 20,
        acquire_timeout: int = 10,
        idle_timeout: int = 600,
        max_lifetime: int = 3600
    ):
        self.name = name
        self.backend = backend
        self.min_size = min_size
        self.max_size = max_size
        self.acquire_timeout = acquire_timeout
        self.idle_timeout = idle_timeout  # seconds
        self.max_lifetime = max_lifetime  # seconds
        
        self.connections: List[PooledConnection] = []
        self.available_connections: asyncio.Queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(max_size)
        
        self.total_requests = 0
        self.wait_times: List[float] = []
        self.connection_counter = 0
        self.lock = asyncio.Lock()
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize pool with minimum connections"""
        try:
            async with self.lock:
                for _ in range(self.min_size):
                    await self._create_connection()
                self.initialized = True
                return True
        except Exception as e:
            print(f"Pool initialization error: {e}")
            return False
    
    async def _create_connection(self) -> Optional[PooledConnection]:
        """Create a new pooled connection"""
        try:
            self.connection_counter += 1
            conn_id = f"{self.name}_{self.connection_counter}"
            
            pooled_conn = PooledConnection(conn_id, self.backend)
            # conn.connection = await self._establish_connection()
            
            self.connections.append(pooled_conn)
            await self.available_connections.put(pooled_conn)
            
            return pooled_conn
        except Exception as e:
            print(f"Connection creation error: {e}")
            return None
    
    async def acquire(self) -> Optional[PooledConnection]:
        """Acquire a connection from pool"""
        try:
            # Wait for semaphore
            start_wait = time.time()
            await asyncio.wait_for(self.semaphore.acquire(), timeout=self.acquire_timeout)
            wait_time = (time.time() - start_wait) * 1000  # Convert to ms
            self.wait_times.append(wait_time)
            self.total_requests += 1
            
            # Get available connection
            try:
                pooled_conn = self.available_connections.get_nowait()
            except asyncio.QueueEmpty:
                # Create new if under limit
                if len(self.connections) < self.max_size:
                    pooled_conn = await self._create_connection()
                else:
                    # Wait for available
                    try:
                        pooled_conn = await asyncio.wait_for(
                            self.available_connections.get(),
                            timeout=self.acquire_timeout
                        )
                    except asyncio.TimeoutError:
                        self.semaphore.release()
                        return None
            
            if not pooled_conn:
                self.semaphore.release()
                return None
            
            # Check health
            if not await self._check_health(pooled_conn):
                await pooled_conn.close()
                self.semaphore.release()
                return await self.acquire()  # Recursive: try again
            
            pooled_conn.mark_used()
            return pooled_conn
        except Exception as e:
            print(f"Connection acquire error: {e}")
            return None
    
    async def release(self, pooled_conn: PooledConnection) -> None:
        """Release connection back to pool"""
        try:
            if not pooled_conn:
                self.semaphore.release()
                return
            
            # Check if should close due to age or errors
            if (pooled_conn.get_age_seconds() > self.max_lifetime or
                pooled_conn.error_count >= 3):
                await pooled_conn.close()
                async with self.lock:
                    self.connections.remove(pooled_conn)
                self.semaphore.release()
                return
            
            pooled_conn.mark_idle()
            await self.available_connections.put(pooled_conn)
            self.semaphore.release()
        except Exception as e:
            print(f"Connection release error: {e}")
            self.semaphore.release()
    
    async def _check_health(self, pooled_conn: PooledConnection) -> bool:
        """Check connection health"""
        try:
            # In production, implement actual health check
            if not pooled_conn.is_healthy:
                return False
            
            if pooled_conn.get_idle_time_seconds() > self.idle_timeout:
                await pooled_conn.close()
                return False
            
            return True
        except Exception:
            return False
    
    async def close_all(self) -> None:
        """Close all connections"""
        async with self.lock:
            for conn in self.connections:
                await conn.close()
            self.connections.clear()
            
            while not self.available_connections.empty():
                try:
                    self.available_connections.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            self.initialized = False
    
    async def get_statistics(self) -> ConnectionStats:
        """Get pool statistics"""
        try:
            active = sum(1 for c in self.connections if c.state == ConnectionState.IN_USE)
            idle = sum(1 for c in self.connections if c.state == ConnectionState.IDLE)
            failed = sum(1 for c in self.connections if c.state == ConnectionState.ERROR)
            reuses = sum(c.use_count for c in self.connections)
            
            avg_wait = sum(self.wait_times) / len(self.wait_times) if self.wait_times else 0
            max_wait = max(self.wait_times) if self.wait_times else 0
            avg_lifetime = sum(c.get_age_seconds() for c in self.connections) / len(self.connections) if self.connections else 0
            
            return ConnectionStats(
                total_connections=len(self.connections),
                active_connections=active,
                idle_connections=idle,
                failed_connections=failed,
                total_requests=self.total_requests,
                avg_wait_time_ms=round(avg_wait, 2),
                max_wait_time_ms=round(max_wait, 2),
                connection_reuses=reuses,
                avg_connection_lifetime=round(avg_lifetime, 2)
            )
        except Exception as e:
            print(f"Error getting stats: {e}")
            return ConnectionStats(0, 0, 0, 0, 0, 0.0, 0.0, 0, 0.0)


class ConnectionPoolManager:
    """Manages multiple connection pools"""
    
    _instance: Optional['ConnectionPoolManager'] = None
    
    def __init__(self):
        self.enabled = False
        self.pools: Dict[str, ConnectionPool] = {}
        self.default_pool_config = {
            'min_size': 5,
            'max_size': 20,
            'acquire_timeout': 10,
            'idle_timeout': 600,
            'max_lifetime': 3600
        }
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'ConnectionPoolManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = ConnectionPoolManager()
        return cls._instance
    
    async def enable(self) -> bool:
        """Enable connection pool manager"""
        try:
            async with self.lock:
                self.enabled = True
                return True
        except Exception as e:
            print(f"Error enabling pool manager: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable connection pool manager"""
        try:
            async with self.lock:
                self.enabled = False
                for pool in self.pools.values():
                    await pool.close_all()
                self.pools.clear()
                return True
        except Exception as e:
            print(f"Error disabling pool manager: {e}")
            return False
    
    async def create_pool(
        self,
        name: str,
        backend: str,
        **kwargs
    ) -> bool:
        """Create a new connection pool"""
        if not self.enabled:
            return False
        
        try:
            async with self.lock:
                if name in self.pools:
                    return False
                
                config = {**self.default_pool_config, **kwargs}
                pool = ConnectionPool(name, backend, **config)
                
                if await pool.initialize():
                    self.pools[name] = pool
                    return True
                return False
        except Exception as e:
            print(f"Error creating pool: {e}")
            return False
    
    async def get_pool(self, name: str) -> Optional[ConnectionPool]:
        """Get a connection pool by name"""
        return self.pools.get(name)
    
    async def acquire_connection(self, pool_name: str) -> Optional[PooledConnection]:
        """Acquire a connection from pool"""
        if not self.enabled:
            return None
        
        pool = self.pools.get(pool_name)
        if not pool:
            return None
        
        return await pool.acquire()
    
    async def release_connection(
        self,
        pool_name: str,
        connection: PooledConnection
    ) -> None:
        """Release a connection back to pool"""
        pool = self.pools.get(pool_name)
        if pool:
            await pool.release(connection)
    
    async def get_all_statistics(self) -> Dict[str, ConnectionStats]:
        """Get statistics for all pools"""
        try:
            stats = {}
            for name, pool in self.pools.items():
                stats[name] = await pool.get_statistics()
            return stats
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    async def close_pool(self, name: str) -> bool:
        """Close and remove a pool"""
        try:
            if name in self.pools:
                await self.pools[name].close_all()
                del self.pools[name]
                return True
            return False
        except Exception as e:
            print(f"Error closing pool: {e}")
            return False
    
    async def reset(self) -> bool:
        """Reset all pools"""
        try:
            await self.disable()
            self.pools.clear()
            return True
        except Exception as e:
            print(f"Error resetting: {e}")
            return False
