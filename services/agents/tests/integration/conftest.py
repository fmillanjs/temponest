"""
Integration test configuration with proper auth mocking.
"""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from httpx import AsyncClient

from app.main import app
from app.auth_client import AuthContext, AuthClient
from app import auth_middleware


@pytest.fixture
def mock_auth_context():
    """Create a mock auth context for testing"""
    return AuthContext(
        user_id=str(uuid4()),
        tenant_id=str(uuid4()),
        email="test@example.com",
        roles=["admin"],
        permissions=[
            "agents:read",
            "agents:write",
            "agents:execute",
            "departments:read",
            "workflows:read",
            "workflows:create",
            "webhooks:read",
            "webhooks:write"
        ],
        is_superuser=False
    )


@pytest.fixture
async def authenticated_client(mock_auth_context):
    """
    Create async HTTP client with mocked auth client.
    This ensures all auth checks pass in integration tests.
    """
    # Create mock auth client
    mock_auth_client = AsyncMock(spec=AuthClient)
    mock_auth_client.verify_token.return_value = mock_auth_context
    mock_auth_client.check_permission.return_value = True

    # Set the global auth client in the module
    auth_middleware._auth_client = mock_auth_client

    # Create client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Cleanup
    auth_middleware._auth_client = None
