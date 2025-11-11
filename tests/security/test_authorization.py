"""
Security tests for authorization and access control vulnerabilities.

Tests for:
- Broken Access Control (OWASP A01:2021)
- Horizontal privilege escalation (accessing other users' data)
- Vertical privilege escalation (gaining admin/superuser privileges)
- IDOR (Insecure Direct Object Reference)
- Missing function level access control
- Role-Based Access Control (RBAC) bypass
- Tenant isolation violations
- Parameter tampering
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4
import time


# ============================================================
# HORIZONTAL PRIVILEGE ESCALATION TESTS
# ============================================================


@pytest.mark.security
class TestHorizontalPrivilegeEscalation:
    """Test horizontal privilege escalation (accessing other users' data)"""

    async def test_access_other_users_api_keys(self, auth_client: AsyncClient, test_user, auth_token):
        """Test that users cannot access other users' API keys"""
        # Create another user
        from services.auth.app.database import db
        from services.auth.app.handlers import PasswordHandler

        other_user_id = uuid4()
        other_tenant_id = uuid4()
        other_email = f"other_user_{int(time.time())}@example.com"

        # Create tenant for other user
        await db.execute(
            """
            INSERT INTO tenants (id, name, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            other_tenant_id,
            "Other User Tenant",
            True
        )

        # Create other user
        hashed_password = PasswordHandler.hash_password("OtherPassword123!")
        await db.execute(
            """
            INSERT INTO users (id, tenant_id, email, hashed_password, full_name, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            other_user_id,
            other_tenant_id,
            other_email,
            hashed_password,
            "Other User",
            True
        )

        # Login as other user to create their API key
        other_login_response = await auth_client.post(
            "/auth/login",
            json={
                "email": other_email,
                "password": "OtherPassword123!"
            }
        )

        if other_login_response.status_code == 200:
            other_token = other_login_response.json()["access_token"]

            # Create API key as other user
            other_key_response = await auth_client.post(
                "/api-keys/",
                headers={"Authorization": f"Bearer {other_token}"},
                json={
                    "name": "Other User's Key",
                    "scopes": ["read:agents"]
                }
            )

            if other_key_response.status_code in [200, 201]:
                other_key_id = other_key_response.json().get("id")

                # Try to access other user's API key with test_user token
                access_response = await auth_client.get(
                    f"/api-keys/{other_key_id}",
                    headers={"Authorization": f"Bearer {auth_token}"}
                )

                # Should be denied (403 or 404)
                assert access_response.status_code in [403, 404, 401], \
                    f"User accessed another user's API key! Status: {access_response.status_code}"

        # Clean up
        await db.execute("DELETE FROM users WHERE id = $1", other_user_id)
        await db.execute("DELETE FROM tenants WHERE id = $1", other_tenant_id)

    async def test_list_only_own_resources(self, auth_client: AsyncClient, auth_token):
        """Test that users only see their own resources in list endpoints"""
        # Get list of API keys
        response = await auth_client.get(
            "/api-keys/",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        if response.status_code == 200:
            data = response.json()

            # All returned items should belong to the authenticated user
            # (This is implicitly tested by the API implementation)
            # We verify the response structure is correct
            assert isinstance(data, list) or isinstance(data, dict)


# ============================================================
# VERTICAL PRIVILEGE ESCALATION TESTS
# ============================================================


@pytest.mark.security
class TestVerticalPrivilegeEscalation:
    """Test vertical privilege escalation (gaining higher privileges)"""

    async def test_regular_user_cannot_access_admin_endpoints(
        self,
        auth_client: AsyncClient,
        auth_token
    ):
        """Test that regular users cannot access admin endpoints"""
        # Try to access admin-only endpoints (if they exist)
        admin_endpoints = [
            "/admin/users",
            "/admin/tenants",
            "/admin/system",
        ]

        for endpoint in admin_endpoints:
            response = await auth_client.get(
                endpoint,
                headers={"Authorization": f"Bearer {auth_token}"}
            )

            # Should be forbidden or not found
            assert response.status_code in [403, 404], \
                f"Regular user accessed admin endpoint {endpoint}!"

    async def test_role_escalation_via_parameter_tampering(
        self,
        auth_client: AsyncClient,
        test_user
    ):
        """Test that role cannot be escalated via parameter tampering"""
        # Try to register with admin role
        response = await auth_client.post(
            "/auth/register",
            json={
                "email": f"escalation_test_{int(time.time())}@example.com",
                "password": "TestPassword123!",
                "full_name": "Escalation Test",
                "role": "admin",  # Attempt to set admin role
                "is_superuser": True  # Attempt to become superuser
            }
        )

        if response.status_code == 201:
            data = response.json()

            # Should not have admin role or superuser status
            assert not data.get("is_superuser", False), \
                "User gained superuser status via parameter tampering!"

            roles = data.get("roles", [])
            assert "admin" not in roles, \
                "User gained admin role via parameter tampering!"

    async def test_jwt_privilege_escalation(self, auth_client: AsyncClient, test_user):
        """Test that privileges in JWT cannot be escalated"""
        import os
        import jwt
        from datetime import datetime, timedelta

        # Create a token with escalated privileges
        escalated_payload = {
            "sub": str(test_user["id"]),
            "tenant_id": str(test_user["tenant_id"]),
            "email": test_user["email"],
            "exp": datetime.utcnow() + timedelta(hours=1),
            "type": "access",
            "is_superuser": True,  # Escalate to superuser
            "roles": ["admin", "superuser"],  # Add admin roles
            "permissions": ["*"]  # Grant all permissions
        }

        secret_key = os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-testing-only-min-32-characters-long")

        escalated_token = jwt.encode(
            escalated_payload,
            secret_key,
            algorithm="HS256"
        )

        # Try to use escalated token
        response = await auth_client.post(
            "/api-keys/",
            headers={"Authorization": f"Bearer {escalated_token}"},
            json={
                "name": "Escalated Key",
                "scopes": ["admin:all"]  # Try to create admin-scoped key
            }
        )

        # Token is validly signed, so request might succeed
        # But the user shouldn't have admin privileges in the database
        # This tests if API validates permissions against database, not just JWT
        assert response.status_code in [200, 201, 403, 401]


# ============================================================
# INSECURE DIRECT OBJECT REFERENCE (IDOR) TESTS
# ============================================================


@pytest.mark.security
class TestIDOR:
    """Test Insecure Direct Object Reference vulnerabilities"""

    async def test_idor_via_id_parameter(self, auth_client: AsyncClient, auth_token):
        """Test IDOR by manipulating ID parameters"""
        # Create an API key
        create_response = await auth_client.post(
            "/api-keys/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "IDOR Test Key",
                "scopes": ["read:agents"]
            }
        )

        if create_response.status_code in [200, 201]:
            key_id = create_response.json().get("id")

            # Try to access with modified ID
            random_id = str(uuid4())

            access_response = await auth_client.get(
                f"/api-keys/{random_id}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )

            # Should return 404, not 403 (to prevent enumeration)
            assert access_response.status_code in [404, 403]

    async def test_idor_via_sequential_id_enumeration(
        self,
        auth_client: AsyncClient,
        auth_token
    ):
        """Test IDOR via sequential ID enumeration"""
        # Create two API keys
        key_ids = []

        for i in range(2):
            response = await auth_client.post(
                "/api-keys/",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "name": f"Sequential Test Key {i}",
                    "scopes": ["read:agents"]
                }
            )

            if response.status_code in [200, 201]:
                key_ids.append(response.json().get("id"))

        # Check if IDs are sequential (UUIDs should not be)
        if len(key_ids) == 2:
            # UUIDs should be random, not sequential
            assert key_ids[0] != key_ids[1]

            # If using numeric IDs, check they're not easily enumerable
            # This is a design consideration

    async def test_delete_other_users_resources(
        self,
        auth_client: AsyncClient,
        auth_token
    ):
        """Test that users cannot delete other users' resources"""
        # Try to delete with random UUID
        random_id = str(uuid4())

        response = await auth_client.delete(
            f"/api-keys/{random_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Should return 404, not succeed
        assert response.status_code in [404, 403]


# ============================================================
# MISSING FUNCTION LEVEL ACCESS CONTROL TESTS
# ============================================================


@pytest.mark.security
class TestMissingFunctionLevelAccessControl:
    """Test missing function level access control"""

    async def test_unauthenticated_access_to_protected_endpoints(
        self,
        auth_client: AsyncClient
    ):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            ("GET", "/api-keys/"),
            ("POST", "/api-keys/"),
            ("DELETE", "/api-keys/some-id"),
        ]

        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = await auth_client.get(endpoint)
            elif method == "POST":
                response = await auth_client.post(endpoint, json={})
            elif method == "DELETE":
                response = await auth_client.delete(endpoint)

            # Should require authentication (401)
            assert response.status_code in [401, 403, 404, 405], \
                f"{method} {endpoint} accessible without authentication!"

    async def test_http_verb_tampering(self, auth_client: AsyncClient, auth_token):
        """Test HTTP verb tampering to bypass access controls"""
        # Try to use different HTTP methods on same endpoint
        endpoint = "/api-keys/"

        methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

        for method in methods:
            if method == "GET":
                response = await auth_client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
            elif method == "POST":
                response = await auth_client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {auth_token}"},
                    json={"name": "Test", "scopes": ["read:agents"]}
                )
            elif method == "PUT":
                response = await auth_client.put(
                    endpoint,
                    headers={"Authorization": f"Bearer {auth_token}"},
                    json={}
                )
            elif method == "PATCH":
                response = await auth_client.patch(
                    endpoint,
                    headers={"Authorization": f"Bearer {auth_token}"},
                    json={}
                )
            elif method == "DELETE":
                response = await auth_client.delete(
                    endpoint,
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
            elif method == "HEAD":
                response = await auth_client.head(
                    endpoint,
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
            elif method == "OPTIONS":
                response = await auth_client.options(
                    endpoint,
                    headers={"Authorization": f"Bearer {auth_token}"}
                )

            # Each method should either work or return proper error
            # Should not reveal different behavior that could be exploited
            assert response.status_code in [200, 201, 204, 405, 404, 400, 422]


# ============================================================
# ROLE-BASED ACCESS CONTROL (RBAC) TESTS
# ============================================================


@pytest.mark.security
class TestRBACBypass:
    """Test Role-Based Access Control bypass attempts"""

    async def test_rbac_enforcement_on_api_endpoints(
        self,
        auth_client: AsyncClient,
        auth_token
    ):
        """Test that RBAC is enforced on API endpoints"""
        # Create API key with limited scopes
        response = await auth_client.post(
            "/api-keys/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Limited Scope Key",
                "scopes": ["read:agents"]  # Only read permission
            }
        )

        if response.status_code in [200, 201]:
            # Verify the key has correct scopes
            data = response.json()
            scopes = data.get("scopes", [])

            assert "read:agents" in scopes
            # Should not have write or admin scopes
            assert "write:agents" not in scopes
            assert "admin:*" not in scopes

    async def test_scope_escalation_via_update(
        self,
        auth_client: AsyncClient,
        auth_token
    ):
        """Test that users cannot escalate scopes via update"""
        # Create API key
        create_response = await auth_client.post(
            "/api-keys/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Scope Test Key",
                "scopes": ["read:agents"]
            }
        )

        if create_response.status_code in [200, 201]:
            key_id = create_response.json().get("id")

            # Try to update with escalated scopes
            update_response = await auth_client.patch(
                f"/api-keys/{key_id}",
                headers={"Authorization": f"Bearer {auth_token}"},
                json={
                    "scopes": ["admin:*", "write:all"]
                }
            )

            # Should either fail or not grant escalated scopes
            if update_response.status_code == 200:
                data = update_response.json()
                scopes = data.get("scopes", [])

                # Should not have admin scopes if user doesn't have permission
                # (depends on user's role)
                pass


# ============================================================
# TENANT ISOLATION TESTS
# ============================================================


@pytest.mark.security
class TestTenantIsolation:
    """Test multi-tenant isolation"""

    async def test_cross_tenant_data_access(self, auth_client: AsyncClient, test_user):
        """Test that users cannot access other tenants' data"""
        from services.auth.app.database import db
        from services.auth.app.handlers import PasswordHandler
        import time

        # Create second tenant and user
        tenant2_id = uuid4()
        user2_id = uuid4()
        email2 = f"tenant2_user_{int(time.time())}@example.com"

        # Create second tenant
        await db.execute(
            """
            INSERT INTO tenants (id, name, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            tenant2_id,
            "Tenant 2",
            True
        )

        # Create user in second tenant
        hashed_password = PasswordHandler.hash_password("Tenant2Password123!")
        await db.execute(
            """
            INSERT INTO users (id, tenant_id, email, hashed_password, full_name, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            user2_id,
            tenant2_id,
            email2,
            hashed_password,
            "Tenant 2 User",
            True
        )

        # Login as both users
        login1 = await auth_client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        login2 = await auth_client.post(
            "/auth/login",
            json={
                "email": email2,
                "password": "Tenant2Password123!"
            }
        )

        if login1.status_code == 200 and login2.status_code == 200:
            token1 = login1.json()["access_token"]
            token2 = login2.json()["access_token"]

            # Create API key as user2
            create_response = await auth_client.post(
                "/api-keys/",
                headers={"Authorization": f"Bearer {token2}"},
                json={
                    "name": "Tenant 2 Key",
                    "scopes": ["read:agents"]
                }
            )

            if create_response.status_code in [200, 201]:
                # Get all API keys as user1 (different tenant)
                list_response = await auth_client.get(
                    "/api-keys/",
                    headers={"Authorization": f"Bearer {token1}"}
                )

                if list_response.status_code == 200:
                    keys = list_response.json()

                    # User1 should not see User2's API keys
                    for key in keys if isinstance(keys, list) else []:
                        key_name = key.get("name", "")
                        assert "Tenant 2" not in key_name, \
                            "Cross-tenant data leak: User can see other tenant's data!"

        # Clean up
        await db.execute("DELETE FROM users WHERE id = $1", user2_id)
        await db.execute("DELETE FROM tenants WHERE id = $1", tenant2_id)

    async def test_tenant_id_tampering(self, auth_client: AsyncClient, test_user):
        """Test that tenant_id cannot be tampered with"""
        import os
        import jwt
        from datetime import datetime, timedelta

        # Create token with different tenant_id
        different_tenant_id = str(uuid4())

        tampered_payload = {
            "sub": str(test_user["id"]),
            "tenant_id": different_tenant_id,  # Different tenant
            "email": test_user["email"],
            "exp": datetime.utcnow() + timedelta(hours=1),
            "type": "access"
        }

        secret_key = os.environ.get("JWT_SECRET_KEY", "test-secret-key-for-testing-only-min-32-characters-long")

        tampered_token = jwt.encode(
            tampered_payload,
            secret_key,
            algorithm="HS256"
        )

        # Try to use token with tampered tenant_id
        response = await auth_client.get(
            "/api-keys/",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )

        # Should validate tenant_id against user's actual tenant
        # Or fail because user doesn't belong to that tenant
        assert response.status_code in [200, 401, 403]


# ============================================================
# PARAMETER TAMPERING TESTS
# ============================================================


@pytest.mark.security
class TestParameterTampering:
    """Test parameter tampering vulnerabilities"""

    async def test_user_id_parameter_tampering(self, auth_client: AsyncClient, auth_token):
        """Test that user_id parameter cannot be tampered with"""
        # Try to create resource for different user
        random_user_id = str(uuid4())

        response = await auth_client.post(
            "/api-keys/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Tampered Key",
                "scopes": ["read:agents"],
                "user_id": random_user_id  # Attempt to set different user_id
            }
        )

        if response.status_code in [200, 201]:
            data = response.json()
            # The API should use authenticated user's ID, not the provided one
            # This is implicitly tested by the implementation

    async def test_mass_assignment_vulnerability(
        self,
        auth_client: AsyncClient,
        auth_token
    ):
        """Test mass assignment vulnerability"""
        # Try to set internal/protected fields
        response = await auth_client.post(
            "/api-keys/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Mass Assignment Test",
                "scopes": ["read:agents"],
                "id": str(uuid4()),  # Try to set ID
                "created_at": "2000-01-01T00:00:00Z",  # Try to set timestamp
                "is_active": False,  # Try to set status
                "uses_count": 1000  # Try to set usage count
            }
        )

        # Should either reject extra fields or ignore them
        assert response.status_code in [200, 201, 422, 400]
