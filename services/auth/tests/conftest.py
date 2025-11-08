"""
Pytest configuration and fixtures for auth service tests.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from uuid import UUID, uuid4
from datetime import datetime, timedelta

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5434/test_agentic")
os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-characters-long"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["JWT_REFRESH_TOKEN_EXPIRE_DAYS"] = "30"
os.environ["API_KEY_PREFIX"] = "sk_test_"

from app.main import app
from app.database import db
from app.handlers import JWTHandler, PasswordHandler, APIKeyHandler


# ============================================================
# EVENT LOOP CONFIGURATION
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================
# DATABASE FIXTURES
# ============================================================

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests as unit or integration based on path"""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


@pytest.fixture(scope="session")
async def db_connection():
    """Setup test database connection for the session"""
    if not db.pool:
        await db.connect()
    yield
    await db.disconnect()


@pytest.fixture
async def clean_database(db_connection):
    """Clean database and rate limits before each integration/e2e test"""
    # Clean all tables before test
    await db.execute("TRUNCATE TABLE audit_log CASCADE")
    await db.execute("TRUNCATE TABLE api_keys CASCADE")
    await db.execute("TRUNCATE TABLE user_roles CASCADE")
    await db.execute("TRUNCATE TABLE users CASCADE")
    await db.execute("TRUNCATE TABLE tenants CASCADE")

    # Clear Redis rate limits
    import redis.asyncio as redis
    from app.settings import settings
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.flushdb()
        await redis_client.close()
    except:
        pass  # Ignore if Redis not available

    yield


# ============================================================
# HTTP CLIENT FIXTURES
# ============================================================

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ============================================================
# DATA FIXTURES
# ============================================================

@pytest.fixture
def test_tenant_data():
    """Test tenant data"""
    return {
        "name": "Test Organization",
        "slug": "test-org",
        "plan": "free"
    }


@pytest.fixture
async def test_tenant(test_tenant_data, clean_database):
    """Create a test tenant"""
    tenant_id = await db.fetchval(
        """
        INSERT INTO tenants (name, slug, plan)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        test_tenant_data["name"],
        test_tenant_data["slug"],
        test_tenant_data["plan"]
    )
    return {
        "id": tenant_id,
        **test_tenant_data
    }


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User"
    }


@pytest.fixture
async def test_user(test_tenant, test_user_data):
    """Create a test user"""
    hashed_password = PasswordHandler.hash_password(test_user_data["password"])

    user_id = await db.fetchval(
        """
        INSERT INTO users (email, hashed_password, full_name, tenant_id)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        test_user_data["email"],
        hashed_password,
        test_user_data["full_name"],
        test_tenant["id"]
    )

    # Assign viewer role
    viewer_role_id = await db.fetchval("SELECT id FROM roles WHERE name = 'viewer'")
    await db.execute(
        "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
        user_id, viewer_role_id
    )

    return {
        "id": user_id,
        "tenant_id": test_tenant["id"],
        **test_user_data
    }


@pytest.fixture
async def test_admin_user(test_tenant):
    """Create a test admin user"""
    hashed_password = PasswordHandler.hash_password("AdminPassword123!")

    user_id = await db.fetchval(
        """
        INSERT INTO users (email, hashed_password, full_name, tenant_id, is_superuser)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """,
        "admin@example.com",
        hashed_password,
        "Admin User",
        test_tenant["id"],
        True
    )

    # Assign admin role
    admin_role_id = await db.fetchval("SELECT id FROM roles WHERE name = 'admin'")
    await db.execute(
        "INSERT INTO user_roles (user_id, role_id) VALUES ($1, $2)",
        user_id, admin_role_id
    )

    return {
        "id": user_id,
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "tenant_id": test_tenant["id"],
        "is_superuser": True
    }


# ============================================================
# TOKEN FIXTURES
# ============================================================

@pytest.fixture
async def test_access_token(test_user):
    """Generate test access token"""
    # Get roles and permissions
    roles = await db.fetch(
        """
        SELECT r.name
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = $1
        """,
        test_user["id"]
    )

    permissions = await db.fetch(
        """
        SELECT p.resource || ':' || p.action as permission
        FROM user_roles ur
        JOIN role_permissions rp ON ur.role_id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id
        WHERE ur.user_id = $1
        """,
        test_user["id"]
    )

    return JWTHandler.create_access_token(
        user_id=test_user["id"],
        tenant_id=test_user["tenant_id"],
        email=test_user["email"],
        roles=[r["name"] for r in roles],
        permissions=[p["permission"] for p in permissions],
        is_superuser=False
    )


@pytest.fixture
async def test_admin_token(test_admin_user):
    """Generate test admin access token"""
    # Get roles and permissions
    roles = await db.fetch(
        """
        SELECT r.name
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE ur.user_id = $1
        """,
        test_admin_user["id"]
    )

    permissions = await db.fetch(
        """
        SELECT p.resource || ':' || p.action as permission
        FROM user_roles ur
        JOIN role_permissions rp ON ur.role_id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id
        WHERE ur.user_id = $1
        """,
        test_admin_user["id"]
    )

    return JWTHandler.create_access_token(
        user_id=test_admin_user["id"],
        tenant_id=test_admin_user["tenant_id"],
        email=test_admin_user["email"],
        roles=[r["name"] for r in roles],
        permissions=[p["permission"] for p in permissions],
        is_superuser=True
    )


@pytest.fixture
def test_refresh_token(test_user):
    """Generate test refresh token"""
    return JWTHandler.create_refresh_token(
        user_id=test_user["id"],
        tenant_id=test_user["tenant_id"]
    )


# ============================================================
# API KEY FIXTURES
# ============================================================

@pytest.fixture
async def test_api_key(test_tenant, test_user):
    """Create a test API key"""
    api_key_id, full_key = await APIKeyHandler.create_api_key(
        name="Test API Key",
        tenant_id=test_tenant["id"],
        user_id=test_user["id"],
        scopes=["agents:read", "workflows:create"],
        expires_in_days=30
    )

    return {
        "id": api_key_id,
        "key": full_key,
        "tenant_id": test_tenant["id"],
        "user_id": test_user["id"]
    }


# ============================================================
# UTILITY FIXTURES
# ============================================================

@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime for testing expiration"""
    class MockDatetime:
        @classmethod
        def utcnow(cls):
            return datetime(2025, 1, 1, 12, 0, 0)

    monkeypatch.setattr("app.handlers.jwt_handler.datetime", MockDatetime)
    return MockDatetime


@pytest.fixture
def expired_token(test_user):
    """Generate an expired access token"""
    # Create token with negative expiry
    payload = {
        "sub": str(test_user["id"]),
        "tenant_id": str(test_user["tenant_id"]),
        "email": test_user["email"],
        "roles": ["viewer"],
        "permissions": [],
        "is_superuser": False,
        "exp": datetime.utcnow() - timedelta(hours=1),
        "iat": datetime.utcnow() - timedelta(hours=2),
        "type": "access"
    }

    from jose import jwt
    from app.settings import settings

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
