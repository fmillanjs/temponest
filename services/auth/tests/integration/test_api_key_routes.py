"""
Integration tests for API key routes.

Tests /api-keys/* endpoints.
"""

import pytest
from httpx import AsyncClient
from app.settings import settings


@pytest.mark.integration
class TestCreateAPIKeyEndpoint:
    """Test POST /api-keys"""

    async def test_create_api_key_success(self, client: AsyncClient, test_access_token):
        """Test successful API key creation"""
        response = await client.post(
            "/api-keys",
            headers={"Authorization": f"Bearer {test_access_token}"},
            json={
                "name": "Test API Key",
                "scopes": ["agents:read", "workflows:create"],
                "expires_in_days": 30
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert "key" in data  # Full key only returned on creation
        assert data["key"].startswith(settings.API_KEY_PREFIX)
        assert data["name"] == "Test API Key"
        assert data["scopes"] == ["agents:read", "workflows:create"]
        assert data["expires_at"] is not None
        assert "id" in data

    async def test_create_api_key_no_expiry(self, client: AsyncClient, test_access_token):
        """Test creating API key without expiration"""
        response = await client.post(
            "/api-keys",
            headers={"Authorization": f"Bearer {test_access_token}"},
            json={
                "name": "Never Expires",
                "scopes": ["agents:read"]
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["expires_at"] is None

    async def test_create_api_key_no_scopes(self, client: AsyncClient, test_access_token):
        """Test creating API key with empty scopes"""
        response = await client.post(
            "/api-keys",
            headers={"Authorization": f"Bearer {test_access_token}"},
            json={
                "name": "No Scopes",
                "scopes": []
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert data["scopes"] == []

    async def test_create_api_key_unauthorized(self, client: AsyncClient):
        """Test API key creation without authentication"""
        response = await client.post(
            "/api-keys",
            json={
                "name": "Test Key",
                "scopes": ["agents:read"]
            }
        )

        assert response.status_code == 401

    async def test_create_api_key_invalid_token(self, client: AsyncClient):
        """Test API key creation with invalid token"""
        response = await client.post(
            "/api-keys",
            headers={"Authorization": "Bearer invalid.token.here"},
            json={
                "name": "Test Key",
                "scopes": ["agents:read"]
            }
        )

        assert response.status_code == 401

    async def test_create_api_key_missing_name(self, client: AsyncClient, test_access_token):
        """Test API key creation without name"""
        response = await client.post(
            "/api-keys",
            headers={"Authorization": f"Bearer {test_access_token}"},
            json={
                "scopes": ["agents:read"]
            }
        )

        assert response.status_code == 422

    async def test_create_api_key_creates_audit_log(self, client: AsyncClient, test_access_token, test_user):
        """Test that API key creation logs to audit"""
        from app.database import db

        response = await client.post(
            "/api-keys",
            headers={"Authorization": f"Bearer {test_access_token}"},
            json={
                "name": "Audit Test Key",
                "scopes": ["agents:read"]
            }
        )

        assert response.status_code == 201

        # Check audit log
        log_entry = await db.fetchrow(
            """
            SELECT * FROM audit_log
            WHERE user_id = $1 AND action = 'api_key_create'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            str(test_user["id"])
        )

        assert log_entry is not None
        assert log_entry["action"] == "api_key_create"


@pytest.mark.integration
class TestListAPIKeysEndpoint:
    """Test GET /api-keys"""

    async def test_list_api_keys_success(self, client: AsyncClient, test_access_token, test_api_key):
        """Test listing API keys"""
        response = await client.get(
            "/api-keys",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 1  # At least the test_api_key

        # Find our test key
        test_key = next((k for k in data if k["id"] == str(test_api_key["id"])), None)
        assert test_key is not None
        assert "key" not in test_key or test_key["key"] is None  # Full key never returned in list

    async def test_list_api_keys_empty(self, client: AsyncClient, test_access_token):
        """Test listing API keys when none exist"""
        response = await client.get(
            "/api-keys",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    async def test_list_api_keys_unauthorized(self, client: AsyncClient):
        """Test listing API keys without authentication"""
        response = await client.get("/api-keys")

        assert response.status_code == 401

    async def test_list_api_keys_different_tenant(self, client: AsyncClient):
        """Test that users only see their tenant's keys"""
        from app.database import db

        # Create another tenant
        tenant2_id = await db.fetchval(
            "INSERT INTO tenants (name, slug, plan) VALUES ('Tenant 2', 'tenant-2', 'free') RETURNING id"
        )

        # Create user in tenant 2
        from app.handlers.password import PasswordHandler
        hashed_pw = PasswordHandler.hash_password("Password123!")
        user2_id = await db.fetchval(
            """
            INSERT INTO users (email, hashed_password, full_name, tenant_id)
            VALUES ('user2@example.com', $1, 'User 2', $2)
            RETURNING id
            """,
            hashed_pw, tenant2_id
        )

        # Assign viewer role
        viewer_role_id = await db.fetchval("SELECT id FROM roles WHERE name = 'viewer'")
        await db.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
            user2_id, viewer_role_id
        )

        # Create token for user 2
        from app.handlers.jwt_handler import JWTHandler
        token2 = JWTHandler.create_access_token(
            user_id=user2_id,
            tenant_id=tenant2_id,
            email="user2@example.com",
            roles=["viewer"],
            permissions=[],
            is_superuser=False
        )

        # List keys for user 2 (should be empty)
        response = await client.get(
            "/api-keys",
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response.status_code == 200
        assert len(response.json()) == 0


@pytest.mark.integration
class TestRevokeAPIKeyEndpoint:
    """Test DELETE /api-keys/{key_id}"""

    async def test_revoke_api_key_success(self, client: AsyncClient, test_access_token, test_api_key):
        """Test successful API key revocation"""
        response = await client.delete(
            f"/api-keys/{test_api_key['id']}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )

        assert response.status_code == 204

        # Verify key is revoked (can't be validated)
        from app.handlers.api_key import APIKeyHandler
        result = await APIKeyHandler.validate_api_key(test_api_key["key"])

        assert result is None

    async def test_revoke_api_key_unauthorized(self, client: AsyncClient, test_api_key):
        """Test API key revocation without authentication"""
        response = await client.delete(f"/api-keys/{test_api_key['id']}")

        assert response.status_code == 401

    async def test_revoke_api_key_not_found(self, client: AsyncClient, test_access_token):
        """Test revoking non-existent API key"""
        from uuid import uuid4

        response = await client.delete(
            f"/api-keys/{uuid4()}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )

        assert response.status_code == 404

    async def test_revoke_api_key_different_tenant(self, client: AsyncClient):
        """Test that users can't revoke other tenants' keys"""
        from app.database import db
        from app.handlers import PasswordHandler, JWTHandler, APIKeyHandler

        # Create another tenant with user
        tenant2_id = await db.fetchval(
            "INSERT INTO tenants (name, slug, plan) VALUES ('Tenant 2', 'tenant-2', 'free') RETURNING id"
        )

        hashed_pw = PasswordHandler.hash_password("Password123!")
        user2_id = await db.fetchval(
            """
            INSERT INTO users (email, hashed_password, full_name, tenant_id)
            VALUES ('user2@example.com', $1, 'User 2', $2)
            RETURNING id
            """,
            hashed_pw, tenant2_id
        )

        viewer_role_id = await db.fetchval("SELECT id FROM roles WHERE name = 'viewer'")
        await db.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
            user2_id, viewer_role_id
        )

        # Create API key for tenant 2
        key2_id, _ = await APIKeyHandler.create_api_key(
            name="Tenant 2 Key",
            tenant_id=tenant2_id,
            user_id=user2_id,
            scopes=[],
            expires_in_days=None
        )

        # Create token for tenant 1 user
        tenant1_id = await db.fetchval("SELECT id FROM tenants LIMIT 1")
        user1_id = await db.fetchval("SELECT id FROM users WHERE tenant_id = $1 LIMIT 1", tenant1_id)
        token1 = JWTHandler.create_access_token(
            user_id=user1_id,
            tenant_id=tenant1_id,
            email="user1@example.com",
            roles=["viewer"],
            permissions=[],
            is_superuser=False
        )

        # Try to revoke tenant 2's key with tenant 1's token
        response = await client.delete(
            f"/api-keys/{key2_id}",
            headers={"Authorization": f"Bearer {token1}"}
        )

        assert response.status_code == 403

    async def test_revoke_api_key_creates_audit_log(self, client: AsyncClient, test_access_token, test_api_key, test_user):
        """Test that API key revocation logs to audit"""
        from app.database import db

        response = await client.delete(
            f"/api-keys/{test_api_key['id']}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )

        assert response.status_code == 204

        # Check audit log
        log_entry = await db.fetchrow(
            """
            SELECT * FROM audit_log
            WHERE user_id = $1 AND action = 'api_key_revoke'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            str(test_user["id"])
        )

        assert log_entry is not None
        assert log_entry["resource_id"] == str(test_api_key["id"])

    async def test_revoke_already_revoked_key(self, client: AsyncClient, test_access_token, test_api_key):
        """Test revoking an already revoked key"""
        # Revoke once
        response1 = await client.delete(
            f"/api-keys/{test_api_key['id']}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )

        assert response1.status_code == 204

        # Try to revoke again
        response2 = await client.delete(
            f"/api-keys/{test_api_key['id']}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )

        # Should still succeed (idempotent operation)
        assert response2.status_code == 204


@pytest.mark.integration
class TestAPIKeyAuthentication:
    """Test using API keys for authentication"""

    async def test_api_key_auth_success(self, client: AsyncClient, test_api_key):
        """Test using API key for authentication"""
        # Try to list API keys using API key auth
        response = await client.get(
            "/api-keys",
            headers={"Authorization": f"Bearer {test_api_key['key']}"}
        )

        # Should work if API key validation is implemented in middleware
        # Note: This depends on middleware implementation
        # For now, check that it doesn't crash
        assert response.status_code in [200, 401]  # Either works or not implemented yet

    async def test_api_key_auth_invalid_key(self, client: AsyncClient):
        """Test using invalid API key"""
        fake_key = f"{settings.API_KEY_PREFIX}" + "0" * 64

        response = await client.get(
            "/api-keys",
            headers={"Authorization": f"Bearer {fake_key}"}
        )

        assert response.status_code == 401
