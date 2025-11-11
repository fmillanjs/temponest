"""
Unit tests for base HTTP client
"""
import pytest
import httpx
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from temponest_sdk.client import BaseClient, AsyncBaseClient
from temponest_sdk.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    TemponestAPIError,
    ConnectionError as TemponestConnectionError,
    TimeoutError as TemponestTimeoutError,
    ConfigurationError,
)


# ==================== BaseClient Tests ====================

class TestBaseClientInitialization:
    """Test BaseClient initialization"""

    def test_init_with_base_url_and_token(self, clean_env):
        """Test initialization with explicit parameters"""
        client = BaseClient(
            base_url="http://test.com",
            auth_token="test-token"
        )

        assert client.base_url == "http://test.com/"
        assert client.auth_token == "test-token"
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.retry_backoff_factor == 0.5

    def test_init_with_env_vars(self, set_env):
        """Test initialization with environment variables"""
        client = BaseClient()

        assert client.base_url == "http://localhost:9000/"
        assert client.auth_token == "test-token"

    def test_init_uses_default_base_url(self, clean_env):
        """Test initialization uses default base_url when not provided"""
        client = BaseClient()
        # Should use default localhost:9000
        assert client.base_url == "http://localhost:9000/"

    def test_init_adds_trailing_slash(self, clean_env):
        """Test that trailing slash is added to base_url"""
        client = BaseClient(base_url="http://test.com")
        assert client.base_url == "http://test.com/"

        client2 = BaseClient(base_url="http://test.com/")
        assert client2.base_url == "http://test.com/"

    def test_init_custom_timeout(self, clean_env):
        """Test custom timeout"""
        client = BaseClient(
            base_url="http://test.com",
            timeout=60.0
        )
        assert client.timeout == 60.0

    def test_init_custom_retry_params(self, clean_env):
        """Test custom retry parameters"""
        client = BaseClient(
            base_url="http://test.com",
            max_retries=5,
            retry_backoff_factor=1.0
        )
        assert client.max_retries == 5
        assert client.retry_backoff_factor == 1.0


class TestBaseClientHeaders:
    """Test HTTP headers"""

    def test_get_headers_without_token(self, clean_env):
        """Test headers without auth token"""
        client = BaseClient(base_url="http://test.com")
        headers = client._get_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["User-Agent"] == "temponest-sdk/1.0.0"
        assert "Authorization" not in headers

    def test_get_headers_with_token(self, clean_env):
        """Test headers with auth token"""
        client = BaseClient(
            base_url="http://test.com",
            auth_token="test-token"
        )
        headers = client._get_headers()

        assert headers["Authorization"] == "Bearer test-token"


class TestBaseClientErrorHandling:
    """Test error handling"""

    def test_handle_401_error(self, clean_env, mock_httpx_response):
        """Test 401 raises AuthenticationError"""
        client = BaseClient(base_url="http://test.com")
        response = mock_httpx_response(
            status_code=401,
            json_data={"detail": "Unauthorized"}
        )

        with pytest.raises(AuthenticationError, match="Unauthorized"):
            client._handle_error(response)

    def test_handle_403_error(self, clean_env, mock_httpx_response):
        """Test 403 raises AuthorizationError"""
        client = BaseClient(base_url="http://test.com")
        response = mock_httpx_response(
            status_code=403,
            json_data={"detail": "Forbidden"}
        )

        with pytest.raises(AuthorizationError, match="Forbidden"):
            client._handle_error(response)

    def test_handle_404_error(self, clean_env, mock_httpx_response):
        """Test 404 raises NotFoundError"""
        client = BaseClient(base_url="http://test.com")
        response = mock_httpx_response(
            status_code=404,
            json_data={"detail": "Not found"}
        )

        with pytest.raises(NotFoundError, match="Not found"):
            client._handle_error(response)

    def test_handle_422_error(self, clean_env, mock_httpx_response):
        """Test 422 raises ValidationError"""
        client = BaseClient(base_url="http://test.com")
        response = mock_httpx_response(
            status_code=422,
            json_data={"detail": "Validation failed"}
        )

        with pytest.raises(ValidationError, match="Validation failed"):
            client._handle_error(response)

    def test_handle_429_error(self, clean_env, mock_httpx_response):
        """Test 429 raises RateLimitError"""
        client = BaseClient(base_url="http://test.com")
        response = mock_httpx_response(
            status_code=429,
            json_data={"detail": "Rate limit exceeded"},
            headers={"Retry-After": "60"}
        )

        with pytest.raises(RateLimitError, match="Rate limit exceeded") as exc_info:
            client._handle_error(response)

        assert exc_info.value.retry_after == 60

    def test_handle_500_error(self, clean_env, mock_httpx_response):
        """Test 500 raises ServerError"""
        client = BaseClient(base_url="http://test.com")
        response = mock_httpx_response(
            status_code=500,
            json_data={"detail": "Internal server error"}
        )

        with pytest.raises(ServerError, match="Internal server error"):
            client._handle_error(response)

    def test_handle_generic_error(self, clean_env, mock_httpx_response):
        """Test generic error raises TemponestAPIError"""
        client = BaseClient(base_url="http://test.com")
        response = mock_httpx_response(
            status_code=418,
            json_data={"detail": "I'm a teapot"}
        )

        with pytest.raises(TemponestAPIError, match="I'm a teapot"):
            client._handle_error(response)

    def test_handle_error_without_json(self, clean_env):
        """Test error handling when response is not JSON"""
        client = BaseClient(base_url="http://test.com")
        response = Mock(spec=httpx.Response)
        response.status_code = 500
        response.text = "Plain text error"
        response.json.side_effect = Exception("Not JSON")

        with pytest.raises(ServerError, match="Plain text error"):
            client._handle_error(response)


