# Codebase Structure

**Analysis Date:** 2026-03-04

## Directory Layout

```
temponest/                          # Monorepo root
├── apps/
│   └── console/                    # Next.js 14 management console
│       ├── app/                    # App Router pages & API routes
│       │   ├── (auth)/login/       # Auth group: login page
│       │   ├── (dashboard)/dashboard/ # Dashboard group: main dashboard
│       │   ├── agents/             # Agent monitoring page
│       │   ├── api/                # BFF API routes (Next.js Route Handlers)
│       │   │   ├── agents/health/  # Agent health endpoint
│       │   │   ├── auth/[...all]/  # BetterAuth catch-all route
│       │   │   ├── financials/     # Financials run/save endpoints
│       │   │   ├── git/summary/    # Git summary endpoint
│       │   │   ├── observability/  # Logs and metrics proxy endpoints
│       │   │   └── wizard/         # Wizard factory/single step streaming endpoints
│       │   ├── docs/               # Documentation viewer page
│       │   ├── factory-map/        # SaaS factory map page
│       │   ├── financials/         # Financial metrics page
│       │   ├── observability/      # Observability dashboard page
│       │   ├── projects/[slug]/    # Individual project detail page
│       │   ├── settings/           # Settings page
│       │   ├── wizards/            # Wizard UI pages
│       │   │   ├── factory/        # Factory wizard (multi-phase)
│       │   │   └── single/         # Single SaaS wizard
│       │   └── workflows/          # Workflow list page
│       ├── components/             # Shared React components
│       │   ├── ui/                 # Shadcn/ui primitive components
│       │   └── financials/         # Financial-specific components
│       ├── hooks/                  # React hooks
│       ├── lib/                    # Client/server utilities
│       │   ├── db/client.ts        # Prisma singleton client
│       │   ├── server/exec.ts      # Server-side process execution (streaming)
│       │   ├── auth.ts             # BetterAuth server config
│       │   ├── auth-client.ts      # BetterAuth client config
│       │   ├── api.ts              # HTTP client helpers
│       │   ├── permissions.ts      # Permission constants
│       │   ├── schemas.ts          # Zod validation schemas
│       │   └── utils.ts            # General utilities
│       ├── styles/                 # Global CSS
│       ├── prisma/schema.prisma    # Database schema (PostgreSQL via Prisma)
│       ├── e2e/                    # Playwright E2E tests
│       └── tests/                  # Vitest unit/integration tests
├── services/                       # Python microservices
│   ├── agents/                     # Core AI agent service (port 9000)
│   │   └── app/
│   │       ├── main.py             # FastAPI application entry point
│   │       ├── agents/             # Agent implementations
│   │       │   ├── factory.py      # AgentFactory: creates agents by provider
│   │       │   ├── overseer.py     # Overseer agent (goal decomposition)
│   │       │   ├── developer.py    # Developer agent v1 (CrewAI/Ollama)
│   │       │   ├── developer_v2.py # Developer agent v2 (Claude/OpenAI direct)
│   │       │   ├── qa_tester.py    # QA Tester agent
│   │       │   ├── devops.py       # DevOps agent
│   │       │   ├── designer.py     # Designer/UX agent
│   │       │   ├── security_auditor.py # Security Auditor agent
│   │       │   └── ux_researcher.py    # UX Researcher agent
│   │       ├── collaboration/      # Multi-agent collaboration manager
│   │       ├── cost/               # Cost calculator and tracker
│   │       ├── departments/        # Department/org structure manager
│   │       ├── llm/                # LLM provider abstractions
│   │       ├── memory/
│   │       │   ├── rag.py          # Qdrant RAG memory with Redis caching
│   │       │   └── langfuse_tracer.py # LLM execution tracer
│   │       ├── prompts/            # System prompt templates
│   │       ├── routers/            # FastAPI route modules
│   │       │   ├── health.py       # Health check router
│   │       │   ├── departments.py  # Departments router
│   │       │   ├── webhooks.py     # Webhook management router
│   │       │   └── collaboration.py # Collaboration router
│   │       ├── tools/              # Agent tool definitions
│   │       ├── webhooks/           # EventDispatcher + WebhookManager
│   │       ├── models.py           # AgentRequest / AgentResponse Pydantic models
│   │       ├── settings.py         # Pydantic settings (env vars)
│   │       ├── metrics.py          # Prometheus metrics definitions
│   │       ├── limiter.py          # slowapi rate limiter instance
│   │       └── utils.py            # Token counting, citation validation, cost recording
│   ├── auth/                       # Auth service (port 9002)
│   │   └── app/
│   │       ├── main.py             # FastAPI app entry point
│   │       ├── database.py         # asyncpg database manager
│   │       ├── models.py           # User/token Pydantic models
│   │       ├── settings.py         # Auth settings
│   │       ├── limiter.py          # Rate limiter
│   │       ├── routers/
│   │       │   ├── auth.py         # Login, register, token refresh routes
│   │       │   └── api_keys.py     # API key CRUD routes
│   │       ├── handlers/           # Business logic handlers
│   │       ├── middleware/         # JWT verification middleware
│   │       └── utils/              # JWT helpers
│   ├── approval_ui/                # Human approval UI (port 9001, Flask)
│   │   ├── templates/              # Jinja2 HTML templates
│   │   └── static/                 # CSS/JS assets
│   ├── scheduler/                  # Task scheduler service (port 9003)
│   │   └── app/
│   │       ├── main.py             # FastAPI app entry point
│   │       ├── scheduler.py        # APScheduler integration
│   │       ├── db.py               # Database manager
│   │       ├── models.py           # Schedule Pydantic models
│   │       ├── metrics.py          # Prometheus metrics
│   │       └── routers/schedules.py # Schedule CRUD routes
│   ├── temporal_workers/           # Temporal workflow worker
│   │   ├── worker.py               # Worker entry point; connects to Temporal
│   │   ├── workflows.py            # ProjectPipelineWorkflow, SimpleTaskWorkflow
│   │   └── activities.py           # Activity functions (HTTP calls to Agent/Approval UI)
│   ├── ingestion/                  # RAG document ingestion service
│   │   └── ingest.py               # File watcher + Ollama embeddings + Qdrant upsert
│   └── n8n/                        # n8n workflow automation config directory
├── shared/                         # Shared Python module (volume-mounted into all services)
│   ├── auth/                       # AuthClient, AuthContext, middleware, models
│   ├── redis/                      # RedisCache wrapper
│   ├── telemetry/                  # OpenTelemetry helpers
│   ├── logging_config.py           # Logging configuration
│   ├── exceptions.py               # Shared exception types
│   └── error_handlers.py           # Shared error handler utilities
├── sdk/                            # Python client SDK
│   ├── temponest_sdk/
│   │   ├── client.py               # Main SDK client
│   │   ├── agents.py               # Agent execution methods
│   │   ├── collaboration.py        # Collaboration methods
│   │   ├── costs.py                # Cost query methods
│   │   ├── rag.py                  # RAG search methods
│   │   ├── scheduler.py            # Schedule management methods
│   │   └── webhooks.py             # Webhook management methods
│   └── tests/                      # SDK tests (unit, integration, examples)
├── cli/                            # Command-line interface
│   └── temponest_cli/cli.py        # Click-based CLI
├── config/                         # Configuration files
│   └── departments/                # Department YAML config files
│       ├── marketing.yaml
│       ├── social_media.yaml
│       └── video_production.yaml
├── docker/                         # Docker Compose and runtime assets
│   ├── docker-compose.yml          # Main compose file (all services)
│   ├── docker-compose.dev.yml      # Dev overrides
│   ├── docker-compose.prod.yml     # Production overrides
│   ├── docker-compose.telemetry.yml # Telemetry stack compose
│   ├── init-db.sql                 # PostgreSQL initialization SQL
│   ├── migrations/                 # DB migration SQL files
│   ├── documents/                  # Drop documents here for RAG ingestion
│   └── agent-output/               # Agent output artifacts directory
├── infra/                          # Infrastructure configuration
│   ├── k8s/                        # Kubernetes manifests (00-namespace through 07-autoscaling)
│   ├── prometheus/                 # Prometheus config and alert rules
│   ├── grafana/                    # Grafana dashboards and provisioning
│   ├── alertmanager/               # AlertManager config
│   └── cloudflare/                 # Cloudflare Tunnel config
├── alembic/                        # Alembic DB migration runner
│   └── versions/                   # Migration version files
├── tests/                          # Cross-service integration/E2E/performance tests
│   ├── integration/                # Integration tests spanning services
│   ├── performance/                # k6 load tests, DB perf tests
│   ├── security/                   # Security-focused tests
│   ├── rag/                        # RAG pipeline tests
│   └── workflows/                  # Workflow integration tests
├── web-ui/                         # Legacy Flask admin dashboard
│   ├── app.py                      # Flask application
│   ├── templates/                  # Jinja2 templates (dashboard.html, visualization.html)
│   └── static/                     # CSS and JS assets
├── docs/                           # Documentation (Markdown)
├── examples/                       # Usage examples
├── tools/                          # Internal tooling scripts
├── scripts/deploy/                 # Deployment scripts
├── START.sh                        # Quick-start script
├── quick-demo.sh                   # Demo launch script
└── alembic.ini                     # Alembic configuration
```

