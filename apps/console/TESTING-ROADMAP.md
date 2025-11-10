# Testing Roadmap — SaaS Empire Console

**Created**: 2025-11-10
**Status**: In Progress
**Current Test Status**: 67 failed | 260 passed (327 total)

---

## Executive Summary

This document outlines the comprehensive testing strategy and roadmap for the SaaS Empire Console. Based on the current test analysis, we have identified two primary categories of failures:

1. **Async Import Issues** - Page component tests using top-level `await` (5 test files)
2. **Schema Validation Mismatches** - API route tests with incorrect model names (3 test files)

---

## Current Test Status

### Test Coverage Summary
- **Test Files**: 14 failed | 10 passed (24 total)
- **Tests**: 67 failed | 260 passed (327 total)
- **Duration**: ~4 seconds

### Test File Categories

#### ✅ Passing Tests (10 files)
1. `/tests/example.test.ts`
2. `/tests/lib/utils.test.ts`
3. `/tests/api/financials/save-route.test.ts`
4. `/tests/api/git/summary-route.test.ts`
5. `/tests/api/wizard/factory-step-route.test.ts` (partial)
6. `/tests/api/wizard/single-step-route.test.ts` (partial)
7. `/tests/components/AgentStatusCard.test.tsx`
8. `/tests/components/CommandPalette.test.tsx`
9. `/tests/components/Header.test.tsx`
10. `/tests/components/Sidebar.test.tsx`
11. `/tests/components/ui/button.test.tsx`
12. `/tests/components/ui/card.test.tsx`
13. `/tests/app/wizards/factory/page.test.tsx`
14. `/tests/app/wizards/single/page.test.tsx`

#### ❌ Failing Tests (14 files)

**Category A: Async Import Issues (5 files)**
- `/tests/app/dashboard/page.test.tsx` - Top-level await at line 41
- `/tests/app/agents/page.test.tsx` - Top-level await at line 27
- `/tests/app/projects/page.test.tsx` - Top-level await pattern
- `/tests/app/workflows/page.test.tsx` - Top-level await pattern
- `/tests/app/factory-map/page.test.tsx` - Top-level await pattern

**Category B: Schema Validation Issues (3 files)**
- `/tests/api/financials/run-route.test.ts` - Using 'conservative'/'aggressive' instead of valid models
- `/tests/api/agents/health-route.test.ts` - Response format mismatch
- `/tests/api/observability/metrics-route.test.ts` - Response format mismatch

**Category C: Component Rendering Issues (6 files)**
- `/tests/app/financials/page.test.tsx` - Component structure changes
- `/tests/api/observability/logs-route.test.ts` - Query parameter handling

---

## Issue Analysis

### Issue #1: Top-Level Await in Tests

**Problem**: Tests use `const { prisma } = await import('@/lib/db/client')` outside async functions

**Example** (from dashboard/page.test.tsx:41):
```typescript
describe('DashboardPage', () => {
  const { prisma } = await import('@/lib/db/client')  // ❌ ERROR

  beforeEach(() => {
    vi.clearAllMocks()
  })
})
```

**Solution**: Move import inside beforeEach or use synchronous mocking
```typescript
describe('DashboardPage', () => {
  let prisma: any

  beforeEach(async () => {
    const imported = await import('@/lib/db/client')
    prisma = imported.prisma
    vi.clearAllMocks()
  })
})
```

**OR** (Simpler approach):
```typescript
import { prisma } from '@/lib/db/client'

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })
})
```

**Affected Files**:
- `tests/app/dashboard/page.test.tsx:41`
- `tests/app/agents/page.test.tsx:27`
- `tests/app/projects/page.test.tsx`
- `tests/app/workflows/page.test.tsx`
- `tests/app/factory-map/page.test.tsx`

---

### Issue #2: Schema Validation Mismatch

**Problem**: API tests use incorrect model names that don't match Zod schema

**Schema Definition** (lib/schemas.ts:87-91):
```typescript
export const FinancialRunRequestSchema = z.object({
  model: z.enum(['formbuilder', 'analytics', 'crm', 'scheduler', 'emailbuilder']),
  args: z.array(z.string()).optional(),
  workdir: z.string().default('/home/doctor/temponest'),
})
```

**Test Using Wrong Values** (tests/api/financials/run-route.test.ts:41):
```typescript
const request = new NextRequest('http://localhost:3000/api/financials/run', {
  method: 'POST',
  body: JSON.stringify({
    model: 'conservative',  // ❌ Not in schema enum
    args: ['arg1', 'arg2'],
    workdir: '/tmp/test',
  }),
})
```

