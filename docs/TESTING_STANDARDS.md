# Testing Standards

This document defines the testing standards, conventions, and best practices for the TempoNest project.

---

## Table of Contents

1. [Overview](#overview)
2. [Test Naming Conventions](#test-naming-conventions)
3. [Test Structure](#test-structure)
4. [Fixture Patterns](#fixture-patterns)
5. [Mocking Strategies](#mocking-strategies)
6. [Coverage Requirements](#coverage-requirements)
7. [Test Types](#test-types)
8. [Best Practices](#best-practices)
9. [CI/CD Integration](#cicd-integration)
10. [Code Review Checklist](#code-review-checklist)

---

## Overview

TempoNest follows a comprehensive testing strategy based on the testing pyramid:
- **60% Unit Tests**: Fast, isolated tests for individual functions and classes
- **30% Integration Tests**: Tests for API endpoints and service interactions
- **10% E2E Tests**: Complete workflow tests covering critical user paths

### Quality Metrics
- **Test Pass Rate**: 100% (no failing tests in main branch)
- **Coverage Target**: 85%+ overall (varies by component)
- **Test Execution Time**: < 5 minutes (unit + integration), < 15 minutes (E2E)
- **Test Reliability**: Zero flaky tests (deterministic only)

---

## Test Naming Conventions

### Python (pytest)

#### File Names
- Test files: `test_<module_name>.py`
- Location: Mirror source structure in `tests/` directory

```
services/agents/
├── app/
│   ├── agents/
│   │   └── overseer.py
│   └── routers/
│       └── webhooks.py
└── tests/
    ├── unit/
    │   └── agents/
    │       └── test_overseer.py
    └── integration/
        └── test_webhooks_api.py
```

#### Test Function Names
- Format: `test_<function_name>_<scenario>_<expected_result>`
- Use descriptive names that explain what is being tested
- Use underscores for readability

**Good Examples:**
```python
def test_create_agent_success()
def test_create_agent_with_invalid_name_returns_validation_error()
def test_execute_agent_with_timeout_raises_timeout_error()
def test_list_agents_returns_paginated_results()
def test_delete_agent_by_unauthorized_user_returns_403()
```

**Bad Examples:**
```python
def test_agent()  # Too vague
def test1()  # No description
def test_createAgent()  # Wrong naming convention
```

### TypeScript/JavaScript (Vitest/Jest)

#### File Names
- Test files: `<component>.test.tsx` or `<module>.test.ts`
- Location: Co-located with source files or in `__tests__/` directory

#### Test Structure
- Use `describe` blocks for grouping related tests
- Use `it` or `test` for individual test cases
- Be descriptive and specific

**Good Examples:**
```typescript
describe('AgentCard', () => {
  it('renders agent name and type correctly', () => {})
  it('displays loading state when data is being fetched', () => {})
  it('calls onDelete callback when delete button is clicked', () => {})
  it('shows error message when agent execution fails', () => {})
})
```

---

## Test Structure

### Arrange-Act-Assert (AAA) Pattern

All tests should follow the AAA pattern:

```python
def test_create_agent_success(db_session, auth_headers):
    # Arrange: Set up test data and preconditions
    agent_data = {
        "name": "Test Agent",
        "type": "developer",
        "description": "Test description"
    }

    # Act: Execute the function/endpoint being tested
    response = client.post("/agents/", json=agent_data, headers=auth_headers)

    # Assert: Verify the expected outcome
    assert response.status_code == 201
    assert response.json()["name"] == "Test Agent"
    assert response.json()["type"] == "developer"
```

### Test Organization

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (60%)
│   ├── test_models.py
│   ├── test_utils.py
│   └── agents/
│       └── test_overseer.py
├── integration/             # Integration tests (30%)
│   ├── test_agent_api.py
│   └── test_webhook_api.py
└── e2e/                     # End-to-end tests (10%)
    └── test_agent_workflow.py
```

---

## Fixture Patterns

### Python (pytest)

#### Fixture Scope
- `function` (default): New instance for each test
- `class`: Shared across all tests in a class
- `module`: Shared across all tests in a module
- `session`: Shared across entire test session

```python
# conftest.py

@pytest.fixture(scope="session")
def database_engine():
    """Create database engine once per test session."""
    engine = create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(database_engine):
    """Create a new database session for each test."""
    connection = database_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def auth_headers(db_session):
    """Create authenticated user and return auth headers."""
    user = create_test_user(db_session, email="test@example.com")
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_agent(db_session, auth_headers):
    """Create a sample agent for testing."""
    agent_data = {
        "name": "Test Agent",
        "type": "developer",
        "tenant_id": "test-tenant"
    }
    response = client.post("/agents/", json=agent_data, headers=auth_headers)
    return response.json()
```

#### Fixture Best Practices
- Use `autouse=True` sparingly (only for essential setup like database cleanup)
- Use fixture chaining to build complex test data
- Clean up resources in fixture teardown (use `yield`)
- Use factories for creating multiple test objects

```python
@pytest.fixture
def agent_factory(db_session):
    """Factory for creating multiple test agents."""
    def _create_agent(name="Test Agent", agent_type="developer", **kwargs):
        agent = Agent(name=name, type=agent_type, **kwargs)
        db_session.add(agent)
        db_session.commit()
        return agent
    return _create_agent

def test_list_multiple_agents(agent_factory):
    # Create multiple agents using factory
    agent1 = agent_factory(name="Agent 1")
    agent2 = agent_factory(name="Agent 2")
    agent3 = agent_factory(name="Agent 3")

    # Test listing
    response = client.get("/agents/")
    assert len(response.json()) == 3
```

### TypeScript/React (Vitest)

```typescript
// setup.ts
import { beforeEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

beforeEach(() => {
  cleanup()
  localStorage.clear()
  vi.clearAllMocks()
})

// Component test with fixtures
describe('AgentList', () => {
  const mockAgents = [
    { id: '1', name: 'Agent 1', type: 'developer' },
    { id: '2', name: 'Agent 2', type: 'designer' }
  ]

  const mockFetchAgents = vi.fn()

  beforeEach(() => {
    mockFetchAgents.mockResolvedValue(mockAgents)
  })

  it('displays all agents', async () => {
    render(<AgentList fetchAgents={mockFetchAgents} />)

    await waitFor(() => {
      expect(screen.getByText('Agent 1')).toBeInTheDocument()
      expect(screen.getByText('Agent 2')).toBeInTheDocument()
    })
  })
})
```

---

## Mocking Strategies

### When to Mock

**DO Mock:**
- External API calls (HTTP requests)
- Database calls in unit tests
- File system operations
- Time-dependent functions (datetime.now())
- Random number generators
- Third-party services (LLM APIs, email services)

**DON'T Mock:**
- Business logic being tested
- Simple data structures
- Pure functions
- Database calls in integration tests

### Python Mocking

#### Using unittest.mock

```python
from unittest.mock import Mock, patch, MagicMock
import pytest

# Mocking function return values
def test_agent_execution_with_mocked_llm(db_session):
    with patch('app.llm.client.ClaudeClient.generate') as mock_generate:
        mock_generate.return_value = "Mocked response"

        result = execute_agent("test-agent-id", "test message")

        assert result == "Mocked response"
        mock_generate.assert_called_once_with("test message")

# Mocking API calls with httpx
@pytest.fixture
def mock_httpx_client():
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_client.return_value.get.return_value = mock_response
        yield mock_client

def test_fetch_external_data(mock_httpx_client):
    result = fetch_external_data("https://api.example.com/data")
    assert result["status"] == "success"
```

#### Using pytest-mock

```python
def test_agent_creation_with_timestamp(mocker):
    # Mock datetime.now()
    mock_now = datetime(2025, 1, 1, 12, 0, 0)
    mocker.patch('app.models.datetime.now', return_value=mock_now)

    agent = create_agent(name="Test Agent")

    assert agent.created_at == mock_now
```

#### Mocking Environment Variables

```python
@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test_db")
    monkeypatch.setenv("CLAUDE_API_KEY", "test-api-key")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
```

### TypeScript/React Mocking

#### Mocking API Calls

```typescript
import { vi } from 'vitest'

// Mock fetch
global.fetch = vi.fn()

beforeEach(() => {
  (fetch as any).mockResolvedValue({
    ok: true,
    json: async () => ({ data: 'mocked data' })
  })
})

it('fetches and displays data', async () => {
  render(<DataComponent />)

  await waitFor(() => {
    expect(screen.getByText('mocked data')).toBeInTheDocument()
  })

  expect(fetch).toHaveBeenCalledWith('/api/data')
})
```

#### Mocking Modules

```typescript
// Mock entire module
vi.mock('@/lib/api', () => ({
  fetchAgents: vi.fn(() => Promise.resolve([
    { id: '1', name: 'Test Agent' }
  ]))
}))

// Mock specific functions
import { fetchAgents } from '@/lib/api'

vi.mock('@/lib/api')

beforeEach(() => {
  vi.mocked(fetchAgents).mockResolvedValue([
    { id: '1', name: 'Test Agent' }
  ])
})
```

---

## Coverage Requirements

### Overall Targets

| Component | Target | Justification |
|-----------|--------|---------------|
| Backend Services | 85-95% | Critical business logic, complex workflows |
| Frontend (Console) | 75-80% | UI components, some visual-only code |
| Python SDK | 85% | Public API, user-facing functionality |
| CLI Tool | 80-90% | User commands, error handling |

### Service-Specific Targets

| Service | Target | Achieved |
|---------|--------|----------|
| Auth Service | 95%+ | ✅ 97% |
| Agents Service | 90%+ | ✅ 94% |
| Scheduler Service | 85%+ | ✅ 84% |
| Approval UI | 85%+ | ✅ 98% |
| Ingestion | 85%+ | ✅ 92% |
| Temporal Workers | 80%+ | ✅ 92% |
| Console | 75%+ | ✅ 100% pass rate |
| Web UI | 75%+ | ✅ 97% |
| CLI Tool | 80%+ | ✅ 99% |
| Python SDK | 85%+ | ✅ 85% |

### What NOT to Cover

The following code is acceptable to exclude from coverage:
- `if __name__ == "__main__":` blocks
- Abstract base classes not directly tested
- Exception handlers for impossible conditions
- Deprecated code paths
- Debug/logging code
- Type checking code (TYPE_CHECKING blocks)

```python
# .coveragerc
[run]
omit =
    */tests/*
    */conftest.py
    */__main__.py
    */migrations/*
    */scripts/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if __name__ == .__main__.:
    if TYPE_CHECKING:
    raise AssertionError
    raise NotImplementedError
    if 0:
    if False:
```

### Coverage Enforcement

- **PR Requirement**: No coverage decrease allowed
- **Minimum Coverage**: 85% overall
- **New Code**: 100% coverage for new files
- **Modified Code**: Maintain or improve coverage

```bash
# Check coverage in CI
pytest --cov --cov-fail-under=85 --cov-report=term-missing

# Check coverage diff
coverage-diff origin/main HEAD --fail-under=0
```

---

## Test Types

### Unit Tests (60%)

**Purpose**: Test individual functions, classes, and methods in isolation

**Characteristics:**
- Fast (milliseconds)
- No external dependencies (mocked)
- No database or network I/O
- Focus on single responsibility

**Examples:**
```python
# Good unit test
def test_calculate_cost_with_valid_tokens():
    cost = calculate_cost(tokens=1000, model="claude-3-sonnet")
    assert cost == 0.015  # $0.015 per 1K tokens

# Good unit test with mock
def test_hash_password_uses_bcrypt(mocker):
    mock_bcrypt = mocker.patch('app.auth.bcrypt.hashpw')
    hash_password("test_password")
    mock_bcrypt.assert_called_once()
```

### Integration Tests (30%)

**Purpose**: Test interactions between components (API endpoints, database queries, service calls)

**Characteristics:**
- Slower (seconds)
- Real database (test database)
- Real HTTP clients (test client)
- Test multiple components together

**Examples:**
```python
# API endpoint integration test
def test_create_agent_api(db_session, auth_headers):
    response = client.post(
        "/agents/",
        json={"name": "Test Agent", "type": "developer"},
        headers=auth_headers
    )

    assert response.status_code == 201

    # Verify database side effect
    agent = db_session.query(Agent).filter_by(name="Test Agent").first()
    assert agent is not None
    assert agent.type == "developer"

# Service-to-service integration test
@pytest.mark.asyncio
async def test_agent_execution_triggers_webhook(db_session, auth_headers):
    # Create webhook
    webhook = create_webhook(url="http://test.com/hook", events=["agent.completed"])

    # Execute agent
    response = await execute_agent("test-agent-id", "test message")

    # Verify webhook was triggered
    await asyncio.sleep(0.1)  # Wait for async webhook delivery
    assert mock_webhook_delivery.called
```

### E2E Tests (10%)

**Purpose**: Test complete user workflows from start to finish

**Characteristics:**
- Slowest (10+ seconds)
- Real browser (Playwright)
- Complete system integration
- Test critical business paths only

**Examples:**
```typescript
// Playwright E2E test
test('complete single SaaS wizard workflow', async ({ page }) => {
  // Navigate to wizard
  await page.goto('/wizards/single')

  // Fill form
  await page.fill('[name="projectName"]', 'TestSaaS')
  await page.fill('[name="workdir"]', '/tmp/test')
  await page.selectOption('[name="agent"]', 'overseer')

  // Start execution
  await page.click('button:has-text("Run Step")')

  // Wait for streaming logs
  await page.waitForSelector('.log-stream')

  // Verify completion
  await expect(page.locator('.status')).toHaveText('Completed')
  await expect(page.locator('.result')).toContainText('Success')
})
```

---

## Best Practices

### 1. Test Independence

Each test should be completely independent and able to run in any order.

**Good:**
```python
def test_create_agent(db_session):
    # Create agent within test
    agent = Agent(name="Test Agent")
    db_session.add(agent)
    db_session.commit()

    assert db_session.query(Agent).count() == 1

def test_delete_agent(db_session):
    # Create agent within test (not dependent on previous test)
    agent = Agent(name="Test Agent")
    db_session.add(agent)
    db_session.commit()

    db_session.delete(agent)
    db_session.commit()

    assert db_session.query(Agent).count() == 0
```

**Bad:**
```python
# Test order dependency - BAD!
def test_create_agent(db_session):
    agent = Agent(name="Test Agent")
    db_session.add(agent)
    db_session.commit()

def test_delete_agent(db_session):
    # Assumes agent from previous test exists - BAD!
    agent = db_session.query(Agent).first()
    db_session.delete(agent)
    db_session.commit()
```

### 2. Test One Thing

Each test should verify one specific behavior.

**Good:**
```python
def test_create_agent_returns_201():
    response = client.post("/agents/", json={"name": "Test"})
    assert response.status_code == 201

def test_create_agent_returns_agent_data():
    response = client.post("/agents/", json={"name": "Test"})
    assert response.json()["name"] == "Test"
```

**Bad:**
```python
def test_create_agent():
    # Testing multiple things - BAD!
    response = client.post("/agents/", json={"name": "Test"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test"
    assert "id" in response.json()
    agent = db.query(Agent).first()
    assert agent.name == "Test"
```

### 3. Use Descriptive Assertions

```python
# Good
assert agent.status == "active", f"Expected status 'active', got '{agent.status}'"
assert len(agents) == 3, f"Expected 3 agents, got {len(agents)}"

# Bad
assert agent.status == "active"
assert len(agents) == 3
```

### 4. Test Error Cases

Don't just test the happy path - test error conditions too.

```python
def test_create_agent_with_duplicate_name_returns_409():
    # Create first agent
    client.post("/agents/", json={"name": "Test Agent"})

    # Try to create duplicate
    response = client.post("/agents/", json={"name": "Test Agent"})

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()

def test_execute_agent_with_invalid_id_returns_404():
    response = client.post("/agents/nonexistent/execute")
    assert response.status_code == 404
```

### 5. Use Fixtures for Common Setup

```python
# Good - reusable fixture
@pytest.fixture
def authenticated_client(db_session):
    user = create_test_user(db_session)
    token = create_access_token(user.id)
    client.headers = {"Authorization": f"Bearer {token}"}
    return client

def test_list_agents(authenticated_client):
    response = authenticated_client.get("/agents/")
    assert response.status_code == 200

def test_create_agent(authenticated_client):
    response = authenticated_client.post("/agents/", json={"name": "Test"})
    assert response.status_code == 201
```

### 6. Avoid Test Logic

Tests should be simple and straightforward - no complex logic.

**Good:**
```python
def test_agent_execution_cost():
    result = execute_agent("test-agent", tokens=1000)
    assert result.cost == 0.015
```

**Bad:**
```python
def test_agent_execution_cost():
    result = execute_agent("test-agent", tokens=1000)
    # Complex calculation in test - BAD!
    expected_cost = (1000 / 1000) * 0.015
    if result.model == "claude-3-opus":
        expected_cost *= 2
    assert result.cost == expected_cost
```

### 7. Use Parameterized Tests

For testing similar scenarios with different inputs:

```python
@pytest.mark.parametrize("tokens,model,expected_cost", [
    (1000, "claude-3-sonnet", 0.015),
    (2000, "claude-3-sonnet", 0.030),
    (1000, "claude-3-opus", 0.075),
    (0, "claude-3-sonnet", 0.0),
])
def test_calculate_cost(tokens, model, expected_cost):
    cost = calculate_cost(tokens=tokens, model=model)
    assert cost == expected_cost
```

### 8. Clean Test Data

Always clean up test data after tests:

```python
@pytest.fixture
def test_agent(db_session):
    agent = Agent(name="Test Agent")
    db_session.add(agent)
    db_session.commit()

    yield agent

    # Cleanup
    db_session.delete(agent)
    db_session.commit()
```

---

## CI/CD Integration

### GitHub Actions Workflow

Tests run automatically on:
- Every push to any branch
- Every pull request
- Scheduled nightly runs

### Test Stages

1. **Lint & Format Check**: Verify code style
2. **Unit Tests**: Fast tests, run in parallel
3. **Integration Tests**: Service tests with real database
4. **Security Tests**: OWASP vulnerability checks
5. **E2E Tests**: Browser tests (critical paths only)
6. **Coverage Report**: Upload to Codecov

### Branch Protection

- Require all tests to pass before merge
- Require coverage to maintain or increase
- Require at least one approval
- No force pushes to main

### Pre-commit Hooks

Run tests locally before commit:

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Runs automatically on git commit
git commit -m "Add new feature"
```

### Docker Test Environment

Tests run in Docker containers matching production:

```bash
# Run tests in Docker
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Run specific service tests
docker-compose -f docker-compose.test.yml run agents-service pytest tests/
```

---

## Code Review Checklist

When reviewing test code, verify:

### Test Quality
- [ ] Tests follow AAA pattern (Arrange-Act-Assert)
- [ ] Test names are descriptive and follow naming conventions
- [ ] Each test verifies one specific behavior
- [ ] Tests are independent and can run in any order
- [ ] Tests use appropriate fixtures and mocks
- [ ] Tests include both happy path and error cases

### Coverage
- [ ] New code has 100% test coverage
- [ ] Modified code maintains or improves coverage
- [ ] Critical paths have E2E test coverage
- [ ] Edge cases are tested

### Performance
- [ ] Tests run quickly (unit tests < 100ms)
- [ ] No unnecessary database queries
- [ ] Mocks are used appropriately
- [ ] No sleep/wait calls (use proper async/await)

### Reliability
- [ ] Tests are deterministic (no random data)
- [ ] No flaky tests (timing issues)
- [ ] Database state is cleaned between tests
- [ ] External dependencies are mocked

### Documentation
- [ ] Complex test logic is commented
- [ ] Fixtures are documented
- [ ] Test file has module docstring if needed

---

## Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Library](https://testing-library.com/)
- [Playwright Documentation](https://playwright.dev/)

### Internal Guides
- [Testing Roadmap](./TESTING_ROADMAP.md) - Testing progress and milestones
- [Coverage Summary](./COVERAGE_SUMMARY_2025-11-11.md) - Latest coverage analysis
- Project README - Setup and testing commands

### Tools
- pytest: Python testing framework
- pytest-cov: Coverage plugin
- pytest-asyncio: Async test support
- pytest-mock: Mocking utilities
- Vitest: TypeScript/React testing
- Playwright: E2E browser testing
- Codecov: Coverage reporting

---

**Last Updated**: 2025-11-11
**Owner**: Development Team
**Version**: 1.0
