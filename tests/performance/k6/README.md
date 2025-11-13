# K6 Load Testing for TempoNest

K6 is a modern load testing tool that complements our Locust-based tests with different capabilities and perspectives.

## Installation

### Option 1: Package Manager (Recommended)

```bash
# macOS
brew install k6

# Ubuntu/Debian
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Windows (with Chocolatey)
choco install k6
```

### Option 2: Docker

```bash
docker pull grafana/k6:latest

# Run tests with Docker
docker run --rm -i --network=host grafana/k6:latest run - <tests/performance/k6/auth-api.js
```

### Verify Installation

```bash
k6 version
```

## Running Tests

### Prerequisites

Ensure Docker containers are running:

```bash
cd /home/doctor/temponest
docker-compose up -d
docker ps  # Verify services are healthy
```

### Auth API Tests

```bash
# Quick test (default configuration)
k6 run tests/performance/k6/auth-api.js

# Custom load profile
k6 run --vus 50 --duration 5m tests/performance/k6/auth-api.js

# Generate JSON report
k6 run tests/performance/k6/auth-api.js \
  --out json=tests/performance/reports/k6-auth-results.json

# Custom base URL
k6 run -e BASE_URL=http://localhost:9002 tests/performance/k6/auth-api.js
```

### Agents API Tests

```bash
# Standard test
k6 run tests/performance/k6/agents-api.js

# High load test
k6 run --vus 50 --duration 5m tests/performance/k6/agents-api.js

# With custom URLs
k6 run \
  -e AUTH_URL=http://localhost:9002 \
  -e AGENTS_URL=http://localhost:9000 \
  tests/performance/k6/agents-api.js

# Generate HTML report (requires k6-reporter)
k6 run tests/performance/k6/agents-api.js \
  --out json=tests/performance/reports/k6-agents-results.json
```

### All Tests in Sequence

```bash
# Run all k6 tests
./tests/performance/k6/run-all.sh
```

## Test Scenarios

### auth-api.js

**What it tests:**
- User registration
- User login
- Token verification
- Health checks

**Load profile:**
- Ramp up: 0 → 10 users (30s)
- Scale: 10 → 50 users (1m)
- Steady: 50 users (2m)
- Spike: 50 → 100 users (30s)
- Peak: 100 users (1m)
- Ramp down: 100 → 0 users (30s)

**Performance targets:**
- 95th percentile < 200ms
- Error rate < 1%
- Auth operations < 300ms (95th percentile)

### agents-api.js

**What it tests:**
- List agents
- Create agents
- Get agent details
- Update agents
- Delete agents
- (Optional) Agent execution

**Load profile:**
- Ramp up: 0 → 5 users (30s)
- Scale: 5 → 20 users (1m)
- Steady: 20 users (2m)
- Spike: 20 → 50 users (1m)
- Ramp down: 50 → 0 users (30s)

**Performance targets:**
- List operations: < 200ms (95th percentile)
- Agent execution: < 2s (95th percentile)
- Error rate < 5%

## Understanding Results

### K6 Output

K6 provides detailed metrics:

```
scenarios: (100.00%) 1 scenario, 100 max VUs, 5m30s max duration
default: 100 looping VUs for 5m0s (gracefulStop: 30s)

     ✓ register status is 200 or 201
     ✓ login status is 200
     ✓ login returns access_token

     checks.........................: 100.00% ✓ 15000      ✗ 0
     data_received..................: 7.5 MB  25 kB/s
     data_sent......................: 3.8 MB  13 kB/s
     http_req_blocked...............: avg=1.2ms    min=2µs      med=8µs      max=125ms    p(95)=4ms
     http_req_connecting............: avg=582µs    min=0s       med=0s       max=89ms     p(95)=1.8ms
     http_req_duration..............: avg=89ms     min=12ms     med=78ms     max=456ms    p(95)=167ms
     http_req_failed................: 0.00%   ✓ 0          ✗ 5000
     http_req_receiving.............: avg=124µs    min=18µs     med=98µs     max=12ms     p(95)=234µs
     http_req_sending...............: avg=45µs     min=9µs      med=38µs     max=2.1ms    p(95)=89µs
     http_req_tls_handshaking.......: avg=0s       min=0s       med=0s       max=0s       p(95)=0s
     http_req_waiting...............: avg=88.8ms   min=11.9ms   med=77.8ms   max=455ms    p(95)=166ms
     http_reqs......................: 5000    16.666667/s
     iteration_duration.............: avg=5.9s     min=5.1s     med=5.8s     max=7.2s     p(95)=6.5s
     iterations.....................: 1000    3.333333/s
     vus............................: 100     min=0        max=100
     vus_max........................: 100     min=100      max=100

     auth_duration..................: avg=91ms     min=13ms     med=80ms     max=458ms    p(95)=170ms
     auth_failures..................: 0.00%   ✓ 0          ✗ 1000
     logins.........................: 1000    3.333333/s
     registrations..................: 1000    3.333333/s
```

