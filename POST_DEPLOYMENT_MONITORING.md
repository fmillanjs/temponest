# Post-Deployment Monitoring Checklist

**Purpose**: Monitor TempoNest v1.8.0 production deployment for 48 hours
**Timeline**: Day 0 (Deployment) through Day 2
**Goal**: Ensure stable operation and catch issues early

---

## Monitoring Schedule

### Phase 1: Intensive Monitoring (0-4 Hours Post-Deployment)
**Frequency**: Every 15 minutes
**Team**: Full deployment team on-call
**Focus**: Catch immediate issues

### Phase 2: Active Monitoring (4-24 Hours)
**Frequency**: Every 2 hours
**Team**: On-call engineer + backup
**Focus**: Detect trending issues

### Phase 3: Standard Monitoring (24-48 Hours)
**Frequency**: Every 4 hours
**Team**: On-call engineer
**Focus**: Confirm stability

---

## Real-Time Dashboards

### Primary Dashboard: Deployment Overview
**URL**: http://grafana.temponest.io/d/deployment-overview

**Key Panels**:
1. **Request Rate** (Blue vs Green)
2. **Error Rate** (5xx by service)
3. **Response Time** (p50, p95, p99)
4. **Resource Usage** (CPU, Memory, Disk)
5. **Active Connections** (DB, Redis)

### Secondary Dashboards

- **Application Health**: http://grafana.temponest.io/d/app-health
- **Database Performance**: http://grafana.temponest.io/d/db-performance
- **Infrastructure**: http://grafana.temponest.io/d/infrastructure
- **Business Metrics**: http://grafana.temponest.io/d/business-metrics

---

## Metrics & Thresholds

### 1. API Performance Metrics

#### Response Time (Target: Improved from baseline)

| Metric | Baseline (v1.7) | Target (v1.8) | Critical Threshold | Action |
|--------|-----------------|---------------|-------------------|---------|
| p50 latency | 150ms | < 100ms | > 300ms | Investigate |
| p95 latency | 800ms | < 400ms | > 1000ms | Alert team |
| p99 latency | 2000ms | < 1000ms | > 3000ms | Rollback consider |
| Max latency | 5000ms | < 2500ms | > 10000ms | Immediate rollback |

**Check Command**:
```bash
# Query Prometheus for p95 latency
curl -s 'http://prometheus:9090/api/v1/query?query=
  histogram_quantile(0.95,
    rate(http_request_duration_seconds_bucket[5m])
  )' | jq '.data.result[0].value[1]'

# Expected: < 0.4 (400ms)
```

#### Throughput (Target: Maintained or improved)

| Metric | Baseline | Target | Critical Threshold | Action |
|--------|----------|--------|-------------------|---------|
| Requests/sec | 50 rps | 50-80 rps | < 30 rps | Check capacity |
| Active requests | 5-20 | 5-20 | > 100 | Scale up |

**Check Command**:
```bash
# Current request rate
curl -s 'http://prometheus:9090/api/v1/query?query=
  rate(http_requests_total[1m])
' | jq '.data.result[0].value[1]'
```

### 2. Error Rates (Target: < 1%)

| Service | Normal Rate | Warning Threshold | Critical Threshold | Action |
|---------|-------------|------------------|-------------------|---------|
| **Agents** | < 0.5% | > 1% | > 5% | Investigate/Rollback |
| **Auth** | < 0.1% | > 0.5% | > 2% | Investigate/Rollback |
| **Scheduler** | < 0.2% | > 1% | > 3% | Investigate/Rollback |
| **Web UI** | < 0.3% | > 1% | > 5% | Investigate/Rollback |

**Check Command**:
```bash
# 5xx error rate by service (last 5 min)
curl -s 'http://prometheus:9090/api/v1/query?query=
  sum by (service) (
    rate(http_requests_total{status=~"5.."}[5m])
  ) / sum by (service) (
    rate(http_requests_total[5m])
  ) * 100
' | jq '.data.result'

# Expected: Each service < 1%
```

