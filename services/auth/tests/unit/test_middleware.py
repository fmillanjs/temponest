"""
Unit tests for authentication middleware.

Tests get_current_user, get_current_active_user, require_permission, and require_role.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.middleware.auth import (
    get_current_user,
    get_current_active_user,
    require_permission,
    require_role,
    get_user_permissions,
    get_user_roles,
    AuthMiddleware
)
from app.models import AuthContext


@pytest.mark.unit
class TestGetCurrentUser:
    """Test get_current_user dependency"""

    async def test_get_current_user_missing_credentials(self):
        """Test that missing credentials raises 401"""
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "missing authentication credentials" in exc_info.value.detail.lower()

    @patch('app.middleware.auth.JWTHandler')
    async def test_get_current_user_valid_jwt(self, mock_jwt_handler):
        """Test successful authentication with valid JWT"""
        # Mock JWT verification
        mock_jwt_handler.verify_token.return_value = {
            "sub": "user-123",
            "tenant_id": "tenant-456",
            "email": "test@example.com",
            "roles": ["viewer"],
            "permissions": ["agents:read"],
            "is_superuser": False
        }

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="valid.jwt.token"
        )

        result = await get_current_user(credentials=credentials)

        assert isinstance(result, AuthContext)
        assert result.user_id == "user-123"
        assert result.tenant_id == "tenant-456"
        assert result.email == "test@example.com"
        assert result.roles == ["viewer"]
        assert result.permissions == ["agents:read"]
        assert result.is_superuser is False

    @patch('app.middleware.auth.APIKeyHandler')
    async def test_get_current_user_valid_api_key_with_user(self, mock_api_key_handler):
        """Test successful authentication with API key (has user_id)"""
        # Mock API key validation
        mock_api_key_handler.validate_api_key = AsyncMock(return_value={
            "user_id": "user-123",
            "tenant_id": "tenant-456",
            "user_email": "test@example.com",
            "scopes": ["agents:read", "agents:execute"],
            "is_superuser": False
        })

        # Mock get_user_permissions
        with patch('app.middleware.auth.get_user_permissions', new=AsyncMock(return_value=["agents:read", "agents:execute"])):
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="sk_test_validapikey"
            )

            result = await get_current_user(credentials=credentials)

            assert isinstance(result, AuthContext)
            assert result.user_id == "user-123"
            assert result.tenant_id == "tenant-456"
            assert result.email == "test@example.com"
            assert result.roles == ["api-key"]
            assert result.permissions == ["agents:read", "agents:execute"]

    @patch('app.middleware.auth.APIKeyHandler')
    async def test_get_current_user_valid_api_key_without_user(self, mock_api_key_handler):
        """Test successful authentication with API key (no user_id)"""
        # Mock API key validation
        mock_api_key_handler.validate_api_key = AsyncMock(return_value={
            "user_id": None,
            "tenant_id": "tenant-456",
            "scopes": ["agents:read"],
            "is_superuser": False
        })

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="sk_test_validapikey"
        )

        result = await get_current_user(credentials=credentials)

        assert isinstance(result, AuthContext)
        assert result.user_id == "api-key"
        assert result.tenant_id == "tenant-456"
        assert result.email == "api-key@system"
        assert result.roles == ["api-key"]
        assert result.permissions == ["agents:read"]

    @patch('app.middleware.auth.JWTHandler')
    @patch('app.middleware.auth.APIKeyHandler')
    async def test_get_current_user_invalid_jwt(self, mock_api_key_handler, mock_jwt_handler):
        """Test that invalid JWT raises 401"""
        # Mock JWT verification failure
        mock_jwt_handler.verify_token.return_value = None
        # Mock API key validation failure
        mock_api_key_handler.validate_api_key = AsyncMock(return_value=None)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.jwt.token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid authentication credentials" in exc_info.value.detail.lower()

    @patch('app.middleware.auth.APIKeyHandler')
    async def test_get_current_user_invalid_api_key(self, mock_api_key_handler):
        """Test that invalid API key raises 401"""
        # Mock API key validation failure
        mock_api_key_handler.validate_api_key = AsyncMock(return_value=None)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="sk_test_invalidkey"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('app.middleware.auth.JWTHandler')
    async def test_get_current_user_expired_jwt(self, mock_jwt_handler):
        """Test that expired JWT raises 401"""
        # Mock JWT verification with expired token
        mock_jwt_handler.verify_token.return_value = None

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="expired.jwt.token"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.unit
class TestGetCurrentActiveUser:
    """Test get_current_active_user dependency"""

    @patch('app.middleware.auth.db')
    async def test_get_current_active_user_success(self, mock_db):
        """Test that active user passes through"""
        # Mock database response
        mock_db.fetchrow = AsyncMock(return_value={"is_active": True})

        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="test@example.com",
            roles=["viewer"],
            permissions=["agents:read"],
            is_superuser=False
        )

        result = await get_current_active_user(current_user=auth_context)

        assert result == auth_context
        mock_db.fetchrow.assert_called_once()

    @patch('app.middleware.auth.db')
    async def test_get_current_active_user_inactive(self, mock_db):
        """Test that inactive user raises 403"""
        # Mock database response with inactive user
        mock_db.fetchrow = AsyncMock(return_value={"is_active": False})

        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="test@example.com",
            roles=["viewer"],
            permissions=["agents:read"],
            is_superuser=False
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=auth_context)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "inactive" in exc_info.value.detail.lower()

    @patch('app.middleware.auth.db')
    async def test_get_current_active_user_not_found(self, mock_db):
        """Test that non-existent user raises 403"""
        # Mock database response with no user
        mock_db.fetchrow = AsyncMock(return_value=None)

        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="test@example.com",
            roles=["viewer"],
            permissions=["agents:read"],
            is_superuser=False
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(current_user=auth_context)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    async def test_get_current_active_user_api_key(self):
        """Test that API key user (user_id='api-key') passes without DB check"""
        auth_context = AuthContext(
            user_id="api-key",
            tenant_id="tenant-456",
            email="api-key@system",
            roles=["api-key"],
            permissions=["agents:read"],
            is_superuser=False
        )

        result = await get_current_active_user(current_user=auth_context)

        assert result == auth_context
        # No DB call should be made for api-key users


@pytest.mark.unit
class TestRequirePermission:
    """Test require_permission dependency factory"""

    async def test_require_permission_success(self):
        """Test that user with permission passes"""
        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="test@example.com",
            roles=["viewer"],
            permissions=["agents:execute", "agents:read"],
            is_superuser=False
        )

        permission_checker = await require_permission("agents:execute")
        result = await permission_checker(current_user=auth_context)

        assert result == auth_context

    async def test_require_permission_missing(self):
        """Test that user without permission raises 403"""
        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="test@example.com",
            roles=["viewer"],
            permissions=["agents:read"],
            is_superuser=False
        )

        permission_checker = await require_permission("agents:delete")

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(current_user=auth_context)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "missing required permission" in exc_info.value.detail.lower()
        assert "agents:delete" in exc_info.value.detail

    async def test_require_permission_superuser_bypass(self):
        """Test that superuser bypasses permission check"""
        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="admin@example.com",
            roles=["admin"],
            permissions=[],  # Empty permissions
            is_superuser=True
        )

        permission_checker = await require_permission("agents:delete")
        result = await permission_checker(current_user=auth_context)

        assert result == auth_context

    async def test_require_permission_empty_permissions(self):
        """Test that user with no permissions fails check"""
        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="test@example.com",
            roles=["viewer"],
            permissions=[],
            is_superuser=False
        )

        permission_checker = await require_permission("agents:read")

        with pytest.raises(HTTPException) as exc_info:
            await permission_checker(current_user=auth_context)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.unit
class TestRequireRole:
    """Test require_role dependency factory"""

    async def test_require_role_success(self):
        """Test that user with role passes"""
        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="test@example.com",
            roles=["admin", "viewer"],
            permissions=["agents:read"],
            is_superuser=False
        )

        role_checker = await require_role("admin")
        result = await role_checker(current_user=auth_context)

        assert result == auth_context

    async def test_require_role_missing(self):
        """Test that user without role raises 403"""
        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="test@example.com",
            roles=["viewer"],
            permissions=["agents:read"],
            is_superuser=False
        )

        role_checker = await require_role("admin")

        with pytest.raises(HTTPException) as exc_info:
            await role_checker(current_user=auth_context)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "missing required role" in exc_info.value.detail.lower()
        assert "admin" in exc_info.value.detail

    async def test_require_role_superuser_bypass(self):
        """Test that superuser bypasses role check"""
        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="admin@example.com",
            roles=["viewer"],
            permissions=[],
            is_superuser=True
        )

        role_checker = await require_role("admin")
        result = await role_checker(current_user=auth_context)

        assert result == auth_context

    async def test_require_role_empty_roles(self):
        """Test that user with no roles fails check"""
        auth_context = AuthContext(
            user_id="user-123",
            tenant_id="tenant-456",
            email="test@example.com",
            roles=[],
            permissions=["agents:read"],
            is_superuser=False
        )

        role_checker = await require_role("viewer")

        with pytest.raises(HTTPException) as exc_info:
            await role_checker(current_user=auth_context)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.unit
class TestGetUserPermissions:
    """Test get_user_permissions helper"""

    @patch('app.middleware.auth.db')
    async def test_get_user_permissions_success(self, mock_db):
        """Test retrieving user permissions"""
        mock_db.fetch = AsyncMock(return_value=[
            {"name": "agents:read"},
            {"name": "agents:execute"},
            {"name": "workflows:create"}
        ])

        permissions = await get_user_permissions("user-123")

        assert len(permissions) == 3
        assert "agents:read" in permissions
        assert "agents:execute" in permissions
        assert "workflows:create" in permissions

    @patch('app.middleware.auth.db')
    async def test_get_user_permissions_empty(self, mock_db):
        """Test user with no permissions"""
        mock_db.fetch = AsyncMock(return_value=[])

        permissions = await get_user_permissions("user-123")

        assert permissions == []


@pytest.mark.unit
class TestGetUserRoles:
    """Test get_user_roles helper"""

    @patch('app.middleware.auth.db')
    async def test_get_user_roles_success(self, mock_db):
        """Test retrieving user roles"""
        mock_db.fetch = AsyncMock(return_value=[
            {"name": "admin"},
            {"name": "viewer"}
        ])

        roles = await get_user_roles("user-123")

        assert len(roles) == 2
        assert "admin" in roles
        assert "viewer" in roles

    @patch('app.middleware.auth.db')
    async def test_get_user_roles_empty(self, mock_db):
        """Test user with no roles"""
        mock_db.fetch = AsyncMock(return_value=[])

        roles = await get_user_roles("user-123")

        assert roles == []


@pytest.mark.unit
class TestAuthMiddleware:
    """Test AuthMiddleware class"""

    @patch('app.middleware.auth.JWTHandler')
    async def test_auth_middleware_with_jwt(self, mock_jwt_handler):
        """Test middleware extracts tenant_id from JWT"""
        mock_jwt_handler.verify_token.return_value = {
            "sub": "user-123",
            "tenant_id": "tenant-456"
        }

        # Mock app
        async def mock_app(scope, receive, send):
            assert scope["state"]["tenant_id"] == "tenant-456"
            assert scope["state"]["user_id"] == "user-123"

        middleware = AuthMiddleware(mock_app)

        # Mock scope
        scope = {
            "type": "http",
            "headers": [(b"authorization", b"Bearer valid.jwt.token")],
            "state": {}
        }

        await middleware(scope, None, None)

    @patch('app.middleware.auth.APIKeyHandler')
    async def test_auth_middleware_with_api_key(self, mock_api_key_handler):
        """Test middleware extracts tenant_id from API key"""
        mock_api_key_handler.validate_api_key = AsyncMock(return_value={
            "tenant_id": "tenant-456",
            "user_id": "user-123"
        })

        # Mock app
        async def mock_app(scope, receive, send):
            assert scope["state"]["tenant_id"] == "tenant-456"
            assert scope["state"]["user_id"] == "user-123"

        middleware = AuthMiddleware(mock_app)

        # Mock scope
        scope = {
            "type": "http",
            "headers": [(b"authorization", b"Bearer sk_test_validkey")],
            "state": {}
        }

        await middleware(scope, None, None)

    async def test_auth_middleware_without_auth_header(self):
        """Test middleware handles missing auth header"""
        # Mock app
        async def mock_app(scope, receive, send):
            # Should not have tenant_id or user_id
            assert "tenant_id" not in scope.get("state", {})

        middleware = AuthMiddleware(mock_app)

        # Mock scope without authorization
        scope = {
            "type": "http",
            "headers": [],
            "state": {}
        }

        await middleware(scope, None, None)

    async def test_auth_middleware_non_http(self):
        """Test middleware skips non-HTTP requests"""
        call_count = [0]

        # Mock app
        async def mock_app(scope, receive, send):
            call_count[0] += 1

        middleware = AuthMiddleware(mock_app)

        # Mock WebSocket scope
        scope = {
            "type": "websocket",
            "headers": []
        }

        await middleware(scope, None, None)

        assert call_count[0] == 1

    @patch('app.middleware.auth.JWTHandler')
    async def test_auth_middleware_invalid_token(self, mock_jwt_handler):
        """Test middleware handles invalid token gracefully"""
        mock_jwt_handler.verify_token.return_value = None

        # Mock app
        async def mock_app(scope, receive, send):
            # Should not have tenant_id
            assert "tenant_id" not in scope.get("state", {})

        middleware = AuthMiddleware(mock_app)

        # Mock scope with invalid token
        scope = {
            "type": "http",
            "headers": [(b"authorization", b"Bearer invalid.token")],
            "state": {}
        }

        await middleware(scope, None, None)
