# Agentic Company Platform

A production-ready multi-agent platform with human-in-the-loop approvals, durable workflows, and RAG-powered AI agents.

## Overview

The Agentic Company platform enables you to build and run autonomous AI agents that can:

- **Decompose complex goals** into concrete, executable tasks (Overseer Agent)
- **Generate production code** for APIs, database schemas, and UI components (Developer Agent)
- **Request human approval** for risky operations via Telegram or Web UI
- **Ground all outputs** in documentation with ≥2 citations (RAG)
- **Track and trace** all LLM calls with costs and latency (Langfuse)
- **Run durably** with retries and fault tolerance (Temporal)

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Telegram  │────▶│  Approval UI │────▶│  Temporal   │
│     Bot     │     │   (FastAPI)  │     │  Workflows  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                     │
                            ▼                     ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│    n8n      │────▶│   PostgreSQL │◀────│   Agents    │
│  Workflows  │     │   (DB + Jobs)│     │  (CrewAI)   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                  │
                    ┌──────────────┐              │
                    │   Qdrant     │◀─────────────┤
                    │   (Vectors)  │              │
                    └──────────────┘              │
                                                  ▼
                    ┌──────────────┐     ┌─────────────┐
                    │   Ollama     │◀────│  Langfuse   │
                    │   (Models)   │     │  (Tracing)  │
                    └──────────────┘     └─────────────┘
```

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose
- 8GB+ RAM recommended
- ~10GB disk space for models

### 1. Clone and Setup

```bash
# Run automated setup
./infra/scripts/setup.sh
```

This will:
- Start all Docker services
- Pull Ollama models (mistral:7b-instruct, qwen2.5-coder:7b, nomic-embed-text)
- Initialize databases
- Wait for services to be healthy

### 2. Configure Environment

Edit `docker/.env`:

```bash
# Required
TELEGRAM_BOT_TOKEN=<from @BotFather>
LANGFUSE_PUBLIC_KEY=<from http://localhost:3000>
LANGFUSE_SECRET_KEY=<from http://localhost:3000>

# Optional (defaults provided)
POSTGRES_PASSWORD=change-me
BUDGET_TOKENS_PER_TASK=8000
LATENCY_SLO_MS=5000
```

### 3. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Temporal UI | http://localhost:8080 | None |
| Langfuse | http://localhost:3000 | Sign up on first visit |
| Approval UI | http://localhost:9001 | None |
| n8n | http://localhost:5678 | admin/admin (change in .env) |
| Open WebUI | http://localhost:8081 | Sign up on first visit |
| Qdrant | http://localhost:6333/dashboard | None |

## Usage

### Example 1: Create a New Project

```python
from temporalio.client import Client

# Connect to Temporal
client = await Client.connect("localhost:7233")

# Start workflow
result = await client.start_workflow(
    "ProjectPipelineWorkflow",
    args=[{
        "goal": "Create a user management API with CRUD operations",
        "context": {
            "database": "postgresql",
            "framework": "fastapi"
        },
        "requester": "alice@example.com",
        "idempotency_key": "project-users-001"
    }],
    id="user-mgmt-project",
    task_queue="agentic-task-queue"
)

# Wait for result
output = await result.result()
print(output)
```

**What happens:**

1. **Overseer decomposes** the goal into tasks (schema, API, tests)
2. **Approval requested** (Web UI + Telegram) for each medium/high risk task
3. **Human approves** via Telegram or web interface
4. **Developer generates** code with tests
5. **Validation** ensures ≥2 citations and complete implementation
6. **Deployment approval** requested (high risk, requires 2 approvers)
7. **Deploy** when approved

### Example 2: Direct Agent Invocation

```bash
# Overseer: Decompose a goal
curl -X POST http://localhost:9000/overseer/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Design a notification system",
    "context": {},
    "idempotency_key": "notif-design-001",
    "risk_level": "low"
  }'

# Developer: Generate code
curl -X POST http://localhost:9000/developer/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a PostgreSQL schema for users table",
    "context": {"columns": ["id", "name", "email", "created_at"]},
    "idempotency_key": "users-schema-001",
    "risk_level": "medium"
  }'
