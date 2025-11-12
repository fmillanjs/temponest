# TempoNest Optimization Roadmap

**Generated**: 2025-11-12
**Status**: Planning Phase
**Total Estimated Effort**: 6-8 weeks
**Priority Focus**: Security → Performance → Maintainability

---

## Overview

This roadmap addresses **67 identified issues** across:
- 🔒 Security (4 Critical SQL Injection vulnerabilities)
- ⚡ Performance (23 API optimization opportunities)
- 🗄️ Database (13 query optimization issues)
- 🐳 Docker/Deployment (10 configuration issues)
- 🧹 Code Quality (38 maintainability issues)

**Expected Outcomes**:
- 50-80% API performance improvement
- 55% Docker image size reduction
- 50% database load reduction
- Elimination of all critical security vulnerabilities
- 40% CI/CD time reduction

---

## Phase 1: Critical Security & Stability (Week 1)

### 🎯 Goals
- Eliminate all critical security vulnerabilities
- Prevent system instability
- Quick wins with minimal risk

### Tasks

#### 1.1 Security Fixes (Priority: CRITICAL - Day 1)
**Estimated Time**: 2 hours

- [ ] **Fix SQL Injection in Auth Service**
  - File: `services/auth/app/database.py:63`
  - Change: Replace `f"SET app.current_tenant = '{tenant_id}'"` with parameterized query
  - Test: Run auth service integration tests
  ```python
  # Before
  await conn.execute(f"SET app.current_tenant = '{tenant_id}'")

  # After
  await conn.execute("SET app.current_tenant = $1", tenant_id)
  ```

- [ ] **Fix SQL Injection in Scheduler**
  - File: `services/scheduler/app/db.py:301-305`
  - Change: Use query builder or validated column whitelist
  - Test: Run scheduler integration tests

- [ ] **Fix SQL Injection in Web UI (2 locations)**
  - Files: `web-ui/app.py:157-165, 442`
  - Change: Use parameterized queries for date ranges
  - Test: Manual testing of cost summary and timeline

- [ ] **Security Audit Commit**
  - Run security scanner (`bandit -r services/`)
  - Document changes in SECURITY.md
  - Create security policy if missing

**Deliverable**: All SQL injection vulnerabilities patched, security tests passing

---

#### 1.2 Production Configuration Fixes (Priority: CRITICAL - Day 1)
**Estimated Time**: 1 hour

- [ ] **Remove Development Flags from Production**
  - `services/agents/Dockerfile` - Remove `--reload`
  - `services/scheduler/Dockerfile` - Remove `--reload`
  - `services/approval_ui/Dockerfile` - Remove `--reload`
  - Test: Verify services restart without code changes

- [ ] **Add Resource Limits to docker-compose.yml**
  - Add CPU/memory limits for all 18 services
  - Configuration:
    ```yaml
    # Lightweight services (auth, scheduler, ingestion)
    deploy:
      resources:
        limits: {cpus: '0.5', memory: 512M}
        reservations: {cpus: '0.25', memory: 256M}

    # Medium services (approval-ui, temporal-workers, web-ui)
    deploy:
      resources:
        limits: {cpus: '1.0', memory: 1G}
        reservations: {cpus: '0.5', memory: 512M}

    # Heavy services (agents, ollama)
    deploy:
      resources:
        limits: {cpus: '2.0', memory: 2G}
        reservations: {cpus: '1.0', memory: 1G}

    # Databases (postgres, qdrant, redis)
    deploy:
      resources:
        limits: {cpus: '1.0', memory: 2G}
        reservations: {cpus: '0.5', memory: 1G}
    ```
  - Test: Run `docker stats` to verify limits applied

**Deliverable**: Production-ready configuration, resource limits enforced

---

#### 1.3 Build Optimization Quick Wins (Priority: HIGH - Day 2)
**Estimated Time**: 2 hours

