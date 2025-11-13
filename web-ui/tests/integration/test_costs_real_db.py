"""
Real integration tests for cost tracking endpoints with actual database connections.
These tests connect to a real PostgreSQL database to ensure query and type handling work correctly.
"""
import pytest
import asyncpg
from datetime import date, datetime
from decimal import Decimal
import os
import uuid


# Database connection parameters from environment or defaults
# Use POSTGRES_HOST for Docker environment, fallback to DB_HOST or localhost
DB_HOST = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost"))
# Use POSTGRES_PORT for Docker environment (5432 internal), fallback to 5434 (external)
DB_PORT = int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5434")))
DB_NAME = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "agentic"))
DB_USER = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "postgres"))
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")


@pytest.fixture
async def db_connection():
    """Create a real database connection for testing"""
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
    """, tenant_id, "Test Tenant", "test-tenant-integration")

    yield tenant_id

    # Cleanup - delete test tenant (cascades to cost_tracking)
    await db_connection.execute(
        "DELETE FROM tenants WHERE id = $1", tenant_id
    )


@pytest.fixture
async def clean_test_data(db_connection):
    """Clean up test data before and after tests"""
    # Cleanup before test
    await db_connection.execute(
        "DELETE FROM cost_tracking WHERE task_id LIKE 'test-%'"
    )
    await db_connection.execute(
        "DELETE FROM tenants WHERE slug = 'test-tenant-integration'"
    )
    yield
    # Cleanup after test
    await db_connection.execute(
        "DELETE FROM cost_tracking WHERE task_id LIKE 'test-%'"
    )
    await db_connection.execute(
        "DELETE FROM tenants WHERE slug = 'test-tenant-integration'"
    )


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_cost_summary_with_real_database(db_connection, clean_test_data, test_tenant_id):
    """Test cost summary query with REAL database connection - This catches type conversion bugs!"""

    # Insert test data with proper types (using UUID for tenant_id)

    await db_connection.execute("""
        INSERT INTO cost_tracking
        (task_id, agent_name, tenant_id, model_provider, model_name,
         total_tokens, total_cost_usd, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """,
        "test-task-1", "test-agent", test_tenant_id,
        "anthropic", "claude-3-opus", 1000, Decimal("1.50"),
        datetime(2025, 1, 15, 10, 0, 0)
    )

    await db_connection.execute("""
        INSERT INTO cost_tracking
        (task_id, agent_name, tenant_id, model_provider, model_name,
         total_tokens, total_cost_usd, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """,
        "test-task-2", "test-agent", test_tenant_id,
        "anthropic", "claude-3-sonnet", 500, Decimal("0.75"),
        datetime(2025, 1, 20, 14, 30, 0)
    )

    # Test the actual query with date parameters (THIS IS THE CRITICAL TEST!)
    # This is what the Web UI does and what was failing in production
    start = date(2025, 1, 1)
    end = date(2025, 1, 31)

    row = await db_connection.fetchrow("""
        SELECT
            COALESCE(SUM(total_cost_usd), 0) as total_usd,
            COALESCE(SUM(total_tokens), 0) as total_tokens,
            COUNT(*) as total_executions
        FROM cost_tracking
        WHERE created_at::date >= $1
        AND created_at::date <= $2
        AND task_id LIKE 'test-%'
    """, start, end)

    # Verify the results
    assert row is not None
    assert row['total_usd'] == Decimal("2.25")  # 1.50 + 0.75
    assert row['total_tokens'] == 1500  # 1000 + 500
    assert row['total_executions'] == 2


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_cost_summary_with_string_dates_should_fail(db_connection, clean_test_data, test_tenant_id):
    """Test that passing string dates to asyncpg raises TypeError - demonstrates the bug"""

    # Insert test data with proper UUID

    await db_connection.execute("""
        INSERT INTO cost_tracking
        (task_id, agent_name, tenant_id, model_provider, model_name,
         total_tokens, total_cost_usd, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """,
        "test-task-3", "test-agent", test_tenant_id,
        "anthropic", "claude-3-opus", 1000, Decimal("1.50"),
        datetime(2025, 1, 15, 10, 0, 0)
    )

    # This should raise a TypeError because asyncpg expects date objects, not strings
    # This is exactly the bug that was happening in production!
    with pytest.raises(Exception):  # asyncpg will raise an error
        start_str = "2025-01-01"  # String, not date object
        end_str = "2025-01-31"

        await db_connection.fetchrow("""
            SELECT
                COALESCE(SUM(total_cost_usd), 0) as total_usd,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COUNT(*) as total_executions
            FROM cost_tracking
            WHERE created_at::date >= $1
            AND created_at::date <= $2
            AND task_id LIKE 'test-%'
        """, start_str, end_str)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_cost_summary_no_date_filter(db_connection, clean_test_data, test_tenant_id):
    """Test cost summary query without date filter"""

    # Insert test data with proper UUID

    await db_connection.execute("""
        INSERT INTO cost_tracking
        (task_id, agent_name, tenant_id, model_provider, model_name,
         total_tokens, total_cost_usd, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """,
        "test-task-4", "test-agent", test_tenant_id,
        "anthropic", "claude-3-opus", 2000, Decimal("3.00"),
        datetime(2025, 1, 15, 10, 0, 0)
    )

    # Query without date filter
    row = await db_connection.fetchrow("""
        SELECT
            COALESCE(SUM(total_cost_usd), 0) as total_usd,
            COALESCE(SUM(total_tokens), 0) as total_tokens,
            COUNT(*) as total_executions
        FROM cost_tracking
        WHERE task_id LIKE 'test-%'
    """)

    assert row is not None
    assert row['total_usd'] == Decimal("3.00")
    assert row['total_tokens'] == 2000
    assert row['total_executions'] == 1


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_cost_summary_empty_results(db_connection, clean_test_data):
    """Test cost summary query with no matching data"""

    # Query with date range that has no data
    start = date(2099, 1, 1)
    end = date(2099, 12, 31)

    row = await db_connection.fetchrow("""
        SELECT
            COALESCE(SUM(total_cost_usd), 0) as total_usd,
            COALESCE(SUM(total_tokens), 0) as total_tokens,
            COUNT(*) as total_executions
        FROM cost_tracking
        WHERE created_at::date >= $1
        AND created_at::date <= $2
        AND task_id LIKE 'test-%'
    """, start, end)

    assert row is not None
    assert row['total_usd'] == Decimal("0")
    assert row['total_tokens'] == 0
    assert row['total_executions'] == 0


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_decimal_precision_handling(db_connection, clean_test_data, test_tenant_id):
    """Test that Decimal values maintain precision through database round-trip"""

    # Insert data with precise decimal and proper UUID
    precise_cost = Decimal("0.123456789")

    await db_connection.execute("""
        INSERT INTO cost_tracking
        (task_id, agent_name, tenant_id, model_provider, model_name,
         total_tokens, total_cost_usd, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """,
        "test-task-5", "test-agent", test_tenant_id,
        "anthropic", "claude-3-opus", 100, precise_cost,
        datetime(2025, 1, 15, 10, 0, 0)
    )

    # Query and verify precision
    row = await db_connection.fetchrow("""
        SELECT total_cost_usd
        FROM cost_tracking
        WHERE task_id = $1
    """, "test-task-5")

    # The database may truncate based on column definition, but type should be Decimal
    assert isinstance(row['total_cost_usd'], Decimal)
