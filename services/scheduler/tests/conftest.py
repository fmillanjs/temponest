"""
Shared pytest fixtures for scheduler service tests
"""
import os

# Set test environment variables BEFORE any other imports
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:agentic_postgres_2024@localhost:5434/agentic")
os.environ["AGENT_SERVICE_URL"] = "http://test-agents:9000"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-characters-long"

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import asyncpg
from httpx import AsyncClient, Response
import respx

# Add app to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from db import DatabaseManager
from scheduler import TaskScheduler
from models import ScheduleType, ExecutionStatus
from settings import settings


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_pool():
    """Create a test database connection pool"""
    # Use the same database as main app (configured via environment)
    pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=1,
        max_size=5,
        command_timeout=60
    )

    yield pool

    await pool.close()


@pytest_asyncio.fixture
async def db_manager(db_pool):
    """Create a DatabaseManager with test database pool"""
    manager = DatabaseManager()
    manager.pool = db_pool
    return manager


@pytest_asyncio.fixture
async def clean_db(db_pool, test_tenant_id, test_user_id):
    """Clean database and create test tenant/user before each test"""
    async with db_pool.acquire() as conn:
        # Clean up
        await conn.execute("DELETE FROM task_executions")
        await conn.execute("DELETE FROM scheduled_tasks")

        # Create test tenant if it doesn't exist
        await conn.execute("""
            INSERT INTO tenants (id, name, slug, created_at)
            VALUES ($1, 'Test Tenant', 'test-tenant', CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO NOTHING
        """, test_tenant_id)

        # Create test user if it doesn't exist
        await conn.execute("""
            INSERT INTO users (id, tenant_id, email, hashed_password, full_name, created_at)
            VALUES ($1, $2, 'test@example.com', 'test_hash', 'Test User', CURRENT_TIMESTAMP)
            ON CONFLICT (email) DO NOTHING
        """, test_user_id, test_tenant_id)

    yield
    # Clean up after test as well
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM task_executions")
        await conn.execute("DELETE FROM scheduled_tasks")


# ============================================================================
# Scheduler Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def scheduler(db_manager):
    """Create a TaskScheduler instance"""
    scheduler = TaskScheduler(db_manager)
    yield scheduler
    # Stop scheduler if running
    if scheduler.is_running():
        await scheduler.stop()


@pytest_asyncio.fixture
async def running_scheduler(scheduler):
    """Create and start a TaskScheduler instance"""
    await scheduler.start()
    yield scheduler
    await scheduler.stop()


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_agent_service():
    """Mock the agent service HTTP calls"""
    with respx.mock(base_url=settings.agent_service_url) as respx_mock:
        yield respx_mock


@pytest.fixture
def mock_agent_success_response():
    """Mock successful agent execution response"""
    return {
        "status": "success",
        "task_id": "test-task-123",
        "result": {
            "output": "Task completed successfully",
            "artifacts": []
        },
        "tokens_used": 1500,
        "cost_info": {
            "total_cost_usd": 0.045
        }
    }


@pytest.fixture
def mock_agent_error_response():
    """Mock failed agent execution response"""
    return {
        "status": "error",
        "error": "Agent execution failed: Invalid task configuration"
    }


# ============================================================================
# Data Fixtures
# ============================================================================

@pytest.fixture
def test_tenant_id() -> UUID:
    """Get a test tenant ID"""
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def test_user_id() -> UUID:
    """Get a test user ID"""
    return UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def test_task_payload() -> Dict[str, Any]:
    """Get a test task payload"""
    return {
        "task": "Write a Python function to calculate fibonacci numbers",
        "context": {
            "language": "python",
            "framework": "none"
        },
        "risk_level": "low"
    }


@pytest.fixture
def cron_schedule_data(test_tenant_id, test_user_id, test_task_payload):
    """Get test data for creating a cron schedule"""
    return {
        "tenant_id": test_tenant_id,
        "user_id": test_user_id,
        "name": "Daily Backup Task",
        "description": "Runs daily backup at 2 AM",
        "schedule_type": "cron",
        "cron_expression": "0 2 * * *",
        "timezone": "UTC",
        "agent_name": "developer",
        "task_payload": test_task_payload,
        "project_id": "test-project-123",
        "workflow_id": "test-workflow-456",
        "timeout_seconds": 300,
        "max_retries": 3,
        "retry_delay_seconds": 60,
        "is_active": True,
        "is_paused": False
    }