## Directory Purposes

**`apps/console/`:**
- Purpose: Production-grade Next.js 14 management console for operators
- Contains: App Router pages, React components, BFF API routes, Prisma schema, Vitest tests, Playwright E2E tests
- Key files: `app/layout.tsx`, `prisma/schema.prisma`, `lib/db/client.ts`, `lib/auth.ts`, `middleware.ts`

**`services/agents/`:**
- Purpose: The core AI execution engine — runs all 7 specialized agents
- Contains: FastAPI app, agent implementations, RAG memory, cost tracker, webhook system
- Key files: `app/main.py`, `app/agents/factory.py`, `app/memory/rag.py`, `app/models.py`

**`services/auth/`:**
- Purpose: Central authentication and authorization service for the Python backend
- Contains: JWT issuance/validation, API key management, user registration
- Key files: `app/main.py`, `app/routers/auth.py`, `app/routers/api_keys.py`

**`services/temporal_workers/`:**
- Purpose: Connects to Temporal and runs durable multi-step agent workflows
- Contains: Worker setup, two workflow definitions, activity functions
- Key files: `worker.py`, `workflows.py`, `activities.py`

**`services/approval_ui/`:**
- Purpose: Flask web app for human approvers to review and approve/deny agent actions
- Contains: Approval display pages, Temporal signal sending
- Key files: Main app Python file, `templates/`, `static/`

