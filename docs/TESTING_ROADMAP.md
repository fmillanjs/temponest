# Testing Roadmap to 100% Coverage

## Current Status (Baseline Audit)

### Services Coverage (Python)
- **Total Service Files**: 69 Python files across all services
- **Test Files**: 9 (Auth service only)
- **Current Coverage**: ~15% (Auth service only)
- **Target Coverage**: 100%

### Frontend Coverage (TypeScript/React)
- **Total Console Files**: 27 TypeScript/TSX files
- **Test Files**: 0
- **Current Coverage**: 0%
- **Target Coverage**: 100%

### Services Status

| Service | Files | Tests | Coverage | Status |
|---------|-------|-------|----------|--------|
| Auth Service | ~15 | ✅ 6 tests | ~40% | Partial |
| Agents Service | ~25 | ❌ None | 0% | Not Started |
| Scheduler Service | ~12 | ❌ None | 0% | Not Started |
| Approval UI | ~8 | ❌ None | 0% | Not Started |
| Ingestion | ~5 | ❌ None | 0% | Not Started |
| Temporal Workers | ~4 | ❌ None | 0% | Not Started |
| **Total Backend** | **69** | **6** | **~15%** | **In Progress** |

### Frontend Status

| Component | Files | Tests | Coverage | Status |
|-----------|-------|-------|----------|--------|
| Console (Next.js) | 27 | ❌ None | 0% | Not Started |
| Web UI (Flask) | ~10 | ❌ None | 0% | Not Started |
| **Total Frontend** | **37** | **0** | **0%** | **Not Started** |

### SDK & Tools Status

| Component | Files | Tests | Coverage | Status |
|-----------|-------|-------|----------|--------|
| Python SDK | ~10 | ❌ None | 0% | Not Started |
| CLI Tool | ~5 | ❌ None | 0% | Not Started |
| **Total Tools** | **15** | **0** | **0%** | **Not Started** |

### Overall Project Status
- **Total Files to Test**: 121
- **Total Test Files**: 9
- **Overall Coverage**: ~12%
- **Target**: 100%
- **Gap**: 88%

---

## Testing Strategy

### Testing Pyramid

```
         /\
        /  \    E2E Tests (10%)
       /____\   - Critical user flows
      /      \  - Cross-service integration
     /  INT   \ Integration Tests (30%)
    /__________\  - API endpoints
   /            \ - Service interactions
  /    UNIT      \ Unit Tests (60%)
 /________________\ - Functions, classes, components
```

### Test Types

1. **Unit Tests** (60% of tests)
   - Individual functions
   - Classes and methods
   - React components (isolated)
   - Pure logic

2. **Integration Tests** (30% of tests)
   - API endpoints
   - Database operations
   - Service-to-service calls
   - Authentication flows

3. **E2E Tests** (10% of tests)
   - Complete user workflows
   - Multi-service scenarios
   - Browser automation (Console)
   - Critical business paths

---

## Phase 1: Infrastructure Setup (Week 1)

### 1.1 Backend Testing Infrastructure ✅
```bash
# Install testing tools
cd /home/doctor/temponest/services/agents
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx

cd /home/doctor/temponest/services/scheduler
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx

cd /home/doctor/temponest/sdk
pip install pytest pytest-asyncio pytest-cov
```

### 1.2 Frontend Testing Infrastructure ⏳
```bash
# Install testing tools for Console
cd /home/doctor/temponest/apps/console
npm install --save-dev \
  vitest \
  @testing-library/react \
  @testing-library/jest-dom \
  @testing-library/user-event \
  @vitest/ui \
  @playwright/test \
  happy-dom

# Create vitest config
cat > vitest.config.ts <<EOF
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',
    globals: true,
    setupFiles: './tests/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '*.config.*'
      ]
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './')
    }
  }
})
EOF
```

### 1.3 CI/CD Integration ⏳
```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Run Auth Service Tests
        run: |
          cd services/auth
          pip install -r requirements.txt
          pytest tests/ --cov=app --cov-report=xml

      - name: Run Agents Service Tests
        run: |
          cd services/agents
          pip install -r requirements.txt
          pytest tests/ --cov=app --cov-report=xml

      - name: Run Scheduler Service Tests
        run: |
          cd services/scheduler
          pip install -r requirements.txt
          pytest tests/ --cov=app --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./services/*/coverage.xml
          fail_ci_if_error: true

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Run Console Tests
        run: |
          cd apps/console
          npm ci
          npm run test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./apps/console/coverage/coverage-final.json

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run E2E Tests
        run: |
          cd apps/console
          npx playwright install
          npx playwright test
```

