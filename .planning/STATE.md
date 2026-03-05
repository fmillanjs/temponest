# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-05)

**Core value:** Operator submits a project goal and receives a completed, deployed software project with minimal human involvement
**Current focus:** Phase 1 — Agent LLM Routing

## Current Position

Phase: 1 of 4 (Agent LLM Routing)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-03-05 — Roadmap created for milestone v0.1

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

- Overseer uses Claude (Anthropic), all other agents use Ollama — balances decomposition quality vs execution cost
- Approval fires only at final deployment step — minimizes operator interruptions while preserving safety gate

### Pending Todos

None yet.

### Blockers/Concerns

- `services/agents/app/agents/factory.py` — provider setting read but ignored for 6 of 7 agents; all route to v1 CrewAI (Ollama). Root cause for Phase 1.
- `services/agents/app/collaboration/manager.py` line 343 — `_call_agent()` returns hardcoded mock. Phase 2 target.
- `services/temporal_workers/workflows.py` — approval fires on medium AND high risk, not just final deployment. Phase 3 target.
- `services/ingestion/ingest.py` line 58 — `processed_files` set is in-memory only, reset on restart. Phase 4 target.
- Docker Compose is the runtime — check for running containers before running standalone commands
- All Python services share `shared/` via volume mount at `/app/shared`

## Session Continuity

Last session: 2026-03-05
Stopped at: Roadmap created; no plans written yet
Resume file: None
