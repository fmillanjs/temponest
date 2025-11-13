# Database Migrations with Alembic

This directory contains the Alembic migration framework for TempoNest database schema management.

## Prerequisites

```bash
pip install alembic asyncpg
```

## Environment Variables

Set the database connection URL:

```bash
export ALEMBIC_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/agentic"
# Or use DATABASE_URL
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/agentic"
```

## Common Commands

### Create a new migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of changes"

# Create empty migration (for manual SQL)
alembic revision -m "description of changes"
```

### Apply migrations

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade by 1 version
alembic upgrade +1

# Upgrade to specific revision
alembic upgrade <revision>
```

### Rollback migrations

```bash
# Downgrade by 1 version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision>

# Downgrade to base (removes all migrations)
alembic downgrade base
```

### View migration history

```bash
# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Migration Best Practices

1. **Always test migrations** in development before production
2. **Create backups** before running migrations in production
3. **Write both upgrade and downgrade** functions
4. **Keep migrations small** and focused on one change
5. **Test rollback** functionality to ensure it works

## Converting Existing SQL Migrations

The existing SQL migrations in `docker/migrations/` have been numbered sequentially. To migrate to Alembic:

1. Create baseline migration:
   ```bash
   alembic revision -m "baseline schema"
   ```

2. Copy SQL from existing migration files into the `upgrade()` function

3. Write corresponding `downgrade()` SQL to reverse changes

4. Mark as applied without running:
   ```bash
   alembic stamp head
   ```

## Docker Integration

To run migrations in Docker:

```bash
# Connect to database container
docker compose exec postgres bash

# Inside container, run migrations
cd /app
alembic upgrade head
```

Or create a migration service in docker-compose.yml:

```yaml
migrations:
  build: ./services/migrations
  environment:
    - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/agentic
  depends_on:
    - postgres
  command: alembic upgrade head
```

## Rollback Strategy

If a migration fails:

1. **Check the error** in logs
2. **Rollback** to previous version: `alembic downgrade -1`
3. **Fix the migration** file
4. **Re-run** the migration

## Current Migration Status

Run `alembic current` to see which migrations have been applied.
