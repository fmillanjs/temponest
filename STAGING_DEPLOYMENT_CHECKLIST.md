# Staging Deployment Checklist

**Purpose**: Validate v1.8.0 in staging environment before production rollout
**Timeline**: 48 hours before production deployment
**Environment**: staging.temponest.io
**Target**: Zero defects before production

---

## Pre-Deployment Setup

### 1. Environment Preparation

- [ ] **Staging environment provisioned**
  ```bash
  # Verify infrastructure
  ssh staging-server
  df -h  # Check disk space (need 20GB+ free)
  free -h  # Check memory (need 8GB+ available)
  docker ps  # Check existing containers
  ```

- [ ] **Backup current staging database**
  ```bash
  docker exec staging-postgres pg_dump -U postgres agentic_staging > \
    backups/staging_$(date +%Y%m%d_%H%M%S).sql
  ```

- [ ] **Clean up old containers/images**
  ```bash
  docker system prune -af --volumes
  # Free up space for new builds
  ```

- [ ] **Pull latest code**
  ```bash
  cd /opt/temponest-staging
  git fetch origin
  git checkout v1.8.0
  git pull origin v1.8.0
  ```

### 2. Configuration Validation

- [ ] **Environment variables set correctly**
  ```bash
  # Verify .env file exists and contains:
  cat .env | grep -E "(DATABASE_URL|REDIS_URL|OLLAMA_URL|AUTH_SERVICE_URL)"

  # Required variables:
  # - DATABASE_URL=postgresql://...
  # - REDIS_URL=redis://...
  # - OLLAMA_URL=http://...
  # - AUTH_SERVICE_URL=http://...
  ```

- [ ] **Secrets loaded from vault/secrets manager**
  ```bash
  # Verify JWT_SECRET, DB_PASSWORD, API_KEYS are set
  # DO NOT print these values to stdout!
  ```

- [ ] **Docker Compose configuration**
  ```bash
  # Validate compose file
  docker compose -f docker-compose.prod.yml config
  # Should show no errors
  ```

### 3. Database Preparation

- [ ] **Database migrations ready**
  ```bash
  # Check migration files exist
  ls -lh docker/migrations/00*.sql

  # Expected files:
  # - 006_composite_indexes.sql
  # - 007_metrics_views.sql
  # - 008_* (any new Phase 8 migrations)
  ```

- [ ] **Test migrations on copy of staging DB**
  ```bash
  # Create test database
  docker exec staging-postgres psql -U postgres -c \
    "CREATE DATABASE agentic_staging_test TEMPLATE agentic_staging;"

  # Apply migrations to test DB
  docker exec staging-postgres psql -U postgres -d agentic_staging_test \
    -f /migrations/006_composite_indexes.sql
  docker exec staging-postgres psql -U postgres -d agentic_staging_test \
    -f /migrations/007_metrics_views.sql

  # Verify no errors
  # Drop test DB
  docker exec staging-postgres psql -U postgres -c \
    "DROP DATABASE agentic_staging_test;"
  ```

---

## Deployment Execution

### 4. Build Docker Images

- [ ] **Build all service images**
  ```bash
  cd /opt/temponest-staging

  # Build with no cache to ensure clean build
  docker compose -f docker-compose.prod.yml build --no-cache agents
  docker compose -f docker-compose.prod.yml build --no-cache scheduler
  docker compose -f docker-compose.prod.yml build --no-cache auth
  docker compose -f docker-compose.prod.yml build --no-cache web-ui
  docker compose -f docker-compose.prod.yml build --no-cache approval-ui
  docker compose -f docker-compose.prod.yml build --no-cache ingestion
  docker compose -f docker-compose.prod.yml build --no-cache temporal-workers

  # Verify builds succeeded
  docker images | grep temponest-staging
  ```

- [ ] **Tag images with v1.8.0**
  ```bash
  docker tag temponest-staging-agents:latest temponest-staging-agents:v1.8.0
  docker tag temponest-staging-scheduler:latest temponest-staging-scheduler:v1.8.0
  # ... (all services)
  ```

- [ ] **Check image sizes**
  ```bash
  docker images --format "table {{.Repository}}\t{{.Size}}" | grep staging

  # Expected sizes (after Phase 3 optimizations):
  # agents: ~400-500MB (down from 1.58GB)
  # scheduler: ~200-300MB
  # auth: ~200-300MB
  # web-ui: ~300-400MB
  ```

