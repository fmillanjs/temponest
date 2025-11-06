# SaaS Empire Console — Implementation Roadmap

**Created**: 2025-11-05
**Status**: Scaffold Complete ✅
**Next Session**: Phase 1 Implementation

---

## Executive Summary

The SaaS Empire Console is a Next.js 15 web application that provides a unified interface to orchestrate your autonomous SaaS building system. The scaffold is now complete with all core structure, components, pages, and API routes in place.

**Location**: `/home/doctor/temponest/apps/console/`

---

## What Has Been Built (Session 1)

### ✅ Complete Scaffold

#### 1. Project Setup
- ✅ Next.js 15 with TypeScript
- ✅ Tailwind CSS with custom theme (NO PURPLE)
- ✅ shadcn/ui configuration
- ✅ Package.json with all dependencies
- ✅ ESLint, PostCSS, TypeScript configs
- ✅ .env.example with all required variables
- ✅ .gitignore and .dockerignore

#### 2. Design System
- ✅ Custom color palette: Slate base + Emerald/Sky/Amber/Rose accents
- ✅ Typography: Inter font family
- ✅ Rounded 2xl borders, soft shadows
- ✅ No purple/violet/indigo hues (per design constraint)

#### 3. Database & Data Layer
- ✅ Prisma schema with 7 models:
  - Project, Run, Agent, Approval, User, AuditLog
- ✅ Enum types for status, roles, agent names
- ✅ Prisma client singleton pattern
- ✅ Zod schemas for validation

#### 4. Layout & Navigation
- ✅ Root layout with Inter font
- ✅ Dashboard layout with sidebar + header
- ✅ Sidebar with 10 navigation items
- ✅ Header with search bar and user menu
- ✅ Fully responsive design

#### 5. Core Components
- ✅ AgentStatusCard - Display agent health
- ✅ KpiBar - 5 key metrics
- ✅ QuickActions - 3 action cards
- ✅ RecentActivity - Activity feed
- ✅ FactoryMap - React Flow graph visualization
- ✅ Sidebar - Main navigation
- ✅ Header - Search and profile

#### 6. All Page Routes (10 Sections)
- ✅ `/dashboard` - Main dashboard with KPIs
- ✅ `/factory-map` - Graph visualization
- ✅ `/workflows` - Kanban board
- ✅ `/projects` - Project list
- ✅ `/projects/[slug]` - Project detail
- ✅ `/agents` - Agent grid
- ✅ `/wizards` - Wizard list
- ✅ `/wizards/single` - Single-SaaS wizard
- ✅ `/wizards/factory` - Factory wizard
- ✅ `/financials` - Financial models
- ✅ `/docs` - Documentation browser
- ✅ `/observability` - Logs & metrics
- ✅ `/settings` - Configuration

#### 7. API Routes (5 Endpoints)
- ✅ `POST /api/financials/run` - Run calculator
- ✅ `POST /api/wizard/single/step` - Single wizard step
- ✅ `POST /api/wizard/factory/step` - Factory wizard step
- ✅ `GET /api/agents/health` - Get agent status
- ✅ `POST /api/agents/health` - Update agent heartbeat
- ✅ `GET /api/git/summary` - Git status

#### 8. Utility Libraries
- ✅ `lib/utils.ts` - cn(), date formatters
- ✅ `lib/schemas.ts` - Zod schemas & types
- ✅ `lib/api.ts` - Client API utilities
- ✅ `lib/server/exec.ts` - Sandboxed script execution
- ✅ `lib/db/client.ts` - Prisma singleton

#### 9. Deployment
- ✅ Dockerfile (multi-stage with standalone output)
- ✅ .dockerignore
- ✅ Coolify-ready configuration
- ✅ README.md with full documentation

---

## File Structure Created

