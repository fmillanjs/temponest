# Docker Services Guide

## Available Configurations

### 1. Simplified Stack (Recommended for Development)

**File:** `docker-compose.simple.yml`

**Includes:**
- ✅ PostgreSQL (port 5433)
- ✅ Redis (port 6380)
- ✅ MailHog (ports 1025, 8025)
- ✅ MinIO (ports 9000, 9001)

**Start:** `pnpm docker:dev` or `docker compose -f docker-compose.simple.yml up -d`

This is the **recommended** configuration for local development. All essential services work reliably.

---

### 2. Full Stack (Includes Analytics)

**File:** `docker-compose.dev.yml`

**Includes everything from Simplified Stack plus:**
- Plausible Analytics (port 8000)
- ClickHouse (analytics events database)
- PostgreSQL for Plausible

**Start:** `pnpm docker:dev:full` or `docker compose -f docker-compose.dev.yml up -d`

**Note:** ClickHouse can be resource-intensive and may have startup issues in WSL2 or resource-constrained environments. Use the simplified stack if you encounter problems.

---

## Service Details

### PostgreSQL (Main Database)
- **Port:** 5433 (to avoid conflicts)
- **User:** postgres
- **Password:** postgres
- **Database:** temponest
- **Connection:** `postgresql://postgres:postgres@localhost:5433/temponest`

**Access:**
```bash
psql postgresql://postgres:postgres@localhost:5433/temponest

# Or with Docker
docker exec -it temponest-postgres psql -U postgres -d temponest
```

---

### Redis (Cache & Job Queue)
- **Port:** 6380 (to avoid conflicts)
- **Password:** None (local dev only)
- **Connection:** `redis://localhost:6380`

**Access:**
```bash
redis-cli -p 6380

# Or with Docker
docker exec -it temponest-redis redis-cli
```

---

### MailHog (Email Testing)
- **SMTP Port:** 1025 (for sending emails)
- **Web UI:** http://localhost:8025
- **Use in dev:** Configure `RESEND_API_KEY` or use MailHog directly

**View Emails:** Open http://localhost:8025 in your browser

---

### MinIO (S3-Compatible Storage)
- **API Port:** 9000
- **Console Port:** 9001
- **Username:** minioadmin
- **Password:** minioadmin
- **Default Bucket:** temponest
- **Console:** http://localhost:9001

**Access:**
```bash
# Web Console
open http://localhost:9001

# Using AWS CLI
aws --endpoint-url http://localhost:9000 s3 ls s3://temponest
```

---

### Plausible Analytics (Optional - Full Stack Only)
- **Port:** 8000
- **Web UI:** http://localhost:8000
- **Note:** May take 30-60 seconds to fully start

---

## Common Commands

```bash
# Start services (simplified)
pnpm docker:dev

# Start services (full with analytics)
pnpm docker:dev:full

# Stop services
pnpm docker:dev:down

# View logs
docker compose -f docker-compose.simple.yml logs -f

# View specific service logs
docker logs temponest-postgres -f

# Check service status
docker compose -f docker-compose.simple.yml ps

# Clean everything (removes volumes!)
pnpm docker:dev:clean
```

---

## Troubleshooting

### Port Already in Use

If you see "port is already allocated" errors:

1. **Check what's using the port:**
   ```bash
   ss -tuln | grep <PORT>
   ```

2. **Stop the conflicting service or change ports in docker-compose file**

---

### ClickHouse Won't Start (Full Stack)

ClickHouse can be problematic in WSL2 or low-resource environments.

**Solutions:**
1. Use the simplified stack instead (`pnpm docker:dev`)
2. Increase Docker resources (Memory: 4GB+, CPU: 2+ cores)
3. Remove and recreate ClickHouse volume:
   ```bash
   docker compose -f docker-compose.dev.yml down
   docker volume rm temponest_plausible-events-data
   docker compose -f docker-compose.dev.yml up -d
   ```

---

### Database Connection Errors

Ensure PostgreSQL is healthy:
```bash
docker exec temponest-postgres pg_isready -U postgres
```

If unhealthy, check logs:
```bash
docker logs temponest-postgres
```

---

### Redis Connection Errors

Test Redis:
```bash
docker exec temponest-redis redis-cli ping
```

Should return `PONG`

---

## Health Checks

All services include health checks that Docker monitors:

```bash
# Check all health statuses
docker compose -f docker-compose.simple.yml ps

# Services should show (healthy) status
```

**Healthy services:**
- ✅ PostgreSQL - Ready to accept connections
- ✅ Redis - Responds to PING
- ✅ MinIO - API endpoint accessible

---

## Development Workflow

1. **Start services:** `pnpm docker:dev`
2. **Wait for health checks:** ~10 seconds
3. **Push database schema:**
   ```bash
   DATABASE_URL="postgresql://postgres:postgres@localhost:5433/temponest" npx prisma db push
   ```
4. **Start development servers:** `pnpm dev` (once apps are created)
5. **Access services:**
   - Database: Port 5433
   - Redis: Port 6380
   - MailHog: http://localhost:8025
   - MinIO: http://localhost:9001

---

## Production Considerations

**Never use these configurations in production!**

For production:
- Use managed services (RDS, ElastiCache, etc.) or Coolify deployments
- Set strong passwords
- Enable SSL/TLS
- Configure proper backups
- Set up monitoring and alerts
- Use environment-specific configurations

---

## Docker Resources

Monitor Docker resource usage:
```bash
docker stats
```

**Recommended minimums:**
- **Simplified Stack:** 2GB RAM, 2 CPU cores
- **Full Stack:** 4GB RAM, 4 CPU cores

---

## Quick Reference

| Service | Port | Health Check | Notes |
|---------|------|--------------|-------|
| PostgreSQL | 5433 | ✅ pg_isready | Main database |
| Redis | 6380 | ✅ PING | Cache & queues |
| MailHog SMTP | 1025 | N/A | Email delivery |
| MailHog UI | 8025 | N/A | Email inbox |
| MinIO API | 9000 | ✅ /health | S3 storage |
| MinIO Console | 9001 | N/A | Web UI |
| Plausible* | 8000 | ✅ HTTP | Analytics |

*Full stack only

---

**Need help?** Check the logs: `docker compose logs -f`