- [ ] **Create .dockerignore Files**

  **For Python Services** (`services/*/.dockerignore`):
  ```
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

  **For Next.js** (`apps/console/.dockerignore`):
  ```
  .next/
  node_modules/
  .git/
  .gitignore
  *.md
  .env*.local
  coverage/
  .vscode/
  .idea/
  tests/
  playwright-report/
  test-results/
  e2e/
  ```

- [ ] **Test Build Performance**
  - Build all services: `docker-compose build --parallel`
  - Measure time and context size
  - Expected: 30-40% faster builds

**Deliverable**: .dockerignore files for all services, faster builds

---

#### 1.4 Database Pagination Critical Fix (Priority: HIGH - Day 2-3)
**Estimated Time**: 3 hours

- [ ] **Add Pagination to Project Details Page**
  - File: `apps/console/app/projects/[slug]/page.tsx`
  - Changes:
    - Add pagination parameters (page, limit)
    - Separate query for project metadata vs runs
    - Lazy load run logs
    - Add run count endpoint
  ```typescript
  // Paginated approach
  const [project, totalRuns] = await Promise.all([
    prisma.project.findUnique({
      where: { slug },
      select: { /* only essential fields */ }
    }),
    prisma.run.count({ where: { project: { slug } } })
  ])

  const runs = await prisma.run.findMany({
    where: { project: { slug } },
    select: { /* exclude logs field */ },
    take: 20,
    skip: page * 20
  })
  ```
  - Add frontend pagination component
  - Test with large dataset (1000+ runs)

**Deliverable**: Paginated project details page, no memory issues

---

### Phase 1 Checkpoint
**Duration**: 3 days
**Effort**: 8 hours
**Risk**: Low (isolated changes)

**Success Criteria**:
- ✅ Zero critical security vulnerabilities
- ✅ Production flags removed
- ✅ Resource limits enforced
- ✅ Build time reduced by 30-40%
- ✅ Project page handles 1000+ runs without issues

**Commit & Deploy**: Create PR "Phase 1: Critical Security & Stability Fixes"

---

## Phase 2: Performance Infrastructure (Week 1-2)

### 🎯 Goals
- Enable caching infrastructure
- Fix blocking operations
- Optimize API response times

### Tasks

#### 2.1 Redis Caching Implementation (Priority: HIGH - Day 4-5)
**Estimated Time**: 6 hours

- [ ] **Create Shared Redis Client Module**
  - File: `shared/redis_client.py`
  - Features: Connection pooling, serialization helpers, TTL management
  ```python
  from redis.asyncio import Redis
  import json
  from typing import Optional, Any

  class RedisCache:
      def __init__(self, url: str):
          self.redis = Redis.from_url(url, decode_responses=True)

      async def get(self, key: str) -> Optional[Any]:
          value = await self.redis.get(key)
          return json.loads(value) if value else None

      async def set(self, key: str, value: Any, ttl: int):
          await self.redis.setex(key, ttl, json.dumps(value))

      async def delete(self, pattern: str):
          keys = await self.redis.keys(pattern)
          if keys:
              await self.redis.delete(*keys)
  ```

- [ ] **JWT Token Caching**
  - Files:
    - `services/auth/app/middleware/auth.py`
    - `services/agents/app/auth_middleware.py`
  - Cache key: `jwt:{sha256(token)}`
  - TTL: 30 seconds
  - Expected impact: 50-100ms saved per authenticated request

- [ ] **User Permissions Caching**
  - File: `services/auth/app/middleware/auth.py:136-162`
  - Cache key: `user_perms:{user_id}`
  - TTL: 5 minutes
  - Include cache invalidation on permission changes
  - Expected impact: 20-50ms saved, 95% DB load reduction

- [ ] **RAG Query Results Caching**
  - File: `services/agents/app/memory/rag.py`
  - Cache key: `rag:{sha256(query + filters)}`
  - TTL: 15 minutes
  - Expected impact: 200-500ms saved per cache hit

- [ ] **Health Check Caching**
  - All `/health` endpoints
  - Cache key: `health:{service_name}`
  - TTL: 10 seconds
  - Expected impact: 50-100ms saved

- [ ] **Dashboard Metrics Caching**
  - Files:
    - `apps/console/components/KpiBar.tsx`
    - `apps/console/app/api/observability/metrics/route.ts`
  - Cache key: `metrics:dashboard`, `metrics:logs:{filters}`
  - TTL: 30-60 seconds
  - Expected impact: 100-200ms saved

**Deliverable**: Redis caching operational, 50-80% API response time improvement

---

#### 2.2 Fix Blocking Operations (Priority: HIGH - Day 5-6)
**Estimated Time**: 4 hours

- [ ] **Token Counting Async Wrapper**
  - File: `services/agents/app/main.py`
  - Create async wrapper:
  ```python
  async def count_tokens_async(text: str, model: str) -> int:
      return await asyncio.to_thread(count_tokens, text, model)
  ```
  - Replace all calls (10+ locations in main.py)
  - Test: Measure event loop blocking with pytest-asyncio

- [ ] **Password Hashing Async Wrapper**
  - File: `services/auth/app/handlers/password.py`
  - Create async wrappers:
  ```python
  async def hash_password_async(password: str) -> str:
      return await asyncio.to_thread(
          PasswordHandler.hash_password, password
      )

  async def verify_password_async(plain: str, hashed: str) -> bool:
      return await asyncio.to_thread(
          PasswordHandler.verify_password, plain, hashed
      )
  ```
  - Update all auth endpoints
  - Test: Login performance benchmark

- [ ] **Move to Background Tasks**
  - Webhook publishing (services/agents/app/main.py)
  - Cost tracking writes
  - Audit logging
  - Use FastAPI `BackgroundTasks`
  ```python
  from fastapi import BackgroundTasks

  @app.post("/overseer/run")
  async def run_overseer(request: Request, bg: BackgroundTasks):
      result = await agent.execute()
      bg.add_task(publish_webhook, event_type, result)
      bg.add_task(track_cost, usage)
      return result  # Don't wait for background tasks
  ```

**Deliverable**: No blocking operations in request handlers, 30% faster responses

---

#### 2.3 Enable Rate Limiting (Priority: HIGH - Day 6)
**Estimated Time**: 2 hours

- [ ] **Enable Agents Service Rate Limiting**
  - File: `services/agents/app/main.py`
  - Uncomment lines 233-237
  - Add middleware:
  ```python
  from app.rate_limiting import RateLimiter, RateLimitMiddleware

  rate_limiter = RateLimiter(
      redis_url=settings.REDIS_URL or "redis://redis:6379/0"
  )
  app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
  ```
  - Configure per-endpoint limits:
    - `/overseer/run`: 20/minute
    - `/developer/run`: 30/minute
    - `/qa-tester/run`: 15/minute
    - `/health`: 100/minute

- [ ] **Add Rate Limiting to Scheduler**
  - Create rate limiting module (copy from agents)
  - Apply to endpoints:
    - `POST /schedules`: 50/hour
    - `POST /schedules/{id}/trigger`: 100/hour

- [ ] **Add Rate Limiting to Next.js API Routes**
  - Install: `npm install @upstash/ratelimit`
  - Add middleware: `middleware.ts`
  - Apply to expensive routes

**Deliverable**: Rate limiting active on all services, abuse prevention

---

### Phase 2 Checkpoint
**Duration**: 3 days
**Effort**: 12 hours
**Risk**: Medium (requires testing)

**Success Criteria**:
- ✅ Redis caching operational with >70% hit rate
- ✅ No blocking operations in critical paths
- ✅ Rate limiting prevents abuse
- ✅ API response times 50-80% faster
- ✅ Database load reduced 30-50%

**Commit & Deploy**: Create PR "Phase 2: Performance Infrastructure"

---

## Phase 3: Docker Optimization (Week 2-3)

### 🎯 Goals
- Reduce Docker image sizes by 50-70%
- Implement multi-stage builds
- Optimize build caching

### Tasks

#### 3.1 Multi-Stage Docker Builds for Python Services (Priority: HIGH - Day 7-9)
**Estimated Time**: 8 hours

- [ ] **Create Standard Python Dockerfile Template**
  ```dockerfile
  # Build stage
  FROM python:3.11-alpine AS builder
  WORKDIR /app

  # Install build dependencies
  RUN apk add --no-cache gcc musl-dev postgresql-dev

  # Install Python dependencies
  COPY requirements.txt .
  RUN pip install --user --no-cache-dir -r requirements.txt

  # Runtime stage
  FROM python:3.11-alpine
  WORKDIR /app

  # Install runtime dependencies only
  RUN apk add --no-cache postgresql-libs

  # Copy installed packages from builder
  COPY --from=builder /root/.local /root/.local
  ENV PATH=/root/.local/bin:$PATH

  # Copy application code
  COPY app/ ./app/

  # Run as non-root
  RUN adduser -D appuser
  USER appuser

  # Health check
  HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:PORT/health')"

  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "PORT"]
  ```

- [ ] **Refactor Services (Apply Template)**
  - [ ] Auth Service (`services/auth/Dockerfile`)
    - Target: 211MB → 140MB
  - [ ] Agents Service (`services/agents/Dockerfile`)
    - Target: 1.58GB → 400MB (CRITICAL)
    - Consider removing unused dependencies
  - [ ] Scheduler Service (`services/scheduler/Dockerfile`)
    - Target: 216MB → 150MB
  - [ ] Approval UI (`services/approval_ui/Dockerfile`)
    - Target: 318MB → 200MB
  - [ ] Ingestion Service (`services/ingestion/Dockerfile`)
    - Target: 288MB → 180MB
  - [ ] Temporal Workers (`services/temporal_workers/Dockerfile`)
    - Target: 216MB → 150MB

- [ ] **Optimize Web UI Dockerfile**
  - File: `web-ui/Dockerfile`
  - Use Python 3.11 (consistency)
  - Remove SDK copy-delete pattern
  - Target: 178MB → 130MB

- [ ] **Test All Images**
  - Build: `docker-compose build --parallel`
  - Size: `docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"`
  - Function: Full integration test suite
  - Performance: Measure startup times

