# Database Performance Benchmarking

Comprehensive database performance testing suite for TempoNest PostgreSQL database.

## Overview

This suite tests various aspects of database performance:

1. **Simple Queries**: Basic SELECT, COUNT, and health check queries
2. **Indexed Queries**: Queries that utilize database indexes
3. **JOIN Queries**: Multi-table JOINs with various complexities
4. **Aggregations**: GROUP BY and aggregation functions
5. **Concurrent Load**: Connection pool and concurrent query handling

## Prerequisites

```bash
# Install dependencies
pip install -r tests/performance/database/requirements.txt

# Ensure PostgreSQL is running
docker ps | grep agentic-postgres

# Verify database connection
psql postgresql://postgres:postgres@localhost:5434/agentic -c "SELECT 1"
```

## Running Benchmarks

### Basic Usage

```bash
# Run all benchmarks with default settings
python tests/performance/database/benchmark.py

# Run with verbose output
python tests/performance/database/benchmark.py --verbose

# Specify custom connection string
python tests/performance/database/benchmark.py \
  --connection postgresql://user:pass@localhost:5434/dbname

# Save results to custom location
python tests/performance/database/benchmark.py \
  --output tests/performance/reports/db-results-$(date +%Y%m%d).json
```

### Example Output

```
================================================================================
TempoNest Database Performance Benchmark
================================================================================

Connection: localhost:5434/agentic
Verbose: True
Output: tests/performance/reports/db-benchmark.json

=== Simple Query Benchmarks ===

Running: Health Check Query
  Query: SELECT 1
  Iterations: 1000
  Progress: 100/1000
  Progress: 200/1000
  ...
  ✓ Completed in 0.85s
  Avg: 0.83ms, P95: 1.20ms

================================================================================
BENCHMARK SUMMARY
================================================================================

Total Tests: 15
Timestamp: 2025-11-12 15:30:45

Test Name                                         Avg (ms)   P95 (ms)        QPS
--------------------------------------------------------------------------------
Health Check Query                                    0.83       1.20     1176.5
Timestamp Query                                       0.91       1.35     1098.9
Count Query (Agents)                                  2.45       3.80      408.2
Count Query (Schedules)                               2.12       3.45      471.7
Query by ID (Primary Key)                             1.23       2.10      813.0
Query by Tenant ID (Index)                            3.45       5.67      289.9
Query by Created At (Index)                           4.12       6.89      242.7
Simple JOIN (Schedules + Agents)                      5.67       8.90      176.4
JOIN with Filter                                      4.89       7.65      204.5
Count by Tenant                                       12.34      18.90       81.0
Complex Aggregation                                   18.90      28.45       52.9
Concurrent Light Load (10 workers)                    2.34       4.50      854.7
Concurrent Medium Load (50 workers)                   8.90      15.67      561.8
Concurrent Heavy Load (100 workers)                  25.67      45.89      389.1
--------------------------------------------------------------------------------

Overall Average Response Time: 6.85ms
Overall Average Throughput: 487.4 qps
Total Queries Executed: 15,500
Total Errors: 0

✓ Results saved to: tests/performance/reports/db-benchmark.json
```

## Understanding Results

### Key Metrics

1. **Avg (ms)**: Average query response time
   - **Target**: < 10ms for simple queries, < 50ms for complex queries
   - **Good**: < 5ms, **Acceptable**: 5-20ms, **Review**: > 20ms

2. **P95 (ms)**: 95th percentile response time
   - 95% of queries complete faster than this
   - **Target**: < 2x average time

3. **QPS (Queries Per Second)**: Throughput
   - Higher is better
   - **Good**: > 500 qps, **Acceptable**: 100-500 qps, **Review**: < 100 qps

### Performance Targets

| Query Type | Avg Target | P95 Target | QPS Target |
|------------|------------|------------|------------|
| Simple SELECT | < 2ms | < 5ms | > 1000 |
| Indexed Lookup | < 5ms | < 10ms | > 500 |
| JOIN Queries | < 10ms | < 20ms | > 200 |
| Aggregations | < 20ms | < 40ms | > 100 |
| Concurrent (100) | < 30ms | < 60ms | > 300 |

### Common Issues

#### Slow Simple Queries (> 5ms avg)

Possible causes:
- Network latency to database
- Database under heavy load
- Insufficient database resources (CPU/Memory)
- Connection pool exhaustion

