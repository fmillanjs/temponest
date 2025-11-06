# SaaS Empire Console — File Structure

**Created**: 2025-11-05
**Status**: Complete Scaffold ✅
**Total Files**: 50+

---

## Directory Tree

```
apps/console/
├── app/                                    # Next.js App Router
│   ├── (dashboard)/                        # Dashboard layout group
│   │   ├── layout.tsx                      # Sidebar + Header layout
│   │   └── dashboard/page.tsx              # Main dashboard page
│   │
│   ├── factory-map/page.tsx                # React Flow graph visualization
│   ├── workflows/page.tsx                  # Kanban board
│   │
│   ├── projects/                           # Project management
│   │   ├── page.tsx                        # Project list
│   │   └── [slug]/page.tsx                 # Project detail (dynamic)
│   │
│   ├── agents/page.tsx                     # Agent monitoring
│   │
│   ├── wizards/                            # Interactive wizards
│   │   ├── page.tsx                        # Wizard list
│   │   ├── single/page.tsx                 # Single-SaaS wizard (8 weeks)
│   │   └── factory/page.tsx                # Factory wizard (4 weeks)
│   │
│   ├── financials/page.tsx                 # Financial modeling
│   ├── docs/page.tsx                       # Documentation browser
│   ├── observability/page.tsx              # Logs & metrics
│   ├── settings/page.tsx                   # Configuration
│   │
│   ├── api/                                # API routes
│   │   ├── financials/run/route.ts         # Run calculator
│   │   ├── wizard/
│   │   │   ├── single/step/route.ts        # Single-SaaS step
│   │   │   └── factory/step/route.ts       # Factory step
│   │   ├── agents/health/route.ts          # Agent health API
│   │   └── git/summary/route.ts            # Git status API
│   │
│   ├── layout.tsx                          # Root layout (Inter font)
│   └── page.tsx                            # Home (redirects to /dashboard)
│
├── components/                             # React components
│   ├── AgentStatusCard.tsx                 # Agent health card
│   ├── KpiBar.tsx                          # 5 KPI metrics
│   ├── QuickActions.tsx                    # 3 quick action cards
│   ├── RecentActivity.tsx                  # Activity feed
│   ├── FactoryMap.tsx                      # React Flow graph
│   ├── Sidebar.tsx                         # Main navigation (10 items)
│   └── Header.tsx                          # Search + profile
│
├── lib/                                    # Utilities
│   ├── server/
│   │   └── exec.ts                         # Sandboxed script execution
│   ├── db/
│   │   └── client.ts                       # Prisma singleton
│   ├── api.ts                              # Client API utilities
│   ├── schemas.ts                          # Zod schemas + types
│   └── utils.ts                            # cn(), date formatters
│
├── prisma/
│   └── schema.prisma                       # Database schema (7 models)
│
├── styles/
│   └── globals.css                         # Global CSS + Tailwind
│
├── public/                                 # Static assets (empty)
│
├── package.json                            # Dependencies (50+ packages)
├── tsconfig.json                           # TypeScript config
├── next.config.js                          # Next.js config (standalone)
├── tailwind.config.ts                      # Custom theme (NO PURPLE)
├── postcss.config.js                       # PostCSS config
├── components.json                         # shadcn/ui config
├── .env.example                            # Environment variables template
├── .gitignore                              # Git ignore rules
├── .dockerignore                           # Docker ignore rules
├── .eslintrc.json                          # ESLint config
├── Dockerfile                              # Multi-stage Docker build
└── README.md                               # Full documentation
```

---

## Key Files by Purpose

### Configuration (8 files)
- `package.json` - Dependencies and scripts
- `tsconfig.json` - TypeScript configuration
- `next.config.js` - Next.js settings (standalone output)
- `tailwind.config.ts` - Custom theme (Slate/Emerald/Sky/Amber/Rose)
- `postcss.config.js` - PostCSS with Tailwind & Autoprefixer
- `components.json` - shadcn/ui configuration
- `.env.example` - Environment variables template
- `.eslintrc.json` - ESLint rules

### Layout & UI (9 files)
- `app/layout.tsx` - Root layout with Inter font
- `app/(dashboard)/layout.tsx` - Dashboard layout with sidebar
- `components/Sidebar.tsx` - Main navigation (10 sections)
- `components/Header.tsx` - Search bar + profile
- `components/AgentStatusCard.tsx` - Agent health display
- `components/KpiBar.tsx` - 5 KPI metrics
- `components/QuickActions.tsx` - 3 quick action cards
- `components/RecentActivity.tsx` - Activity feed
- `components/FactoryMap.tsx` - React Flow visualization

### Pages (13 files)
1. `/dashboard` - Main dashboard with KPIs + agents
2. `/factory-map` - Graph visualization
3. `/workflows` - Kanban board
4. `/projects` - Project list
5. `/projects/[slug]` - Project detail (dynamic)
6. `/agents` - Agent grid
7. `/wizards` - Wizard list
8. `/wizards/single` - Single-SaaS wizard (8 weeks)
9. `/wizards/factory` - Factory wizard (4 weeks)
10. `/financials` - Financial models + projections
11. `/docs` - Documentation browser
12. `/observability` - Logs, traces, metrics
13. `/settings` - Configuration