**Deliverable**: All services using optimized multi-stage builds, 50-70% size reduction

---

#### 3.2 Docker Compose Separation (Priority: MEDIUM - Day 9-10)
**Estimated Time**: 4 hours

- [ ] **Create docker-compose.prod.yml**
  - Remove all volume mounts to source code
  - Keep only data volumes
  - Remove development-specific services
  ```yaml
  # Override for production
  services:
    agents:
      volumes:
        - ./agent-output:/output  # Data only
      environment:
        - LOG_LEVEL=INFO  # Production logging

    # Remove development mounts
    # volumes:
    #   - ../services/agents/app:/app/app  # REMOVED
  ```

- [ ] **Create docker-compose.dev.yml**
  - Extend base with development features
  - Add hot reload
  - Add debug ports
  ```yaml
  services:
    agents:
      command: uvicorn app.main:app --reload --host 0.0.0.0
      volumes:
        - ../services/agents/app:/app/app
      ports:
        - "5678:5678"  # Debug port
  ```

- [ ] **Update Documentation**
  - README.md with usage instructions
  - Development: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up`
  - Production: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up`

**Deliverable**: Separate dev/prod configurations, immutable production deployments

---

#### 3.3 Health Check Optimization (Priority: LOW - Day 10)
**Estimated Time**: 2 hours

- [ ] **Optimize Health Check Intervals**
  - Increase intervals from 10s → 30s for stable services
  - Use Python instead of curl where possible
  - Example:
  ```yaml
  healthcheck:
    test: ["CMD-SHELL", "python -c 'import httpx; httpx.get(\"http://localhost:9000/health\")'"]
    interval: 30s  # Reduced from 10s
    timeout: 5s
    retries: 3
    start_period: 60s
  ```

- [ ] **Batch Health Checks**
  - Create combined health check script
  - Run checks in parallel with asyncio.gather()

**Deliverable**: Reduced health check overhead, lower CPU/network usage

---

### Phase 3 Checkpoint
**Duration**: 4 days
**Effort**: 14 hours
**Risk**: Medium (requires testing)

**Success Criteria**:
- ✅ Docker images 50-70% smaller
- ✅ Clear dev/prod separation
- ✅ Build cache efficiency >80%
- ✅ All services start and pass health checks
- ✅ Integration tests pass

**Commit & Deploy**: Create PR "Phase 3: Docker Optimization"

---

## Phase 4: Database Optimization (Week 3-4)

### 🎯 Goals
- Optimize slow queries
- Add missing indexes
- Reduce N+1 queries

### Tasks

#### 4.1 Query Optimization (Priority: HIGH - Day 11-12)
**Estimated Time**: 6 hours

- [ ] **Optimize KpiBar Component**
  - File: `apps/console/components/KpiBar.tsx`
  - Combine 6 COUNT queries into 1-2 queries
  ```typescript
  // Single aggregated query
  const stats = await prisma.$queryRaw`
    WITH project_stats AS (
      SELECT
        COUNT(DISTINCT CASE WHEN status NOT IN ('idle') THEN id END) as active,
        COUNT(DISTINCT id) as total
      FROM projects
    ),
    run_stats AS (
      SELECT
        COUNT(DISTINCT CASE WHEN created_at >= CURRENT_DATE THEN id END) as today,
        COUNT(DISTINCT CASE WHEN status = 'pending' THEN id END) as queued
      FROM runs
    ),
    agent_stats AS (
      SELECT
        COUNT(DISTINCT CASE WHEN status = 'healthy' THEN id END) as healthy,
        COUNT(DISTINCT id) as total
      FROM agents
    )
    SELECT * FROM project_stats, run_stats, agent_stats
  `
  ```
  - Add Redis cache (60s TTL)

- [ ] **Optimize Metrics Route**
  - File: `apps/console/app/api/observability/metrics/route.ts`
  - Combine 9 queries into 2-3 CTEs
  - Add query result caching (30s TTL)

- [ ] **Replace SELECT * Queries**
  - Files: `services/scheduler/app/db.py`, `services/agents/app/webhooks/webhook_manager.py`
  - List explicit columns needed (10+ locations)
  - Test: Verify no breaking changes

- [ ] **Batch INSERT for Webhooks**
  - File: `services/agents/app/webhooks/event_dispatcher.py:101-116`
  - Use executemany() instead of loop
  ```python
  # Batch insert
  await conn.executemany(
      """INSERT INTO webhook_deliveries (...) VALUES ($1, $2, ...)""",
      [(record['id'], record['webhook_id'], ...) for record in records]
  )
  ```