Solutions:
```bash
# Check database load
docker stats agentic-postgres

# Check connection pool settings
psql -c "SHOW max_connections"
psql -c "SELECT count(*) FROM pg_stat_activity"

# Check slow queries
psql -c "SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10"
```

#### High P95 Times (> 3x avg)

Indicates variability in performance. Possible causes:
- Garbage collection pauses
- Cache misses
- Lock contention
- Resource competition

Solutions:
```sql
-- Check for blocking queries
SELECT * FROM pg_stat_activity WHERE wait_event_type IS NOT NULL;

-- Check for lock contention
SELECT * FROM pg_locks WHERE NOT granted;

-- Analyze table statistics
ANALYZE agents;
ANALYZE schedules;
```

#### Low Throughput (< 100 qps)

Possible causes:
- Connection pool too small
- Slow queries blocking pool
- Database configuration issues

Solutions:
```python
# Increase pool size in benchmark.py
self.pool = await asyncpg.create_pool(
    self.connection_string,
    min_size=20,  # Increase from 10
    max_size=50,  # Increase from 20
)
```

```sql
-- Check database configuration
SHOW shared_buffers;
SHOW work_mem;
SHOW effective_cache_size;
```

## Database Optimization

### Index Analysis

Check if queries are using indexes:

```sql
-- Enable query plan logging
SET log_statement = 'all';
SET log_min_duration_statement = 0;

-- Analyze a specific query
EXPLAIN ANALYZE SELECT * FROM agents WHERE tenant_id = 'test-tenant';

-- Check index usage
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### Missing Indexes

If queries are slow, check for missing indexes:

```sql
-- Find tables with sequential scans
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / seq_scan as avg_seq_tup
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC;

-- Create missing indexes
CREATE INDEX idx_agents_tenant_created ON agents(tenant_id, created_at);
CREATE INDEX idx_schedules_active ON schedules(is_active) WHERE is_active = true;
```

### Connection Pool Tuning

Optimize PostgreSQL for connection pooling:

```sql
-- Increase max connections
ALTER SYSTEM SET max_connections = 200;

-- Tune memory per connection
ALTER SYSTEM SET work_mem = '16MB';

-- Reload configuration
SELECT pg_reload_conf();
```

### Query Optimization

For slow queries:

```sql
-- Update statistics
ANALYZE;

-- Vacuum tables
VACUUM ANALYZE agents;
VACUUM ANALYZE schedules;

-- Check table bloat
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as external_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Continuous Monitoring

### Integration with Grafana

The database metrics can be exported to Prometheus/Grafana:

```bash
# Run benchmark and export to JSON
python tests/performance/database/benchmark.py --output /tmp/db-metrics.json

# Parse and push to Prometheus (using node exporter textfile collector)
cat /tmp/db-metrics.json | jq '.results[] | "db_query_time{test=\"\(.test_name)\"} \(.avg_time)"' > /var/lib/node_exporter/textfile_collector/db_metrics.prom
```

### Automated Testing

Add to CI/CD pipeline:

```yaml
# .github/workflows/performance.yml
performance_test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Start database
      run: docker-compose up -d agentic-postgres
    - name: Install dependencies
      run: pip install -r tests/performance/database/requirements.txt
    - name: Run database benchmarks
      run: python tests/performance/database/benchmark.py --output db-results.json
    - name: Check performance thresholds
      run: |
        python scripts/check_db_performance.py db-results.json
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: db-performance-results
        path: db-results.json
```

## Troubleshooting

### Connection Errors

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs agentic-postgres

# Test connection manually
psql postgresql://postgres:postgres@localhost:5434/agentic -c "SELECT 1"
```

### Permission Errors

```sql
-- Grant necessary permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_user;
GRANT SELECT ON pg_stat_statements TO your_user;
```

### Benchmark Fails to Complete

```bash
# Increase query timeout
python tests/performance/database/benchmark.py --timeout 120

# Run individual test suites
python -c "
import asyncio
from tests.performance.database.benchmark import DatabaseBenchmark

async def run():
    b = DatabaseBenchmark('postgresql://postgres:postgres@localhost:5434/agentic', verbose=True)
    await b.setup()
    await b.benchmark_simple_queries()  # Run only simple queries
    await b.cleanup()

asyncio.run(run())
"
```

## Resources

- [PostgreSQL Performance Tips](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [Database Indexing Best Practices](https://use-the-index-luke.com/)
- [TempoNest Performance Guide](../../PERFORMANCE.md)