```
apps/console/
├── app/
│   ├── (dashboard)/
│   │   ├── layout.tsx
│   │   └── dashboard/page.tsx
│   ├── factory-map/page.tsx
│   ├── workflows/page.tsx
│   ├── projects/
│   │   ├── page.tsx
│   │   └── [slug]/page.tsx
│   ├── agents/page.tsx
│   ├── wizards/
│   │   ├── page.tsx
│   │   ├── single/page.tsx
│   │   └── factory/page.tsx
│   ├── financials/page.tsx
│   ├── docs/page.tsx
│   ├── observability/page.tsx
│   ├── settings/page.tsx
│   ├── api/
│   │   ├── financials/run/route.ts
│   │   ├── wizard/
│   │   │   ├── single/step/route.ts
│   │   │   └── factory/step/route.ts
│   │   ├── agents/health/route.ts
│   │   └── git/summary/route.ts
│   ├── layout.tsx
│   └── page.tsx
├── components/
│   ├── AgentStatusCard.tsx
│   ├── KpiBar.tsx
│   ├── QuickActions.tsx
│   ├── RecentActivity.tsx
│   ├── FactoryMap.tsx
│   ├── Sidebar.tsx
│   └── Header.tsx
├── lib/
│   ├── server/
│   │   └── exec.ts
│   ├── db/
│   │   └── client.ts
│   ├── api.ts
│   ├── schemas.ts
│   └── utils.ts
├── prisma/
│   └── schema.prisma
├── styles/
│   └── globals.css
├── public/
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.ts
├── postcss.config.js
├── components.json
├── .env.example
├── .gitignore
├── .dockerignore
├── .eslintrc.json
├── Dockerfile
└── README.md
```

**Total Files Created**: 50+

---

## Next Steps — Phase-by-Phase Implementation

### Phase 1: Foundation & Data (Week 1-2)

#### Tasks:
1. **Database Setup**
   - [ ] Set up PostgreSQL (check if Docker container exists)
   - [ ] Run `npm install` in apps/console
   - [ ] Configure DATABASE_URL in .env
   - [ ] Run `npx prisma db push`
   - [ ] Seed initial data (7 agents)

2. **Make Pages Dynamic**
   - [ ] Replace mock data with Prisma queries
   - [ ] Dashboard: Fetch real agent data
   - [ ] Agents: Query from database
   - [ ] Projects: Query from database

3. **Test Basic Flow**
   - [ ] Start dev server: `npm run dev`
   - [ ] Navigate through all pages
   - [ ] Verify no TypeScript errors
   - [ ] Test responsive design

4. **Git Commit**
   - [ ] Commit all scaffold files
   - [ ] Message: "feat: complete SaaS Empire Console scaffold"

**Deliverable**: Working console with database-driven pages

---

### Phase 2: Interactive Features (Week 3-4)

#### Tasks:
1. **Factory Map Enhancements**
   - [ ] Make nodes clickable (side panel with details)
   - [ ] Add node types with custom styling
   - [ ] Fetch real data from Projects/Agents/Infrastructure
   - [ ] Add zoom controls, minimap

2. **Workflows Kanban**
   - [ ] Implement drag-and-drop with dnd-kit
   - [ ] Connect to Project status updates
   - [ ] Add card actions (view, edit, delete)
   - [ ] Real-time status badges

3. **Project Detail Pages**
   - [ ] Build history table with Run data
   - [ ] Log viewer for each run
   - [ ] Artifacts display (JSON viewer)
   - [ ] Quick actions (rerun, approve, cancel)

4. **Git Commit**
   - [ ] Commit interactive features
   - [ ] Message: "feat: add Factory Map interactions and Workflows kanban"

**Deliverable**: Fully interactive Factory Map and Workflows

---

### Phase 3: Wizards & Streaming (Week 5-6)

#### Tasks:
1. **Single-SaaS Wizard**
   - [ ] Multi-step form with React Hook Form
   - [ ] Auto-save to localStorage
   - [ ] Stream logs from API using ReadableStream
   - [ ] Real-time progress indicators
   - [ ] Retry/skip functionality

2. **Factory Wizard**
   - [ ] 4-week phase breakdown
   - [ ] Infrastructure setup steps
   - [ ] Agent configuration UI
   - [ ] Template selection

3. **Approval Workflows**
   - [ ] Approval gates in wizard steps
   - [ ] Comment and decision UI
   - [ ] Email/notification triggers
   - [ ] Audit log entries

4. **Git Commit**
   - [ ] Commit wizard implementations
   - [ ] Message: "feat: implement streaming wizards with approval workflows"

**Deliverable**: Full wizard experiences with streaming logs

---

### Phase 4: Financials & Calculators (Week 7-8)

#### Tasks:
1. **Calculator Integration**
   - [ ] Form inputs for each calculator type
   - [ ] Stream results from Python script
   - [ ] Chart visualizations with recharts
   - [ ] Save results to Run table

