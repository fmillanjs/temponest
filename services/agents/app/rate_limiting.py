"""
Rate Limiting Middleware for Agent Service
"""
import time
from typing import Dict, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis
from datetime import datetime, timedelta


class RateLimiter:
    """
    Token bucket rate limiter using Redis

    Supports multiple rate limit tiers and per-tenant/per-user limits
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_rate: int = 100,  # requests
        default_period: int = 60,  # seconds
    ):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.default_rate = default_rate
        self.default_period = default_period

        # Rate limit tiers
        self.tiers = {
            "free": {"rate": 10, "period": 60},  # 10 req/min
            "basic": {"rate": 50, "period": 60},  # 50 req/min
            "pro": {"rate": 200, "period": 60},  # 200 req/min
            "enterprise": {"rate": 1000, "period": 60},  # 1000 req/min
        }

    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate Redis key for rate limit tracking"""
        return f"ratelimit:{identifier}:{endpoint}"

    def _get_tier_limits(self, tier: str) -> Dict[str, int]:
        """Get rate limits for a specific tier"""
        return self.tiers.get(tier, {
            "rate": self.default_rate,
            "period": self.default_period
        })

    def is_allowed(
        self,
        identifier: str,
        endpoint: str,
        tier: str = "basic",
    ) -> tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed under rate limit

        Args:
            identifier: Unique identifier (user_id, tenant_id, API key)
            endpoint: Endpoint being accessed
            tier: Rate limit tier

        Returns:
            Tuple of (allowed, info) where info contains:
            - remaining: Requests remaining
            - reset: Unix timestamp when limit resets
            - retry_after: Seconds to wait before retry (if not allowed)
        """
        limits = self._get_tier_limits(tier)
        rate = limits["rate"]
        period = limits["period"]

        key = self._get_key(identifier, endpoint)
        now = time.time()

        # Get current window
        pipe = self.redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, now - period)  # Remove old entries
        pipe.zcard(key)  # Count current entries
        pipe.zadd(key, {str(now): now})  # Add current request
        pipe.expire(key, period)  # Set expiration

        results = pipe.execute()
        current_count = results[1]

        if current_count >= rate:
            # Rate limit exceeded
            oldest_entry = self.redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_entry:
                oldest_time = oldest_entry[0][1]
                retry_after = int(period - (now - oldest_time))
            else:
                retry_after = period

            return False, {
                "remaining": 0,
                "reset": int(now + retry_after),
                "retry_after": retry_after,
                "limit": rate,
                "period": period,
            }

        # Request allowed
        remaining = rate - current_count - 1
        reset = int(now + period)

        return True, {
            "remaining": remaining,
            "reset": reset,
            "limit": rate,
            "period": period,
        }

    def get_usage(self, identifier: str, endpoint: str) -> Dict[str, any]:
        """Get current usage statistics"""
        key = self._get_key(identifier, endpoint)
        now = time.time()

        # Clean old entries
        self.redis_client.zremrangebyscore(key, 0, now - self.default_period)

        count = self.redis_client.zcard(key)
        ttl = self.redis_client.ttl(key)

        return {
            "count": count,
            "limit": self.default_rate,
            "ttl": ttl,
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting

    Adds rate limit headers to all responses and enforces limits
    """

    def __init__(
        self,
        app,
        rate_limiter: RateLimiter,
        exempt_paths: Optional[list] = None,
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json"]

    def _get_identifier(self, request: Request) -> str:
        """
        Get identifier for rate limiting

        Priority:
        1. Tenant ID from auth
        2. User ID from auth
        3. API Key
        4. IP Address
        """
        # Check for tenant_id in request state (from auth middleware)
        if hasattr(request.state, "tenant_id"):
            return f"tenant:{request.state.tenant_id}"

        # Check for user_id
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"

        # Check for API key in headers
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key}"

        # Fall back to IP address
        client_ip = request.client.host
        return f"ip:{client_ip}"

    def _get_tier(self, request: Request) -> str:
        """Get rate limit tier for request"""
        # Check request state for tier (from auth/subscription middleware)
        if hasattr(request.state, "rate_limit_tier"):
            return request.state.rate_limit_tier

        # Default to basic tier
        return "basic"

    def _should_exempt(self, path: str) -> bool:
        """Check if path should be exempt from rate limiting"""
        return any(path.startswith(exempt) for exempt in self.exempt_paths)

    async def dispatch(self, request: Request, call_next):
        """Process request and enforce rate limits"""
        path = request.url.path

        # Skip rate limiting for exempt paths
        if self._should_exempt(path):
            return await call_next(request)

        # Get identifier and tier
        identifier = self._get_identifier(request)
        tier = self._get_tier(request)
        endpoint = f"{request.method}:{path}"

        # Check rate limit
        allowed, info = self.rate_limiter.is_allowed(identifier, endpoint, tier)

        # Add rate limit headers
        headers = {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info.get("remaining", 0)),
            "X-RateLimit-Reset": str(info["reset"]),
        }

        if not allowed:
            # Rate limit exceeded
            headers["Retry-After"] = str(info["retry_after"])

            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                headers=headers,
                media_type="application/json",
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        for key, value in headers.items():
            response.headers[key] = value

        return response


# Usage in FastAPI app:
# from rate_limiting import RateLimiter, RateLimitMiddleware
#
# rate_limiter = RateLimiter(redis_url=settings.REDIS_URL)
# app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
