# TempoNest Operations Guide

**Last Updated:** 2025-11-12
**Version:** 1.0

This guide covers deployment procedures, troubleshooting, rollback strategies, and operational best practices for TempoNest.

---

## Table of Contents

1. [Deployment Procedures](#deployment-procedures)
2. [Environment Management](#environment-management)
3. [Monitoring & Health Checks](#monitoring--health-checks)
4. [Troubleshooting](#troubleshooting)
5. [Rollback Procedures](#rollback-procedures)
6. [Backup & Recovery](#backup--recovery)
7. [Security Operations](#security-operations)
8. [Maintenance Tasks](#maintenance-tasks)
9. [Incident Response](#incident-response)

---

## Deployment Procedures

### Quick Reference

```bash
# Development deployment
cd docker
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Production deployment
cd docker
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Rolling deployment (zero-downtime)
./scripts/deploy/rolling-deploy.sh

# Verify deployment
./scripts/deploy/verify-deployment.sh

# Run smoke tests
./scripts/deploy/smoke-tests.sh
```

### Zero-Downtime Rolling Deployment

The rolling deployment script performs blue-green deployments with automatic health checks and rollback.

```bash
#!/bin/bash
# scripts/deploy/rolling-deploy.sh

# Usage
./scripts/deploy/rolling-deploy.sh [service_name]

# Deploy all services
./scripts/deploy/rolling-deploy.sh

# Deploy specific service
./scripts/deploy/rolling-deploy.sh agents
```

**How it works:**

1. **Backup Current State**
   - Tags current Docker images
   - Backs up docker-compose files
   - Records current version

2. **Pull New Images**
   - Downloads latest images from registry
   - Verifies image integrity

3. **Scale Up (Blue-Green)**
   ```bash
   # Scale up new version alongside old version
   docker-compose up -d --scale agents=2 --no-recreate
   ```

4. **Health Check New Version**
   ```bash
   # Wait for healthy status (up to 5 minutes)
   until docker inspect --format='{{.State.Health.Status}}' temponest-agents-new | grep "healthy"; do
       sleep 5
   done
   ```

5. **Switch Traffic**
   - Update load balancer / proxy
   - Gradual traffic shift

6. **Scale Down Old Version**
   ```bash
   docker-compose stop agents-old
   docker-compose rm -f agents-old
   ```

7. **Verify Deployment**
   - Run smoke tests
   - Check error rates
   - Validate metrics

8. **Cleanup**
   - Remove old containers
   - Clean up old images (keep last 3)

**On Failure:**
- Automatic rollback to previous version
- Notification sent (if configured)
- Logs collected for debugging

### Manual Deployment Steps

If you need to deploy manually:

```bash
# 1. Backup current state
./scripts/deploy/backup-current-state.sh

# 2. Pull latest code
git pull origin main

# 3. Build images
docker-compose -f docker/docker-compose.yml build --parallel

# 4. Stop services (with traffic draining)
docker-compose -f docker/docker-compose.yml stop

# 5. Start new services
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d

# 6. Wait for health checks
./scripts/deploy/health-check.sh --wait

# 7. Run smoke tests
./scripts/deploy/smoke-tests.sh

# 8. Monitor for issues
watch docker-compose ps
```

### GitHub Actions Deployment

Automated deployments via CI/CD:

```yaml
# .github/workflows/deploy.yml

name: Deploy to Production

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment || 'production' }}

    steps:
      - name: Deploy with rolling update
        run: |
          ssh ${{ secrets.DEPLOY_USER }}@${{ secrets.DEPLOY_HOST }} \
            'cd /opt/temponest && ./scripts/deploy/rolling-deploy.sh'

      - name: Verify deployment
        run: |
          ssh ${{ secrets.DEPLOY_USER }}@${{ secrets.DEPLOY_HOST }} \
            'cd /opt/temponest && ./scripts/deploy/verify-deployment.sh'

      - name: Run smoke tests
        run: |
          ssh ${{ secrets.DEPLOY_USER }}@${{ secrets.DEPLOY_HOST }} \
            'cd /opt/temponest && ./scripts/deploy/smoke-tests.sh'
```

---

## Environment Management

### Development Environment

**Configuration:** `docker-compose.dev.yml`

**Features:**
- Hot reload enabled (`--reload` flags)
- Source code volume mounts
- Debug ports exposed
- Lower resource limits
- `restart: unless-stopped`

**Start Development:**
```bash
cd docker
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Watch logs
docker-compose logs -f agents auth scheduler
```

**Development Best Practices:**
1. Use hot reload for faster iteration
2. Volume mounts for code changes
3. Lower resource limits (laptop-friendly)
4. Debug ports for IDE integration
5. Use staging databases (not production)

### Production Environment

**Configuration:** `docker-compose.prod.yml`

**Features:**
- No hot reload (better performance)
- No source code mounts (code baked in)
- Production environment variables
- Higher resource limits
- `restart: always`
- Redis with maxmemory policy
- Prometheus with 90-day retention

**Start Production:**
```bash
cd docker
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor startup
docker-compose ps
watch docker-compose ps
```

**Production Best Practices:**
1. Use immutable Docker images
2. Set appropriate resource limits
3. Configure restart policies
4. Enable persistent volumes
5. Use secrets management
6. Configure logging aggregation

### Environment Variables

**Required:**
```bash
# docker/.env

# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/agentic
POSTGRES_PASSWORD=change-in-production

# Redis
REDIS_URL=redis://redis:6379/0

# Auth
JWT_SECRET=change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your-bot-token

# Langfuse
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
```

**Performance Tuning:**
```bash
# Connection Pools
AGENTS_POOL_MIN_SIZE=15
AGENTS_POOL_MAX_SIZE=100
AUTH_POOL_MIN_SIZE=10
AUTH_POOL_MAX_SIZE=50
SCHEDULER_POOL_MIN_SIZE=5
SCHEDULER_POOL_MAX_SIZE=20

# Caching TTLs
JWT_CACHE_TTL=30
PERMISSIONS_CACHE_TTL=300
RAG_CACHE_TTL=900
HEALTH_CACHE_TTL=10

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=20
```

---

## Monitoring & Health Checks

### Health Check Script

```bash
#!/bin/bash
# scripts/deploy/health-check.sh

# Check all services
./scripts/deploy/health-check.sh

# Check specific service
./scripts/deploy/health-check.sh agents

# Wait for healthy status
./scripts/deploy/health-check.sh --wait --timeout=300
```

**What it checks:**
1. Container status (running/exited)
2. Health endpoint response (200 OK)
3. Recent error logs
4. Resource usage (CPU, memory)
5. Restart count (alerts if > 3)

### Service Health Endpoints

```bash
# Core services
curl http://localhost:9000/health  # Agents
curl http://localhost:9002/health  # Auth
curl http://localhost:9003/health  # Scheduler
curl http://localhost:9001/health  # Approval UI

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "qdrant": "healthy"
  }
}
```

### Monitoring Dashboard Access

**Grafana:** http://localhost:3001
- Username: admin
- Password: admin (change on first login)

**Key Dashboards:**
1. **Service Overview**
   - Service health status
   - Request rates
   - Error rates
   - Response times

2. **Database Performance**
   - Query duration (p50, p95, p99)
   - Connection pool usage
   - Slow queries
   - Index usage

3. **Cache Performance**
   - Hit rate
   - Miss rate
   - Eviction rate
   - Memory usage

4. **Resource Utilization**
   - CPU usage per service
   - Memory usage per service
   - Disk I/O
   - Network traffic

### Alert Configuration

**Critical Alerts (PagerDuty/Slack):**
- Service down for > 2 minutes
- Error rate > 5%
- p95 response time > 1000ms
- Database connections exhausted
- Disk usage > 90%

**Warning Alerts (Email):**
- Error rate > 1%
- p95 response time > 500ms
- Cache hit rate < 60%
- Memory usage > 80%
- CPU usage > 75%

---

## Troubleshooting

### Service Won't Start

**Symptoms:**
- Container exits immediately
- Restart loop
- Health checks failing

**Diagnosis:**
```bash
# Check container logs
docker logs temponest-agents --tail=100

# Check container exit code
docker inspect temponest-agents | grep ExitCode

# Check resource limits
docker stats --no-stream temponest-agents

# Check dependencies (DB, Redis)
docker-compose ps
```

**Common Causes & Solutions:**

1. **Database connection failure**
   ```bash
   # Check PostgreSQL is running
   docker-compose ps postgres

   # Test connection
   docker exec -it temponest-postgres pg_isready

   # Check credentials
   docker-compose exec agents env | grep DATABASE_URL
   ```

2. **Redis connection failure**
   ```bash
   # Check Redis is running
   docker-compose ps redis

   # Test connection
   docker exec -it temponest-redis redis-cli PING
   ```

3. **Missing environment variables**
   ```bash
   # Verify .env file exists
   ls -la docker/.env

   # Check required vars
   docker-compose config | grep -A 5 environment
   ```

4. **Port conflicts**
   ```bash
   # Check port availability
   sudo lsof -i :9000
   sudo lsof -i :9002

   # Change ports in docker-compose.yml if needed
   ```

5. **Memory limits exceeded**
   ```bash
   # Check memory usage
   docker stats --no-stream

   # Increase limits in docker-compose.prod.yml
   ```

### High Response Times

**Symptoms:**
- API responses > 500ms
- Timeout errors
- Slow page loads

**Diagnosis:**
```bash
# Check OpenTelemetry traces
# Visit: http://localhost:16686

# Check database slow queries
docker exec -it temponest-postgres psql -U postgres -d agentic -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 500
ORDER BY mean_exec_time DESC
LIMIT 10;"

# Check Redis cache hit rate
docker exec -it temponest-redis redis-cli INFO stats | grep keyspace

# Check service CPU/memory
docker stats temponest-agents temponest-auth temponest-scheduler
```

**Solutions:**

1. **Add missing indexes**
   ```sql
   -- Find missing indexes
   SELECT schemaname, tablename, attname
   FROM pg_stats
   WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
   ORDER BY n_distinct DESC;
   ```

2. **Increase cache TTLs**
   ```bash
   # In docker/.env
   PERMISSIONS_CACHE_TTL=600  # Increase from 300
   RAG_CACHE_TTL=1800          # Increase from 900
   ```

3. **Scale connection pools**
   ```bash
   # In docker/.env
   AGENTS_POOL_MAX_SIZE=150    # Increase from 100
   ```

4. **Optimize queries**
   - Use database views for complex queries
   - Batch operations instead of loops
   - Select only needed columns

### Database Connection Errors

**Symptoms:**
- "Connection pool exhausted"
- "Too many connections"
- Slow query performance

**Diagnosis:**
```bash
# Check active connections
docker exec -it temponest-postgres psql -U postgres -d agentic -c "
SELECT count(*), state
FROM pg_stat_activity
GROUP BY state;"

# Check connection limits
docker exec -it temponest-postgres psql -U postgres -c "SHOW max_connections;"

# Check per-service connections
docker exec -it temponest-postgres psql -U postgres -d agentic -c "
SELECT application_name, count(*)
FROM pg_stat_activity
GROUP BY application_name;"
```

**Solutions:**

1. **Increase max_connections**
   ```yaml
   # docker/docker-compose.yml
   services:
     postgres:
       command: postgres -c max_connections=200  # Default: 100
   ```

2. **Tune connection pools**
   ```bash
   # Reduce pool sizes if too many connections
   AGENTS_POOL_MAX_SIZE=50    # Reduce from 100
   AUTH_POOL_MAX_SIZE=30      # Reduce from 50
   ```

3. **Enable connection recycling**
   ```python
   # Already configured
   max_queries=50000  # Recycle after 50k queries
   max_inactive_connection_lifetime=300  # Close idle after 5min
   ```

4. **Identify connection leaks**
   ```bash
   # Check long-running connections
   docker exec -it temponest-postgres psql -U postgres -d agentic -c "
   SELECT pid, usename, state, query, now() - query_start AS duration
   FROM pg_stat_activity
   WHERE state != 'idle'
   ORDER BY duration DESC;"
   ```

### Memory Issues

**Symptoms:**
- OOM (Out of Memory) kills
- Container restarts
- Swap usage

**Diagnosis:**
```bash
# Check container memory usage
docker stats --no-stream

# Check system memory
free -h

# Check for memory leaks
docker exec -it <container> ps aux --sort=-%mem | head -10

# Check swap usage
swapon --show
```

**Solutions:**

1. **Increase memory limits**
   ```yaml
   # docker-compose.prod.yml
   services:
     agents:
       deploy:
         resources:
           limits:
             memory: 4G  # Increase from 2G
   ```

2. **Configure Redis maxmemory**
   ```yaml
   services:
     redis:
       command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
   ```

3. **Tune PostgreSQL memory**
   ```yaml
   services:
     postgres:
       command: |
         postgres
         -c shared_buffers=1GB
         -c effective_cache_size=3GB
         -c work_mem=16MB
   ```

4. **Review application memory usage**
   - Check for memory leaks
   - Optimize object caching
   - Use generators for large datasets

### Docker Build Failures

**Symptoms:**
- Build hangs or times out
- "No space left on device"
- Image pull failures

**Diagnosis:**
```bash
# Check disk space
df -h

# Check Docker disk usage
docker system df

# Check build cache
docker builder du
```

**Solutions:**

1. **Clean up Docker system**
   ```bash
   # Remove unused images
   docker image prune -a

   # Remove unused volumes
   docker volume prune

   # Remove build cache
   docker builder prune -a

   # Full cleanup (caution!)
   docker system prune -a --volumes
   ```

2. **Increase build resources**
   ```bash
   # In Docker Desktop: Settings > Resources
   # Increase CPUs: 4-8 cores
   # Increase Memory: 8-16 GB
   # Increase Disk: 100+ GB
   ```

3. **Use BuildKit**
   ```bash
   export DOCKER_BUILDKIT=1
   docker-compose build --parallel
   ```

---

## Rollback Procedures

### Automatic Rollback

The rolling deployment script automatically rolls back on failure:

```bash
# Rollback triggers:
# - Health check failures (>5 minutes)
# - Smoke test failures
# - Error rate > 10%
# - Manual cancellation (Ctrl+C)

# Rollback process:
# 1. Stop new version
# 2. Restart old version
# 3. Verify health
# 4. Restore traffic
# 5. Clean up new version
```

### Manual Rollback

```bash
# Rollback script
./scripts/deploy/rollback.sh

# Rollback to specific version
./scripts/deploy/rollback.sh v1.2.3

# Rollback specific service
./scripts/deploy/rollback.sh agents
```

**Manual Rollback Steps:**

```bash
# 1. Identify previous version
git tag --sort=-version:refname | head -5

# 2. Stop current services
docker-compose -f docker/docker-compose.yml stop

# 3. Checkout previous version
git checkout v1.2.3

# 4. Restore database backup (if needed)
./scripts/backup/restore-database.sh backup-2025-11-12.sql

# 5. Start previous version
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d

# 6. Verify health
./scripts/deploy/health-check.sh --wait

# 7. Run smoke tests
./scripts/deploy/smoke-tests.sh

# 8. Monitor for stability
watch docker-compose ps
```

### Database Rollback

```bash
# Restore from backup
./scripts/backup/restore-database.sh backup-2025-11-12.sql

# Rollback migration
docker exec -it temponest-postgres psql -U postgres -d agentic -c "
-- Run rollback migration
\i /migrations/rollback/007_rollback.sql"

# Verify data integrity
docker exec -it temponest-postgres psql -U postgres -d agentic -c "
SELECT COUNT(*) FROM runs;
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM users;"
```

---

## Backup & Recovery

### Database Backups

**Automated Daily Backups:**

```bash
#!/bin/bash
# scripts/backup/backup-database.sh

# Backup PostgreSQL
BACKUP_DIR="/opt/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

docker exec temponest-postgres pg_dump -U postgres -d agentic \
  > "$BACKUP_DIR/agentic_$TIMESTAMP.sql"

# Compress
gzip "$BACKUP_DIR/agentic_$TIMESTAMP.sql"

# Retain last 30 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
```

**Backup Schedule (Cron):**
```bash
# /etc/cron.d/temponest-backup

# Daily at 2 AM
0 2 * * * /opt/temponest/scripts/backup/backup-database.sh

# Weekly full backup Sunday 3 AM
0 3 * * 0 /opt/temponest/scripts/backup/full-backup.sh
```

**Restore from Backup:**

```bash
# scripts/backup/restore-database.sh

BACKUP_FILE=$1

# Stop services
docker-compose stop agents auth scheduler

# Restore database
gunzip < "$BACKUP_FILE" | \
  docker exec -i temponest-postgres psql -U postgres -d agentic

# Restart services
docker-compose start agents auth scheduler

# Verify
./scripts/deploy/health-check.sh
```

### Redis Backups

```bash
# Enable Redis persistence
# docker-compose.yml
services:
  redis:
    command: redis-server --save 60 1000 --appendonly yes
    volumes:
      - redis-data:/data

# Manual backup
docker exec temponest-redis redis-cli BGSAVE

# Copy backup
docker cp temponest-redis:/data/dump.rdb /opt/backups/redis/dump_$(date +%Y%m%d).rdb
```

### Disaster Recovery

**Recovery Time Objective (RTO):** 15 minutes
**Recovery Point Objective (RPO):** 1 hour

**Full System Restore:**

```bash
# 1. Provision infrastructure
# - Server with Docker installed
# - Network configuration
# - DNS records

# 2. Clone repository
git clone https://github.com/your-org/temponest.git
cd temponest

# 3. Restore environment variables
cp /backup/.env docker/.env

# 4. Restore database
./scripts/backup/restore-database.sh /backup/latest.sql.gz

# 5. Restore Redis data
docker cp /backup/redis/dump.rdb temponest-redis:/data/

# 6. Restore volumes
docker volume create temponest-postgres-data
docker run --rm -v temponest-postgres-data:/data \
  -v /backup/postgres-volume:/backup alpine \
  sh -c "cd /data && tar xzf /backup/postgres-data.tar.gz"

# 7. Start services
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d

# 8. Verify recovery
./scripts/deploy/health-check.sh --wait
./scripts/deploy/smoke-tests.sh

# 9. Update DNS / load balancer
```

---

## Security Operations

### Security Scanning

**Scan Schedule:**
- Daily: Dependency vulnerabilities
- Weekly: Container image scanning
- Monthly: Full security audit

**Run Security Scans:**

```bash
# Python dependencies
docker-compose exec agents pip install safety
docker-compose exec agents safety check

# Bandit (Python security linter)
docker-compose exec agents bandit -r app/

# Node.js dependencies
docker-compose exec console npm audit

# Docker image scanning
docker scan temponest-agents:latest
docker scan temponest-auth:latest
```

### Secret Rotation

**JWT Secret Rotation:**

```bash
# 1. Generate new secret
NEW_SECRET=$(openssl rand -base64 32)

# 2. Update .env
echo "JWT_SECRET=$NEW_SECRET" >> docker/.env.new

# 3. Deploy with both secrets (grace period)
# - Old secret for existing tokens
# - New secret for new tokens

# 4. After token expiry (24 hours), remove old secret
```

**Database Password Rotation:**

```bash
# 1. Create new password
NEW_PASSWORD=$(openssl rand -base64 24)

# 2. Update PostgreSQL password
docker exec -it temponest-postgres psql -U postgres -c "
ALTER USER postgres WITH PASSWORD '$NEW_PASSWORD';"

# 3. Update .env
sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$NEW_PASSWORD/" docker/.env

# 4. Restart services
docker-compose restart agents auth scheduler
```

### Access Control

**Service Authentication:**
- All internal services use JWT authentication
- API keys for external access
- Rate limiting on all endpoints

**Database Access:**
- Principle of least privilege
- Read-only replicas for analytics
- Connection pooling limits

**Network Security:**
- Internal Docker network
- No direct external access to databases
- Reverse proxy for public endpoints

---

## Maintenance Tasks

### Daily

```bash
# Check service health
./scripts/deploy/health-check.sh

# Monitor error rates
# Visit Grafana: http://localhost:3001

# Review critical alerts
# Check PagerDuty / Slack

# Verify backups completed
ls -lh /opt/backups/postgres/ | tail -1
```

### Weekly

```bash
# Review slow query logs
docker exec -it temponest-postgres psql -U postgres -d agentic -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
WHERE mean_exec_time > 500
ORDER BY mean_exec_time DESC
LIMIT 20;"

# Analyze cache performance
docker exec -it temponest-redis redis-cli INFO stats

# Check disk usage
df -h
docker system df

# Review and restart containers if needed
docker-compose restart
```

### Monthly

```bash
# Security updates
docker-compose pull
docker-compose up -d

# Database maintenance
docker exec -it temponest-postgres psql -U postgres -d agentic -c "
VACUUM ANALYZE;
REINDEX DATABASE agentic;"

# Dependency updates
cd apps/console && npm update
cd services/agents && pip list --outdated

# Performance benchmarking
./scripts/performance/benchmark.sh

# Capacity planning review
./scripts/reporting/capacity-report.sh
```

### Quarterly

```bash
# Full security audit
./scripts/security/full-audit.sh

# Performance optimization review
# - Analyze slow traces
# - Review and optimize database queries
# - Update resource limits if needed

# Disaster recovery drill
./scripts/dr/disaster-recovery-test.sh

# Architecture review
# - Review service dependencies
# - Identify bottlenecks
# - Plan optimizations
```

---

## Incident Response

### Incident Classification

**P0 (Critical) - Response: Immediate**
- System completely down
- Data loss or corruption
- Security breach
- RTO: 15 minutes

**P1 (High) - Response: < 1 hour**
- Service degradation affecting >50% users
- Critical feature unavailable
- Performance degradation >200%
- RTO: 2 hours

**P2 (Medium) - Response: < 4 hours**
- Service degradation affecting <50% users
- Non-critical feature unavailable
- Performance degradation 50-200%
- RTO: 8 hours

**P3 (Low) - Response: Next business day**
- Minor issues
- Cosmetic bugs
- Performance degradation <50%

### Incident Response Procedure

1. **Detection & Alert**
   - Monitoring alert triggers
   - User reports
   - Automated health checks

2. **Assessment**
   - Determine severity (P0-P3)
   - Identify affected services
   - Estimate impact

3. **Response Team**
   - Assign incident commander
   - Mobilize on-call engineers
   - Create incident channel (Slack)

4. **Mitigation**
   - Implement immediate fixes
   - Rollback if necessary
   - Communicate with stakeholders

5. **Resolution**
   - Verify fix deployed
   - Run smoke tests
   - Monitor for recurrence

6. **Post-Mortem**
   - Document timeline
   - Root cause analysis
   - Action items for prevention

### Incident Response Commands

```bash
# Quick diagnostics
./scripts/incident/quick-diagnose.sh

# Gather logs
./scripts/incident/gather-logs.sh > incident-logs-$(date +%Y%m%d-%H%M%S).txt

# Emergency rollback
./scripts/deploy/rollback.sh

# Emergency restart
docker-compose restart

# Check last deployments
git log --oneline --decorate -10

# Database snapshot (before risky operation)
./scripts/backup/snapshot-database.sh emergency

# Enable debug logging
docker-compose exec agents env LOG_LEVEL=DEBUG
docker-compose restart agents
```

---

## Additional Resources

- [PERFORMANCE.md](PERFORMANCE.md) - Performance optimization guide
- [TELEMETRY_INTEGRATION.md](TELEMETRY_INTEGRATION.md) - Observability setup
- [DOCKER_USAGE.md](../DOCKER_USAGE.md) - Docker environment guide
- [OPTIMIZATION_PROGRESS.md](../OPTIMIZATION_PROGRESS.md) - Optimization tracking

---

**Maintained By:** Operations Team
**Last Review:** 2025-11-12
**Next Review:** 2025-12-12
**On-Call Rotation:** Check PagerDuty schedule