2. **Financial Dashboard**
   - [ ] MRR/ARR trend charts
   - [ ] Payback period calculator
   - [ ] Sensitivity analysis sliders
   - [ ] Export to CSV/JSON

3. **Projections**
   - [ ] Multi-product portfolio view
   - [ ] Growth scenarios
   - [ ] CAC/LTV modeling

4. **Git Commit**
   - [ ] Commit financial features
   - [ ] Message: "feat: add financial modeling and calculator integrations"

**Deliverable**: Complete financial modeling suite

---

### Phase 5: Observability & Monitoring (Week 9-10)

#### Tasks:
1. **Log Streaming**
   - [ ] Real-time log viewer with auto-scroll
   - [ ] Filter by agent, project, level
   - [ ] Search functionality
   - [ ] Export logs

2. **Langfuse Integration**
   - [ ] Deep links to traces
   - [ ] Session grouping by runId
   - [ ] Cost tracking

3. **Metrics Dashboard**
   - [ ] Job queue visualization
   - [ ] Success rate charts
   - [ ] Duration histograms
   - [ ] Alert thresholds

4. **Git Commit**
   - [ ] Commit observability features
   - [ ] Message: "feat: add comprehensive observability and monitoring"

**Deliverable**: Production-grade observability

---

### Phase 6: Auth & Security (Week 11-12)

#### Tasks:
1. **Better Auth Setup**
   - [ ] Install and configure Better Auth
   - [ ] Email/password authentication
   - [ ] Session management
   - [ ] Protected routes

2. **Role-Based Access**
   - [ ] Owner/Collaborator/ReadOnly roles
   - [ ] Permission checks on API routes
   - [ ] UI elements hidden by role

3. **Security Hardening**
   - [ ] Rate limiting on API routes
   - [ ] CSRF protection
   - [ ] Secure headers
   - [ ] Secret management

4. **Git Commit**
   - [ ] Commit auth and security
   - [ ] Message: "feat: implement authentication and role-based access control"

**Deliverable**: Secure multi-user system

---

### Phase 7: Polish & UX (Week 13-14)

#### Tasks:
1. **Command Palette**
   - [ ] ⌘K shortcut with cmdk
   - [ ] Quick navigation
   - [ ] Action execution
   - [ ] Search everything

2. **Notifications**
   - [ ] Toast system for actions
   - [ ] Real-time notifications bell
   - [ ] Notification preferences

3. **Documentation Browser**
   - [ ] Parse markdown from docs/
   - [ ] Syntax highlighting
   - [ ] Copy-to-clipboard for code
   - [ ] Search with fuzzy matching

4. **Performance**
   - [ ] Image optimization
   - [ ] Code splitting
   - [ ] React Query for caching
   - [ ] Lighthouse audit

5. **Git Commit**
   - [ ] Commit polish and UX improvements
   - [ ] Message: "feat: add command palette and polish UX"

**Deliverable**: Production-ready polish

---

## Deployment Checklist

### Pre-Deploy
- [ ] Run `npm run build` — verify no errors
- [ ] Test production build locally: `npm start`
- [ ] Run Lighthouse audit (aim for 90+ scores)
- [ ] Security audit: `npm audit`
- [ ] Database migrations ready

### Coolify Deploy
- [ ] Create new Coolify project
- [ ] Set environment variables from .env.example
- [ ] Connect to PostgreSQL service
- [ ] Build and deploy Docker image
- [ ] Run database migrations: `npx prisma db push`
- [ ] Verify health check endpoint
- [ ] Set up domain and SSL

### Post-Deploy
- [ ] Smoke test all major flows
- [ ] Monitor error logs
- [ ] Set up backup schedule
- [ ] Configure alerting (Sentry, PagerDuty)

---

## Critical Dependencies to Install

Before starting Phase 1, run in `apps/console/`:

```bash
npm install
```

This installs:
- Next.js 15 + React 19 RC
- Tailwind + shadcn/ui components
- Prisma + @prisma/client
- React Flow + Recharts
- Zod for validation
- Better Auth (later)
- All @radix-ui primitives

---

## Database Setup

### Option 1: Check for Existing Docker Container
```bash
docker ps -a | grep postgres
```

If exists:
```bash
docker start <container-id>
```

