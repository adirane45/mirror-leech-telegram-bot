"""
Connection Pool Manager Models
Data structures for connection pooling
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from datetime import datetime


class BackendType(Enum):
    """Supported database backend types"""
    MONGODB = "mongodb"
    REDIS = "redis"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


@dataclass
class PoolStatistics:
    """Statistics for a connection pool"""
    pool_name: str
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    total_acquired: int = 0
    total_released: int = 0
    failed_acquisitions: int = 0
    avg_wait_time_ms: float = 0.0
    max_wait_time_ms: float = 0.0
    
    @property
    def utilization_percent(self) -> float:
        """Calculate pool utilization percentage"""
        if self.total_connections == 0:
            return 0.0
        return (self.active_connections / self.total_connections) * 100


class Connection:
    """Wrapper around a database connection"""
    
    def __init__(self, connection_id: str, backend: BackendType, raw_connection: Any):
        self.connection_id = connection_id
        self.backend = backend
        self.raw_connection = raw_connection
        self.created_at = datetime.now()
        self.last_used = datetime.now()
        self.is_healthy = True
        self.use_count = 0

    def is_expired(self, max_lifetime_seconds: int = 3600) -> bool:
        """Check if connection has exceeded max lifetime"""
        age = datetime.now() - self.created_at
        return age.total_seconds() > max_lifetime_seconds

    def mark_unhealthy(self) -> None:
        """Mark connection as unhealthy"""
        import logging
        logger = logging.getLogger(__name__)
        self.is_healthy = False
        logger.warning(f"Connection {self.connection_id} marked as unhealthy")