### 3. Resource Usage

#### CPU Usage

| Service | Normal | Warning | Critical | Action |
|---------|--------|---------|----------|---------|
| **Agents** | 20-40% | > 70% | > 90% | Scale/Optimize |
| **Scheduler** | 5-15% | > 50% | > 80% | Investigate |
| **Auth** | 5-10% | > 40% | > 70% | Investigate |
| **Postgres** | 10-30% | > 60% | > 85% | Check queries |
| **Redis** | 5-15% | > 50% | > 75% | Check cache |

**Check Command**:
```bash
# Current CPU usage
docker stats --no-stream --format \
  "table {{.Name}}\t{{.CPUPerc}}\t{{.MemPerc}}"
```

#### Memory Usage

| Service | Normal | Warning | Critical | Action |
|---------|--------|---------|----------|---------|
| **Agents** | 500-800MB | > 1.5GB | > 2GB | Check leaks/Restart |
| **Scheduler** | 200-400MB | > 800MB | > 1GB | Check leaks |
| **Auth** | 150-300MB | > 600MB | > 800MB | Investigate |
| **Postgres** | 800MB-1.5GB | > 3GB | > 4GB | Check cache size |

**Check for Memory Leaks**:
```bash
# Memory usage trend over 1 hour
curl -s 'http://prometheus:9090/api/v1/query?query=
  container_memory_usage_bytes{container=~"agents|scheduler|auth"}[1h]
' | jq '.data.result'

# Look for: Constantly increasing memory (leak indicator)
```

### 4. Database Metrics

#### Connection Pool

| Metric | Normal | Warning | Critical | Action |
|--------|--------|---------|----------|---------|
| **Active connections** | 10-30 | > 60 | > 80 | Scale pool/Check leaks |
| **Idle connections** | 5-15 | < 2 | 0 | Increase min_size |
| **Wait time** | < 10ms | > 50ms | > 200ms | Increase pool size |

**Check Command**:
```bash
# Current connections by state
docker exec postgres psql -U postgres -d agentic -c "
  SELECT state, count(*)
  FROM pg_stat_activity
  WHERE datname = 'agentic'
  GROUP BY state;"

# Expected:
# active: 10-30
# idle: 5-15
```

#### Query Performance

| Metric | Baseline | Target | Critical | Action |
|--------|----------|--------|----------|---------|
| **Avg query time** | 15ms | < 10ms | > 50ms | Check slow queries |
| **Slow queries (>100ms)** | 5/min | < 2/min | > 20/min | Optimize queries |
| **Lock waits** | 0 | 0 | > 5/min | Check transactions |

**Check Command**:
```bash
# Top 10 slowest queries
docker exec postgres psql -U postgres -d agentic -c "
  SELECT substring(query, 1, 60) as query,
         calls, mean_exec_time, max_exec_time
  FROM pg_stat_statements
  WHERE mean_exec_time > 50
  ORDER BY mean_exec_time DESC
  LIMIT 10;"
```

### 5. Cache Performance (Redis)

| Metric | Target | Warning | Critical | Action |
|--------|--------|---------|----------|---------|
| **Hit rate** | > 60% | < 40% | < 20% | Check cache strategy |
| **Memory usage** | < 500MB | > 800MB | > 1GB | Increase maxmemory |
| **Evictions** | < 100/min | > 500/min | > 2000/min | Increase memory |
| **Connections** | 10-50 | > 100 | > 200 | Check connection leaks |

**Check Command**:
```bash
# Cache statistics
docker exec redis redis-cli info stats | grep -E "(keyspace_hits|keyspace_misses|evicted_keys|used_memory_human)"

# Calculate hit rate:
# hit_rate = hits / (hits + misses) * 100
# Expected: > 60%
```

### 6. Queue Metrics

#### Agent Execution Queue

