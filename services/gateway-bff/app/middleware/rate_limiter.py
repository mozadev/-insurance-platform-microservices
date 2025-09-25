"""Rate limiting middleware."""

import time
from typing import Dict, Optional
from collections import defaultdict, deque

from fastapi import Request, HTTPException, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ...shared.logging import LoggerMixin


class RedisRateLimiter(LoggerMixin):
    """Redis-based rate limiter."""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._redis = None
    
    async def get_redis(self):
        """Get Redis connection."""
        if self._redis is None:
            import aioredis
            self._redis = await aioredis.from_url(self.redis_url)
        return self._redis
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed."""
        try:
            redis = await self.get_redis()
            
            # Use sliding window counter
            now = int(time.time())
            window_start = now - window
            
            # Remove old entries
            await redis.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_count = await redis.zcard(key)
            
            if current_count >= limit:
                return False
            
            # Add current request
            await redis.zadd(key, {str(now): now})
            await redis.expire(key, window)
            
            return True
            
        except Exception as e:
            self.logger.error("Rate limiter error", error=str(e))
            return True  # Allow on error


class MemoryRateLimiter(LoggerMixin):
    """In-memory rate limiter for development."""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed."""
        now = time.time()
        window_start = now - window
        
        # Get requests for this key
        requests = self.requests[key]
        
        # Remove old requests
        while requests and requests[0] < window_start:
            requests.popleft()
        
        # Check if under limit
        if len(requests) >= limit:
            return False
        
        # Add current request
        requests.append(now)
        
        return True


def create_rate_limiter(redis_url: Optional[str] = None) -> Limiter:
    """Create rate limiter instance."""
    if redis_url:
        # Use Redis-based limiter
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=redis_url
        )
    else:
        # Use in-memory limiter for development
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri="memory://"
        )
    
    return limiter


def create_rate_limit_exception_handler():
    """Create rate limit exception handler."""
    def handler(request: Request, exc: RateLimitExceeded):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {exc.detail}"
        )
    
    return handler