**Solution**: Update tests to use valid model names from schema
```typescript
model: 'formbuilder',  // ✅ Valid
```

**Affected Files**:
- `tests/api/financials/run-route.test.ts` (5 tests)

---

## Testing Roadmap

### Phase 1: Critical Fixes (Week 1) - Priority: URGENT

#### Task 1.1: Fix Async Import Issues
- **Duration**: 1-2 hours
- **Files**: 5 page test files
- **Action**: Remove top-level await, use direct imports
- **Success Criteria**: All page tests compile without errors

**Steps**:
1. Update `tests/app/dashboard/page.test.tsx`
2. Update `tests/app/agents/page.test.tsx`
3. Update `tests/app/projects/page.test.tsx`
4. Update `tests/app/workflows/page.test.tsx`
5. Update `tests/app/factory-map/page.test.tsx`
6. Run tests to verify fix: `npm run test -- tests/app/`

#### Task 1.2: Fix Schema Validation Issues
- **Duration**: 1 hour
- **Files**: API test files
- **Action**: Update model names to match schema

**Steps**:
1. Update all 'conservative' → 'formbuilder' in run-route.test.ts
2. Update all 'aggressive' → 'analytics' in run-route.test.ts
3. Verify workdir parameter handling
4. Run API tests: `npm run test -- tests/api/financials/`

#### Task 1.3: Fix Component Test Failures
- **Duration**: 2-3 hours
- **Files**: financials/page.test.tsx, observability tests
- **Action**: Update tests to match current component structure

**Success Criteria**:
- All 14 failing test files pass
- Test coverage remains at current levels
- No regressions in passing tests

---

### Phase 2: Expand Test Coverage (Week 2-3)

#### Task 2.1: Add Missing API Route Tests
**Coverage Goal**: 100% of API routes

- [ ] `POST /api/observability/logs` - Filter and search tests
- [ ] `GET /api/observability/metrics` - Metrics aggregation tests
- [ ] `GET /api/agents/health` - Edge cases for agent status
- [ ] Error handling for all routes
- [ ] Rate limiting tests
- [ ] Input validation edge cases

#### Task 2.2: Add Missing Page Tests
**Coverage Goal**: 90% of page components

- [ ] `/docs/page.tsx` - Documentation browser tests
- [ ] `/observability/page.tsx` - Complete observability UI tests
- [ ] `/settings/page.tsx` - Settings form tests
- [ ] Project detail page `/projects/[slug]/page.tsx`

#### Task 2.3: Component Library Tests
**Coverage Goal**: 100% of custom components

Currently tested:
- ✅ AgentStatusCard
- ✅ Header
- ✅ Sidebar
- ✅ CommandPalette
- ✅ Button (UI)
- ✅ Card (UI)

Need tests for:
- [ ] KpiBar
- [ ] QuickActions
- [ ] RecentActivity
- [ ] FactoryMap (complex - React Flow integration)
- [ ] All other shadcn/ui components used

---

### Phase 3: Integration & E2E Tests (Week 4-5)

#### Task 3.1: Database Integration Tests
- [ ] Prisma query tests with real test database
- [ ] Transaction handling tests
- [ ] Migration tests
- [ ] Seed data tests

#### Task 3.2: API Integration Tests
- [ ] Full wizard flow tests (multi-step)
- [ ] File upload/download tests
- [ ] Streaming response tests
- [ ] WebSocket tests (if applicable)

#### Task 3.3: E2E Tests with Playwright
**Coverage Goal**: Critical user flows

- [ ] User login flow
- [ ] Create new project wizard
- [ ] Agent monitoring dashboard
- [ ] Financial calculator flow
- [ ] Factory map navigation
- [ ] Settings configuration

**E2E Test Suite Structure**:
```
tests/e2e/
├── auth/
│   ├── login.spec.ts
│   └── logout.spec.ts
├── wizards/
│   ├── single-saas.spec.ts
│   └── factory-setup.spec.ts
├── dashboard/
│   ├── agent-monitoring.spec.ts
│   └── kpi-display.spec.ts
├── financials/
│   └── calculator.spec.ts
└── settings/
    └── configuration.spec.ts
```

---

### Phase 4: Performance & Load Testing (Week 6)

#### Task 4.1: Performance Tests
- [ ] API endpoint response time benchmarks
- [ ] Database query optimization tests
- [ ] Frontend rendering performance tests
- [ ] Bundle size tests

