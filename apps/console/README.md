# SaaS Empire Console

A modern web interface to orchestrate your SaaS building empire — agents, wizards, calculators, factory map, and documentation.

## Features

- **Dashboard**: Monitor KPIs, agent health, and quick actions
- **Factory Map**: Visualize products, pipelines, agents, and infrastructure
- **Workflows**: Kanban board to track projects through the pipeline
- **Projects**: Manage your SaaS products with build history
- **Agents**: Monitor and manage 7 autonomous agents
- **Wizards**: Interactive guides for single-SaaS and factory setup
- **Financials**: Model projections with integrated calculators
- **Docs**: Browse guides, tutorials, and references
- **Observability**: Logs, traces, metrics, and job queue monitoring
- **Settings**: Configure paths, risk controls, and API tokens

## Tech Stack

- **Next.js 15** (App Router) + TypeScript
- **Tailwind CSS** + shadcn/ui components
- **React Flow** for graph visualization
- **Prisma** + PostgreSQL for data persistence
- **Better Auth** for authentication
- **Zod** for schema validation
- **Coolify** deployment ready

## Design System

- **Colors**: Slate base with Emerald (success), Sky (info), Amber (warn), Rose (danger)
- **No Purple**: Following strict design constraint
- **Typography**: Inter font
- **Components**: Rounded corners (2xl), soft shadows, minimal aesthetic

## Getting Started

### Prerequisites

- Node.js 20+
- PostgreSQL 14+
- npm or pnpm

### Installation

1. Install dependencies:

```bash
npm install
```

2. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Initialize database:

```bash
npm run db:generate
npm run db:push
```

4. Run development server:

```bash
npm run dev
```

5. Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard)

## Project Structure

```
apps/console/
├── app/                      # Next.js App Router
│   ├── (dashboard)/          # Dashboard layout group
│   │   └── dashboard/        # Main dashboard
│   ├── factory-map/          # Factory visualization
│   ├── workflows/            # Kanban board
│   ├── projects/             # Project management
│   ├── agents/               # Agent monitoring
│   ├── wizards/              # Interactive wizards
│   ├── financials/           # Financial modeling
│   ├── docs/                 # Documentation
│   ├── observability/        # Logs & metrics
│   ├── settings/             # Configuration
│   └── api/                  # API routes
├── components/               # React components
├── lib/                      # Utilities & helpers
│   ├── server/               # Server-side utilities
│   ├── db/                   # Database client
│   ├── api.ts                # Client API utils
│   ├── schemas.ts            # Zod schemas
│   └── utils.ts              # Common utilities
├── prisma/                   # Database schema
├── styles/                   # Global styles
└── public/                   # Static assets
```

## API Routes

- `POST /api/financials/run` - Run financial calculator
- `POST /api/wizard/single/step` - Execute single-SaaS wizard step
- `POST /api/wizard/factory/step` - Execute factory wizard step
- `GET /api/agents/health` - Get agent health status
- `POST /api/agents/health` - Update agent heartbeat
- `GET /api/git/summary` - Get git repository summary

## Database Models

- **Project**: SaaS products and their metadata
- **Run**: Build runs, wizard steps, calculations
- **Agent**: Agent configurations and health
- **Approval**: Human-in-the-loop approvals
- **User**: User accounts and roles
- **AuditLog**: Action audit trail

## Deployment

### Docker (Coolify)

```bash
docker build -t saas-empire-console .
docker run -p 3000:3000 --env-file .env saas-empire-console
```

### Manual

```bash
npm run build
npm start
```

## Development

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run db:generate` - Generate Prisma client
- `npm run db:push` - Push schema to database
- `npm run db:studio` - Open Prisma Studio

## Security

- Role-based access control (Owner, Collaborator, ReadOnly)
- Approval gates for destructive actions
- Sandboxed script execution with allowlists
- Secret redaction in logs
- Input validation with Zod schemas

## Roadmap

### Phase 1 (Weeks 1-2) ✅
- Dashboard, Agents, Financials, Docs

### Phase 2 (Weeks 3-4)
- Factory Map (React Flow)
- Workflows (Kanban)
- Project detail pages

### Phase 3 (Weeks 5-6)
- Full Wizards with streaming logs
- Approval workflows
- Real-time updates

### Phase 4 (Ongoing)
- Observability deep-links
- Multi-user auth
- Advanced metrics
- Command palette (⌘K)

## Contributing

This is a private tool for building SaaS products. Follow the existing patterns and keep the design minimal and functional.

## License

Private - All Rights Reserved
