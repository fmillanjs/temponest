# Testing Patterns

**Analysis Date:** 2026-03-04

## Test Framework

**Runner:**
- pytest `>=7.4.0,<8.0.0`
- Config: `services/agents/pytest.ini`, `services/ingestion/pytest.ini`, `services/auth/pytest.ini`, `services/temporal_workers/pytest.ini`, `services/approval_ui/pytest.ini`, `services/scheduler/pytest.ini`, `sdk/pytest.ini`, `web-ui/pytest.ini`, `tests/integration/pytest.ini`
- Each service has its own `pytest.ini` — tests are run per-service, not from root

**Key pytest plugins:**
- `pytest-asyncio>=0.21.0` — async test support with `asyncio_mode = auto`
- `pytest-cov>=4.1.0` — coverage reporting
- `pytest-xdist>=3.3.0` — parallel test execution (`-n auto --dist loadgroup`)
- `pytest-timeout>=2.1.0` — timeout enforcement
- `pytest-mock>=3.11.0` — mock helpers

**Assertion Library:**
- pytest built-in `assert` statements

**Run Commands (from service directory):**
```bash
cd services/agents
pytest                          # Run all tests with coverage
pytest tests/unit/              # Run unit tests only
pytest tests/integration/       # Run integration tests only
pytest tests/e2e/               # Run e2e tests only
pytest -m unit                  # Run by marker
pytest -m "not e2e"             # Exclude e2e tests
pytest --no-cov                 # Skip coverage (faster)
pytest -x                       # Stop on first failure
```

## Test File Organization

**Location:** Separate `tests/` directory per service (not co-located with source)

**Structure:**
```
services/agents/tests/
├── __init__.py
├── conftest.py                         # Session-scoped fixtures, env setup, mock clients
├── unit/
│   ├── __init__.py
│   ├── test_cost_calculator.py
│   ├── test_rag_memory.py
│   ├── test_rate_limiting.py
│   ├── test_webhook_manager.py
│   ├── test_claude_client.py
│   ├── test_settings.py
│   └── agents/
│       ├── __init__.py
│       ├── test_developer.py
│       ├── test_overseer.py
│       ├── test_qa_tester.py
│       ├── test_devops.py
│       ├── test_designer.py
│       ├── test_security_auditor.py
│       ├── test_ux_researcher.py
│       └── test_factory.py
├── integration/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_main_api.py
│   ├── test_departments_routes.py
│   ├── test_webhooks_routes.py
│   └── test_health_api.py
└── e2e/
    ├── __init__.py
    └── test_agent_workflow.py
```

**Naming:**
- Files: `test_<module_name>.py`
- Classes: `Test<ClassName>`
- Methods: `test_<behavior_description>`

## Test Structure

**Suite Organization:**
```python
"""
Unit tests for cost calculator.
"""

import pytest
from decimal import Decimal
from app.cost.calculator import CostCalculator


class TestCostCalculator:
    """Test suite for CostCalculator"""

    def test_calculate_cost_claude_sonnet(self):
        """Test cost calculation for Claude Sonnet"""
        calc = CostCalculator()

        input_cost, output_cost, total_cost = calc.calculate_cost(
            provider="claude",
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500
        )

        # Claude Sonnet: $3/1M input, $15/1M output
        assert input_cost == Decimal("0.003000")
        assert output_cost == Decimal("0.007500")
        assert total_cost == Decimal("0.010500")
```

**Patterns:**
- All test logic in class methods grouped by `Test<Subject>` class
- Each test method is fully self-contained (no shared state between tests)
- Descriptive one-liner docstring per test describing the scenario
- `pytest.fixture` methods defined inside the test class for per-class scope
- `asyncio_mode = auto` — no need to decorate async tests with `@pytest.mark.asyncio` (but `@pytest.mark.asyncio` is still used explicitly in many tests for clarity)

## Markers

Defined in `pytest.ini` and auto-applied by path via `conftest.py`:
```
unit        - Tests in tests/unit/
integration - Tests in tests/integration/ (require database)
e2e         - Tests in tests/e2e/ (require full service stack)
slow        - Tests that take significant time
```