### 5. Apply Database Migrations

- [ ] **Stop application services (keep DB running)**
  ```bash
  docker compose -f docker-compose.prod.yml stop agents scheduler auth web-ui
  ```

- [ ] **Apply migrations sequentially**
  ```bash
  # Migration 006: Composite Indexes
  docker exec staging-postgres psql -U postgres -d agentic_staging \
    -f /migrations/006_composite_indexes.sql

  # Verify: Check indexes created
  docker exec staging-postgres psql -U postgres -d agentic_staging -c \
    "SELECT indexname FROM pg_indexes WHERE schemaname = 'public'
     AND indexname LIKE 'idx_%';"

  # Migration 007: Metrics Views
  docker exec staging-postgres psql -U postgres -d agentic_staging \
    -f /migrations/007_metrics_views.sql

  # Verify: Check views created
  docker exec staging-postgres psql -U postgres -d agentic_staging -c \
    "SELECT viewname FROM pg_views WHERE schemaname = 'public'
     AND viewname LIKE 'v_%';"
  ```

- [ ] **Verify migration success**
  ```bash
  # Check for errors in postgres logs
  docker logs staging-postgres --tail=100 | grep -i error

  # Run test query against new views
  docker exec staging-postgres psql -U postgres -d agentic_staging -c \
    "SELECT * FROM v_run_metrics_summary LIMIT 5;"
  ```

### 6. Deploy Services

- [ ] **Start infrastructure services**
  ```bash
  docker compose -f docker-compose.prod.yml up -d postgres redis qdrant ollama

  # Wait for services to be healthy
  sleep 30
  docker compose -f docker-compose.prod.yml ps
  ```

- [ ] **Start application services**
  ```bash
  docker compose -f docker-compose.prod.yml up -d \
    auth agents scheduler web-ui approval-ui ingestion temporal-workers
  ```

- [ ] **Monitor startup logs**
  ```bash
  # Watch logs for errors
  docker compose -f docker-compose.prod.yml logs -f --tail=50

  # Look for:
  # ✅ "Application startup complete"
  # ✅ "Database connection successful"
  # ✅ "Redis connected"
  # ❌ Any ERROR or CRITICAL messages
  ```

- [ ] **Wait for health checks to pass**
  ```bash
  # Run health check script
  ./scripts/deploy/health-check.sh --environment staging --timeout 300

  # Expected: All services report healthy within 5 minutes
  ```

---

## Post-Deployment Validation

### 7. Automated Testing

- [ ] **Run smoke tests**
  ```bash
  export WEB_UI_URL=https://staging.temponest.io
  export AGENTS_URL=https://staging-agents.temponest.io

  ./scripts/deploy/smoke-tests.sh

  # Expected: All tests pass ✅
  ```

- [ ] **Run integration test suite**
  ```bash
  # Database integration tests
  pytest web-ui/tests/integration/ -v --tb=short

  # Agents integration tests
  pytest services/agents/tests/integration/ -v

  # Auth integration tests
  pytest services/auth/tests/integration/ -v

  # Expected: 100% pass rate ✅
  ```

- [ ] **Run E2E test suite**
  ```bash
  # Full end-to-end tests
  pytest web-ui/tests/e2e/ -v --tb=short

  # Expected: All E2E tests pass ✅
  ```

- [ ] **Run performance tests**
  ```bash
  cd scripts/performance

  # Auth API load test
  k6 run --vus 50 --duration 5m load-tests/auth-api.js

  # Agents API load test
  k6 run --vus 50 --duration 5m load-tests/agents-api.js

  # Expected:
  # - p95 latency < 500ms ✅
  # - Error rate < 1% ✅
  # - Throughput > baseline ✅
  ```

### 8. Manual Testing - Critical Flows

#### Flow 1: User Authentication
- [ ] **Register new user**
  - Navigate to https://staging.temponest.io/register
  - Fill form: email, password, confirm password
  - Click "Register"
  - **Expected**: Account created, redirected to dashboard

- [ ] **Login with new user**
  - Navigate to https://staging.temponest.io/login
  - Enter credentials
  - Click "Login"
  - **Expected**: JWT token received, redirected to dashboard

- [ ] **Logout**
  - Click profile menu → Logout
  - **Expected**: Logged out, redirected to login page

#### Flow 2: Agent Execution
- [ ] **Create agent execution**
  - Navigate to Agents page
  - Select agent type: "Developer"
  - Enter task description: "Create a simple Python function"
  - Click "Execute"
  - **Expected**: Task created, execution started

