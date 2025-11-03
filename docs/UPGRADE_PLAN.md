# Agentic Company Platform - Comprehensive Upgrade Plan

## Overview

This document outlines the implementation plan for upgrading the Agentic Company Platform to production-grade enterprise readiness.

## Phase 1: Critical Security (Week 1)

### 1.1 Authentication & Authorization

**Architecture:**
- JWT-based authentication for user sessions
- API Key authentication for service-to-service communication
- Role-Based Access Control (RBAC) with permissions
- Tenant-scoped tokens

**Implementation:**
```
services/
├── auth/
│   ├── main.py                 # Auth service (FastAPI)
│   ├── models.py               # User, Role, Permission models
│   ├── jwt_handler.py          # JWT encode/decode
│   ├── api_key_handler.py      # API key validation
│   └── middleware.py           # Auth middleware for other services
```

**Roles:**
- `admin`: Full system access
- `manager`: Department management, workflow approval
- `developer`: Agent execution, code generation
- `viewer`: Read-only access

**Permissions:**
- `agents:execute`
- `workflows:create`
- `approvals:approve`
- `departments:manage`
- `users:manage`

**Database Schema:**
```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Roles table
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Permissions table
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Role permissions junction
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id),
    permission_id UUID REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);

-- User roles junction
CREATE TABLE user_roles (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);

-- API keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    scopes TEXT[],  -- Array of permission scopes
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 1.2 Rate Limiting

**Architecture:**
- Redis-based token bucket algorithm
- Per-user, per-tenant, and per-IP limits
- Configurable limits by endpoint and role

**Implementation:**
```python
# Middleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://agentic-redis:6379"
)

# Per-endpoint limits
@app.post("/overseer/run")
@limiter.limit("10/minute")  # 10 requests per minute
async def run_overseer(...):
    pass
```

**Rate Limit Tiers:**
- Free: 100 requests/hour
- Developer: 1000 requests/hour
- Enterprise: Unlimited

**Redis Schema:**
```
rate_limit:{tenant_id}:{endpoint}:{window} → count
rate_limit:{user_id}:{endpoint}:{window} → count
```

## Phase 2: New Agent Types (Week 2)

### 2.1 QA Tester Agent

**Capabilities:**
- Generate unit tests (pytest, jest, go test)
- Generate integration tests
- Generate E2E tests (Playwright, Selenium)
- Test coverage analysis
- Bug reproduction scripts

**YAML Config:**
```yaml
name: QA Tester
role: Quality Assurance Engineer
goal: Generate comprehensive tests and ensure code quality
backstory: |
  Expert QA engineer with 10+ years testing complex systems.
  Specializes in test-driven development and behavior-driven development.
tools:
  - pytest_generator
  - coverage_analyzer
  - bug_reproducer
llm:
  provider: claude
  model: claude-sonnet-4-20250514
```

### 2.2 DevOps/Infrastructure Agent

**Capabilities:**
- Generate Kubernetes manifests
- Generate Terraform/CloudFormation
- Docker optimization
- CI/CD pipeline generation (GitHub Actions, GitLab CI)
- Infrastructure monitoring setup

**YAML Config:**
```yaml
name: DevOps Engineer
role: Infrastructure & Deployment Specialist
goal: Automate infrastructure and deployment pipelines
backstory: |
  Senior DevOps engineer with expertise in cloud platforms,
  containerization, and infrastructure as code.
tools:
  - kubernetes_generator
  - terraform_generator
  - dockerfile_optimizer
  - cicd_generator
llm:
  provider: ollama
  model: qwen2.5-coder:7b
```

### 2.3 Designer/UX Agent

**Capabilities:**
- Generate design systems (colors, typography, components)
- Create wireframes (Mermaid diagrams)
- Generate accessible HTML/CSS
- Component library scaffolding (React, Vue)
- Responsive design patterns

**YAML Config:**
```yaml
name: UX Designer
role: User Experience & Interface Designer
goal: Create accessible, beautiful user interfaces
backstory: |
  Award-winning UX designer with expertise in design systems,
  accessibility (WCAG AA), and modern UI frameworks.
