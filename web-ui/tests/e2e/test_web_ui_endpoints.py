"""
End-to-end tests for Web UI endpoints against running Docker stack.
These tests make real HTTP requests to the Web UI service.
"""
import pytest
import httpx
import os
import asyncpg
from datetime import datetime
from decimal import Decimal
import uuid


# Service URLs from environment or defaults
WEB_UI_URL = os.getenv("WEB_UI_URL", "http://localhost:8082")
# Use POSTGRES_HOST for Docker environment, fallback to DB_HOST or localhost
DB_HOST = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost"))
# Use POSTGRES_PORT for Docker environment (5432 internal), fallback to 5434 (external)
DB_PORT = int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5434")))
DB_NAME = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "agentic"))
DB_USER = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "postgres"))
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")


@pytest.fixture
async def db_connection():
    """Database connection for test data setup/cleanup"""
    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    yield conn
    await conn.close()


@pytest.fixture
async def test_tenant_id(db_connection):
    """Create a test tenant and return its ID"""
    tenant_id = uuid.uuid4()

    # Insert test tenant with required columns
    await db_connection.execute("""
        INSERT INTO tenants (id, name, slug, created_at)
        VALUES ($1, $2, $3, NOW())
        ON CONFLICT (id) DO NOTHING
    """, tenant_id, "E2E Test Tenant", "test-tenant-e2e")

    yield tenant_id

    # Cleanup - delete test tenant (cascades to cost_tracking)
    await db_connection.execute(
        "DELETE FROM tenants WHERE id = $1", tenant_id
    )


@pytest.fixture
async def setup_test_data(db_connection, test_tenant_id):
    """Setup and teardown test data"""
    # Cleanup before
    await db_connection.execute(
        "DELETE FROM cost_tracking WHERE task_id LIKE 'e2e-test-%'"
    )

    # Insert test data with proper UUID

    await db_connection.execute("""
        INSERT INTO cost_tracking
        (task_id, agent_name, tenant_id, model_provider, model_name,
         total_tokens, total_cost_usd, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """,
        "e2e-test-task-1", "e2e-agent", test_tenant_id,
        "anthropic", "claude-3-opus", 1000, Decimal("1.50"),
        datetime(2025, 1, 15, 10, 0, 0)
    )

    await db_connection.execute("""
        INSERT INTO cost_tracking
        (task_id, agent_name, tenant_id, model_provider, model_name,
         total_tokens, total_cost_usd, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """,
        "e2e-test-task-2", "e2e-agent", test_tenant_id,
        "anthropic", "claude-3-sonnet", 500, Decimal("0.75"),
        datetime(2025, 1, 20, 14, 30, 0)
    )

    yield

    # Cleanup after
    await db_connection.execute(
        "DELETE FROM cost_tracking WHERE task_id LIKE 'e2e-test-%'"
    )


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_cost_summary_endpoint_e2e_no_dates(setup_test_data):
    """Test Web UI /api/costs/summary endpoint without date parameters"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{WEB_UI_URL}/api/costs/summary")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_usd" in data
        assert "total_tokens" in data
        assert "total_executions" in data

        # Verify types
        assert isinstance(data["total_usd"], (int, float))
        assert isinstance(data["total_tokens"], int)
        assert isinstance(data["total_executions"], int)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_cost_summary_endpoint_e2e_with_dates(setup_test_data):
    """
    Test Web UI /api/costs/summary endpoint with date parameters.
    THIS IS THE CRITICAL TEST - Would have caught the 500 error bug!
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{WEB_UI_URL}/api/costs/summary",
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31"
            }
        )

        # This would have failed with 500 error before the fix!
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()

        # Verify response structure
        assert "total_usd" in data
        assert "total_tokens" in data
        assert "total_executions" in data

        # Verify types
        assert isinstance(data["total_usd"], (int, float))
        assert isinstance(data["total_tokens"], int)
        assert isinstance(data["total_executions"], int)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_cost_summary_endpoint_invalid_dates():
    """Test Web UI /api/costs/summary endpoint with invalid date parameters"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{WEB_UI_URL}/api/costs/summary",
            params={
                "start_date": "invalid-date",
                "end_date": "2025-01-31"
            }
        )

        # Should return error for invalid dates
        assert response.status_code in [400, 500]


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Test Web UI health check endpoint"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{WEB_UI_URL}/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_status_endpoint():
    """Test Web UI /api/status endpoint"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{WEB_UI_URL}/api/status")

        assert response.status_code == 200
        data = response.json()

        # Should contain service health information
        assert isinstance(data, dict)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_agents_endpoint():
    """Test Web UI /api/agents endpoint"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{WEB_UI_URL}/api/agents")

        assert response.status_code == 200
        data = response.json()

        # Should return a list (empty or with agents)
        assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_schedules_endpoint():
    """Test Web UI /api/schedules endpoint"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{WEB_UI_URL}/api/schedules")

        assert response.status_code == 200
        data = response.json()

        # Should return a list (empty or with schedules)
        assert isinstance(data, list)


@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_home_page_loads():
    """Test that the Web UI home page loads successfully"""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(f"{WEB_UI_URL}/")

        assert response.status_code == 200
        # Should return HTML
        assert "text/html" in response.headers.get("content-type", "")
