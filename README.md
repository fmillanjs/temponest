# 🚀 TempoNest

**Enterprise-Grade SaaS Project Generator Platform**

TempoNest is a powerful platform for generating and deploying SaaS applications at scale. Built with modern technologies and best practices, it embodies all essential SaaS design principles: extensibility, scalability, reliability, observability, security, and more.

## 🎯 Value Propositions

- **Rapid Deployment**: Generate SaaS projects in minutes, not weeks
- **Multi-Tenant Architecture**: Scalable from day one with proper data isolation
- **Type-Safe Development**: End-to-end type safety with TypeScript, Prisma, and tRPC
- **Production-Ready**: Built with enterprise-grade security and observability
- **Developer Experience**: Modern tooling with hot reload, linting, and automation
- **Extensible**: Plugin architecture and composable packages

## 🏗️ Architecture

TempoNest is built as a **monorepo** using pnpm workspaces and Turbo for optimal development experience.

### 📦 Structure

```
temponest/
├── apps/
│   ├── web/              # Customer-facing Next.js 15 app
│   ├── admin/            # Admin dashboard (Next.js 15)
│   └── workers/          # Background job processor (BullMQ)
├── packages/
│   ├── database/         # Prisma schema & client
│   ├── api/              # tRPC API routers
│   ├── auth/             # Better Auth configuration
│   ├── ui/               # Shared UI components (shadcn/ui)
│   ├── email/            # Email templates (React Email)
│   ├── validators/       # Zod schemas
│   ├── types/            # Shared TypeScript types
│   ├── utils/            # Utility functions
│   └── config/           # Shared configs (ESLint, TS, Tailwind)
└── docker/               # Dockerfiles for each service
```

## 🛠️ Tech Stack

### Frontend
- **Next.js 15** - App Router, Server Components
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - High-quality React components

### Backend
- **tRPC** - End-to-end type-safe APIs
- **Prisma** - Type-safe database ORM
- **PostgreSQL** - Relational database
- **Redis** - Caching and job queues
- **Better Auth** - Modern authentication

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Local development
- **Coolify** - Self-hosted deployment
- **GitHub Actions** - CI/CD
- **Turbo** - Monorepo build system
- **pnpm** - Fast, efficient package manager

### Integrations
- **Stripe** - Subscription billing
- **Resend** - Transactional emails
- **Plausible** - Self-hosted analytics
- **hCaptcha** - Bot protection

## 🚀 Quick Start

### Prerequisites

- **Node.js** 20+
- **pnpm** 9+
- **Docker** & Docker Compose
- **Git**

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/temponest.git
   cd temponest
   ```

2. **Run the setup script**
   ```bash
   ./scripts/setup.sh
   ```

   This will:
   - Install all dependencies
   - Copy `.env.example` to `.env`
   - Start Docker services (PostgreSQL, Redis, Plausible, MailHog, MinIO)
   - Initialize the database
   - Seed sample data

3. **Update environment variables**
   ```bash
   # Edit .env with your actual values
   nano .env
   ```

4. **Start development servers**
   ```bash
   pnpm dev
   ```

   This starts:
   - Web app: http://localhost:3000
   - Admin app: http://localhost:3001
   - Workers: Background process

### 🐳 Docker Services

The local development environment includes:

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5432 | Main database |
| Redis | 6379 | Cache & job queue |
| Plausible | 8000 | Analytics dashboard |
| MailHog | 8025 | Email testing UI |
| MinIO | 9001 | S3-compatible storage console |

**Access services:**
- Plausible Analytics: http://localhost:8000
- MailHog (Emails): http://localhost:8025
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- Prisma Studio: `pnpm db:studio`

## 📚 Development

### Available Commands

```bash
# Development
pnpm dev                 # Start all apps
pnpm dev:web            # Start web app only
pnpm dev:admin          # Start admin app only
pnpm dev:workers        # Start workers only

# Building
pnpm build              # Build all packages/apps
pnpm build:web          # Build web app only

# Database
pnpm db:generate        # Generate Prisma client
pnpm db:push            # Push schema to DB (dev)
pnpm db:migrate         # Create migration
pnpm db:migrate:deploy  # Apply migrations (prod)
pnpm db:seed            # Seed database
pnpm db:studio          # Open Prisma Studio

# Testing
pnpm test               # Run all tests
pnpm test:watch         # Run tests in watch mode

