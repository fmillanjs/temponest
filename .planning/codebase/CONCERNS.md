# Codebase Concerns

**Analysis Date:** 2026-03-04

---

## Tech Debt

**agent main.py is a 1168-line God File:**
- Issue: All 7 agent endpoint handlers (`/overseer/run`, `/developer/run`, `/qa-tester/run`, `/devops/run`, `/designer/run`, `/security-auditor/run`, `/ux-researcher/run`) are inline in one file with near-identical boilerplate repeated per handler (~80 lines each)
- Files: `services/agents/app/main.py`
- Impact: Any cross-cutting change (e.g. adding tracing, changing error format) must be replicated 7 times; high risk of drift
- Fix approach: Extract a generic `run_agent_endpoint()` helper, reduce handlers to delegation calls

**Dead Code — rate_limiting.py:**
- Issue: `services/agents/app/rate_limiting.py` defines a full `RateLimiter` class (Redis token bucket, per-tier limits) that is never imported anywhere in the application. Actual rate limiting uses `slowapi` via `services/agents/app/limiter.py`
- Files: `services/agents/app/rate_limiting.py`
- Impact: Confusing to future developers; may cause duplicate/conflicting rate-limit implementations if someone discovers and wires it in
- Fix approach: Delete the file or document explicitly that `limiter.py` (slowapi) is canonical

**Alembic autogenerate disabled:**
- Issue: `alembic/env.py` line 23 sets `target_metadata = None`, disabling schema diff-based migration generation. All schema changes require hand-written SQL in `docker/migrations/` (currently 9 files numbered manually)
- Files: `alembic/env.py`, `docker/migrations/`
- Impact: No automated guard against schema drift; SQL migrations can diverge from actual ORM models; no version tracking inside the database
- Fix approach: Set `target_metadata` to the SQLAlchemy Base metadata and switch from raw SQL migration files to Alembic-managed versions

**V1/V2 agent versioning left open:**
- Issue: `DeveloperAgent` (v1, CrewAI) and `DeveloperAgentV2` (direct LLM) both exist. The factory routes only `developer` to V2 for non-Ollama providers; all other agents (QA, DevOps, Designer, Security, UX, Overseer) are forced to V1 CrewAI regardless of provider selection. The factory assigns `provider` variable but never uses it after the comment "Use CrewAI approach for now"
- Files: `services/agents/app/agents/factory.py`, `services/agents/app/agents/developer_v2.py`
- Impact: Provider config has no effect for 6 of 7 agents; users configuring `claude` or `openai` as provider will silently get Ollama-based CrewAI behavior for most agents
- Fix approach: Either migrate all agents to the V2 pattern or document that V1 is Ollama-only and add a validation error when non-Ollama providers are configured for V1 agents

**web-ui uses `asyncio.run()` inside sync Flask handlers:**
- Issue: `web-ui/app.py` (lines 195, 382, 409, 458, 523) uses `asyncio.run()` to run async DB calls from synchronous Flask route handlers. This creates a new event loop per request and is incompatible with any async framework/middleware layer
- Files: `web-ui/app.py`
- Impact: Performance overhead (new event loop per request); potential deadlocks if called inside an existing event loop; will break if Flask is ever replaced with an async server
- Fix approach: Either rewrite the Flask routes as async (use `asgiref` or replace with FastAPI/Starlette), or use synchronous `psycopg2` instead of `asyncpg` for this service

**Collaboration manager uses mock execution:**
- Issue: `CollaborationManager._call_agent()` (line 343) returns a hardcoded mock response and prints a warning instead of executing real agents. The full collaboration workflow (sequential, parallel, iterative, hierarchical) calls this stub for every task
- Files: `services/agents/app/collaboration/manager.py` (line 343-357)
- Impact: All collaboration API endpoints return fake results; the feature appears functional but produces no real agent output
- Fix approach: Replace stub with actual calls to each agent's `.execute()` method (documented in the comment at line 344)

**Department manager approval integration missing:**
- Issue: `DepartmentManager._execute_department_workflow()` (line 299) contains a `FIXME` noting that `approval_required` flag is checked but approval is printed as "automatic approval not implemented" — the approval service is never called
- Files: `services/agents/app/departments/manager.py` (lines 298-304)
- Impact: Any workflow step marked `approval_required: true` silently auto-approves; the approval UI service exists but receives no requests from this code path
- Fix approach: POST to approval service at `http://approval:8000/api/approval/request` and poll or await webhook callback before proceeding