### Key Metrics

1. **http_req_duration**: Total time for requests
   - **p(95)**: 95th percentile - 95% of requests faster than this
   - **p(99)**: 99th percentile - 99% of requests faster than this
   - **avg**: Average response time
   - **med**: Median response time

2. **http_req_failed**: Percentage of failed requests
   - Target: < 1% for critical endpoints

3. **checks**: Pass/fail rate for assertions
   - Should be 100% for stable systems

4. **http_reqs**: Total requests and requests per second

5. **Custom metrics**: Domain-specific metrics (e.g., auth_duration, agent_creation_success)

### Success Criteria

| Metric | Target | Evaluation |
|--------|--------|------------|
| http_req_duration p(95) | < 200ms (API) | ✅ Good / ⚠️ Review / ❌ Issue |
| http_req_duration p(95) | < 2s (Agents) | ✅ Good / ⚠️ Review / ❌ Issue |
| http_req_failed | < 1% | ✅ Good / ⚠️ Review / ❌ Issue |
| checks | 100% | ✅ Good / ⚠️ Review / ❌ Issue |

## Comparing K6 vs Locust

| Aspect | K6 | Locust |
|--------|----|----|
| Language | JavaScript | Python |
| Protocol Support | HTTP/1.1, HTTP/2, WebSocket | HTTP/1.1, WebSocket |
| Distributed Testing | Master-Worker | Master-Worker |
| Scripting | JavaScript/ES6 | Python |
| Metrics | Built-in detailed metrics | Custom + events |
| Resource Usage | Low (Go-based) | Medium (Python) |
| Real-time UI | CLI + Grafana | Web UI |
| Best For | Quick tests, CI/CD | Complex scenarios |

## Advanced Usage

### Custom Thresholds

```javascript
export const options = {
  thresholds: {
    'http_req_duration': ['p(95)<200', 'p(99)<500'],
    'http_req_duration{endpoint:auth}': ['p(95)<100'],
    'http_req_failed': ['rate<0.01'],
    'checks': ['rate>0.99'],
  },
};
```

### Environment Variables

```bash
k6 run \
  -e BASE_URL=http://production.example.com \
  -e VUS=100 \
  -e DURATION=10m \
  tests/performance/k6/auth-api.js
```

### Integration with Grafana

K6 can export metrics to InfluxDB/Prometheus for visualization in Grafana:

```bash
# Export to InfluxDB
k6 run --out influxdb=http://localhost:8086/k6 tests/performance/k6/auth-api.js

# Export to Prometheus
k6 run --out prometheus tests/performance/k6/auth-api.js
```

### CI/CD Integration

```yaml
# GitHub Actions example
performance_test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Install k6
      run: |
        sudo gpg -k
        sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
        echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
        sudo apt-get update
        sudo apt-get install k6
    - name: Start services
      run: docker-compose up -d
    - name: Run k6 tests
      run: |
        sleep 30
        k6 run tests/performance/k6/auth-api.js
        k6 run tests/performance/k6/agents-api.js
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: k6-results
        path: tests/performance/reports/
```

## Troubleshooting

### Services Not Ready

```bash
# Wait for services to be healthy
docker-compose up -d
sleep 30
docker ps  # Check health status
```

### High Error Rates

1. Check service logs:
   ```bash
   docker logs agentic-auth
   docker logs agentic-agents
   ```

2. Reduce load:
   ```bash
   k6 run --vus 10 --duration 1m tests/performance/k6/auth-api.js
   ```

3. Increase timeouts in test scripts

### Connection Refused

Ensure services are accessible:

```bash
curl http://localhost:9002/health  # Auth
curl http://localhost:9000/health  # Agents
```

## Resources

- [K6 Documentation](https://k6.io/docs/)
- [K6 Best Practices](https://k6.io/docs/misc/fine-tuning-os/)
- [K6 Examples](https://github.com/grafana/k6-learn)
- [TempoNest Performance Guide](../../PERFORMANCE.md)