**`services/scheduler/`:**
- Purpose: Scheduled execution of agent tasks (cron/interval triggers)
- Key files: `app/main.py`, `app/scheduler.py`

**`services/ingestion/`:**
- Purpose: Watches `docker/documents/` and ingests files into Qdrant RAG knowledge base
- Key files: `ingest.py`

**`shared/`:**
- Purpose: Shared Python library; volume-mounted into every Python service at `/app/shared`
- Contains: Auth middleware, Redis client, telemetry helpers, shared exceptions
- Key files: `shared/auth/__init__.py`, `shared/redis/__init__.py`

**`config/departments/`:**
- Purpose: YAML configuration files defining department structure and agent roles
- Contains: One file per department (marketing, social media, video production)
- Key files: `marketing.yaml`, `social_media.yaml`, `video_production.yaml`

**`docker/`:**
- Purpose: All Docker Compose definitions and runtime data directories
- Contains: Compose files for dev/prod/telemetry, DB init SQL, document drop-folder for RAG

**`infra/`:**
- Purpose: Production infrastructure as code
- Contains: Kubernetes manifests (numbered in apply order), Prometheus/Grafana/AlertManager configs

**`tests/`:**
- Purpose: Cross-service and system-level testing
- Contains: Performance (k6), security, RAG, integration, and workflow tests separate from per-service tests

## Key File Locations

**Entry Points:**
- `services/agents/app/main.py`: Agent service FastAPI app (port 9000)
- `services/auth/app/main.py`: Auth service FastAPI app (port 9002)
- `services/temporal_workers/worker.py`: Temporal worker process
- `services/scheduler/app/main.py`: Scheduler service (port 9003)
- `services/approval_ui/`: Approval UI (port 9001)
- `services/ingestion/ingest.py`: Ingestion service
- `apps/console/app/layout.tsx`: Next.js root layout
- `web-ui/app.py`: Legacy Flask admin dashboard

**Configuration:**
- `docker/docker-compose.yml`: Primary service definitions with all env var defaults
- `apps/console/prisma/schema.prisma`: Prisma ORM schema (Projects, Runs, Agents, Approvals, Users)
- `alembic.ini`: Python DB migration config
- `services/agents/app/settings.py`: Agent service Pydantic settings (all env vars)
- `services/auth/app/settings.py`: Auth service Pydantic settings

**Core Logic:**
- `services/agents/app/agents/factory.py`: Agent creation logic; switches Ollama vs Claude/OpenAI
- `services/agents/app/memory/rag.py`: Qdrant RAG retrieval with Redis cache
- `services/temporal_workers/workflows.py`: `ProjectPipelineWorkflow` with human approval gates
- `shared/auth/__init__.py`: Auth exports used by all Python services
- `shared/redis/`: Redis client used for caching and rate limiting

