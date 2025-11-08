"""
End-to-end tests for complete authentication workflows.

Tests full user journeys from registration through authentication and authorization.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


@pytest.mark.e2e
class TestCompleteUserJourney:
    """Test complete user lifecycle from registration to authenticated access"""

    async def test_complete_registration_to_access_flow(self, client: AsyncClient, clean_database):
        """
        Test complete flow: Register -> Login -> Use Token -> Refresh Token
        """
        # Step 1: Register new user
        register_response = await client.post(
            "/auth/register",
            json={
                "email": "journey@example.com",
                "password": "SecurePassword123!",
                "full_name": "Journey User"
            }
        )

        assert register_response.status_code == 201
        user_data = register_response.json()

        assert user_data["email"] == "journey@example.com"
        assert user_data["full_name"] == "Journey User"
        assert user_data["is_active"] is True
        assert "viewer" in user_data["roles"]
        user_id = user_data["id"]
        tenant_id = user_data["tenant_id"]

        # Step 2: Login with new credentials
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "journey@example.com",
                "password": "SecurePassword123!"
            }
        )

        assert login_response.status_code == 200
        tokens = login_response.json()

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Step 3: Use access token to access protected endpoint (verify token works)
        from app.handlers import JWTHandler
        payload = JWTHandler.verify_token(access_token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["tenant_id"] == tenant_id
        assert payload["email"] == "journey@example.com"
        assert "viewer" in payload["roles"]

        # Step 4: Refresh token to get new access token
        refresh_response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()

        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != access_token  # New token
        new_access_token = new_tokens["access_token"]

        # Step 5: Verify new token works
        new_payload = JWTHandler.verify_token(new_access_token)
        assert new_payload is not None
        assert new_payload["sub"] == user_id

    async def test_multi_tenant_user_flow(self, client: AsyncClient, test_tenant):
        """
        Test user joining existing tenant
        """
        # Step 1: Register user in existing tenant
        register_response = await client.post(
            "/auth/register",
            json={
                "email": "tenant_user@example.com",
                "password": "SecurePassword123!",
                "full_name": "Tenant User",
                "tenant_id": str(test_tenant["id"])
            }
        )

        assert register_response.status_code == 201
        user_data = register_response.json()

        assert user_data["tenant_id"] == str(test_tenant["id"])
        assert user_data["tenant_name"] == test_tenant["name"]

        # Step 2: Login and verify tenant context
        login_response = await client.post(
            "/auth/login",
            json={
                "email": "tenant_user@example.com",
                "password": "SecurePassword123!"
            }
        )

        assert login_response.status_code == 200
        tokens = login_response.json()

        from app.handlers import JWTHandler
        payload = JWTHandler.verify_token(tokens["access_token"])

        assert payload["tenant_id"] == str(test_tenant["id"])


@pytest.mark.e2e
class TestAPIKeyWorkflow:
    """Test complete API key authentication workflow"""

    async def test_api_key_creation_and_usage_flow(self, client: AsyncClient, test_user, test_access_token):
        """
        Test flow: Create API key -> Use for authentication
        """
        # Step 1: Create API key using authenticated endpoint
        create_response = await client.post(
            "/api-keys/",
            headers={"Authorization": f"Bearer {test_access_token}"},
            json={
                "name": "E2E Test Key",
                "scopes": ["agents:read", "agents:execute"],
                "expires_in_days": 30
            }
        )

        assert create_response.status_code == 201
        api_key_data = create_response.json()

        assert "key" in api_key_data  # Full key only returned on creation
        assert api_key_data["name"] == "E2E Test Key"
        api_key = api_key_data["key"]

        # Step 2: Use API key for authentication (in middleware)
        # Simulate how API key would be used
        from app.handlers import APIKeyHandler
        validated = await APIKeyHandler.validate_api_key(api_key)

        assert validated is not None
        assert validated["tenant_id"] == str(test_user["tenant_id"])
        assert "agents:read" in validated["scopes"]

        # Step 3: List API keys
        list_response = await client.get(
            "/api-keys/",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )

        assert list_response.status_code == 200
        keys = list_response.json()

        assert len(keys) > 0
        # Find our key by prefix
        our_key = next((k for k in keys if k["name"] == "E2E Test Key"), None)
        assert our_key is not None
        assert "key" not in our_key  # Full key not shown in list

        # Step 4: Delete API key
        delete_response = await client.delete(
            f"/api-keys/{api_key_data['id']}",
            headers={"Authorization": f"Bearer {test_access_token}"}
        )

        assert delete_response.status_code == 204

        # Step 5: Verify API key no longer works
        validated_after_delete = await APIKeyHandler.validate_api_key(api_key)
        assert validated_after_delete is None


@pytest.mark.e2e
class TestSecurityFlows:
    """Test security-related workflows"""

    async def test_account_lockout_flow(self, client: AsyncClient, test_user):
        """
        Test that multiple failed login attempts trigger rate limiting
        """
        # Attempt multiple failed logins
        failed_attempts = 0
        rate_limited = False

        for i in range(10):
            response = await client.post(
                "/auth/login",
                json={
                    "email": test_user["email"],
                    "password": "WrongPassword123!"
                }
            )

            if response.status_code == 429:
                rate_limited = True
                break
            elif response.status_code == 401:
                failed_attempts += 1

        # Should hit rate limit before 10 attempts (limit is 5/minute)
        assert rate_limited or failed_attempts <= 5

    async def test_token_expiry_and_refresh_flow(self, client: AsyncClient, test_user):
        """
        Test token expiration and refresh workflow
        """
        # Step 1: Login and get tokens
        login_response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Step 2: Verify token is valid
        from app.handlers import JWTHandler
        payload = JWTHandler.verify_token(access_token)
        assert payload is not None

        # Step 3: Token should have expiration
        assert "exp" in payload
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()
        assert exp_time > now  # Token not yet expired

        # Step 4: Use refresh token before access token expires
        refresh_response = await client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        assert new_tokens["access_token"] != access_token

    async def test_inactive_user_cannot_login(self, client: AsyncClient, test_user):
        """
        Test that deactivated user cannot login
        """
        from app.database import db

        # Step 1: Verify user can login initially
        login_response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )
        assert login_response.status_code == 200

        # Step 2: Deactivate user
        await db.execute(
            "UPDATE users SET is_active = false WHERE id = $1",
            test_user["id"]
        )

        # Step 3: Attempt login again
        login_response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        # Should be forbidden
        assert login_response.status_code == 403
        assert "inactive" in login_response.json()["detail"].lower()

        # Cleanup: Reactivate user
        await db.execute(
            "UPDATE users SET is_active = true WHERE id = $1",
            test_user["id"]
        )


@pytest.mark.e2e
class TestAuditLogging:
    """Test that authentication events are logged"""

    async def test_registration_creates_audit_log(self, client: AsyncClient, clean_database):
        """Test that user registration is logged"""
        from app.database import db

        # Register user
        response = await client.post(
            "/auth/register",
            json={
                "email": "audit_test@example.com",
                "password": "SecurePass123!",
                "full_name": "Audit Test"
            }
        )

        assert response.status_code == 201
        user_data = response.json()

        # Check audit log
        log = await db.fetchrow(
            """
            SELECT * FROM audit_log
            WHERE user_id = $1 AND action = 'register'
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            user_data["id"]
        )

        assert log is not None
        assert log["action"] == "register"
        assert log["resource_type"] == "user"

    async def test_login_creates_audit_log(self, client: AsyncClient, test_user):
        """Test that login is logged"""
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
        log = await db.fetchrow(
            """
            SELECT * FROM audit_log
            WHERE user_id = $1 AND action = 'login'
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            test_user["id"]
        )

        assert log is not None
        assert log["action"] == "login"

    async def test_api_key_creation_creates_audit_log(self, client: AsyncClient, test_user, test_access_token):
        """Test that API key creation is logged"""
        from app.database import db

        # Create API key
        response = await client.post(
            "/api-keys/",
            headers={"Authorization": f"Bearer {test_access_token}"},
            json={
                "name": "Audit Test Key",
                "scopes": ["agents:read"]
            }
        )

        assert response.status_code == 201

        # Check audit log
        log = await db.fetchrow(
            """
            SELECT * FROM audit_log
            WHERE user_id = $1 AND action = 'api_key_create'
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            test_user["id"]
        )

        assert log is not None
        assert log["action"] == "api_key_create"