Auto-marker hook in `services/agents/tests/conftest.py`:
```python
def pytest_collection_modifyitems(config, items):
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
```

## Mocking

**Framework:** `unittest.mock` — `Mock`, `AsyncMock`, `MagicMock`, `patch`

**Patterns:**

Async dependency mocking:
```python
@pytest.fixture
def mock_rag_memory(self):
    """Create mock RAG memory"""
    mock = AsyncMock()
    mock.retrieve = AsyncMock(return_value=[
        {"source": "docs/api/crud.md", "version": "v1.0", "score": 0.95, "content": "..."}
    ])
    return mock
```

Class-level patching for heavy imports (CrewAI):
```python
def developer_agent(self, mock_rag_memory, mock_tracer):
    with patch('app.agents.developer.Agent'):
        agent = DeveloperAgent(rag_memory=mock_rag_memory, tracer=mock_tracer, code_model="test-model")
        return agent
```

Context manager patching for execution:
```python
async def test_execute_success(self, mock_rag_memory, mock_tracer):
    with patch('app.agents.developer.Agent') as mock_agent_class:
        with patch('app.agents.developer.Crew') as mock_crew_class:
            with patch('app.agents.developer.Task') as mock_task_class:
                mock_crew = MagicMock()
                mock_crew.kickoff = Mock(return_value='{"implementation": "def hello(): pass"}')
                mock_crew_class.return_value = mock_crew
                result = await developer_agent.execute(...)
```

Global patch for external services (in `conftest.py`):
```python
@pytest.fixture
def mock_ollama():
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "...", "done": True}
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        yield mock_client
```

**What to Mock:**
- All external HTTP calls (Ollama, Qdrant, Langfuse, Auth service)
- Database pools (`asyncpg.Pool`) in unit tests
- CrewAI `Agent`, `Task`, `Crew` classes in unit tests
- Redis connections
- Auth middleware for integration tests (set `auth_middleware._auth_client` directly)

**What NOT to Mock:**
- Pure business logic (e.g., `CostCalculator.calculate_cost`, `validate_citations`)
- Pydantic models
- Settings (override via `os.environ` in `conftest.py` before import)

## Environment Setup for Tests

`conftest.py` sets all required env vars **before** importing the app:
```python
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5434/test_agentic")
os.environ["OLLAMA_BASE_URL"] = "http://test-ollama:11434"
os.environ["QDRANT_URL"] = "http://test-qdrant:6333"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-min-32-characters-long"

# Import after setting environment
from app.main import app
```

## Fixtures and Factories

**Test data fixtures in `conftest.py`:**
```python
@pytest.fixture
def test_agent_request() -> Dict[str, Any]:
    """Standard agent request payload"""
    return {
        "task": "Create a Python function to calculate fibonacci numbers",
        "context": {"language": "python", "requirements": ["Use recursion", "Add docstring"]},
        "risk_level": "low",
        "project_id": "test-project-123",
        "workflow_id": "test-workflow-456"
    }

@pytest.fixture
def test_tenant_id() -> UUID:
    return uuid4()
```

**Database fixtures (integration/e2e only):**
```python
@pytest.fixture
async def test_webhook(db_pool, test_tenant_id, test_user_id):
    """Create a test webhook (only runs for integration/e2e tests)"""
    if not db_pool:
        return None
    webhook_id = uuid4()
    async with db_pool.acquire() as conn:
        await conn.execute("""INSERT INTO webhooks (...) VALUES ($1, $2, ...)""", ...)
    return {"id": webhook_id, "url": "https://example.com/webhook", "secret_key": "test-secret"}
```

**Fixture scope:**
- `scope="session"` for `event_loop`, `db_pool`, `setup_test_database`
- `scope="function"` (default) for all data and mock fixtures

**Location:** `services/agents/tests/conftest.py` for session-level fixtures. Per-class fixtures defined inline as `@pytest.fixture` methods.

**Available fixture libraries:** `faker>=19.0.0`, `factory-boy>=3.3.0` (declared in `requirements-test.txt` but not widely used yet — prefer explicit dict fixtures)

## HTTP Client Testing