---

## Phase 2: Backend Services Testing (Weeks 2-4)

### 2.1 Complete Auth Service Tests ✅ (Week 2, Day 1-2)

**Existing Tests (Auth Service):**
- ✅ `test_jwt_handler.py` - JWT token operations
- ✅ `test_password_handler.py` - Password hashing
- ✅ `test_api_key_handler.py` - API key operations
- ✅ `test_auth_routes.py` - Login/register/refresh
- ✅ `test_api_key_routes.py` - API key management

**Additional Tests Needed:**
- [ ] `test_middleware.py` - Auth middleware edge cases
- [ ] `test_rate_limiting.py` - Rate limit enforcement
- [ ] `test_rbac.py` - Role-based access control
- [ ] `test_audit_logging.py` - Audit log creation
- [ ] `test_auth_e2e.py` - Full authentication flows

**Target Coverage**: 95%+

### 2.2 Agents Service Tests ❌ (Week 2, Day 3-7)

**Test Structure**:
```
services/agents/tests/
├── conftest.py              # Fixtures and setup
├── unit/
│   ├── test_agent_crud.py   # Agent CRUD operations
│   ├── test_agent_execution.py  # Agent execution logic
│   ├── test_rag_retrieval.py    # RAG search and retrieval
│   ├── test_tools.py        # Tool execution
│   ├── test_cost_tracking.py    # Cost calculation
│   ├── test_webhooks.py     # Webhook delivery
│   ├── test_collaboration.py   # Multi-agent collaboration
│   └── agents/
│       ├── test_overseer.py      # Overseer agent
│       ├── test_developer.py     # Developer agent
│       ├── test_designer.py      # Designer agent
│       ├── test_qa_tester.py     # QA Tester agent
│       ├── test_devops.py        # DevOps agent
│       ├── test_security.py      # Security Auditor agent
│       └── test_ux_researcher.py # UX Researcher agent
├── integration/
│   ├── test_agent_api.py    # Agent API endpoints
│   ├── test_execution_api.py    # Execution endpoints
│   ├── test_rag_api.py      # RAG endpoints
│   ├── test_cost_api.py     # Cost tracking endpoints
│   └── test_webhook_api.py  # Webhook endpoints
└── e2e/
    ├── test_agent_workflow.py   # Complete agent workflow
    └── test_collaboration_workflow.py  # Multi-agent flows
```

**Key Test Cases**:
```python
# test_agent_crud.py
def test_create_agent_success()
def test_create_agent_validation_error()
def test_get_agent_success()
def test_get_agent_not_found()
def test_list_agents_pagination()
def test_update_agent_success()
def test_delete_agent_success()
def test_agent_tenant_isolation()

# test_agent_execution.py
def test_execute_agent_success()
def test_execute_agent_with_tools()
def test_execute_agent_with_rag()
def test_execute_agent_cost_tracking()
def test_execute_agent_timeout()
def test_execute_agent_error_handling()
def test_execute_agent_streaming()

# test_rag_retrieval.py
def test_rag_query_success()
def test_rag_query_with_filters()
def test_rag_query_empty_results()
def test_rag_document_upload()
def test_rag_collection_management()
```

**Target Coverage**: 90%+

### 2.3 Scheduler Service Tests ❌ (Week 3, Day 1-5)

**Test Structure**:
```
services/scheduler/tests/
├── conftest.py
├── unit/
│   ├── test_schedule_crud.py        # Schedule operations
│   ├── test_cron_parser.py          # Cron expression parsing
│   ├── test_job_execution.py        # Job execution logic
│   ├── test_collaboration.py        # Multi-agent patterns
│   └── test_webhook_delivery.py     # Webhook notifications
├── integration/
│   ├── test_schedule_api.py         # Schedule API
│   ├── test_execution_api.py        # Execution API
│   └── test_agent_integration.py    # Integration with Agents service
└── e2e/
    ├── test_scheduled_workflow.py   # Complete scheduled workflow
    └── test_collaboration_patterns.py  # Sequential/parallel/iterative
```

**Key Test Cases**:
```python
# test_schedule_crud.py
def test_create_schedule_success()
def test_create_schedule_invalid_cron()
def test_list_schedules()
def test_pause_schedule()
def test_resume_schedule()
def test_trigger_schedule_manually()
def test_delete_schedule()

# test_job_execution.py
def test_execute_scheduled_job()
def test_job_execution_retry()
def test_job_execution_failure()
def test_job_execution_timeout()

# test_collaboration.py
def test_sequential_collaboration()
def test_parallel_collaboration()
def test_iterative_collaboration()
def test_hierarchical_collaboration()
```

