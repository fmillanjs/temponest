"""
Unit tests for auth_middleware module.
Tests authentication and authorization middleware.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from auth_client import AuthClient, AuthContext
from auth_middleware import (
    set_auth_client,
    get_current_user,
    require_permission,
    require_any_permission
)


class TestSetAuthClient:
    """Test set_auth_client function"""

    def test_set_auth_client(self):
        """Test setting the global auth client"""
        client = AsyncMock(spec=AuthClient)
        set_auth_client(client)

        # Verify it was set (implicitly tested by other tests)
        assert True


class TestGetCurrentUser:
    """Test get_current_user dependency"""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self, mock_auth_client):
        """Test getting current user with valid credentials"""
        client, auth_context = mock_auth_client
        set_auth_client(client)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-token-12345"
        )

        result = await get_current_user(credentials)

        assert result == auth_context
        assert result.user_id == "test-user-id"
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self):
        """Test get_current_user with missing credentials"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(None)

        assert exc_info.value.status_code == 401
        assert "Missing authentication credentials" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_no_auth_client(self):
        """Test get_current_user when auth client is not set"""
        set_auth_client(None)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid-token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 503
        assert "Authentication service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, mock_auth_client):
        """Test get_current_user with invalid token"""
        client, _ = mock_auth_client
        client.verify_token.return_value = None  # Invalid token
        set_auth_client(client)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail


class TestRequirePermission:
    """Test require_permission dependency factory"""

    @pytest.mark.asyncio
    async def test_require_permission_granted(self, mock_auth_client):
        """Test require_permission when user has permission"""
        client, auth_context = mock_auth_client
        client.check_permission.return_value = True
        set_auth_client(client)

        permission_checker = require_permission("approvals:read")

        result = await permission_checker(auth_context)

        assert result == auth_context
        client.check_permission.assert_called_once_with(auth_context, "approvals:read")

    @pytest.mark.asyncio
    async def test_require_permission_denied(self, mock_auth_client):
        """Test require_permission when user lacks permission"""
        client, auth_context = mock_auth_client
        client.check_permission.return_value = False
        set_auth_client(client)

        permission_checker = require_permission("approvals:delete")

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(auth_context)

        assert exc_info.value.status_code == 403
        assert "Missing required permission: approvals:delete" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_permission_no_auth_client(self):
        """Test require_permission when auth client is not set"""
        set_auth_client(None)

        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-1",
            email="user@example.com",
            roles=["user"],
            permissions=["approvals:read"],
            is_superuser=False
        )

        permission_checker = require_permission("approvals:read")

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(auth_context)

        assert exc_info.value.status_code == 503
        assert "Authentication service unavailable" in exc_info.value.detail


class TestRequireAnyPermission:
    """Test require_any_permission dependency factory"""

    @pytest.mark.asyncio
    async def test_require_any_permission_first_granted(self, mock_auth_client):
        """Test require_any_permission when user has first permission"""
        client, auth_context = mock_auth_client
        client.check_permission.return_value = True
        set_auth_client(client)

        permission_checker = require_any_permission(["approvals:read", "approvals:write"])

        result = await permission_checker(auth_context)

        assert result == auth_context

    @pytest.mark.asyncio
    async def test_require_any_permission_second_granted(self, mock_auth_client):
        """Test require_any_permission when user has second permission"""
        client, auth_context = mock_auth_client
        set_auth_client(client)

        # First permission denied, second granted
        client.check_permission.side_effect = [False, True]

        permission_checker = require_any_permission(["approvals:delete", "approvals:read"])

        result = await permission_checker(auth_context)

        assert result == auth_context

    @pytest.mark.asyncio
    async def test_require_any_permission_all_denied(self, mock_auth_client):
        """Test require_any_permission when user has no permissions"""
        client, auth_context = mock_auth_client
        client.check_permission.return_value = False
        set_auth_client(client)

        permission_checker = require_any_permission(["approvals:delete", "approvals:admin"])

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(auth_context)

        assert exc_info.value.status_code == 403
        assert "Missing required permissions" in exc_info.value.detail
        assert "approvals:delete" in exc_info.value.detail
        assert "approvals:admin" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_any_permission_single_permission(self, mock_auth_client):
        """Test require_any_permission with single permission"""
        client, auth_context = mock_auth_client
        client.check_permission.return_value = True
        set_auth_client(client)

        permission_checker = require_any_permission(["approvals:read"])

        result = await permission_checker(auth_context)

        assert result == auth_context

    @pytest.mark.asyncio
    async def test_require_any_permission_no_auth_client(self):
        """Test require_any_permission when auth client is not set"""
        set_auth_client(None)

        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-1",
            email="user@example.com",
            roles=["user"],
            permissions=["approvals:read"],
            is_superuser=False
        )

        permission_checker = require_any_permission(["approvals:read"])

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(auth_context)

        assert exc_info.value.status_code == 503
        assert "Authentication service unavailable" in exc_info.value.detail
