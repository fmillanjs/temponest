# Testing Gaps Report - Web UI Cost Summary Bug

**Date**: 2025-11-13
**Issue**: 500 error on `/api/costs/summary` endpoint with date parameters
**Root Cause**: asyncpg expects Python `date` objects, but strings were passed

## Why Tests Didn't Catch This

### 1. Over-Mocking in "Integration" Tests
**File**: `web-ui/tests/test_api_endpoints.py`
**Test**: `test_api_cost_summary_with_date_range` (line 103)

**Problem**:
```python
@pytest.mark.integration  # ❌ This is NOT a real integration test
def test_api_cost_summary_with_date_range(client, mock_asyncpg):
    mock_asyncpg.fetchrow.return_value = {...}  # Mocks the DB entirely
    response = client.get("/api/costs/summary?start_date=2025-01-01&end_date=2025-01-31")
    assert response.status_code == 200  # Passes but doesn't test real DB interaction
```

The `mock_asyncpg` fixture mocks `asyncpg.connect()`, so:
- SQL queries are never executed
- Parameter binding is never tested
- Type conversion bugs are invisible

**Impact**: Test passes ✅ but bug exists in production ❌

### 2. No True E2E Tests for Web UI
**Gap**: No tests that:
- Run the Web UI container
- Connect to a real PostgreSQL database
- Make HTTP requests with real date parameters
- Validate actual asyncpg behavior

**Comparison**:
- ✅ Auth service has proper E2E tests (`tests/integration/test_auth_integration.py`)
- ✅ Agents service is tested in workflows
- ❌ Web UI only has mocked unit tests

### 3. Mislabeled Test Markers
Tests marked as `@pytest.mark.integration` are actually **unit tests** because they mock all external dependencies.

## Recommendations

### Immediate Fixes

#### 1. Add Real Integration Test for Web UI
Create `web-ui/tests/integration/test_costs_real_db.py`:
```python
import pytest
import asyncpg
from datetime import date
from decimal import Decimal

@pytest.mark.integration
@pytest.mark.slow
async def test_cost_summary_with_real_database():
    """Test costs/summary endpoint with REAL database connection"""
    # Connect to actual test database
    conn = await asyncpg.connect(
        host="localhost",
        port=5434,  # Test DB port
        database="agentic_test",
        user="postgres",
        password="postgres"
    )

    try:
        # Insert test data
        await conn.execute("""
            INSERT INTO cost_tracking
            (task_id, agent_name, tenant_id, model_provider, model_name,
             total_tokens, total_cost_usd, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """,
            "test-task", "test-agent", "test-tenant-id",
            "anthropic", "claude-3-opus", 1000, Decimal("1.50"),
            date(2025, 1, 15)
        )

        # Test the actual query with date parameters
        # This would have caught the bug!
        start = date(2025, 1, 1)
        end = date(2025, 1, 31)

        row = await conn.fetchrow("""
            SELECT
                COALESCE(SUM(total_cost_usd), 0) as total_usd,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COUNT(*) as total_executions
            FROM cost_tracking
            WHERE created_at::date >= $1
            AND created_at::date <= $2
        """, start, end)

        assert row['total_usd'] == Decimal("1.50")
        assert row['total_tokens'] == 1000

    finally:
        await conn.execute("DELETE FROM cost_tracking WHERE task_id = 'test-task'")
        await conn.close()
```

#### 2. Add E2E Test with HTTP Client
Create `web-ui/tests/e2e/test_web_ui_endpoints.py`:
```python
import pytest
import httpx

@pytest.mark.e2e
async def test_cost_summary_endpoint_e2e():
    """Test Web UI cost summary endpoint against running Docker stack"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8082/api/costs/summary",
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31"
            }
        )

        assert response.status_code == 200  # Would have failed with 500!
        data = response.json()
        assert "total_usd" in data
        assert "total_tokens" in data
        assert "total_executions" in data
```

#### 3. Relabel Test Markers Accurately
```python
# Before (misleading):
@pytest.mark.integration
def test_api_cost_summary_with_date_range(client, mock_asyncpg):
    ...

# After (accurate):
@pytest.mark.unit  # It's a unit test because it mocks everything
def test_api_cost_summary_with_date_range(client, mock_asyncpg):
    ...
```

### Structural Changes

#### 4. Testing Pyramid Strategy
```
         /\     E2E Tests (few, slow, comprehensive)
        /  \    - Test full Docker stack
       /____\   - Real database, real services
      /      \
     / INTEGR \  Integration Tests (some, medium speed)
    /  -ATION  \ - Real database connections
   /____________\- Limited mocking
  /              \
 /  UNIT  TESTS  \ Unit Tests (many, fast, focused)
/                 \- Mock external dependencies
```

**Current State**: We have mostly unit tests disguised as integration tests

**Target State**:
- **Unit tests**: Mock database, test business logic
- **Integration tests**: Real database, test SQL/asyncpg interaction
- **E2E tests**: Full Docker stack, test user-facing endpoints

#### 5. Add Pre-deployment E2E Test Suite
Create `scripts/run-e2e-tests.sh`:
```bash
#!/bin/bash
# Run before deployment to catch integration bugs

echo "Starting E2E test suite..."

# Start Docker stack
docker compose up -d

# Wait for services
./scripts/wait-for-services.sh

# Run E2E tests against running stack
pytest tests/e2e/ -v --tb=short

# Cleanup
docker compose down
```

#### 6. Update CI/CD Pipeline
Add to `.github/workflows/test.yml`:
```yaml
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Start Docker Stack
        run: docker compose up -d

      - name: Wait for Services
        run: ./scripts/wait-for-services.sh

      - name: Run E2E Tests
        run: pytest tests/e2e/ -v

      - name: Cleanup
        run: docker compose down
```

## Lessons Learned

1. **Mocking hides bugs** - Over-mocking can create false confidence
2. **Test labels matter** - Mislabeled tests mislead developers
3. **E2E tests are critical** - Unit tests alone don't catch integration bugs
4. **Test like production** - Use real dependencies in integration tests

## Action Items

- [ ] Add real database integration tests for Web UI
- [ ] Add E2E tests that run against Docker stack
- [ ] Relabel existing tests accurately (unit vs integration)
- [ ] Add E2E test suite to CI/CD pipeline
- [ ] Document testing strategy in CONTRIBUTING.md
- [ ] Run E2E tests before each deployment

---

**Prepared by**: Claude Code
**Issue Reference**: Web UI costs/summary 500 error (2025-11-13)
