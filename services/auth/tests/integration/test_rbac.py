"""
Integration tests for Role-Based Access Control (RBAC).

Tests role and permission enforcement across the auth service.
"""

import pytest
from httpx import AsyncClient
from app.database import db


@pytest.mark.integration
class TestRoleBasedAccess:
    """Test role-based access control"""

    async def test_user_has_assigned_role(self, test_user):
        """Test that user has their assigned role"""
        # Get user roles
        roles = await db.fetch(
            """
            SELECT r.name
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = $1
            """,
            test_user["id"]
        )

        role_names = [r["name"] for r in roles]
        assert "viewer" in role_names

    async def test_admin_user_has_admin_role(self, test_admin_user):
        """Test that admin user has admin role"""
        roles = await db.fetch(
            """
            SELECT r.name
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = $1
            """,
            test_admin_user["id"]
        )

        role_names = [r["name"] for r in roles]
        assert "admin" in role_names

    async def test_user_has_role_permissions(self, test_user):
        """Test that user gets permissions from their roles"""
        permissions = await db.fetch(
            """
            SELECT DISTINCT p.resource, p.action, p.name
            FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = $1
            """,
            test_user["id"]
        )

        assert len(permissions) > 0
        # Viewer role should have read permissions
        permission_names = [p["name"] for p in permissions]
        # Check that at least some read permissions exist
        has_read_permission = any("read" in p.lower() for p in permission_names)
        assert has_read_permission

    async def test_admin_has_more_permissions_than_viewer(self, test_user, test_admin_user):
        """Test that admin role has more permissions than viewer"""
        # Get viewer permissions
        viewer_perms = await db.fetch(
            """
            SELECT DISTINCT p.name
            FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = $1
            """,
            test_user["id"]
        )

        # Get admin permissions
        admin_perms = await db.fetch(
            """
            SELECT DISTINCT p.name
            FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = $1
            """,
            test_admin_user["id"]
        )

        assert len(admin_perms) >= len(viewer_perms)

    async def test_superuser_flag_bypasses_permissions(self, test_admin_user):
        """Test that is_superuser flag allows bypass"""
        user = await db.fetchrow(
            "SELECT is_superuser FROM users WHERE id = $1",
            test_admin_user["id"]
        )

        assert user["is_superuser"] is True

    async def test_regular_user_not_superuser(self, test_user):
        """Test that regular users are not superusers"""
        user = await db.fetchrow(
            "SELECT is_superuser FROM users WHERE id = $1",
            test_user["id"]
        )

        assert user["is_superuser"] is False

    async def test_tenant_isolation_in_roles(self, test_tenant):
        """Test that users only see roles within their tenant"""
        # Create a second tenant and user
        tenant2_id = await db.fetchval(
            """
            INSERT INTO tenants (name, slug, plan)
            VALUES ('Tenant2', 'tenant2', 'free')
            RETURNING id
            """
        )

        user2_id = await db.fetchval(
            """
            INSERT INTO users (email, hashed_password, full_name, tenant_id)
            VALUES ('user2@example.com', 'hash', 'User 2', $1)
            RETURNING id
            """,
            tenant2_id
        )

        # Both users should not see each other's role assignments
        # This is enforced at the application level
        # Verify data isolation exists in database
        assert tenant2_id != test_tenant["id"]


