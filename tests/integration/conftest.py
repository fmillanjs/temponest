"""
Fixtures for cross-service integration tests.

These tests interact with actual running services via Docker containers.
"""

import pytest
import pytest_asyncio
import httpx
import asyncio
from typing import Dict, Any
import os


# Service URLs (from Docker containers)
AUTH_URL = os.getenv("AUTH_URL", "http://localhost:9002")
AGENTS_URL = os.getenv("AGENTS_URL", "http://localhost:9000")
SCHEDULER_URL = os.getenv("SCHEDULER_URL", "http://localhost:9003")
APPROVAL_UI_URL = os.getenv("APPROVAL_UI_URL", "http://localhost:9001")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


@pytest_asyncio.fixture(scope="session")
async def http_client():
    """Create HTTP client for API calls"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest_asyncio.fixture(scope="session")
async def auth_client(http_client):
    """Client for Auth service"""
    return {
        "client": http_client,
        "base_url": AUTH_URL
    }


@pytest_asyncio.fixture(scope="session")
async def agents_client(http_client):
    """Client for Agents service"""
    return {
        "client": http_client,
        "base_url": AGENTS_URL
    }


@pytest_asyncio.fixture(scope="session")
async def scheduler_client(http_client):
    """Client for Scheduler service"""
    return {
        "client": http_client,
        "base_url": SCHEDULER_URL
    }


@pytest_asyncio.fixture(scope="session")
async def approval_ui_client(http_client):
    """Client for Approval UI service"""
    return {
        "client": http_client,
        "base_url": APPROVAL_UI_URL
    }


@pytest_asyncio.fixture(scope="session")
async def qdrant_client(http_client):
    """Client for Qdrant service"""
    return {
        "client": http_client,
        "base_url": QDRANT_URL
    }


@pytest_asyncio.fixture(scope="session")
async def test_user_credentials():
    """Test user credentials for authentication"""
    return {
        "email": "integration-test@example.com",
        "password": "Integration123!Test",
        "tenant_id": "integration-test-tenant"
    }


@pytest_asyncio.fixture(scope="session")
async def authenticated_session(http_client, auth_client, test_user_credentials):
    """
    Create authenticated session with access token.

    Returns:
        Dict with client, access_token, and user info
    """
    # Try to register user (may already exist)
    try:
        register_response = await http_client.post(
            f"{auth_client['base_url']}/auth/register",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"],
                "tenant_id": test_user_credentials["tenant_id"]
            }
        )
        if register_response.status_code not in [200, 201, 409]:
            pytest.skip(f"Failed to register test user: {register_response.text}")
    except Exception:
        # User may already exist, continue to login
        pass

    # Login to get access token
    try:
        login_response = await http_client.post(
            f"{auth_client['base_url']}/auth/login",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"]
            }
        )

        if login_response.status_code != 200:
            pytest.skip(f"Failed to login test user: {login_response.text}")

        auth_data = login_response.json()
        access_token = auth_data.get("access_token")

        if not access_token:
            pytest.skip("No access token in login response")

        return {
            "client": http_client,
            "access_token": access_token,
            "user_id": auth_data.get("user_id"),
            "tenant_id": test_user_credentials["tenant_id"],
            "headers": {"Authorization": f"Bearer {access_token}"}
        }
    except Exception as e:
        pytest.skip(f"Failed to authenticate: {str(e)}")


@pytest_asyncio.fixture(scope="function")
async def test_agent(authenticated_session, agents_client):
    """
    Create a test agent for integration tests.

    Automatically cleans up after the test.
    """
    agent_id = None
    try:
        # Create test agent
        create_response = await authenticated_session["client"].post(
            f"{agents_client['base_url']}/agents/",
            headers=authenticated_session["headers"],
            json={
                "name": "Integration Test Agent",
                "type": "developer",
                "description": "Agent for integration testing",
                "provider": "anthropic",
                "model": "claude-3-5-sonnet-20241022",
                "system_prompt": "You are a helpful developer agent for testing.",
                "tenant_id": authenticated_session["tenant_id"]
            }
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create test agent: {create_response.text}")

        agent_data = create_response.json()
        agent_id = agent_data.get("id")

        yield agent_data

    finally:
        # Cleanup: delete test agent
        if agent_id:
            try:
                await authenticated_session["client"].delete(
                    f"{agents_client['base_url']}/agents/{agent_id}",
                    headers=authenticated_session["headers"]
                )
            except Exception:
                pass  # Best effort cleanup


@pytest_asyncio.fixture(scope="function")
async def test_schedule(authenticated_session, scheduler_client, test_agent):
    """
    Create a test schedule for integration tests.

    Automatically cleans up after the test.
    """
    schedule_id = None
    try:
        # Create test schedule
        create_response = await authenticated_session["client"].post(
            f"{scheduler_client['base_url']}/schedules/",
            headers=authenticated_session["headers"],
            json={
                "name": "Integration Test Schedule",
                "agent_id": test_agent["id"],
                "cron_expression": "0 0 * * *",  # Daily at midnight
                "task_payload": {"test": "data"},
                "is_active": False,  # Don't run automatically
                "tenant_id": authenticated_session["tenant_id"]
            }
        )

        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create test schedule: {create_response.text}")

        schedule_data = create_response.json()
        schedule_id = schedule_data.get("id")

        yield schedule_data

    finally:
        # Cleanup: delete test schedule
        if schedule_id:
            try:
                await authenticated_session["client"].delete(
                    f"{scheduler_client['base_url']}/schedules/{schedule_id}",
                    headers=authenticated_session["headers"]
                )
            except Exception:
                pass  # Best effort cleanup


@pytest_asyncio.fixture(scope="session")
async def service_health_check(http_client):
    """
    Check health of all services before running tests.

    Skips tests if critical services are down.
    """
    services_status = {}

    services = {
        "auth": f"{AUTH_URL}/health",
        "agents": f"{AGENTS_URL}/health",
        "scheduler": f"{SCHEDULER_URL}/health",
        "approval_ui": f"{APPROVAL_UI_URL}/health",
    }

    for service_name, health_url in services.items():
        try:
            response = await http_client.get(health_url, timeout=5.0)
            services_status[service_name] = response.status_code == 200
        except Exception:
            services_status[service_name] = False

    # Check if critical services are up
    critical_services = ["auth"]
    for service in critical_services:
        if not services_status.get(service):
            pytest.skip(f"Critical service '{service}' is not healthy")

    return services_status


@pytest_asyncio.fixture(scope="session")
async def second_test_user():
    """
    Second test user for multi-tenant testing.

    Returns credentials for a separate tenant.
    """
    return {
        "email": "integration-test-2@example.com",
        "password": "Integration123!Test2",
        "tenant_id": "integration-test-tenant-2"
    }


@pytest_asyncio.fixture(scope="session")
async def second_authenticated_session(http_client, auth_client, second_test_user):
    """
    Second authenticated session for multi-tenant testing.
    """
    # Try to register user (may already exist)
    try:
        register_response = await http_client.post(
            f"{auth_client['base_url']}/auth/register",
            json={
                "email": second_test_user["email"],
                "password": second_test_user["password"],
                "tenant_id": second_test_user["tenant_id"]
            }
        )
        if register_response.status_code not in [200, 201, 409]:
            pytest.skip(f"Failed to register second test user: {register_response.text}")
    except Exception:
        pass

    # Login to get access token
    try:
        login_response = await http_client.post(
            f"{auth_client['base_url']}/auth/login",
            json={
                "email": second_test_user["email"],
                "password": second_test_user["password"]
            }
        )

        if login_response.status_code != 200:
            pytest.skip(f"Failed to login second test user: {login_response.text}")

        auth_data = login_response.json()
        access_token = auth_data.get("access_token")

        if not access_token:
            pytest.skip("No access token in login response")

        return {
            "client": http_client,
            "access_token": access_token,
            "user_id": auth_data.get("user_id"),
            "tenant_id": second_test_user["tenant_id"],
            "headers": {"Authorization": f"Bearer {access_token}"}
        }
    except Exception as e:
        pytest.skip(f"Failed to authenticate second user: {str(e)}")