**Deliverable**: Optimized queries, 30-50% reduction in DB load

---

#### 4.2 Database Indexing (Priority: HIGH - Day 12-13)
**Estimated Time**: 4 hours

- [ ] **Add Composite Indexes to Prisma Schema**
  - File: `apps/console/prisma/schema.prisma`
  ```prisma
  model Run {
    // ... existing fields ...

    @@index([projectId, status])
    @@index([projectId, createdAt])
    @@index([status, createdAt])
    @@map("runs")
  }
  ```

- [ ] **Add Covering Indexes for Cost Tracking**
  - Migration: `docker/migrations/003_cost_tracking.sql`
  ```sql
  -- Optimize date range queries
  CREATE INDEX idx_cost_tenant_date ON cost_tracking(tenant_id, created_at DESC)
    INCLUDE (total_cost_usd, total_tokens);

  CREATE INDEX idx_cost_project_date ON cost_tracking(project_id, created_at DESC)
    WHERE project_id IS NOT NULL
    INCLUDE (total_cost_usd, agent_name);
  ```

- [ ] **Add Full-Text Search Index for Logs**
  - Migration: `docker/migrations/00X_audit_log_fts.sql`
  ```sql
  CREATE INDEX idx_audit_log_fts ON audit_log
    USING gin(to_tsvector('english', action || ' ' || resource));
  ```

- [ ] **Add Index for Webhook Retries**
  ```sql
  CREATE INDEX idx_webhook_deliveries_retry
    ON webhook_deliveries(status, next_retry_at, updated_at)
    WHERE status = 'retrying';
  ```

- [ ] **Generate and Apply Migrations**
  - Prisma: `npm run db:generate`
  - SQL migrations: Run against database
  - Test: Query performance benchmarks
  - Monitor: Index usage with `pg_stat_user_indexes`

**Deliverable**: Optimized indexes, 10-100x query speedup for filtered queries

---

#### 4.3 Connection Pool Optimization (Priority: MEDIUM - Day 13)
**Estimated Time**: 3 hours

- [ ] **Review and Optimize Pool Configurations**
  - Files: `services/*/app/database.py`
  - Recommendations:
  ```python
  # Auth service (high traffic)
  min_size=3, max_size=15

  # Agents service (moderate traffic)
  min_size=2, max_size=10

  # Scheduler service (low traffic)
  min_size=2, max_size=8
  ```

- [ ] **Add Connection Management**
  ```python
  self.pool = await asyncpg.create_pool(
      settings.DATABASE_URL,
      min_size=3,
      max_size=15,
      command_timeout=30,
      max_queries=50000,  # Recycle after 50k queries
      max_inactive_connection_lifetime=300,  # Close idle after 5min
      statement_cache_size=50  # Per connection
  )
  ```

- [ ] **Add Per-Query Timeouts**
  - For expensive queries, add explicit timeout:
  ```python
  await conn.execute("SET statement_timeout = '10s'")
  result = await conn.fetch(query, *params)
  ```

- [ ] **Monitor Connection Usage**
  - Add Prometheus metrics for pool exhaustion
  - Alert on high connection usage

**Deliverable**: Optimized connection pools, no pool exhaustion

---

### Phase 4 Checkpoint
**Duration**: 3 days
**Effort**: 13 hours
**Risk**: Medium (database changes)

**Success Criteria**:
- ✅ Queries 30-50% faster
- ✅ Indexes in place with good selectivity
- ✅ Connection pools optimized
- ✅ No query timeouts under load
- ✅ Database CPU usage reduced 30-50%

**Commit & Deploy**: Create PR "Phase 4: Database Optimization"

---

## Phase 5: Code Quality & Maintainability (Week 4-5)

### 🎯 Goals
- Eliminate code duplication
- Improve error handling
- Refactor complex modules

### Tasks

#### 5.1 Extract Shared Authentication Module (Priority: HIGH - Day 14-16)
**Estimated Time**: 8 hours

- [ ] **Create Shared Package**
  - Directory: `shared/auth/`
  - Structure:
  ```
  shared/auth/
  ├── __init__.py
  ├── client.py        # AuthClient
  ├── context.py       # AuthContext, Permission
  ├── middleware.py    # AuthMiddleware
  └── exceptions.py    # AuthError, UnauthorizedError
  ```

- [ ] **Extract AuthClient (198 lines × 3 = 594 lines duplicated)**
  - Current locations:
    - `services/agents/app/auth_client.py`
    - `services/scheduler/app/auth_client.py`
    - `services/approval_ui/auth_client.py`
  - Consolidate into `shared/auth/client.py`

- [ ] **Extract AuthMiddleware (109 lines × 2 = 218 lines duplicated)**
  - Current locations:
    - `services/agents/app/auth_middleware.py`
    - `services/approval_ui/auth_middleware.py`
  - Consolidate into `shared/auth/middleware.py`

- [ ] **Update All Services to Use Shared Module**
  - Add to requirements.txt: `../shared/auth`
  - Update imports
  - Test each service independently

- [ ] **Create Shared Package Documentation**
  - README.md with usage examples
  - API documentation

**Deliverable**: Shared auth module, 800+ lines of duplication eliminated

---

#### 5.2 Refactor Large Files (Priority: MEDIUM - Day 16-18)
**Estimated Time**: 10 hours

- [ ] **Split Agents Main File (1263 lines)**
  - File: `services/agents/app/main.py`
  - Create router modules:
  ```
  services/agents/app/routers/
  ├── __init__.py
  ├── overseer.py      # POST /overseer/run
  ├── developer.py     # POST /developer/run
  ├── qa_tester.py     # POST /qa-tester/run
  ├── devops.py        # POST /devops/run
  ├── designer.py      # POST /designer/run
  ├── security.py      # POST /security-auditor/run
  ├── ux.py            # POST /ux-researcher/run
  └── health.py        # GET /health, /metrics
  ```
  - Update main.py to include routers:
  ```python
  from app.routers import overseer, developer, qa_tester, ...

  app.include_router(overseer.router, prefix="/overseer", tags=["overseer"])
  app.include_router(developer.router, prefix="/developer", tags=["developer"])
  # ... etc
  ```

