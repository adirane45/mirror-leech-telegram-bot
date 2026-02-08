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
from datetime import datetime, UTC
from typing import Dict, List, Set, Optional

# Import models
from .api_gateway_models import (
    ApiRequest,
    ApiResponse,
    RouteConfig,
    GatewayMetrics,
    ApiGatewayListener,
)

# Import specialized components
from .api_gateway_router import ApiGatewayRouter
from .api_gateway_limiter import ApiGatewayLimiter


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
        self.auth_tokens: Set[str] = set()
        self.listeners: List[ApiGatewayListener] = []
        
        # Component delegation
        self.router = ApiGatewayRouter()
        self.limiter = ApiGatewayLimiter()
        
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
            
            # Configure components
            self.router.set_enabled(True)
            self.router.set_node_info(self.node_id)
            self.limiter.set_enabled(True)
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._circuit_check_task = asyncio.create_task(self.limiter.circuit_check_loop())
            
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
            self.router.set_enabled(False)
            self.limiter.set_enabled(False)
            
            if self._cleanup_task:
                self._cleanup_task.cancel()
            if self._circuit_check_task:
                self._circuit_check_task.cancel()
            
            await asyncio.sleep(0.1)
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # ROUTING DELEGATION
    # ========================================================================
    
    async def register_route(self, route: RouteConfig) -> bool:
        """Register a route"""
        return await self.router.register_route(route)
    
    async def register_node(self, node_id: str) -> bool:
        """Register target node"""
        result = await self.router.register_node(node_id)
        self.limiter.initialize_node(node_id)
        return result
    
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
            self.limiter.metrics.total_requests += 1
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_request_received(request)
            
            # Check rate limit
            if not await self.limiter.check_rate_limit(request.client_id):
                self.limiter.metrics.rate_limited_requests += 1
                return ApiResponse(
                    request_id=request.request_id,
                    status_code=429,
                    body="Rate limit exceeded"
                )
            
            # Find route
            route = await self.router.get_route(request.path)
            if not route:
                self.limiter.metrics.failed_requests += 1
                return ApiResponse(
                    request_id=request.request_id,
                    status_code=404,
                    body="Route not found"
                )
            
            # Check auth
            if route.requires_auth:
                auth_token = request.headers.get("Authorization", "")
                if not await self._check_auth(auth_token):
                    self.limiter.metrics.failed_requests += 1
                    return ApiResponse(
                        request_id=request.request_id,
                        status_code=401,
                        body="Unauthorized"
                    )
            
            # Select target node
            target_node = await self.router.select_node(
                route,
                circuit_states=self.limiter.circuit_states
            )
            if not target_node:
                self.limiter.metrics.failed_requests += 1
                return ApiResponse(
                    request_id=request.request_id,
                    status_code=503,
                    body="No available nodes"
                )
            
            # Check circuit breaker
            if not await self.limiter.check_circuit(target_node):
                self.limiter.metrics.circuit_open_count += 1
                return ApiResponse(
                    request_id=request.request_id,
                    status_code=503,
                    body="Circuit breaker open"
                )
            
            # Route request
            response = await self.router.route_request(request, target_node)
            
            # Calculate processing time
            elapsed = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            response.processing_time_ms = elapsed
            
            # Update metrics
            if response.status_code < 400:
                self.limiter.metrics.successful_requests += 1
                await self.limiter.record_success(target_node)
            else:
                self.limiter.metrics.failed_requests += 1
                await self.limiter.record_failure(target_node)
            
            # Notify response
            for listener in self.listeners:
                await listener.on_response_sent(response)
            
            return response
            
        except Exception as e:
            self.limiter.metrics.failed_requests += 1
            return ApiResponse(
                request_id=request.request_id,
                status_code=500,
                body=f"Internal error: {str(e)}"
            )
    
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
    # RATE LIMITING DELEGATION
    # ========================================================================
    
    async def set_rate_limit(self, max_requests: int, window_seconds: int) -> bool:
        """Set global rate limit"""
        return await self.limiter.set_rate_limit(max_requests, window_seconds)
    
    # ========================================================================
    # MANAGEMENT
    # ========================================================================
    
    async def add_listener(self, listener: ApiGatewayListener) -> bool:
        """Register gateway listener"""
        try:
            self.listeners.append(listener)
            self.router.add_listener(listener)
            self.limiter.add_listener(listener)
            return True
        except Exception:
            return False
    
    async def get_metrics(self) -> GatewayMetrics:
        """Get gateway metrics"""
        return self.limiter.metrics
    
    async def get_circuit_state(self, node_id: str):
        """Get circuit breaker state for node"""
        return self.limiter.get_circuit_state(node_id)
    
    async def is_enabled(self) -> bool:
        """Check if gateway is enabled"""
        return self.enabled
    
    async def _cleanup_loop(self) -> None:
        """Background loop for cleanup"""
        while self.enabled:
            try:
                # Clean up old request history
                await self.limiter.cleanup_old_history(hours=1)
                await asyncio.sleep(300)
            except Exception:
                await asyncio.sleep(300)
