# Technology Stack

**Analysis Date:** 2026-03-04

## Languages

**Primary:**
- Python 3.11 - All backend services (agents, auth, scheduler, approval-ui, ingestion, temporal-workers, web-ui)
- TypeScript 5.6 - Frontend console app (`apps/console/`)

**Secondary:**
- JavaScript (Node.js 20) - Claude Code CLI execution within agents container
- SQL - PostgreSQL schema migrations via Alembic (`alembic/`)
- Bash - CLI tooling (`cli/agentic-cli.sh`, `cli/saas-builder.sh`, `START.sh`)

## Runtime

**Environment:**
- Python services: Python 3.11-slim (Debian-based Docker images)
- Console app: Node.js 20 Alpine (Docker multi-stage build)
- SDK: Python 3.8+ compatible (`sdk/pyproject.toml`)

**Package Manager:**
- Python: pip with requirements.txt files per service
- Node.js: npm with lockfile (`apps/console/package-lock.json`)
- Lockfile: present for npm; Python services use pinned version ranges

## Frameworks

**Backend Web:**
- FastAPI >= 0.115.0 - agents service (`services/agents/`), scheduler (`services/scheduler/`), approval-ui base
- FastAPI 0.109.0 - auth service (`services/auth/`), approval-ui (`services/approval_ui/`)
- Uvicorn - ASGI server for all FastAPI services
- Flask >= 3.0.0 - web-ui admin dashboard (`web-ui/requirements.txt`)

**Frontend:**
- Next.js 15 - Console app (`apps/console/`)
- React 19 RC - UI rendering
- Tailwind CSS 3.4 - Styling
- Radix UI - Headless component primitives (`@radix-ui/*`)
- shadcn/ui pattern (components.json present)

**Agent Framework:**
- CrewAI 0.203.1 - Multi-agent orchestration (`services/agents/requirements.txt`)
- LangChain 0.3.27 + langchain-community 0.3.31 - LLM tooling
- LangChain Core 0.3.79
- instructor 1.12.0 - Structured LLM outputs

**Workflow Orchestration:**
- Temporal 1.24.2 (server, Docker image `temporalio/auto-setup`)
- temporalio Python SDK 1.5.1 - workers and client (`services/temporal_workers/`, `services/approval_ui/`)

**Scheduling:**
- APScheduler >= 3.10.0 - in-process cron/interval scheduling (`services/scheduler/`)
- croniter >= 2.0.0 - cron expression parsing

**ORM / Database:**
- Prisma 5.20.0 - ORM for console app (`apps/console/prisma/schema.prisma`)
- asyncpg >= 0.29.0 - raw async PostgreSQL driver for Python services
- SQLAlchemy 2.0.25 - approval-ui ORM layer (`services/approval_ui/requirements.txt`)
- Alembic - Python migration tool (`alembic/`, `alembic.ini`)

**Testing:**
- pytest >= 8.3.0 - Python unit/integration tests (all services)
- pytest-asyncio - async test support
- pytest-mock - mocking
- pytest-cov - coverage
- Vitest 4.x - TypeScript unit tests (`apps/console/`)
- Playwright 1.56 - E2E tests for console app
- Testing Library (React) - component tests

**Build/Dev:**
- Docker Compose - local development orchestration (`docker/docker-compose.yml`)
- Next.js bundle analyzer - frontend bundle analysis
- tsx - TypeScript execution for Prisma seeds
- black, ruff, mypy - Python code quality (SDK `sdk/pyproject.toml`)
- ESLint 8 + eslint-config-next - TypeScript linting

## Key Dependencies

**Critical:**
- crewai 0.203.1 - Agent task decomposition and execution
- temporalio 1.5.1 - Durable workflow execution with retry semantics
- qdrant-client >= 1.11.0 - Vector similarity search for RAG
- chromadb 1.1.1 - Alternative vector store (agents service)
- litellm 1.74.9 - Unified LLM provider abstraction layer
- openai 1.109.1 - OpenAI API client (also used via litellm)
- langfuse >= 2.50.0 - LLM observability and tracing
- better-auth 1.3.34 - Authentication library for console app
- Prisma 5.20.0 - Type-safe database client for console

**Infrastructure:**
- redis[hiredis] >= 5.0.0 - Caching and rate limiting
- asyncpg >= 0.29.0 - PostgreSQL async driver
- slowapi >= 0.1.9 - FastAPI rate limiting
- prometheus-client >= 0.20.0 - Metrics exposition
- PyJWT >= 2.8.0 - JWT token handling
- python-jose[cryptography] 3.3.0 - JWT + cryptography (auth service)
- bcrypt 4.1.2 - Password hashing (auth service)
- httpx >= 0.27.0 - Async HTTP client (inter-service calls)
- pydantic >= 2.9.0 + pydantic-settings - Settings validation
- tenacity >= 8.2.0 - Retry logic
- tiktoken >= 0.7.0 - Token counting
- onnxruntime 1.23.2 - Required by chromadb (must install before)
- ollama >= 0.3.0 - Local LLM Python client
- reactflow 11.11.4 - Workflow visualization in console
- recharts 2.12.7 - Charts in console
- dnd-kit - Drag-and-drop in console
- zod 3.23 - Schema validation (frontend)
- react-hook-form 7.66 - Form handling (frontend)
- date-fns 3.6 - Date utilities (frontend)

**Document Processing (ingestion service):**
- pypdf 3.17.4 - PDF parsing
- python-docx 1.1.0 - DOCX parsing
- markdown 3.5.1 - Markdown parsing
- watchdog 3.0.0 - File system monitoring

**Telemetry (shared):**
- opentelemetry-api/sdk >= 1.20.0 - Tracing instrumentation
- opentelemetry-exporter-otlp-proto-grpc - OTLP export
- opentelemetry-instrumentation-fastapi/asyncpg/redis/httpx

## Configuration

**Environment:**
- Primary config: `docker/.env.example` (copy to `docker/.env` for local dev)
- Console app: `apps/console/.env.example` (copy to `apps/console/.env.local`)
- Services load config via `pydantic-settings` / `python-dotenv`
- All sensitive values via environment variables; no hardcoded secrets in code

**Key config required:**
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `JWT_SECRET_KEY` - must be identical across auth, agents, scheduler, approval-ui
- `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`
- LLM provider tokens: `CLAUDE_SESSION_TOKEN` / `OPENAI_API_KEY` / or Ollama (local, no key)
- `TELEGRAM_BOT_TOKEN` (optional, for Telegram approval notifications)
- `DATABASE_URL` - console app Prisma connection
- `BETTER_AUTH_SECRET` - console app auth

**Build:**
- `apps/console/tsconfig.json` - TypeScript with `@/*` path alias
- `docker/docker-compose.yml` - primary compose
- `docker/docker-compose.dev.yml` - dev overrides
- `docker/docker-compose.prod.yml` - production overrides
- `docker/docker-compose.telemetry.yml` - optional OpenTelemetry stack (Jaeger/Tempo)
- `infra/k8s/` - Kubernetes manifests (Kustomize)

## Platform Requirements

**Development:**
- Docker + Docker Compose (all services run in containers)
- For local Python work: Python 3.11+
- For console local dev: Node.js 20+, npm

**Production:**
- Docker Compose (current primary deployment)
- Kubernetes supported via `infra/k8s/` Kustomize manifests with Traefik ingress
- Cloudflare config present in `infra/cloudflare/`
- Coolify deployment supported (env var `COOLIFY_API_URL` in console)

---

*Stack analysis: 2026-03-04*
