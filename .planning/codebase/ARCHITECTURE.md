# Architecture

**Analysis Date:** 2026-03-04

## Pattern Overview

**Overall:** Microservices + Event-Driven Agentic Platform

The system is a multi-language microservices architecture orchestrating AI agents to autonomously build SaaS products. Python FastAPI services handle AI/backend logic; a Next.js frontend acts as the management console. Services communicate via HTTP (synchronous) and Temporal workflows (durable async). All services share a common `shared/` Python module for auth, Redis, and telemetry.

**Key Characteristics:**
- Polyglot: Python (FastAPI) backends + TypeScript (Next.js) frontend
- Durable workflow execution via Temporal for long-running agent tasks
- Shared Python module (`shared/`) consumed by all Python services as a volume mount
- RAG (Retrieval-Augmented Generation) memory via Qdrant for grounding agent outputs
- Human-in-the-loop approval gates embedded in Temporal workflows
- All Python services expose Prometheus `/metrics` endpoints
- Docker Compose is the primary runtime environment; Kubernetes manifests exist for production

## Layers

**Presentation Layer:**
- Purpose: Web UI for operators to manage agents, projects, and view observability data
- Location: `apps/console/` (Next.js 14 App Router)
- Contains: Route pages, React Server Components, API routes (BFF pattern), Prisma client
- Depends on: Python backend services via HTTP, PostgreSQL via Prisma
- Used by: Human operators via browser

**Legacy Web UI:**
- Purpose: Admin dashboard with workflow visualization (Flask/Jinja2, Python)
- Location: `web-ui/app.py`, `web-ui/templates/`, `web-ui/static/`
- Contains: HTML templates, embedded JS visualization
- Depends on: Agent service at port 9000, PostgreSQL direct
- Used by: Internal admin use; largely superseded by `apps/console/`

**Agent Execution Layer:**
- Purpose: LLM-powered agents that execute tasks (code generation, QA, design, devops, security)
- Location: `services/agents/app/`
- Contains: 7 specialized agents, RAG memory, cost tracking, webhook event dispatch
- Depends on: Qdrant (RAG), Ollama/Claude/OpenAI (LLM providers), Langfuse (tracing), PostgreSQL, Redis, Auth service
- Used by: Temporal workers (via HTTP), console BFF routes, direct API callers

**Authentication Layer:**
- Purpose: JWT and API key authentication for all services
- Location: `services/auth/app/`
- Contains: Auth routers, JWT middleware, API key management, user handlers
- Depends on: PostgreSQL, Redis (token caching)
- Used by: All other Python services via `shared.auth.AuthClient`

**Workflow Orchestration Layer:**
- Purpose: Durable execution of multi-step agent pipelines with human approval gates
- Location: `services/temporal_workers/` (worker + workflows + activities)
- Contains: `ProjectPipelineWorkflow`, `SimpleTaskWorkflow`, activity functions that call Agent service HTTP endpoints
- Depends on: Temporal server, Agent service (HTTP), Approval UI (HTTP), Telegram (notifications)
- Used by: Triggered externally via Temporal client

**Approval Layer:**
- Purpose: Web UI for human approvers to approve/deny high-risk agent actions
- Location: `services/approval_ui/`
- Contains: Flask app, HTML templates, approval database records
- Depends on: PostgreSQL, Temporal (sends signals back to workflows), Auth service
- Used by: Human approvers during workflow execution

**Scheduler Layer:**
- Purpose: Scheduled and recurring task execution (cron-style triggers for agents)
- Location: `services/scheduler/app/`
- Contains: APScheduler integration, schedule management routers, database manager
- Depends on: PostgreSQL, Agent service (HTTP at 9000)
- Used by: Operator-configured recurring agent tasks

**Ingestion Layer:**
- Purpose: Document ingestion pipeline to populate the RAG knowledge base
- Location: `services/ingestion/ingest.py`
- Contains: File watcher, Ollama embeddings, Qdrant upsert
- Depends on: Qdrant, Ollama (embedding model: `nomic-embed-text`)
- Used by: Operators placing documents in `docker/documents/`

**Shared Infrastructure Module:**
- Purpose: Eliminate code duplication across all Python microservices
- Location: `shared/`
- Contains: `shared/auth/` (AuthClient, AuthContext, middleware), `shared/redis/` (RedisCache), `shared/telemetry/`, `shared/logging_config.py`, `shared/exceptions.py`
- Depends on: Nothing (foundational)
- Used by: All Python services; mounted as volume at `/app/shared`

