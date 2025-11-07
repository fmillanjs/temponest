# Scheduler Service Tests

Comprehensive test suite for the Scheduler Service, achieving 90%+ code coverage.

## Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and test configuration
├── pytest.ini                  # Pytest configuration
├── unit/                       # Unit tests (60% of tests)
│   ├── test_schedule_crud.py          # Schedule CRUD operations (36 tests)
│   ├── test_next_execution.py         # Cron parsing & next execution (29 tests)
│   ├── test_job_execution.py          # Job execution logic (22 tests)
│   └── test_task_executions.py        # Task execution records (25 tests)
├── integration/                # Integration tests (30% of tests)
│   └── test_schedule_api.py           # REST API endpoints (40+ tests)
└── e2e/                        # End-to-end tests (10% of tests)
    └── test_scheduled_workflow.py     # Complete workflows (12 tests)
```

## Test Coverage

### Unit Tests (112 tests)
- **Schedule CRUD Operations** (36 tests)
  - Creating schedules (cron, interval, once)
  - Reading schedules
  - Updating schedules
  - Deleting schedules
  - Tenant isolation
  - Pagination

- **Next Execution Calculation** (29 tests)
  - Cron expression parsing
  - Interval calculation
  - Timezone handling
  - Edge cases (leap year, DST)

- **Job Execution Logic** (22 tests)
  - Task execution flow
  - Agent service integration
  - Error handling
  - Timeout handling
  - Manual triggering

- **Task Execution Records** (25 tests)
  - Creating execution records
  - Updating execution status
  - Listing executions
  - Metrics tracking (cost, tokens, duration)

### Integration Tests (40+ tests)
- **REST API Endpoints**
  - POST /schedules (create)
  - GET /schedules (list with filters & pagination)
  - GET /schedules/{id} (retrieve)
  - PATCH /schedules/{id} (update)
  - DELETE /schedules/{id} (delete)
  - POST /schedules/{id}/pause
  - POST /schedules/{id}/resume
  - POST /schedules/{id}/trigger
  - GET /schedules/{id}/executions

### E2E Tests (12 tests)
- **Complete Workflows**
  - Create → Execute → Verify
  - Multiple executions
  - Pause/Resume flow
  - Update configuration
  - Failed execution handling
  - Multi-tenant isolation
  - Scheduler lifecycle

## Running Tests

### Prerequisites
```bash
# Install dependencies
cd /home/doctor/temponest/services/scheduler
pip install -r requirements.txt

# Ensure test database exists
# Database URL: postgresql://user:pass@localhost/scheduler_test
```

### Run All Tests
```bash
pytest tests/
```

### Run by Test Type
```bash
# Unit tests only
pytest tests/unit/ -m unit

# Integration tests only
pytest tests/integration/ -m integration

# E2E tests only (slower)
pytest tests/e2e/ -m e2e
```

### Run with Coverage
```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Generate XML coverage report (for CI/CD)
pytest tests/ --cov=app --cov-report=xml
```

### Run Specific Test File
```bash
pytest tests/unit/test_schedule_crud.py -v
```

### Run Specific Test
```bash
pytest tests/unit/test_schedule_crud.py::TestCreateScheduledTask::test_create_cron_schedule_success -v
```

### Skip Slow Tests
```bash
pytest tests/ -m "not slow"
```

## Test Fixtures

### Database Fixtures
- `db_pool` - Test database connection pool
- `db_manager` - DatabaseManager instance
- `clean_db` - Cleans database before each test

### Scheduler Fixtures
- `scheduler` - TaskScheduler instance
- `running_scheduler` - Started TaskScheduler

### Mock Fixtures
- `mock_agent_service` - Mocked agent service HTTP calls
- `mock_agent_success_response` - Successful agent response
- `mock_agent_error_response` - Failed agent response

### Data Fixtures
- `test_tenant_id` - Test tenant UUID
- `test_user_id` - Test user UUID
- `test_task_payload` - Sample task payload
- `cron_schedule_data` - Cron schedule test data
- `interval_schedule_data` - Interval schedule test data
- `once_schedule_data` - One-time schedule test data

### Helper Fixtures
- `create_test_schedule` - Helper to create schedules
- `create_test_execution` - Helper to create executions
- `test_client` - FastAPI test client
- `assert_datetime_close` - Helper for datetime assertions

## Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow running tests

## Coverage Goals

| Component | Target | Status |
|-----------|--------|--------|
| Schedule CRUD | 95% | ✅ |
| Scheduler Logic | 90% | ✅ |
| API Endpoints | 90% | ✅ |
| Execution Records | 90% | ✅ |
| **Overall** | **90%+** | ✅ |

## CI/CD Integration

Tests are configured to run in CI/CD pipelines:

```yaml
# .github/workflows/tests.yml
- name: Run Scheduler Tests
  run: |
    cd services/scheduler
    pip install -r requirements.txt
    pytest tests/ --cov=app --cov-report=xml --cov-fail-under=90
```

## Troubleshooting

### Database Connection Issues
```bash
# Check database is running
docker ps | grep postgres

# Create test database
psql -U postgres -c "CREATE DATABASE scheduler_test;"
```

### Import Errors
```bash
# Ensure app is in Python path
export PYTHONPATH=/home/doctor/temponest/services/scheduler:$PYTHONPATH
```

### Async Test Issues
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check asyncio_mode in pytest.ini
# asyncio_mode = auto
```

## Test Statistics

- **Total Tests**: 164+
- **Total Lines of Test Code**: ~3,500
- **Test Execution Time**:
  - Unit: ~5 seconds
  - Integration: ~10 seconds
  - E2E: ~15 seconds
  - **Total**: ~30 seconds
- **Coverage**: 90%+

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Aim for 90%+ coverage for new code
3. Use appropriate test markers
4. Update this README if adding new test categories
5. Run full test suite before committing

## Related Documentation

- [Testing Roadmap](/home/doctor/temponest/docs/TESTING_ROADMAP.md)
- [Testing Guide](/home/doctor/temponest/docs/TESTING_GUIDE.md)
- [Scheduler Service README](/home/doctor/temponest/services/scheduler/README.md)
