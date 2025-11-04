"""
Integration tests for authentication routes.

Tests /auth/login, /auth/register, /auth/refresh endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestLoginEndpoint:
    """Test POST /auth/login"""

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login with correct credentials"""
        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert isinstance(data["expires_in"], int)
        assert data["expires_in"] > 0

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login fails with wrong password"""
        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login fails with nonexistent email"""
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SomePassword123!"
            }
        )

        assert response.status_code == 401
        assert "incorrect email or password" in response.json()["detail"].lower()

    async def test_login_inactive_user(self, client: AsyncClient, test_user):
        """Test login fails for inactive user"""
        from app.database import db

        # Deactivate user
        await db.execute(
            "UPDATE users SET is_active = false WHERE id = $1",
            test_user["id"]
        )

        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()

    async def test_login_inactive_tenant(self, client: AsyncClient, test_user, test_tenant):
        """Test login fails for user with inactive tenant"""
        from app.database import db

        # Deactivate tenant
        await db.execute(
            "UPDATE tenants SET is_active = false WHERE id = $1",
            test_tenant["id"]
        )

        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 401

    async def test_login_invalid_email_format(self, client: AsyncClient):
        """Test login with invalid email format"""
        response = await client.post(
            "/auth/login",
            json={
                "email": "not-an-email",
                "password": "Password123!"
            }
        )

        assert response.status_code == 422  # Pydantic validation error

    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing fields"""
        response = await client.post(
            "/auth/login",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 422

    async def test_login_empty_password(self, client: AsyncClient):
        """Test login with empty password"""
        response = await client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": ""
            }
        )

        assert response.status_code == 401

    async def test_login_updates_last_login(self, client: AsyncClient, test_user):
        """Test that login updates last_login_at"""
        from app.database import db

        # Get initial last_login_at
        before = await db.fetchval(
            "SELECT last_login_at FROM users WHERE id = $1",
            test_user["id"]
        )

        # Login
        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 200

        # Check last_login_at was updated
        after = await db.fetchval(
            "SELECT last_login_at FROM users WHERE id = $1",
            test_user["id"]
        )

        assert after is not None
        assert after > before if before else True

    async def test_login_creates_audit_log(self, client: AsyncClient, test_user):
        """Test that login creates audit log entry"""
        from app.database import db

        # Login
        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 200

        # Check audit log
        log_entry = await db.fetchrow(
            """
            SELECT * FROM audit_log
            WHERE user_id = $1 AND action = 'login'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            test_user["id"]
        )

        assert log_entry is not None
        assert log_entry["action"] == "login"
        assert log_entry["resource_type"] == "user"


@pytest.mark.integration
class TestRegisterEndpoint:
    """Test POST /auth/register"""

    async def test_register_success_new_tenant(self, client: AsyncClient):
        """Test successful registration creating new tenant"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "viewer" in data["roles"]
        assert "id" in data
        assert "tenant_id" in data

    async def test_register_success_existing_tenant(self, client: AsyncClient, test_tenant):
        """Test successful registration joining existing tenant"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User",
                "tenant_id": str(test_tenant["id"])
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["email"] == "newuser@example.com"
        assert data["tenant_id"] == str(test_tenant["id"])

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration fails with duplicate email"""
        response = await client.post(
            "/auth/register",
            json={
                "email": test_user["email"],  # Already exists
                "password": "SecurePass123!",
                "full_name": "Duplicate User"
            }
        )

        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration fails with weak password"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "weak",  # Too short
                "full_name": "New User"
            }
        )

        assert response.status_code == 422  # Pydantic validation

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration fails with invalid email"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )

        assert response.status_code == 422

    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration fails with missing required fields"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!"
                # Missing full_name
            }
        )

        assert response.status_code == 422

    async def test_register_creates_tenant(self, client: AsyncClient):
        """Test that registration creates a tenant"""
        from app.database import db

        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Check tenant was created
        tenant = await db.fetchrow(
            "SELECT * FROM tenants WHERE id = $1",
            data["tenant_id"]
        )

        assert tenant is not None
        assert tenant["is_active"] is True

    async def test_register_assigns_viewer_role(self, client: AsyncClient):
        """Test that registration assigns viewer role"""
        from app.database import db

        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Check role assignment
        role = await db.fetchrow(
            """
            SELECT r.name
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = $1
            """,
            data["id"]
        )

        assert role["name"] == "viewer"

    async def test_register_creates_audit_log(self, client: AsyncClient):
        """Test that registration creates audit log entry"""
        from app.database import db

        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )

        assert response.status_code == 201
        data = response.json()

        # Check audit log
        log_entry = await db.fetchrow(
            """
            SELECT * FROM audit_log
            WHERE user_id = $1 AND action = 'register'
            """,
            data["id"]
        )

        assert log_entry is not None


@pytest.mark.integration
class TestRefreshTokenEndpoint:
    """Test POST /auth/refresh"""

    async def test_refresh_token_success(self, client: AsyncClient, test_user, test_refresh_token):
        """Test successful token refresh"""
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": test_refresh_token}
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        # Should return same refresh token
        assert data["refresh_token"] == test_refresh_token

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test refresh fails with invalid token"""
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_refresh_token_wrong_type(self, client: AsyncClient, test_access_token):
        """Test refresh fails with access token instead of refresh token"""
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": test_access_token}
        )

        assert response.status_code == 401

    async def test_refresh_token_inactive_user(self, client: AsyncClient, test_user, test_refresh_token):
        """Test refresh fails for inactive user"""
        from app.database import db

        # Deactivate user
        await db.execute(
            "UPDATE users SET is_active = false WHERE id = $1",
            test_user["id"]
        )

        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": test_refresh_token}
        )

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()

    async def test_refresh_token_expired(self, client: AsyncClient, expired_token):
        """Test refresh fails with expired token"""
        response = await client.post(
            "/auth/refresh",
            json={"refresh_token": expired_token}
        )

        assert response.status_code == 401

    async def test_refresh_token_missing_field(self, client: AsyncClient):
        """Test refresh fails with missing refresh_token field"""
        response = await client.post(
            "/auth/refresh",
            json={}
        )

        assert response.status_code == 422


@pytest.mark.integration
class TestHealthEndpoint:
    """Test GET /health"""

    async def test_health_check_success(self, client: AsyncClient):
        """Test health check returns success"""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "auth"
        assert "database" in data

    async def test_health_check_no_auth_required(self, client: AsyncClient):
        """Test health check doesn't require authentication"""
        response = await client.get("/health")

        assert response.status_code == 200
        # Should work without any authorization header
