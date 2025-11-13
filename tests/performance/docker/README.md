# Docker Performance Measurement

Tools for measuring Docker container startup times, resource usage, and optimization effectiveness.

## Overview

This suite provides tools to measure:

1. **Container Startup Times**: Time from `docker-compose up` to healthy status
2. **Health Check Times**: Time for each container to pass health checks
3. **Resource Usage**: CPU, memory, and network usage per container
4. **Image Sizes**: Docker image sizes and optimization impact
5. **Build Times**: Docker build performance

## Running Measurements

### Startup Time Measurement

```bash
# Basic measurement
./tests/performance/docker/measure_startup.sh

# The script will:
# 1. Stop all containers
# 2. Start containers and measure startup time
# 3. Wait for all health checks to pass
# 4. Collect resource usage statistics
# 5. Generate JSON and text reports
```

### Example Output

```
========================================
Docker Startup Performance Report
========================================

Timestamp: 2025-11-12 15:45:30

Summary
-------
Total Startup Time:     45.3s
Docker Compose Time:    8.7s
Total Health Time:      36.6s
Average Health Time:    2.2s
Healthy Containers:     17
Total Containers:       21

Container Details
-----------------

agentic-postgres
  Image: postgres:16-alpine
  Image Size: 238MB
  Health: healthy
  Health Time: 5.2s
  CPU: 2.3%
  Memory: 45.6MB

agentic-redis
  Image: redis:7-alpine
  Image Size: 31MB
  Health: healthy
  Health Time: 1.8s
  CPU: 0.5%
  Memory: 8.2MB

agentic-agents
  Image: temponest-agents:latest
  Image Size: 156MB
  Health: healthy
  Health Time: 12.4s
  CPU: 5.2%
  Memory: 234MB

...
```

## Understanding Results

### Startup Time Metrics

1. **Total Startup Time**: End-to-end time from `docker-compose up` to all containers healthy
   - **Target**: < 60s for all containers
   - **Good**: < 45s, **Acceptable**: 45-60s, **Review**: > 60s

2. **Docker Compose Time**: Time for Docker Compose to start all containers
   - **Target**: < 15s
   - **Good**: < 10s, **Acceptable**: 10-15s, **Review**: > 15s

3. **Health Check Time**: Time for containers to pass health checks
   - **Target**: < 30s total, < 5s per container
   - Varies by service complexity

4. **Average Health Time**: Average time per container to become healthy
   - **Target**: < 3s
   - **Good**: < 2s, **Acceptable**: 2-5s, **Review**: > 5s

### Resource Usage Metrics

1. **CPU Usage**: Percentage of CPU used by each container
   - **Idle**: < 1%, **Normal**: 1-10%, **High**: > 10%

2. **Memory Usage**: RAM consumed by each container
   - Monitor for memory leaks or unexpected growth

3. **Image Size**: Size of Docker images
   - **Small**: < 100MB, **Medium**: 100-500MB, **Large**: > 500MB
   - Smaller images = faster pulls and startup

## Optimization Targets

### Before Optimization (Baseline)

| Metric | Before | Target | Impact |
|--------|--------|--------|--------|
| Total Startup | ~120s | < 60s | 50% faster |
| Image Sizes | ~800MB avg | < 200MB | 75% smaller |
| Health Time | ~60s | < 30s | 50% faster |
| Build Time | ~15min | < 5min | 66% faster |

### After Optimization (Current)

| Container | Image Size | Health Time | Status |
|-----------|------------|-------------|--------|
| postgres | 238MB | ~5s | ✅ Optimized |
| redis | 31MB | ~2s | ✅ Optimized |
| agents | 156MB | ~12s | ✅ Optimized |
| auth | 142MB | ~8s | ✅ Optimized |
| scheduler | 145MB | ~10s | ✅ Optimized |

## Troubleshooting

### Slow Startup Times

#### Issue: Container takes > 30s to become healthy

**Diagnosis:**
```bash
# Check container logs
docker logs <container-name>

# Check health check definition
docker inspect <container-name> | jq '.[0].Config.Healthcheck'

# Monitor startup process
docker logs -f <container-name>
```

**Common causes:**
1. **Database migrations**: Long-running migrations on startup
2. **External dependencies**: Waiting for other services
3. **Resource constraints**: Insufficient CPU/memory
4. **Network issues**: DNS resolution, slow downloads

