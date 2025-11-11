"""
Pytest configuration and fixtures for security tests.
"""

import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime, timedelta

# Add service directories to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(project_root, "services/auth"))
sys.path.insert(0, os.path.join(project_root, "services/agents"))

# Set test environment variables for all services
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:agentic_postgres_2024@localhost:5434/agentic")
os.environ["REDIS_URL"] = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-characters-long"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["JWT_REFRESH_TOKEN_EXPIRE_DAYS"] = "30"
os.environ["API_KEY_PREFIX"] = "sk_test_"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def auth_client() -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for auth service"""
    import sys
    sys.path.insert(0, os.path.join(project_root, "services/auth"))
    from app.main import app
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def agents_client() -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for agents service"""
    import sys
    sys.path.insert(0, os.path.join(project_root, "services/agents"))
    from app.main import app
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
async def clean_db():
    """Clean database before and after tests"""
    from services.auth.app.database import db

    # Clean up before test
    await db.connect()
    await db.execute("DELETE FROM api_keys")
    await db.execute("DELETE FROM audit_logs")
    await db.execute("DELETE FROM users WHERE email LIKE '%security_test%'")
    await db.execute("DELETE FROM tenants WHERE name LIKE '%Security Test%'")

    yield

    # Clean up after test
    await db.execute("DELETE FROM api_keys")
    await db.execute("DELETE FROM audit_logs")
    await db.execute("DELETE FROM users WHERE email LIKE '%security_test%'")
    await db.execute("DELETE FROM tenants WHERE name LIKE '%Security Test%'")


@pytest.fixture
async def test_tenant(clean_db):
    """Create a test tenant for security tests"""
    from services.auth.app.database import db

    tenant_id = uuid4()
    await db.execute(
        """
        INSERT INTO tenants (id, name, is_active, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5)
        """,
        tenant_id,
        "Security Test Tenant",
        True,
        datetime.utcnow(),
        datetime.utcnow()
    )

    return {
        "id": tenant_id,
        "name": "Security Test Tenant"
    }


@pytest.fixture
async def test_user(test_tenant):
    """Create a test user for security tests"""
    from services.auth.app.database import db
    from services.auth.app.handlers import PasswordHandler

    password_handler = PasswordHandler()
    user_id = uuid4()
    email = "security_test@example.com"
    password = "SecurePassword123!"
    hashed_password = password_handler.hash_password(password)

    await db.execute(
        """
        INSERT INTO users (id, tenant_id, email, hashed_password, full_name, is_active, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
        user_id,
        test_tenant["id"],
        email,
        hashed_password,
        "Security Test User",
        True,
        datetime.utcnow(),
        datetime.utcnow()
    )

    return {
        "id": user_id,
        "email": email,
        "password": password,
        "tenant_id": test_tenant["id"]
    }


@pytest.fixture
async def auth_token(auth_client: AsyncClient, test_user):
    """Get authentication token for test user"""
    response = await auth_client.post(
        "/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )

    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
async def admin_user(test_tenant):
    """Create an admin user for authorization tests"""
    from services.auth.app.database import db
    from services.auth.app.handlers import PasswordHandler

    password_handler = PasswordHandler()
    user_id = uuid4()
    email = "admin_security_test@example.com"
    password = "AdminPassword123!"
    hashed_password = password_handler.hash_password(password)

    await db.execute(
        """
        INSERT INTO users (id, tenant_id, email, hashed_password, full_name, is_active, role, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        user_id,
        test_tenant["id"],
        email,
        hashed_password,
        "Admin Security Test User",
        True,
        "admin",
        datetime.utcnow(),
        datetime.utcnow()
    )

    return {
        "id": user_id,
        "email": email,
        "password": password,
        "tenant_id": test_tenant["id"]
    }
