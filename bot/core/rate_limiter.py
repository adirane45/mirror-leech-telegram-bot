"""
Phase 4: Rate Limiter  
Token bucket-based rate limiting to protect against abuse
"""

import asyncio
import time
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_second: float = 10.0
    burst_size: int = 50
    window_size_seconds: int = 60


@dataclass
class RateLimitStatus:
    """Status of rate limit check"""
    allowed: bool
    remaining_tokens: float
    retry_after: float  # Seconds until allowed
    requests_in_window: int


class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(
        self,
        client_id: str,
        requests_per_second: float,
        burst_size: int
    ):
        self.client_id = client_id
        self.rps = requests_per_second
        self.burst_size = burst_size
        self.tokens = float(burst_size)
        self.max_tokens = float(burst_size)
        self.last_refill = time.time()
        self.request_count = 0
        self.blocked_count = 0

    def _refill(self) -> None:
        """
        Refill token bucket based on elapsed time (Token Bucket Algorithm).
        
        Tokens regenerate at a constant rate (requests_per_second).
        The bucket has a maximum capacity (burst_size) to allow short bursts.
        
        Example:
            If rps=10 and 2 seconds elapsed, add 20 tokens (up to max)
        """
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on request rate
        new_tokens = elapsed * self.rps
        self.tokens = min(self.max_tokens, self.tokens + new_tokens)
        self.last_refill = now

    def is_allowed(self, tokens_required: int = 1) -> Tuple[bool, float]:
        """
        Check if request is allowed
        
        Args:
            tokens_required: Tokens needed for this request
            
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        self._refill()
        
        if self.tokens >= tokens_required:
            self.tokens -= tokens_required
            self.request_count += 1
            return True, 0.0
        
        # Calculate when we'll have enough tokens
        needed = tokens_required - self.tokens
        retry_after = needed / self.rps if self.rps > 0 else 0.0
        self.blocked_count += 1
        return False, retry_after

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive bucket status for monitoring.
        
        Returns:
            Dictionary containing:
                - client_id: Client identifier
                - tokens_available: Current token count
                - max_tokens: Maximum burst capacity
                - rps: Requests per second rate limit
                - request_count: Total allowed requests
                - blocked_count: Total blocked requests
                - block_rate: Percentage of requests blocked
        """
        return {
            'client_id': self.client_id,
            'tokens_available': self.tokens,
            'max_tokens': self.max_tokens,
            'rps': self.rps,
            'request_count': self.request_count,
            'blocked_count': self.blocked_count,
            'block_rate': (
                self.blocked_count / (self.request_count + self.blocked_count) * 100
                if (self.request_count + self.blocked_count) > 0 else 0.0
            )
        }


