"""
Unit tests for AuthClient.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.auth_client import AuthClient, AuthContext
import jwt
from datetime import datetime, timedelta


@pytest.mark.unit
class TestAuthClient:
    """Test suite for AuthClient"""

    @pytest.fixture
    def auth_client(self):
        """Create auth client with test secret"""
        return AuthClient(
            auth_service_url="http://test-auth:9002",
            jwt_secret="test-secret-key-123"
        )

    @pytest.fixture
    def valid_jwt_payload(self):
        """Valid JWT payload"""
        return {
            "sub": "user-123",
            "tenant_id": "tenant-456",
            "email": "test@example.com",
            "roles": ["admin", "user"],
            "permissions": ["read:agents", "write:agents"],
            "is_superuser": False,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

    @pytest.mark.asyncio
    async def test_verify_token_valid_jwt(self, auth_client, valid_jwt_payload):
        """Test verifying a valid JWT token"""
        # Create a valid JWT
        token = jwt.encode(valid_jwt_payload, "test-secret-key-123", algorithm="HS256")

        result = await auth_client.verify_token(token)

        assert result is not None
        assert result.user_id == "user-123"
        assert result.tenant_id == "tenant-456"
        assert result.email == "test@example.com"
        assert result.roles == ["admin", "user"]
        assert result.permissions == ["read:agents", "write:agents"]
        assert result.is_superuser is False

    @pytest.mark.asyncio
    async def test_verify_token_expired_jwt(self, auth_client):
        """Test verifying an expired JWT token"""
        # Create an expired JWT
        expired_payload = {
            "sub": "user-123",
            "tenant_id": "tenant-456",
            "email": "test@example.com",
            "roles": [],
            "permissions": [],
            "is_superuser": False,
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        token = jwt.encode(expired_payload, "test-secret-key-123", algorithm="HS256")

        result = await auth_client.verify_token(token)

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_invalid_signature(self, auth_client, valid_jwt_payload):
        """Test verifying a JWT with invalid signature"""
        # Create JWT with different secret
        token = jwt.encode(valid_jwt_payload, "wrong-secret", algorithm="HS256")

        result = await auth_client.verify_token(token)

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_malformed_jwt(self, auth_client):
        """Test verifying a malformed JWT"""
        result = await auth_client.verify_token("not-a-valid-jwt")

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_api_key_success(self, auth_client):
        """Test verifying a valid API key"""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "user-789",
            "tenant_id": "tenant-abc",
            "email": "apikey@example.com",
            "roles": ["service"],
            "permissions": ["execute:agents"],
            "is_superuser": False
        }

        with patch.object(auth_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await auth_client.verify_token("sk_test_api_key_123")

            assert result is not None
            assert result.user_id == "user-789"
            assert result.tenant_id == "tenant-abc"
            assert result.email == "apikey@example.com"
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_token_api_key_invalid(self, auth_client):
        """Test verifying an invalid API key"""
        # Mock HTTP response with 401
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch.object(auth_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await auth_client.verify_token("sk_invalid_api_key")

            assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_api_key_network_error(self, auth_client):
        """Test API key verification with network error"""
        with patch.object(auth_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = await auth_client.verify_token("sk_test_api_key")

            assert result is None

    @pytest.mark.asyncio
    async def test_verify_api_key_success(self, auth_client):
        """Test _verify_api_key with successful response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "user-xyz",
            "tenant_id": "tenant-def",
            "email": "service@example.com",
            "roles": ["api"],
            "permissions": ["read:all"],
            "is_superuser": True
        }

        with patch.object(auth_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await auth_client._verify_api_key("sk_test_key")

            assert result is not None
            assert result.user_id == "user-xyz"
            assert result.is_superuser is True
            # Verify correct URL and headers
            call_args = mock_get.call_args
            assert "api-keys/verify" in call_args[0][0]
            assert call_args[1]["headers"]["Authorization"] == "Bearer sk_test_key"

    @pytest.mark.asyncio
    async def test_verify_api_key_not_found(self, auth_client):
        """Test _verify_api_key with 404 response"""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch.object(auth_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await auth_client._verify_api_key("sk_nonexistent_key")

            assert result is None

    @pytest.mark.asyncio
    async def test_verify_api_key_server_error(self, auth_client):
        """Test _verify_api_key with 500 response"""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.object(auth_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await auth_client._verify_api_key("sk_test_key")

            assert result is None

    @pytest.mark.asyncio
    async def test_verify_api_key_exception_handling(self, auth_client):
        """Test _verify_api_key exception handling"""
        with patch.object(auth_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = Exception("Connection timeout")

            result = await auth_client._verify_api_key("sk_test_key")

            assert result is None

    @pytest.mark.asyncio
    async def test_check_permission_superuser(self, auth_client):
        """Test that superusers have all permissions"""
        auth_context = AuthContext(
            user_id="super-user",
            tenant_id="tenant-1",
            email="super@example.com",
            roles=["admin"],
            permissions=[],
            is_superuser=True
        )

        result = await auth_client.check_permission(auth_context, "any:permission")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_permission_user_has_permission(self, auth_client):
        """Test user with specific permission"""
        auth_context = AuthContext(
            user_id="user-1",
            tenant_id="tenant-1",
            email="user@example.com",
            roles=["user"],
            permissions=["read:agents", "write:agents"],
            is_superuser=False
        )

        result = await auth_client.check_permission(auth_context, "read:agents")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_permission_user_lacks_permission(self, auth_client):
        """Test user without specific permission"""
        auth_context = AuthContext(
            user_id="user-2",
            tenant_id="tenant-1",
            email="limited@example.com",
            roles=["user"],
            permissions=["read:agents"],
            is_superuser=False
        )

        result = await auth_client.check_permission(auth_context, "delete:agents")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_permission_empty_permissions(self, auth_client):
        """Test user with no permissions"""
        auth_context = AuthContext(
            user_id="user-3",
            tenant_id="tenant-1",
            email="noperm@example.com",
            roles=[],
            permissions=[],
            is_superuser=False
        )

        result = await auth_client.check_permission(auth_context, "any:permission")

        assert result is False

    @pytest.mark.asyncio
    async def test_close(self, auth_client):
        """Test closing the HTTP client"""
        with patch.object(auth_client.client, 'aclose', new_callable=AsyncMock) as mock_close:
            await auth_client.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_token_with_default_values(self, auth_client):
        """Test JWT with missing optional fields uses defaults"""
        # Minimal JWT payload
        minimal_payload = {
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(minimal_payload, "test-secret-key-123", algorithm="HS256")

        result = await auth_client.verify_token(token)

        assert result is not None
        assert result.user_id == "unknown"
        assert result.tenant_id == "unknown"
        assert result.email == "unknown"
        assert result.roles == []
        assert result.permissions == []
        assert result.is_superuser is False

    @pytest.mark.asyncio
    async def test_verify_token_empty_string(self, auth_client):
        """Test verifying empty token string"""
        result = await auth_client.verify_token("")

        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_non_sk_prefix(self, auth_client):
        """Test invalid token without sk_ prefix"""
        result = await auth_client.verify_token("invalid_prefix_key")

        assert result is None

    @pytest.mark.asyncio
    async def test_auth_client_initialization(self):
        """Test AuthClient initialization with custom values"""
        client = AuthClient(
            auth_service_url="http://custom-auth:8080",
            jwt_secret="custom-secret"
        )

        assert client.auth_service_url == "http://custom-auth:8080"
        assert client.jwt_secret == "custom-secret"
        assert client.client is not None

    @pytest.mark.asyncio
    async def test_auth_client_default_initialization(self):
        """Test AuthClient initialization with defaults"""
        client = AuthClient()

        assert client.auth_service_url == "http://auth:9002"
        assert client.jwt_secret == ""
        assert client.client is not None

    @pytest.mark.asyncio
    async def test_verify_token_jwt_decode_exception(self, auth_client):
        """Test JWT decode with generic exception"""
        with patch('jwt.decode', side_effect=Exception("Unexpected error")):
            result = await auth_client.verify_token("any-token")
            assert result is None

    @pytest.mark.asyncio
    async def test_auth_context_model(self):
        """Test AuthContext Pydantic model"""
        context = AuthContext(
            user_id="user-1",
            tenant_id="tenant-1",
            email="test@example.com",
            roles=["admin"],
            permissions=["read:all"],
            is_superuser=True
        )

        assert context.user_id == "user-1"
        assert context.tenant_id == "tenant-1"
        assert context.email == "test@example.com"
        assert context.roles == ["admin"]
        assert context.permissions == ["read:all"]
        assert context.is_superuser is True

    @pytest.mark.asyncio
    async def test_verify_api_key_json_decode_error(self, auth_client):
        """Test API key verification with JSON decode error"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch.object(auth_client.client, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response

            result = await auth_client._verify_api_key("sk_test_key")

            assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_api_key_starts_with_sk(self, auth_client):
        """Test that only tokens starting with 'sk_' are treated as API keys"""
        # This should not trigger API key verification
        result = await auth_client.verify_token("not_sk_prefix")

        assert result is None

    @pytest.mark.asyncio
    async def test_concurrent_verify_token_calls(self, auth_client, valid_jwt_payload):
        """Test multiple concurrent verify_token calls"""
        token = jwt.encode(valid_jwt_payload, "test-secret-key-123", algorithm="HS256")

        # Run multiple verifications concurrently
        import asyncio
        results = await asyncio.gather(
            auth_client.verify_token(token),
            auth_client.verify_token(token),
            auth_client.verify_token(token)
        )

        # All should succeed
        assert all(r is not None for r in results)
        assert all(r.user_id == "user-123" for r in results)
