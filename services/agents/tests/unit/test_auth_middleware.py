"""
Unit tests for auth middleware.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth_middleware import (
    set_auth_client,
    get_current_user,
    require_permission,
    require_any_permission,
    _auth_client
)
from app.auth_client import AuthClient, AuthContext


class TestSetAuthClient:
    """Test suite for set_auth_client function"""

    def test_set_auth_client(self):
        """Test setting global auth client"""
        from app import auth_middleware

        mock_client = Mock(spec=AuthClient)

        # Set the client
        set_auth_client(mock_client)

        # Verify it was set
        assert auth_middleware._auth_client == mock_client

        # Clean up - reset to None
        auth_middleware._auth_client = None


class TestGetCurrentUser:
    """Test suite for get_current_user dependency"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Reset auth client before and after each test"""
        from app import auth_middleware
        auth_middleware._auth_client = None
        yield
        auth_middleware._auth_client = None

    @pytest.mark.asyncio
    async def test_get_current_user_missing_credentials(self):
        """Test get_current_user raises 401 when credentials missing"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=None)

        assert exc_info.value.status_code == 401
        assert "Missing authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_no_auth_client(self):
        """Test get_current_user raises 503 when auth client not initialized"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test_token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials)

        assert exc_info.value.status_code == 503
        assert "Authentication service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test get_current_user raises 401 when token is invalid"""
        from app import auth_middleware

        mock_client = AsyncMock(spec=AuthClient)
        mock_client.verify_token = AsyncMock(return_value=None)
        auth_middleware._auth_client = mock_client

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid_token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail
        mock_client.verify_token.assert_called_once_with("invalid_token")

    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test get_current_user returns auth context on success"""
        from app import auth_middleware

        mock_client = AsyncMock(spec=AuthClient)
        mock_auth_context = AuthContext(
            user_id="user123",
            tenant_id="tenant456",
            email="test@example.com",
            roles=["user"], permissions=["agents:execute"], is_superuser=False
        )
        mock_client.verify_token = AsyncMock(return_value=mock_auth_context)
        auth_middleware._auth_client = mock_client

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid_token"
        )

        result = await get_current_user(credentials=credentials)

        assert result == mock_auth_context
        assert result.user_id == "user123"
        assert result.email == "test@example.com"
        mock_client.verify_token.assert_called_once_with("valid_token")


class TestRequirePermission:
    """Test suite for require_permission dependency factory"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Reset auth client before and after each test"""
        from app import auth_middleware
        auth_middleware._auth_client = None
        yield
        auth_middleware._auth_client = None

    @pytest.mark.asyncio
    async def test_require_permission_no_auth_client(self):
        """Test require_permission raises 503 when auth client not initialized"""
        permission_checker = require_permission("agents:execute")

        mock_auth_context = AuthContext(
            user_id="user123",
            tenant_id="tenant456",
            email="test@example.com",
            roles=[], permissions=[], is_superuser=False
        )

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(auth_context=mock_auth_context)

        assert exc_info.value.status_code == 503
        assert "Authentication service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_permission_missing(self):
        """Test require_permission raises 403 when permission missing"""
        from app import auth_middleware

        mock_client = AsyncMock(spec=AuthClient)
        mock_client.check_permission = AsyncMock(return_value=False)
        auth_middleware._auth_client = mock_client

        permission_checker = require_permission("agents:execute")

        mock_auth_context = AuthContext(
            user_id="user123",
            tenant_id="tenant456",
            email="test@example.com",
            roles=["user"], permissions=["agents:read"], is_superuser=False
        )

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(auth_context=mock_auth_context)

        assert exc_info.value.status_code == 403
        assert "Missing required permission: agents:execute" in exc_info.value.detail
        mock_client.check_permission.assert_called_once_with(mock_auth_context, "agents:execute")

    @pytest.mark.asyncio
    async def test_require_permission_success(self):
        """Test require_permission returns auth context when permission granted"""
        from app import auth_middleware

        mock_client = AsyncMock(spec=AuthClient)
        mock_client.check_permission = AsyncMock(return_value=True)
        auth_middleware._auth_client = mock_client

        permission_checker = require_permission("agents:execute")

        mock_auth_context = AuthContext(
            user_id="user123",
            tenant_id="tenant456",
            email="test@example.com",
            roles=["user"], permissions=["agents:execute"], is_superuser=False
        )

        result = await permission_checker(auth_context=mock_auth_context)

        assert result == mock_auth_context
        mock_client.check_permission.assert_called_once_with(mock_auth_context, "agents:execute")


