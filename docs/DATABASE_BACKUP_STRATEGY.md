# Database Backup Strategy for TempoNest

## Overview

This document outlines the database backup strategy for TempoNest's PostgreSQL databases to prevent data loss and enable disaster recovery.

## Databases to Backup

TempoNest uses multiple PostgreSQL databases:

1. **agentic** - Main application database (agents, workflows, tasks)
2. **approvals** - Approval requests and audit logs
3. **langfuse** - LLM tracing and observability data
4. **temporal** - Temporal workflow state
5. **saas_console** - Next.js console application data

## Backup Strategy

### Automated Backups

#### 1. Daily Full Backups

**Schedule**: Daily at 2:00 AM UTC

**Retention**:
- Daily backups: Keep for 7 days
- Weekly backups: Keep Sunday backups for 4 weeks
- Monthly backups: Keep first Sunday backup for 12 months

**Implementation**:

```bash
#!/bin/bash
# /infra/scripts/backup-databases.sh

set -e

BACKUP_DIR="/backups/postgresql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

mkdir -p ${BACKUP_DIR}

# Backup each database
for DB in agentic approvals langfuse temporal saas_console; do
    echo "Backing up database: ${DB}"

    pg_dump \
        -h postgres \
        -U postgres \
        -d ${DB} \
        -F c \
        -f "${BACKUP_DIR}/${DB}_${TIMESTAMP}.dump"

    # Compress backup
    gzip "${BACKUP_DIR}/${DB}_${TIMESTAMP}.dump"

    echo "✓ Backup completed: ${DB}_${TIMESTAMP}.dump.gz"
done

# Remove backups older than retention period
find ${BACKUP_DIR} -name "*.dump.gz" -mtime +${RETENTION_DAYS} -delete

echo "✓ All databases backed up successfully"
```

#### 2. Continuous WAL Archiving

Enable PostgreSQL Write-Ahead Log (WAL) archiving for point-in-time recovery.

**PostgreSQL Configuration** (`docker/postgres-backup.conf`):

```ini
# Write-Ahead Log (WAL) Settings
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /backups/wal_archive/%f && cp %p /backups/wal_archive/%f'
archive_timeout = 300  # Archive every 5 minutes

# Checkpoint settings
checkpoint_timeout = 5min
max_wal_size = 1GB
min_wal_size = 80MB
```

### Backup Storage

#### Local Storage (Development)

- **Location**: `./backups/` directory
- **Mount**: Docker volume `backup-data`

#### Remote Storage (Production)

**Option 1: AWS S3**

```bash
# Upload to S3 after backup
aws s3 sync /backups/postgresql s3://temponest-backups/postgres/ \
    --exclude "*" \
    --include "*.dump.gz" \
    --storage-class STANDARD_IA

# Upload WAL archives
aws s3 sync /backups/wal_archive s3://temponest-backups/wal/ \
    --storage-class GLACIER_IR
```

**Option 2: Azure Blob Storage**

```bash
az storage blob upload-batch \
    --account-name temponest \
    --destination backups \
    --source /backups/postgresql \
    --pattern "*.dump.gz"
```

**Option 3: Google Cloud Storage**

```bash
gsutil -m rsync -r /backups/postgresql gs://temponest-backups/postgres/
```

## Docker Compose Integration

Add backup service to `docker-compose.yml`:

```yaml
services:
  postgres-backup:
    image: postgres:16-alpine
    environment:
      - PGPASSWORD=postgres
    volumes:
      - ./backups:/backups
      - ./infra/scripts/backup-databases.sh:/backup.sh:ro
    depends_on:
      - postgres
    command: >
      sh -c "
        while true; do
          echo 'Running scheduled backup...'
          /backup.sh
          echo 'Backup complete. Sleeping for 24 hours...'
          sleep 86400
        done
      "
    restart: unless-stopped
```

## Restoration Procedures

### Full Database Restore

```bash
# Stop all services
docker compose down

# Restore database from dump
pg_restore \
    -h postgres \
    -U postgres \
    -d agentic \
    --clean \
    --if-exists \
    /backups/postgresql/agentic_20250113_020000.dump.gz

# Restart services
docker compose up -d
```

### Point-in-Time Recovery (PITR)

