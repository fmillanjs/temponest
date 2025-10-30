# Claude Code Integration Guide

This guide explains how to configure the Agentic Company platform to use Claude models for code generation via the Developer agent.

## Overview

The platform supports **three LLM providers** for each agent:
- **Ollama** - Local models (free, no API keys needed)
- **Claude** - Anthropic's Claude models via API
- **OpenAI** - OpenAI models via API

You can mix and match providers per agent. For example:
- Overseer: Ollama (local, free)
- Developer: Claude (cloud, high quality code generation)

## Provider Configuration

Edit `docker/.env`:

```bash
# Choose provider for each agent
OVERSEER_PROVIDER=ollama        # or claude, openai
DEVELOPER_PROVIDER=claude       # or ollama, openai
```

## Claude Authentication Methods

Claude Code integration supports **three authentication methods**:

### Method 1: URL-Based Authentication (Recommended)

This method is similar to how opencode.ai connects to Claude Code.

**Setup:**

1. **Get authentication URL** from your Claude Code setup
2. **Add to docker/.env**:

```bash
CLAUDE_AUTH_URL=https://your-auth-service.com/api/auth
```

**How it works:**
- The platform calls the auth URL on startup
- Auth URL returns a session token
- Token is used for all subsequent API calls

**Expected auth URL response:**
```json
{
  "token": "session-token-here",
  "expires_at": "2025-11-01T00:00:00Z"
}
```

### Method 2: Direct Session Token

If you already have a session token from your auth service:

```bash
CLAUDE_SESSION_TOKEN=your-session-token-here
```

### Method 3: Anthropic API Key

If you have a standard Anthropic API key:

```bash
CLAUDE_SESSION_TOKEN=sk-ant-api03-xxxxxxxxxx
```

## Complete Claude Configuration

Edit `docker/.env`:

```bash
# =============================================================================
# PROVIDER SELECTION
# =============================================================================
OVERSEER_PROVIDER=ollama
DEVELOPER_PROVIDER=claude

# =============================================================================
# CLAUDE CONFIGURATION
# =============================================================================
# Choose ONE of these authentication methods:

# Option 1: URL-based auth (recommended)
CLAUDE_AUTH_URL=https://your-auth-service.com/api/auth

# Option 2: Direct token
# CLAUDE_SESSION_TOKEN=your-token-here

# Option 3: Anthropic API key
# CLAUDE_SESSION_TOKEN=sk-ant-api03-xxxxxxxxxx

# Claude API endpoint (default is fine)
CLAUDE_API_URL=https://api.anthropic.com/v1/messages

# Models to use
CLAUDE_CHAT_MODEL=claude-sonnet-4-20250514
CLAUDE_CODE_MODEL=claude-sonnet-4-20250514

# =============================================================================
# MODEL PARAMETERS
# =============================================================================
MODEL_TEMPERATURE=0.2
MODEL_TOP_P=0.9
MODEL_MAX_TOKENS=4096
MODEL_SEED=42
```

## Testing Claude Integration

### 1. Start the platform

```bash
cd docker
docker-compose up -d
```

### 2. Check health endpoint

```bash
curl http://localhost:9000/health | jq
```

Expected output:
```json
{
  "status": "healthy",
  "services": {
    "qdrant": "healthy",
    "langfuse": "healthy",
    "overseer": "ready",
    "developer": "ready"
  },
  "models": {
    "overseer_provider": "ollama",
    "overseer_model": "mistral:7b-instruct",
    "developer_provider": "claude",
    "developer_model": "claude-sonnet-4-20250514",
    "embedding": "nomic-embed-text"
  }
}
```

### 3. Test Developer agent

```bash
curl -X POST http://localhost:9000/developer/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a FastAPI endpoint for user registration",
    "context": {"database": "postgresql"},
    "idempotency_key": "test-claude-001",
    "risk_level": "medium"
  }' | jq
```

## Switching Models

You can easily switch models for each agent:

**Example: Use different Claude models**

```bash
# Overseer: Claude Haiku (faster, cheaper)
OVERSEER_PROVIDER=claude
CLAUDE_CHAT_MODEL=claude-haiku-3-20240307

# Developer: Claude Opus (highest quality)
DEVELOPER_PROVIDER=claude
CLAUDE_CODE_MODEL=claude-opus-3-20240229
```

**Example: Mix providers**