**SDK Layer:**
- Purpose: Python client SDK for external consumers of the platform
- Location: `sdk/temponest_sdk/`
- Contains: `agents.py`, `client.py`, `collaboration.py`, `costs.py`, `rag.py`, `scheduler.py`, `webhooks.py`
- Depends on: Agent service HTTP API
- Used by: External applications, examples

**CLI Layer:**
- Purpose: Command-line interface for interacting with the platform
- Location: `cli/temponest_cli/cli.py`
- Contains: Click-based CLI commands
- Depends on: SDK
- Used by: Developers and operators

## Data Flow

**Standard Agent Execution Flow:**

1. Console (`apps/console/`) sends authenticated request to Agent service API (`:9000`)
2. Agent service validates JWT via `shared.auth.require_permission("agents:execute")`
3. Budget check: token count of task vs `BUDGET_TOKENS_PER_TASK` setting
4. RAG query: `RAGMemory.search()` fetches relevant context from Qdrant with cosine similarity
5. LLM call: agent sends prompt + RAG context to Ollama/Claude/OpenAI
6. Citation validation: response must include ≥2 citations with score ≥ `RAG_MIN_SCORE`
7. Latency SLO check: warn if response exceeds `LATENCY_SLO_MS`
8. Cost recorded: `CostTracker` writes to PostgreSQL `model_pricing` / cost tables
9. Event dispatched: `EventDispatcher` publishes `task.started`, `task.completed`, or `task.failed` events
10. Idempotent response cached in-memory and returned to caller

**Durable Workflow Flow (ProjectPipelineWorkflow):**

1. External trigger starts `ProjectPipelineWorkflow` on Temporal queue `agentic-task-queue`
2. Temporal worker (`services/temporal_workers/worker.py`) picks up work
3. `invoke_overseer` activity calls Agent service `POST /overseer/run` → decomposes goal into tasks
4. For each task: risk is assessed (`low` / `medium` / `high`)
5. Medium/high risk: `request_approval` activity creates DB record; `send_telegram_notification` pings approvers
6. Workflow waits via `workflow.wait_condition()` for `approval_signal` (24-hour timeout)
7. On approval: `invoke_developer` activity calls Agent service `POST /developer/run`
8. `validate_output` activity checks result quality
9. Final deployment approval gate (always `high` risk, requires 2 approvers)
10. `execute_deployment` activity runs deployment

**Console Data Fetch (Server Components):**

1. Next.js Server Component calls `prisma.agent.findMany()` directly (server-side, no API hop)
2. Prisma queries PostgreSQL at `DATABASE_URL`
3. Component renders HTML server-side with live data

**State Management (Console):**
- Server state: React Server Components + direct Prisma queries
- Client state: React `useState` hooks for forms and loading states
- No global client-side state store (Redux/Zustand not present)
- Auth state: BetterAuth sessions (`apps/console/lib/auth.ts`, `apps/console/lib/auth-client.ts`)

## Key Abstractions

**AgentFactory:**
- Purpose: Creates the correct agent implementation based on the configured LLM provider
- Examples: `services/agents/app/agents/factory.py`
- Pattern: Static factory methods; switches between `DeveloperAgent` (CrewAI/Ollama) and `DeveloperAgentV2` (direct LLM for Claude/OpenAI)

**RAGMemory:**
- Purpose: Abstraction over Qdrant for embedding retrieval with Redis caching layer
- Examples: `services/agents/app/memory/rag.py`
- Pattern: Initialize → search returns citations with scores; agents require ≥2 citations above threshold

**AuthClient / shared.auth:**
- Purpose: Centralized auth validation shared across all Python microservices
- Examples: `shared/auth/__init__.py`, `shared/auth/client.py`, `shared/auth/middleware.py`
- Pattern: Each service calls `set_auth_client()` at startup; route handlers use `Depends(require_permission("..."))`

**DepartmentManager:**
- Purpose: Loads organizational department configurations from YAML files and provides agents structured by business function
- Examples: `services/agents/app/departments/manager.py`
- Config: `config/departments/*.yaml` (marketing.yaml, social_media.yaml, video_production.yaml)
- Pattern: Loaded at startup; injected into `departments_router`

**CollaborationManager:**
- Purpose: Coordinates multi-agent collaboration; routes tasks among the 7 specialized agents
- Examples: `services/agents/app/collaboration/manager.py`
- Pattern: Initialized with `agents_dict` keyed by `AgentRole` enum; exposes collaboration endpoint

