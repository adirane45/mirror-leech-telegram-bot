"""
API Gateway Rate Limiter and Circuit Breaker

Implements:
- Rate limiting enforcement
- Circuit breaker pattern
- Request throttling
- Node health tracking
"""

import asyncio
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional

from .api_gateway_models import (
    CircuitState,
    RateLimitConfig,
    CircuitBreakerConfig,
    GatewayMetrics,
    ApiGatewayListener,
)


class ApiGatewayLimiter:
    """
    Manages rate limiting and circuit breaker logic
    
    Responsible for:
    - Rate limit enforcement per client
    - Circuit breaker state management
    - Node health tracking
    - Background recovery checks
    """
    
    def __init__(self):
        self.request_history: Dict[str, List[datetime]] = {}
        self.circuit_states: Dict[str, CircuitState] = {}
        self.circuit_failures: Dict[str, int] = {}
        self.circuit_successes: Dict[str, int] = {}
        self.listeners: List[ApiGatewayListener] = []
        self.metrics = GatewayMetrics()
        self.enabled = False
        
        self.default_rate_limit = RateLimitConfig()
        self.default_circuit_breaker = CircuitBreakerConfig()
        
        self._circuit_check_task: Optional[asyncio.Task] = None
    
    async def check_rate_limit(self, client_id: str) -> bool:
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
    
    async def check_circuit(self, node_id: str) -> bool:
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
    
    async def record_failure(self, node_id: str) -> None:
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
    
    async def record_success(self, node_id: str) -> None:
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
    
    async def circuit_check_loop(self) -> None:
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
    
    def get_circuit_state(self, node_id: str) -> CircuitState:
        """Get circuit breaker state for node"""
        return self.circuit_states.get(node_id, CircuitState.CLOSED)
    
    def set_enabled(self, enabled: bool) -> None:
        """Set limiter enabled state"""
        self.enabled = enabled
    
    def initialize_node(self, node_id: str) -> None:
        """Initialize circuit state for node"""
        self.circuit_states[node_id] = CircuitState.CLOSED
        self.circuit_failures[node_id] = 0
        self.circuit_successes[node_id] = 0
    
    def add_listener(self, listener: ApiGatewayListener) -> None:
        """Add limiter listener"""
        if listener not in self.listeners:
            self.listeners.append(listener)
    
    async def cleanup_old_history(self, hours: int = 1) -> None:
        """Clean up old request history"""
        try:
            cutoff = datetime.now(UTC) - timedelta(hours=hours)
            for client_id in list(self.request_history.keys()):
                self.request_history[client_id] = [
                    ts for ts in self.request_history[client_id]
                    if ts > cutoff
                ]
                
                # Remove empty histories
                if not self.request_history[client_id]:
                    del self.request_history[client_id]
            
            self.metrics.last_updated = datetime.now(UTC)
        except Exception:
            pass
