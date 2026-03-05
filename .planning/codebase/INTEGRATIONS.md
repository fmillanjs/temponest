# External Integrations

**Analysis Date:** 2026-03-04

## LLM Providers

**Anthropic Claude (REST API):**
- Used for: Overseer and Developer agents when `OVERSEER_PROVIDER=claude` or `DEVELOPER_PROVIDER=claude`
- SDK/Client: `openai` 1.109.1 / direct httpx calls (`services/agents/app/llm/claude_client.py`)
- Auth: `CLAUDE_SESSION_TOKEN` env var (session token or `sk-ant-` API key)
- Endpoint: `CLAUDE_API_URL` (default `https://api.anthropic.com/v1/messages`)
- Models: `CLAUDE_CHAT_MODEL` / `CLAUDE_CODE_MODEL` (default `claude-sonnet-4-20250514`)
- Also supports URL-based auth: `CLAUDE_AUTH_URL` env var

**Anthropic Claude Code CLI:**
- Used for: Developer agent when `DEVELOPER_PROVIDER=claude-code`
- SDK/Client: `@anthropic-ai/claude-code` npm package (installed globally in agents container)
- Auth: `CLAUDE_CODE_ACCESS_TOKEN` + `CLAUDE_CODE_REFRESH_TOKEN` (OAuth, stored in `~/.claude/.credentials.json`)
- Implementation: `services/agents/app/llm/claude_code_client.py`
- Node.js 20 runtime installed in agents Docker image for CLI execution

**OpenAI:**
- Used for: Overseer and Developer agents when `OVERSEER_PROVIDER=openai` or `DEVELOPER_PROVIDER=openai`
- SDK/Client: `openai` 1.109.1 / `litellm` 1.74.9
- Auth: `OPENAI_API_KEY` env var
- Endpoint: `OPENAI_BASE_URL` (default `https://api.openai.com/v1`)
- Models: `OPENAI_CHAT_MODEL` / `OPENAI_CODE_MODEL` (default `gpt-4-turbo-preview`)

**Ollama (Local LLM):**
- Used for: Default LLM provider for all agents; also embeddings
- SDK/Client: `ollama` Python package >= 0.3.0
- Auth: None (local service)
- Endpoint: `OLLAMA_BASE_URL` (default `http://ollama:11434`)
- Chat model: `OLLAMA_CHAT_MODEL` (default `mistral:7b-instruct`)
- Code model: `OLLAMA_CODE_MODEL` (default `qwen2.5-coder:7b`)
- Embedding model: `EMBEDDING_MODEL` (default `nomic-embed-text`)
- Docker image: `ollama/ollama:latest` (port 11434)

**LiteLLM:**
- Used for: Unified LLM abstraction layer across providers
- SDK/Client: `litellm` 1.74.9
- Implementation: `services/agents/app/llm/unified_client.py`

## Data Storage

**PostgreSQL 16:**
- Used by: All services (shared instance via Docker)
- Docker image: `postgres:16-alpine` (port 5434 external, 5432 internal)
- Connection env: `DATABASE_URL` (per service, with different DB names: `agentic`, `langfuse`, `approvals`)
- Client: `asyncpg` for Python services; Prisma for console app; SQLAlchemy in approval-ui
- Schemas: managed by Alembic (`alembic/`) for Python services; Prisma for console
- Console schema: `apps/console/prisma/schema.prisma` — models: Project, Run, Agent, Approval, User, Account, Session, VerificationToken, AuditLog

**Qdrant (Vector Database):**
- Used by: ingestion service (write), agents service (read/write for RAG)
- Docker image: `qdrant/qdrant:v1.12.0` (port 6333 HTTP, 6334 gRPC)
- SDK/Client: `qdrant-client` >= 1.11.0 (agents), 1.9.2 (ingestion)
- Connection env: `QDRANT_URL` (default `http://qdrant:6333`)
- Purpose: Vector similarity search for RAG knowledge base; embeddings stored by ingestion service