- [ ] **Monitor execution**
  - Wait for execution to complete (30-60 seconds)
  - Check status updates
  - **Expected**: Status progresses through: queued → running → completed

- [ ] **View execution results**
  - Click on completed execution
  - View output, logs, cost metrics
  - **Expected**: Results displayed correctly, no errors

#### Flow 3: Dashboard & Metrics
- [ ] **View dashboard**
  - Navigate to Dashboard
  - **Expected**: Metrics load within 2 seconds
  - Verify: Total cost, token usage, execution count displayed

- [ ] **Filter by date range**
  - Select date range: Last 7 days
  - Click "Apply"
  - **Expected**: Metrics update, no 500 errors

- [ ] **View cost breakdown**
  - Navigate to Costs page
  - **Expected**: Cost by agent, model, time period displayed

#### Flow 4: Scheduled Tasks
- [ ] **Create scheduled task**
  - Navigate to Scheduler
  - Click "New Schedule"
  - Fill form:
    - Name: "Test Hourly Task"
    - Cron: `0 * * * *` (every hour)
    - Agent: Developer
    - Task: "Check system health"
  - Click "Save"
  - **Expected**: Schedule created

- [ ] **Verify schedule appears in list**
  - Check scheduler page
  - **Expected**: New schedule listed with status "Active"

- [ ] **Trigger manual run**
  - Click "Run Now" on schedule
  - **Expected**: Execution starts immediately

#### Flow 5: Webhooks
- [ ] **Create webhook**
  - Navigate to Webhooks
  - Click "New Webhook"
  - URL: https://webhook.site/[unique-id]
  - Events: agent.execution.completed
  - Click "Save"
  - **Expected**: Webhook created

- [ ] **Trigger webhook**
  - Create and complete an agent execution
  - Check webhook.site for delivery
  - **Expected**: Webhook delivered, payload correct

### 9. Performance Validation

- [ ] **API response times**
  ```bash
  # Test multiple endpoints
  curl -w "@curl-format.txt" -o /dev/null -s https://staging.temponest.io/api/status
  curl -w "@curl-format.txt" -o /dev/null -s https://staging.temponest.io/health
  curl -w "@curl-format.txt" -o /dev/null -s https://staging.temponest.io/api/costs/summary

  # Expected: All responses < 500ms
  ```

- [ ] **Database query performance**
  ```bash
  # Check slow queries
  docker exec staging-postgres psql -U postgres -d agentic_staging -c "
    SELECT query, calls, mean_exec_time, max_exec_time
    FROM pg_stat_statements
    WHERE mean_exec_time > 100
    ORDER BY mean_exec_time DESC
    LIMIT 10;"

  # Expected: No queries > 500ms mean time
  ```

- [ ] **Cache hit rate**
  ```bash
  docker exec staging-redis redis-cli info stats | grep keyspace_hits
  docker exec staging-redis redis-cli info stats | grep keyspace_misses

  # Calculate hit rate
  # Expected: > 60% hit rate after warming period
  ```

- [ ] **Resource usage**
  ```bash
  # Check container resource usage
  docker stats --no-stream

  # Expected:
  # - CPU usage < 50% (under normal load)
  # - Memory usage < 80% of limits
  # - No containers constantly restarting
  ```

### 10. Error Monitoring

- [ ] **Check application logs**
  ```bash
  # Look for errors in last 30 minutes
  docker compose -f docker-compose.prod.yml logs --since 30m | grep -i error

  # Expected: No ERROR or CRITICAL messages
  ```

- [ ] **Check database errors**
  ```bash
  docker logs staging-postgres --since 30m | grep -i error

  # Expected: No connection errors, no query errors
  ```

- [ ] **Check Redis errors**
  ```bash
  docker logs staging-redis --since 30m | grep -i error

  # Expected: No connection errors
  ```

- [ ] **Review error rates in Grafana**
  - Navigate to https://grafana-staging.temponest.io
  - Check "Error Rate" dashboard
  - **Expected**: Error rate < 1%

---

## 24-Hour Stability Period

### Day 1 (Deployment Day)

**Hour 0-4: Intensive Monitoring**
- [ ] Check metrics every 30 minutes
- [ ] Review logs every hour
- [ ] Monitor resource usage trends
- [ ] Watch for memory leaks