tools:
  - design_system_generator
  - wireframe_generator
  - component_generator
  - accessibility_checker
llm:
  provider: claude
  model: claude-sonnet-4-20250514
```

### 2.4 Security Auditor Agent

**Capabilities:**
- OWASP Top 10 vulnerability scanning
- Dependency vulnerability check (npm audit, pip-audit)
- Secret detection in code
- Security best practices validation
- Generate security reports

**YAML Config:**
```yaml
name: Security Auditor
role: Application Security Specialist
goal: Identify and fix security vulnerabilities
backstory: |
  Certified security professional (CISSP, CEH) with deep knowledge
  of OWASP, secure coding practices, and threat modeling.
tools:
  - owasp_scanner
  - dependency_checker
  - secret_detector
  - security_report_generator
llm:
  provider: claude
  model: claude-sonnet-4-20250514
```

## Phase 3: Enterprise Features (Week 3)

### 3.1 Multi-Tenancy

**Architecture:**
- Tenant isolation at database and application level
- Shared database with tenant_id column (simpler) OR separate schemas per tenant (stronger isolation)
- Tenant context propagation through all services

**Database Schema:**
```sql
-- Tenants table
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    plan VARCHAR(50) DEFAULT 'free',  -- free, developer, enterprise
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add tenant_id to all existing tables
ALTER TABLE approval_requests ADD COLUMN tenant_id UUID REFERENCES tenants(id);
ALTER TABLE workflows ADD COLUMN tenant_id UUID REFERENCES tenants(id);
ALTER TABLE departments ADD COLUMN tenant_id UUID REFERENCES tenants(id);

-- Row-level security policies
ALTER TABLE approval_requests ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON approval_requests
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

**Tenant Context Middleware:**
```python
@app.middleware("http")
async def add_tenant_context(request: Request, call_next):
    # Extract tenant from JWT or API key
    token = request.headers.get("Authorization")
    tenant_id = extract_tenant_from_token(token)

    # Set in request state
    request.state.tenant_id = tenant_id

    # Set Postgres session variable for RLS
    await db.execute(f"SET app.current_tenant = '{tenant_id}'")

    response = await call_next(request)
    return response
```

### 3.2 Cost Tracking Per Project

**Database Schema:**
```sql
-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    budget_usd DECIMAL(10,2),
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cost tracking table
CREATE TABLE cost_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    project_id UUID REFERENCES projects(id),
    workflow_id VARCHAR(255),
    agent_name VARCHAR(100),
    operation_type VARCHAR(50),  -- llm_call, embedding, approval
    provider VARCHAR(50),  -- ollama, claude, openai
    model VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10,6),
    latency_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_cost_project ON cost_records(project_id, timestamp);
CREATE INDEX idx_cost_tenant ON cost_records(tenant_id, timestamp);
CREATE INDEX idx_cost_workflow ON cost_records(workflow_id);
```

**Cost Calculation:**
```python
# Pricing per 1M tokens (as of 2025)
PRICING = {
    "claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "claude-opus": {"input": 15.00, "output": 75.00},
    "gpt-4": {"input": 30.00, "output": 60.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "ollama": {"input": 0.00, "output": 0.00},  # Free (self-hosted)
}

def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int):
    if provider == "ollama":
        return 0.0

    pricing = PRICING.get(model, {"input": 0, "output": 0})
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost
```

**Budget Enforcement:**
```python
async def check_project_budget(project_id: UUID) -> bool:
    total_cost = await db.fetch_val(
        "SELECT SUM(cost_usd) FROM cost_records WHERE project_id = $1",
        project_id
    )
    project = await db.fetch_one("SELECT budget_usd FROM projects WHERE id = $1", project_id)

    if project.budget_usd and total_cost >= project.budget_usd:
        raise BudgetExceededError(f"Project budget exceeded: ${total_cost:.2f} / ${project.budget_usd:.2f}")

    return True
```

