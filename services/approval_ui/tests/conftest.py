"""
Pytest configuration and shared fixtures for Approval UI tests.
"""

import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
import asyncpg

# Add parent directory to Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set test environment variables
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/test_approvals"
os.environ["TEMPORAL_HOST"] = "localhost:7233"
os.environ["AUTH_SERVICE_URL"] = "http://localhost:9002"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-purposes-only-min-32-chars"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db_pool():
    """Mock database pool"""
    pool = AsyncMock(spec=asyncpg.Pool)
    conn = AsyncMock()

    # Configure the connection context manager
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None

    return pool, conn


@pytest.fixture
async def mock_temporal_client():
    """Mock Temporal client"""
    client = MagicMock()
    workflow_handle = AsyncMock()

    # Make get_workflow_handle return the workflow_handle directly (not a coroutine)
    client.get_workflow_handle = MagicMock(return_value=workflow_handle)

    return client, workflow_handle


@pytest.fixture
def mock_auth_client():
    """Mock authentication client"""
    from auth_client import AuthClient, AuthContext

    client = AsyncMock(spec=AuthClient)

    # Default auth context for testing
    auth_context = AuthContext(
        user_id="test-user-id",
        tenant_id="test-tenant-id",
        email="test@example.com",
        roles=["admin"],
        permissions=["approvals:read", "approvals:approve", "workflows:create"],
        is_superuser=False
    )

    client.verify_token.return_value = auth_context
    client.check_permission.return_value = True

    return client, auth_context


@pytest.fixture
def valid_jwt_token():
    """Generate a valid JWT token for testing"""
    import jwt
    from datetime import datetime, timedelta

    payload = {
        "sub": "test-user-id",
        "tenant_id": "test-tenant-id",
        "email": "test@example.com",
        "roles": ["admin"],
        "permissions": ["approvals:read", "approvals:approve", "workflows:create"],
        "is_superuser": False,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    token = jwt.encode(
        payload,
        "test-secret-key-for-testing-purposes-only-min-32-chars",
        algorithm="HS256"
    )

    return token


@pytest.fixture
def expired_jwt_token():
    """Generate an expired JWT token for testing"""
    import jwt
    from datetime import datetime, timedelta

    payload = {
        "sub": "test-user-id",
        "exp": datetime.utcnow() - timedelta(hours=1)  # Expired
    }

    token = jwt.encode(
        payload,
        "test-secret-key-for-testing-purposes-only-min-32-chars",
        algorithm="HS256"
    )

    return token


@pytest.fixture
def sample_approval_request():
    """Sample approval request data"""
    return {
        "workflow_id": "test-workflow-123",
        "run_id": "test-run-456",
        "task_description": "Deploy to production",
        "risk_level": "high",
        "context": {"environment": "production", "service": "api"}
    }


@pytest.fixture
def sample_approval_db_row():
    """Sample approval database row"""
    from datetime import datetime

    return {
        "id": "test-approval-id-123",
        "workflow_id": "test-workflow-123",
        "run_id": "test-run-456",
        "task_description": "Deploy to production",
        "risk_level": "high",
        "context": {"environment": "production"},
        "status": "pending",
        "approved_by": None,
        "created_at": datetime.utcnow(),
        "approved_at": None
    }


@pytest.fixture
async def app_with_mocks(mock_db_pool, mock_temporal_client, mock_auth_client):
    """
    FastAPI app with mocked dependencies.
    Use this for integration tests.
    """
    from main import app
    import main as main_module
    from auth_middleware import set_auth_client

    # Set mocked dependencies
    db_pool, db_conn = mock_db_pool
    temporal_client, workflow_handle = mock_temporal_client
    auth_client, auth_context = mock_auth_client

    main_module.db_pool = db_pool
    main_module.temporal_client = temporal_client
    set_auth_client(auth_client)

    yield app, db_conn, workflow_handle, auth_client, auth_context

    # Cleanup
    main_module.db_pool = None
    main_module.temporal_client = None


@pytest.fixture
async def async_client(app_with_mocks):
    """Async HTTP client for testing"""
    app, _, _, _, _ = app_with_mocks

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