#### Task 4.2: Load Tests
- [ ] Concurrent user simulation
- [ ] Streaming endpoint stress tests
- [ ] Database connection pool tests

---

## Testing Standards

### Test File Naming
- Unit tests: `*.test.ts` or `*.test.tsx`
- Integration tests: `*.integration.test.ts`
- E2E tests: `*.spec.ts` (in tests/e2e/)

### Test Structure
```typescript
describe('ComponentName or API Route', () => {
  beforeEach(() => {
    // Setup
  })

  afterEach(() => {
    // Cleanup
  })

  describe('Feature Group', () => {
    it('should do something specific', () => {
      // Test implementation
    })
  })
})
```

### Coverage Goals
- **Unit Tests**: 80% minimum
- **Integration Tests**: Critical paths 100%
- **E2E Tests**: All user-facing features

### Mocking Strategy
- Mock external services (APIs, databases) in unit tests
- Use real implementations in integration tests
- Mock time-dependent functions (`Date.now()`, etc.)
- Mock file system operations

---

## Tools & Configuration

### Current Setup
- **Test Runner**: Vitest 4.0.8
- **Coverage**: @vitest/coverage-v8
- **React Testing**: @testing-library/react 16.3.0
- **E2E**: @playwright/test 1.56.1
- **Mocking**: Vitest built-in mocks

### Configuration Files
- `vitest.config.ts` - Main test configuration
- `playwright.config.ts` - E2E test configuration
- `tests/setup.ts` - Global test setup

### Running Tests
```bash
# All tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# UI mode
npm run test:ui

# E2E tests
npm run test:e2e

# E2E UI mode
npm run test:e2e:ui
```

---

## CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: npm install
      - run: npm run test:coverage
      - run: npm run test:e2e
      - uses: codecov/codecov-action@v3
```

---

## Known Issues & Limitations

### Current Limitations
1. ❌ Some page tests fail due to async import pattern
2. ❌ API tests have schema validation mismatches
3. ⚠️ No E2E tests yet implemented
4. ⚠️ Database integration tests not implemented
5. ⚠️ Performance benchmarks not established

### Technical Debt
1. Mock data needs to be centralized in test fixtures
2. Test helpers should be extracted to shared utilities
3. Need better error message assertions
4. Missing negative test cases for error paths

---

## Quick Reference

### Fix Test Issues Checklist
- [ ] Fix 5 async import issues in page tests
- [ ] Fix schema validation in 3 API tests
- [ ] Update component tests for current structure
- [ ] Run full test suite
- [ ] Verify coverage remains above 80%
- [ ] Commit fixes with proper message

### Test Commands
```bash
# Run failing tests only
npm run test -- --reporter=verbose --bail

# Run specific test file
npm run test -- tests/app/dashboard/page.test.tsx

# Run tests matching pattern
npm run test -- tests/api/

# Generate coverage report
npm run test:coverage

# Debug tests
npm run test -- --inspect-brk
```

---

## Success Metrics

### Phase 1 Complete When:
- ✅ All 14 failing test files pass
- ✅ Test suite runs in < 5 seconds
- ✅ No compilation errors
- ✅ Coverage maintained at current levels

### Phase 2 Complete When:
- ✅ API route coverage > 90%
- ✅ Page component coverage > 85%
- ✅ All custom components tested
- ✅ Edge cases covered

### Phase 3 Complete When:
- ✅ E2E tests for all critical flows
- ✅ Integration tests pass with real database
- ✅ Full wizard flows tested end-to-end

### Phase 4 Complete When:
- ✅ Performance benchmarks established
- ✅ Load tests pass for expected traffic
- ✅ No performance regressions

---

## Next Steps

**Immediate Actions** (Today):
1. Fix async import issues in 5 page tests
2. Fix schema validation in API tests
3. Run full test suite to verify fixes
4. Commit changes

**This Week**:
1. Complete Phase 1 fixes
2. Start Phase 2 - expand coverage
3. Set up E2E test framework

**Next Week**:
1. Continue Phase 2
2. Begin Phase 3 integration tests

---

## Resources

### Documentation
- [Vitest Docs](https://vitest.dev)
- [Testing Library](https://testing-library.com/react)
- [Playwright Docs](https://playwright.dev)

### Test Examples
- See `/tests/components/` for component test examples
- See `/tests/api/` for API route test examples
- See passing tests for patterns to follow

---

**Last Updated**: 2025-11-10
**Maintained By**: Development Team
**Status**: Living Document - Update as testing evolves