**Target Coverage**: 90%+

### 2.4 Approval UI Tests ❌ (Week 3, Day 6-7)

**Test Structure**:
```
services/approval_ui/tests/
├── conftest.py
├── unit/
│   ├── test_approval_logic.py   # Approval decision logic
│   └── test_models.py           # Data models
├── integration/
│   ├── test_approval_routes.py  # API endpoints
│   └── test_telegram_integration.py  # Telegram bot
└── e2e/
    └── test_approval_workflow.py  # Complete approval flow
```

**Target Coverage**: 85%+

### 2.5 Ingestion Service Tests ❌ (Week 4, Day 1-2)

**Test Structure**:
```
services/ingestion/tests/
├── conftest.py
├── unit/
│   ├── test_document_parser.py  # Document parsing
│   ├── test_chunking.py         # Text chunking
│   └── test_embedding.py        # Embedding generation
└── integration/
    ├── test_ingestion_pipeline.py  # Full ingestion
    └── test_qdrant_integration.py  # Vector DB integration
```

**Target Coverage**: 85%+

### 2.6 Temporal Workers Tests ❌ (Week 4, Day 3-4)

**Test Structure**:
```
services/temporal_workers/tests/
├── conftest.py
├── unit/
│   ├── test_workflows.py    # Workflow definitions
│   └── test_activities.py   # Activity implementations
└── integration/
    └── test_worker_integration.py  # Full worker execution
```

**Target Coverage**: 80%+

---

## Phase 3: Frontend Testing (Weeks 5-6)

### 3.1 Console Component Tests ❌ (Week 5, Day 1-5)

**Test Structure**:
```
apps/console/tests/
├── setup.ts                 # Test setup
├── components/
│   ├── Header.test.tsx
│   ├── Sidebar.test.tsx
│   ├── CommandPalette.test.tsx
│   ├── ui/
│   │   ├── button.test.tsx
│   │   ├── card.test.tsx
│   │   ├── dialog.test.tsx
│   │   └── toast.test.tsx
│   └── charts/
│       ├── LineChart.test.tsx
│       └── BarChart.test.tsx
├── hooks/
│   └── use-toast.test.ts
└── lib/
    ├── utils.test.ts
    └── api.test.ts
```

**Key Test Cases**:
```typescript
// Header.test.tsx
describe('Header', () => {
  it('renders logo and navigation', () => {})
  it('opens command palette on cmd+k', () => {})
  it('shows notifications dropdown', () => {})
  it('handles user menu interactions', () => {})
})

// CommandPalette.test.tsx
describe('CommandPalette', () => {
  it('opens with keyboard shortcut', () => {})
  it('filters commands on search', () => {})
  it('executes selected command', () => {})
  it('closes on escape', () => {})
})
```

**Target Coverage**: 80%+

### 3.2 Console Page Tests ❌ (Week 5, Day 6-7)

**Test Structure**:
```
apps/console/tests/
├── app/
│   ├── dashboard/page.test.tsx
│   ├── factory-map/page.test.tsx
│   ├── workflows/page.test.tsx
│   ├── projects/page.test.tsx
│   ├── agents/page.test.tsx
│   ├── wizards/
│   │   ├── single/page.test.tsx
│   │   └── factory/page.test.tsx
│   └── financials/page.test.tsx
```

**Target Coverage**: 75%+

### 3.3 Console API Routes Tests ❌ (Week 6, Day 1-2)

**Test Structure**:
```
apps/console/tests/
├── api/
│   ├── financials/route.test.ts
│   ├── wizard/single/route.test.ts
│   ├── wizard/factory/route.test.ts
│   └── agents/health/route.test.ts
```

**Target Coverage**: 90%+

### 3.4 Console E2E Tests ❌ (Week 6, Day 3-5)

**Test Structure**:
```
apps/console/e2e/
├── playwright.config.ts
├── auth.setup.ts
├── critical-flows/
│   ├── wizard-single-saas.spec.ts
│   ├── wizard-factory.spec.ts
│   ├── agent-execution.spec.ts
│   ├── project-creation.spec.ts
│   └── financial-calculator.spec.ts
└── smoke/
    ├── navigation.spec.ts
    └── responsive.spec.ts
```

**Key E2E Cases**:
```typescript
// wizard-single-saas.spec.ts
test('completes single SaaS wizard workflow', async ({ page }) => {
  await page.goto('/wizards/single')
  await page.fill('[name="projectName"]', 'TestSaaS')
  await page.fill('[name="workdir"]', '/tmp/test')
  await page.click('button:has-text("Run Step")')
  // ... assert streaming logs, progress, completion
})
```

