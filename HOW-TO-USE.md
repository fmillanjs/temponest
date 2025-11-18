# How to Use TempoNest - Practical Guide

## ✅ System Status
All services are running! 18 containers healthy, 7 agents ready.

---

## 🚀 Three Ways to Use TempoNest

### Method 1: Using the CLI (Recommended for Beginners)

The CLI tool makes it easy to work with agents.

#### Setup (One-time)
```bash
# Make the CLI easily accessible
alias agentic='/home/doctor/temponest/cli/agentic-cli.sh'

# Or add to your .bashrc permanently:
echo "alias agentic='/home/doctor/temponest/cli/agentic-cli.sh'" >> ~/.bashrc
source ~/.bashrc
```

#### Basic Commands
```bash
# Check system status
agentic status

# Initialize a new project
agentic init my-first-project
cd ~/agentic-projects/my-first-project

# Ask Overseer to plan a project
agentic plan "Build a REST API for managing tasks with FastAPI"

# Ask Developer to write code
agentic develop "Create a FastAPI endpoint for user registration with email validation"

# Ask Designer for UI mockups
agentic design "Create a modern login page with email/password fields"

# Ask QA to write tests
agentic test "Write pytest tests for the user registration endpoint"

# Ask DevOps to create deployment config
agentic deploy "Create Docker configuration for FastAPI app with PostgreSQL"

# Ask Security Auditor to check for issues
agentic audit

# Ask UX Researcher for user insights
agentic research "Create user personas for a task management app"
```

---

### Method 2: Direct API Calls (For Advanced Users)

If you want direct control, you can call the APIs directly.

#### Step 1: Create a User Account
```bash
# Register a new user
curl -X POST http://localhost:9002/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "yourpassword",
    "full_name": "Your Name"
  }'
```

#### Step 2: Login and Get Token
```bash
# Login
TOKEN=$(curl -X POST http://localhost:9002/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "yourpassword"
  }' | jq -r '.access_token')

# Save token for reuse
echo $TOKEN > ~/.temponest-token
```

#### Step 3: Call Agents

**Overseer Agent (Planning):**
```bash
curl -X POST http://localhost:9000/overseer/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Plan a REST API for a blog platform with posts, comments, and users",
    "context": {
      "framework": "FastAPI",
      "database": "PostgreSQL"
    },
    "idempotency_key": "blog-plan-001"
  }' | jq '.'
```

**Developer Agent (Code Generation):**
```bash
curl -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a Python function to validate email addresses using regex",
    "context": {
      "language": "Python",
      "include_tests": true,
      "style": "PEP 8"
    },
    "idempotency_key": "email-validation-001"
  }' | jq '.result'
```

**Designer Agent (UI/UX):**
```bash
curl -X POST http://localhost:9000/designer/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Design a pricing page with 3 tiers: Starter, Pro, Enterprise",
    "context": {
      "style": "modern SaaS",
      "brand_colors": "blue and white",
      "include_comparison_table": true
    },
    "idempotency_key": "pricing-page-001"
  }' | jq '.result'
```

**QA Tester Agent (Testing):**
```bash
curl -X POST http://localhost:9000/qa-tester/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write pytest tests for a user authentication endpoint",
    "context": {
      "framework": "pytest",
      "endpoint": "POST /auth/login",
      "test_cases": ["valid credentials", "invalid password", "non-existent user"]
    },
    "idempotency_key": "auth-tests-001"
  }' | jq '.result'
```

**DevOps Agent (Infrastructure):**
```bash
curl -X POST http://localhost:9000/devops/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a Dockerfile for a FastAPI application",
    "context": {
      "base_image": "python:3.11-slim",
      "requirements": ["fastapi", "uvicorn", "sqlalchemy"],
      "production_ready": true
    },
    "idempotency_key": "dockerfile-001"
  }' | jq '.result'
```

**Security Auditor Agent:**
```bash
curl -X POST http://localhost:9000/security-auditor/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Audit this authentication code for security vulnerabilities",
    "context": {
      "code": "def login(username, password):\n    query = f\"SELECT * FROM users WHERE username='{username}'\"\n    ...",
      "focus": "SQL injection, password handling"
    },
    "idempotency_key": "security-audit-001"
  }' | jq '.result'
```

**UX Researcher Agent:**
```bash
curl -X POST http://localhost:9000/ux-researcher/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a user persona for a small business owner using project management software",
    "context": {
      "industry": "retail",
      "company_size": "5-20 employees",
      "tech_savviness": "medium"
    },
    "idempotency_key": "persona-001"
  }' | jq '.result'
```

---

### Method 3: Using the Web UI

