# Requirements: Temponest

**Defined:** 2026-03-05
**Core Value:** Operator submits a project goal → agents build it → approve at final deployment

## v0.1 Requirements

### Agent LLM Routing

- [ ] **ROUTE-01**: Overseer agent executes using the Claude (Anthropic) provider
- [ ] **ROUTE-02**: Developer, QA, DevOps, Designer, Security Auditor, and UX Researcher agents execute using Ollama
- [ ] **ROUTE-03**: Agent provider can be configured per-agent (not one global setting for all)

### Multi-Agent Collaboration

- [ ] **COLLAB-01**: Collaboration manager executes real agent calls instead of returning mock responses
- [ ] **COLLAB-02**: Sequential collaboration pattern passes output from one agent as input to the next
- [ ] **COLLAB-03**: Parallel collaboration pattern runs multiple agents concurrently and aggregates results

### Project Pipeline

- [ ] **PIPE-01**: Operator can submit a project goal and the Overseer decomposes it into tasks
- [ ] **PIPE-02**: Each decomposed task is executed by the appropriate specialist agent
- [ ] **PIPE-03**: Workflow completes all tasks without stopping for mid-flow approval
- [ ] **PIPE-04**: Final deployment step requires operator approval before proceeding

### Approval Gates

- [ ] **APPR-01**: Approval is only requested at the final deployment step
- [ ] **APPR-02**: Operator can approve or reject deployment via the Approval UI

### RAG Ingestion

- [ ] **RAG-01**: Document ingestion service tracks processed files persistently across restarts
- [ ] **RAG-02**: Already-ingested documents are not re-embedded on restart

## Future Requirements

### Security Hardening

- **SEC-01**: Hardcoded default JWT secrets rejected at startup in production environment
- **SEC-02**: Test session token bypass disabled outside of test environment
- **SEC-03**: Scheduler endpoints require authentication

### Observability

- **OBS-01**: Agent readiness endpoint surfaces which optional subsystems are active
- **OBS-02**: Per-provider token counting (Anthropic tokenizer for Claude, not GPT-3.5 encoding)

### Performance

- **PERF-01**: Idempotency cache stored in Redis (not in-memory dict) for multi-replica support
- **PERF-02**: RAG Qdrant calls use AsyncQdrantClient to avoid blocking the event loop

## Out of Scope

| Feature | Reason |
|---------|--------|
| OAuth2 / OIDC authentication | Email/password sufficient for v0.1 |
| Multi-region support | Not needed until scaling |
| RBAC | Single-operator use case for v0.1 |
| Web-UI (legacy Flask) improvements | Superseded by Next.js console |
| Scheduler service improvements | Not on critical path for project pipeline |
| Agent v1 (CrewAI) migration to v2 | Ollama agents stay on v1 CrewAI for now |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ROUTE-01 | Phase 1 | Pending |
| ROUTE-02 | Phase 1 | Pending |
| ROUTE-03 | Phase 1 | Pending |
| COLLAB-01 | Phase 2 | Pending |
| COLLAB-02 | Phase 2 | Pending |
| COLLAB-03 | Phase 2 | Pending |
| PIPE-01 | Phase 3 | Pending |
| PIPE-02 | Phase 3 | Pending |
| PIPE-03 | Phase 3 | Pending |
| PIPE-04 | Phase 3 | Pending |
| APPR-01 | Phase 3 | Pending |
| APPR-02 | Phase 3 | Pending |
| RAG-01 | Phase 4 | Pending |
| RAG-02 | Phase 4 | Pending |

**Coverage:**
- v0.1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0

---
*Requirements defined: 2026-03-05*
*Last updated: 2026-03-05 — traceability mapped after roadmap creation*