**ingestion service tracks processed files in memory only:**
- Issue: `DocumentProcessor.__init__` stores `self.processed_files = set()`. On restart, all files are reprocessed and re-ingested into Qdrant, generating duplicate vector entries
- Files: `services/ingestion/ingest.py` (line 58)
- Impact: Each service restart duplicates embeddings; search quality degrades with duplicate chunks; storage grows unboundedly
- Fix approach: Persist processed file hashes to a file or database table; check before embedding

---

## Known Bugs

**Overseer idempotency cache write uses wrong object:**
- Symptoms: Idempotency key is correctly read from `agent_request` on check, but cache write on line 479 uses `request.idempotency_key` where `request` is the FastAPI `Request` object (not `AgentRequest`). The attribute does not exist on `Request`; the `if` condition evaluates to `False` silently, so the response is never cached for the `/overseer/run` endpoint
- Files: `services/agents/app/main.py` (line 479)
- Trigger: Any POST to `/overseer/run` with an `idempotency_key` value; subsequent identical requests will re-execute instead of returning cached result
- Workaround: None — the cache read on line 425-426 correctly uses `agent_request`, but the write is broken

**Cost tracking uses rough 40/60 token split:**
- Symptoms: `record_execution_cost()` assumes input tokens = 40% and output tokens = 60% of total `tokens_used`. Actual LLM calls often have high input-to-output ratios (e.g. a long RAG context with short completion), causing billing estimates to be systematically inaccurate
- Files: `services/agents/app/utils.py` (lines 77-79)
- Trigger: Every agent execution that records cost
- Workaround: Only affects reporting accuracy, not functional correctness

**Claude Code CLI token counting is estimated:**
- Symptoms: `ClaudeCodeClient._execute_command()` estimates tokens at `len(text) // 4`. This is not token-accurate and will under/overcount, affecting budget enforcement and cost tracking for the `claude-code` provider
- Files: `services/agents/app/llm/claude_code_client.py` (lines 231-232)
- Trigger: Any agent using `provider=claude-code`

---

## Security Considerations

**Hardcoded default JWT secret keys in multiple services:**
- Risk: All services ship with weak plaintext default secrets. If an operator forgets to override the env var, tokens signed in development will be accepted in production (or vice versa across services since defaults match)
- Files: `services/agents/app/settings.py` (line 32), `services/auth/app/settings.py` (line 19), `services/scheduler/app/settings.py` (line 22), `services/approval_ui/main.py` (line 34)
- Current mitigation: Comment says "change in production"; no validation enforces this
- Recommendations: Add a startup assertion that rejects the default value when `ENVIRONMENT=production`, or generate a random secret on first start and persist to a secrets file

**Hardcoded default DB credentials:**
- Risk: `postgresql://postgres:postgres@...` is the default for agents, auth, scheduler, and approval_ui services. If env vars are not set, these credentials are used
- Files: `services/agents/app/settings.py` (line 20), `services/auth/app/settings.py` (line 13), `services/scheduler/app/settings.py` (line 13), `services/approval_ui/main.py` (line 30)
- Current mitigation: None
- Recommendations: Same startup validation approach as JWT secret

**Wildcard CORS on agents and scheduler services:**
- Risk: `allow_origins=["*"]` with `allow_credentials=True` is not valid per the CORS specification (browsers reject this combination) and exposes the service to cross-origin attacks from any domain
- Files: `services/agents/app/main.py` (line 374), `services/scheduler/app/main.py` (line 84)
- Current mitigation: Browser enforcement will block credential sharing; machine-to-machine calls are unaffected
- Recommendations: Set explicit `CORS_ORIGINS` env var per the pattern already used in `services/auth/app/settings.py`

**Test session token bypass in production middleware:**
- Risk: `apps/console/middleware.ts` (lines 21-25) grants full access to any request carrying a cookie value starting with `test-session-token-`. This bypass is intended for E2E tests but is active in all environments including production
- Files: `apps/console/middleware.ts`, `apps/console/e2e/auth.setup.ts`
- Current mitigation: The prefix string must be known; this is security through obscurity
- Recommendations: Gate the bypass behind an env var (e.g. only allow if `NODE_ENV=test`) or remove it and implement real test authentication

