"""
Load Balancer Models
Data structures for load balancing and bot instance management
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED = "weighted"
    RANDOM = "random"


@dataclass
class BotInstance:
    """Represents a bot instance"""
    instance_id: str
    host: str
    port: int
    weight: float = 1.0
    is_healthy: bool = True
    active_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    last_request_time: Optional[datetime] = None
    response_time_ms: float = 0.0
    
    @property
    def connection_ratio(self) -> float:
        """Get relative connection load"""
        return self.active_connections / max(1, self.weight)
