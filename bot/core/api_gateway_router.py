"""
API Gateway Router for request routing and load balancing



































































































































































































            pass        except Exception:            self.metrics.last_updated = datetime.now(UTC)                                del self.request_history[client_id]                if not self.request_history[client_id]:                # Remove empty histories                                ]                    if ts > cutoff                    ts for ts in self.request_history[client_id]                self.request_history[client_id] = [            for client_id in list(self.request_history.keys()):            cutoff = datetime.now(UTC) - timedelta(hours=hours)        try:        """Clean up old request history"""    async def cleanup_old_history(self, hours: int = 1) -> None:                self.listeners.append(listener)        if listener not in self.listeners:        """Add limiter listener"""    def add_listener(self, listener: ApiGatewayListener) -> None:            self.circuit_successes[node_id] = 0        self.circuit_failures[node_id] = 0        self.circuit_states[node_id] = CircuitState.CLOSED        """Initialize circuit state for node"""    def initialize_node(self, node_id: str) -> None:            self.enabled = enabled        """Set limiter enabled state"""    def set_enabled(self, enabled: bool) -> None:            return self.circuit_states.get(node_id, CircuitState.CLOSED)        """Get circuit breaker state for node"""    def get_circuit_state(self, node_id: str) -> CircuitState:                    await asyncio.sleep(60)            except Exception:                await asyncio.sleep(timeout)                                        self.circuit_states[node_id] = CircuitState.HALF_OPEN                        # For now, just transition to half-open occasionally                        # In real implementation, would track when circuit opened                    if self.circuit_states[node_id] == CircuitState.OPEN:                for node_id in self.circuit_states:                # Check for circuits to transition to half-open                                timeout = self.default_circuit_breaker.timeout_seconds            try:        while self.enabled:        """Background loop for circuit breaker recovery"""    async def circuit_check_loop(self) -> None:                pass        except Exception:                    self.circuit_successes[node_id] = 0                    self.circuit_states[node_id] = CircuitState.CLOSED                if self.circuit_successes[node_id] >= self.default_circuit_breaker.success_threshold:            if state == CircuitState.HALF_OPEN:            # Check if should close circuit from half-open                        state = self.circuit_states.get(node_id, CircuitState.CLOSED)                        self.circuit_failures[node_id] = 0            self.circuit_successes[node_id] = self.circuit_successes.get(node_id, 0) + 1        try:                    return        if not self.default_circuit_breaker.enabled:        """Record request success for circuit breaker"""    async def record_success(self, node_id: str) -> None:                pass        except Exception:                self.circuit_failures[node_id] = 0                self.circuit_states[node_id] = CircuitState.OPEN            if self.circuit_failures[node_id] >= self.default_circuit_breaker.failure_threshold:            # Check if should open circuit                        self.circuit_successes[node_id] = 0            self.circuit_failures[node_id] = self.circuit_failures.get(node_id, 0) + 1        try:                    return        if not self.default_circuit_breaker.enabled:        """Record request failure for circuit breaker"""    async def record_failure(self, node_id: str) -> None:            return True                    return True            # Allow one request to test        elif state == CircuitState.HALF_OPEN:            return False        if state == CircuitState.OPEN:                state = self.circuit_states.get(node_id, CircuitState.CLOSED)                    return True        if not self.default_circuit_breaker.enabled:        """Check circuit breaker state"""    async def check_circuit(self, node_id: str) -> bool:                return False        except Exception:            return True            )                enabled=True                window_seconds=window_seconds,                max_requests=max_requests,            self.default_rate_limit = RateLimitConfig(        try:        """Set global rate limit"""    async def set_rate_limit(self, max_requests: int, window_seconds: int) -> bool:                return True  # Allow on error        except Exception:                        return True            self.request_history[client_id].append(now)            # Record request                            return False                    await listener.on_rate_limit_exceeded(client_id)                for listener in self.listeners:                # Notify listeners            if len(self.request_history[client_id]) >= self.default_rate_limit.max_requests:            # Check limit                        ]                if ts > window_start                ts for ts in self.request_history[client_id]            self.request_history[client_id] = [            # Remove old requests                            self.request_history[client_id] = []            if client_id not in self.request_history:            # Get request history for client                        window_start = now - timedelta(seconds=self.default_rate_limit.window_seconds)            now = datetime.now(UTC)        try:                    return True        if not self.default_rate_limit.enabled or not client_id:        """Check if request is within rate limit"""    async def check_rate_limit(self, client_id: str) -> bool:            self._circuit_check_task: Optional[asyncio.Task] = None                self.default_circuit_breaker = CircuitBreakerConfig()        self.default_rate_limit = RateLimitConfig()                self.enabled = False        self.metrics = GatewayMetrics()        self.listeners: List[ApiGatewayListener] = []        self.circuit_successes: Dict[str, int] = {}        self.circuit_failures: Dict[str, int] = {}        self.circuit_states: Dict[str, CircuitState] = {}        self.request_history: Dict[str, List[datetime]] = {}    def __init__(self):        """    - Background recovery checks    - Node health tracking    - Circuit breaker state management    - Rate limit enforcement per client    Responsible for:        Manages rate limiting and circuit breaker logic    """class ApiGatewayLimiter:)    ApiGatewayListener,    GatewayMetrics,    CircuitBreakerConfig,    RateLimitConfig,    CircuitState,from .api_gateway_models import (from typing import Dict, List, Optionalfrom datetime import datetime, timedelta, UTCimport asyncio"""- Node health tracking- Request throttling- Circuit breaker pattern- Rate limiting enforcementImplements:
Implements:
- Route management and registration
- Node selection and load balancing
- Request routing to target nodes
"""

import asyncio
import random
from datetime import datetime, UTC
from typing import Dict, List, Optional

from .api_gateway_models import (
    ApiRequest,
    ApiResponse,
    RouteConfig,
    CircuitState,
    ApiGatewayListener,
)


class ApiGatewayRouter:
    """
    Routes requests to appropriate nodes
    
    Responsible for:
    - Route configuration and registration
    - Node management
    - Request routing logic
    - Load balancing decisions
    """
    
    def __init__(self):
        self.routes: Dict[str, RouteConfig] = {}
        self.nodes: Dict[str, dict] = {}  # node_id -> node info
        self.listeners: List[ApiGatewayListener] = []
        self.enabled = False
        self.node_id = ""
    
    async def register_route(self, route: RouteConfig) -> bool:
        """Register a route"""
        if not self.enabled:
            return False
        
        try:
            self.routes[route.path] = route
            return True
        except Exception:
            return False
    
    async def register_node(self, node_id: str) -> bool:
        """Register target node"""
        try:
            self.nodes[node_id] = {'id': node_id, 'state': CircuitState.CLOSED}
            return True
        except Exception:
            return False
    
    async def get_route(self, path: str) -> Optional[RouteConfig]:
        """Get route configuration"""
        return self.routes.get(path)
    
    async def get_available_nodes(self, exclude_open_circuits=True, circuit_states=None) -> list:
        """Get list of available nodes"""
        available = list(self.nodes.keys())
        
        if exclude_open_circuits and circuit_states:
            available = [
                n for n in available
                if circuit_states.get(n) != CircuitState.OPEN
            ]
        
        return available
    
    async def select_node(self, route: RouteConfig, circuit_states: Dict = None) -> Optional[str]:
        """Select target node for route"""
        if route.target_node:
            return route.target_node
        
        if route.use_load_balancer:
            available = await self.get_available_nodes(
                exclude_open_circuits=True,
                circuit_states=circuit_states or {}
            )
            if available:
                return random.choice(available)
        
        return None
    
    async def route_request(
        self,
        request: ApiRequest,
        target_node: str,
        get_circuit_state_fn=None
    ) -> ApiResponse:
        """Process request routing"""
        try:
            # Notify listeners of routing decision
            for listener in self.listeners:
                await listener.on_request_routed(request, target_node)
            
            # Process request (simulated)
            response = await self._process_request(request, target_node)
            return response
            
        except Exception as e:
            return ApiResponse(
                request_id=request.request_id,
                status_code=500,
                body=f"Routing error: {str(e)}"
            )
    
    async def _process_request(self, request: ApiRequest, target_node: str) -> ApiResponse:
        """Process request (simulated)"""
        # In real implementation, would forward to actual node
        await asyncio.sleep(0.01)  # Simulate processing
        
        return ApiResponse(
            request_id=request.request_id,
            status_code=200,
            body={"message": "Success", "node": target_node}
        )
    
    def set_enabled(self, enabled: bool) -> None:
        """Set router enabled state"""
        self.enabled = enabled
    
    def set_node_info(self, node_id: str) -> None:
        """Set local node info"""
        self.node_id = node_id
    
    def add_listener(self, listener: ApiGatewayListener) -> None:
        """Add router listener"""
        if listener not in self.listeners:
            self.listeners.append(listener)
    
    def get_all_routes(self) -> Dict[str, RouteConfig]:
        """Get all registered routes"""
        return self.routes.copy()
    
    def get_all_nodes(self) -> list:
        """Get all registered nodes"""
        return list(self.nodes.keys())