#### Access the Dashboard
Open your browser to: **http://localhost:8082**

The Web UI provides:
- Visual workflow builder
- Agent execution history
- Cost tracking dashboard
- Real-time metrics
- Project management

---

## 📊 Monitor Your Work

### Grafana Dashboards (Metrics)
- URL: http://localhost:3003
- Login: admin / admin
- Dashboards: Agent Performance, Cost Tracking, System Health

### Langfuse (LLM Tracing)
- URL: http://localhost:3001
- Track every LLM call, tokens used, and costs

### Temporal UI (Workflows)
- URL: http://localhost:8080
- View workflow executions and history

### Qdrant (Vector Database)
- URL: http://localhost:6333/dashboard
- Manage your RAG documents

---

## 🎓 Your First Real Project

Let's build something together. Here's a complete example:

### Example: Build a Contact Form API

```bash
# 1. Initialize project
mkdir -p ~/projects/contact-form-api
cd ~/projects/contact-form-api

# 2. Get auth token
TOKEN=$(curl -X POST http://localhost:9002/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "builder@example.com",
    "password": "securepass123",
    "full_name": "Builder"
  }' 2>/dev/null | jq -r '.access_token')

# If registration fails (user exists), login instead:
TOKEN=$(curl -X POST http://localhost:9002/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "builder@example.com",
    "password": "securepass123"
  }' 2>/dev/null | jq -r '.access_token')

# 3. Plan the project
curl -X POST http://localhost:9000/overseer/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Plan a REST API for contact form submissions with email notifications",
    "context": {
      "framework": "FastAPI",
      "database": "PostgreSQL",
      "email_service": "SendGrid"
    },
    "idempotency_key": "contact-form-plan"
  }' | jq '.result.plan' > plan.json

# 4. Generate the database models
curl -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create SQLAlchemy models for contact form submissions table with fields: id, name, email, message, created_at",
    "context": {
      "orm": "SQLAlchemy",
      "database": "PostgreSQL"
    },
    "idempotency_key": "contact-models"
  }' | jq -r '.result' > models.py

# 5. Generate the API endpoints
curl -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create FastAPI endpoints for contact form: POST /contact (create), GET /contact (list), GET /contact/{id} (get one)",
    "context": {
      "framework": "FastAPI",
      "validation": "Pydantic",
      "include_error_handling": true
    },
    "idempotency_key": "contact-endpoints"
  }' | jq -r '.result' > api.py

# 6. Generate tests
curl -X POST http://localhost:9000/qa-tester/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write pytest tests for contact form API endpoints",
    "context": {
      "framework": "pytest",
      "endpoints": ["POST /contact", "GET /contact", "GET /contact/{id}"],
      "include_fixtures": true
    },
    "idempotency_key": "contact-tests"
  }' | jq -r '.result' > test_api.py

# 7. Security audit
curl -X POST http://localhost:9000/security-auditor/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Audit the contact form API for security issues",
    "context": {
      "focus": "input validation, SQL injection, rate limiting, email validation"
    },
    "idempotency_key": "contact-security"
  }' | jq '.result'

# 8. Create deployment config
curl -X POST http://localhost:9000/devops/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create Docker Compose configuration for FastAPI app with PostgreSQL",
    "context": {
      "services": ["fastapi", "postgres"],
      "include_nginx": true,
      "production_ready": true
    },
    "idempotency_key": "contact-docker"
  }' | jq -r '.result' > docker-compose.yml

echo "✓ Project generated! Check the files in $(pwd)"
```

---

## 💡 Pro Tips

### 1. Use Idempotency Keys
Always provide unique `idempotency_key` to avoid re-running the same task:
```json
"idempotency_key": "my-unique-task-id-001"
```

### 2. Provide Context
The more context you give, the better the output:
```json
"context": {
  "framework": "FastAPI",
  "database": "PostgreSQL",
  "authentication": "JWT",
  "style": "clean, production-ready",
  "include_tests": true
}
```

### 3. Iterate on Results
If the output isn't perfect, refine your prompt and try again with a new idempotency key.

### 4. Review Everything
**Always review agent-generated code before using it in production.**

### 5. Choose Your LLM Provider

TempoNest supports multiple LLM providers. Choose based on your needs:

#### Option A: Ollama (Default - Free, Local)
```bash
# Already configured by default
OVERSEER_PROVIDER=ollama
DEVELOPER_PROVIDER=ollama
```
- **Cost:** Free
- **Speed:** Moderate (depends on hardware)
- **Quality:** Good for development, testing

