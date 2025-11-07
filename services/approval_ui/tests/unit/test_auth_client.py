"""
Unit tests for auth_client module.
Tests AuthClient and AuthContext functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from auth_client import AuthClient, AuthContext


class TestAuthContext:
    """Test AuthContext model"""

    def test_auth_context_creation(self):
        """Test creating an AuthContext with valid data"""
        context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="user@example.com",
            roles=["admin", "user"],
            permissions=["read", "write"],
            is_superuser=True
        )

        assert context.user_id == "user-123"
        assert context.tenant_id == "tenant-456"
        assert context.email == "user@example.com"
        assert context.roles == ["admin", "user"]
        assert context.permissions == ["read", "write"]
        assert context.is_superuser is True

    def test_auth_context_validation(self):
        """Test AuthContext validation"""
        # Should work with minimal data
        context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="user@example.com",
            roles=[],
            permissions=[],
            is_superuser=False
        )

        assert context.user_id == "user-123"
        assert context.roles == []


class TestAuthClient:
    """Test AuthClient functionality"""

    def test_auth_client_initialization(self):
        """Test AuthClient initialization"""
        client = AuthClient(
            auth_service_url="http://localhost:9002",
            jwt_secret="test-secret"
        )

        assert client.auth_service_url == "http://localhost:9002"
        assert client.jwt_secret == "test-secret"
        assert isinstance(client.client, httpx.AsyncClient)

    def test_auth_client_default_initialization(self):
        """Test AuthClient with default values"""
        client = AuthClient()

        assert client.auth_service_url == "http://auth:9002"
        assert client.jwt_secret == ""

    @pytest.mark.asyncio
    async def test_verify_valid_jwt_token(self, valid_jwt_token):
        """Test verifying a valid JWT token"""
        client = AuthClient(
            auth_service_url="http://localhost:9002",
            jwt_secret="test-secret-key-for-testing-purposes-only-min-32-chars"
        )

        auth_context = await client.verify_token(valid_jwt_token)

        assert auth_context is not None
        assert auth_context.user_id == "test-user-id"
        assert auth_context.tenant_id == "test-tenant-id"
        assert auth_context.email == "test@example.com"
        assert "admin" in auth_context.roles
        assert "approvals:read" in auth_context.permissions

        await client.close()

    @pytest.mark.asyncio
    async def test_verify_expired_jwt_token(self, expired_jwt_token):
        """Test verifying an expired JWT token"""
        client = AuthClient(
            auth_service_url="http://localhost:9002",
            jwt_secret="test-secret-key-for-testing-purposes-only-min-32-chars"
        )

        auth_context = await client.verify_token(expired_jwt_token)

        assert auth_context is None

        await client.close()

    @pytest.mark.asyncio
    async def test_verify_invalid_jwt_token(self):
        """Test verifying an invalid JWT token"""
        client = AuthClient(
            auth_service_url="http://localhost:9002",
            jwt_secret="test-secret-key-for-testing-purposes-only-min-32-chars"
        )

        auth_context = await client.verify_token("invalid.jwt.token")

        assert auth_context is None

        await client.close()

    @pytest.mark.asyncio
    async def test_verify_jwt_with_wrong_secret(self, valid_jwt_token):
        """Test verifying JWT with wrong secret"""
        client = AuthClient(
            auth_service_url="http://localhost:9002",
            jwt_secret="wrong-secret-key"
        )

        auth_context = await client.verify_token(valid_jwt_token)

        assert auth_context is None

        await client.close()

    @pytest.mark.asyncio
    async def test_verify_api_key_success(self):
        """Test verifying a valid API key"""
        client = AuthClient(auth_service_url="http://localhost:9002")

        # Mock the HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={
            "user_id": "api-user-123",
            "tenant_id": "api-tenant-456",
            "email": "api@example.com",
            "roles": ["service"],
            "permissions": ["approvals:create"],
            "is_superuser": False
        })

        # Create an async mock that returns the mock_response
        async_get_mock = AsyncMock(return_value=mock_response)

        with patch.object(client.client, 'get', async_get_mock):
            auth_context = await client.verify_token("sk_test_api_key_12345")

        assert auth_context is not None
        assert auth_context.user_id == "api-user-123"
        assert auth_context.tenant_id == "api-tenant-456"
        assert auth_context.email == "api@example.com"

        await client.close()

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self):
        """Test verifying an invalid API key"""
        client = AuthClient(auth_service_url="http://localhost:9002")

        # Mock the HTTP client to return 401
        mock_response = AsyncMock()
        mock_response.status_code = 401

        with patch.object(client.client, 'get', return_value=mock_response):
            auth_context = await client.verify_token("sk_invalid_api_key")

        assert auth_context is None

        await client.close()

    @pytest.mark.asyncio
    async def test_verify_api_key_service_error(self):
        """Test API key verification when auth service is down"""
        client = AuthClient(auth_service_url="http://localhost:9002")

        # Mock the HTTP client to raise exception
        with patch.object(client.client, 'get', side_effect=Exception("Connection failed")):
            auth_context = await client.verify_token("sk_test_api_key")

        assert auth_context is None

        await client.close()

    @pytest.mark.asyncio
    async def test_check_permission_superuser(self):
        """Test permission check for superuser"""
        client = AuthClient()

        auth_context = AuthContext(
            user_id="superuser",
            tenant_id="tenant-1",
            email="super@example.com",
            roles=["superuser"],
            permissions=[],
            is_superuser=True
        )

        # Superuser should have all permissions
        has_permission = await client.check_permission(auth_context, "any:permission")

        assert has_permission is True

        await client.close()

    @pytest.mark.asyncio
    async def test_check_permission_granted(self):
        """Test permission check when user has permission"""
        client = AuthClient()

        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-1",
            email="user@example.com",
            roles=["user"],
            permissions=["approvals:read", "approvals:write"],
            is_superuser=False
        )

        has_permission = await client.check_permission(auth_context, "approvals:read")

        assert has_permission is True

        await client.close()

    @pytest.mark.asyncio
    async def test_check_permission_denied(self):
        """Test permission check when user lacks permission"""
        client = AuthClient()

        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-1",
            email="user@example.com",
            roles=["user"],
            permissions=["approvals:read"],
            is_superuser=False
        )

        has_permission = await client.check_permission(auth_context, "approvals:delete")

        assert has_permission is False

        await client.close()

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the auth client"""
        client = AuthClient()

        # Should not raise any errors
        await client.close()
