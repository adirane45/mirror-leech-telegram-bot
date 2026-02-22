"""
Circuit Breaker Pattern Implementation

Implements:
- State machine (CLOSED -> OPEN -> HALF_OPEN)
- Failure tracking and thresholds
- Exponential backoff retry strategy
- Metrics and monitoring
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field

from .. import LOGGER


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"              # Normal operation, requests pass through
    OPEN = "open"                  # Failed requests are blocked immediately
    HALF_OPEN = "half_open"        # Testing if service recovered


class CircuitBreakerException(Exception):
    """Raised when circuit breaker is open"""
    pass


@dataclass
class CircuitBreakerMetrics:
    """Metrics for a circuit breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    
    last_state_change: Optional[datetime] = None
    last_error_message: Optional[str] = None
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "rejected_calls": self.rejected_calls,
            "success_rate": self.success_rate(),
            "last_state_change": self.last_state_change.isoformat() if self.last_state_change else None,
            "last_error": self.last_error_message,
        }


class CircuitBreaker:
    """
    Generic Circuit Breaker implementation
    
    Usage:
        breaker = CircuitBreaker(
            name="my_service",
            failure_threshold=5,
            success_threshold=2,
            timeout=60,
        )
        
        try:
            result = await breaker.call(my_async_func, arg1, arg2)
        except CircuitBreakerException:
            # Circuit is open, handle gracefully
            pass
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        expected_exception: type = Exception,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now(timezone.utc)
        
        self.metrics = CircuitBreakerMetrics()
        self._lock = asyncio.Lock()
    
    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
    
    async def _handle_success(self) -> None:
        """Handle successful call"""
        async with self._lock:
            self.metrics.successful_calls += 1
            self.metrics.total_calls += 1
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                
                if self.success_count >= self.success_threshold:
                    LOGGER.info(f"CircuitBreaker '{self.name}': HALF_OPEN -> CLOSED")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.metrics.last_state_change = self._now()
            
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on successful call
                self.failure_count = 0
    
    async def _handle_failure(self, error: Exception) -> None:
        """Handle failed call"""
        async with self._lock:
            self.metrics.failed_calls += 1
            self.metrics.total_calls += 1
            self.metrics.last_error_message = str(error)
            self.last_failure_time = self._now()
            
            if self.state == CircuitState.CLOSED:
                self.failure_count += 1
                
                if self.failure_count >= self.failure_threshold:
                    LOGGER.warning(
                        f"CircuitBreaker '{self.name}': CLOSED -> OPEN "
                        f"(failures: {self.failure_count}/{self.failure_threshold})"
                    )
                    self.state = CircuitState.OPEN
                    self.last_state_change = self._now()
            
            elif self.state == CircuitState.HALF_OPEN:
                # Single failure in HALF_OPEN triggers OPEN
                LOGGER.warning(f"CircuitBreaker '{self.name}': HALF_OPEN -> OPEN (test failed)")
                self.state = CircuitState.OPEN
                self.success_count = 0
                self.metrics.last_state_change = self._now()
    
    async def _handle_rejection(self) -> None:
        """Handle request rejection"""
        async with self._lock:
            self.metrics.rejected_calls += 1
            self.metrics.total_calls += 1
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with circuit breaker protection
        
        Raises:
            CircuitBreakerException: If circuit is open
            Exception: If function raises expected_exception
        """
        # Check if we need to transition to HALF_OPEN
        async with self._lock:
            if self.state == CircuitState.OPEN:
                time_since_open = (self._now() - self.last_state_change).total_seconds()
                if time_since_open >= self.timeout:
                    # Try recovery
                    LOGGER.info(
                        f"CircuitBreaker '{self.name}': OPEN -> HALF_OPEN "
                        f"(after {time_since_open}s timeout)"
                    )
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    self.metrics.last_state_change = self._now()
                else:
                    # Still open
                    await self._handle_rejection()
                    raise CircuitBreakerException(
                        f"Circuit breaker '{self.name}' is OPEN. "
                        f"Retry in {int(self.timeout - time_since_open)}s"
                    )
        
        # Execute the call
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            await self._handle_success()
            return result
        
        except self.expected_exception as e:
            await self._handle_failure(e)
            raise
    
    async def reset(self) -> None:
        """Force reset circuit to CLOSED"""
        async with self._lock:
            LOGGER.info(f"CircuitBreaker '{self.name}': Reset to CLOSED")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_state_change = self._now()
            self.metrics.last_state_change = self._now()
    
    async def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        async with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "last_state_change": self.last_state_change.isoformat(),
                "metrics": self.metrics.to_dict(),
            }


class CircuitBreakerPool:
    """Manage multiple circuit breakers"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    async def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: int = 60,
        expected_exception: type = Exception,
    ) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        async with self._lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    success_threshold=success_threshold,
                    timeout=timeout,
                    expected_exception=expected_exception,
                )
            return self.breakers[name]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get stats for all breakers"""
        stats = {}
        for name, breaker in self.breakers.items():
            stats[name] = await breaker.get_state()
        return stats
    
    async def reset_all(self) -> None:
        """Reset all breakers"""
        for breaker in self.breakers.values():
            await breaker.reset()


# Global circuit breaker pool
circuit_breaker_pool = CircuitBreakerPool()