```

### Example 3: Add Documents for RAG

```bash
# Copy your documentation to the watched directory
cp docs/*.md docker/documents/

# Ingestion service will automatically:
# 1. Extract text
# 2. Chunk into 512-token pieces
# 3. Generate embeddings
# 4. Store in Qdrant
```

Check ingestion logs:
```bash
docker logs -f agentic-ingestion
```

## Approval Matrix

| Risk Level | Auto-Approve | Required Approvers | Timeout |
|------------|-------------|-------------------|---------|
| **Low** (docs, drafts) | ✅ Yes | 0 | N/A |
| **Medium** (code gen, schema) | ❌ No | 1 | 24h |
| **High** (deploy, billing) | ❌ No | 2 | 24h |

**Examples:**
- Low: Write README, create PR draft, read-only queries
- Medium: Generate API endpoint, create migration, dev deploy
- High: Production deploy, process refund, modify pricing, data migration

## Guardrails & Policies

### 1. Budget Enforcement

```python
# Each task limited to 8000 tokens (configurable)
BUDGET_TOKENS_PER_TASK=8000

# If exceeded, agent degrades context or asks human
```

### 2. RAG Grounding

```python
# ALL agent outputs require ≥2 citations
citations = result.get("citations", [])
if len(citations) < 2:
    raise ValueError("Insufficient grounding")

# Citations must meet score threshold
if any(c["score"] < 0.7 for c in citations[:2]):
    raise ValueError("Low confidence citations")
```

### 3. Latency SLO

```python
# Target: 5000ms (configurable)
LATENCY_SLO_MS=5000

# If violated, logged and traced in Langfuse
```

### 4. Idempotency

```python
# All mutations accept idempotency_key
{
    "task": "...",
    "idempotency_key": "unique-operation-id"
}

# Duplicate calls return cached result
```

### 5. Deterministic Outputs

```python
# Fixed model parameters
MODEL_SEED=42
MODEL_TEMPERATURE=0.2  # Low for reproducibility
MODEL_TOP_P=0.9
```

## Development

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific test suite
pytest tests/rag/test_rag_retrieval.py -v
pytest tests/workflows/test_project_pipeline.py -v
pytest tests/agents/test_agent_execution.py -v

# With coverage
pytest tests/ --cov=services --cov-report=html
```

### View Logs

```bash
# All services
docker-compose -f docker/docker-compose.yml logs -f

# Specific service
docker logs -f agentic-agents
docker logs -f agentic-temporal-workers
docker logs -f agentic-ingestion
```

### Restart Services

```bash
cd docker
docker-compose restart agents
docker-compose restart temporal-workers
```

### Access Databases

```bash
# PostgreSQL
docker exec -it agentic-postgres psql -U postgres -d approvals

# Check approval requests
SELECT id, task_description, risk_level, status, created_at
FROM approval_requests
ORDER BY created_at DESC
LIMIT 10;
```

## Configuration

### Environment Variables

See `docker/.env.example` for all options. Key settings:

**Models:**
```bash
CHAT_MODEL=mistral:7b-instruct        # Overseer conversations
CODE_MODEL=qwen2.5-coder:7b           # Developer code generation
EMBEDDING_MODEL=nomic-embed-text      # RAG embeddings
```

**Guardrails:**
```bash
BUDGET_TOKENS_PER_TASK=8000          # Max tokens per task
LATENCY_SLO_MS=5000                   # Latency target
RAG_TOP_K=5                           # Retrieval count
RAG_MIN_SCORE=0.7                     # Min similarity
```

**Approvals:**
```bash
ENABLE_TELEGRAM_APPROVALS=true
ENABLE_WEB_APPROVALS=true
APPROVAL_TIMEOUT_HOURS=24
```

## Telegram Bot Setup

1. **Create bot** with @BotFather on Telegram
2. **Get token** and add to `docker/.env`
3. **Import n8n workflow:**
   - Open http://localhost:5678
   - Import `services/n8n/telegram-approval-workflow.json`
   - Add Telegram credentials
4. **Test:** Start a workflow and check for Telegram notification

## Monitoring & Observability

### Langfuse (LLM Tracing)

- **URL:** http://localhost:3000
- **Features:**
  - Every LLM call traced with input/output
  - RAG citations attached to spans
  - Token counts and costs
  - Latency breakdown

### Temporal (Workflow Execution)

- **URL:** http://localhost:8080
- **Features:**
  - View running/completed workflows
  - Inspect workflow history
  - Retry failed activities
  - Send signals to workflows

### Metrics Endpoint

```bash
curl http://localhost:9000/metrics

# Returns:
{
  "idempotency_cache_size": 42,
  "rag_collection_size": 1543,
  "langfuse_traces": 89
}
```

## Troubleshooting

### Ollama models not loading

```bash
# Check Ollama service
docker logs agentic-ollama

# Manually pull models
docker exec -it agentic-ollama ollama pull mistral:7b-instruct
docker exec -it agentic-ollama ollama pull qwen2.5-coder:7b
docker exec -it agentic-ollama ollama pull nomic-embed-text

# Verify
docker exec -it agentic-ollama ollama list
```

### Agent returns "Insufficient grounding"

```bash
# Add more documents to RAG
cp your-docs/* docker/documents/

# Check Qdrant collection size
curl http://localhost:6333/collections/agentic_knowledge

# View ingestion logs
docker logs -f agentic-ingestion
```

### Workflow stuck "pending approval"

```bash
# Check approval UI
open http://localhost:9001

# Or approve via API
curl -X POST http://localhost:9001/api/approvals/<approval-id>/approve \
  -F "approver=your-name" \
  -F "reason=Looks good"
```

### High latency / timeout

```bash
# Check if models are cached
docker exec -it agentic-ollama ollama list

# Increase SLO
# In docker/.env:
LATENCY_SLO_MS=10000

# Or reduce task complexity
BUDGET_TOKENS_PER_TASK=4000
```

## Security

### Secret Detection

Pre-commit hook blocks commits with:
- `.pem` files
- AWS keys (`AKIA...`)
- Private keys (`-----BEGIN`)
- Passwords (`password=`)
- `.env` files (except `.env.example`)

Install:
```bash
./infra/scripts/install-hooks.sh
```

### Best Practices

1. **Never commit secrets** - use `.env` (gitignored)
2. **Change default passwords** in `docker/.env`
3. **Use HTTPS** in production (add nginx/traefik)
4. **Restrict approval UI** to internal network
5. **Audit logs** stored in `audit_log` table

## Architecture Decisions

### Why CrewAI?

- Task-oriented framework
- Built-in role delegation
- Sequential/hierarchical execution
- Better for structured, repeatable workflows

### Why Temporal?

- Durable execution (survives restarts)
- Built-in retries
- Human-in-the-loop via signals
- Excellent observability

### Why Ollama (local models)?

- Zero cloud costs
- Data privacy
- Fixed performance (no rate limits)
- Reproducible with seeds

### Why Qdrant?

- Fast vector search
- Simple deployment
- Good metadata filtering
- Open source

## Cost Analysis

**Infrastructure (local):**
- $0/month (runs on your hardware)
- ~8GB RAM for all services
- ~50GB disk (with models)

**Scaling to cloud:**
- Models: Keep local (Ollama on EC2/GCP)
- Data: Qdrant Cloud (~$40/month)
- Temporal: Temporal Cloud (~$200/month) or self-host
- Postgres: RDS (~$50/month)

**Total cloud cost estimate: $300-500/month**

## Roadmap

- [ ] Additional agents (QA Tester, DevOps, Designer)
- [ ] Web-based workflow builder
- [ ] Cost tracking per project
- [ ] Multi-tenant support
- [ ] Kubernetes deployment
- [ ] OpenTelemetry integration
- [ ] Slack integration (in addition to Telegram)

## Contributing

See `CONTRIBUTING.md` for guidelines.

## License

MIT License - see `LICENSE` file.

## Support

- **Issues:** https://github.com/your-org/agentic-company/issues
- **Docs:** https://docs.agentic-company.dev
- **Discord:** https://discord.gg/agentic-company

---

Built with ❤️ using CrewAI, Temporal, Qdrant, and Ollama.
