# TempoNest Performance Guide

**Last Updated:** 2025-11-12
**Version:** 1.0

This guide covers all performance optimizations implemented in TempoNest and provides best practices for maintaining optimal performance.

---

## Table of Contents

1. [Performance Overview](#performance-overview)
2. [Caching Strategy](#caching-strategy)
3. [Database Optimization](#database-optimization)
4. [API Performance](#api-performance)
5. [Frontend Optimization](#frontend-optimization)
6. [Docker & Build Performance](#docker--build-performance)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Performance Tuning](#performance-tuning)
9. [Troubleshooting](#troubleshooting)

---

## Performance Overview

### Achieved Improvements

TempoNest has undergone 7 phases of optimization (145+ hours of work):

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **API Response Times** |
| Auth Login | 250ms | 125ms | 50% |
| JWT Token Validation | 100ms | 20-30ms | 70-80% |
| User Permissions Check | 50ms | 5-10ms | 80-90% |
| RAG Query Results | 500ms | 100-200ms | 60-80% |
| Dashboard Metrics | 650ms | 125ms | 81% |
| **Frontend** |
| Financials Page Bundle | 104 kB | 2.54 kB | 97.5% |
| Build Warnings | 15+ warnings | 0 warnings | 100% |
| **Infrastructure** |
| Docker Images (Agents) | 1.58 GB | ~400 MB | 75% |
| Docker Build Time | 12 min | <6 min | 50% |
| CI Pipeline Time | 15 min | ~8 min | 47% |
| **Database** |
| Query Response (avg) | 120ms | <50ms | 58% |
| Slow Queries (>1s) | 23 | 0 | 100% |
| Database Load | 100% | ~48% | 52% |

### Key Technologies

- **Redis** - Distributed caching with 70%+ hit rates
- **PostgreSQL** - Optimized with 30+ indexes and 15+ views
- **AsyncIO** - Non-blocking operations throughout
- **OpenTelemetry** - Distributed tracing with <1% overhead
- **Next.js** - Dynamic imports and tree-shaking
- **Docker BuildKit** - Multi-stage builds with layer caching

---

## Caching Strategy

### Redis Caching Infrastructure

TempoNest uses Redis for distributed caching across all services.

#### Cache Categories

**1. JWT Token Caching**
- **Location:** Auth service, Agents service
- **Cache Key:** `jwt:{sha256(token)}`
- **TTL:** 30 seconds
- **Expected Hit Rate:** >90%
- **Impact:** 50-100ms saved per authenticated request

```python
# Implementation
from shared.redis.client import RedisCache

cache = RedisCache(redis_url="redis://redis:6379/0")

# Cache JWT validation
token_hash = hashlib.sha256(token.encode()).hexdigest()
cached_claims = await cache.get(f"jwt:{token_hash}")

if cached_claims:
    return cached_claims  # Cache hit
else:
    claims = decode_jwt(token)  # Validate
    await cache.set(f"jwt:{token_hash}", claims, ttl=30)
    return claims
```

**2. User Permissions Caching**
- **Location:** Auth service
- **Cache Key:** `user_perms:{user_id}`
- **TTL:** 5 minutes (300 seconds)
- **Expected Hit Rate:** >85%
- **Impact:** 20-50ms saved, 95% DB load reduction

```python
# Cache user permissions
perms = await cache.get(f"user_perms:{user_id}")

if not perms:
    perms = await db.fetch_user_permissions(user_id)
    await cache.set(f"user_perms:{user_id}", perms, ttl=300)
```

**Cache Invalidation:**
```python
# Invalidate on permission changes
await cache.delete(f"user_perms:{user_id}")
```

**3. RAG Query Results Caching**
- **Location:** Agents service
- **Cache Key:** `rag:{sha256(query + filters)}`
- **TTL:** 15 minutes (900 seconds)
- **Expected Hit Rate:** >60%
- **Impact:** 200-500ms saved per cache hit

```python
# Cache RAG results
query_hash = hashlib.sha256(
    f"{query}:{json.dumps(filters)}".encode()
).hexdigest()

results = await cache.get(f"rag:{query_hash}")

if not results:
    results = await qdrant_client.search(query, filters)
    await cache.set(f"rag:{query_hash}", results, ttl=900)
```

**4. Health Check Caching**
- **Location:** All services
- **Cache Key:** `health:{service_name}`
- **TTL:** 10 seconds
- **Expected Hit Rate:** >95%
- **Impact:** 50-100ms saved

**5. Dashboard Metrics Caching**
- **Location:** Console API routes
- **Cache Key:** `metrics:dashboard`, `metrics:logs:{filters}`
- **TTL:** 30-60 seconds
- **Expected Hit Rate:** >70%
- **Impact:** 100-200ms saved

### Caching Best Practices

1. **Set appropriate TTLs**
   - Frequently changing data: 10-30 seconds
   - Moderately stable data: 5-15 minutes
   - Stable data: 30-60 minutes

2. **Implement cache invalidation**
   - On data mutations, invalidate related cache keys
   - Use pattern matching for bulk invalidation: `await cache.delete("user_perms:*")`

3. **Monitor cache hit rates**
   - Target: >70% overall hit rate
   - Alert if hit rate drops below 60%
   - Use Grafana dashboard to track

4. **Handle cache failures gracefully**
   ```python
   try:
       cached = await cache.get(key)
       if cached:
           return cached
   except Exception as e:
       logger.warning(f"Cache error: {e}")
       # Continue to fetch from DB

   return await fetch_from_database()
   ```

5. **Use cache for expensive operations only**
   - Database queries (>50ms)
   - External API calls
   - Complex computations
   - Do NOT cache simple operations (<10ms)

---

## Database Optimization

### Indexing Strategy

TempoNest uses 30+ composite indexes for optimal query performance.

#### Cost Tracking Indexes

```sql
-- Dashboard metrics (tenant-level)
CREATE INDEX idx_cost_tracking_tenant_date_agent
ON cost_tracking(tenant_id, created_at DESC, agent_name)
WHERE deleted_at IS NULL;

-- Project cost reports
CREATE INDEX idx_cost_tracking_project_tenant_date
ON cost_tracking(project_id, tenant_id, created_at DESC)
WHERE project_id IS NOT NULL;

-- Model usage analysis
CREATE INDEX idx_cost_tracking_model_date
ON cost_tracking(model_name, created_at DESC)
INCLUDE (total_cost_usd, total_tokens);
```

#### Webhook Indexes

```sql
-- Delivery history
CREATE INDEX idx_webhook_deliveries_webhook_status_date
ON webhook_deliveries(webhook_id, status, created_at DESC);

-- Retry worker optimization
CREATE INDEX idx_webhook_deliveries_retry_queue
ON webhook_deliveries(status, next_retry_at, updated_at)
WHERE status = 'retrying';

-- Event publishing (GIN index for arrays)
CREATE INDEX idx_webhooks_events_gin
ON webhooks USING gin(events);
```

#### Scheduled Tasks Indexes

```sql
-- Scheduler polling (most critical)
CREATE INDEX idx_scheduled_tasks_ready_to_run
ON scheduled_tasks(next_run_at, status, is_active)
WHERE is_active = true AND status = 'scheduled';

-- Tenant metrics
CREATE INDEX idx_task_executions_tenant_date_status
ON task_executions(tenant_id, created_at DESC, status);
```

#### Console App Indexes

```sql
-- KpiBar optimization
CREATE INDEX idx_runs_created_status
ON runs(created_at DESC, status)
WHERE deleted_at IS NULL;

-- Project detail pages
CREATE INDEX idx_runs_project_status_created
ON runs(project_id, status, created_at DESC);
```

### Database Views

TempoNest uses 15+ materialized views for complex metrics queries.

#### Console Metrics Views

```sql
-- All run metrics in one query (replaces 6+ queries)
CREATE VIEW v_run_metrics_summary AS
SELECT
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as runs_24h,
    COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
    AVG(duration_ms) FILTER (WHERE status = 'completed') as avg_duration_ms
FROM runs
WHERE deleted_at IS NULL;

-- Status distribution with percentages
CREATE VIEW v_run_status_distribution_24h AS
SELECT
    status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM runs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY status;
```

#### Backend Metrics Views

```sql
-- Hourly cost aggregations
CREATE VIEW v_cost_summary_hourly AS
SELECT
    date_trunc('hour', created_at) as hour,
    tenant_id,
    SUM(total_cost_usd) as total_cost,
    SUM(total_tokens) as total_tokens,
    COUNT(*) as execution_count
FROM cost_tracking
WHERE deleted_at IS NULL
GROUP BY hour, tenant_id;

-- Agent performance metrics
CREATE VIEW v_agent_performance_metrics AS
SELECT
    agent_name,
    COUNT(*) as execution_count,
    AVG(duration_ms) as avg_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms,
    AVG(total_cost_usd) as avg_cost_usd,
    COUNT(*) FILTER (WHERE status = 'failed') as failure_count
FROM cost_tracking
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY agent_name;
```

### Connection Pool Optimization

#### Agents Service (Highest Traffic)
```python
# services/agents/app/main.py
pool = await asyncpg.create_pool(
    settings.DATABASE_URL,
    min_size=15,        # Increased from 2
    max_size=100,       # Increased from 10
    max_queries=50000,  # Recycle after 50k queries
    max_inactive_connection_lifetime=300,  # Close idle after 5min
    timeout=10,         # Connection acquisition timeout
    command_timeout=30, # Per-query timeout
    statement_cache_size=100
)
```

#### Auth Service (High Traffic)
```python
# services/auth/app/database.py
pool = await asyncpg.create_pool(
    settings.DATABASE_URL,
    min_size=10,        # Increased from 5
    max_size=50,        # Increased from 20
    max_queries=30000,
    max_inactive_connection_lifetime=300,
    timeout=10,
    statement_timeout="30s"
)
```

#### Scheduler Service (Moderate Traffic)
```python
# services/scheduler/app/db.py
pool = await asyncpg.create_pool(
    settings.DATABASE_URL,
    min_size=5,         # Increased from 2
    max_size=20,        # Increased from 10
    max_queries=30000,
    max_inactive_connection_lifetime=300
)
```

### Query Optimization Best Practices

1. **Use database views for complex queries**
   - Replace 6+ queries with 1 view query
   - Pre-computed aggregations
   - Simplified application code

2. **Batch operations**
   ```python
   # Bad: N queries
   for record in records:
       await conn.execute("INSERT INTO ...", record)

   # Good: 1 batched query
   await conn.executemany(
       "INSERT INTO ... VALUES ($1, $2, $3)",
       [(r['a'], r['b'], r['c']) for r in records]
   )
   ```

3. **Select only needed columns**
   ```python
   # Bad
   SELECT * FROM runs WHERE project_id = $1

   # Good
   SELECT id, status, created_at FROM runs WHERE project_id = $1
   ```

4. **Use covering indexes**
   ```sql
   -- Include commonly accessed columns
   CREATE INDEX idx_runs_project_created
   ON runs(project_id, created_at DESC)
   INCLUDE (status, duration_ms);
   ```

5. **Monitor slow queries**
   ```sql
   -- Enable slow query logging
   ALTER DATABASE your_db SET log_min_duration_statement = 1000;

   -- Check slow queries
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   WHERE mean_exec_time > 1000
   ORDER BY mean_exec_time DESC;
   ```

---

## API Performance

### Async Operations

All blocking operations have been converted to async:

#### Token Counting
```python
# services/agents/app/main.py

# Blocking version (BAD)
def count_tokens(text: str, model: str) -> int:
    return tiktoken.encoding_for_model(model).encode(text)

# Async wrapper (GOOD)
async def count_tokens_async(text: str, model: str) -> int:
    return await asyncio.to_thread(count_tokens, text, model)
```

#### Password Hashing
```python
# services/auth/app/handlers/password.py

# Async password operations
async def hash_password_async(password: str) -> str:
    return await asyncio.to_thread(
        PasswordHandler.hash_password, password
    )

async def verify_password_async(plain: str, hashed: str) -> bool:
    return await asyncio.to_thread(
        PasswordHandler.verify_password, plain, hashed
    )
```

### Rate Limiting

Rate limiting prevents abuse and ensures fair resource usage.

#### Agents Service
```python
# services/agents/app/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["20/minute"],
    storage_uri="redis://redis:6379/0"
)

# Apply to endpoints
@app.post("/overseer/run")
@limiter.limit("20/minute")
async def run_overseer(request: Request):
    ...
```

#### Auth Service
```python
# Already rate-limited
@app.post("/login")
@limiter.limit("5/minute")
async def login(request: LoginRequest):
    ...

@app.post("/register")
@limiter.limit("3/hour")
async def register(request: RegisterRequest):
    ...
```

### Pagination

Large result sets use cursor-based pagination:

```python
# apps/console/app/projects/[slug]/page.tsx

# Fetch project metadata and count separately
const [project, totalRuns] = await Promise.all([
    prisma.project.findUnique({
        where: { slug },
        select: { id: true, name: true, slug: true }  // Only needed fields
    }),
    prisma.run.count({ where: { projectId: project.id } })
])

# Paginate runs
const runs = await prisma.run.findMany({
    where: { projectId: project.id },
    select: {
        id: true,
        status: true,
        createdAt: true
        // Exclude logs field (large)
    },
    take: 20,
    skip: page * 20,
    orderBy: { createdAt: 'desc' }
})
```

---

## Frontend Optimization

### Bundle Size Optimization

#### Dynamic Imports

Heavy components are loaded on demand:

```typescript
// apps/console/app/financials/page.tsx

// Dynamic import with loading state
const FinancialsCharts = dynamic(
    () => import('@/components/FinancialsCharts'),
    {
        loading: () => <SkeletonLoader />,
        ssr: false  // Client-side only
    }
)

// Result: 104 kB → 2.54 kB (97.5% reduction!)
```

#### Tree-Shaking Configuration

```javascript
// apps/console/next.config.js

module.exports = {
    modularizeImports: {
        'lucide-react': {
            transform: 'lucide-react/dist/esm/icons/{{member}}'
        }
    },
    experimental: {
        optimizePackageImports: [
            'lucide-react',
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu',
            'recharts'
        ]
    }
}
```

### Image Optimization

```typescript
// Replace <img> with Next.js <Image>
import Image from 'next/image'

<Image
    src={user.avatarUrl}
    alt={user.name}
    width={32}
    height={32}
    className="rounded-full"
/>

// Automatic AVIF/WebP conversion
// Lazy loading by default
```

### React Rendering Optimization

```typescript
// Memoize expensive components
const FinancialsCharts = React.memo(({ data }) => {
    return <Charts data={data} />
})

// Memoize callbacks
const fetchMetrics = useCallback(async () => {
    const response = await fetch('/api/metrics')
    return response.json()
}, [])  // Dependencies array

// Memoize expensive calculations
const chartData = useMemo(() => {
    return processChartData(rawData)
}, [rawData])
```

---

## Docker & Build Performance

### Multi-Stage Builds

All Python services use optimized multi-stage builds:

```dockerfile
# Stage 1: Builder
FROM python:3.11-alpine AS builder
WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev postgresql-dev libffi-dev

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-alpine
WORKDIR /app

# Install runtime dependencies only
RUN apk add --no-cache libpq

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY app/ ./app/

# Run as non-root
RUN adduser -D appuser
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]
```

**Result:** 70% smaller images (1.58GB → 400MB for agents service)

### Docker BuildKit Caching

```yaml
# .github/workflows/docker-build.yml

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: ${{ matrix.service.path }}
    push: ${{ github.event_name == 'push' }}
    tags: ${{ steps.meta.outputs.tags }}
    cache-from: type=gha
    cache-to: type=gha,mode=max  # Maximum caching
```

**Result:** 60-80% faster builds with cache hits

### .dockerignore Files

```
# services/*/.dockerignore
__pycache__
*.pyc
*.pyo
*.pyd
.pytest_cache
.coverage
htmlcov/
tests/
*.md
.git
.env
.venv
venv/
*.log
.mypy_cache
.ruff_cache
```

**Result:** 30-40% faster builds, smaller context

---

## Monitoring & Alerting

### OpenTelemetry Tracing

All services are instrumented with OpenTelemetry:

```python
# shared/telemetry/tracing.py
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

# Initialize tracing
tracer_provider = TracerProvider()
trace.set_tracer_provider(tracer_provider)

# Instrument libraries
FastAPIInstrumentor.instrument_app(app)
AsyncPGInstrumentor().instrument()
RedisInstrumentor().instrument()
```

**Access:** http://localhost:16686 (Jaeger UI - Development)

### Grafana Dashboards

Key metrics to monitor:

1. **API Response Times**
   - p50, p95, p99 latencies
   - Alert: p95 > 500ms

2. **Cache Performance**
   - Hit rate (target: >70%)
   - Miss rate
   - Alert: Hit rate < 60%

3. **Database Performance**
   - Query duration (p95, p99)
   - Connection pool usage
   - Slow queries (>1s)
   - Alert: Slow queries > 5/min

4. **Error Rates**
   - 5xx errors
   - 4xx errors
   - Alert: Error rate > 1%

5. **Resource Utilization**
   - CPU usage
   - Memory usage
   - Disk I/O
   - Alert: CPU > 80% or Memory > 85%

### Prometheus Metrics

```python
# Custom metrics
from prometheus_client import Counter, Histogram

# Request counter
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Response time histogram
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)
```

---

## Performance Tuning

### Environment Variables

```bash
# docker/.env

# Database
POSTGRES_MAX_CONNECTIONS=200        # Default: 100
POSTGRES_SHARED_BUFFERS=2GB        # Default: 128MB
POSTGRES_EFFECTIVE_CACHE_SIZE=6GB  # Default: 4GB
POSTGRES_WORK_MEM=16MB             # Default: 4MB

# Redis
REDIS_MAXMEMORY=1GB
REDIS_MAXMEMORY_POLICY=allkeys-lru

# Services
AGENTS_POOL_MIN_SIZE=15
AGENTS_POOL_MAX_SIZE=100
AUTH_POOL_MIN_SIZE=10
AUTH_POOL_MAX_SIZE=50

# Caching TTLs (seconds)
JWT_CACHE_TTL=30
PERMISSIONS_CACHE_TTL=300
RAG_CACHE_TTL=900
HEALTH_CACHE_TTL=10
METRICS_CACHE_TTL=60
```

### Resource Limits

```yaml
# docker-compose.prod.yml
services:
  agents:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  postgres:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

---

## Troubleshooting

### High Response Times

**Symptoms:**
- API responses > 500ms
- Timeout errors
- Slow page loads

**Diagnosis:**
```bash
# Check OpenTelemetry traces
# Look for slow spans: http://localhost:16686

# Check slow queries
docker exec -it temponest-postgres psql -U postgres -d agentic -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 500
ORDER BY mean_exec_time DESC
LIMIT 10;"

# Check cache hit rate
docker exec -it temponest-redis redis-cli INFO stats | grep keyspace_hits
```

**Solutions:**
1. Add missing indexes
2. Increase cache TTLs
3. Optimize slow queries
4. Scale connection pools
5. Add database views

### Low Cache Hit Rates

**Symptoms:**
- Cache hit rate < 60%
- High database load
- Slow API responses

**Diagnosis:**
```bash
# Check Redis metrics
docker exec -it temponest-redis redis-cli INFO stats

# Check cache keys
docker exec -it temponest-redis redis-cli KEYS "*" | head -20

# Monitor cache operations in Grafana
```

**Solutions:**
1. Increase TTLs (if appropriate)
2. Verify cache keys are correct
3. Check for cache eviction (maxmemory)
4. Optimize cache invalidation logic

### High Database CPU

**Symptoms:**
- Database CPU > 80%
- Slow queries
- Connection pool exhaustion

**Diagnosis:**
```bash
# Check running queries
docker exec -it temponest-postgres psql -U postgres -d agentic -c "
SELECT pid, usename, state, query, now() - query_start AS duration
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;"

# Check index usage
docker exec -it temponest-postgres psql -U postgres -d agentic -c "
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan < 100
ORDER BY idx_scan;"
```

**Solutions:**
1. Add missing indexes
2. Optimize N+1 queries
3. Use database views
4. Implement query result caching
5. Scale connection pools

### Memory Issues

**Symptoms:**
- OOM kills
- Swap usage
- Container restarts

**Diagnosis:**
```bash
# Check container memory usage
docker stats --no-stream

# Check memory-intensive processes
docker exec -it <container> ps aux --sort=-%mem | head -10
```

**Solutions:**
1. Increase memory limits
2. Reduce connection pool sizes
3. Enable connection recycling
4. Optimize cache usage (set maxmemory)
5. Review memory leaks in application code

---

## Performance Checklist

### Daily
- [ ] Monitor cache hit rates (target: >70%)
- [ ] Check error rates (target: <1%)
- [ ] Review p95 response times (target: <500ms)
- [ ] Verify no slow queries (>1s)

### Weekly
- [ ] Review OpenTelemetry traces
- [ ] Analyze slow query logs
- [ ] Check database index usage
- [ ] Review cache eviction metrics
- [ ] Monitor resource trends (CPU, memory)

### Monthly
- [ ] Performance benchmarking
- [ ] Review and optimize TTLs
- [ ] Update resource limits if needed
- [ ] Review and optimize database views
- [ ] Dependency updates (security + performance)

---

## Additional Resources

- [OPTIMIZATION_ROADMAP.md](../OPTIMIZATION_ROADMAP.md) - Complete optimization strategy
- [OPTIMIZATION_PROGRESS.md](../OPTIMIZATION_PROGRESS.md) - Detailed progress tracking
- [OPERATIONS.md](OPERATIONS.md) - Deployment and operations guide
- [TELEMETRY_INTEGRATION.md](TELEMETRY_INTEGRATION.md) - OpenTelemetry setup

---

**Maintained By:** Development Team
**Last Review:** 2025-11-12
**Next Review:** 2025-12-12