- [ ] **Refactor Large Agent Classes**
  - Designer (902 lines) → Extract validators, formatters
  - Security Auditor (864 lines) → Extract checkers, reporters
  - DevOps (633 lines) → Extract provisioners, monitors
  - Pattern: Create subdirectories with specialized modules

- [ ] **Test Refactored Code**
  - Ensure all endpoints still work
  - Run full integration test suite
  - Update documentation

**Deliverable**: Modular code structure, <500 lines per file

---

#### 5.3 Improve Error Handling (Priority: MEDIUM - Day 18-19)
**Estimated Time**: 6 hours

- [ ] **Replace Generic Exception Catching**
  - Find: `except Exception as e:`
  - Replace with specific exceptions
  - Example:
  ```python
  # Before
  except Exception as e:
      print(f"Error: {e}")
      return False

  # After
  except ValidationError as e:
      logger.error(f"Validation failed: {e}", exc_info=True)
      raise
  except DatabaseError as e:
      logger.error(f"Database error: {e}", exc_info=True)
      raise DatabaseUnavailable("Service temporarily unavailable")
  except Exception as e:
      logger.exception(f"Unexpected error: {e}")
      raise InternalServerError("An unexpected error occurred")
  ```

- [ ] **Implement Structured Logging**
  - Install: `pip install structlog`
  - Configure for all services:
  ```python
  import structlog

  structlog.configure(
      processors=[
          structlog.stdlib.add_log_level,
          structlog.stdlib.add_logger_name,
          structlog.processors.TimeStamper(fmt="iso"),
          structlog.processors.StackInfoRenderer(),
          structlog.processors.format_exc_info,
          structlog.processors.JSONRenderer()
      ]
  )
  ```

- [ ] **Add Correlation IDs**
  - Middleware to add X-Request-ID header
  - Include in all log messages
  - Pass through service calls

**Deliverable**: Proper error handling, structured logging, traceable requests

---

#### 5.4 Security Hardening (Priority: HIGH - Day 19-20)
**Estimated Time**: 6 hours

- [ ] **Implement Secrets Management**
  - Option 1: AWS Secrets Manager
  - Option 2: HashiCorp Vault
  - Option 3: Docker Secrets (for now)
  - Migrate from .env to secrets manager

- [ ] **Add CSRF Protection**
  - Install: `pip install fastapi-csrf-protect`
  - Add middleware to all FastAPI apps
  - Update frontend to include CSRF tokens

- [ ] **Input Validation**
  - Add Pydantic validators for all request models
  - Sanitize user inputs
  - Add max length constraints
  - Example:
  ```python
  from pydantic import BaseModel, Field, validator

  class TaskRequest(BaseModel):
      task: str = Field(..., max_length=5000, min_length=1)

      @validator('task')
      def sanitize_task(cls, v):
          # Remove potential XSS
          return v.strip()
  ```

- [ ] **Password Policy**
  - Add complexity requirements
  - Minimum length: 12 characters
  - Require uppercase, lowercase, number
  - Reject common passwords

- [ ] **Security Headers**
  - Add middleware for security headers
  ```python
  @app.middleware("http")
  async def add_security_headers(request, call_next):
      response = await call_next(request)
      response.headers["X-Content-Type-Options"] = "nosniff"
      response.headers["X-Frame-Options"] = "DENY"
      response.headers["X-XSS-Protection"] = "1; mode=block"
      response.headers["Strict-Transport-Security"] = "max-age=31536000"
      return response
  ```

**Deliverable**: Hardened security, OWASP best practices implemented

---

### Phase 5 Checkpoint
**Duration**: 7 days
**Effort**: 30 hours
**Risk**: Medium-High (large refactoring)

**Success Criteria**:
- ✅ Shared auth module in use across services
- ✅ No files >500 lines
- ✅ Structured logging operational
- ✅ All security vulnerabilities addressed
- ✅ CSRF protection enabled
- ✅ Secrets management in place

**Commit & Deploy**: Create PR "Phase 5: Code Quality & Security"

---

## Phase 6: CI/CD & Automation (Week 5-6)

### 🎯 Goals
- Automate Docker builds
- Implement caching strategy
- Add performance monitoring

### Tasks

#### 6.1 Docker Build Pipeline (Priority: HIGH - Day 21-22)
**Estimated Time**: 8 hours

- [ ] **Create Build Workflow**
  - File: `.github/workflows/build.yml`
  ```yaml
  name: Build and Push Images

  on:
    push:
      branches: ['main', 'develop']
    pull_request:
      branches: ['main']

  env:
    REGISTRY: ghcr.io
    IMAGE_NAME: ${{ github.repository }}

  jobs:
    build:
      runs-on: ubuntu-latest
      strategy:
        matrix:
          service:
            - { name: auth, path: services/auth, port: 9002 }
            - { name: agents, path: services/agents, port: 9000 }
            - { name: scheduler, path: services/scheduler, port: 9003 }
            - { name: approval-ui, path: services/approval_ui, port: 9001 }
            - { name: ingestion, path: services/ingestion }
            - { name: temporal-workers, path: services/temporal_workers }
            - { name: web-ui, path: web-ui, port: 8080 }
            - { name: console, path: apps/console, port: 3000 }

      steps:
        - uses: actions/checkout@v4

        - name: Set up Docker Buildx
          uses: docker/setup-buildx-action@v3

        - name: Log in to registry
          if: github.event_name == 'push'
          uses: docker/login-action@v3
          with:
            registry: ${{ env.REGISTRY }}
            username: ${{ github.actor }}
            password: ${{ secrets.GITHUB_TOKEN }}

        - name: Extract metadata
          id: meta
          uses: docker/metadata-action@v5
          with:
            images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/${{ matrix.service.name }}
            tags: |
              type=ref,event=branch
              type=ref,event=pr
              type=semver,pattern={{version}}
              type=sha,prefix={{branch}}-

        - name: Build and push
          uses: docker/build-push-action@v5
          with:
            context: ${{ matrix.service.path }}
            push: ${{ github.event_name == 'push' }}
            tags: ${{ steps.meta.outputs.tags }}
            labels: ${{ steps.meta.outputs.labels }}
            cache-from: type=gha
            cache-to: type=gha,mode=max

        - name: Report image size
          if: github.event_name == 'pull_request'
          run: |
            docker images --format "{{.Repository}}:{{.Tag}} - {{.Size}}" \
              | grep ${{ matrix.service.name }}
  ```

