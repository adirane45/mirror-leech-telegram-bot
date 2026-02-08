"""
API Gateway Models - Data structures for request routing and management

Includes:
- Request method and circuit state enumerations
- Request/response and configuration dataclasses
- Gateway listener interface
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, Optional, Any


# ============================================================================
# ENUMS
# ============================================================================

class RequestMethod(str, Enum):
    """HTTP-like request methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


# ============================================================================
# DATACLASSES
# ============================================================================

@dataclass
class ApiRequest:
    """API request"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    method: RequestMethod = RequestMethod.GET
    path: str = "/"
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    client_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'request_id': self.request_id,
            'method': self.method.value,
            'path': self.path,
            'client_id': self.client_id,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ApiResponse:
    """API response"""
    request_id: str
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Any = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'request_id': self.request_id,
            'status_code': self.status_code,
            'processing_time_ms': self.processing_time_ms,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_requests: int = 100
    window_seconds: int = 60
    enabled: bool = True


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: int = 60
    enabled: bool = True


@dataclass
class RouteConfig:
    """Route configuration"""
    path: str
    target_node: Optional[str] = None
    use_load_balancer: bool = True
    requires_auth: bool = False
    rate_limit: Optional[RateLimitConfig] = None
    circuit_breaker: Optional[CircuitBreakerConfig] = None


@dataclass
class GatewayMetrics:
    """Metrics for API gateway"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    circuit_open_count: int = 0
    avg_response_time_ms: float = 0.0
    active_connections: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'rate_limited_requests': self.rate_limited_requests,
            'circuit_open_count': self.circuit_open_count,
            'avg_response_time_ms': round(self.avg_response_time_ms, 2),
            'active_connections': self.active_connections,
            'last_updated': self.last_updated.isoformat()
        }


# ============================================================================
# ABSTRACT LISTENERS
# ============================================================================

class ApiGatewayListener(ABC):
    """Abstract listener for gateway events"""
    
    @abstractmethod
    async def on_request_received(self, request: ApiRequest) -> None:
        """Called when request received"""
        pass
    
    @abstractmethod
    async def on_request_routed(self, request: ApiRequest, target_node: str) -> None:
        """Called when request routed"""
        pass
    
    @abstractmethod
    async def on_response_sent(self, response: ApiResponse) -> None:
        """Called when response sent"""
        pass
    
    @abstractmethod
    async def on_rate_limit_exceeded(self, client_id: str) -> None:
        """Called when rate limit exceeded"""
        pass