### 3.3 Webhook/Event System

**Architecture:**
- Event-driven architecture with event bus
- Postgres-based event queue (simple) OR RabbitMQ/Kafka (scalable)
- Webhook delivery with exponential backoff retry

**Database Schema:**
```sql
-- Webhook subscriptions
CREATE TABLE webhook_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    url TEXT NOT NULL,
    events TEXT[] NOT NULL,  -- ['workflow.completed', 'agent.failed']
    secret VARCHAR(255),  -- For HMAC signature
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Event queue
CREATE TABLE event_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    event_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, delivered, failed
    attempts INTEGER DEFAULT 0,
    next_retry_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP
);

-- Webhook delivery logs
CREATE TABLE webhook_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID REFERENCES webhook_subscriptions(id),
    event_id UUID REFERENCES event_queue(id),
    status_code INTEGER,
    response_body TEXT,
    latency_ms INTEGER,
    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Event Types:**
- `workflow.started`
- `workflow.completed`
- `workflow.failed`
- `agent.started`
- `agent.completed`
- `agent.failed`
- `approval.requested`
- `approval.approved`
- `approval.denied`
- `project.budget_exceeded`

**Webhook Worker:**
```python
async def webhook_worker():
    while True:
        # Fetch pending events
        events = await db.fetch(
            """
            SELECT * FROM event_queue
            WHERE status = 'pending' AND next_retry_at <= NOW()
            ORDER BY created_at
            LIMIT 10
            """
        )

        for event in events:
            await deliver_webhooks(event)

        await asyncio.sleep(5)

async def deliver_webhooks(event: dict):
    # Find subscriptions for this event type
    subscriptions = await db.fetch(
        """
        SELECT * FROM webhook_subscriptions
        WHERE tenant_id = $1 AND $2 = ANY(events) AND is_active = true
        """,
        event["tenant_id"],
        event["event_type"]
    )

    for sub in subscriptions:
        try:
            # Generate HMAC signature
            signature = hmac.new(
                sub["secret"].encode(),
                json.dumps(event["payload"]).encode(),
                hashlib.sha256
            ).hexdigest()

            # Deliver webhook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    sub["url"],
                    json=event["payload"],
                    headers={"X-Webhook-Signature": signature},
                    timeout=30
                )

            # Log delivery
            await log_webhook_delivery(sub["id"], event["id"], response.status_code, response.text)

            if response.status_code == 200:
                await mark_event_delivered(event["id"])
            else:
                await retry_event(event["id"])

        except Exception as e:
            await retry_event(event["id"], error=str(e))
```

### 3.4 Scheduling System

**Architecture:**
- Leverage Temporal's built-in scheduling
- Cron-based task scheduling
- One-time scheduled tasks

**Implementation:**
```python
from temporalio.client import Client, Schedule, ScheduleActionStartWorkflow, ScheduleSpec, ScheduleIntervalSpec

# Create scheduled workflow
async def create_scheduled_task(
    schedule_id: str,
    workflow: str,
    args: dict,
    cron: str = None,
    interval: timedelta = None,
    start_at: datetime = None
):
    client = await Client.connect("localhost:7233")

    # Cron-based schedule
    if cron:
        schedule = Schedule(
            action=ScheduleActionStartWorkflow(
                workflow,
                args=[args],
                task_queue="agentic-task-queue"
            ),
            spec=ScheduleSpec(cron_expressions=[cron])
        )

    # Interval-based schedule
    elif interval:
        schedule = Schedule(
            action=ScheduleActionStartWorkflow(
                workflow,
                args=[args],
                task_queue="agentic-task-queue"
            ),
            spec=ScheduleSpec(intervals=[ScheduleIntervalSpec(every=interval)])
        )

    await client.create_schedule(schedule_id, schedule)

