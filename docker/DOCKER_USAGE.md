# Docker Compose Usage Guide

This directory contains separate Docker Compose configurations for development and production environments.

## Files

- **docker-compose.yml** - Original configuration (deprecated, use dev or prod instead)
- **docker-compose.dev.yml** - Development configuration with hot reload
- **docker-compose.prod.yml** - Production configuration optimized for deployment

## Development

For local development with hot reload:

```bash
cd docker
docker-compose -f docker-compose.dev.yml up -d
```

### Development Features:
- ✅ Source code volume mounts for hot reload
- ✅ `--reload` flag enabled for Python services
- ✅ `FLASK_DEBUG=1` for web-ui
- ✅ Lower resource limits (laptop-friendly)
- ✅ Development-friendly restart policy (`unless-stopped`)

### Making Changes:
When you edit code in:
- `services/agents/app/` → Agents service auto-reloads
- `services/auth/app/` → Auth service auto-reloads
- `services/scheduler/app/` → Scheduler service auto-reloads
- `web-ui/` → Web UI auto-reloads (Flask debug mode)

## Production

For production deployment:

```bash
cd docker
docker-compose -f docker-compose.prod.yml up -d
```

### Production Features:
- ✅ No source code volume mounts (code baked into images)
- ✅ No `--reload` flags (better performance)
- ✅ Production environment variables required
- ✅ Higher resource limits for performance
- ✅ `restart: always` policy
- ✅ 50-70% smaller images (Alpine + multi-stage builds)

### Production Requirements:
Set these environment variables before deploying:
```bash
# Required
export JWT_SECRET_KEY="your-long-random-secret-key"
export LANGFUSE_NEXTAUTH_SECRET="your-nextauth-secret"
export LANGFUSE_SALT="your-salt-secret"
export WEBUI_SECRET_KEY="your-webui-secret"
export APPROVAL_UI_SECRET_KEY="your-approval-secret"
export N8N_USER="your-n8n-username"
export N8N_PASSWORD="your-n8n-password"
export GRAFANA_ADMIN_USER="your-grafana-username"
export GRAFANA_ADMIN_PASSWORD="your-grafana-password"

# Optional (with defaults)
export POSTGRES_PASSWORD="postgres"
export LANGFUSE_NEXTAUTH_URL="https://your-domain.com/langfuse"
export N8N_HOST="your-domain.com"
export N8N_WEBHOOK_URL="https://your-domain.com/n8n"
export GRAFANA_ROOT_URL="https://your-domain.com/grafana"
export ALERTMANAGER_URL="https://your-domain.com/alertmanager"
```

## Building Images

### Development
Development mode uses the `runtime` target from multi-stage builds:
```bash
docker-compose -f docker-compose.dev.yml build
```

### Production
Production mode also uses the `runtime` target but without volume mounts:
```bash
docker-compose -f docker-compose.prod.yml build
```

## Optimization Benefits

### Multi-Stage Builds
- **Stage 1 (builder)**: Installs build dependencies, creates venv, installs packages
- **Stage 2 (runtime)**: Copies only venv and runtime dependencies
- **Result**: 30-50% smaller images

### Alpine Base Images
- Uses `python:3.11-alpine` instead of `python:3.11-slim`
- **Result**: 50-70% smaller than Debian-based images
- **Total size reduction**: ~400MB (from 1.58GB for agents service)

### Dev/Prod Separation
- **Development**: Fast iteration with hot reload
- **Production**: Optimized performance and security
- **Result**: Better developer experience + production reliability

## Monitoring

All configurations include monitoring stack:
- **Prometheus**: http://localhost:9091 - Metrics collection
- **Grafana**: http://localhost:3003 - Dashboards (default admin/admin in dev)
- **AlertManager**: http://localhost:9093 - Alert management

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| agents | 9000 | Agent execution service |
| approval-ui | 9001 | Human approval interface |
| auth | 9002 | Authentication service |
| scheduler | 9003 | Scheduled task execution |
| web-ui | 8082 | Admin dashboard |
| langfuse | 3001 | LLM observability |
| grafana | 3003 | Metrics visualization |
| postgres | 5434 | PostgreSQL database |
| redis | 6379 | Cache and rate limiting |
| qdrant | 6333 | Vector database |
| temporal | 7233, 8080 | Workflow engine |
| ollama | 11434 | LLM runtime |
| open-webui | 8081 | Chat interface |
| n8n | 5678 | Workflow automation |
| prometheus | 9091 | Metrics collection |
| alertmanager | 9093 | Alert routing |

## Health Checks

All services include health checks. Check status:

```bash
docker-compose -f docker-compose.dev.yml ps
```

## Logs

View logs for all services:
```bash
docker-compose -f docker-compose.dev.yml logs -f
```

View logs for specific service:
```bash
docker-compose -f docker-compose.dev.yml logs -f agents
```

## Cleanup

Stop and remove containers:
```bash
docker-compose -f docker-compose.dev.yml down
```

Stop and remove containers + volumes:
```bash
docker-compose -f docker-compose.dev.yml down -v
```

## Troubleshooting

### Services not starting
1. Check health status: `docker-compose ps`
2. View logs: `docker-compose logs <service-name>`
3. Verify environment variables are set
4. Ensure ports are not already in use

### Volume mount issues (dev only)
- Ensure source directories exist
- Check file permissions
- On Windows/Mac, ensure Docker Desktop has access to the directories

### Build failures
- Clear build cache: `docker-compose build --no-cache`
- Check Dockerfile syntax
- Verify all required files exist in context

## Migration from Old Setup

If you were using the original `docker-compose.yml`:

1. **For development**: Switch to `docker-compose.dev.yml`
   ```bash
   docker-compose down
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. **For production**: Use `docker-compose.prod.yml` and set required env vars
   ```bash
   docker-compose down
   # Set environment variables
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Performance Tips

### Development
- Use `docker-compose up -d` to run in background
- Rebuild only changed services: `docker-compose build <service-name>`
- Use `docker system prune` periodically to clean up

### Production
- Use `--scale` to run multiple instances of stateless services
- Configure reverse proxy (nginx/traefik) for SSL/TLS
- Set up log rotation for Docker logs
- Use Docker secrets instead of environment variables for sensitive data
- Consider using Docker Swarm or Kubernetes for orchestration