**Hour 4-8: Reduced Monitoring**
- [ ] Check metrics every 2 hours
- [ ] Review critical alerts only
- [ ] Verify scheduled tasks executing

**Hour 8-24: Passive Monitoring**
- [ ] Check metrics every 4 hours
- [ ] Respond to alerts only
- [ ] Let automated tests run

### Day 2 (24 Hours Post-Deployment)

**Final Validation**
- [ ] Run full test suite again
  ```bash
  pytest web-ui/tests/ -v
  pytest services/agents/tests/ -v
  pytest services/auth/tests/ -v
  ```

- [ ] Performance regression check
  ```bash
  k6 run --vus 100 --duration 10m load-tests/agents-api.js
  # Compare to baseline
  ```

- [ ] Review 24h metrics
  - Error rate over 24h < 1%
  - No service restarts
  - No memory leaks detected
  - Database performance stable

- [ ] Collect feedback from team
  - Any bugs discovered?
  - Any performance issues?
  - Any UX problems?

**Go/No-Go Decision for Production**
- [ ] All tests passing
- [ ] No critical bugs
- [ ] Performance meets SLA
- [ ] Team confident in stability

**Decision**: ☐ GO to production ☐ NO-GO (address issues first)

---

## Troubleshooting Common Issues

### Issue 1: Service Won't Start

**Symptoms**: Container exits immediately, health check fails

**Diagnosis**:
```bash
# Check logs
docker compose logs [service]

# Check if port is already in use
netstat -tlnp | grep [port]

# Check if required dependencies are running
docker compose ps
```

**Solutions**:
- Ensure all environment variables are set
- Check database connection string
- Verify Redis is running
- Check for port conflicts

### Issue 2: Database Migration Fails

**Symptoms**: Migration script errors, service can't connect to DB

**Diagnosis**:
```bash
# Check postgres logs
docker logs staging-postgres

# Verify database exists
docker exec staging-postgres psql -U postgres -l

# Check migrations were applied
docker exec staging-postgres psql -U postgres -d agentic_staging -c \
  "SELECT indexname FROM pg_indexes WHERE schemaname = 'public';"
```

**Solutions**:
- Restore from backup
- Rerun migrations
- Check for table lock conflicts
- Verify database user permissions

### Issue 3: High Error Rate

**Symptoms**: 5xx errors > 5%, timeouts

**Diagnosis**:
```bash
# Check application logs
docker compose logs agents | grep ERROR

# Check database connections
docker exec staging-postgres psql -U postgres -c \
  "SELECT count(*) FROM pg_stat_activity;"

# Check resource usage
docker stats
```

**Solutions**:
- Scale up resources (CPU, memory)
- Check for infinite loops/memory leaks
- Verify database query performance
- Check external API availability

### Issue 4: Slow Performance

**Symptoms**: Response times > 1000ms, timeouts

**Diagnosis**:
```bash
# Check database slow queries
docker exec staging-postgres psql -U postgres -d agentic_staging -c \
  "SELECT query, mean_exec_time FROM pg_stat_statements
   ORDER BY mean_exec_time DESC LIMIT 10;"

# Check cache hit rate
docker exec staging-redis redis-cli info stats

# Check resource contention
docker stats
```

**Solutions**:
- Enable query caching
- Add database indexes
- Increase connection pool size
- Scale horizontally

---

## Rollback Procedure

**If issues found during staging validation:**

1. **Stop services**
   ```bash
   docker compose -f docker-compose.prod.yml down
   ```

2. **Restore database backup**
   ```bash
   docker exec staging-postgres psql -U postgres -d agentic_staging < \
     backups/staging_[timestamp].sql
   ```

3. **Checkout previous version**
   ```bash
   git checkout v1.7.0
   ```

4. **Redeploy**
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```

5. **Verify rollback**
   ```bash
   ./scripts/deploy/smoke-tests.sh
   ```

---

## Sign-Off

### Staging Validation Complete

- [ ] All automated tests passed
- [ ] All manual tests passed
- [ ] Performance meets baseline
- [ ] No critical issues found
- [ ] 24-hour stability achieved
- [ ] Team approves production deployment

**Approved By**:
- **Tech Lead**: _______________ Date: _______
- **QA Lead**: _______________ Date: _______
- **DevOps**: _______________ Date: _______

**Ready for Production**: ☐ YES ☐ NO (reason: _____________)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-13
**Next Review**: After staging deployment
**Owner**: DevOps/SRE Team