**Target Coverage**: Critical paths only

---

## Phase 4: SDK & Tools Testing (Week 7)

### 4.1 Python SDK Tests ❌ (Week 7, Day 1-3)

**Test Structure**:
```
sdk/tests/
├── conftest.py
├── unit/
│   ├── test_client.py           # Base client
│   ├── test_agents_client.py    # Agents operations
│   ├── test_scheduler_client.py # Scheduler operations
│   ├── test_rag_client.py       # RAG operations
│   ├── test_collaboration_client.py  # Collaboration
│   ├── test_costs_client.py     # Cost tracking
│   └── test_webhooks_client.py  # Webhooks
├── integration/
│   ├── test_sdk_integration.py  # Real API calls
│   └── test_streaming.py        # Streaming support
└── examples/
    └── test_examples.py         # Example scripts work
```

**Key Test Cases**:
```python
# test_agents_client.py
def test_create_agent()
def test_list_agents()
def test_execute_agent()
def test_execute_agent_stream()
def test_delete_agent()
def test_error_handling()
def test_retry_logic()

# test_sdk_integration.py (requires live services)
@pytest.mark.integration
def test_full_agent_workflow()
def test_scheduled_agent_execution()
def test_multi_agent_collaboration()
```

**Target Coverage**: 85%+

### 4.2 CLI Tool Tests ❌ (Week 7, Day 4-5)

**Test Structure**:
```
cli/tests/
├── conftest.py
├── test_commands.py         # All CLI commands
├── test_output.py           # Output formatting
└── test_integration.py      # End-to-end CLI flows
```

**Key Test Cases**:
```python
# test_commands.py
def test_agent_list()
def test_agent_create()
def test_agent_execute()
def test_schedule_create()
def test_cost_summary()
def test_status_check()
```

**Target Coverage**: 80%+

### 4.3 Web UI Tests ❌ (Week 7, Day 6-7)

**Test Structure**:
```
web-ui/tests/
├── conftest.py
├── test_routes.py           # Flask routes
├── test_templates.py        # Template rendering
└── test_api_calls.py        # API integration
```

**Target Coverage**: 75%+

---

## Phase 5: Integration & Performance Testing (Week 8)

### 5.1 Cross-Service Integration Tests ❌ (Week 8, Day 1-3)

**Test Structure**:
```
tests/integration/
├── conftest.py
├── test_auth_integration.py     # Auth + all services
├── test_agent_scheduler.py      # Agents + Scheduler
├── test_full_workflow.py        # Complete workflows
└── test_multi_tenant.py         # Tenant isolation
```

**Key Scenarios**:
```python
# test_full_workflow.py
def test_authenticated_agent_execution()
def test_scheduled_multi_agent_collaboration()
def test_rag_powered_agent_with_cost_tracking()
def test_webhook_triggered_workflow()
```

**Target Coverage**: Critical paths

### 5.2 Load & Performance Tests ❌ (Week 8, Day 4-5)

**Test Structure**:
```
tests/performance/
├── locustfile.py            # Main load test
├── scenarios/
│   ├── agent_execution.py   # Agent execution load
│   ├── rag_queries.py       # RAG search load
│   └── api_endpoints.py     # General API load
└── reports/
    └── .gitkeep
```

**Locust Test Example**:
```python
# locustfile.py
from locust import HttpUser, task, between

class AgentUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_agents(self):
        self.client.get("/agents/")

    @task(1)
    def execute_agent(self):
        self.client.post("/agents/123/execute", json={
            "message": "Test execution"
        })
```

**Performance Targets**:
- Agent execution: < 2s p95
- RAG query: < 500ms p95
- API endpoints: < 200ms p95
- Concurrent users: 100+

### 5.3 Security Tests ❌ (Week 8, Day 6-7)

**Test Structure**:
```
tests/security/
├── test_owasp_top10.py      # OWASP Top 10 tests
├── test_injection.py        # SQL/Command injection
├── test_xss.py              # Cross-site scripting
├── test_csrf.py             # CSRF protection
├── test_authentication.py   # Auth security
└── test_authorization.py    # Authorization bypass
```

**Key Security Tests**:
```python
# test_injection.py
def test_sql_injection_prevention()
def test_command_injection_prevention()

# test_authentication.py
def test_jwt_signature_verification()
def test_expired_token_rejection()
def test_brute_force_protection()

# test_authorization.py
def test_rbac_enforcement()
def test_tenant_isolation()
def test_api_key_scopes()
```

---

## Phase 6: Coverage Analysis & Gaps (Week 9)

### 6.1 Run Full Test Suite

