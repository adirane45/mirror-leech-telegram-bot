"""
Phase 4: Connection Pool Manager
Manages reusable database connection pools for improved performance
"""

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .connection_pool_manager_models import BackendType, PoolStatistics, Connection

logger = logging.getLogger(__name__)


class ConnectionPool:
    """Manages a pool of connections for a specific database"""
    
    def __init__(
        self,
        name: str,
        backend: BackendType,
        min_size: int = 5,
        max_size: int = 20
    ):
        self.name = name
        self.backend = backend
        self.min_size = min_size
        self.max_size = max_size
        
        self.available_connections: asyncio.Queue = asyncio.Queue()
        self.all_connections: Dict[str, Connection] = {}
        self.active_connections: set = set()
        
        self.lock = asyncio.Lock()
        self.statistics = PoolStatistics(pool_name=name)
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the pool with minimum connections"""
        async with self.lock:
            try:
                logger.info(f"Initializing pool '{self.name}' ({self.min_size}-{self.max_size} connections)")
                
                # In production, would create actual connections
                # For now, create dummy connections
                for i in range(self.min_size):
                    conn_id = f"{self.name}-{i}"
                    # Create dummy connection object
                    dummy_conn = f"connection_{conn_id}"
                    conn = Connection(conn_id, self.backend, dummy_conn)
                    self.all_connections[conn_id] = conn
                    await self.available_connections.put(conn_id)
                
                self.statistics.idle_connections = self.min_size
                self.statistics.total_connections = self.min_size
                self.initialized = True
                logger.info(f"Pool '{self.name}' initialized with {self.min_size} connections")
                return True
            except Exception as e:
                logger.error(f"Error initializing pool '{self.name}': {e}")
                return False

    async def acquire_connection(self, timeout: float = 10.0) -> Optional[Connection]:
        """
        Acquire a connection from the pool
        
        Args:
            timeout: Max wait time in seconds
            
        Returns:
            Connection or None if timeout
        """
        try:
            start_time = datetime.now()
            
            # Try to get available connection
            try:
                conn_id = await asyncio.wait_for(
                    self.available_connections.get(),
                    timeout=timeout
                )
                conn = self.all_connections.get(conn_id)
                
                if conn:
                    # Check health
                    if not conn.is_healthy or conn.is_expired():
                        await self.release_connection(conn, is_healthy=False)
                        return await self.acquire_connection(timeout)
                    
                    # Mark as active
                    self.active_connections.add(conn_id)
                    conn.last_used = datetime.now()
                    conn.use_count += 1
                    
                    # Update statistics
                    wait_time = (datetime.now() - start_time).total_seconds() * 1000
                    self.statistics.total_acquired += 1
                    self.statistics.active_connections = len(self.active_connections)
                    self.statistics.idle_connections = self.available_connections.qsize()
                    self.statistics.avg_wait_time_ms = (
                        (self.statistics.avg_wait_time_ms * (self.statistics.total_acquired - 1) + wait_time)
                        / self.statistics.total_acquired
                    )
                    
                    logger.debug(f"Acquired connection from pool '{self.name}': {conn_id}")
                    return conn
                    
            except asyncio.TimeoutError:
                # Check if we can create new connection
                async with self.lock:
                    if len(self.all_connections) < self.max_size:
                        conn_id = f"{self.name}-{len(self.all_connections)}"
                        dummy_conn = f"connection_{conn_id}"
                        conn = Connection(conn_id, self.backend, dummy_conn)
                        self.all_connections[conn_id] = conn
                        self.active_connections.add(conn_id)
                        
                        self.statistics.total_connections = len(self.all_connections)
                        self.statistics.active_connections = len(self.active_connections)
                        self.statistics.total_acquired += 1
                        
                        logger.info(f"Created new connection for pool '{self.name}': {conn_id}")
                        return conn
                
                self.statistics.failed_acquisitions += 1
                logger.error(f"Failed to acquire connection from pool '{self.name}' (timeout)")
                return None
                
        except Exception as e:
            logger.error(f"Error acquiring connection: {e}")
            self.statistics.failed_acquisitions += 1
            return None

    async def release_connection(self, conn: Connection, is_healthy: bool = True) -> bool:
        """
        Release connection back to the pool
        
        Args:
            conn: Connection to release
            is_healthy: Whether connection is healthy
            
        Returns:
            Success status
        """
        try:
            if is_healthy:
                # Return to available pool
                conn.is_healthy = True
                self.active_connections.discard(conn.connection_id)
                await self.available_connections.put(conn.connection_id)
                
                self.statistics.total_released += 1
                self.statistics.active_connections = len(self.active_connections)
                self.statistics.idle_connections = self.available_connections.qsize()
                
                logger.debug(f"Released connection to pool '{self.name}': {conn.connection_id}")
            else:
                # Connection is unhealthy, remove it
                self.active_connections.discard(conn.connection_id)
                del self.all_connections[conn.connection_id]
                
                # Create replacement if needed
                async with self.lock:
                    if len(self.all_connections) < self.min_size:
                        new_conn_id = f"{self.name}-{len(self.all_connections)}"
                        dummy_conn = f"connection_{new_conn_id}"
                        new_conn = Connection(new_conn_id, self.backend, dummy_conn)
                        self.all_connections[new_conn_id] = new_conn
                        await self.available_connections.put(new_conn_id)
                        logger.info(f"Created replacement connection for pool '{self.name}'")
                
                self.statistics.active_connections = len(self.active_connections)
            
            return True
        except Exception as e:
            logger.error(f"Error releasing connection: {e}")
            return False

    async def health_check(self) -> bool:
        """Check health of all connections in pool"""
        healthy_count = sum(1 for c in self.all_connections.values() if c.is_healthy)
        logger.info(f"Pool '{self.name}' health check: {healthy_count}/{len(self.all_connections)} healthy")
        return healthy_count > 0

    async def get_statistics(self) -> Dict[str, Any]:
        """Get pool statistics"""
        return {
            'pool_name': self.name,
            'backend': self.backend.value,
            'total_connections': self.statistics.total_connections,
            'active_connections': self.statistics.active_connections,
            'idle_connections': self.statistics.idle_connections,
            'min_size': self.min_size,
            'max_size': self.max_size,
            'utilization_percent': self.statistics.utilization_percent,
            'total_acquired': self.statistics.total_acquired,
            'total_released': self.statistics.total_released,
            'failed_acquisitions': self.statistics.failed_acquisitions,
            'avg_wait_time_ms': self.statistics.avg_wait_time_ms,
        }


class ConnectionPoolManager:
    """
    Singleton manager for all connection pools
    """

    _instance: Optional['ConnectionPoolManager'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.enabled = False
        self.pools: Dict[str, ConnectionPool] = {}
        
    @classmethod
    def get_instance(cls) -> 'ConnectionPoolManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = ConnectionPoolManager()
        return cls._instance

    async def enable(self) -> bool:
        """Enable the Connection Pool Manager"""
        async with self._lock:
            self.enabled = True
            logger.info("Connection Pool Manager enabled")
            return True

    async def disable(self) -> bool:
        """Disable the Connection Pool Manager"""
        async with self._lock:
            self.enabled = False
            self.pools.clear()
            logger.info("Connection Pool Manager disabled")
            return True

    async def create_pool(
        self,
        name: str,
        backend: str,
        min_size: int = 5,
        max_size: int = 20
    ) -> bool:
        """
        Create a new connection pool
        
        Args:
            name: Pool identifier
            backend: Backend type (mongodb, redis, postgresql, mysql)
            min_size: Minimum pool size
            max_size: Maximum pool size
            
        Returns:
            Success status
        """
        if not self.enabled:
            return False

        try:
            # Map backend string to enum
            backend_enum = BackendType[backend.upper()]
            
            pool = ConnectionPool(
                name=name,
                backend=backend_enum,
                min_size=min_size,
                max_size=max_size
            )
            
            if await pool.initialize():
                self.pools[name] = pool
                logger.info(f"Created connection pool '{name}' ({backend})")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error creating pool '{name}': {e}")
            return False

    async def acquire_connection(
        self,
        pool_name: str,
        timeout: float = 10.0
    ) -> Optional[Connection]:
        """
        Acquire connection from named pool
        
        Args:
            pool_name: Pool identifier
            timeout: Max wait time in seconds
            
        Returns:
            Connection or None if not available
        """
        if pool_name not in self.pools:
            logger.error(f"Pool '{pool_name}' not found")
            return None
        
        pool = self.pools[pool_name]
        return await pool.acquire_connection(timeout)

    async def release_connection(
        self,
        pool_name: str,
        connection: Connection,
        is_healthy: bool = True
    ) -> bool:
        """
        Release connection back to pool
        
        Args:
            pool_name: Pool identifier
            connection: Connection to release
            is_healthy: Whether connection is still healthy
            
        Returns:
            Success status
        """
        if pool_name not in self.pools:
            logger.error(f"Pool '{pool_name}' not found")
            return False
        
        pool = self.pools[pool_name]
        return await pool.release_connection(connection, is_healthy)

    async def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools"""
        stats = {}
        for pool_name, pool in self.pools.items():
            stats[pool_name] = await pool.get_statistics()
        return stats

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all pools"""
        results = {}
        for pool_name, pool in self.pools.items():
            results[pool_name] = await pool.health_check()
        return results