**Redis 7:**
- Used by: auth service, agents service (caching + rate limiting)
- Docker image: `redis:7-alpine` (port 6379)
- SDK/Client: `redis[hiredis]` >= 5.0.0
- Connection env: `REDIS_URL` (default `redis://redis:6379/0`)
- Purpose: Session caching, rate limit counters

**ChromaDB:**
- Used by: agents service (alternative in-process vector store)
- SDK/Client: `chromadb` 1.1.1
- Note: Requires `onnxruntime` 1.23.2 installed first

**File Storage:**
- Local filesystem only — documents watched at `WATCH_DIR=/data/documents` by ingestion service
- No cloud object storage (S3/GCS) detected

**Caching:**
- Redis (see above)

## LLM Observability

**Langfuse:**
- Used for: LLM call tracing, RAG citation tracking, cost monitoring
- Docker image: `langfuse/langfuse:2` (port 3001 external)
- SDK/Client: `langfuse` >= 2.50.0 Python SDK
- Auth: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` env vars
- Internal host: `LANGFUSE_HOST=http://langfuse:3000`
- Implementation: `services/agents/app/memory/langfuse_tracer.py`
- Config: `LANGFUSE_TRACE_ALL`, `LANGFUSE_TRACE_RAG_CITATIONS`
- Console app also integrates: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` env vars

## Workflow Automation

**n8n:**
- Used for: Approval notification workflows, Telegram bot integration
- Docker image: `n8nio/n8n:latest` (port 5678)
- Auth: Basic auth via `N8N_USER` / `N8N_PASSWORD` env vars
- Webhook endpoint: `N8N_WEBHOOK_URL` (default `http://n8n:5678/webhook/approval`)
- Workflow file: `services/n8n/telegram-approval-workflow.json`
- Called from: `services/temporal_workers/activities.py` (`send_telegram_notification` activity)

**Temporal:**
- Used for: Durable workflow orchestration with retries and human-in-the-loop approval waits
- Docker image: `temporalio/auto-setup:1.24.2` (port 7233 gRPC, 8080 UI)
- SDK/Client: `temporalio` 1.5.1 (workers: `services/temporal_workers/`, client: `services/approval_ui/`)
- Connection env: `TEMPORAL_HOST` (default `temporal:7233`), `TEMPORAL_NAMESPACE`
- Workers: `services/temporal_workers/worker.py`, workflows in `services/temporal_workers/workflows.py`

## Messaging / Notifications

**Telegram Bot:**
- Used for: Human approval notifications
- Auth: `TELEGRAM_BOT_TOKEN` env var
- Integration: routed through n8n webhook; n8n sends Telegram messages
- Feature flag: `ENABLE_TELEGRAM_APPROVALS`

## Authentication & Identity

**Custom Auth Service (JWT):**
- Implementation: `services/auth/` — FastAPI service on port 9002
- Approach: JWT access + refresh tokens; bcrypt password hashing
- Client: `python-jose[cryptography]` 3.3.0, `bcrypt` 4.1.2
- JWT secret: `JWT_SECRET_KEY` env var (must match across all services)
- Other services validate JWTs using shared `JWT_SECRET_KEY`
- Token lifetimes: `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` (default 60), `JWT_REFRESH_TOKEN_EXPIRE_DAYS` (default 30)

**Better Auth (Console App):**
- Used by: `apps/console/` Next.js app
- SDK/Client: `better-auth` 1.3.34
- Auth: `BETTER_AUTH_SECRET` + `AUTH_SECRET` env vars
- Database: Prisma models — User, Account, Session, VerificationToken in `apps/console/prisma/schema.prisma`
- Optional GitHub OAuth: `GITHUB_TOKEN` env var

## Monitoring & Observability