**WizardStepRequestSchema does not sanitize `step` or `args` before shell execution:**
- Risk: `apps/console/app/api/wizard/factory/step/route.ts` (line 14) interpolates `step` and `args` directly into a bash command string: `` `./cli/saas-factory-init.sh ${step} ${args.join(' ')}` ``. While `execStream` disables shell and validates `workdir`, the arguments are passed to `/bin/bash -lc` as a string, enabling injection through `step` or `args` values
- Files: `apps/console/app/api/wizard/factory/step/route.ts`, `apps/console/lib/schemas.ts`
- Current mitigation: `WizardStepRequestSchema` uses `z.string()` with no pattern restriction on `step`; `sanitizeArgs` in `lib/server/exec.ts` is never called in this route
- Recommendations: Add an allowlist of valid step names to the Zod schema, and apply `sanitizeArgs()` before building the command string

**Scheduler service has no authentication on listing endpoints:**
- Risk: Documented known issue — the scheduler `/schedules` endpoint currently returns 200 for unauthenticated requests
- Files: `services/scheduler/app/routers/schedules.py`, `tests/integration/test_auth_integration.py` (line 92)
- Current mitigation: Test explicitly accepts this as current behavior; auth client is initialized but enforcement is inconsistent
- Recommendations: Verify `get_current_user` dependency is enforced on all scheduler routes

---

## Performance Bottlenecks

**In-memory idempotency cache is unbounded and not shared:**
- Problem: `idempotency_cache: Dict[str, AgentResponse] = {}` in `services/agents/app/main.py` (line 64) grows without eviction. In a multi-replica deployment, each pod has its own cache so idempotency is not guaranteed across replicas
- Files: `services/agents/app/main.py`
- Cause: Python dict with no TTL or size limit
- Improvement path: Store idempotency records in Redis with a short TTL (e.g. 24 hours) matching the key's validity window

**Collaboration workspaces stored in memory with no cleanup:**
- Problem: `CollaborationManager.active_workspaces: Dict[UUID, CollaborationWorkspace]` accumulates completed workspaces indefinitely; there is no cleanup after `start_collaboration()` returns
- Files: `services/agents/app/collaboration/manager.py` (line 35, line 68)
- Cause: Dict grows unboundedly; long-running services will leak memory
- Improvement path: Remove workspace from `active_workspaces` after `start_collaboration()` completes, or implement a TTL-based cleanup task

**RAG embedding calls are synchronous Qdrant client calls inside async service:**
- Problem: `RAGMemory.retrieve()` and `add_documents()` use `self.client.query_points()` (the synchronous `QdrantClient` method) directly in an async context without `asyncio.to_thread()`, blocking the event loop during Qdrant I/O
- Files: `services/agents/app/memory/rag.py` (lines 139, 44, 47, 50)
- Cause: `qdrant-client` has an async client (`AsyncQdrantClient`) that is not used here
- Improvement path: Replace `QdrantClient` with `AsyncQdrantClient` or wrap blocking calls in `asyncio.to_thread()`

---

## Fragile Areas

**Agent service startup is all-or-nothing with cascading optional disables:**
- Files: `services/agents/app/main.py` (lifespan function, lines 121-331)
- Why fragile: If Redis, database, or Qdrant are unavailable at startup, the entire cost tracking, webhooks, and caching subsystems are silently set to `None`. The service starts but with degraded functionality, and callers have no way to know which subsystems are disabled. Error messages go to stdout only
- Safe modification: Always verify which optional subsystems are active before adding code that depends on them; add a `/readiness` endpoint that surfaces which components are disabled

**Multiple dual-library JWT implementations (PyJWT vs python-jose):**
- Files: `shared/auth/client.py` (uses `import jwt` — PyJWT), `services/auth/app/handlers/jwt_handler.py` (uses `from jose import jwt` — python-jose)
- Why fragile: The two libraries have different APIs and different behavior for algorithm handling; a token created with python-jose may behave differently when decoded with PyJWT; algorithm confusion bugs are a well-known JWT attack vector
- Test coverage: Unit tests for each handler exist but do not cross-verify token compatibility
- Safe modification: Standardize on one library across all services; python-jose is the one already used for token creation

