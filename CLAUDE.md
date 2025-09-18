# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TempoNest** is a comprehensive SaaS platform designed specifically for small retail stores in Mexico, leveraging WhatsApp as the primary communication channel for business operations, customer interactions, and notifications.

### Core Value Proposition
- **Localized Solution**: Tailored for Mexican small businesses with WhatsApp-centric operations
- **All-in-One Platform**: Complete business management from inventory to accounting
- **Mobile-First Design**: Optimized for smartphone usage with WhatsApp integration
- **Affordable & Scalable**: SaaS model suitable for small stores with growth potential

### Target Market
- Small retail stores (tiendas de abarrotas, papelerías, farmacias pequeñas)
- Businesses with 1-10 employees
- Stores currently using WhatsApp for customer communication
- Mexican market focus with peso currency support

## Technology Stack

### Frontend
- **Next.js 14+**: App Router, Server Components
- **TypeScript**: Type safety across the application
- **Tailwind CSS + shadcn/ui**: UI framework and components
- **React Query (TanStack Query)**: Server state management
- **Zustand**: Client state management
- **React Hook Form + Zod**: Form handling and validation
- **Recharts/Tremor**: Financial dashboards and analytics

### Backend & Database
- **Next.js API Routes / tRPC**: API layer
- **NextAuth.js**: Authentication with JWT sessions
- **PostgreSQL**: Primary relational database
- **Prisma ORM**: Type-safe database ORM with migrations
- **Redis**: Session management, notifications queue, WhatsApp message queue, cache

### External Integrations
- **WhatsApp Business API**: Official API integration for messaging
- **SAT Integration**: CFDI 4.0 invoice generation for Mexican tax compliance
- **Payment Gateways**: Mexican payment processors

### Infrastructure
- **Coolify**: Self-hosted PaaS for deployment
- **Docker**: Containerization for all services
- **MinIO**: Object storage for documents/receipts

## Core Modules & Architecture

### 1. Inventory Control (Critical Priority)
- Product catalog with SKU, barcode, descriptions
- Real-time stock levels with WhatsApp alerts
- Batch/lot tracking with expiration dates
- Multi-location inventory support

### 2. Sales & Point of Sale (Critical Priority)
- Quick sale interface with barcode scanning
- Multiple payment methods (cash, card, transfer)
- Receipt generation with WhatsApp delivery
- Offline mode with sync capability

### 3. Client Management (High Priority)
- Customer database with WhatsApp integration
- Purchase history and credit management
- Loyalty programs with automated WhatsApp communications

### 4. Financial Analysis & Reporting (High Priority)
- Real-time KPI dashboards
- Profit & loss statements
- Cash flow projections
- Sales analytics with WhatsApp report delivery

### 5. Additional Modules
- Provider Management
- Expense Control
- Employee & Salary Management
- Returns & Exchanges
- Accounting (SAT/CFDI compliance)
- Cash Flow Management

## Database Schema Patterns

### Multi-Tenant Structure
```prisma
model Organization {
  id            String   @id @default(cuid())
  name          String
  whatsappPhone String   @unique
  subscription  Subscription @relation(...)
  // All entities belong to organization
}

model User {
  id             String   @id @default(cuid())
  organizationId String
  role           Role     @default(CASHIER)
  permissions    Json     // Granular permissions
}
```

### Key Entities
- **Product**: SKU, barcode, pricing, stock levels
- **Sale**: Invoice generation, payment tracking, customer association
- **Customer**: WhatsApp integration, credit management, purchase history
- **InventoryMovement**: Stock tracking with movement types (SALE, PURCHASE, ADJUSTMENT, etc.)

## WhatsApp Integration Architecture

### Message Flow
1. **Webhook Handler**: Receives WhatsApp messages
2. **Message Processor**: Processes and classifies intent
3. **Business Logic**: Executes appropriate actions
4. **Response Sender**: Sends structured responses

### Message Types
- **Transactional**: Order confirmations, payment receipts
- **Notifications**: Low stock alerts, payment reminders
- **Interactive**: Product catalogs, quick replies, button templates

### Queue Management
Uses Redis for message queuing with priority levels (high/medium/low) and retry mechanisms.

## Development Commands

This project is in initial setup phase. Standard Next.js commands will apply:
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run type-check` - TypeScript type checking
- `npx prisma migrate dev` - Run database migrations
- `npx prisma studio` - Database admin interface

## Security & Compliance

### Mexican Regulations
- **SAT Compliance**: CFDI 4.0 invoice generation, RFC validation
- **Data Protection (LFPDPPP)**: Privacy notices, consent tracking
- **WhatsApp Business API**: Template approval, opt-in/opt-out management

### Security Measures
- Role-based access control (RBAC)
- Encryption at rest and in transit
- API rate limiting and authentication
- Audit logs for sensitive operations

## Key Development Considerations

1. **Mobile-First**: All interfaces must work well on smartphones
2. **WhatsApp-Centric**: Every major action should have WhatsApp integration
3. **Mexican Localization**: Currency (MXN), tax calculations (IVA 16%), SAT compliance
4. **Multi-Tenant**: All data queries must include organizationId
5. **Offline Capability**: Critical for small stores with unreliable internet
6. **Performance**: Optimized for low-bandwidth connections common in target market