# Example: Daily report generation at 9 AM
await create_scheduled_task(
    schedule_id="daily-report",
    workflow="GenerateReportWorkflow",
    args={"report_type": "daily_summary"},
    cron="0 9 * * *"  # 9 AM daily
)
```

**Database Schema:**
```sql
CREATE TABLE scheduled_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    name VARCHAR(255) NOT NULL,
    workflow_name VARCHAR(255) NOT NULL,
    schedule_spec JSONB NOT NULL,  -- Cron or interval
    args JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    temporal_schedule_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.5 Agent Collaboration Framework

**Architecture:**
- Shared context store (Redis)
- Agent handoff protocol
- Context versioning

**Shared Context Store:**
```python
class CollaborationContext:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def set_context(self, project_id: str, key: str, value: dict, ttl: int = 3600):
        """Store shared context for agent collaboration"""
        context_key = f"collab:{project_id}:{key}"
        await self.redis.setex(
            context_key,
            ttl,
            json.dumps(value)
        )

    async def get_context(self, project_id: str, key: str) -> dict:
        """Retrieve shared context"""
        context_key = f"collab:{project_id}:{key}"
        data = await self.redis.get(context_key)
        return json.loads(data) if data else {}

    async def append_to_context(self, project_id: str, key: str, item: dict):
        """Append to context list (e.g., task history)"""
        context = await self.get_context(project_id, key)
        if not isinstance(context, list):
            context = []
        context.append(item)
        await self.set_context(project_id, key, context)

# Usage in agent
async def developer_agent_with_context(task: dict, project_id: str):
    collab = CollaborationContext(redis_client)

    # Get context from overseer
    plan = await collab.get_context(project_id, "plan")
    qa_requirements = await collab.get_context(project_id, "qa_requirements")

    # Execute task with context
    result = await execute_developer_task(task, context={
        "plan": plan,
        "qa_requirements": qa_requirements
    })

    # Store result for QA agent
    await collab.set_context(project_id, "code_artifacts", result)

    return result
```

**Agent Handoff Protocol:**
```python
class AgentHandoff:
    """Structured handoff between agents"""

    async def handoff(
        self,
        from_agent: str,
        to_agent: str,
        project_id: str,
        context: dict,
        instructions: str
    ):
        # Store handoff in database
        handoff_id = await db.fetch_val(
            """
            INSERT INTO agent_handoffs (
                project_id, from_agent, to_agent, context, instructions
            ) VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            project_id, from_agent, to_agent, json.dumps(context), instructions
        )

        # Store in Redis for fast access
        await collab_context.set_context(
            project_id,
            f"handoff:{to_agent}",
            {
                "from": from_agent,
                "context": context,
                "instructions": instructions,
                "handoff_id": str(handoff_id)
            }
        )

        # Emit event
        await emit_event("agent.handoff", {
            "project_id": project_id,
            "from_agent": from_agent,
            "to_agent": to_agent
        })
```

## Phase 4: Observability (Week 4)

### 4.1 Prometheus Integration

**Metrics to Expose:**
- Agent execution count, duration, errors
- Workflow execution count, duration, errors
- LLM calls count, tokens, latency
- Cost per tenant, project, agent
- Rate limit hits
- Authentication failures
- Webhook deliveries

**Implementation:**
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Metrics
agent_executions = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent_name', 'tenant_id', 'status']
)

agent_duration = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration',
    ['agent_name']
)

llm_tokens = Counter(
    'llm_tokens_total',
    'Total LLM tokens consumed',
    ['provider', 'model', 'type']  # type: input/output
)

project_cost = Gauge(
    'project_cost_usd',
    'Current project cost',
    ['project_id', 'tenant_id']
)

# Expose metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

