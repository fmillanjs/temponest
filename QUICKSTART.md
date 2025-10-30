# Quick Start Guide - Agentic Company Platform

Get up and running in 10 minutes.

## Prerequisites

- Docker and Docker Compose installed
- 8GB RAM minimum
- ~10GB free disk space

## Step 1: Setup (5 minutes)

```bash
# Run automated setup
./infra/scripts/setup.sh
```

This will:
- Start all services
- Pull AI models (~4GB)
- Initialize databases
- Wait for health checks

## Step 2: Configure (2 minutes)

### Get Langfuse Keys

1. Open http://localhost:3000
2. Sign up for a new account
3. Go to Settings → API Keys
4. Copy Public Key and Secret Key

### Update Environment

Edit `docker/.env`:

```bash
# Required
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxx

# Optional (for Telegram approvals)
TELEGRAM_BOT_TOKEN=<from @BotFather>
```

Restart services:
```bash
cd docker
docker-compose restart agents temporal-workers
```

## Step 3: Test (3 minutes)

### 3.1 Test Agent Directly

```bash
# Test Overseer (goal decomposition)
curl -X POST http://localhost:9000/overseer/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Design a REST API for managing blog posts",
    "context": {"framework": "FastAPI"},
    "idempotency_key": "test-001",
    "risk_level": "low"
  }'
```

Expected response:
```json
{
  "task_id": "...",
  "status": "completed",
  "result": {
    "plan": [...],
    "citations": [
      {"source": "...", "version": "1.0", "score": 0.85},
      {"source": "...", "version": "1.0", "score": 0.78}
    ]
  },
  "tokens_used": 450,
  "latency_ms": 2341
}
```

### 3.2 Add Sample Documents

```bash
# Create a sample doc
cat > docker/documents/api-guide.md << 'EOF'
# API Development Guide

## FastAPI Best Practices

Use FastAPI for modern REST APIs:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    description: str

@app.post("/items")
async def create_item(item: Item):
    return {"id": 1, **item.dict()}
```

Always include:
- Request validation with Pydantic
- Proper error handling
- OpenAPI documentation
EOF

# Wait 10 seconds for ingestion
sleep 10

# Check ingestion
docker logs agentic-ingestion | tail -20
```

### 3.3 Test RAG Retrieval

```bash
# Now query should return citations
curl -X POST http://localhost:9000/overseer/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a FastAPI endpoint for items",
    "context": {},
    "idempotency_key": "test-002",
    "risk_level": "low"
  }'
```

Should now include citations from `api-guide.md`.

### 3.4 Start a Workflow

```python
# save as test_workflow.py
import asyncio
from temporalio.client import Client

async def main():
    client = await Client.connect("localhost:7233")

    result = await client.execute_workflow(
        "ProjectPipelineWorkflow",
        args=[{
            "goal": "Create a simple user API",
            "context": {"database": "postgresql"},
            "requester": "test@example.com",
            "idempotency_key": "workflow-test-001"
        }],
        id="test-workflow-1",
        task_queue="agentic-task-queue"
    )

    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

Run:
```bash
pip install temporalio
python test_workflow.py
```

Check progress:
- Temporal UI: http://localhost:8080
- Approval UI: http://localhost:9001

## Common Issues

### "No citations found"

Add documents to `docker/documents/`:
```bash
cp your-docs/*.md docker/documents/
```

### "Service unhealthy"

Check logs:
```bash
docker logs agentic-agents
docker logs agentic-qdrant
docker logs agentic-ollama
```

### "Models not loaded"

Pull manually:
```bash
docker exec -it agentic-ollama ollama pull mistral:7b-instruct
docker exec -it agentic-ollama ollama pull qwen2.5-coder:7b
docker exec -it agentic-ollama ollama pull nomic-embed-text
```

## Next Steps

1. **Read full README.md** for architecture details
2. **Configure Telegram bot** for mobile approvals
3. **Import n8n workflow** for notifications
4. **Run tests**: `pytest tests/ -v`
5. **Customize agents** in `services/agents/app/agents/`

## Support

- Issues: GitHub Issues
- Logs: `docker-compose logs -f`
- Health: http://localhost:9000/health

Happy building! 🚀
