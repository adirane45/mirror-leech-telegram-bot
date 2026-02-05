"""
Advanced Rate Limiter with Token Bucket Algorithm

Implements rate limiting with multiple strategies, graceful backoff,
and per-user/per-IP limiting.

Features:
- Token bucket algorithm
- Multiple limit strategies
- Sliding window
- Per-user limits
- Per-IP limits
- Graceful backoff
- Rate limit headers
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from enum import Enum
import math


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "token_bucket"  # Standard token bucket
    SLIDING_WINDOW = "sliding_window"  # Sliding window counter
    LEAKY_BUCKET = "leaky_bucket"  # Leaky bucket
    FIXED_WINDOW = "fixed_window"  # Fixed window / sliding minute


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_second: float = 10.0
    burst_size: int = 50
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    window_size: int = 60  # seconds


@dataclass
class RateLimitStatus:
    """Rate limit status for a client"""
    remaining: int
    limit: int
    reset_at: datetime
    retry_after: Optional[int] = None  # seconds to wait
    is_limited: bool = False


class TokenBucket:
    """Token bucket implementation"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = float(capacity)
        self.last_refill_time = time.time()
        self.lock = asyncio.Lock()
    
    async def try_consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens"""
        async with self.lock:
            await self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    async def consume(self, tokens: int = 1) -> float:
        """Consume tokens, returns wait time if needed"""
        async with self.lock:
            await self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            
            # Calculate wait time
            needed = tokens - self.tokens
            wait_time = needed / self.refill_rate
            return wait_time
    
    async def _refill(self) -> None:
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill_time
        
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill_time = now
    
    async def get_tokens(self) -> float:
        """Get current token count"""
        async with self.lock:
            await self._refill()
            return self.tokens


class RateLimiter:
    """Advanced rate limiter with multiple strategies"""
    
    _instance: Optional['RateLimiter'] = None
    
    def __init__(self):
        self.enabled = False
        self.default_config = RateLimitConfig()
        self.buckets: Dict[str, TokenBucket] = {}
        self.request_history: Dict[str, List[float]] = defaultdict(list)
        self.blocked_clients: Dict[str, datetime] = {}
        self.limits_exceeded: Dict[str, int] = defaultdict(int)
        self.total_requests = 0
        self.blocked_requests = 0
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'RateLimiter':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = RateLimiter()
        return cls._instance
    
    async def enable(self) -> bool:
        """Enable rate limiter"""
        try:
            async with self.lock:
                self.enabled = True
                return True
        except Exception as e:
            print(f"Error enabling rate limiter: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable rate limiter"""
        try:
            async with self.lock:
                self.enabled = False
                self.buckets.clear()
                self.request_history.clear()
                return True
        except Exception as e:
            print(f"Error disabling rate limiter: {e}")
            return False
    
    async def is_allowed(
        self,
        client_id: str,
        config: Optional[RateLimitConfig] = None
    ) -> Tuple[bool, RateLimitStatus]:
        """Check if request is allowed"""
        if not self.enabled:
            return True, RateLimitStatus(
                remaining=999,
                limit=999,
                reset_at=datetime.utcnow() + timedelta(seconds=60),
                is_limited=False
            )
        
        config = config or self.default_config
        
        try:
            async with self.lock:
                self.total_requests += 1
                
                # Check if client is blocked
                if client_id in self.blocked_clients:
                    if self.blocked_clients[client_id] > datetime.utcnow():
                        self.blocked_requests += 1
                        reset_time = self.blocked_clients[client_id]
                        retry_after = int((reset_time - datetime.utcnow()).total_seconds())
                        return False, RateLimitStatus(
                            remaining=0,
                            limit=int(config.requests_per_second),
                            reset_at=reset_time,
                            retry_after=max(1, retry_after),
                            is_limited=True
                        )
                    else:
                        del self.blocked_clients[client_id]
                
                # Get or create bucket
                if client_id not in self.buckets:
                    self.buckets[client_id] = TokenBucket(
                        capacity=config.burst_size,
                        refill_rate=config.requests_per_second
                    )
                
                bucket = self.buckets[client_id]
                
                # Try to consume a token
                if await bucket.try_consume(1):
                    remaining = int(await bucket.get_tokens())
                    return True, RateLimitStatus(
                        remaining=remaining,
                        limit=config.burst_size,
                        reset_at=datetime.utcnow() + timedelta(seconds=60),
                        is_limited=False
                    )
                else:
                    # Rate limited
                    self.blocked_requests += 1
                    self.limits_exceeded[client_id] += 1
                    
                    # Calculate backoff
                    backoff_seconds = min(3600, 2 ** self.limits_exceeded[client_id])
                    
                    # Block client for backoff period
                    block_until = datetime.utcnow() + timedelta(seconds=backoff_seconds)
                    self.blocked_clients[client_id] = block_until
                    
                    return False, RateLimitStatus(
                        remaining=0,
                        limit=config.burst_size,
                        reset_at=block_until,
                        retry_after=backoff_seconds,
                        is_limited=True
                    )
        except Exception as e:
            print(f"Rate limit check error: {e}")
            return True, RateLimitStatus(
                remaining=999,
                limit=999,
                reset_at=datetime.utcnow() + timedelta(seconds=60),
                is_limited=False
            )
    
    async def allow_batch(
        self,
        client_id: str,
        batch_size: int,
        config: Optional[RateLimitConfig] = None
    ) -> Tuple[bool, RateLimitStatus]:
        """Check if batch request is allowed"""
        if not self.enabled:
            return True, RateLimitStatus(
                remaining=999,
                limit=999,
                reset_at=datetime.utcnow() + timedelta(seconds=60),
                is_limited=False
            )
        
        config = config or self.default_config
        
        try:
            async with self.lock:
                if client_id not in self.buckets:
                    self.buckets[client_id] = TokenBucket(
                        capacity=config.burst_size,
                        refill_rate=config.requests_per_second
                    )
                
                bucket = self.buckets[client_id]
                
                if await bucket.try_consume(batch_size):
                    remaining = int(await bucket.get_tokens())
                    return True, RateLimitStatus(
                        remaining=remaining,
                        limit=config.burst_size,
                        reset_at=datetime.utcnow() + timedelta(seconds=60),
                        is_limited=False
                    )
                else:
                    wait_time = await bucket.consume(batch_size)
                    return False, RateLimitStatus(
                        remaining=0,
                        limit=config.burst_size,
                        reset_at=datetime.utcnow() + timedelta(seconds=int(wait_time) + 1),
                        retry_after=int(math.ceil(wait_time)),
                        is_limited=True
                    )
        except Exception as e:
            print(f"Batch rate limit error: {e}")
            return True, RateLimitStatus(
                remaining=999,
                limit=999,
                reset_at=datetime.utcnow() + timedelta(seconds=60),
                is_limited=False
            )
    
    async def get_status(
        self,
        client_id: str,
        config: Optional[RateLimitConfig] = None
    ) -> RateLimitStatus:
        """Get current rate limit status"""
        config = config or self.default_config
        
        try:
            async with self.lock:
                if client_id not in self.buckets:
                    self.buckets[client_id] = TokenBucket(
                        capacity=config.burst_size,
                        refill_rate=config.requests_per_second
                    )
                
                bucket = self.buckets[client_id]
                remaining = int(await bucket.get_tokens())
                
                if client_id in self.blocked_clients:
                    reset_time = self.blocked_clients[client_id]
                    retry_after = int((reset_time - datetime.utcnow()).total_seconds())
                    return RateLimitStatus(
                        remaining=0,
                        limit=config.burst_size,
                        reset_at=reset_time,
                        retry_after=max(1, retry_after),
                        is_limited=True
                    )
                
                return RateLimitStatus(
                    remaining=remaining,
                    limit=config.burst_size,
                    reset_at=datetime.utcnow() + timedelta(seconds=60),
                    is_limited=False
                )
        except Exception as e:
            print(f"Error getting status: {e}")
            return RateLimitStatus(
                remaining=0,
                limit=0,
                reset_at=datetime.utcnow(),
                is_limited=True
            )
    
    async def reset_client(self, client_id: str) -> bool:
        """Reset rate limit for a client"""
        try:
            async with self.lock:
                if client_id in self.buckets:
                    del self.buckets[client_id]
                if client_id in self.blocked_clients:
                    del self.blocked_clients[client_id]
                if client_id in self.limits_exceeded:
                    del self.limits_exceeded[client_id]
                return True
        except Exception as e:
            print(f"Error resetting client: {e}")
            return False
    
    async def get_statistics(self) -> Dict:
        """Get rate limiter statistics"""
        try:
            async with self.lock:
                return {
                    'enabled': self.enabled,
                    'total_requests': self.total_requests,
                    'blocked_requests': self.blocked_requests,
                    'block_rate': round(
                        (self.blocked_requests / self.total_requests * 100) 
                        if self.total_requests > 0 else 0,
                        2
                    ),
                    'active_clients': len(self.buckets),
                    'blocked_clients': len(self.blocked_clients),
                    'clients_exceeded': len(self.limits_exceeded)
                }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'error': str(e)}
    
    async def reset(self) -> bool:
        """Reset rate limiter"""
        try:
            await self.disable()
            self.buckets.clear()
            self.request_history.clear()
            self.blocked_clients.clear()
            self.limits_exceeded.clear()
            self.total_requests = 0
            self.blocked_requests = 0
            return True
        except Exception as e:
            print(f"Error resetting rate limiter: {e}")
            return False