**Prometheus:**
- Docker image: `prom/prometheus:latest` (port 9091 external)
- Config: `infra/prometheus/prometheus.yml`, alerts in `infra/prometheus/alerts/`
- Python services expose metrics via `prometheus-client` >= 0.20.0
- Retention: 30 days

**Grafana:**
- Docker image: `grafana/grafana:latest` (port 3003 external)
- Dashboards: `infra/grafana/dashboards/`, `infra/grafana/provisioning/`
- Auth: `GRAFANA_ADMIN_USER` / `GRAFANA_ADMIN_PASSWORD` env vars

**AlertManager:**
- Docker image: `prom/alertmanager:latest` (port 9093)
- Config: `infra/alertmanager/alertmanager.yml`
- Routing: email (configurable), grouped by alertname/service/tenant_id

**OpenTelemetry (optional stack):**
- Activated via: `docker/docker-compose.telemetry.yml`
- Jaeger: `jaegertracing/all-in-one:1.51` (UI port 16686, OTLP gRPC 4317)
- Grafana Tempo: lightweight tracing alternative
- Instrumentation: `shared/requirements-telemetry.txt` — FastAPI, asyncpg, Redis, httpx auto-instrumentation
- Exporter: `opentelemetry-exporter-otlp-proto-grpc`

**Open WebUI:**
- Docker image: `ghcr.io/open-webui/open-webui:main` (port 8081)
- Purpose: Chat interface for direct interaction with Ollama models
- Auth: `WEBUI_SECRET_KEY` env var

## CI/CD & Deployment

**Hosting:**
- Primary: Docker Compose (self-hosted)
- Kubernetes: `infra/k8s/` — Kustomize manifests, Traefik ingress (`infra/k8s/traefik-values.yaml`), HPA autoscaling
- Coolify PaaS: env vars `COOLIFY_API_URL`, `COOLIFY_API_TOKEN` in console app

**CI Pipeline:**
- `codecov.yml` present — Codecov integration for coverage reporting
- No CI pipeline YAML (GitHub Actions, etc.) detected in root

## Webhooks & Callbacks

**Incoming:**
- `services/agents/app/routers/webhooks.py` - webhook receiver endpoint in agents service
- n8n triggers agents via HTTP

**Outgoing:**
- Agents → n8n: `POST {N8N_WEBHOOK_URL}` for approval notifications
- Temporal Workers → Agents: `POST http://agents:9000/overseer/run`, `POST http://agents:9000/developer/run`
- Temporal Workers → Approval UI: `http://approval-ui:9001`
- Web UI → Prometheus: `PROMETHEUS_URL=http://agentic-prometheus:9090`
- Console App → GitHub: optional via `GITHUB_TOKEN`
- Console App → Coolify: optional via `COOLIFY_API_URL` + `COOLIFY_API_TOKEN`

## Environment Configuration

**Required env vars (docker/.env):**
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `JWT_SECRET_KEY` (shared across services — must be identical)
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_NEXTAUTH_SECRET`, `LANGFUSE_SALT`
- `TELEGRAM_BOT_TOKEN` (if Telegram approvals enabled)
- LLM: `CLAUDE_SESSION_TOKEN` or `OPENAI_API_KEY` (if not using Ollama)
- Claude Code: `CLAUDE_CODE_ACCESS_TOKEN`, `CLAUDE_CODE_REFRESH_TOKEN` (if provider=claude-code)

**Required env vars (apps/console/.env.local):**
- `DATABASE_URL` - PostgreSQL connection string
- `BETTER_AUTH_SECRET`, `AUTH_SECRET`
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` (optional)
- `GITHUB_TOKEN` (optional)
- `COOLIFY_API_URL`, `COOLIFY_API_TOKEN` (optional)

**Secrets location:**
- Local dev: `docker/.env` (gitignored)
- Kubernetes: `infra/k8s/secrets.example.yaml` (template only; actual secrets external)

---

*Integration audit: 2026-03-04*
