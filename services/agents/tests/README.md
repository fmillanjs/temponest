# Agents Service Tests

Comprehensive test suite for the Agents service, covering unit tests, integration tests, and end-to-end tests.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, no external dependencies)
│   ├── test_cost_calculator.py
│   ├── test_cost_tracker.py
│   └── test_webhook_models.py
├── integration/             # Integration tests (require database)
│   ├── test_health_api.py
│   └── test_main_api.py
└── e2e/                     # End-to-end tests (full service stack)
    └── test_agent_workflow.py
```

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Types

```bash
# Unit tests only (fast, no external dependencies)
pytest -m unit

# Integration tests (requires database)
pytest -m integration

# End-to-end tests (requires full service stack)
pytest -m e2e
```

### Run with Coverage

```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Specific Test Files

```bash
pytest tests/unit/test_cost_calculator.py
pytest tests/integration/test_health_api.py -v
```

### Run in Docker Container

```bash
# Run tests inside the agents container
docker exec agentic-agents pytest /app/tests/ -v

# Run with coverage
docker exec agentic-agents pytest /app/tests/ --cov=app --cov-report=xml
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Tests requiring database/external services
- `@pytest.mark.e2e` - Full end-to-end workflow tests
- `@pytest.mark.slow` - Tests that take significant time

## Test Fixtures

Common fixtures are defined in `conftest.py`:

### Database Fixtures
- `db_pool` - AsyncPG connection pool
- `setup_test_database` - Initialize test database
- `clean_database` - Clean database before each test

### Mock Fixtures
- `mock_ollama` - Mock Ollama API
- `mock_qdrant` - Mock Qdrant vector database
- `mock_auth_client` - Mock Auth service client
- `mock_langfuse` - Mock Langfuse tracer

### Data Fixtures
- `test_tenant_id`, `test_user_id`, `test_project_id`
- `test_agent_request`, `test_agent_response`
- `test_auth_headers`, `test_auth_context`

### HTTP Client
- `client` - Async HTTP client for API testing

## Coverage Goals

- **Unit Tests**: 90%+ coverage of business logic
- **Integration Tests**: 80%+ coverage of API endpoints
- **E2E Tests**: Critical user workflows

Current coverage targets by module:
- `cost/calculator.py` - 95%+
- `cost/tracker.py` - 90%+
- `webhooks/` - 85%+
- `memory/rag.py` - 85%+
- API endpoints - 80%+

## Writing New Tests

### Unit Test Example

```python
@pytest.mark.unit
class TestMyFeature:
    def test_feature_success(self):
        # Test implementation
        pass

    def test_feature_validation_error(self):
        # Test error cases
        pass
```

### Integration Test Example

```python
@pytest.mark.integration
class TestMyAPI:
    @pytest.mark.asyncio
    async def test_endpoint(self, client, clean_database):
        response = await client.post("/endpoint", json={...})
        assert response.status_code == 200
```

### E2E Test Example

```python
@pytest.mark.e2e
class TestWorkflow:
    @pytest.mark.asyncio
    async def test_full_workflow(self, client, test_auth_headers):
        # Complete workflow test
        pass
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled nightly builds

See `.github/workflows/tests.yml` for CI configuration.

## Troubleshooting

### Tests fail with "ModuleNotFoundError"

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Database connection errors

Ensure test database is running and `TEST_DATABASE_URL` is set:
```bash
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5434/test_agentic"
```

### Integration tests skip unexpectedly

Integration tests are automatically skipped if they're not in an integration test path. Ensure tests are in `tests/integration/` directory.

## Best Practices

1. **Keep unit tests fast** - Mock external dependencies
2. **Test edge cases** - Test validation errors and edge conditions
3. **Use descriptive names** - Test names should describe what they test
4. **One assertion focus** - Each test should focus on one behavior
5. **Clean up resources** - Use fixtures for setup/teardown
6. **Test both success and failure** - Cover happy path and error cases
7. **Use async/await properly** - Mark async tests with `@pytest.mark.asyncio`
8. **Mock external services** - Don't depend on live external APIs in unit tests

## Related Documentation

- [Testing Roadmap](../../../docs/TESTING_ROADMAP.md)
- [Testing Guide](../../../docs/TESTING_GUIDE.md)
- [Pytest Documentation](https://docs.pytest.org/)