**Testing:**
- `apps/console/tests/`: Vitest tests (co-located pattern under `tests/`)
- `apps/console/e2e/`: Playwright E2E critical flow tests
- `services/agents/tests/`: pytest with `unit/`, `integration/`, `e2e/` subdirs
- `tests/`: Root-level cross-service tests

## Naming Conventions

**Python Files:**
- `snake_case.py` for all modules (e.g., `rag.py`, `cost_tracker.py`, `security_auditor.py`)
- `main.py` is the FastAPI entry point in every service
- `settings.py` holds Pydantic BaseSettings config per service
- `models.py` holds Pydantic request/response models

**TypeScript/Next.js Files:**
- `page.tsx` for route pages (Next.js App Router convention)
- `route.ts` for API route handlers
- `layout.tsx` for layout wrappers
- `PascalCase.tsx` for React components (e.g., `AgentStatusCard.tsx`, `KpiBar.tsx`)
- `kebab-case.ts` for utility modules (e.g., `auth-client.ts`)

**Python Classes:**
- `PascalCase` for classes (e.g., `AgentFactory`, `RAGMemory`, `CostTracker`)
- `snake_case` for functions and methods

**Directories:**
- `snake_case` for Python packages (e.g., `temporal_workers/`, `approval_ui/`)
- `kebab-case` is used in Docker service names; `snake_case` in directory names

## Where to Add New Code

**New Agent Type:**
- Implementation: `services/agents/app/agents/{agent_name}.py`
- Register in factory: `services/agents/app/agents/factory.py` — add `create_{agent_name}()` static method
- Instantiate in lifespan: `services/agents/app/main.py` — add to global state and `agents_dict`
- Add route handler: `services/agents/app/main.py` — add `@app.post("/{agent-name}/run")` endpoint
- Update health router: `services/agents/app/routers/health.py`

**New Next.js Page:**
- Dashboard page: `apps/console/app/(dashboard)/{page-name}/page.tsx`
- New API route: `apps/console/app/api/{endpoint}/route.ts`
- New component: `apps/console/components/{ComponentName}.tsx`
- Tests: `apps/console/tests/app/{page-name}/page.test.tsx`

**New Python Service:**
- Directory: `services/{service_name}/`
- Entry point: `services/{service_name}/app/main.py` (FastAPI)
- Mount shared: Add `- ../shared:/app/shared` volume in docker-compose.yml
- Auth integration: Call `set_auth_client()` in lifespan and import from `shared.auth`
- Expose metrics: Mount `make_asgi_app()` at `/metrics`
- Register in compose: Add service block to `docker/docker-compose.yml`

**New Department Config:**
- Add YAML: `config/departments/{department_name}.yaml`
- The `DepartmentManager` loads all files from that directory at startup — no code change required

**New RAG Documents:**
- Drop files into: `docker/documents/`
- The ingestion service (`services/ingestion/ingest.py`) watches this directory and auto-ingests

**New Shared Utilities:**
- Shared auth helpers: `shared/auth/`
- Shared Redis helpers: `shared/redis/`
- Shared exceptions: `shared/exceptions.py`

**Database Migrations:**
- Python services: Add Alembic migration to `alembic/versions/`
- Console (Prisma): Update `apps/console/prisma/schema.prisma` and run `prisma migrate`

**Utilities:**
- Python service-specific helpers: `services/{service}/app/utils.py`
- Console shared helpers: `apps/console/lib/utils.ts`

## Special Directories

**`docker/documents/`:**
- Purpose: Drop zone for files to be ingested into the Qdrant RAG knowledge base
- Generated: No (operator-managed)
- Committed: No

**`docker/agent-output/`:**
- Purpose: Volume-mounted output directory for agent-generated artifacts
- Generated: Yes (by agents at runtime)
- Committed: No

**`apps/console/.next/`:**
- Purpose: Next.js build cache and compiled output
- Generated: Yes
- Committed: No

**`apps/console/coverage/`:**
- Purpose: Vitest code coverage reports
- Generated: Yes
- Committed: No

**`apps/console/test-results/`:**
- Purpose: Playwright test result artifacts and screenshots
- Generated: Yes
- Committed: No

**`services/*/htmlcov/`:**
- Purpose: Python pytest HTML coverage reports per service
- Generated: Yes
- Committed: No

**`.planning/codebase/`:**
- Purpose: GSD architecture and convention documents consumed by plan/execute phases
- Generated: Yes (by map-codebase)
- Committed: Yes

---

*Structure analysis: 2026-03-04*
