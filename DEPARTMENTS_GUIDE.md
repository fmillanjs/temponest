# Department Management Guide

Complete guide to creating, editing, and managing your agentic company's organizational structure.

## Overview

The platform supports a **hierarchical department structure** where you can:
- ✅ Create top-level departments (Marketing, Engineering, Sales, etc.)
- ✅ Add sub-departments (Video Production under Marketing)
- ✅ Assign AI agents to each department
- ✅ Define custom workflows
- ✅ Grow dynamically as your company scales

## Quick Start

### View Current Organization

```bash
# List all departments
curl http://localhost:9000/departments/

# Get organizational structure (hierarchical)
curl http://localhost:9000/departments/structure

# View specific department
curl http://localhost:9000/departments/marketing

# List all workflows
curl http://localhost:9000/departments/workflows/all
```

### Execute a Workflow

```bash
curl -X POST http://localhost:9000/departments/workflows/execute \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_path": "marketing.video_production.create_marketing_video",
    "context": {
      "campaign": "Product Launch Q4",
      "target_audience": "B2B decision makers",
      "duration": "60 seconds"
    }
  }'
```

### Execute an Agent Task Directly

```bash
curl -X POST http://localhost:9000/departments/agents/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_path": "marketing.video_production.script_writer",
    "task": "Write a script for a 30-second product demo video",
    "context": {"product": "AI automation platform"}
  }'
```

## Creating a New Department

### Step 1: Create YAML Configuration

Create a file in `config/departments/<department_name>.yaml`:

```bash
# Example: config/departments/engineering.yaml
```

```yaml
# Engineering Department Configuration

department:
  id: engineering
  name: Engineering
  description: "Software development and technical operations"
  parent: null  # Top-level department (null) or parent ID

  # Budget allocation
  budget:
    tokens_per_task: 10000
    monthly_limit: 5000000

  # Department agents
  agents:
    - id: senior_engineer
      name: Senior Software Engineer
      role: "Senior Full-Stack Engineer"
      provider: claude  # ollama, claude, or openai
      model: claude-sonnet-4-20250514
      temperature: 0.2
      responsibilities:
        - "Design and implement new features"
        - "Review code and architecture decisions"
        - "Mentor junior developers"
        - "Optimize system performance"
      tools:
        - rag_search
        - code_analyzer
        - test_runner

    - id: qa_engineer
      name: QA Engineer
      role: "Quality Assurance Engineer"
      provider: claude
      model: claude-sonnet-4-20250514
      temperature: 0.1
      responsibilities:
        - "Create comprehensive test plans"
        - "Write automated tests"
        - "Perform regression testing"
        - "Document bugs and issues"
      tools:
        - rag_search
        - test_framework
        - bug_tracker

  # Sub-departments (optional)
  sub_departments:
    - backend
    - frontend
    - devops

  # Department workflows
  workflows:
    - id: feature_development
      name: "Develop New Feature"
      description: "Full feature development lifecycle"
      trigger: manual
      risk_level: medium
      steps:
        - agent: senior_engineer
          task: "Design feature architecture and API"
          approval_required: true

        - agent: senior_engineer
          task: "Implement feature with tests"
          approval_required: false

        - agent: qa_engineer
          task: "Create test plan and execute tests"
          approval_required: false

        - agent: senior_engineer
          task: "Review QA results and deploy to staging"
          approval_required: true
```

### Step 2: Restart Service

```bash
cd docker
docker-compose restart agents
```

The department will be loaded automatically on startup.

### Step 3: Verify

```bash
# Check if loaded
curl http://localhost:9000/departments/engineering

# List agents
curl http://localhost:9000/departments/engineering/agents
```

## Creating a Sub-Department

### Example: Video Production (under Marketing)

```yaml
# config/departments/video_production.yaml

department:
  id: video_production
  name: Video Production
  description: "Video content creation team"
  parent: marketing  # 👈 Set parent department

  budget:
    tokens_per_task: 10000
    monthly_limit: 300000

  agents:
    - id: video_producer
      name: Video Producer
      role: "Senior Video Producer"
      provider: claude
      model: claude-sonnet-4-20250514
      temperature: 0.3
      responsibilities:
        - "Plan video content and storyboards"
        - "Coordinate video production workflow"
      tools:
        - rag_search
        - storyboard_generator

  workflows:
    - id: create_marketing_video
      name: "Create Marketing Video"
      description: "Full video production workflow"
      trigger: manual
      risk_level: medium
      steps:
        # Can reference parent department agents
        - agent: marketing.marketing_strategist
          task: "Define video goals and messaging"
          approval_required: true

        # Own agents
        - agent: video_producer
          task: "Create storyboard and shot list"
          approval_required: false
```

