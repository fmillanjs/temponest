"""
Tests for Rate Limiting Middleware
"""

import time
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi import Request, status
from fastapi.testclient import TestClient
from starlette.responses import Response

from app.rate_limiting import RateLimiter, RateLimitMiddleware


class TestRateLimiter:
    """Test RateLimiter class"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        mock = MagicMock()
        mock.from_url.return_value = mock

        # Mock pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 0, None, None]  # current_count = 0
        mock.pipeline.return_value = mock_pipeline

        # Mock other operations
        mock.zcard.return_value = 0
        mock.ttl.return_value = 60
        mock.zrange.return_value = []
        mock.zremrangebyscore.return_value = None

        return mock

    @pytest.fixture
    def rate_limiter(self, mock_redis):
        """Create RateLimiter instance with mocked Redis"""
        with patch('app.rate_limiting.redis.from_url', return_value=mock_redis):
            limiter = RateLimiter(
                redis_url="redis://localhost:6379",
                default_rate=100,
                default_period=60
            )
            limiter.redis_client = mock_redis
            return limiter

    def test_init_default_values(self, mock_redis):
        """Test RateLimiter initialization with defaults"""
        with patch('app.rate_limiting.redis.from_url', return_value=mock_redis):
            limiter = RateLimiter()
            assert limiter.default_rate == 100
            assert limiter.default_period == 60
            assert "free" in limiter.tiers
            assert "basic" in limiter.tiers
            assert "pro" in limiter.tiers
            assert "enterprise" in limiter.tiers

    def test_init_custom_values(self, mock_redis):
        """Test RateLimiter initialization with custom values"""
        with patch('app.rate_limiting.redis.from_url', return_value=mock_redis):
            limiter = RateLimiter(
                redis_url="redis://custom:6379",
                default_rate=50,
                default_period=30
            )
            assert limiter.default_rate == 50
            assert limiter.default_period == 30

    def test_get_key(self, rate_limiter):
        """Test Redis key generation"""
        key = rate_limiter._get_key("user123", "/api/agents")
        assert key == "ratelimit:user123:/api/agents"

        key = rate_limiter._get_key("tenant:abc", "POST:/api/execute")
        assert key == "ratelimit:tenant:abc:POST:/api/execute"

    def test_get_tier_limits_free(self, rate_limiter):
        """Test getting free tier limits"""
        limits = rate_limiter._get_tier_limits("free")
        assert limits["rate"] == 10
        assert limits["period"] == 60

    def test_get_tier_limits_basic(self, rate_limiter):
        """Test getting basic tier limits"""
        limits = rate_limiter._get_tier_limits("basic")
        assert limits["rate"] == 50
        assert limits["period"] == 60

    def test_get_tier_limits_pro(self, rate_limiter):
        """Test getting pro tier limits"""
        limits = rate_limiter._get_tier_limits("pro")
        assert limits["rate"] == 200
        assert limits["period"] == 60

    def test_get_tier_limits_enterprise(self, rate_limiter):
        """Test getting enterprise tier limits"""
        limits = rate_limiter._get_tier_limits("enterprise")
        assert limits["rate"] == 1000
        assert limits["period"] == 60

    def test_get_tier_limits_unknown_uses_default(self, rate_limiter):
        """Test that unknown tier uses default limits"""
        limits = rate_limiter._get_tier_limits("unknown_tier")
        assert limits["rate"] == rate_limiter.default_rate
        assert limits["period"] == rate_limiter.default_period

    def test_is_allowed_within_limit(self, rate_limiter, mock_redis):
        """Test request allowed when within rate limit"""
        # Mock pipeline to return count = 5 (within limit of 50 for basic tier)
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 5, None, None]
        mock_redis.pipeline.return_value = mock_pipeline

        allowed, info = rate_limiter.is_allowed("user123", "/api/agents", "basic")

        assert allowed is True
        assert info["remaining"] == 44  # 50 - 5 - 1
        assert "reset" in info
        assert info["limit"] == 50
        assert info["period"] == 60

    def test_is_allowed_exceeded_limit(self, rate_limiter, mock_redis):
        """Test request denied when rate limit exceeded"""
        # Mock pipeline to return count = 50 (at limit for basic tier)
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 50, None, None]
        mock_redis.pipeline.return_value = mock_pipeline

        # Mock zrange for retry_after calculation
        mock_redis.zrange.return_value = [("1234567890", 1234567890.0)]

        allowed, info = rate_limiter.is_allowed("user123", "/api/agents", "basic")

        assert allowed is False
        assert info["remaining"] == 0
        assert "retry_after" in info
        assert info["limit"] == 50
        assert info["period"] == 60

    def test_is_allowed_free_tier(self, rate_limiter, mock_redis):
        """Test rate limiting for free tier"""
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 2, None, None]
        mock_redis.pipeline.return_value = mock_pipeline

        allowed, info = rate_limiter.is_allowed("user123", "/api/agents", "free")

        assert allowed is True
        assert info["limit"] == 10
        assert info["remaining"] == 7  # 10 - 2 - 1

    def test_is_allowed_pro_tier(self, rate_limiter, mock_redis):
        """Test rate limiting for pro tier"""
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 50, None, None]
        mock_redis.pipeline.return_value = mock_pipeline

        allowed, info = rate_limiter.is_allowed("user123", "/api/agents", "pro")

        assert allowed is True
        assert info["limit"] == 200
        assert info["remaining"] == 149  # 200 - 50 - 1

    def test_is_allowed_enterprise_tier(self, rate_limiter, mock_redis):
        """Test rate limiting for enterprise tier"""
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 100, None, None]
        mock_redis.pipeline.return_value = mock_pipeline

        allowed, info = rate_limiter.is_allowed("user123", "/api/agents", "enterprise")

        assert allowed is True
        assert info["limit"] == 1000
        assert info["remaining"] == 899  # 1000 - 100 - 1

    def test_is_allowed_at_exact_limit(self, rate_limiter, mock_redis):
        """Test when current count equals the rate limit"""
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 50, None, None]
        mock_redis.pipeline.return_value = mock_pipeline
        mock_redis.zrange.return_value = [("1234567890", time.time() - 30)]

        allowed, info = rate_limiter.is_allowed("user123", "/api/agents", "basic")

        assert allowed is False
        assert info["remaining"] == 0

    def test_is_allowed_different_identifiers(self, rate_limiter, mock_redis):
        """Test that different identifiers have separate limits"""
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 5, None, None]
        mock_redis.pipeline.return_value = mock_pipeline

        allowed1, info1 = rate_limiter.is_allowed("user1", "/api/agents", "basic")
        allowed2, info2 = rate_limiter.is_allowed("user2", "/api/agents", "basic")

        assert allowed1 is True
        assert allowed2 is True

    def test_is_allowed_different_endpoints(self, rate_limiter, mock_redis):
        """Test that different endpoints have separate limits"""
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 5, None, None]
        mock_redis.pipeline.return_value = mock_pipeline

        allowed1, info1 = rate_limiter.is_allowed("user1", "/api/agents", "basic")
        allowed2, info2 = rate_limiter.is_allowed("user1", "/api/execute", "basic")

        assert allowed1 is True
        assert allowed2 is True

    def test_is_allowed_retry_after_calculation(self, rate_limiter, mock_redis):
        """Test retry_after calculation when limit exceeded"""
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 50, None, None]
        mock_redis.pipeline.return_value = mock_pipeline

        oldest_time = time.time() - 30  # 30 seconds ago
        mock_redis.zrange.return_value = [("entry", oldest_time)]

        allowed, info = rate_limiter.is_allowed("user123", "/api/agents", "basic")

        assert allowed is False
        assert "retry_after" in info
        assert info["retry_after"] >= 29  # Should be around 30 seconds

    def test_is_allowed_retry_after_no_oldest_entry(self, rate_limiter, mock_redis):
        """Test retry_after when no oldest entry exists"""
        mock_pipeline = MagicMock()
        mock_pipeline.execute.return_value = [None, 50, None, None]
        mock_redis.pipeline.return_value = mock_pipeline

        mock_redis.zrange.return_value = []  # No oldest entry

        allowed, info = rate_limiter.is_allowed("user123", "/api/agents", "basic")

        assert allowed is False
        assert info["retry_after"] == 60  # Should use period as retry_after

    def test_get_usage(self, rate_limiter, mock_redis):
        """Test getting current usage statistics"""
        mock_redis.zcard.return_value = 25
        mock_redis.ttl.return_value = 45

        usage = rate_limiter.get_usage("user123", "/api/agents")

        assert usage["count"] == 25
        assert usage["limit"] == 100  # default_rate
        assert usage["ttl"] == 45

    def test_get_usage_zero_count(self, rate_limiter, mock_redis):
        """Test usage when no requests made"""
        mock_redis.zcard.return_value = 0
        mock_redis.ttl.return_value = 60

        usage = rate_limiter.get_usage("user123", "/api/agents")

        assert usage["count"] == 0
        assert usage["limit"] == 100

    def test_get_usage_calls_cleanup(self, rate_limiter, mock_redis):
        """Test that get_usage cleans up old entries"""
        mock_redis.zcard.return_value = 10
        mock_redis.ttl.return_value = 30

        rate_limiter.get_usage("user123", "/api/agents")

        # Verify zremrangebyscore was called to clean old entries
        mock_redis.zremrangebyscore.assert_called()


class TestRateLimitMiddleware:
    """Test RateLimitMiddleware class"""

    @pytest.fixture
    def mock_rate_limiter(self):
        """Mock RateLimiter"""
        limiter = Mock()
        limiter.is_allowed.return_value = (True, {
            "remaining": 45,
            "reset": int(time.time() + 60),
            "limit": 50,
            "period": 60
        })
        return limiter

    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI app"""
        return Mock()

    @pytest.fixture
    def middleware(self, mock_app, mock_rate_limiter):
        """Create RateLimitMiddleware instance"""
        return RateLimitMiddleware(
            app=mock_app,
            rate_limiter=mock_rate_limiter,
            exempt_paths=["/health", "/docs", "/openapi.json"]
        )

    def test_init_default_exempt_paths(self, mock_app, mock_rate_limiter):
        """Test middleware initialization with default exempt paths"""
        middleware = RateLimitMiddleware(mock_app, mock_rate_limiter)
        assert "/health" in middleware.exempt_paths
        assert "/docs" in middleware.exempt_paths
        assert "/openapi.json" in middleware.exempt_paths

    def test_init_custom_exempt_paths(self, mock_app, mock_rate_limiter):
        """Test middleware initialization with custom exempt paths"""
        middleware = RateLimitMiddleware(
            mock_app,
            mock_rate_limiter,
            exempt_paths=["/custom", "/metrics"]
        )
        assert "/custom" in middleware.exempt_paths
        assert "/metrics" in middleware.exempt_paths

    def test_get_identifier_tenant_id(self, middleware):
        """Test identifier extraction from tenant_id"""
        request = Mock()
        request.state.tenant_id = "tenant123"

        identifier = middleware._get_identifier(request)
        assert identifier == "tenant:tenant123"

    def test_get_identifier_user_id(self, middleware):
        """Test identifier extraction from user_id when no tenant_id"""
        request = Mock()
        request.state.user_id = "user456"
        # Simulate no tenant_id attribute
        del request.state.tenant_id

        identifier = middleware._get_identifier(request)
        assert identifier == "user:user456"

    def test_get_identifier_api_key(self, middleware):
        """Test identifier extraction from API key when no auth"""
        request = Mock()
        # Simulate no state attributes
        request.state = Mock(spec=[])
        request.headers.get.return_value = "api-key-789"

        identifier = middleware._get_identifier(request)
        assert identifier == "key:api-key-789"

    def test_get_identifier_ip_address(self, middleware):
        """Test identifier extraction from IP when no other identifiers"""
        request = Mock()
        # Simulate no state attributes
        request.state = Mock(spec=[])
        request.headers.get.return_value = None
        request.client.host = "192.168.1.1"

        identifier = middleware._get_identifier(request)
        assert identifier == "ip:192.168.1.1"

    def test_get_tier_from_state(self, middleware):
        """Test tier extraction from request state"""
        request = Mock()
        request.state.rate_limit_tier = "pro"

        tier = middleware._get_tier(request)
        assert tier == "pro"

    def test_get_tier_default(self, middleware):
        """Test default tier when not in state"""
        request = Mock()
        # Simulate no rate_limit_tier attribute
        request.state = Mock(spec=[])

        tier = middleware._get_tier(request)
        assert tier == "basic"

    def test_should_exempt_health(self, middleware):
        """Test that /health is exempt"""
        assert middleware._should_exempt("/health") is True

    def test_should_exempt_docs(self, middleware):
        """Test that /docs is exempt"""
        assert middleware._should_exempt("/docs") is True

    def test_should_exempt_openapi(self, middleware):
        """Test that /openapi.json is exempt"""
        assert middleware._should_exempt("/openapi.json") is True

    def test_should_exempt_prefix_match(self, middleware):
        """Test that prefix matching works for exempt paths"""
        assert middleware._should_exempt("/health/check") is True
        assert middleware._should_exempt("/docs/swagger") is True

    def test_should_not_exempt_regular_path(self, middleware):
        """Test that regular paths are not exempt"""
        assert middleware._should_exempt("/api/agents") is False
        assert middleware._should_exempt("/api/execute") is False

    @pytest.mark.asyncio
    async def test_dispatch_exempt_path(self, middleware, mock_rate_limiter):
        """Test that exempt paths skip rate limiting"""
        request = Mock()
        request.url.path = "/health"

        call_next = AsyncMock(return_value=Response())

        response = await middleware.dispatch(request, call_next)

        # Verify rate limiter was not called
        mock_rate_limiter.is_allowed.assert_not_called()
        # Verify request was processed
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_dispatch_allowed_request(self, middleware, mock_rate_limiter):
        """Test allowed request processing"""
        request = Mock()
        request.url.path = "/api/agents"
        request.method = "GET"
        request.state.tenant_id = "tenant123"
        request.state.rate_limit_tier = "basic"

        mock_response = Mock(spec=Response)
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        mock_rate_limiter.is_allowed.return_value = (True, {
            "remaining": 45,
            "reset": 1234567890,
            "limit": 50,
            "period": 60
        })

        response = await middleware.dispatch(request, call_next)

        # Verify rate limiter was called
        mock_rate_limiter.is_allowed.assert_called_once_with(
            "tenant:tenant123",
            "GET:/api/agents",
            "basic"
        )

        # Verify headers were added
        assert "X-RateLimit-Limit" in mock_response.headers
        assert mock_response.headers["X-RateLimit-Limit"] == "50"
        assert mock_response.headers["X-RateLimit-Remaining"] == "45"
        assert mock_response.headers["X-RateLimit-Reset"] == "1234567890"

    @pytest.mark.asyncio
    async def test_dispatch_rate_limit_exceeded(self, middleware, mock_rate_limiter):
        """Test request denied when rate limit exceeded"""
        request = Mock()
        request.url.path = "/api/execute"
        request.method = "POST"
        request.state.tenant_id = "tenant456"
        request.state.rate_limit_tier = "free"

        call_next = AsyncMock()

        mock_rate_limiter.is_allowed.return_value = (False, {
            "remaining": 0,
            "reset": 1234567890,
            "retry_after": 30,
            "limit": 10,
            "period": 60
        })

        response = await middleware.dispatch(request, call_next)

        # Verify rate limiter was called
        mock_rate_limiter.is_allowed.assert_called_once()

        # Verify response is 429
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

        # Verify headers
        assert response.headers["X-RateLimit-Limit"] == "10"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.headers["X-RateLimit-Reset"] == "1234567890"
        assert response.headers["Retry-After"] == "30"

        # Verify call_next was NOT called
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_rate_limit_exceeded_content(self, middleware, mock_rate_limiter):
        """Test rate limit exceeded response content"""
        request = Mock()
        request.url.path = "/api/agents"
        request.method = "GET"
        request.state.tenant_id = "tenant789"
        request.state.rate_limit_tier = "basic"

        call_next = AsyncMock()

        mock_rate_limiter.is_allowed.return_value = (False, {
            "remaining": 0,
            "reset": 1234567890,
            "retry_after": 45,
            "limit": 50,
            "period": 60
        })

        response = await middleware.dispatch(request, call_next)

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert response.media_type == "application/json"
        assert b"Rate limit exceeded" in response.body

    @pytest.mark.asyncio
    async def test_dispatch_different_methods_same_path(self, middleware, mock_rate_limiter):
        """Test that different HTTP methods on same path are tracked separately"""
        # GET request
        request_get = Mock()
        request_get.url.path = "/api/agents"
        request_get.method = "GET"
        request_get.state.tenant_id = "tenant123"
        request_get.state.rate_limit_tier = "basic"

        mock_response = Mock(spec=Response)
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        await middleware.dispatch(request_get, call_next)

        # Verify endpoint includes method
        assert mock_rate_limiter.is_allowed.call_args[0][1] == "GET:/api/agents"

        # POST request
        request_post = Mock()
        request_post.url.path = "/api/agents"
        request_post.method = "POST"
        request_post.state.tenant_id = "tenant123"
        request_post.state.rate_limit_tier = "basic"

        await middleware.dispatch(request_post, call_next)

        # Verify endpoint includes method
        assert mock_rate_limiter.is_allowed.call_args[0][1] == "POST:/api/agents"

    @pytest.mark.asyncio
    async def test_dispatch_uses_ip_fallback(self, middleware, mock_rate_limiter):
        """Test that IP address is used as fallback identifier"""
        request = Mock()
        request.url.path = "/api/agents"
        request.method = "GET"
        # No auth state
        request.state = Mock(spec=[])
        # No API key
        request.headers.get.return_value = None
        # IP address
        request.client.host = "203.0.113.45"

        mock_response = Mock(spec=Response)
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        await middleware.dispatch(request, call_next)

        # Verify IP was used as identifier
        assert mock_rate_limiter.is_allowed.call_args[0][0] == "ip:203.0.113.45"

    @pytest.mark.asyncio
    async def test_dispatch_tier_priority(self, middleware, mock_rate_limiter):
        """Test that tier from state is used when available"""
        request = Mock()
        request.url.path = "/api/agents"
        request.method = "GET"
        request.state.tenant_id = "tenant123"
        request.state.rate_limit_tier = "enterprise"

        mock_response = Mock(spec=Response)
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        await middleware.dispatch(request, call_next)

        # Verify enterprise tier was used
        assert mock_rate_limiter.is_allowed.call_args[0][2] == "enterprise"