| Metric | Normal | Warning | Critical | Action |
|--------|--------|---------|----------|---------|
| **Queue depth** | 0-10 | > 50 | > 200 | Scale workers |
| **Processing time** | < 30s | > 2min | > 5min | Check workers |
| **Failed tasks** | < 1% | > 5% | > 20% | Investigate errors |

**Check Command**:
```bash
# Queue depth
docker exec redis redis-cli llen agent_execution_queue

# Expected: < 10 under normal load
```

### 7. External Dependencies

#### Ollama (LLM Service)

| Metric | Normal | Warning | Critical | Action |
|--------|--------|---------|----------|---------|
| **Response time** | 2-5s | > 10s | > 30s | Check GPU/CPU |
| **Availability** | 100% | < 99% | < 95% | Restart service |
| **Queue depth** | 0-5 | > 20 | > 50 | Scale instances |

**Check Command**:
```bash
# Ollama health
curl -s http://localhost:11434/api/health

# Expected: {"status":"ok"}
```

#### Qdrant (Vector DB)

| Metric | Normal | Warning | Critical | Action |
|--------|--------|---------|----------|---------|
| **Query time** | < 100ms | > 500ms | > 2000ms | Check indexes |
| **Memory usage** | < 2GB | > 4GB | > 6GB | Scale storage |

**Check Command**:
```bash
# Qdrant health
curl -s http://localhost:6333/health

# Expected: {"title":"healthy","status":"ok"}
```

---

## Monitoring Procedures

### Every 15 Minutes (Hours 0-4)

1. **Check Deployment Dashboard**
   ```bash
   # Open Grafana
   open http://grafana.temponest.io/d/deployment-overview

   # Verify:
   ✅ Error rate < 1%
   ✅ p95 latency < 500ms
   ✅ CPU < 70%
   ✅ Memory stable (not increasing)
   ```

2. **Check Recent Errors**
   ```bash
   # Last 15 minutes errors
   docker compose logs --since 15m | grep -i error | grep -v "DEBUG"

   # Expected: 0-2 errors (none critical)
   ```

3. **Check Health Endpoints**
   ```bash
   curl -s http://localhost:9000/health | jq '.status'  # agents
   curl -s http://localhost:9002/health | jq '.status'  # auth
   curl -s http://localhost:9003/health | jq '.status'  # scheduler

   # All should return: "healthy"
   ```

4. **Record Observations**
   ```markdown
   ## [Timestamp]
   - Error rate: ___%
   - p95 latency: ___ms
   - CPU avg: ___%
   - Issues: [None / Description]
   - Action taken: [None / Description]
   ```

### Every 2 Hours (Hours 4-24)

1. **Run Automated Health Check**
   ```bash
   ./scripts/deploy/health-check.sh --environment production

   # Expected: All checks pass ✅
   ```

2. **Check Resource Trends**
   ```bash
   # CPU trend (last 2 hours)
   curl -s 'http://prometheus:9090/api/v1/query?query=
     avg(rate(container_cpu_usage_seconds_total[2h]))
   ' | jq

   # Memory trend (last 2 hours)
   curl -s 'http://prometheus:9090/api/v1/query?query=
     avg(container_memory_usage_bytes[2h])
   ' | jq

   # Look for: Stable trends (not constantly increasing)
   ```

3. **Check Database Performance**
   ```bash
   # Connection count
   docker exec postgres psql -U postgres -d agentic -c \
     "SELECT count(*) FROM pg_stat_activity WHERE datname = 'agentic';"

   # Slow queries
   docker exec postgres psql -U postgres -d agentic -c \
     "SELECT COUNT(*) FROM pg_stat_statements WHERE mean_exec_time > 100;"

   # Expected: Connections < 50, Slow queries < 10
   ```

4. **Verify Business Metrics**
   ```bash
   # Total executions (last 2 hours)
   curl -s http://localhost:8082/api/metrics/executions?hours=2 | jq

   # Expected: Normal business activity continuing
   ```

### Every 4 Hours (Hours 24-48)

