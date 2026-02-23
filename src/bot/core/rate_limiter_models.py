"""
Rate Limiter Models
Data structures for rate limiting and token bucket algorithm
"""

from dataclasses import dataclass


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