Integration tests use `httpx.AsyncClient` mounted against the FastAPI app:
```python
@pytest.fixture
async def client(request) -> AsyncGenerator[AsyncClient, None]:
    if "integration" in str(request.fspath) or "e2e" in str(request.fspath):
        # Mock auth middleware
        auth_middleware._auth_client = mock_auth_client
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
        auth_middleware._auth_client = None
    else:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
```

Auth headers fixture for routes requiring authentication:
```python
@pytest.fixture
def test_auth_headers(test_user_id, test_tenant_id) -> Dict[str, str]:
    return {
        "Authorization": "Bearer test-token",
        "X-User-ID": str(test_user_id),
        "X-Tenant-ID": str(test_tenant_id)
    }
```

## Coverage

**Requirements:**
- Project target: 85% overall (enforced via Codecov)
- Agents service: 90% target
- Auth service: 95% target
- New code on PRs: 100% target
- `--cov-fail-under=0` in `pytest.ini` (local threshold disabled; Codecov enforces remotely)

**Codecov config:** `/home/doctor/temponest/codecov.yml`

**View Coverage:**
```bash
cd services/agents
pytest --cov=app --cov-report=html
open htmlcov/index.html          # Coverage HTML report
cat coverage.xml                 # XML for CI upload
```

**Coverage artifacts:** `services/agents/coverage.json`, `services/agents/coverage.xml`, `services/agents/htmlcov/`

## Test Types

**Unit Tests** (`tests/unit/`):
- Test individual classes and functions in isolation
- All external dependencies mocked
- No database, no HTTP, no filesystem
- Fast — should complete in milliseconds each
- Examples: `test_cost_calculator.py`, `test_developer.py`, `test_rag_memory.py`

**Integration Tests** (`tests/integration/`):
- Test API routes via `httpx.AsyncClient` against live FastAPI app
- Auth middleware mocked; other external deps mocked as needed
- Database used if available (skipped gracefully if no pool)
- Examples: `test_main_api.py`, `test_webhooks_routes.py`, `test_health_api.py`

**E2E Tests** (`tests/e2e/`):
- Test complete workflows against the full stack
- Most are decorated `@pytest.mark.skip(reason="Requires full service dependencies")`
- Intended to run manually with `docker-compose up`
- Example: `test_agent_workflow.py`

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_search_code_examples_with_results(self, developer_agent, mock_rag_memory):
    """Test search code examples tool returns formatted results"""
    tool = developer_agent._create_search_code_examples_tool()
    result = await tool.func("CRUD API endpoint")

    mock_rag_memory.retrieve.assert_called_once_with(
        query="code example: CRUD API endpoint",
        top_k=5,
        min_score=0.7
    )
    assert "[Example 1]" in result
```

**Error Testing:**
```python
@pytest.mark.asyncio
async def test_execute_error_handling(self, mock_rag_memory, mock_tracer):
    """Test error handling during execution"""
    mock_rag_memory.retrieve = AsyncMock(side_effect=Exception("RAG failure"))

    with patch('app.agents.developer.Agent'):
        developer_agent = DeveloperAgent(rag_memory=mock_rag_memory, tracer=mock_tracer, code_model="test-model")

        with pytest.raises(Exception) as exc_info:
            await developer_agent.execute(task="Generate code", context={}, task_id="task-error")

        assert "RAG failure" in str(exc_info.value)
```

**Integration endpoint testing — accept multiple valid status codes:**
```python
async def test_overseer_execution_with_mocks(self, mock_cost_tracker, mock_overseer, client, test_auth_headers):
    response = await client.post("/overseer/run", json={"task": "Analyze this", "risk_level": "low"}, headers=test_auth_headers)
    # Accept various valid states (503 = deps unavailable in test env)
    assert response.status_code in [200, 401, 422, 503]
```

**Assertion style — prefer specific values:**
```python
assert input_cost == Decimal("0.003000")   # Not: assert input_cost > 0
assert result["citations"][0]["source"] == "docs/api/crud.md"
assert "✓ Basic syntax validation passed" in result
```

---

*Testing analysis: 2026-03-04*