```bash
# 1. Restore base backup
pg_restore -d agentic /backups/postgresql/agentic_base.dump.gz

# 2. Configure recovery
cat > /var/lib/postgresql/data/recovery.conf <<EOF
restore_command = 'cp /backups/wal_archive/%f %p'
recovery_target_time = '2025-01-13 14:30:00'
recovery_target_action = 'promote'
EOF

# 3. Start PostgreSQL (it will replay WAL logs)
docker compose start postgres

# 4. Verify recovery
psql -U postgres -d agentic -c "SELECT NOW();"
```

## Backup Verification

### Automated Verification

Add to backup script:

```bash
# Verify backup integrity
pg_restore --list ${BACKUP_DIR}/${DB}_${TIMESTAMP}.dump.gz > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Backup verification successful"
else
    echo "✗ Backup verification failed!"
    # Send alert
    curl -X POST https://alerts.example.com/webhook \
        -d "Backup verification failed for ${DB}"
fi
```

### Manual Testing

Periodically (monthly) test full restoration:

```bash
# Create test database
createdb -U postgres agentic_test

# Restore from backup
pg_restore \
    -U postgres \
    -d agentic_test \
    /backups/postgresql/agentic_latest.dump.gz

# Verify data
psql -U postgres -d agentic_test -c "
    SELECT COUNT(*) FROM agents;
    SELECT COUNT(*) FROM workflows;
"

# Cleanup
dropdb -U postgres agentic_test
```

## Monitoring and Alerting

### Backup Monitoring

Monitor backup success/failure:

```yaml
# Prometheus metrics
backup_last_success_timestamp{database="agentic"}
backup_duration_seconds{database="agentic"}
backup_size_bytes{database="agentic"}
```

### Alerts

Configure alerts for:

1. **Backup Failure**: No successful backup in 25 hours
2. **Backup Size Anomaly**: Backup size changes >50%
3. **Storage Space**: Backup volume >80% full
4. **WAL Archive Lag**: WAL archive delay >15 minutes

Example Prometheus alert:

```yaml
groups:
  - name: database_backups
    rules:
      - alert: DatabaseBackupFailed
        expr: time() - backup_last_success_timestamp > 90000
        labels:
          severity: critical
        annotations:
          summary: "Database backup has not succeeded in 25+ hours"
```

## Security Considerations

1. **Encryption at Rest**: Encrypt backups before storage
   ```bash
   # Encrypt with GPG
   gpg --encrypt --recipient backups@temponest.com backup.dump.gz
   ```

2. **Access Control**: Restrict backup access to admin only

3. **Backup Credentials**: Store in secrets manager (not in code)

4. **Audit Logging**: Log all backup and restore operations

## Disaster Recovery Plan

### RTO and RPO

- **Recovery Time Objective (RTO)**: < 1 hour
- **Recovery Point Objective (RPO)**: < 15 minutes (with WAL archiving)

### Recovery Steps

1. Provision new infrastructure
2. Restore latest full backup
3. Apply WAL archives (if PITR needed)
4. Verify data integrity
5. Redirect traffic to new instance
6. Update DNS/load balancer

### Testing Schedule

- **Monthly**: Test single database restore
- **Quarterly**: Test full disaster recovery scenario
- **Annually**: Test cross-region failover

## Cost Optimization

1. Use lifecycle policies to move old backups to cheaper storage
2. Compress backups before upload
3. Deduplicate WAL archives
4. Delete test/development backups aggressively

## Implementation Checklist

- [ ] Create backup scripts in `/infra/scripts/`
- [ ] Add backup service to docker-compose
- [ ] Configure WAL archiving
- [ ] Set up remote storage (S3/Azure/GCS)
- [ ] Configure backup encryption
- [ ] Set up monitoring and alerts
- [ ] Document restoration procedures
- [ ] Test backup restoration
- [ ] Schedule regular DR drills
- [ ] Train team on recovery procedures

## References

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [pg_dump Reference](https://www.postgresql.org/docs/current/app-pgdump.html)
- [Point-in-Time Recovery](https://www.postgresql.org/docs/current/continuous-archiving.html)

---

**Last Updated**: 2025-01-13
**Owner**: DevOps Team
**Review Frequency**: Quarterly