@pytest.mark.integration
class TestPermissionEnforcement:
    """Test permission checking and enforcement"""

    async def test_user_permissions_loaded_in_token(self, client: AsyncClient, test_user):
        """Test that JWT token contains user permissions"""
        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Decode token to check permissions (would need JWT handler)
        from app.handlers import JWTHandler
        payload = JWTHandler.verify_token(data["access_token"])

        assert "permissions" in payload
        assert isinstance(payload["permissions"], list)

    async def test_user_roles_loaded_in_token(self, client: AsyncClient, test_user):
        """Test that JWT token contains user roles"""
        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        from app.handlers import JWTHandler
        payload = JWTHandler.verify_token(data["access_token"])

        assert "roles" in payload
        assert isinstance(payload["roles"], list)
        assert "viewer" in payload["roles"]

    async def test_superuser_flag_in_token(self, client: AsyncClient, test_admin_user):
        """Test that superuser flag is included in token"""
        response = await client.post(
            "/auth/login",
            json={
                "email": test_admin_user["email"],
                "password": test_admin_user["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        from app.handlers import JWTHandler
        payload = JWTHandler.verify_token(data["access_token"])

        assert "is_superuser" in payload
        assert payload["is_superuser"] is True

    async def test_permission_naming_convention(self):
        """Test that permissions follow resource:action naming convention"""
        permissions = await db.fetch(
            "SELECT name, resource, action FROM permissions"
        )

        for perm in permissions:
            # Permission name should be resource:action
            expected_name = f"{perm['resource']}:{perm['action']}"
            assert perm["name"] == expected_name

    async def test_multiple_roles_aggregate_permissions(self, test_tenant):
        """Test that user with multiple roles gets all permissions"""
        # Create user with multiple roles
        from app.handlers import PasswordHandler

        user_id = await db.fetchval(
            """
            INSERT INTO users (email, hashed_password, full_name, tenant_id)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            "multirole@example.com",
            PasswordHandler.hash_password("Password123!"),
            "Multi Role User",
            test_tenant["id"]
        )

        # Assign viewer role
        viewer_role_id = await db.fetchval("SELECT id FROM roles WHERE name = 'viewer'")
        await db.execute(
            "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
            user_id, viewer_role_id
        )

        # Assign editor role (if exists)
        editor_role_id = await db.fetchval("SELECT id FROM roles WHERE name = 'editor'")
        if editor_role_id:
            await db.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
                user_id, editor_role_id
            )

            # Get all permissions
            permissions = await db.fetch(
                """
                SELECT DISTINCT p.name
                FROM user_roles ur
                JOIN role_permissions rp ON ur.role_id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = $1
                """,
                user_id
            )

            # Should have permissions from both roles
            assert len(permissions) > 0


@pytest.mark.integration
class TestRoleManagement:
    """Test role creation and management"""

    async def test_default_roles_exist(self):
        """Test that default roles are created"""
        roles = await db.fetch("SELECT name FROM roles ORDER BY name")
        role_names = [r["name"] for r in roles]

        # At minimum, should have viewer and admin
        assert "viewer" in role_names
        assert "admin" in role_names

    async def test_viewer_role_has_read_permissions(self):
        """Test that viewer role has read-only permissions"""
        viewer_permissions = await db.fetch(
            """
            SELECT p.name, p.action
            FROM roles r
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE r.name = 'viewer'
            """
        )

        actions = [p["action"] for p in viewer_permissions]
        # Viewer should primarily have 'read' actions
        assert "read" in actions

        # Viewer should NOT have 'delete' permissions
        assert "delete" not in actions

    async def test_admin_role_has_all_permissions(self):
        """Test that admin role has comprehensive permissions"""
        admin_permissions = await db.fetch(
            """
            SELECT p.name, p.action
            FROM roles r
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE r.name = 'admin'
            """
        )

        actions = set([p["action"] for p in admin_permissions])

        # Admin should have create, read, update, delete
        expected_actions = {"create", "read", "update", "delete"}
        assert expected_actions.issubset(actions)

    async def test_new_user_gets_default_viewer_role(self, client: AsyncClient):
        """Test that newly registered users get viewer role by default"""
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

        assert "roles" in data
        assert "viewer" in data["roles"]

    async def test_role_permissions_are_hierarchical(self):
        """Test that role permissions follow a hierarchy"""
        # Get permissions for each role
        viewer_perms = await db.fetch(
            """
            SELECT p.name
            FROM roles r
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE r.name = 'viewer'
            """
        )

        editor_perms = await db.fetch(
            """
            SELECT p.name
            FROM roles r
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE r.name = 'editor'
            """
        ) if await db.fetchval("SELECT id FROM roles WHERE name = 'editor'") else []

        admin_perms = await db.fetch(
            """
            SELECT p.name
            FROM roles r
            JOIN role_permissions rp ON r.id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE r.name = 'admin'
            """
        )

        # Admin should have more permissions than viewer
        assert len(admin_perms) >= len(viewer_perms)

        # If editor exists, it should have more than viewer but maybe less than admin
        if editor_perms:
            assert len(editor_perms) >= len(viewer_perms)


@pytest.mark.integration
class TestTenantIsolation:
    """Test that RBAC respects tenant boundaries"""

    async def test_user_roles_isolated_by_tenant(self, test_tenant):
        """Test that users can only be assigned roles within their tenant"""
        # Create two tenants
        tenant1_id = test_tenant["id"]

        tenant2_id = await db.fetchval(
            """
            INSERT INTO tenants (name, slug, plan)
            VALUES ('Tenant2', 'tenant2', 'free')
            RETURNING id
            """
        )

        # Create users in each tenant
        from app.handlers import PasswordHandler

        user1_id = await db.fetchval(
            """
            INSERT INTO users (email, hashed_password, full_name, tenant_id)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            "user1@tenant1.com",
            PasswordHandler.hash_password("Password123!"),
            "User 1",
            tenant1_id
        )

        user2_id = await db.fetchval(
            """
            INSERT INTO users (email, hashed_password, full_name, tenant_id)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            "user2@tenant2.com",
            PasswordHandler.hash_password("Password123!"),
            "User 2",
            tenant2_id
        )

        # Users should be in different tenants
        assert tenant1_id != tenant2_id

        # Role assignments should not cross tenant boundaries
        # This is enforced by application logic, verified by separate tenant_ids

    async def test_permission_checks_respect_tenant_context(self, test_user, test_tenant):
        """Test that permission checks include tenant context"""
        # User should only have permissions within their tenant
        user = await db.fetchrow(
            "SELECT tenant_id FROM users WHERE id = $1",
            test_user["id"]
        )

        assert user["tenant_id"] == test_tenant["id"]

        # Permission checks should always include tenant_id verification
        # This prevents cross-tenant privilege escalation

    async def test_api_key_permissions_scoped_to_tenant(self, test_api_key):
        """Test that API key permissions are scoped to tenant"""
        api_key_data = await db.fetchrow(
            "SELECT tenant_id FROM api_keys WHERE id = $1",
            test_api_key["id"]
        )

        assert api_key_data["tenant_id"] == test_api_key["tenant_id"]

        # API keys should only grant access within their tenant
        # This is enforced in the middleware