1. **System Health Summary**
   ```bash
   # Generate summary report
   ./scripts/monitoring/health-summary.sh

   # Review:
   - Uptime: 100%
   - Error rate: < 1%
   - Performance: Within SLA
   - Resource usage: Stable
   ```

2. **Check for Anomalies**
   ```bash
   # Unusual error patterns
   docker compose logs --since 4h | grep ERROR | sort | uniq -c | sort -rn | head -10

   # Expected: No repeated error patterns
   ```

3. **Database Maintenance Check**
   ```bash
   # Table bloat
   docker exec postgres psql -U postgres -d agentic -c \
     "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
      FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size DESC LIMIT 10;"

   # Index usage
   docker exec postgres psql -U postgres -d agentic -c \
     "SELECT schemaname, tablename, indexname, idx_scan
      FROM pg_stat_user_indexes WHERE idx_scan = 0;"

   # Expected: No unused indexes, tables growing normally
   ```

---

## Alert Response Procedures

### Critical Alert: Service Down

**Trigger**: Health check fails 3+ times

**Immediate Actions** (within 2 minutes):
1. Check service status:
   ```bash
   docker ps -a | grep [service-name]
   docker logs [service-name] --tail=100
   ```

2. Attempt restart:
   ```bash
   docker compose restart [service-name]
   ```

3. If restart fails:
   ```bash
   # Initiate rollback
   ./scripts/deploy/rollback.sh --immediate
   ```

4. Notify team in #ops-critical

### Critical Alert: High Error Rate (> 5%)

**Trigger**: 5xx errors > 5% for 2 minutes

**Immediate Actions** (within 5 minutes):
1. Identify error source:
   ```bash
   docker compose logs --since 5m | grep "ERROR\|5[0-9][0-9]" | head -50
   ```

2. Check if specific endpoint:
   ```bash
   # Query error logs for patterns
   curl -s 'http://prometheus:9090/api/v1/query?query=
     sum by (endpoint) (
       rate(http_requests_total{status=~"5.."}[5m])
     )
   ' | jq
   ```

3. If widespread, initiate rollback:
   ```bash
   ./scripts/deploy/rollback.sh
   ```

4. If isolated, disable problematic feature:
   ```bash
   # Feature flag or kill specific routes
   ```

### Warning Alert: Elevated Response Time

**Trigger**: p95 > 1000ms for 5 minutes

**Actions** (within 10 minutes):
1. Check for slow queries:
   ```bash
   docker exec postgres psql -U postgres -d agentic -c \
     "SELECT query, mean_exec_time FROM pg_stat_statements
      ORDER BY mean_exec_time DESC LIMIT 5;"
   ```

2. Check cache hit rate:
   ```bash
   docker exec redis redis-cli info stats | grep keyspace
   ```

3. Check resource saturation:
   ```bash
   docker stats --no-stream
   ```

4. Scale if needed:
   ```bash
   docker compose up -d --scale agents=3
   ```

### Warning Alert: Memory Pressure

**Trigger**: Memory usage > 85%

**Actions** (within 15 minutes):
1. Check for memory leak:
   ```bash
   # Memory usage over time
   docker stats --no-stream --format "{{.Name}}\t{{.MemUsage}}"

   # Wait 5 minutes, check again
   # If constantly increasing → memory leak
   ```

2. Check top memory consumers:
   ```bash
   docker stats --no-stream | sort -k 4 -h
   ```

3. If leak confirmed, restart affected service:
   ```bash
   docker compose restart [service-with-leak]
   ```

4. If persistent, consider rollback

---

## Success Criteria Review

### After 24 Hours

**Deployment Success Checklist**:
- [ ] **Uptime**: 100% (no unplanned downtime)
- [ ] **Error rate**: < 1% (improved or maintained)
- [ ] **Performance**: p95 latency < 500ms (50% improvement achieved)
- [ ] **Resource usage**: Stable (no leaks detected)
- [ ] **Database**: No connection issues, query performance improved
- [ ] **Cache**: Hit rate > 60%
- [ ] **Scheduled tasks**: 100% execution success rate
- [ ] **Webhooks**: Delivery success > 95%
- [ ] **Customer complaints**: 0 deployment-related issues
- [ ] **Team confidence**: High (no concerns raised)

