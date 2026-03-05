# Roadmap: Temponest

## Overview

Milestone v0.1 "First Working Build" fixes four broken areas in the existing codebase: the agent LLM routing that ignores provider configuration, the collaboration manager that returns hardcoded mock responses, the Temporal pipeline approval gate that fires on medium-risk actions instead of only at final deployment, and the RAG ingestion service that re-embeds already-processed documents on every restart. Each phase delivers one coherent fix boundary. Routing must land first because every other phase depends on agents actually calling the right LLM.

## Milestones

- 🚧 **v0.1 First Working Build** - Phases 1-4 (in progress)

## Phases

- [ ] **Phase 1: Agent LLM Routing** - Fix AgentFactory so Overseer routes to Claude and all other agents route to Ollama
- [ ] **Phase 2: Real Collaboration** - Replace CollaborationManager mock with real agent execution for sequential and parallel patterns
- [ ] **Phase 3: Project Pipeline and Approval Gates** - Wire end-to-end Temporal pipeline; restrict approval to final deployment step only
- [ ] **Phase 4: RAG Ingestion Deduplication** - Persist processed-file tracking so documents are not re-embedded on restart

## Phase Details

### Phase 1: Agent LLM Routing
**Goal**: Each agent uses the LLM provider it is configured for — Overseer calls Claude, all specialist agents call Ollama
**Depends on**: Nothing (first phase)
**Requirements**: ROUTE-01, ROUTE-02, ROUTE-03
**Success Criteria** (what must be TRUE):
  1. A POST to /overseer/run results in a real Anthropic Claude API call, not an Ollama call
  2. A POST to /developer/run (and /qa-tester/run, /devops/run, /designer/run, /security-auditor/run, /ux-researcher/run) results in a real Ollama call
  3. Changing the provider setting for a specific agent in config changes which LLM that agent calls without affecting other agents
  4. No agent silently falls back to a different provider than configured
**Plans**: TBD

### Phase 2: Real Collaboration
**Goal**: The collaboration endpoint executes real agent calls in the configured pattern and returns actual agent output
**Depends on**: Phase 1
**Requirements**: COLLAB-01, COLLAB-02, COLLAB-03
**Success Criteria** (what must be TRUE):
  1. A collaboration request returns output produced by real agent execution, not a hardcoded mock string
  2. In a sequential collaboration, the output of agent N is passed as input context to agent N+1
  3. In a parallel collaboration, multiple agents run concurrently and their results are combined in the response
  4. A failed agent call in a collaboration returns an error response rather than a mock success
**Plans**: TBD

### Phase 3: Project Pipeline and Approval Gates
**Goal**: An operator can submit a project goal, agents execute all tasks without mid-flow interruption, and the operator approves only before final deployment
**Depends on**: Phase 2
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, APPR-01, APPR-02
**Success Criteria** (what must be TRUE):
  1. Submitting a project goal triggers the Overseer to produce a decomposed task list
  2. Each task in the decomposed list is executed by the appropriate specialist agent (developer, QA, devops, etc.)
  3. The workflow runs all tasks through to completion without pausing for approval on medium-risk steps
  4. The workflow pauses and sends an approval request only when reaching the final deployment step
  5. The operator can approve or reject the deployment via the Approval UI and the workflow proceeds or halts accordingly
**Plans**: TBD

### Phase 4: RAG Ingestion Deduplication
**Goal**: The ingestion service remembers which documents it has already processed across restarts so it never creates duplicate embeddings
**Depends on**: Nothing (independent of Phases 1-3)
**Requirements**: RAG-01, RAG-02
**Success Criteria** (what must be TRUE):
  1. After ingesting a document and restarting the ingestion service, the document is not re-embedded
  2. Dropping a new document after restart causes only that new document to be ingested
  3. The Qdrant collection does not accumulate duplicate vectors for the same document content after multiple restarts
**Plans**: TBD

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Agent LLM Routing | 0/TBD | Not started | - |
| 2. Real Collaboration | 0/TBD | Not started | - |
| 3. Project Pipeline and Approval Gates | 0/TBD | Not started | - |
| 4. RAG Ingestion Deduplication | 0/TBD | Not started | - |

---
*Roadmap created: 2026-03-05*
*Milestone: v0.1 First Working Build*