**CostTracker / CostCalculator:**
- Purpose: Records per-task LLM cost to PostgreSQL using pricing loaded from `model_pricing` table
- Examples: `services/agents/app/cost/tracker.py`, `services/agents/app/cost/calculator.py`
- Pattern: `CostTracker.record()` called after every agent execution with tokens_used and model info

**EventDispatcher / WebhookManager:**
- Purpose: Publish lifecycle events (task.started, task.completed, task.failed) and dispatch to registered webhooks
- Examples: `services/agents/app/webhooks/` directory
- Pattern: Fire-and-forget; errors logged but do not fail the main request

## Entry Points

**Agent Service:**
- Location: `services/agents/app/main.py`
- Port: 9000
- Triggers: HTTP POST to `/overseer/run`, `/developer/run`, `/qa-tester/run`, `/devops/run`, `/designer/run`, `/security-auditor/run`, `/ux-researcher/run`
- Responsibilities: JWT auth, budget enforcement, RAG retrieval, LLM execution, citation validation, cost recording, event dispatch

**Auth Service:**
- Location: `services/auth/app/main.py`
- Port: 9002
- Triggers: HTTP requests from all other services for token validation; user login/registration
- Responsibilities: Issue JWT tokens, validate tokens, manage API keys, cache token validation results in Redis

**Temporal Worker:**
- Location: `services/temporal_workers/worker.py`
- Triggers: Temporal task queue `agentic-task-queue`
- Responsibilities: Execute `ProjectPipelineWorkflow` and `SimpleTaskWorkflow`; call Agent and Approval UI services

**Scheduler Service:**
- Location: `services/scheduler/app/main.py`
- Port: 9003
- Triggers: Configured cron schedules stored in PostgreSQL
- Responsibilities: Poll DB for due tasks; invoke Agent service on schedule

**Approval UI:**
- Location: `services/approval_ui/` (Flask app)
- Port: 9001
- Triggers: Human operator visiting approval UI; Temporal activities calling `request_approval`
- Responsibilities: Display pending approvals; send `approval_signal` back to Temporal

**Ingestion Service:**
- Location: `services/ingestion/ingest.py`
- Triggers: Files dropped into `docker/documents/` directory (file watcher)
- Responsibilities: Generate embeddings via Ollama; upsert vectors into Qdrant `agentic_knowledge` collection

**Next.js Console:**
- Location: `apps/console/app/layout.tsx`
- Port: 3000 (dev) / standalone build
- Triggers: Browser navigation; BetterAuth session
- Responsibilities: Render dashboard, projects, agents health, wizards, financials, observability views

**Web UI (Legacy Flask):**
- Location: `web-ui/app.py`
- Port: 8082 (via Docker)
- Triggers: Browser navigation
- Responsibilities: Admin dashboard with Prometheus metrics visualization

## Error Handling

**Strategy:** Graceful degradation at service startup; try/except at endpoint level returns structured error responses

**Patterns:**
- At startup: optional dependencies (Redis, Langfuse, cost DB) are wrapped in try/except; service starts degraded if they fail
- At request time: unhandled exceptions return `AgentResponse(status="failed", error=str(e))` rather than raising HTTP 500
- Auth service has global `@app.exception_handler(Exception)` returning `{"detail": "Internal server error"}` (no leaking)
- Validation errors in Auth service sanitize input with `html.escape()` before returning (XSS prevention)
- Temporal workflows have `RetryPolicy` on activities; approval timeout after 24h returns `status: "timeout"`
- RAG: if citation count < 2 and `REQUIRE_CITATIONS=true`, returns HTTP 400 (configurable flag for testing)

## Cross-Cutting Concerns

**Logging:** `print()` statements throughout (structured logging config in `shared/logging_config.py` exists but not consistently used)

**Validation:** Pydantic models for all FastAPI request/response schemas; Zod (`WizardStepRequestSchema`) in Next.js API routes

**Authentication:** JWT Bearer tokens issued by Auth service; validated by `shared.auth.AuthClient` which caches results in Redis. Console uses BetterAuth (`better-auth` npm package) for session management with its own Prisma-backed session store.

**Rate Limiting:** `slowapi` on Agent service (20/minute for `/overseer/run`); Auth service also uses `slowapi`

**Observability:** Prometheus metrics exposed at `/metrics` on all Python services; Grafana dashboards in `infra/grafana/dashboards/`; Langfuse for LLM tracing

**Idempotency:** In-memory `idempotency_cache` dict in Agent service; callers provide `idempotency_key` to deduplicate requests within a process lifetime (lost on restart)

---

*Architecture analysis: 2026-03-04*