# Linting & Formatting
pnpm lint               # Lint all packages
pnpm format             # Format all files
pnpm type-check         # TypeScript type checking

# Docker
pnpm docker:dev         # Start Docker services
pnpm docker:dev:down    # Stop Docker services
pnpm docker:dev:clean   # Stop and remove volumes

# Cleanup
pnpm clean              # Clean all build artifacts
```

### Project Structure

```
apps/web/                # Customer-facing application
├── app/                 # Next.js App Router
│   ├── (auth)/         # Auth pages group
│   ├── (dashboard)/    # Dashboard pages group
│   ├── api/            # API routes
│   └── layout.tsx      # Root layout
├── components/         # React components
├── lib/                # Utilities & helpers
└── public/             # Static assets

packages/database/       # Database layer
├── prisma/
│   ├── schema.prisma   # Database schema
│   ├── migrations/     # Migration files
│   └── seed.ts         # Seed script
└── src/
    └── index.ts        # Prisma client export

packages/api/            # tRPC API
├── src/
│   ├── routers/        # API routers
│   ├── context.ts      # Request context
│   └── root.ts         # Root router
```

## 🧪 Testing

We use **Vitest** for unit/integration tests and **Playwright** for E2E tests.

```bash
# Unit & Integration Tests
pnpm test
pnpm test:watch

# E2E Tests (coming soon)
pnpm test:e2e
```

## 🔐 Security

### Built-in Security Features

- ✅ **Authentication**: Better Auth with email/password + OAuth
- ✅ **Authorization**: Role-based access control (RBAC)
- ✅ **Rate Limiting**: hCaptcha + API rate limits
- ✅ **SQL Injection**: Prisma parameterized queries
- ✅ **XSS Protection**: React auto-escaping
- ✅ **CSRF Protection**: Better Auth built-in
- ✅ **Environment Variables**: Never commit secrets
- ✅ **Audit Logs**: Complete activity tracking

### Security Best Practices

1. Always use environment variables for secrets
2. Never commit `.env` files
3. Use API keys with proper scopes
4. Implement rate limiting on all public endpoints
5. Keep dependencies updated
6. Review audit logs regularly

## 📊 Database Schema

The database is designed for **multi-tenancy** with the following key models:

- **User**: Authentication and profile
- **Organization**: Multi-tenant workspace
- **Project**: Generated SaaS applications
- **Template**: Project templates
- **Deployment**: Deployment history
- **Activity**: Audit logs

See `packages/database/prisma/schema.prisma` for the complete schema.

## 🚢 Deployment

### Coolify Deployment

TempoNest is designed to be deployed on **Coolify**, a self-hosted PaaS.

1. Push your code to GitHub
2. Create a new project in Coolify
3. Connect your GitHub repository
4. Configure environment variables
5. Deploy!

Each service (web, admin, workers) can be deployed independently.

### Environment Variables

See `.env.example` for all required environment variables.

**Critical variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `BETTER_AUTH_SECRET` - Auth secret (32+ chars)
- `STRIPE_SECRET_KEY` - Stripe API key
- `RESEND_API_KEY` - Resend API key

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'feat: add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Commit Convention

We use **Conventional Commits**:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

## 📖 Documentation

- [Architecture](./ARCHITECTURE.md) - System design and patterns
- [API Documentation](./docs/API.md) - tRPC API reference
- [Deployment Guide](./docs/DEPLOYMENT.md) - Coolify deployment
- [Contributing Guide](./CONTRIBUTING.md) - Contribution guidelines

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

Built with amazing open-source tools:

- [Next.js](https://nextjs.org/) by Vercel
- [tRPC](https://trpc.io/) by tRPC team
- [Prisma](https://www.prisma.io/) by Prisma team
- [Better Auth](https://www.better-auth.com/) by Better Auth team
- [shadcn/ui](https://ui.shadcn.com/) by shadcn
- [Tailwind CSS](https://tailwindcss.com/) by Tailwind Labs
- [Coolify](https://coolify.io/) by Coolify team
- [Plausible](https://plausible.io/) by Plausible Analytics

## 💬 Support

- **Documentation**: [docs.temponest.com](https://docs.temponest.com)
- **GitHub Issues**: [github.com/your-org/temponest/issues](https://github.com/your-org/temponest/issues)
- **Discord**: [discord.gg/temponest](https://discord.gg/temponest)
- **Email**: support@temponest.com

---

**Built with ❤️ by the TempoNest Team**

*Empowering developers to ship SaaS applications faster*