**Path structure:**
- Department: `marketing`
- Sub-department: `marketing.video_production`
- Agent: `marketing.video_production.video_producer`
- Workflow: `marketing.video_production.create_marketing_video`

## Department YAML Reference

### Required Fields

```yaml
department:
  id: unique_id            # Required: Unique identifier
  name: Display Name       # Required: Human-readable name
  description: "..."       # Required: Description
  parent: null             # Required: null or parent department ID
```

### Optional Fields

```yaml
department:
  # Budget allocation (optional)
  budget:
    tokens_per_task: 8000
    monthly_limit: 1000000

  # Agents (optional, but recommended)
  agents:
    - id: agent_id
      name: Agent Name
      role: Agent Role
      provider: claude | ollama | openai
      model: model-name
      temperature: 0.0-1.0
      responsibilities: [...]
      tools: [...]

  # Sub-departments (optional)
  sub_departments:
    - sub_dept_id_1
    - sub_dept_id_2

  # Workflows (optional)
  workflows:
    - id: workflow_id
      name: Workflow Name
      description: "..."
      trigger: manual | schedule | event
      risk_level: low | medium | high
      steps:
        - agent: agent_path
          task: "..."
          approval_required: true | false

  # Integrations (optional, for documentation)
  integrations:
    - department: other_dept_id
      shared_workflows: [...]
      data_exchange: [...]
```

## Agent Configuration

### Supported Providers

**Ollama (Local)**
```yaml
provider: ollama
model: mistral:7b-instruct
```

**Claude**
```yaml
provider: claude
model: claude-sonnet-4-20250514
```

**OpenAI**
```yaml
provider: openai
model: gpt-4-turbo-preview
```

### Temperature Guidelines

- `0.0-0.2`: Deterministic, factual (engineering, QA)
- `0.3-0.5`: Balanced (marketing, content)
- `0.6-1.0`: Creative (brainstorming, ideation)

### Available Tools

- `rag_search` - Search knowledge base
- `code_analyzer` - Analyze code quality
- `test_runner` - Run tests
- `storyboard_generator` - Create video storyboards
- `analytics_dashboard` - View analytics
- `grammar_check` - Check grammar/spelling
- `seo_optimizer` - Optimize for SEO

## Workflow Configuration

### Risk Levels

**Low**: Auto-execute, no approval needed
- Documentation updates
- Content creation
- Research tasks

**Medium**: Requires 1 approval
- Code generation
- Campaign launches
- Database schema changes

**High**: Requires 2 approvals
- Production deployments
- Billing operations
- Data migrations

### Workflow Steps

```yaml
steps:
  # Step format
  - agent: department.agent_id
    task: "Describe what to do"
    approval_required: true | false

  # Reference parent department agents
  - agent: marketing.marketing_strategist
    task: "Review strategy"
    approval_required: true

  # Reference sub-department agents
  - agent: marketing.video_production.video_producer
    task: "Create video"
    approval_required: false
```

## Real-World Examples

### Example 1: Add Sales Department

```yaml
# config/departments/sales.yaml

department:
  id: sales
  name: Sales
  description: "Revenue generation and customer acquisition"
  parent: null

  agents:
    - id: sales_rep
      name: Sales Representative
      role: "Senior Sales Rep"
      provider: claude
      model: claude-sonnet-4-20250514
      temperature: 0.4
      responsibilities:
        - "Qualify leads"
        - "Create proposals"
        - "Close deals"
      tools:
        - rag_search
        - crm_integration

  workflows:
    - id: create_proposal
      name: "Generate Sales Proposal"
      risk_level: low
      steps:
        - agent: sales_rep
          task: "Research prospect and create customized proposal"
          approval_required: false
```

### Example 2: Add DevOps Sub-Department