@pytest.mark.e2e
class TestPermissionBasedAccess:
    """Test permission-based access control in real scenarios"""

    async def test_viewer_cannot_perform_admin_actions(self, client: AsyncClient, test_user, test_access_token):
        """Test that viewer role cannot perform admin operations"""
        from app.handlers import JWTHandler

        # Verify user is viewer
        payload = JWTHandler.verify_token(test_access_token)
        assert "viewer" in payload["roles"]
        assert payload["is_superuser"] is False

        # In a real scenario, viewer trying to delete something would fail
        # This would be tested with actual protected endpoints in other services
        # For now, verify the token has limited permissions
        permissions = payload.get("permissions", [])

        # Viewer should not have delete permissions
        delete_permissions = [p for p in permissions if "delete" in p.lower()]
        assert len(delete_permissions) == 0

    async def test_admin_can_perform_all_actions(self, client: AsyncClient, test_admin_user, test_admin_token):
        """Test that admin role has comprehensive permissions"""
        from app.handlers import JWTHandler

        # Verify user is admin
        payload = JWTHandler.verify_token(test_admin_token)
        assert "admin" in payload["roles"]
        assert payload["is_superuser"] is True

        # Admin should have extensive permissions
        permissions = payload.get("permissions", [])
        assert len(permissions) > 0

        # Or superuser flag should allow bypass
        assert payload["is_superuser"] is True


@pytest.mark.e2e
class TestCrossServiceAuthentication:
    """Test authentication flow across services"""

    async def test_jwt_token_valid_for_other_services(self, client: AsyncClient, test_user):
        """Test that JWT token from auth service can be used by other services"""
        # Step 1: Get token from auth service
        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 200
        tokens = response.json()
        access_token = tokens["access_token"]

        # Step 2: Verify token structure is valid for cross-service use
        from app.handlers import JWTHandler
        payload = JWTHandler.verify_token(access_token)

        # Should contain all necessary claims for other services
        required_claims = ["sub", "tenant_id", "email", "roles", "permissions"]
        for claim in required_claims:
            assert claim in payload

        # Tenant ID should be present for multi-tenant isolation
        assert payload["tenant_id"] is not None

    async def test_api_key_valid_for_service_to_service_auth(self, test_api_key):
        """Test that API key can authenticate service-to-service calls"""
        from app.handlers import APIKeyHandler

        # Validate API key
        validated = await APIKeyHandler.validate_api_key(test_api_key["key"])

        assert validated is not None
        assert validated["tenant_id"] == str(test_api_key["tenant_id"])
        assert isinstance(validated["scopes"], list)

        # API key should work without user context
        # This enables service-to-service authentication
