"""
Pytest configuration and fixtures for agents service tests.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Dict, Any, Optional
from httpx import AsyncClient
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5434/test_agentic")
os.environ["OLLAMA_BASE_URL"] = "http://test-ollama:11434"
os.environ["QDRANT_URL"] = "http://test-qdrant:6333"
os.environ["AUTH_SERVICE_URL"] = "http://test-auth:9002"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-characters-long"
os.environ["LANGFUSE_PUBLIC_KEY"] = "test-public-key"
os.environ["LANGFUSE_SECRET_KEY"] = "test-secret-key"
os.environ["LANGFUSE_HOST"] = "http://test-langfuse:3000"
os.environ["OLLAMA_CHAT_MODEL"] = "test-chat-model"
os.environ["OLLAMA_CODE_MODEL"] = "test-code-model"
os.environ["EMBEDDING_MODEL"] = "test-embedding-model"

# Import after setting environment
import asyncpg
from app.main import app

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
# TEST MARKERS
# ============================================================

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests as unit, integration, or e2e based on path"""
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


# ============================================================
# DATABASE FIXTURES
# ============================================================

@pytest.fixture(scope="session")
async def db_pool(request):
    """Create database connection pool for integration tests"""
    # Only run for integration/e2e tests
    if "integration" not in str(request.fspath) and "e2e" not in str(request.fspath):
        yield None
        return

    pool = await asyncpg.create_pool(
        os.environ["DATABASE_URL"],
        min_size=2,
        max_size=10
    )

    yield pool

    await pool.close()


@pytest.fixture(scope="session")
async def setup_test_database(db_pool, request):
    """Setup test database before integration tests only"""
    # Only run for integration/e2e tests
    if not db_pool:
        yield
        return

    # Clean all agent-related tables before tests
    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE cost_alerts CASCADE")
        await conn.execute("TRUNCATE TABLE cost_budgets CASCADE")
        await conn.execute("TRUNCATE TABLE cost_tracking CASCADE")
        await conn.execute("TRUNCATE TABLE webhook_deliveries CASCADE")
        await conn.execute("TRUNCATE TABLE webhooks CASCADE")
        await conn.execute("TRUNCATE TABLE event_log CASCADE")

    yield

    # Cleanup is handled by db_pool fixture


@pytest.fixture
async def clean_database(request, db_pool):
    """Clean database before each integration/e2e test"""
    # Only run for integration/e2e tests
    if not db_pool:
        yield
        return

    async with db_pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE cost_alerts CASCADE")
        await conn.execute("TRUNCATE TABLE cost_budgets CASCADE")
        await conn.execute("TRUNCATE TABLE cost_tracking CASCADE")
        await conn.execute("TRUNCATE TABLE webhook_deliveries CASCADE")
        await conn.execute("TRUNCATE TABLE webhooks CASCADE")
        await conn.execute("TRUNCATE TABLE event_log CASCADE")

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
# MOCK EXTERNAL SERVICES
# ============================================================

@pytest.fixture
def mock_ollama():
    """Mock Ollama API responses"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "test-chat-model",
            "created_at": "2025-01-01T00:00:00Z",
            "response": "This is a test response from Ollama",
            "done": True,
            "total_duration": 1000000000,
            "load_duration": 100000000,
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        yield mock_client


@pytest.fixture
def mock_qdrant():
    """Mock Qdrant vector database"""
    with patch("qdrant_client.AsyncQdrantClient") as mock_client:
        mock_instance = AsyncMock()

        # Mock search response
        mock_instance.search.return_value = [
            Mock(
                id="doc1",
                score=0.95,
                payload={
                    "text": "This is a relevant document",
                    "source": "test.txt",
                    "chunk_id": "chunk_1"
                }
            ),
            Mock(
                id="doc2",
                score=0.85,
                payload={
                    "text": "Another relevant document",
                    "source": "test2.txt",
                    "chunk_id": "chunk_2"
                }
            )
        ]

        # Mock collection operations
        mock_instance.collection_exists.return_value = True
        mock_instance.create_collection.return_value = None
        mock_instance.upsert.return_value = None

        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_auth_client():
    """Mock Auth Service client"""
    with patch("app.auth_client.AuthClient") as mock_client:
        mock_instance = AsyncMock()

        # Mock token verification
        mock_instance.verify_token.return_value = {
            "user_id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "email": "test@example.com",
            "roles": ["admin"],
            "permissions": ["agents:read", "agents:write", "agents:execute"],
            "is_superuser": False
        }

        # Mock permission check
        mock_instance.check_permission.return_value = True

        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_langfuse():
    """Mock Langfuse tracer"""
    with patch("app.memory.langfuse_tracer.LangfuseTracer") as mock_tracer:
        mock_instance = Mock()
        mock_instance.trace_agent_execution = Mock(return_value=None)
        mock_instance.trace_rag_query = Mock(return_value=None)
        mock_instance.trace_tool_execution = Mock(return_value=None)
        mock_tracer.return_value = mock_instance
        yield mock_instance


# ============================================================
# DATA FIXTURES
# ============================================================

@pytest.fixture
def test_tenant_id() -> UUID:
    """Generate a test tenant ID"""
    return uuid4()


@pytest.fixture
def test_user_id() -> UUID:
    """Generate a test user ID"""
    return uuid4()


@pytest.fixture
def test_project_id() -> str:
    """Generate a test project ID"""
    return "test-project-123"


@pytest.fixture
def test_workflow_id() -> str:
    """Generate a test workflow ID"""
    return "test-workflow-456"


@pytest.fixture
def test_agent_request() -> Dict[str, Any]:
    """Standard agent request payload"""
    return {
        "task": "Create a Python function to calculate fibonacci numbers",
        "context": {
            "language": "python",
            "requirements": ["Use recursion", "Add docstring"]
        },
        "risk_level": "low",
        "project_id": "test-project-123",
        "workflow_id": "test-workflow-456"
    }


@pytest.fixture
def test_agent_response() -> Dict[str, Any]:
    """Standard agent response"""
    return {
        "task_id": str(uuid4()),
        "status": "completed",
        "result": {
            "output": "def fibonacci(n):\n    '''Calculate fibonacci number'''\n    if n <= 1: return n\n    return fibonacci(n-1) + fibonacci(n-2)",
            "confidence": 0.95
        },
        "citations": [
            {
                "source": "algorithms.txt",
                "relevance": 0.9,
                "excerpt": "Fibonacci sequence implementation"
            }
        ],
        "tokens_used": 250,
        "latency_ms": 1500,
        "model_info": {
            "provider": "ollama",
            "model": "test-code-model",
            "temperature": 0.2
        }
    }


# ============================================================
# COST TRACKING FIXTURES
# ============================================================

@pytest.fixture
async def test_model_pricing(db_pool):
    """Insert test model pricing data"""
    if not db_pool:
        return []

    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO model_pricing (provider, model_name, input_price_per_1m, output_price_per_1m, is_active)
            VALUES
                ('ollama', 'test-chat-model', 0.0, 0.0, true),
                ('ollama', 'test-code-model', 0.0, 0.0, true),
                ('claude', 'claude-sonnet-4-20250514', 3.0, 15.0, true),
                ('openai', 'gpt-4-turbo-preview', 10.0, 30.0, true)
        """)