**Hardcoded host path in exec.ts allowlist:**
- Files: `apps/console/lib/server/exec.ts` (line 21)
- Why fragile: `allowedDirs = ['/home/doctor/temponest']` is a machine-specific absolute path. This will fail immediately on any deployment to a different host, container, or CI environment
- Safe modification: Replace with an env var (e.g. `WORKDIR_BASE`) with a sensible default like `/app`

---

## Scaling Limits

**Token budget enforcement is per-request only:**
- Current capacity: Token budget is checked once at request entry (`enforce_budget()`) based on task string length only, not on actual LLM call sizes
- Limit: No rate limiting on aggregate token consumption per tenant per period; a single tenant could exhaust the LLM provider quota
- Scaling path: Add per-tenant token budget tracking in Redis with rolling window counters

**Scheduler polls at fixed interval (30 seconds):**
- Current capacity: `scheduler_poll_interval_seconds: int = 30` — all scheduled tasks are checked every 30 seconds
- Limit: At scale with thousands of schedules, a single polling loop per pod becomes a bottleneck
- Scaling path: Partition schedules by tenant hash across multiple workers, or switch to event-driven scheduling (e.g. Temporal workflows instead of polling)

---

## Dependencies at Risk

**`tiktoken` used with GPT-3.5-Turbo encoding for all providers:**
- Risk: `count_tokens()` in `services/agents/app/utils.py` uses `gpt-3.5-turbo` encoding regardless of actual provider (Claude, Ollama, OpenAI). Claude and Ollama use different tokenizers; counts will be inaccurate
- Impact: Budget enforcement (`BUDGET_TOKENS_PER_TASK`) is unreliable for non-OpenAI models; tasks may be incorrectly rejected or allowed through the budget check
- Migration plan: Use provider-specific token counting (Anthropic SDK for Claude, model-specific logic for Ollama) or accept ±10% inaccuracy and document it

**Two versions of the developer agent maintained in parallel:**
- Risk: `DeveloperAgent` (v1, `agents/developer.py`) and `DeveloperAgentV2` (`agents/developer_v2.py`) have diverged feature sets; bug fixes applied to one are not applied to the other
- Impact: Behavior differences between Ollama and Claude/OpenAI paths may be unintentional
- Migration plan: Fully deprecate V1 by migrating Ollama support to the UnifiedLLMClient in V2, then delete `developer.py`

---

## Missing Critical Features

**Approval system is not wired end-to-end:**
- Problem: The approval UI service exists (`services/approval_ui/main.py`) and the Temporal workflow infrastructure is in place, but the agent execution path (`DepartmentManager`, `CollaborationManager`) never calls the approval service
- Blocks: Any workflow that requires human review before an action is taken operates without gating

**No token revocation mechanism for JWT tokens:**
- Problem: JWTs have a 1-hour TTL but there is no token blacklist or revocation endpoint. Once issued, a token cannot be invalidated before expiry (e.g. on logout or compromise)
- Blocks: Any security incident response requiring immediate session termination

---

## Test Coverage Gaps

**Overseer endpoint idempotency cache write bug has no test:**
- What's not tested: The `run_overseer` handler's cache write path (line 479) using the wrong object reference
- Files: `apps/console/tests/api/`, `services/agents/tests/`
- Risk: The bug is invisible in current test suite; a cache hit after write would reveal it
- Priority: High

**Collaboration and Department workflows only test mock execution:**
- What's not tested: End-to-end collaboration with real agent calls; all tests confirm the mock stub works correctly, not that actual agent execution occurs
- Files: `services/agents/tests/integration/test_collaboration_routes.py`, `services/agents/tests/integration/test_departments_routes.py`
- Risk: The stub can be removed or fixed without any test failures alerting to behavioral change
- Priority: High

**Scheduler authentication not enforced and test accepts current broken behavior:**
- What's not tested: A genuine auth rejection (401/403) on `/schedules` when unauthenticated
- Files: `tests/integration/test_auth_integration.py` (lines 92-105)
- Risk: Auth bypass will never be caught by automated tests as written; the assertion explicitly accepts 200 as valid
- Priority: High

**web-ui Flask routes not integration-tested against real DB:**
- What's not tested: The `asyncio.run()` pattern under concurrent requests; `tests/integration/test_costs_real_db.py` exists but requires a live database
- Files: `web-ui/app.py`, `web-ui/tests/integration/test_costs_real_db.py`
- Risk: Race conditions and event-loop issues under load go undetected
- Priority: Medium

---

*Concerns audit: 2026-03-04*