- [ ] **Add Size Tracking**
  - Store image sizes as artifacts
  - Compare with baseline
  - Fail if size increase >10%

- [ ] **Add Health Check Smoke Test**
  - Start container
  - Wait for healthy status
  - Hit health endpoint
  - Clean up

**Deliverable**: Automated Docker builds, layer caching, size tracking

---

#### 6.2 Optimize Test Pipeline (Priority: MEDIUM - Day 22-23)
**Estimated Time**: 4 hours

- [ ] **Add Dependency Caching**
  - File: `.github/workflows/tests.yml`
  ```yaml
  - name: Cache pip dependencies
    uses: actions/cache@v3
    with:
      path: ~/.cache/pip
      key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
      restore-keys: |
        ${{ runner.os }}-pip-

  - name: Cache npm dependencies
    uses: actions/cache@v3
    with:
      path: ~/.npm
      key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
      restore-keys: |
        ${{ runner.os }}-node-

  - name: Cache Playwright browsers
    uses: actions/cache@v3
    with:
      path: ~/.cache/ms-playwright
      key: ${{ runner.os }}-playwright-${{ hashFiles('**/package-lock.json') }}
  ```

- [ ] **Optimize E2E Tests for CI**
  - File: `apps/console/playwright.config.ts`
  ```typescript
  export default defineConfig({
    workers: process.env.CI ? 2 : undefined,  // Increased from 1
    retries: process.env.CI ? 2 : 0,

    projects: process.env.CI
      ? [
          // CI: Only chromium
          { name: 'chromium', use: { ...devices['Desktop Chrome'] } }
        ]
      : [
          // Local: All browsers
          { name: 'chromium', ... },
          { name: 'firefox', ... },
          { name: 'webkit', ... }
        ]
  })
  ```

- [ ] **Add Test Result Caching**
  - Skip unchanged test files
  - Use Vitest coverage cache

**Deliverable**: 30-50% faster CI pipeline

---

#### 6.3 Performance Monitoring (Priority: MEDIUM - Day 23-24)
**Estimated Time**: 6 hours

- [ ] **Add OpenTelemetry Instrumentation**
  - Install: `pip install opentelemetry-api opentelemetry-sdk`
  - Configure for all services
  - Export to existing Prometheus/Grafana

- [ ] **Create Performance Dashboards**
  - API response times (p50, p95, p99)
  - Database query times
  - Cache hit rates
  - Error rates
  - Resource utilization

- [ ] **Add Performance Alerts**
  - API response time >500ms (p95)
  - Database query time >1s
  - Cache hit rate <70%
  - Error rate >1%
  - Memory usage >80%

- [ ] **Add Lighthouse CI**
  - File: `.github/workflows/lighthouse.yml`
  - Run on PR
  - Fail if performance score <80

**Deliverable**: Comprehensive performance monitoring

---

#### 6.4 Deployment Automation (Priority: HIGH - Day 24-25)
**Estimated Time**: 6 hours

- [ ] **Create Deployment Workflow**
  - File: `.github/workflows/deploy.yml`
  - Triggers:
    - Manual (workflow_dispatch)
    - On tag push (v*)
    - Scheduled (nightly to staging)

- [ ] **Add Environment Management**
  - Staging environment
  - Production environment
  - Environment-specific secrets

- [ ] **Add Deployment Verification**
  - Health check all services
  - Run smoke tests
  - Rollback on failure

- [ ] **Add Deployment Notifications**
  - Slack/Discord webhook
  - Include: commit, author, changes, status

**Deliverable**: Automated deployments with rollback

---

### Phase 6 Checkpoint
**Duration**: 5 days
**Effort**: 24 hours
**Risk**: Low-Medium

**Success Criteria**:
- ✅ Automated Docker builds with caching
- ✅ CI pipeline 40-60% faster
- ✅ Performance monitoring operational
- ✅ Automated deployments working
- ✅ All dashboards and alerts configured

**Commit & Deploy**: Create PR "Phase 6: CI/CD & Automation"

---

## Phase 7: Next.js & Frontend Optimization (Week 6)

### 🎯 Goals
- Optimize bundle size
- Improve Core Web Vitals
- Enhance user experience

### Tasks

#### 7.1 Next.js Build Optimization (Priority: MEDIUM - Day 26-27)
**Estimated Time**: 6 hours

- [ ] **Enhanced next.config.js**
  - File: `apps/console/next.config.js`
  ```javascript
  const withBundleAnalyzer = require('@next/bundle-analyzer')({
    enabled: process.env.ANALYZE === 'true',
  })

  const nextConfig = {
    reactStrictMode: true,
    output: 'standalone',
    poweredByHeader: false,
    compress: true,
    productionBrowserSourceMaps: false,

    images: {
      formats: ['image/avif', 'image/webp'],
      minimumCacheTTL: 3600,
      deviceSizes: [640, 750, 828, 1080, 1200],
      imageSizes: [16, 32, 48, 64, 96],
    },

    modularizeImports: {
      'lucide-react': {
        transform: 'lucide-react/dist/esm/icons/{{member}}',
      },
      '@radix-ui/react-': {
        transform: '@radix-ui/{{matches.[1]}}/dist/{{member}}',
      },
    },

    experimental: {
      optimizeCss: true,
      optimizePackageImports: [
        'lucide-react',
        '@radix-ui/react-dialog',
        '@radix-ui/react-dropdown-menu',
        '@radix-ui/react-select',
        'recharts'
      ],
    },

    webpack: (config, { dev, isServer }) => {
      if (!dev && !isServer) {
        config.optimization.splitChunks = {
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            framework: {
              name: 'framework',
              chunks: 'all',
              test: /[\\/]node_modules[\\/](react|react-dom|next)[\\/]/,
              priority: 40,
              enforce: true,
            },
            lib: {
              test: /[\\/]node_modules[\\/]/,
              name(module) {
                const packageName = module.context.match(
                  /[\\/]node_modules[\\/](.*?)([\\/]|$)/
                )[1]
                return `npm.${packageName.replace('@', '')}`
              },
              priority: 30,
              minChunks: 1,
              reuseExistingChunk: true,
            },
            commons: {
              name: 'commons',
              minChunks: 2,
              priority: 20,
            },
          },
        }
      }
      return config
    },
  }

  module.exports = withBundleAnalyzer(nextConfig)
  ```