@pytest.fixture
def interval_schedule_data(test_tenant_id, test_user_id, test_task_payload):
    """Get test data for creating an interval schedule"""
    return {
        "tenant_id": test_tenant_id,
        "user_id": test_user_id,
        "name": "Hourly Status Check",
        "description": "Checks system status every hour",
        "schedule_type": "interval",
        "interval_seconds": 3600,
        "timezone": "UTC",
        "agent_name": "devops",
        "task_payload": test_task_payload,
        "timeout_seconds": 120,
        "max_retries": 2,
        "retry_delay_seconds": 30,
        "is_active": True,
        "is_paused": False
    }


@pytest.fixture
def once_schedule_data(test_tenant_id, test_user_id, test_task_payload):
    """Get test data for creating a one-time schedule"""
    scheduled_time = datetime.utcnow() + timedelta(hours=1)
    return {
        "tenant_id": test_tenant_id,
        "user_id": test_user_id,
        "name": "One-time Deployment",
        "description": "Deploy application once",
        "schedule_type": "once",
        "scheduled_time": scheduled_time,
        "timezone": "UTC",
        "agent_name": "devops",
        "task_payload": test_task_payload,
        "timeout_seconds": 600,
        "max_retries": 1,
        "retry_delay_seconds": 0,
        "is_active": True,
        "is_paused": False
    }


# ============================================================================
# Helper Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def create_test_schedule(db_manager, cron_schedule_data):
    """Helper fixture to create a test schedule in the database"""
    async def _create(**overrides):
        data = {**cron_schedule_data, **overrides}
        task_id = await db_manager.create_scheduled_task(**data)
        return task_id
    return _create


@pytest_asyncio.fixture
async def create_test_execution(db_manager, test_tenant_id, test_user_id):
    """Helper fixture to create a test execution in the database"""
    async def _create(scheduled_task_id: UUID, **overrides):
        defaults = {
            "scheduled_task_id": scheduled_task_id,
            "tenant_id": test_tenant_id,
            "user_id": test_user_id,
            "agent_name": "developer",
            "scheduled_for": datetime.utcnow(),
            "execution_number": 1,
            "max_retries": 3
        }
        data = {**defaults, **overrides}
        execution_id = await db_manager.create_task_execution(**data)
        return execution_id
    return _create


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def test_client(db_manager, scheduler):
    """Create a test client for the FastAPI application"""
    from main import app

    # Override dependencies
    from routers.schedules import get_db_manager, get_scheduler, get_current_tenant_id, get_current_user_id

    app.dependency_overrides[get_db_manager] = lambda: db_manager
    app.dependency_overrides[get_scheduler] = lambda: scheduler
    app.dependency_overrides[get_current_tenant_id] = lambda: UUID("11111111-1111-1111-1111-111111111111")
    app.dependency_overrides[get_current_user_id] = lambda: UUID("22222222-2222-2222-2222-222222222222")

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()


# ============================================================================
# Time Travel Fixtures
# ============================================================================

@pytest.fixture
def freeze_time():
    """Fixture to freeze time for testing scheduled tasks"""
    with patch('scheduler.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = datetime(2025, 1, 1, 12, 0, 0)
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield mock_datetime


# ============================================================================
# Assertion Helpers
# ============================================================================

@pytest.fixture
def assert_datetime_close():
    """Helper to assert two datetimes are close (within 5 seconds)"""
    def _assert(dt1: datetime, dt2: datetime, tolerance_seconds: int = 5):
        if dt1 and dt2:
            diff = abs((dt1 - dt2).total_seconds())
            assert diff <= tolerance_seconds, f"Datetimes differ by {diff} seconds (tolerance: {tolerance_seconds}s)"
    return _assert