#### Option B: Claude API (Production - Pay-per-Token)
```bash
# Edit docker/.env
DEVELOPER_PROVIDER=claude
CLAUDE_SESSION_TOKEN=sk-ant-your-api-key-here
# Then restart: docker-compose restart agents
```
- **Cost:** ~$3/1M input tokens, ~$15/1M output tokens
- **Speed:** Fast (API)
- **Quality:** Excellent for production

#### Option C: Claude Code CLI (Subscription - Use Your Claude Code License)
```bash
# Edit docker/.env
DEVELOPER_PROVIDER=claude-code
CLAUDE_CODE_TOKEN=your-claude-code-token

# Get your token from ~/.claude/config.json after running 'claude login'
# Or from your Claude Code subscription dashboard
```
- **Cost:** Included with Claude Pro ($17/mo) or Claude Max ($200/mo)
- **Speed:** Slower (subprocess overhead ~2-5s per call)
- **Quality:** Excellent (same as Claude API)
- **Limitations:**
  - Subprocess overhead adds latency
  - Subject to subscription rate limits
  - No exact token counting
  - Best for development/testing with existing subscription

**How to get Claude Code token:**
```bash
# 1. Install Claude Code CLI (if not in Docker)
npm install -g @anthropic-ai/claude-code

# 2. Login with your subscription
claude login

# 3. Extract token from config
cat ~/.claude/config.json | jq -r '.sessionToken'

# 4. Add to docker/.env
echo "CLAUDE_CODE_TOKEN=<your-token>" >> docker/.env

# 5. Restart services
cd docker && docker-compose restart agents
```

**When to use Claude Code CLI:**
- ✅ You already have a Claude Pro/Max subscription
- ✅ Development and testing workloads
- ✅ Want to avoid per-token API costs
- ❌ Production with high request volume (use API instead)
- ❌ Need streaming responses or minimal latency

#### Option D: OpenAI GPT-4
```bash
# Edit docker/.env
DEVELOPER_PROVIDER=openai
OPENAI_API_KEY=sk-your-openai-key
```
- **Cost:** ~$10/1M tokens
- **Speed:** Fast (API)
- **Quality:** Excellent

**After changing provider, restart agents:**
```bash
cd ~/temponest/docker
docker-compose restart agents
```

---

## 🔧 Troubleshooting

### If agents aren't responding:
```bash
# Check service health
curl http://localhost:9000/health

# Check logs
docker logs agentic-agents --tail 50

# Restart if needed
cd ~/temponest/docker
docker-compose restart agents
```

### If you get authentication errors:
```bash
# Register a new user
curl -X POST http://localhost:9002/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"new@example.com","password":"pass123","full_name":"Name"}'
```

### If models are slow:
- Ollama models (current setup) are slower but free
- For faster responses, switch to Claude or GPT-4 in `.env`

---

## 📚 Next Steps

1. **Try the examples above** - Run the Contact Form API project
2. **Read the workflows** - Check `/docs/agentic-workflows/` for complete workflows
3. **Check the templates** - `/docs/quick-reference/project-templates.md`
4. **Build something real** - Use it for a personal project or client work

---

## 🎯 Common Use Cases

**For Client Projects:**
- REST APIs for web/mobile apps
- Admin dashboards
- Landing pages
- Database design
- Security audits

**For SaaS Development:**
- MVP backend development
- UI/UX design
- User research
- Testing automation
- DevOps setup

**For Learning:**
- Generate example code
- Create boilerplate projects
- Get security best practices
- Design pattern examples

---

## 💰 Cost Tracking

Every agent call is tracked. Check costs:
```bash
# Via Web UI
open http://localhost:8082

# Via Grafana
open http://localhost:3003

# Via API
curl -H "Authorization: Bearer $TOKEN" http://localhost:9000/costs/summary
```

**Cost by Provider:**

| Provider | Cost Model | Typical Cost per Call | Best For |
|----------|------------|----------------------|----------|
| **Ollama** | Free (local) | $0 | Development, testing, learning |
| **Claude Code CLI** | Subscription | $0 (included) | Development if you have Claude Pro/Max |
| **Claude API** | Pay-per-token | $0.01-0.05 | Production, high volume |
| **OpenAI GPT-4** | Pay-per-token | $0.03-0.10 | Production, high quality |

**Detailed Costs:**
- **Ollama:** Free, runs locally
- **Claude Code CLI:** $17/mo (Pro) or $200/mo (Max) subscription, subject to rate limits
- **Claude API:** $3/1M input + $15/1M output tokens
- **OpenAI:** $10/1M tokens

**Note:** Claude Code CLI uses your subscription, which may have weekly usage caps. For high-volume production use, the API is more cost-effective and reliable

---

**You're ready to build! Start with the Contact Form API example above.**