- [ ] **Analyze Bundle**
  - Run: `ANALYZE=true npm run build`
  - Identify large packages
  - Consider alternatives or lazy loading

- [ ] **Fix Image Optimization**
  - File: `apps/console/components/UserMenu.tsx`
  - Replace `<img>` with `<Image />`
  - Add width/height attributes

- [ ] **Add Dynamic Imports**
  - Lazy load heavy components
  - Example:
  ```typescript
  const FlowChart = dynamic(() => import('@/components/FlowChart'), {
    loading: () => <Skeleton />,
    ssr: false
  })
  ```

**Deliverable**: 20-30% bundle size reduction, improved Core Web Vitals

---

#### 7.2 Dependency Optimization (Priority: MEDIUM - Day 27-28)
**Estimated Time**: 4 hours

- [ ] **Audit Dependencies**
  - Run: `npm ls --all`
  - Check for duplicates
  - Run: `npx depcheck`
  - Remove unused: `npm uninstall <package>`

- [ ] **Optimize Package Imports**
  - Tree-shakeable imports:
  ```typescript
  // Before
  import { Button } from '@/components/ui/button'

  // After (if needed)
  import Button from '@/components/ui/button/Button'
  ```

- [ ] **Consider Lighter Alternatives**
  - Evaluate: date-fns vs day.js
  - Evaluate: recharts vs lightweight charts
  - Document decisions

- [ ] **Pin Dependency Versions**
  - Run: `npm shrinkwrap`
  - Ensure reproducible builds

**Deliverable**: Optimized dependencies, faster installs

---

#### 7.3 Frontend Performance (Priority: MEDIUM - Day 28)
**Estimated Time**: 4 hours

- [ ] **Add Performance Monitoring**
  - Install: `npm install @vercel/analytics`
  - Add to _app.tsx:
  ```typescript
  import { Analytics } from '@vercel/analytics/react'

  export default function App({ Component, pageProps }) {
    return (
      <>
        <Component {...pageProps} />
        <Analytics />
      </>
    )
  }
  ```

- [ ] **Optimize React Rendering**
  - Add React.memo() to expensive components
  - Use useMemo() for expensive calculations
  - Use useCallback() for event handlers

- [ ] **Add Loading States**
  - Skeleton loaders for async data
  - Progressive loading
  - Optimistic updates

- [ ] **Fix Accessibility Issues**
  - Add DialogTitle to CommandPalette
  - Fix act() warnings in tests
  - Run axe accessibility audit

**Deliverable**: Improved user experience, better Core Web Vitals

---

### Phase 7 Checkpoint
**Duration**: 3 days
**Effort**: 14 hours
**Risk**: Low

**Success Criteria**:
- ✅ Bundle size reduced 20-30%
- ✅ Lighthouse performance >90
- ✅ No unused dependencies
- ✅ All accessibility issues fixed
- ✅ Frontend monitoring operational

**Commit & Deploy**: Create PR "Phase 7: Frontend Optimization"

---

## Phase 8: Final Polish & Documentation (Week 7)

### 🎯 Goals
- Complete documentation
- Final testing
- Performance validation

### Tasks

#### 8.1 Documentation (Priority: HIGH - Day 29-30)
**Estimated Time**: 8 hours

- [ ] **Update README.md**
  - Architecture overview
  - Setup instructions
  - Development workflow
  - Deployment process

- [ ] **Create Performance Guide**
  - File: `docs/PERFORMANCE.md`
  - Optimization strategies
  - Caching guidelines
  - Monitoring setup

- [ ] **Create Operations Guide**
  - File: `docs/OPERATIONS.md`
  - Deployment procedures
  - Troubleshooting
  - Rollback procedures

- [ ] **API Documentation**
  - OpenAPI/Swagger specs
  - Example requests/responses
  - Authentication guide

- [ ] **Update CHANGELOG.md**
  - Document all optimizations
  - Breaking changes
  - Migration guides

**Deliverable**: Comprehensive documentation

---

#### 8.2 Performance Validation (Priority: HIGH - Day 30-31)
**Estimated Time**: 6 hours

- [ ] **Load Testing**
  - Tool: k6 or Locust
  - Test scenarios:
    - 100 concurrent users on dashboard
    - 50 concurrent agent executions
    - 200 req/s on API endpoints
  - Measure: Response times, error rates, resource usage

- [ ] **Database Performance Testing**
  - Simulate 10,000+ projects with 100+ runs each
  - Measure query times
  - Verify indexes being used

- [ ] **Docker Performance Testing**
  - Measure startup times
  - Verify resource limits working
  - Test under constrained resources

- [ ] **Compare Before/After Metrics**
  | Metric | Before | After | Improvement |
  |--------|--------|-------|-------------|
  | Auth Login | 250ms | 125ms | 50% |
  | Agent Execution | 3000ms | 2000ms | 33% |
  | Project Details | 3000ms | 750ms | 75% |
  | Metrics API | 650ms | 125ms | 81% |
  | Docker Image (agents) | 1.58GB | 420MB | 73% |
  | CI Pipeline | 15min | 8min | 47% |
  | Database Load | 100% | 48% | 52% |

**Deliverable**: Performance validation report

---

#### 8.3 Security Audit (Priority: HIGH - Day 31-32)
**Estimated Time**: 4 hours

- [ ] **Run Security Scanners**
  - Python: `bandit -r services/`
  - Python: `safety check`
  - Node.js: `npm audit`
  - Docker: `docker scan <image>`

- [ ] **Penetration Testing Checklist**
  - [ ] SQL injection attempts (all endpoints)
  - [ ] XSS attempts
  - [ ] CSRF attacks
  - [ ] Authentication bypass attempts
  - [ ] Rate limiting tests
  - [ ] Resource exhaustion tests