class TestRequireAnyPermission:
    """Test suite for require_any_permission dependency factory"""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Reset auth client before and after each test"""
        from app import auth_middleware
        auth_middleware._auth_client = None
        yield
        auth_middleware._auth_client = None

    @pytest.mark.asyncio
    async def test_require_any_permission_no_auth_client(self):
        """Test require_any_permission raises 503 when auth client not initialized"""
        permission_checker = require_any_permission(["agents:read", "agents:execute"])

        mock_auth_context = AuthContext(
            user_id="user123",
            tenant_id="tenant456",
            email="test@example.com",
            roles=[], permissions=[], is_superuser=False
        )

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(auth_context=mock_auth_context)

        assert exc_info.value.status_code == 503
        assert "Authentication service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_any_permission_none_match(self):
        """Test require_any_permission raises 403 when no permissions match"""
        from app import auth_middleware

        mock_client = AsyncMock(spec=AuthClient)
        mock_client.check_permission = AsyncMock(return_value=False)
        auth_middleware._auth_client = mock_client

        permission_checker = require_any_permission(["agents:read", "agents:execute"])

        mock_auth_context = AuthContext(
            user_id="user123",
            tenant_id="tenant456",
            email="test@example.com",
            roles=["user"], permissions=["webhooks:read"], is_superuser=False
        )

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(auth_context=mock_auth_context)

        assert exc_info.value.status_code == 403
        assert "Missing required permissions" in exc_info.value.detail
        assert "agents:read" in exc_info.value.detail
        assert "agents:execute" in exc_info.value.detail
        # Should have checked all permissions
        assert mock_client.check_permission.call_count == 2

    @pytest.mark.asyncio
    async def test_require_any_permission_first_matches(self):
        """Test require_any_permission returns auth context when first permission matches"""
        from app import auth_middleware

        mock_client = AsyncMock(spec=AuthClient)
        mock_client.check_permission = AsyncMock(return_value=True)
        auth_middleware._auth_client = mock_client

        permission_checker = require_any_permission(["agents:read", "agents:execute"])

        mock_auth_context = AuthContext(
            user_id="user123",
            tenant_id="tenant456",
            email="test@example.com",
            roles=["user"], permissions=["agents:read", "agents:execute"], is_superuser=False
        )

        result = await permission_checker(auth_context=mock_auth_context)

        assert result == mock_auth_context
        # Should only check first permission and return early
        mock_client.check_permission.assert_called_once_with(mock_auth_context, "agents:read")

    @pytest.mark.asyncio
    async def test_require_any_permission_second_matches(self):
        """Test require_any_permission returns auth context when second permission matches"""
        from app import auth_middleware

        mock_client = AsyncMock(spec=AuthClient)
        # First permission check fails, second succeeds
        mock_client.check_permission = AsyncMock(side_effect=[False, True])
        auth_middleware._auth_client = mock_client

        permission_checker = require_any_permission(["agents:execute", "agents:read"])

        mock_auth_context = AuthContext(
            user_id="user123",
            tenant_id="tenant456",
            email="test@example.com",
            roles=["user"], permissions=["agents:read"], is_superuser=False
        )

        result = await permission_checker(auth_context=mock_auth_context)

        assert result == mock_auth_context
        # Should check both permissions
        assert mock_client.check_permission.call_count == 2