**Solutions:**
```bash
# Increase resources in docker-compose.yml
services:
  myservice:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

# Optimize health checks
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost/health"]
  interval: 5s          # Check every 5s
  timeout: 3s           # Fail if no response in 3s
  retries: 3            # Retry 3 times
  start_period: 10s     # Grace period before checking
```

### Large Image Sizes

#### Issue: Images > 500MB

**Diagnosis:**
```bash
# Check image layers
docker history <image-name>

# Find large files
docker run --rm <image-name> du -h / | sort -rh | head -20
```

**Solutions:**

1. **Use Alpine base images:**
```dockerfile
# Before
FROM python:3.11
# After
FROM python:3.11-alpine
```

2. **Multi-stage builds:**
```dockerfile
# Build stage
FROM python:3.11 as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-alpine
COPY --from=builder /root/.local /root/.local
COPY . .
```

3. **Remove build dependencies:**
```dockerfile
RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
    && pip install -r requirements.txt \
    && apk del .build-deps
```

4. **Minimize layers:**
```dockerfile
# Before (3 layers)
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get clean

# After (1 layer)
RUN apt-get update && apt-get install -y curl && apt-get clean
```

### High Resource Usage

#### Issue: Container using excessive CPU/memory

**Diagnosis:**
```bash
# Monitor resource usage
docker stats

# Check container processes
docker exec <container-name> ps aux

# Check for memory leaks
docker stats --no-stream | grep <container-name>
```

**Solutions:**
```yaml
# Set resource limits in docker-compose.yml
services:
  myservice:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## Docker Build Performance

### Measuring Build Times

```bash
# Time a build
time docker-compose build <service>

# Build with BuildKit (faster)
DOCKER_BUILDKIT=1 docker-compose build

# Check build cache
docker system df
```

### Build Optimization

1. **Use BuildKit:**
```bash
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
```

2. **Optimize .dockerignore:**
```
# .dockerignore
__pycache__
*.pyc
.git
.pytest_cache
node_modules
*.log
```

3. **Layer caching:**
```dockerfile
# Copy requirements first (changes less often)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy code last (changes more often)
COPY . .
```

4. **Parallel builds:**
```bash
# Build all services in parallel
docker-compose build --parallel
```

## Continuous Monitoring

### CI/CD Integration

```yaml
# .github/workflows/docker-performance.yml
name: Docker Performance

on: [push, pull_request]

jobs:
  measure:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Measure startup times
        run: ./tests/performance/docker/measure_startup.sh

      - name: Check performance thresholds
        run: |
          # Fail if startup time > 90s
          python scripts/check_docker_performance.py

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: docker-performance
          path: tests/performance/reports/docker-*
```

### Alerting

Set up alerts for:
- Startup time > 90s
- Container restart loops
- Health check failures
- Resource usage spikes

## Comparison Reports

### Before/After Optimization

```bash
# Run baseline measurement
./tests/performance/docker/measure_startup.sh
mv tests/performance/reports/docker-startup-*.json baseline.json

# Apply optimizations...

# Run comparison
./tests/performance/docker/measure_startup.sh
./tests/performance/docker/compare.py baseline.json tests/performance/reports/docker-startup-*.json
```

### Example Comparison

```
========================================
Docker Performance Comparison
========================================

Total Startup Time:
  Before: 120.5s
  After:  45.3s
  Improvement: 62.4% faster ✓

Average Health Time:
  Before: 7.2s
  After:  2.2s
  Improvement: 69.4% faster ✓

Total Image Size:
  Before: 3.2GB
  After:  1.1GB
  Improvement: 65.6% smaller ✓
```

## Best Practices

1. **Health Checks**
   - Always define health checks
   - Use lightweight health check commands
   - Set appropriate timeouts and intervals

2. **Image Optimization**
   - Use Alpine base images where possible
   - Multi-stage builds for compiled languages
   - Minimize layers
   - Use .dockerignore

3. **Resource Management**
   - Set memory and CPU limits
   - Monitor resource usage
   - Tune based on workload

4. **Build Optimization**
   - Enable BuildKit
   - Optimize layer caching
   - Use parallel builds
   - Maintain .dockerignore

5. **Monitoring**
   - Regular performance measurements
   - Track trends over time
   - Set up alerts for regressions

## Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Build Cache](https://docs.docker.com/build/cache/)
- [Multi-stage Builds](https://docs.docker.com/build/building/multi-stage/)
- [TempoNest Docker Guide](../../../docker/DOCKER_USAGE.md)