```bash
# Overseer: Local Ollama (free)
OVERSEER_PROVIDER=ollama
OLLAMA_CHAT_MODEL=mistral:7b-instruct

# Developer: Claude Sonnet (best balance)
DEVELOPER_PROVIDER=claude
CLAUDE_CODE_MODEL=claude-sonnet-4-20250514
```

## Available Claude Models

| Model | Best For | Speed | Cost |
|-------|----------|-------|------|
| `claude-opus-3-20240229` | Highest quality code | Slow | High |
| `claude-sonnet-4-20250514` | **Balanced** (recommended) | Medium | Medium |
| `claude-haiku-3-20240307` | Fast responses | Fast | Low |

## Troubleshooting

### "Authentication failed"

**Check:**
1. Is `CLAUDE_AUTH_URL` reachable?
   ```bash
   curl https://your-auth-service.com/api/auth
   ```

2. Does it return valid JSON with `token` field?

3. Is the token still valid (not expired)?

**Solution:**
- Verify auth URL is correct
- Check auth service logs
- Try Method 2 (direct token) to isolate auth issues

### "Claude API error: 401 Unauthorized"

**Possible causes:**
- Invalid API key or session token
- Expired session token
- Wrong API endpoint

**Solution:**
```bash
# Test auth manually
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $CLAUDE_SESSION_TOKEN" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### "Developer agent returns errors"

**Check logs:**
```bash
docker logs -f agentic-agents
```

**Common issues:**
- Auth not configured: Set `CLAUDE_AUTH_URL` or `CLAUDE_SESSION_TOKEN`
- Wrong model name: Check available models above
- Rate limit exceeded: Add delays or reduce `DEVELOPER_CPM`

### "High latency / timeout"

**Adjust settings:**
```bash
# Increase timeout
LATENCY_SLO_MS=15000

# Reduce max tokens
MODEL_MAX_TOKENS=2048

# Use faster model
CLAUDE_CODE_MODEL=claude-haiku-3-20240307
```

## Cost Optimization

### Use Claude selectively

```bash
# Overseer: Free local model
OVERSEER_PROVIDER=ollama

# Developer: Claude only (pay per use)
DEVELOPER_PROVIDER=claude
```

### Reduce token usage

```bash
# Lower max tokens
MODEL_MAX_TOKENS=2048

# Stricter budget per task
BUDGET_TOKENS_PER_TASK=4000

# Fewer RAG results
RAG_TOP_K=3
```

### Monitor costs

Check Langfuse dashboard (http://localhost:3000):
- View total tokens used
- Track costs per task
- Identify expensive operations

## Advanced: Custom Auth Service

If you're building your own auth service (like opencode.ai), it should:

1. **Accept GET request** to `/api/auth`
2. **Return JSON** with:
   ```json
   {
     "token": "session-token-or-api-key",
     "expires_at": "2025-11-01T00:00:00Z"
   }
   ```

3. **Support CORS** for browser access (optional)

**Example auth service (Python/FastAPI):**

```python
from fastapi import FastAPI
from datetime import datetime, timedelta

app = FastAPI()

@app.get("/api/auth")
async def get_auth():
    return {
        "token": "sk-ant-api03-your-key-here",
        "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
    }
```

## Security Best Practices

1. **Never commit API keys**
   - Use .env (gitignored)
   - Pre-commit hooks block secrets

2. **Rotate tokens regularly**
   - Update `CLAUDE_SESSION_TOKEN` monthly
   - Monitor for unauthorized usage

3. **Use rate limits**
   ```bash
   DEVELOPER_CPM=30  # Max 30 calls per minute
   ```

4. **Enable cost tracking**
   ```bash
   ENABLE_COST_TRACKING=true
   ```

## Support

- **Platform issues**: Check logs with `docker logs -f agentic-agents`
- **Claude API docs**: https://docs.anthropic.com/
- **Cost calculator**: https://anthropic.com/pricing

---

**Quick Start Summary:**

1. Edit `docker/.env`:
   ```bash
   DEVELOPER_PROVIDER=claude
   CLAUDE_SESSION_TOKEN=your-token-here
   ```

2. Restart services:
   ```bash
   docker-compose restart agents
   ```

3. Test:
   ```bash
   curl http://localhost:9000/health | jq .models
   ```

Done! Your Developer agent now uses Claude Code. 🚀