class TestBaseClientRequests:
    """Test HTTP request methods"""

    @patch("temponest_sdk.client.httpx.Client")
    def test_get_request(self, mock_client_class, clean_env):
        """Test GET request"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Create response
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.content = b'{"result": "success"}'
        response.json.return_value = {"result": "success"}
        mock_client.request.return_value = response

        client = BaseClient(base_url="http://test.com")
        result = client.get("/test", params={"key": "value"})

        assert result == {"result": "success"}
        mock_client.request.assert_called_once()
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["method"] == "GET"
        assert call_kwargs["params"] == {"key": "value"}

    @patch("temponest_sdk.client.httpx.Client")
    def test_post_request(self, mock_client_class, clean_env):
        """Test POST request"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        response = Mock(spec=httpx.Response)
        response.status_code = 201
        response.content = b'{"id": "123"}'
        response.json.return_value = {"id": "123"}
        mock_client.request.return_value = response

        client = BaseClient(base_url="http://test.com")
        result = client.post("/test", json={"name": "test"})

        assert result == {"id": "123"}
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert call_kwargs["json"] == {"name": "test"}

    @patch("temponest_sdk.client.httpx.Client")
    def test_put_request(self, mock_client_class, clean_env):
        """Test PUT request"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.content = b'{"updated": true}'
        response.json.return_value = {"updated": True}
        mock_client.request.return_value = response

        client = BaseClient(base_url="http://test.com")
        result = client.put("/test/123", json={"name": "updated"})

        assert result == {"updated": True}
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["method"] == "PUT"

    @patch("temponest_sdk.client.httpx.Client")
    def test_patch_request(self, mock_client_class, clean_env):
        """Test PATCH request"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.content = b'{"patched": true}'
        response.json.return_value = {"patched": True}
        mock_client.request.return_value = response

        client = BaseClient(base_url="http://test.com")
        result = client.patch("/test/123", json={"field": "value"})

        assert result == {"patched": True}
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["method"] == "PATCH"

    @patch("temponest_sdk.client.httpx.Client")
    def test_delete_request(self, mock_client_class, clean_env):
        """Test DELETE request"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        response = Mock(spec=httpx.Response)
        response.status_code = 204
        response.content = b''
        mock_client.request.return_value = response

        client = BaseClient(base_url="http://test.com")
        result = client.delete("/test/123")

        assert result is None
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["method"] == "DELETE"

    @patch("temponest_sdk.client.httpx.Client")
    def test_request_with_error_response(self, mock_client_class, clean_env):
        """Test request with error response"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        response = Mock(spec=httpx.Response)
        response.status_code = 404
        response.json.return_value = {"detail": "Not found"}
        mock_client.request.return_value = response

        client = BaseClient(base_url="http://test.com")

        with pytest.raises(NotFoundError):
            client.get("/test")

    @patch("temponest_sdk.client.httpx.Client")
    def test_request_timeout(self, mock_client_class, clean_env):
        """Test request timeout"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.request.side_effect = httpx.TimeoutException("Timeout")

        client = BaseClient(base_url="http://test.com", timeout=5.0)

        with pytest.raises(TemponestTimeoutError, match="Request timed out after 5.0s"):
            client.get("/test")

    @patch("temponest_sdk.client.httpx.Client")
    def test_request_network_error(self, mock_client_class, clean_env):
        """Test network error"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.request.side_effect = httpx.NetworkError("Network error")

        client = BaseClient(base_url="http://test.com")

        with pytest.raises(TemponestConnectionError, match="Network error"):
            client.get("/test")

    @patch("temponest_sdk.client.httpx.Client")
    def test_request_with_files(self, mock_client_class, clean_env):
        """Test request with file upload"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.content = b'{"uploaded": true}'
        response.json.return_value = {"uploaded": True}
        mock_client.request.return_value = response

        client = BaseClient(base_url="http://test.com")
        result = client.post("/upload", files={"file": b"content"})

        assert result == {"uploaded": True}
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["files"] == {"file": b"content"}

    @patch("temponest_sdk.client.httpx.Client")
    def test_request_non_json_response(self, mock_client_class, clean_env):
        """Test request with non-JSON response"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.content = b'plain text'
        response.text = "plain text"
        response.json.side_effect = Exception("Not JSON")
        mock_client.request.return_value = response

        client = BaseClient(base_url="http://test.com")
        result = client.get("/test")

        assert result == "plain text"