```bash
# Backend
cd services/auth && pytest --cov=app --cov-report=html
cd services/agents && pytest --cov=app --cov-report=html
cd services/scheduler && pytest --cov=app --cov-report=html

# Frontend
cd apps/console && npm run test:coverage

# SDK
cd sdk && pytest --cov=temponest_sdk --cov-report=html

# Generate combined report
coverage combine
coverage report
coverage html
```

### 6.2 Identify Gaps

```bash
# Find uncovered lines
coverage report --show-missing

# Generate JSON report for analysis
coverage json
python scripts/analyze_coverage.py coverage.json
```

### 6.3 Write Missing Tests

Focus on:
- Uncovered branches
- Error handling paths
- Edge cases
- Rarely executed code

---

## Phase 7: Documentation & Automation (Week 10)

### 7.1 Testing Standards Document

Create `docs/TESTING_STANDARDS.md`:
- Test naming conventions
- Fixture patterns
- Mocking strategies
- Coverage requirements
- CI/CD integration

### 7.2 Coverage Reporting

**Set up Codecov**:
```yaml
# codecov.yml
coverage:
  status:
    project:
      default:
        target: 100%
        threshold: 1%
    patch:
      default:
        target: 100%
        threshold: 1%

comment:
  layout: "reach, diff, flags, files"
  behavior: default
```

### 7.3 Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        types: [python]
        pass_filenames: false
        always_run: true
        args: [--cov, --cov-fail-under=80]
```

---

## Success Metrics

### Coverage Targets by Component

| Component | Target | Current | Gap |
|-----------|--------|---------|-----|
| Auth Service | 95% | 40% | 55% |
| Agents Service | 90% | 0% | 90% |
| Scheduler Service | 90% | 0% | 90% |
| Approval UI | 85% | 0% | 85% |
| Ingestion | 85% | 0% | 85% |
| Temporal Workers | 80% | 0% | 80% |
| Console (Frontend) | 80% | 0% | 80% |
| Web UI | 75% | 0% | 75% |
| Python SDK | 85% | 0% | 85% |
| CLI Tool | 80% | 0% | 80% |
| **Overall** | **100%** | **12%** | **88%** |

### Quality Metrics

- **Test Execution Time**: < 5 minutes (unit + integration)
- **E2E Execution Time**: < 15 minutes
- **Flaky Tests**: 0 (deterministic tests only)
- **Test Reliability**: 100% pass rate
- **CI/CD**: All PRs must pass tests
- **Coverage Change**: No decrease allowed

---

## Timeline Summary

| Week | Phase | Focus | Deliverables |
|------|-------|-------|--------------|
| 1 | Infrastructure | Setup testing tools | pytest, vitest, playwright configs |
| 2 | Backend | Auth + Agents services | ~500 unit tests |
| 3 | Backend | Scheduler + Approval UI | ~300 unit tests |
| 4 | Backend | Ingestion + Temporal | ~200 unit tests |
| 5 | Frontend | Console components | ~200 component tests |
| 6 | Frontend | Console pages + E2E | ~100 tests + E2E suite |
| 7 | SDK/Tools | SDK + CLI + Web UI | ~300 tests |
| 8 | Integration | Cross-service + Performance | Load tests + security tests |
| 9 | Analysis | Coverage gaps | Fill missing tests |
| 10 | Documentation | Standards + Automation | Testing guide, CI/CD |

**Total Duration**: 10 weeks (2.5 months)
**Total Tests**: ~1,800 tests
**Final Coverage**: 100%

---

## Quick Start Commands

### Run All Tests
```bash
# Backend (from project root)
pytest tests/ services/*/tests/ --cov --cov-report=html

# Frontend
cd apps/console && npm test

# SDK
cd sdk && pytest --cov

# E2E
cd apps/console && npx playwright test
```

### Coverage Reports
```bash
# Generate HTML report
pytest --cov --cov-report=html
open htmlcov/index.html

# Generate terminal report
pytest --cov --cov-report=term-missing

# Check coverage threshold
pytest --cov --cov-fail-under=100
```

### CI/CD Simulation
```bash
# Run what CI/CD will run
./scripts/run_tests.sh
```

---

## Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Library](https://testing-library.com/)
- [Locust Documentation](https://docs.locust.io/)

### Internal Guides
- `docs/TESTING_GUIDE.md` - Comprehensive testing guide
- `docs/TESTING_STANDARDS.md` - Testing standards (to be created)
- `README.md` - Project setup and testing commands

---

**Last Updated**: 2025-11-06
**Owner**: Development Team
**Target Completion**: 10 weeks from start date
**Current Status**: Week 1 - Infrastructure Setup