### Option 2: New PostgreSQL with Docker
```bash
docker run -d \
  --name saas-empire-db \
  -e POSTGRES_USER=saasuser \
  -e POSTGRES_PASSWORD=saaspass \
  -e POSTGRES_DB=saas_empire \
  -p 5432:5432 \
  postgres:14-alpine
```

### Set DATABASE_URL in .env
```
DATABASE_URL="postgresql://saasuser:saaspass@localhost:5432/saas_empire?schema=public"
```

### Initialize
```bash
cd apps/console
npx prisma db push
```

---

## Testing Strategy

### Manual Testing (Each Phase)
1. Navigate to every page
2. Test all interactive elements
3. Check console for errors
4. Verify responsive design (mobile/tablet/desktop)
5. Test dark mode (if implemented)

### Automated Testing (Phase 7+)
- [ ] Unit tests with Vitest
- [ ] Component tests with Testing Library
- [ ] E2E tests with Playwright
- [ ] API tests with Supertest

---

## Performance Targets

- **Lighthouse Score**: 90+ (all metrics)
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **Bundle Size**: < 300KB initial JS

---

## Monitoring & Analytics

### Setup (Phase 5)
1. **Error Tracking**: Sentry or Rollbar
2. **Performance**: Vercel Analytics or Plausible
3. **Logging**: Datadog or Logtail
4. **Uptime**: UptimeRobot or Pingdom

---

## Known Limitations & Future Work

### Current Limitations
- Mock data in most pages (Phase 1 will fix)
- No authentication (Phase 6)
- No real-time updates (WebSockets in future)
- Limited error handling (Phase 2+)

### Future Enhancements
- [ ] Mobile app (React Native)
- [ ] CLI companion tool
- [ ] Slack/Discord bot integration
- [ ] AI assistant (ChatGPT plugin)
- [ ] Template marketplace
- [ ] Multi-tenant support

---

## Quick Start for Next Session

```bash
# 1. Navigate to console
cd /home/doctor/temponest/apps/console

# 2. Install dependencies
npm install

# 3. Set up environment
cp .env.example .env
# Edit .env with your DATABASE_URL

# 4. Initialize database
npx prisma db push

# 5. Start dev server
npm run dev

# 6. Open browser
# http://localhost:3000/dashboard
```

---

## Success Criteria

### Phase 1 Complete When:
- ✅ All pages load without errors
- ✅ Database queries return real data
- ✅ Agent status updates dynamically
- ✅ Project list shows all projects
- ✅ No TypeScript compilation errors

### Phase 2 Complete When:
- ✅ Factory Map nodes are clickable
- ✅ Workflows kanban supports drag-and-drop
- ✅ Project detail shows full history
- ✅ All interactions feel smooth

### Phase 3 Complete When:
- ✅ Wizards stream logs in real-time
- ✅ Approval workflows function end-to-end
- ✅ Steps can be retried/skipped
- ✅ Progress persists across sessions

### MVP Launch Ready When:
- ✅ All 7 phases complete
- ✅ Authentication working
- ✅ Deployed to Coolify
- ✅ Documentation complete
- ✅ Performance targets met

---

## Communication Plan

### Progress Updates
- Daily commits with clear messages
- Weekly progress summary
- Blockers raised immediately

### Documentation
- Update this roadmap as phases complete
- Maintain CHANGELOG.md
- Update README.md with new features

---

## Resources & References

### Design
- shadcn/ui docs: https://ui.shadcn.com
- Tailwind docs: https://tailwindcss.com
- React Flow docs: https://reactflow.dev

### Backend
- Next.js App Router: https://nextjs.org/docs/app
- Prisma docs: https://www.prisma.io/docs
- Zod docs: https://zod.dev

### Deployment
- Coolify docs: https://coolify.io/docs
- Docker best practices: https://docs.docker.com/develop/dev-best-practices

---

## Notes

- **NO PURPLE** is a hard constraint — use Slate/Sky/Emerald/Amber/Rose only
- Commit continuously (per user instructions)
- Always check for existing Docker containers before creating new ones
- All scripts in `/home/doctor/temponest/cli/` and `/home/doctor/temponest/tools/`
- Factory map should eventually show real infrastructure from Coolify/EC2

---

## Changelog

**2025-11-05**: Scaffold complete
- All 50+ files created
- Directory structure established
- Ready for Phase 1 implementation

---

**End of Roadmap**

Next session: Start Phase 1 — Database Setup & Dynamic Pages
