# Temponest

## What This Is

Temponest is an AI agentic platform for running multi-agent software projects. Operators give it a goal (e.g. "build a form builder SaaS"), the Overseer agent decomposes it into tasks, and specialized agents (Developer, QA, DevOps, Designer, Security Auditor, UX Researcher) execute them end-to-end — with the operator approving only the final deployment step.

## Core Value

An operator can submit a project goal and receive a completed, deployed software project with minimal human involvement.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope — v0.1 First Working Build -->

- [ ] Overseer uses Claude (Anthropic); all other agents use Ollama (local)
- [ ] Multi-agent collaboration executes real agent calls (not mock responses)
- [ ] Full Temporal project pipeline runs end-to-end (Overseer → task decomposition → agents → deploy)
- [ ] Approval gate triggers only at the final deployment step, not on every medium-risk action
- [ ] RAG ingestion deduplicates documents across restarts

### Out of Scope

- Multi-region support — not needed for v0.1
- RBAC / OAuth2 — email/password auth sufficient for now
- Scheduler service improvements — not on the critical path
- Web-UI (legacy Flask) improvements — superseded by Next.js console

## Context

- The codebase was built across 7 phases (schema, agents, scheduler, observability, SDK, advanced SDK, tooling)
- Codebase analysis is in `.planning/codebase/` (mapped 2026-03-04)
- **Critical broken areas:**
  - `services/agents/app/agents/factory.py` — provider setting is read but ignored for 6 of 7 agents; all route to v1 CrewAI (Ollama)
  - `services/agents/app/collaboration/manager.py` line 343 — `_call_agent()` returns a hardcoded mock response
  - `services/temporal_workers/workflows.py` — approval requested for medium AND high risk; should be high/deploy only
  - `services/ingestion/ingest.py` line 58 — `processed_files` set is in-memory only, reset on restart
- Docker Compose is the primary runtime (`docker/docker-compose.yml`)
- Shared Python module at `shared/` is volume-mounted into all services

## Constraints

- **LLM**: Overseer → Claude (Anthropic API key required); other agents → Ollama (local, no key)
- **Runtime**: Docker Compose — all services run in containers
- **Approval**: Operator approves only at final deployment step (not every action)
- **Backwards compat**: Do not break existing API contracts on agent endpoints

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Overseer uses Claude, others use Ollama | Balance quality of goal decomposition vs cost of execution | — Pending |
| Approval only at final deploy | Minimize interruptions while keeping safety gate on irreversible actions | — Pending |

---
*Last updated: 2026-03-05 — Milestone v0.1 started*