**Prometheus Configuration:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agentic-agents'
    static_configs:
      - targets: ['agentic-agents:9000']
    scrape_interval: 15s
    metrics_path: '/metrics'

  - job_name: 'agentic-approval-ui'
    static_configs:
      - targets: ['agentic-approval-ui:9001']
    scrape_interval: 15s
```

### 4.2 Grafana Dashboards

**Dashboard 1: System Overview**
- Active workflows
- Agent execution rate (req/min)
- Success rate (%)
- Average latency
- Active users

**Dashboard 2: Cost Analysis**
- Cost per day/week/month
- Cost by project
- Cost by agent type
- Cost by LLM provider
- Budget utilization

**Dashboard 3: Agent Performance**
- Execution time by agent
- Token consumption by agent
- Error rate by agent
- RAG retrieval quality (citation scores)

**Dashboard 4: Multi-Tenancy**
- Active tenants
- Requests per tenant
- Cost per tenant
- Storage per tenant

### 4.3 Alerting System

**AlertManager Rules:**
```yaml
# alertmanager/rules.yml
groups:
  - name: agentic_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighAgentErrorRate
        expr: rate(agent_executions_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High agent error rate detected"
          description: "Agent {{ $labels.agent_name }} has error rate > 10%"

      # Budget exceeded
      - alert: ProjectBudgetExceeded
        expr: project_cost_usd / project_budget_usd > 0.9
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Project budget nearly exceeded"
          description: "Project {{ $labels.project_id }} at 90% budget"

      # High latency
      - alert: HighAgentLatency
        expr: histogram_quantile(0.95, agent_execution_duration_seconds) > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High agent latency detected"
          description: "P95 latency > 30s for {{ $labels.agent_name }}"

      # Webhook delivery failures
      - alert: WebhookDeliveryFailures
        expr: rate(webhook_deliveries_total{status="failed"}[5m]) > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High webhook failure rate"
```

**Notification Channels:**
- Slack
- PagerDuty
- Email
- Telegram (via existing n8n integration)

## Phase 5: Documentation & SDK (Week 5)

### 5.1 Python SDK

**Structure:**
```
sdk/
├── agentic_sdk/
│   ├── __init__.py
│   ├── client.py              # Main client
│   ├── auth.py                # Auth handlers
│   ├── agents.py              # Agent operations
│   ├── workflows.py           # Workflow operations
│   ├── departments.py         # Department operations
│   ├── projects.py            # Project operations
│   ├── webhooks.py            # Webhook management
│   ├── exceptions.py          # Custom exceptions
│   └── types.py               # Type definitions
├── tests/
├── examples/
├── README.md
└── setup.py
```

**Example Usage:**
```python
from agentic_sdk import AgenticClient

# Initialize client
client = AgenticClient(
    base_url="http://localhost:9000",
    api_key="sk_live_..."
)

# Execute agent
result = await client.agents.execute(
    agent="developer",
    task="Create a REST API for products",
    context={"database": "postgresql"},
    risk_level="medium"
)

# Create workflow
workflow = await client.workflows.create(
    name="ProjectPipelineWorkflow",
    args={
        "goal": "Build user management system",
        "context": {"framework": "fastapi"}
    }
)

# Wait for result
output = await workflow.wait_for_result(timeout=3600)

# Create webhook
webhook = await client.webhooks.create(
    url="https://example.com/webhooks",
    events=["workflow.completed", "agent.failed"],
    secret="webhook_secret_123"
)
```

### 5.2 Testing Guide

**Contents:**
- Unit testing agents
- Integration testing workflows
- Testing with mock LLMs
- Load testing
- Security testing

**Example:**
```python
# tests/test_developer_agent.py
import pytest
from agentic_sdk import AgenticClient

@pytest.fixture
async def client():
    return AgenticClient(
        base_url="http://localhost:9000",
        api_key="test_key"
    )

@pytest.mark.asyncio
async def test_developer_agent_generates_fastapi(client):
    result = await client.agents.execute(
        agent="developer",
        task="Create a FastAPI health check endpoint",
        context={},
        risk_level="low"
    )

    assert result.status == "completed"
    assert "FastAPI" in result.output
    assert "@app.get(\"/health\")" in result.output
    assert len(result.citations) >= 2

@pytest.mark.asyncio
async def test_budget_enforcement(client):
    with pytest.raises(BudgetExceededError):
        await client.agents.execute(
            agent="developer",
            task="Generate entire e-commerce platform",
            context={"budget_tokens": 100}  # Artificially low
        )
```

### 5.3 Deployment Guide

**Contents:**
- Kubernetes deployment manifests
- AWS ECS deployment
- Azure Container Apps
- GCP Cloud Run
- Database migration strategy
- Secrets management (AWS Secrets Manager, Vault)
- SSL/TLS setup
- Monitoring setup
- Backup strategy
- Disaster recovery

**Example Kubernetes Manifest:**
```yaml
# k8s/agent-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentic-agents
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentic-agents
  template:
    metadata:
      labels:
        app: agentic-agents
    spec:
      containers:
      - name: agents
        image: agentic/agents:latest
        ports:
        - containerPort: 9000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: agentic-secrets
              key: database-url
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: agentic-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 9000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 9000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: agentic-agents
spec:
  selector:
    app: agentic-agents
  ports:
  - protocol: TCP
    port: 9000
    targetPort: 9000
  type: ClusterIP
```

## Implementation Timeline

### Week 1: Security Foundation
- Day 1-2: Authentication system + JWT
- Day 3-4: RBAC + API keys
- Day 5: Rate limiting
- Day 6-7: Testing & documentation

### Week 2: New Agents
- Day 1-2: QA Tester agent
- Day 3: DevOps agent
- Day 4: Designer agent
- Day 5: Security Auditor agent
- Day 6-7: Integration testing

### Week 3: Enterprise Features
- Day 1-2: Multi-tenancy architecture
- Day 3: Cost tracking system
- Day 4: Webhook/event system
- Day 5: Scheduling system
- Day 6: Agent collaboration
- Day 7: Integration testing

### Week 4: Observability
- Day 1-2: Prometheus metrics
- Day 3-4: Grafana dashboards
- Day 5: AlertManager setup
- Day 6-7: Testing & tuning

### Week 5: Documentation & SDK
- Day 1-3: Python SDK development
- Day 4: Testing guide
- Day 5: Deployment guide
- Day 6-7: Final testing & documentation

## Success Metrics

### Security
- ✅ 100% of endpoints require authentication
- ✅ Rate limiting on all public endpoints
- ✅ Zero exposed credentials in logs

### Features
- ✅ 4 new agent types operational
- ✅ Multi-tenant support with full isolation
- ✅ Cost tracking with budget enforcement
- ✅ Webhook delivery >99% success rate
- ✅ Scheduling with cron support

### Observability
- ✅ <5s metric collection latency
- ✅ <1min alert firing delay
- ✅ 100% of workflows traced

### Documentation
- ✅ Python SDK with >80% test coverage
- ✅ Comprehensive testing guide
- ✅ Production-ready deployment guide

## Risk Mitigation

### Technical Risks
1. **Breaking changes to existing APIs**
   - Mitigation: Version all APIs (v1, v2), maintain backward compatibility

2. **Database migration complexity**
   - Mitigation: Use Alembic for migrations, test on staging first

3. **Performance degradation**
   - Mitigation: Load testing, caching, connection pooling

### Timeline Risks
1. **Scope creep**
   - Mitigation: Strict adherence to this plan, defer non-critical features

2. **Dependencies on external services**
   - Mitigation: Mock external services for testing

## Post-Launch

### Month 1
- Monitor metrics and alerts
- Fix critical bugs
- Performance optimization

### Month 2
- Gather user feedback
- Implement requested features
- Write case studies

### Month 3
- Scale testing (10x load)
- Security audit
- Compliance review (SOC 2, GDPR)