### After 48 Hours

**Stability Confirmation**:
- [ ] All 24h criteria still met
- [ ] No degradation trends observed
- [ ] Resource usage patterns understood
- [ ] Any minor issues documented and resolved
- [ ] Team trained on new monitoring dashboards
- [ ] Runbooks updated with lessons learned

**Decision Point**:
- ☐ **SUCCESS**: Deployment stable, decommission Blue environment
- ☐ **CONCERNS**: Extend monitoring period by 24h
- ☐ **FAILURE**: Initiate rollback, post-mortem required

---

## Data Collection

### Metrics to Export for Analysis

```bash
# Export performance data (last 48h)
curl -s 'http://prometheus:9090/api/v1/query_range?query=
  http_request_duration_seconds{quantile="0.95"}&
  start=..&end=..&step=300
' > performance_48h.json

# Export error rates
curl -s 'http://prometheus:9090/api/v1/query_range?query=
  rate(http_requests_total{status=~"5.."}[5m])&
  start=..&end=..&step=300
' > errors_48h.json

# Export resource usage
docker stats --no-stream --format json > resources_snapshot.json
```

### Incident Log Template

```markdown
## Incident Log: [Date/Time]

**Issue**: [Brief description]
**Severity**: Critical / Warning / Info
**Service Affected**: [Service name]
**Duration**: [Start time] - [End time]

**Timeline**:
- [HH:MM] Issue detected
- [HH:MM] Team notified
- [HH:MM] Root cause identified
- [HH:MM] Mitigation applied
- [HH:MM] Issue resolved

**Root Cause**: [Detailed explanation]
**Resolution**: [Actions taken]
**Prevention**: [Future prevention measures]
**Follow-up**: [Required actions]
```

---

## Post-48h Activities

### 1. Generate Deployment Report

```bash
# Run report generator
./scripts/monitoring/deployment-report.sh --start=[deploy-timestamp] --end=[now]

# Report includes:
# - Performance summary (before/after)
# - Error analysis
# - Resource usage trends
# - Cost analysis
# - Lessons learned
```

### 2. Team Retrospective

**Agenda**:
- What went well?
- What could be improved?
- Were monitoring tools adequate?
- Any process gaps identified?
- Action items for next deployment

### 3. Update Documentation

- [ ] Update runbooks with new procedures
- [ ] Document any workarounds or fixes applied
- [ ] Update monitoring thresholds if needed
- [ ] Add new troubleshooting entries
- [ ] Update capacity planning estimates

### 4. Decommission Blue Environment

```bash
# Backup Blue configuration (just in case)
cd /opt/temponest-blue
docker compose config > blue-config-backup.yml

# Stop and remove Blue
docker compose -f docker-compose.prod.yml down -v

# Archive logs
tar -czf blue-logs-$(date +%Y%m%d).tar.gz logs/

# Free up resources
docker system prune -af
```

---

## Emergency Contacts

| Role | Name | Phone | Slack | Escalation |
|------|------|-------|-------|------------|
| **On-Call Primary** | [Name] | [Phone] | @username | Immediate |
| **On-Call Backup** | [Name] | [Phone] | @username | If no response in 15min |
| **Tech Lead** | [Name] | [Phone] | @username | Critical issues |
| **DevOps Lead** | [Name] | [Phone] | @username | Infrastructure issues |
| **DBA** | [Name] | [Phone] | @username | Database emergencies |

**Escalation Path**:
1. On-Call Primary (0-15 min)
2. On-Call Backup (15-30 min)
3. Tech Lead (30-45 min)
4. Engineering Manager (45+ min)

---

**Document Version**: 1.0
**Last Updated**: 2025-11-13
**Owner**: DevOps/SRE Team
**Next Review**: After deployment completion
