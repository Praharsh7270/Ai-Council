"""Rate limiting service using Redis."""
import time
from typing import Optional, Tuple

from redis.asyncio import Redis

from app.core.config import settings


class RateLimiter:
    """Rate limiter using Redis with sliding window algorithm."""

    def __init__(self, redis_client: Redis):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        self.authenticated_limit = settings.RATE_LIMIT_AUTHENTICATED
        self.demo_limit = settings.RATE_LIMIT_DEMO
        self.admin_limit = settings.RATE_LIMIT_ADMIN
        self.window_seconds = 3600  # 1 hour

    async def check_limit(
        self,
        identifier: str,
        is_demo: bool = False,
        is_admin: bool = False
    ) -> Tuple[bool, int, int]:
        """
        Check if the request is within rate limits using sliding window.
        
        Args:
            identifier: User ID for authenticated users, IP address for demo users
            is_demo: Whether this is a demo user (unauthenticated)
            is_admin: Whether this is an admin user
            
        Returns:
            Tuple of (is_allowed, remaining_requests, reset_at_timestamp)
            - is_allowed: True if request is within limits
            - remaining_requests: Number of requests remaining in current window
            - reset_at_timestamp: Unix timestamp when the limit resets
        """
        # Determine the rate limit based on user type
        if is_admin:
            limit = self.admin_limit
        elif is_demo:
            limit = self.demo_limit
        else:
            limit = self.authenticated_limit

        # Get current timestamp (in seconds)
        current_time = int(time.time())
        
        # Calculate the start of the current hour window
        window_start = current_time - (current_time % self.window_seconds)
        
        # Create Redis key for this user/IP and time window
        if is_demo:
            key = f"rate_limit:demo:{identifier}:hour:{window_start}"
        else:
            key = f"rate_limit:{identifier}:hour:{window_start}"

        # Get current count
        current_count = await self.redis.get(key)
        
        if current_count is None:
            current_count = 0
        else:
            current_count = int(current_count)

        # Calculate reset time (end of current hour window)
        reset_at = window_start + self.window_seconds

        # Check if limit is exceeded
        if current_count >= limit:
            remaining = 0
            is_allowed = False
        else:
            # Increment counter
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window_seconds)
            await pipe.execute()
            
            remaining = limit - current_count - 1
            is_allowed = True

        return is_allowed, remaining, reset_at

    async def get_current_usage(
        self,
        identifier: str,
        is_demo: bool = False
    ) -> Tuple[int, int]:
        """
        Get current usage for a user without incrementing the counter.
        
        Args:
            identifier: User ID for authenticated users, IP address for demo users
            is_demo: Whether this is a demo user
            
        Returns:
            Tuple of (current_count, reset_at_timestamp)
        """
        current_time = int(time.time())
        window_start = current_time - (current_time % self.window_seconds)
        
        if is_demo:
            key = f"rate_limit:demo:{identifier}:hour:{window_start}"
        else:
            key = f"rate_limit:{identifier}:hour:{window_start}"

        current_count = await self.redis.get(key)
        
        if current_count is None:
            current_count = 0
        else:
            current_count = int(current_count)

        reset_at = window_start + self.window_seconds
        
        return current_count, reset_at

    async def reset_limit(self, identifier: str, is_demo: bool = False) -> None:
        """
        Reset rate limit for a user (admin function).
        
        Args:
            identifier: User ID for authenticated users, IP address for demo users
            is_demo: Whether this is a demo user
        """
        current_time = int(time.time())
        window_start = current_time - (current_time % self.window_seconds)
        
        if is_demo:
            key = f"rate_limit:demo:{identifier}:hour:{window_start}"
        else:
            key = f"rate_limit:{identifier}:hour:{window_start}"

        await self.redis.delete(key)