- [ ] **Address Findings**
  - Fix any critical/high issues
  - Document medium/low for future work

- [ ] **Security Sign-off**
  - Create SECURITY.md with findings
  - Document security practices
  - Create vulnerability disclosure policy

**Deliverable**: Security audit report, all critical issues resolved

---

#### 8.4 Final Testing & Rollout (Priority: CRITICAL - Day 32-35)
**Estimated Time**: 12 hours

- [ ] **Integration Testing**
  - Run full test suite
  - Manual testing of critical flows
  - Cross-browser testing

- [ ] **Staging Deployment**
  - Deploy to staging environment
  - Run smoke tests
  - Monitor for 24 hours

- [ ] **Production Rollout Plan**
  - Blue-green deployment strategy
  - Rollback procedures
  - Monitoring checklist

- [ ] **Production Deployment**
  - Deploy during low-traffic window
  - Monitor all metrics
  - Verify performance improvements
  - Keep previous version ready for rollback

- [ ] **Post-Deployment**
  - Monitor for 48 hours
  - Address any issues
  - Document lessons learned

**Deliverable**: Successful production deployment

---

### Phase 8 Checkpoint
**Duration**: 7 days
**Effort**: 30 hours
**Risk**: Low

**Success Criteria**:
- ✅ Complete documentation
- ✅ Performance targets met
- ✅ Security audit passed
- ✅ Successful production deployment
- ✅ No critical issues

**Final Deliverable**: Fully optimized, production-ready system

---

## Success Metrics & KPIs

### Performance KPIs
| Metric | Baseline | Target | Achieved |
|--------|----------|--------|----------|
| **API Response Times** |
| Auth Login | 250ms | <150ms | |
| Agent Execution | 3000ms | <2000ms | |
| Dashboard Load | 1500ms | <500ms | |
| Project Details | 3000ms | <1000ms | |
| **Resource Utilization** |
| Docker Images (total) | 3.3GB | <1.5GB | |
| Agents Service | 1.58GB | <500MB | |
| Build Time | 12min | <6min | |
| CI Pipeline Time | 15min | <8min | |
| **Database** |
| Query Response (avg) | 120ms | <50ms | |
| Connection Pool Usage | 75% | <50% | |
| Slow Queries (>1s) | 23 | 0 | |
| **Reliability** |
| Cache Hit Rate | 0% | >70% | |
| Error Rate | 2.3% | <0.5% | |
| Uptime | 98% | >99.5% | |

### Business Impact
- **Developer Productivity**: +20-30% (faster builds, tests)
- **Infrastructure Costs**: -30-40% (smaller images, optimized resources)
- **User Experience**: Lighthouse score >90, LCP <2.5s
- **Security Posture**: Zero critical vulnerabilities

---

## Risk Management

### High Risk Items
| Risk | Impact | Mitigation |
|------|--------|------------|
| Database migration failure | HIGH | Test on staging, backup before migration, rollback scripts ready |
| Cache invalidation issues | MEDIUM | Conservative TTLs, manual cache clear endpoint |
| Breaking changes in refactor | HIGH | Comprehensive test coverage, incremental rollout |
| Performance regression | MEDIUM | Load testing before/after, monitoring, rollback plan |
| Docker build failures | LOW | Multi-stage rollout, keep old Dockerfiles |

### Rollback Procedures
1. **Code Changes**: Git revert, redeploy previous version
2. **Database Changes**: Restore from backup, run rollback migrations
3. **Docker Changes**: Use previous image tags
4. **Configuration Changes**: Restore previous config files

---

## Resource Requirements

### Team
- **Backend Developer**: 30 hours (Phases 1-4)
- **DevOps Engineer**: 24 hours (Phases 3, 6)
- **Frontend Developer**: 14 hours (Phase 7)
- **QA Engineer**: 12 hours (Phases 8)
- **Security Specialist**: 4 hours (Phase 5, 8)

**Total**: ~84 hours (10-11 days of focused work)

### Infrastructure
- **Staging Environment**: Required for testing
- **Redis**: Already available ✅
- **Monitoring**: Prometheus/Grafana already configured ✅
- **CI/CD**: GitHub Actions already in use ✅

### Budget
- **No additional infrastructure costs** (using existing services)
- **Potential savings**: 30-40% on infrastructure costs post-optimization

---

## Communication Plan

### Weekly Updates
- **Mondays**: Phase kickoff, goals review
- **Fridays**: Phase checkpoint, demos, retrospective

### Stakeholder Updates
- **After Phase 1**: Security fixes completed
- **After Phase 2**: Performance improvements visible
- **After Phase 4**: Database optimization results
- **After Phase 6**: CI/CD automation operational
- **After Phase 8**: Final results and ROI analysis

### Documentation
- Track progress in this roadmap (update "Achieved" column)
- Create detailed commit messages
- Update CHANGELOG.md after each phase
- Maintain runbook for operations team

---

## Maintenance Plan (Post-Optimization)

### Daily
- Monitor performance dashboards
- Check error rates and logs
- Verify cache hit rates

### Weekly
- Review slow query logs
- Analyze cache performance
- Check for security updates

### Monthly
- Dependency updates
- Security scans
- Performance benchmarking
- Review and adjust resource limits

### Quarterly
- Full security audit
- Performance optimization review
- Architecture review
- Capacity planning

---

## Conclusion

This roadmap provides a systematic approach to optimizing the TempoNest platform across all dimensions: security, performance, maintainability, and operations.

**Key Deliverables**:
- ✅ Zero critical security vulnerabilities
- ✅ 50-80% API performance improvement
- ✅ 50-70% Docker image size reduction
- ✅ 30-50% database load reduction
- ✅ 40-60% CI/CD time reduction
- ✅ Production-ready, scalable architecture

**Timeline**: 6-8 weeks
**Effort**: 84 hours
**ROI**: High (30-40% cost savings, 20-30% productivity gain)

**Next Steps**:
1. Review and approve roadmap
2. Allocate resources
3. Set up staging environment
4. Begin Phase 1 (Critical Security Fixes)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-12
**Status**: Ready for Implementation