class RateLimiter:
    """
    Singleton rate limiter using token bucket algorithm
    """

    _instance: Optional['RateLimiter'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.enabled = False
        self.buckets: Dict[str, TokenBucket] = {}
        self.default_config = RateLimitConfig()
        self.tier_configs: Dict[str, RateLimitConfig] = {}
        self.cleanup_interval = 3600  # 1 hour
        self.max_inactive_seconds = 1800  # 30 minutes
        self.last_cleanup = time.time()
        self.total_allowed = 0
        self.total_blocked = 0

    @classmethod
    def get_instance(cls) -> 'RateLimiter':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = RateLimiter()
        return cls._instance

    async def enable(self) -> bool:
        """
        Enable the Rate Limiter to protect against abuse.
        
        Once enabled, all requests are subject to rate limiting based
        on client_id and tier configuration.
        
        Returns:
            bool: True if successfully enabled
            
        Example:
            >>> limiter = RateLimiter.get_instance()
            >>> await limiter.enable()
            >>> is_allowed, status = await limiter.is_allowed('user123')
        """
        async with self._lock:
            self.enabled = True
            logger.info("Rate Limiter enabled")
            return True

    async def disable(self) -> bool:
        """Disable the Rate Limiter"""
        async with self._lock:
            self.enabled = False
            self.buckets.clear()
            logger.info("Rate Limiter disabled")
            return True

    def set_tier_limit(self, tier_name: str, config: RateLimitConfig) -> bool:
        """
        Set rate limit config for tier
        
        Args:
            tier_name: Tier identifier
            config: Rate limit configuration
            
        Returns:
            Success status
        """
        try:
            self.tier_configs[tier_name] = config
            logger.info(f"Set rate limit config for tier '{tier_name}': {config.requests_per_second} req/s")
            return True
        except Exception as e:
            logger.error(f"Error setting tier limit: {e}")
            return False

    async def is_allowed(
        self,
        client_id: str,
        config: Optional[RateLimitConfig] = None,
        tokens_required: int = 1
    ) -> Tuple[bool, RateLimitStatus]:
        """
        Check if request from client is allowed
        
        Args:
            client_id: Client identifier  
            config: Rate limit config (uses default if None)
            tokens_required: Tokens needed for this request
            
        Returns:
            Tuple of (allowed, RateLimitStatus)
        """
        if not self.enabled:
            status = RateLimitStatus(
                allowed=True,
                remaining_tokens=float(tokens_required),
                retry_after=0.0,
                requests_in_window=0
            )
            return True, status

        try:
            # Use provided config or default
            limit_config = config or self.default_config
            
            # Get or create bucket
            if client_id not in self.buckets:
                self.buckets[client_id] = TokenBucket(
                    client_id,
                    limit_config.requests_per_second,
                    limit_config.burst_size
                )
            
            bucket = self.buckets[client_id]
            
            # Check limit
            allowed, retry_after = bucket.is_allowed(tokens_required)
            
            # Update statistics
            if allowed:
                self.total_allowed += 1
            else:
                self.total_blocked += 1
            
            status = RateLimitStatus(
                allowed=allowed,
                remaining_tokens=bucket.tokens,
                retry_after=retry_after,
                requests_in_window=bucket.request_count
            )
            
            # Log if blocked
            if not allowed:
                logger.warning(f"Rate limit blocked for client {client_id} (retry after {retry_after:.1f}s)")
            
            # Cleanup inactive buckets if needed
            if time.time() - self.last_cleanup > self.cleanup_interval:
                await self._cleanup_inactive_buckets()
            
            return allowed, status
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Allow on error
            status = RateLimitStatus(
                allowed=True,
                remaining_tokens=0.0,
                retry_after=0.0,
                requests_in_window=0
            )
            return True, status

    async def _cleanup_inactive_buckets(self) -> None:
        """Remove buckets for inactive clients"""
        try:
            current_time = time.time()
            buckets_to_remove = []
            
            for client_id, bucket in self.buckets.items():
                last_request_time = bucket.last_refill
                inactivity = current_time - last_request_time
                
                if inactivity > self.max_inactive_seconds and bucket.request_count == 0:
                    buckets_to_remove.append(client_id)
            
            for client_id in buckets_to_remove:
                del self.buckets[client_id]
            
            if buckets_to_remove:
                logger.info(f"Cleaned up {len(buckets_to_remove)} inactive rate limit buckets")
            
            self.last_cleanup = current_time
        except Exception as e:
            logger.error(f"Error cleaning up buckets: {e}")

    async def reset_client(self, client_id: str) -> bool:
        """
        Reset rate limit for specific client
        
        Args:
            client_id: Client identifier
            
        Returns:
            Success status
        """
        try:
            if client_id in self.buckets:
                del self.buckets[client_id]
                logger.info(f"Reset rate limit for client {client_id}")
            return True
        except Exception as e:
            logger.error(f"Error resetting client limit: {e}")
            return False

    async def get_client_status(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific client's rate limit"""
        if client_id in self.buckets:
            return self.buckets[client_id].get_status()
        return None

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall rate limiter statistics"""
        total_requests = self.total_allowed + self.total_blocked
        block_rate = (
            self.total_blocked / total_requests * 100
            if total_requests > 0 else 0.0
        )
        
        return {
            'enabled': self.enabled,
            'active_clients': len(self.buckets),
            'total_allowed': self.total_allowed,
            'total_blocked': self.total_blocked,
            'total_requests': total_requests,
            'block_rate_percent': block_rate,
            'tiers_configured': len(self.tier_configs),
        }

    async def get_all_client_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all tracked clients"""
        return {
            client_id: bucket.get_status()
            for client_id, bucket in self.buckets.items()
        }
