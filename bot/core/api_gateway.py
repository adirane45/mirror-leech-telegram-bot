"""
API Gateway for request routing and management

Implements:
- Request routing to cluster nodes
- Rate limiting and throttling
- Authentication and authorization
- Request/response metrics
- Circuit breaker pattern
"""

import asyncio
import uuid
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Set, Optional

# Import models from refactored api_gateway_models module
from .api_gateway_models import (
    RequestMethod,
    CircuitState,
    ApiRequest,
    ApiResponse,
    RateLimitConfig,
    CircuitBreakerConfig,
    RouteConfig,
    GatewayMetrics,
    ApiGatewayListener,
)


class ApiGateway:
    """
    API Gateway for distributed request management
    
    Singleton instance managing:
    - Request routing
    - Rate limiting
    - Circuit breakers
    - Authentication/authorization
    - Metrics collection
    """
    
    _instance: Optional['ApiGateway'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.enabled = False
        self.node_id = ""
        self.routes: Dict[str, RouteConfig] = {}
        self.nodes: Set[str] = set()
        self.request_history: Dict[str, List[datetime]] = {}  # client_id -> timestamps
        self.circuit_states: Dict[str, CircuitState] = {}  # node_id -> state
        self.circuit_failures: Dict[str, int] = {}  # node_id -> failure count
        self.circuit_successes: Dict[str, int] = {}  # node_id -> success count
        self.metrics = GatewayMetrics()
        self.listeners: List[ApiGatewayListener] = []
        self.auth_tokens: Set[str] = set()
        self.default_rate_limit = RateLimitConfig()
        self.default_circuit_breaker = CircuitBreakerConfig()
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._circuit_check_task: Optional[asyncio.Task] = None
    
    @classmethod
    def get_instance(cls) -> 'ApiGateway':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def start(self, node_id: str = "") -> bool:
        """Start API gateway"""
        if self.enabled:
            return True
        
        try:
            self.node_id = node_id or f"gateway_{uuid.uuid4().hex[:8]}"
            self.enabled = True
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._circuit_check_task = asyncio.create_task(self._circuit_check_loop())
            
            return True
        except Exception:
            self.enabled = False
            return False
    
    async def stop(self) -> bool:
        """Stop API gateway"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._circuit_check_task:
                self._circuit_check_task.cancel()
            
            await asyncio.sleep(0.1)
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # ROUTING
    # ========================================================================
    
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
            self.nodes.add(node_id)
            self.circuit_states[node_id] = CircuitState.CLOSED
            self.circuit_failures[node_id] = 0
            self.circuit_successes[node_id] = 0
            return True
        except Exception:
            return False
    
    async def route_request(self, request: ApiRequest) -> ApiResponse:
        """Route request to appropriate node"""
        if not self.enabled:
            return ApiResponse(
                request_id=request.request_id,
                status_code=503,
                body="Gateway not enabled"
            )
        
        start_time = datetime.now(UTC)
        
        try:
            self.metrics.total_requests += 1
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_request_received(request)
            
            # Check rate limit
            if not await self._check_rate_limit(request.client_id):
                self.metrics.rate_limited_requests += 1
                return ApiResponse(
                    request_id=request.request_id,
                    status_code=429,
                    body="Rate limit exceeded"
                )
            
            # Find route
            route = self.routes.get(request.path)
            if not route:
                self.metrics.failed_requests += 1
                return ApiResponse(
                    request_id=request.request_id,
                    status_code=404,
                    body="Route not found"
                )
            
            # Check auth
            if route.requires_auth:
                auth_token = request.headers.get("Authorization", "")
                if not await self._check_auth(auth_token):
                    self.metrics.failed_requests += 1
                    return ApiResponse(
                        request_id=request.request_id,
                        status_code=401,
                        body="Unauthorized"
                    )
            
            # Select target node
            target_node = await self._select_node(route)
            if not target_node:
                self.metrics.failed_requests += 1
                return ApiResponse(
                    request_id=request.request_id,
                    status_code=503,
                    body="No available nodes"
                )
            
            # Check circuit breaker
            if not await self._check_circuit(target_node):
                self.metrics.circuit_open_count += 1
                return ApiResponse(
                    request_id=request.request_id,
                    status_code=503,
                    body="Circuit breaker open"
                )
            
            # Notify routing
            for listener in self.listeners:
                await listener.on_request_routed(request, target_node)
            
            # Process request (simulated)
            response = await self._process_request(request, target_node)
            
            # Calculate processing time
            elapsed = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            response.processing_time_ms = elapsed
            
            # Update metrics
            if response.status_code < 400:
                self.metrics.successful_requests += 1
                await self._record_success(target_node)
            else:
                self.metrics.failed_requests += 1
                await self._record_failure(target_node)
            
            # Notify response
            for listener in self.listeners:
                await listener.on_response_sent(response)
            
            return response
            
        except Exception as e:
            self.metrics.failed_requests += 1
            return ApiResponse(
                request_id=request.request_id,
                status_code=500,
                body=f"Internal error: {str(e)}"
            )
    
    async def _select_node(self, route: RouteConfig) -> Optional[str]:
        """Select target node for route"""
        if route.target_node:
            return route.target_node
        
        if route.use_load_balancer and self.nodes:
            # Simple round-robin (in real impl, would use more sophisticated logic)
            available_nodes = [
                n for n in self.nodes
                if self.circuit_states.get(n) != CircuitState.OPEN
            ]
            if available_nodes:
                import random
                return random.choice(available_nodes)
        
        return None
    
    async def _process_request(self, request: ApiRequest, target_node: str) -> ApiResponse:
        """Process request (simulated)"""
        # In real implementation, would forward to actual node
        await asyncio.sleep(0.01)  # Simulate processing
        
        return ApiResponse(
            request_id=request.request_id,
            status_code=200,
            body={"message": "Success", "node": target_node}
        )
    
    # ========================================================================
    # RATE LIMITING
    # ========================================================================
    
    async def _check_rate_limit(self, client_id: str) -> bool:
        """Check if request is within rate limit"""
        if not self.default_rate_limit.enabled or not client_id:
            return True
        
        try:
            now = datetime.now(UTC)
            window_start = now - timedelta(seconds=self.default_rate_limit.window_seconds)
            
            # Get request history for client
            if client_id not in self.request_history:
                self.request_history[client_id] = []
            
            # Remove old requests
            self.request_history[client_id] = [
                ts for ts in self.request_history[client_id]
                if ts > window_start
            ]
            
            # Check limit
            if len(self.request_history[client_id]) >= self.default_rate_limit.max_requests:
                # Notify listeners
                for listener in self.listeners:
                    await listener.on_rate_limit_exceeded(client_id)
                return False
            
            # Record request
            self.request_history[client_id].append(now)
            return True
            
        except Exception:
            return True  # Allow on error
    
    async def set_rate_limit(self, max_requests: int, window_seconds: int) -> bool:
        """Set global rate limit"""
        try:
            self.default_rate_limit = RateLimitConfig(
                max_requests=max_requests,
                window_seconds=window_seconds,
                enabled=True
            )
            return True
        except Exception:
            return False
    
    # ========================================================================
    # CIRCUIT BREAKER
    # ========================================================================
    
    async def _check_circuit(self, node_id: str) -> bool:
        """Check circuit breaker state"""
        if not self.default_circuit_breaker.enabled:
            return True
        
        state = self.circuit_states.get(node_id, CircuitState.CLOSED)
        
        if state == CircuitState.OPEN:
            return False
        elif state == CircuitState.HALF_OPEN:
            # Allow one request to test
            return True
        
        return True
    
    async def _record_failure(self, node_id: str) -> None:
        """Record request failure for circuit breaker"""
        if not self.default_circuit_breaker.enabled:
            return
        
        try:
            self.circuit_failures[node_id] = self.circuit_failures.get(node_id, 0) + 1
            self.circuit_successes[node_id] = 0
            
            # Check if should open circuit
            if self.circuit_failures[node_id] >= self.default_circuit_breaker.failure_threshold:
                self.circuit_states[node_id] = CircuitState.OPEN
                self.circuit_failures[node_id] = 0
        except Exception:
            pass
    
    async def _record_success(self, node_id: str) -> None:
        """Record request success for circuit breaker"""
        if not self.default_circuit_breaker.enabled:
            return
        
        try:
            self.circuit_successes[node_id] = self.circuit_successes.get(node_id, 0) + 1
            self.circuit_failures[node_id] = 0
            
            state = self.circuit_states.get(node_id, CircuitState.CLOSED)
            
            # Check if should close circuit from half-open
            if state == CircuitState.HALF_OPEN:
                if self.circuit_successes[node_id] >= self.default_circuit_breaker.success_threshold:
                    self.circuit_states[node_id] = CircuitState.CLOSED
                    self.circuit_successes[node_id] = 0
        except Exception:
            pass
    
    async def _circuit_check_loop(self) -> None:
        """Background loop for circuit breaker recovery"""
        while self.enabled:
            try:
                timeout = self.default_circuit_breaker.timeout_seconds
                
                # Check for circuits to transition to half-open
                for node_id in self.circuit_states:
                    if self.circuit_states[node_id] == CircuitState.OPEN:
                        # In real implementation, would track when circuit opened
                        # For now, just transition to half-open occasionally
                        self.circuit_states[node_id] = CircuitState.HALF_OPEN
                
                await asyncio.sleep(timeout)
            except Exception:
                await asyncio.sleep(60)
    
    # ========================================================================
    # AUTHENTICATION
    # ========================================================================
    
    async def register_auth_token(self, token: str) -> bool:
        """Register authentication token"""
        try:
            self.auth_tokens.add(token)
            return True
        except Exception:
            return False
    
    async def _check_auth(self, token: str) -> bool:
        """Check authentication token"""
        return token in self.auth_tokens
    
    # ========================================================================
    # MANAGEMENT
    # ========================================================================
    
    async def add_listener(self, listener: ApiGatewayListener) -> bool:
        """Register gateway listener"""
        try:
            self.listeners.append(listener)
            return True
        except Exception:
            return False
    
    async def get_metrics(self) -> GatewayMetrics:
        """Get gateway metrics"""
        return self.metrics
    
    async def get_circuit_state(self, node_id: str) -> CircuitState:
        """Get circuit breaker state for node"""
        return self.circuit_states.get(node_id, CircuitState.CLOSED)
    
    async def is_enabled(self) -> bool:
        """Check if gateway is enabled"""
        return self.enabled
    
    async def _cleanup_loop(self) -> None:
        """Background loop for cleanup"""
        while self.enabled:
            try:
                # Clean up old request history
                cutoff = datetime.now(UTC) - timedelta(hours=1)
                for client_id in list(self.request_history.keys()):
                    self.request_history[client_id] = [
                        ts for ts in self.request_history[client_id]
                        if ts > cutoff
                    ]
                    
                    # Remove empty histories
                    if not self.request_history[client_id]:
                        del self.request_history[client_id]
                
                self.metrics.last_updated = datetime.now(UTC)
                await asyncio.sleep(300)
            except Exception:
                await asyncio.sleep(300)
