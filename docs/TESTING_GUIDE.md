# Temponest Agentic Platform - Testing Guide

This guide provides comprehensive information on testing the Temponest agentic platform.

## Table of Contents

1. [Testing Environment Setup](#testing-environment-setup)
2. [Unit Testing](#unit-testing)
3. [Integration Testing](#integration-testing)
4. [End-to-End Testing](#end-to-end-testing)
5. [Performance Testing](#performance-testing)
6. [Testing with the SDK](#testing-with-the-sdk)
7. [CI/CD Testing](#cicd-testing)

---

## Testing Environment Setup

### Prerequisites

- Docker and Docker Compose installed
- Python 3.9 or higher
- pytest and pytest-asyncio installed

### Setting Up Test Environment

1. **Start the test environment:**

```bash
cd /home/doctor/temponest/docker
docker-compose up -d
```

2. **Verify all services are healthy:**

```bash
docker-compose ps
```

Expected services:
- agentic-db (PostgreSQL)
- agentic-qdrant (Vector DB)
- agentic-langfuse (Observability)
- agents (Agent Service)
- scheduler (Scheduler Service)
- agentic-prometheus (Metrics)
- alertmanager (Alerts)
- grafana (Dashboards)

3. **Check service health:**

```bash
# Agent Service
curl http://localhost:9000/health

# Scheduler Service
curl http://localhost:9003/health

# Prometheus
curl http://localhost:9091/-/healthy

# Grafana
curl http://localhost:3003/api/health
```

---

## Unit Testing

### Agent Service Tests

```bash
cd /home/doctor/temponest/services/agents
pytest tests/unit/ -v
```

**Key Test Areas:**

1. **Agent CRUD Operations:**
   - Create agent
   - Read agent
   - Update agent
   - Delete agent
   - List agents with filters

2. **Agent Execution:**
   - Single execution
   - Context passing
   - Tool usage
   - Error handling

3. **RAG Integration:**
   - Collection creation
   - Document upload
   - Query execution
   - Relevance scoring

### Scheduler Service Tests

```bash
cd /home/doctor/temponest/services/scheduler
pytest tests/unit/ -v
```

**Key Test Areas:**

1. **Schedule Management:**
   - Create schedule
   - Update cron expression
   - Pause/resume
   - Delete schedule

2. **Task Execution:**
   - Scheduled execution
   - Manual trigger
   - Execution history
   - Error recovery

---

## Integration Testing

### Testing Agent-Scheduler Integration

**Test Script:** `tests/integration/test_agent_scheduler.py`

```python
import pytest
from temponest_sdk import TemponestClient

@pytest.fixture
def client():
    return TemponestClient(base_url="http://localhost:9000")

def test_scheduled_agent_execution(client):
    # Create agent
    agent = client.agents.create(
        name="TestAgent",
        model="llama3.2:latest"
    )

    # Create schedule
    schedule = client.scheduler.create(
        agent_id=agent.id,
        cron_expression="*/5 * * * *",  # Every 5 minutes
        task_config={"user_message": "Test"}
    )

    # Trigger manually
    execution = client.scheduler.trigger(schedule.id)

    # Verify execution
    assert execution.status in ["pending", "running", "completed"]

    # Cleanup
    client.scheduler.delete(schedule.id)
    client.agents.delete(agent.id)
```

**Run Integration Tests:**

```bash
cd /home/doctor/temponest
pytest tests/integration/ -v
```

---

## End-to-End Testing

### Full Workflow Tests

**Test Scenario 1: Agent Creation and Execution**

```bash
# Create agent
curl -X POST http://localhost:9000/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E2ETestAgent",
    "model": "llama3.2:latest",
    "system_prompt": "You are a test assistant."
  }'

# Execute agent (use agent_id from response)
curl -X POST http://localhost:9000/agents/{agent_id}/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_message": "Hello, this is a test",
    "context": {}
  }'

# Verify execution (use execution_id from response)
curl http://localhost:9000/executions/{execution_id}
```

**Test Scenario 2: Scheduled Agent Workflow**

```bash
# Create agent
AGENT_ID=$(curl -s -X POST http://localhost:9000/agents/ \
  -H "Content-Type: application/json" \
  -d '{"name":"ScheduledAgent","model":"llama3.2:latest"}' | jq -r '.id')

# Create schedule
SCHEDULE_ID=$(curl -s -X POST http://localhost:9003/schedules/ \
  -H "Content-Type: application/json" \
  -d "{
    \"agent_id\": \"$AGENT_ID\",
    \"cron_expression\": \"0 * * * *\",
    \"task_config\": {\"user_message\": \"Run scheduled task\"}
  }" | jq -r '.id')

# Trigger schedule
curl -X POST http://localhost:9003/schedules/$SCHEDULE_ID/trigger

# Check execution history
curl http://localhost:9003/schedules/$SCHEDULE_ID/executions
```

---

## Performance Testing

### Load Testing with Apache Bench

**Test Agent Execution Performance:**

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test agent list endpoint
ab -n 1000 -c 10 http://localhost:9000/agents/

# Test health endpoint
ab -n 10000 -c 100 http://localhost:9000/health
```

### Load Testing with Locust

**Install Locust:**

```bash
pip install locust
```

**Create `locustfile.py`:**

```python
from locust import HttpUser, task, between

class AgentServiceUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_agents(self):
        self.client.get("/agents/")

    @task(1)
    def health_check(self):
        self.client.get("/health")
```

**Run Load Test:**

```bash
locust -f locustfile.py --host=http://localhost:9000
```

Access UI at: http://localhost:8089

---

## Testing with the SDK

### SDK Unit Tests

```python
# tests/sdk/test_agents.py
import pytest
from temponest_sdk import TemponestClient
from temponest_sdk.exceptions import AgentNotFoundError

def test_agent_lifecycle():
    client = TemponestClient(base_url="http://localhost:9000")

    # Create
    agent = client.agents.create(
        name="SDKTestAgent",
        model="llama3.2:latest"
    )
    assert agent.id is not None
    assert agent.name == "SDKTestAgent"

    # Read
    retrieved = client.agents.get(agent.id)
    assert retrieved.id == agent.id

    # Update
    updated = client.agents.update(
        agent_id=agent.id,
        description="Updated description"
    )
    assert updated.description == "Updated description"

    # Delete
    client.agents.delete(agent.id)

    # Verify deletion
    with pytest.raises(AgentNotFoundError):
        client.agents.get(agent.id)

    client.close()
```

**Run SDK Tests:**

```bash
cd /home/doctor/temponest/sdk
pytest tests/ -v
```

---

## CI/CD Testing

### GitHub Actions Workflow

**`.github/workflows/test.yml`:**

```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      qdrant:
        image: qdrant/qdrant:latest
        ports:
          - 6333:6333

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r services/agents/requirements.txt
          pip install pytest pytest-asyncio

      - name: Run unit tests
        run: |
          cd services/agents
          pytest tests/unit/ -v

      - name: Run integration tests
        run: |
          pytest tests/integration/ -v

      - name: Run SDK tests
        run: |
          cd sdk
          pip install -e .
          pytest tests/ -v
```

---

## Test Coverage

### Generate Coverage Report

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Target Coverage Goals

- **Unit Tests:** > 80% code coverage
- **Integration Tests:** > 70% code coverage
- **Critical Paths:** 100% coverage

---

## Monitoring Tests

### Verify Metrics Collection

```bash
# Check Prometheus metrics
curl http://localhost:9091/api/v1/query?query=agent_executions_total

# Check specific agent metrics
curl 'http://localhost:9091/api/v1/query?query=agent_executions_total{status="completed"}'
```

### Test Alert Rules

```bash
# Trigger high error rate (for testing)
for i in {1..100}; do
  curl -X POST http://localhost:9000/agents/invalid-id/execute
done

# Check AlertManager
curl http://localhost:9093/api/v2/alerts
```

---

## Troubleshooting Tests

### Common Issues

**1. Service Not Ready:**

```bash
# Wait for service health
timeout 30 bash -c 'until curl -f http://localhost:9000/health; do sleep 1; done'
```

**2. Database Connection:**

```bash
# Check database connectivity
docker exec agentic-db psql -U postgres -c "SELECT 1"
```

**3. Port Conflicts:**

```bash
# Find processes using ports
sudo lsof -i :9000
sudo lsof -i :9003

# Kill conflicting processes
sudo kill -9 <PID>
```

**4. Container Logs:**

```bash
# View service logs
docker-compose logs agents -f
docker-compose logs scheduler -f
```

---

## Best Practices

1. **Isolation:** Each test should be independent
2. **Cleanup:** Always clean up resources after tests
3. **Fixtures:** Use pytest fixtures for common setup
4. **Mocking:** Mock external services in unit tests
5. **Timeouts:** Set appropriate timeouts for async operations
6. **Idempotency:** Tests should be repeatable
7. **Assertions:** Use descriptive assertion messages

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Docker Testing Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Prometheus Testing](https://prometheus.io/docs/prometheus/latest/configuration/unit_testing_rules/)
