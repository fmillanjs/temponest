# TempoNest Performance Tests

Performance and load testing suite using Locust for the TempoNest platform.

## Overview

This directory contains Locust-based performance tests for the TempoNest platform. The tests measure:
- API response times
- Throughput (requests/second)
- Concurrent user handling
- System stability under load

## Performance Targets

| Metric | Target | Description |
|--------|--------|-------------|
| Agent Execution | < 2s p95 | Agent execution should complete within 2 seconds for 95% of requests |
| RAG Queries | < 500ms p95 | RAG document queries should complete within 500ms for 95% of requests |
| API Endpoints | < 200ms p95 | General API endpoints should respond within 200ms for 95% of requests |
| Concurrent Users | 100+ | System should handle 100+ concurrent users |

## Test Structure

```
tests/performance/
├── locustfile.py              # Main test suite (general usage)
├── scenarios/
│   ├── agent_execution.py     # Agent execution focused tests
│   ├── rag_queries.py         # RAG query focused tests
│   └── api_endpoints.py       # API endpoint focused tests
└── reports/                   # Generated test reports
```

## Prerequisites

```bash
# Install Locust
pip install locust

# Ensure Docker containers are running
docker ps
```

## Running Tests

### 1. General Load Test (Web UI)

Run with interactive web UI:

```bash
# From project root
cd /home/doctor/temponest

# Run with web UI on http://localhost:8089
locust -f tests/performance/locustfile.py --host=http://localhost:9002
```

Then open http://localhost:8089 and configure:
- Number of users
- Spawn rate
- Host URL

### 2. Headless Mode (Automated)

Run without web UI for CI/CD:

```bash
# Run with 50 users, spawn rate 5/sec for 2 minutes
locust -f tests/performance/locustfile.py \
    --host=http://localhost:9002 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 2m \
    --headless

# Generate HTML report
locust -f tests/performance/locustfile.py \
    --host=http://localhost:9002 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless \
    --html=tests/performance/reports/performance_report.html
```

### 3. Scenario-Specific Tests

#### Agent Execution Performance

```bash
locust -f tests/performance/scenarios/agent_execution.py \
    --host=http://localhost:9000 \
    --users 20 \
    --spawn-rate 2 \
    --run-time 5m \
    --headless \
    --html=tests/performance/reports/agent_execution_report.html
```

#### RAG Query Performance

```bash
locust -f tests/performance/scenarios/rag_queries.py \
    --host=http://localhost:9000 \
    --users 50 \
    --spawn-rate 5 \
    --run-time 5m \
    --headless \
    --html=tests/performance/reports/rag_queries_report.html
```

#### API Endpoint Performance

```bash
locust -f tests/performance/scenarios/api_endpoints.py \
    --host=http://localhost:9002 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless \
    --html=tests/performance/reports/api_endpoints_report.html
```

## Understanding Results

### Key Metrics

1. **RPS (Requests Per Second)**: Total throughput
2. **Average Response Time**: Mean response time across all requests
3. **Median Response Time**: 50th percentile response time
4. **95th Percentile**: 95% of requests complete within this time
5. **99th Percentile**: 99% of requests complete within this time
6. **Failure Rate**: Percentage of failed requests

### Example Output

```
Name                                    # reqs      # fails  |     Avg     Min     Max  Median  |   req/s failures/s
-----------------------------------------------------------------------------------------------------------------
GET /agents/                              1245         0     |      89      45     234      82  |    20.8      0.0
POST /agents/{id}/execute                  423        12     |    1567     892    4523    1432  |     7.1      0.2
GET /health                               2890         0     |      12       5      89      11  |    48.2      0.0
-----------------------------------------------------------------------------------------------------------------
Aggregated                                4558        12     |     245       5    4523      89  |    76.1      0.2

Response time percentiles (approximated):
 Type     Name                                                          50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100%
----------------------------------------------------------------------------------------------------------------------------------------------------
 GET      /agents/                                                       82     92    101    108    124    145    189    212    234    234    234
 POST     /agents/{id}/execute                                         1432   1678   1823   1912   2234   2567   3234   3892   4523   4523   4523
 GET      /health                                                        11     12     13     14     16     18     23     34     89     89     89
----------------------------------------------------------------------------------------------------------------------------------------------------
```

## Interpreting Results

### Success Criteria

- ✅ **95th percentile ≤ target**: Performance meets expectations
- ⚠️ **95th percentile > target but < 2x target**: Acceptable but needs optimization
- ❌ **95th percentile > 2x target**: Performance issue, needs investigation

### Common Issues

1. **High latency on agent execution**:
   - Check LLM provider API latency
   - Review agent configuration (max_tokens, temperature)
   - Consider caching strategies

2. **High latency on RAG queries**:
   - Check Qdrant performance
   - Review collection size and indexing
   - Optimize query parameters (top_k)

3. **High failure rate**:
   - Check service logs for errors
   - Review rate limiting settings
   - Check database connection pools

## Best Practices

1. **Warm-up**: Run tests for at least 2-3 minutes to get stable results
2. **Baseline**: Establish baseline metrics before making changes
3. **Isolation**: Test one scenario at a time for accurate results
4. **Realistic Load**: Use realistic user behavior patterns
5. **Monitor Resources**: Check CPU, memory, database during tests

## CI/CD Integration

Add to your CI/CD pipeline:

```yaml
performance_test:
  script:
    - docker-compose up -d
    - sleep 30  # Wait for services to be ready
    - locust -f tests/performance/locustfile.py \
        --host=http://localhost:9002 \
        --users 50 --spawn-rate 5 --run-time 5m \
        --headless \
        --html=performance_report.html
    - python scripts/check_performance_targets.py performance_report.html
  artifacts:
    paths:
      - performance_report.html
    when: always
```

## Troubleshooting

### Services Not Responding

```bash
# Check Docker containers
docker ps

# Check service health
curl http://localhost:9002/health
curl http://localhost:9000/health
curl http://localhost:9003/health
```

### Authentication Failures

- Check Auth service is running on port 9002
- Verify user registration is working
- Check database connection

### High Failure Rates

- Review service logs: `docker logs agentic-agents`
- Check rate limiting configuration
- Verify database connection pool size

## Advanced Usage

### Custom Spawn Patterns

```python
# In your locustfile.py
from locust import LoadTestShape

class StagesShape(LoadTestShape):
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 1},
        {"duration": 120, "users": 50, "spawn_rate": 5},
        {"duration": 180, "users": 100, "spawn_rate": 10},
        {"duration": 240, "users": 100, "spawn_rate": 10},
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None
```

### Distributed Load Testing

```bash
# Start master
locust -f tests/performance/locustfile.py --master

# Start workers (on same or different machines)
locust -f tests/performance/locustfile.py --worker --master-host=localhost
```

## Resources

- [Locust Documentation](https://docs.locust.io/)
- [Performance Testing Best Practices](https://locust.io/best-practices)
- [TempoNest Testing Guide](../../docs/TESTING_GUIDE.md)