class TestBaseClientContextManager:
    """Test context manager functionality"""

    @patch("temponest_sdk.client.httpx.Client")
    def test_context_manager(self, mock_client_class, clean_env):
        """Test using client as context manager"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        with BaseClient(base_url="http://test.com") as client:
            assert client is not None

        mock_client.close.assert_called_once()

    @patch("temponest_sdk.client.httpx.Client")
    def test_manual_close(self, mock_client_class, clean_env):
        """Test manual close"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = BaseClient(base_url="http://test.com")
        client.close()

        mock_client.close.assert_called_once()


# ==================== AsyncBaseClient Tests ====================

class TestAsyncBaseClientInitialization:
    """Test AsyncBaseClient initialization"""

    def test_init_with_params(self, clean_env):
        """Test async client initialization"""
        client = AsyncBaseClient(
            base_url="http://test.com",
            auth_token="test-token"
        )

        assert client.base_url == "http://test.com/"
        assert client.auth_token == "test-token"


class TestAsyncBaseClientRequests:
    """Test async HTTP request methods"""

    @pytest.mark.asyncio
    @patch("temponest_sdk.client.httpx.AsyncClient")
    async def test_async_get_request(self, mock_client_class, clean_env):
        """Test async GET request"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.content = b'{"result": "success"}'
        response.json.return_value = {"result": "success"}
        mock_client.request = AsyncMock(return_value=response)

        client = AsyncBaseClient(base_url="http://test.com")
        result = await client.get("/test")

        assert result == {"result": "success"}

    @pytest.mark.asyncio
    @patch("temponest_sdk.client.httpx.AsyncClient")
    async def test_async_post_request(self, mock_client_class, clean_env):
        """Test async POST request"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        response = Mock(spec=httpx.Response)
        response.status_code = 201
        response.content = b'{"id": "123"}'
        response.json.return_value = {"id": "123"}
        mock_client.request = AsyncMock(return_value=response)

        client = AsyncBaseClient(base_url="http://test.com")
        result = await client.post("/test", json={"name": "test"})

        assert result == {"id": "123"}

    @pytest.mark.asyncio
    @patch("temponest_sdk.client.httpx.AsyncClient")
    async def test_async_context_manager(self, mock_client_class, clean_env):
        """Test async context manager"""
        mock_client = MagicMock()
        mock_client.aclose = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        async with AsyncBaseClient(base_url="http://test.com") as client:
            assert client is not None

        # aclose should have been called
        mock_client.aclose.assert_called_once()
