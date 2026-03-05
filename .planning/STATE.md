# State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-05)

**Core value:** Operator submits a project goal → agents build it → approve at final deployment
**Current focus:** Defining requirements for v0.1

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-03-05 — Milestone v0.1 started

## Accumulated Context

- Codebase fully mapped — see `.planning/codebase/` (ARCHITECTURE.md, STACK.md, STRUCTURE.md, CONCERNS.md, CONVENTIONS.md, TESTING.md, INTEGRATIONS.md)
- Primary broken areas are in `factory.py`, `collaboration/manager.py`, `workflows.py`, and `ingestion/ingest.py`
- Docker Compose is the runtime — check for running containers before running standalone commands
- All Python services share `shared/` via volume mount at `/app/shared`