### API Routes (5 endpoints)
- `POST /api/financials/run` - Run calculator script
- `POST /api/wizard/single/step` - Execute single-SaaS wizard step
- `POST /api/wizard/factory/step` - Execute factory wizard step
- `GET /api/agents/health` - Get agent health status
- `POST /api/agents/health` - Update agent heartbeat
- `GET /api/git/summary` - Get git repository summary

### Utilities (5 files)
- `lib/utils.ts` - cn(), date formatters (formatDate, formatDateTime, formatRelativeTime)
- `lib/schemas.ts` - Zod schemas (Project, Run, Agent, Approval, User, AuditLog)
- `lib/api.ts` - Client API utilities (fetchApi, streamApi)
- `lib/server/exec.ts` - Sandboxed script execution (execStream, execCollect, sanitizeArgs)
- `lib/db/client.ts` - Prisma singleton pattern

### Database (1 file)
- `prisma/schema.prisma` - 7 models, 6 enums, full relations

### Deployment (3 files)
- `Dockerfile` - Multi-stage build (deps → builder → runner)
- `.dockerignore` - Exclude node_modules, .next, .git
- `README.md` - Full documentation (features, setup, deployment)

---

## Models & Schemas

### Database Models (Prisma)
1. **Project** - SaaS products (id, name, slug, type, status, repoUrl)
2. **Run** - Build runs, wizard steps (id, projectId, kind, step, status, logs, artifacts)
3. **Agent** - Agent configs (id, name, status, lastHeartbeat, version, config)
4. **Approval** - Human-in-the-loop gates (id, runId, step, status, comment)
5. **User** - User accounts (id, email, name, role)
6. **AuditLog** - Action tracking (id, userId, action, resource, details)

### Enums
- ProjectType: single, portfolio
- ProjectStatus: idle, research, build, qa, deploy, live
- RunKind: wizard, build, deploy, calc
- RunStatus: pending, running, success, failed, cancelled
- AgentName: Overseer, Developer, Designer, UX, QA, Security, DevOps
- AgentStatus: healthy, degraded, down
- ApprovalStatus: pending, approved, changes_requested
- UserRole: owner, collaborator, readonly

---

## Component Hierarchy

```
RootLayout (Inter font)
└── DashboardLayout (Sidebar + Header)
    ├── Sidebar (10 nav items)
    ├── Header (Search + Profile)
    └── Page Content
        ├── KpiBar (5 metrics)
        ├── AgentStatusCard (x7)
        ├── QuickActions (3 cards)
        ├── RecentActivity
        ├── FactoryMap (React Flow)
        └── ... (page-specific content)
```

---

## Color System (NO PURPLE)

### Base Colors (Slate)
- 50-100: Backgrounds
- 200-300: Borders
- 400-500: Muted text
- 600-700: Body text
- 800-900: Headers, dark UI

### Accent Colors
- **Success**: Emerald (#10b981)
- **Info**: Sky (#38bdf8)
- **Warn**: Amber (#f59e0b)
- **Danger**: Rose (#f43f5e)

### Forbidden
- ❌ Purple, Violet, Indigo, Magenta

---

## Dependencies (50+ packages)

### Core
- next@^15.0.2
- react@^19.0.0-rc.0
- react-dom@^19.0.0-rc.0
- typescript@^5.6.3

### Database
- @prisma/client@^5.20.0
- prisma@^5.20.0

### Styling
- tailwindcss@^3.4.13
- tailwindcss-animate@^1.0.7
- class-variance-authority@^0.7.0
- clsx@^2.1.1
- tailwind-merge@^2.5.2

### UI Components (@radix-ui)
- react-dialog, react-dropdown-menu, react-label
- react-separator, react-slot, react-tabs
- react-toast, react-tooltip

### Visualization
- reactflow@^11.11.4
- recharts@^2.12.7

### Utilities
- zod@^3.23.8
- date-fns@^3.6.0
- lucide-react@^0.445.0
- cmdk@^1.0.0

### Auth (future)
- better-auth@^1.0.0

---

## Scripts

```bash
npm run dev        # Start dev server (port 3000)
npm run build      # Build for production
npm start          # Start production server
npm run lint       # Run ESLint
npm run db:generate  # Generate Prisma client
npm run db:push      # Push schema to database
npm run db:studio    # Open Prisma Studio
```

---

## Environment Variables

Required in `.env`:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/saas_empire"
NEXT_PUBLIC_APP_URL="http://localhost:3000"
WORKDIR="/home/doctor/temponest"
AUTH_SECRET="your-secret-key"
AUTH_URL="http://localhost:3000"
NODE_ENV="development"
```

Optional:
- LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY
- GITHUB_TOKEN
- COOLIFY_API_URL, COOLIFY_API_TOKEN

---

## Quick Start Commands

```bash
cd /home/doctor/temponest/apps/console

# Install
npm install

# Setup
cp .env.example .env
# Edit .env with your DATABASE_URL

# Database
npx prisma db push

# Run
npm run dev

# Open http://localhost:3000/dashboard
```

---

## Git Commits

1. **cdfdea3** - feat: complete SaaS Empire Console scaffold (43 files)
2. **26d98ce** - feat: add utility libraries for SaaS Console (6 files)

---

## What's Next?

See `/home/doctor/temponest/SAAS-CONSOLE-ROADMAP.md` for the full implementation plan.

**Next Session**: Phase 1 — Database Setup & Dynamic Pages