@pytest.fixture
async def test_cost_budget(db_pool, test_tenant_id, test_user_id, test_project_id):
    """Create a test cost budget"""
    if not db_pool:
        return None

    budget_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO cost_budgets (
                id, tenant_id, user_id, project_id, budget_type,
                budget_amount_usd, current_spend_usd, period_start, period_end,
                alert_threshold_pct, critical_threshold_pct, is_active
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """, budget_id, test_tenant_id, test_user_id, test_project_id, 'daily',
             Decimal('100.00'), Decimal('0.00'), datetime.utcnow(),
             datetime.utcnow() + timedelta(days=1), 80, 95, True)

    return budget_id


# ============================================================
# WEBHOOK FIXTURES
# ============================================================

@pytest.fixture
async def test_webhook(db_pool, test_tenant_id, test_user_id):
    """Create a test webhook"""
    if not db_pool:
        return None

    webhook_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO webhooks (
                id, tenant_id, user_id, name, url, description,
                events, secret_key, is_active
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """, webhook_id, test_tenant_id, test_user_id, "Test Webhook",
             "https://example.com/webhook", "Test webhook for agent events",
             ["agent.execution.completed", "agent.execution.failed"], "test-secret", True)

    return {
        "id": webhook_id,
        "url": "https://example.com/webhook",
        "secret_key": "test-secret"
    }


# ============================================================
# AUTH FIXTURES
# ============================================================

@pytest.fixture
def test_auth_headers(test_user_id, test_tenant_id) -> Dict[str, str]:
    """Generate test auth headers with JWT token"""
    # In real tests, this would create a proper JWT
    # For now, we'll mock the auth middleware
    return {
        "Authorization": "Bearer test-token",
        "X-User-ID": str(test_user_id),
        "X-Tenant-ID": str(test_tenant_id)
    }


@pytest.fixture
def test_auth_context(test_user_id, test_tenant_id):
    """Create test auth context"""
    from app.auth_client import AuthContext

    return AuthContext(
        user_id=str(test_user_id),
        tenant_id=str(test_tenant_id),
        email="test@example.com",
        roles=["admin"],
        permissions=["agents:read", "agents:write", "agents:execute"],
        is_superuser=False
    )


# ============================================================
# UTILITY FIXTURES
# ============================================================

@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime for consistent testing"""
    class MockDatetime:
        @classmethod
        def utcnow(cls):
            return datetime(2025, 1, 1, 12, 0, 0)

        @classmethod
        def now(cls):
            return datetime(2025, 1, 1, 12, 0, 0)

    return MockDatetime


@pytest.fixture
def sample_rag_documents():
    """Sample documents for RAG testing"""
    return [
        {
            "text": "Python is a high-level programming language known for its simplicity and readability.",
            "source": "python_intro.txt",
            "metadata": {"category": "programming", "language": "python"}
        },
        {
            "text": "FastAPI is a modern web framework for building APIs with Python based on type hints.",
            "source": "fastapi_docs.txt",
            "metadata": {"category": "frameworks", "language": "python"}
        },
        {
            "text": "Pytest is a testing framework for Python that makes it easy to write simple and scalable tests.",
            "source": "pytest_guide.txt",
            "metadata": {"category": "testing", "language": "python"}
        }
    ]
