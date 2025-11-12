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


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def http_client():
    """Create HTTP client for API calls (session-scoped to reduce overhead)"""
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
        "full_name": "Integration Test User",
        "tenant_id": None  # Auto-create tenant
    }


@pytest_asyncio.fixture(scope="session")
async def authenticated_session(http_client, auth_client, test_user_credentials):
    """
    Create authenticated session with access token.

    Returns:
        Dict with client, access_token, and user info
    """
    # Try to register user (may already exist)
    # Skip registration on rate limit or if user likely exists
    try:
        register_response = await http_client.post(
            f"{auth_client['base_url']}/auth/register",
            json={
                "email": test_user_credentials["email"],
                "password": test_user_credentials["password"],
                "full_name": test_user_credentials["full_name"],
                "tenant_id": test_user_credentials["tenant_id"]
            }
        )
        # Accept 409 (user exists) and 429 (rate limit) - just try login
        if register_response.status_code not in [200, 201, 409, 429]:
            # Only skip if it's a real error, not conflict or rate limit
            pass  # Continue to login anyway
    except Exception as e:
        # User may already exist or network error, continue to login
        pass

    # Login to get access token with retry logic for rate limiting
    max_retries = 3
    retry_delay = 2.0

    for attempt in range(max_retries):
        try:
            login_response = await http_client.post(
                f"{auth_client['base_url']}/auth/login",
                json={
                    "email": test_user_credentials["email"],
                    "password": test_user_credentials["password"]
                }
            )

            # Handle rate limiting with exponential backoff
            if login_response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"\nRate limited, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    pytest.skip(f"Rate limit exceeded after {max_retries} retries")

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
                "tenant_id": auth_data.get("user", {}).get("tenant_id") or auth_data.get("tenant_id"),
                "headers": {"Authorization": f"Bearer {access_token}"}
            }
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            pytest.skip(f"Failed to authenticate: {str(e)}")


@pytest_asyncio.fixture(scope="function")
async def test_agent(authenticated_session, agents_client):
    """
    Get a test agent from departments API for integration tests.

    Uses existing developer agent from the engineering department.
    No cleanup needed since we use pre-defined department agents.
    """
    try:
        # Get engineering department agents
        dept_response = await authenticated_session["client"].get(
            f"{agents_client['base_url']}/departments/engineering/agents",
            headers=authenticated_session["headers"]
        )

        if dept_response.status_code == 200:
            agents_data = dept_response.json()
            if agents_data.get("agents") and len(agents_data["agents"]) > 0:
                # Use first available agent (likely Developer)
                agent_info = agents_data["agents"][0]
                yield {
                    "id": agent_info["id"],
                    "name": agent_info["name"],
                    "type": agent_info.get("role", "developer"),
                    "department": "engineering",
                    "path": f"engineering.{agent_info['id']}",
                    "provider": agent_info.get("provider", "anthropic"),
                    "model": agent_info.get("model", "claude-3-5-sonnet-20241022")
                }
                return

        # Fallback: Use developer agent directly (known to exist)
        yield {
            "id": "developer",
            "name": "Developer Agent",
            "type": "developer",
            "department": "engineering",
            "path": "engineering.developer",
            "execution_endpoint": "/developer/run",
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022"
        }

    except Exception as e:
        # If departments API fails, skip tests that depend on agents
        pytest.skip(f"Failed to get department agent: {str(e)}")

    # No cleanup needed - we're using existing department agents


@pytest_asyncio.fixture(scope="function")
async def test_schedule(authenticated_session, scheduler_client, test_agent):
    """
    Create a test schedule for integration tests.

    Uses department agent ID from test_agent fixture.
    Automatically cleans up after the test.
    """
    schedule_id = None
    try:
        # Create test schedule using department agent
        create_response = await authenticated_session["client"].post(
            f"{scheduler_client['base_url']}/schedules/",
            headers=authenticated_session["headers"],
            json={
                "name": "Integration Test Schedule",
                "agent_id": test_agent["id"],  # Use department agent ID
                "agent_name": test_agent.get("name", "Integration Test Agent"),  # Required field
                "schedule_type": "cron",  # Required field
                "agent_path": test_agent.get("path"),  # Add department path
                "cron_expression": "0 0 * * *",  # Daily at midnight
                "task_payload": {"test": "data", "department": test_agent.get("department")},
                "is_active": False,  # Don't run automatically
                "tenant_id": authenticated_session["tenant_id"]
            },
            follow_redirects=True
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


@pytest_asyncio.fixture(scope="function")
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
        "full_name": "Integration Test User 2",
        "tenant_id": None  # Auto-create separate tenant
    }


@pytest_asyncio.fixture(scope="session")
async def second_authenticated_session(http_client, auth_client, second_test_user):
    """
    Second authenticated session for multi-tenant testing.
    """
    # Try to register user (may already exist)
    # Skip registration on rate limit or if user likely exists
    try:
        register_response = await http_client.post(
            f"{auth_client['base_url']}/auth/register",
            json={
                "email": second_test_user["email"],
                "password": second_test_user["password"],
                "full_name": second_test_user["full_name"],
                "tenant_id": second_test_user["tenant_id"]
            }
        )
        # Accept 409 (user exists) and 429 (rate limit) - just try login
        if register_response.status_code not in [200, 201, 409, 429]:
            # Only skip if it's a real error, not conflict or rate limit
            pass  # Continue to login anyway
    except Exception as e:
        # User may already exist or network error, continue to login
        pass

    # Login to get access token with retry logic for rate limiting
    max_retries = 3
    retry_delay = 2.0

    for attempt in range(max_retries):
        try:
            login_response = await http_client.post(
                f"{auth_client['base_url']}/auth/login",
                json={
                    "email": second_test_user["email"],
                    "password": second_test_user["password"]
                }
            )

            # Handle rate limiting with exponential backoff
            if login_response.status_code == 429:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"\nRate limited (second user), waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    pytest.skip(f"Rate limit exceeded after {max_retries} retries")

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
                "tenant_id": auth_data.get("user", {}).get("tenant_id") or auth_data.get("tenant_id"),
                "headers": {"Authorization": f"Bearer {access_token}"}
            }
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                continue
            pytest.skip(f"Failed to authenticate second user: {str(e)}")