```yaml
# config/departments/devops.yaml

department:
  id: devops
  name: DevOps
  description: "Infrastructure and deployment automation"
  parent: engineering

  agents:
    - id: devops_engineer
      name: DevOps Engineer
      role: "Senior DevOps Engineer"
      provider: claude
      model: claude-sonnet-4-20250514
      temperature: 0.1
      responsibilities:
        - "Manage CI/CD pipelines"
        - "Monitor infrastructure"
        - "Automate deployments"
      tools:
        - rag_search
        - infrastructure_manager

  workflows:
    - id: deploy_to_production
      name: "Deploy to Production"
      risk_level: high
      steps:
        - agent: engineering.qa_engineer
          task: "Verify all tests pass"
          approval_required: true

        - agent: devops_engineer
          task: "Deploy to production with rollback plan"
          approval_required: true
```

## Editing Existing Departments

### Option 1: Edit YAML Directly

1. Edit file in `config/departments/<department>.yaml`
2. Restart service:
   ```bash
   docker-compose restart agents
   ```

### Option 2: Via API (Future Enhancement)

```bash
# Coming soon: Dynamic department updates without restart
curl -X PATCH http://localhost:9000/departments/marketing \
  -H "Content-Type: application/json" \
  -d '{"budget": {"tokens_per_task": 12000}}'
```

## Best Practices

### 1. Start Small

Begin with 1-2 departments, add more as needed:
```
✅ Start: Marketing → Add Video Production later
❌ Don't: Create 20 departments on day 1
```

### 2. Hierarchical Organization

```
Company
├── Marketing
│   ├── Video Production
│   ├── Social Media
│   └── Email Marketing
├── Engineering
│   ├── Backend
│   ├── Frontend
│   └── DevOps
└── Sales
    ├── Outbound
    └── Account Management
```

### 3. Agent Responsibilities

Be specific and actionable:
```yaml
# ✅ Good
responsibilities:
  - "Write video scripts under 60 seconds"
  - "Ensure brand voice consistency"

# ❌ Too vague
responsibilities:
  - "Do video stuff"
```

### 4. Workflow Naming

Use action verbs:
```yaml
# ✅ Good
id: create_marketing_video
name: "Create Marketing Video"

# ❌ Vague
id: video_thing
name: "Video"
```

## Troubleshooting

### Department not loading

**Check logs:**
```bash
docker logs -f agentic-agents | grep "Loading departments"
```

**Common issues:**
- Invalid YAML syntax (use yamllint)
- Missing required fields (id, name, description, parent)
- Invalid parent reference

### Agent not found

**Verify agent path:**
```bash
curl http://localhost:9000/departments/marketing/agents
```

**Path format:**
- Top-level: `department.agent_id`
- Sub-department: `parent.child.agent_id`

### Workflow execution fails

**Check:**
1. All referenced agents exist
2. Agent paths are correct
3. Approval system is configured (if approval_required=true)

## Monitoring & Analytics

### View Department Activity

```bash
# Get department details
curl http://localhost:9000/departments/marketing

# List active workflows
curl http://localhost:9000/departments/workflows/all
```

### Langfuse Integration

All department agents are automatically traced in Langfuse:
- Visit http://localhost:3000
- Filter by department ID
- View token usage and costs per department

## Migration from Legacy Agents

Old way (hardcoded):
```python
overseer_agent = OverseerAgent(...)
developer_agent = DeveloperAgent(...)
```

New way (dynamic departments):
```yaml
# config/departments/product.yaml
agents:
  - id: product_manager
    # ...configuration
```

**Both systems coexist!** Legacy agents still work for backward compatibility.

## Next Steps

1. **Create your first department**: Start with your core function (Marketing, Engineering, etc.)
2. **Add 2-3 agents**: Keep it simple initially
3. **Define 1 workflow**: Test end-to-end
4. **Iterate**: Add sub-departments as you grow

## Examples to Get Started

Check these example departments:
- `config/departments/marketing.yaml` - Full marketing department
- `config/departments/video_production.yaml` - Sub-department with workflows
- `config/departments/social_media.yaml` - Social media team

---

**Quick Reference:**

| Task | Command |
|------|---------|
| List departments | `GET /departments/` |
| View department | `GET /departments/{id}` |
| List agents | `GET /departments/{id}/agents` |
| Execute workflow | `POST /departments/workflows/execute` |
| Execute agent task | `POST /departments/agents/execute` |
| Org structure | `GET /departments/structure` |

Happy building! 🚀
