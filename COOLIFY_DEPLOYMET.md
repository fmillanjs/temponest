# 🚀 SaaS Automation System - Coolify Deployment Guide

## Overview
This guide deploys the complete SaaS automation system as Coolify-managed services, utilizing Coolify's built-in features for databases, deployments, and scaling.

## Architecture in Coolify

```
Coolify Platform (Your EC2)
├── Services
│   ├── n8n-automation (Workflow engine)
│   ├── saas-api-gateway (API service)
│   ├── saas-dashboard (Admin panel)
│   └── saas-builder (Project generator)
├── Databases
│   ├── PostgreSQL (Main database)
│   └── Redis (Cache & queues)
├── Storage
│   └── S3 Compatible (MinIO)
└── Applications (Generated Projects)
    ├── client-project-1
    ├── client-project-2
    └── ... (auto-created)
```

## Step 1: Create Coolify Resources

### 1.1 Create a New Project in Coolify

1. Login to Coolify: `https://your-ec2-ip:8000`
2. Click "New Project"
3. Name: `saas-automation`
4. Description: `SaaS Automation Platform`

### 1.2 Create Environment

1. In the project, create environment: `production`
2. Set environment variables:

```env
# System Configuration
DOMAIN=yourdomain.com
NODE_ENV=production
SECRET_KEY=generate-random-32-char-string

# Database (will be auto-filled by Coolify)
DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}

# External Services
GITHUB_TOKEN=ghp_your_token
GITHUB_ORG=your-org
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
RESEND_API_KEY=re_xxx

# Coolify Integration
COOLIFY_API_TOKEN=${COOLIFY_TOKEN}
COOLIFY_INSTANCE_URL=http://localhost:3000
```

## Step 2: Deploy Core Services

### 2.1 PostgreSQL Database

**In Coolify UI:**
1. Go to your project → Add Resource → Database
2. Choose PostgreSQL 16
3. Configuration:
```yaml
Name: saas-db
Database: saasplatform
User: saasadmin
Password: [auto-generated]
Port: 5432
Volume: /data/postgres
```

### 2.2 Redis Cache

**In Coolify UI:**
1. Add Resource → Database
2. Choose Redis 7
3. Configuration:
```yaml
Name: saas-redis
Password: [auto-generated]
Port: 6379
Max Memory: 2GB
Volume: /data/redis
```

## Step 3: Deploy n8n Service

### 3.1 Create n8n Dockerfile

**File: `services/n8n/Dockerfile`**
```dockerfile
FROM n8nio/n8n:latest

USER root

# Install additional dependencies
RUN apk add --no-cache \
    git \
    openssh \
    postgresql-client \
    curl \
    jq

# Create directories for workflows and data
RUN mkdir -p /home/node/.n8n/workflows /home/node/.n8n/credentials /data

# Copy custom nodes if needed
COPY custom-nodes/ /home/node/.n8n/custom/

# Copy workflow templates
COPY workflows/ /home/node/.n8n/workflows/

USER node

EXPOSE 5678

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5678/healthz || exit 1
```

### 3.2 Create docker-compose for n8n

**File: `services/n8n/docker-compose.yml`**
```yaml
version: '3.8'

services:
  n8n:
    build: .
    container_name: saas-n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_HOST=${DOMAIN}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - N8N_PATH=/n8n/
      - WEBHOOK_URL=https://${DOMAIN}/n8n
      - N8N_ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=saas-db
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=${DB_PASSWORD}
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
      - GENERIC_TIMEZONE=America/New_York
      - N8N_METRICS=true
    volumes:
      - n8n-data:/home/node/.n8n
      - ./workflows:/home/node/.n8n/workflows
    networks:
      - coolify
    labels:
      - "coolify.managed=true"
      - "coolify.type=service"
      - "coolify.name=n8n-automation"

volumes:
  n8n-data:

networks:
  coolify:
    external: true
```

### 3.3 Deploy n8n in Coolify

1. In Coolify: Add Resource → Service → Docker Compose
2. Name: `n8n-automation`
3. Paste the docker-compose.yml
4. Deploy

## Step 4: Deploy API Gateway

### 4.1 Create API Gateway Application

**File: `services/api/Dockerfile`**
```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install pnpm
RUN npm install -g pnpm

# Copy package files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY . .

# Build TypeScript
RUN pnpm build

EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD node healthcheck.js || exit 1

CMD ["pnpm", "start"]
```

**File: `services/api/package.json`**
```json
{
  "name": "saas-api-gateway",
  "version": "1.0.0",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "express-rate-limit": "^7.1.5",
    "pg": "^8.11.3",
    "redis": "^4.6.10",
    "axios": "^1.6.2",
    "jsonwebtoken": "^9.0.2",
    "zod": "^3.22.4",
    "winston": "^3.11.0",
    "@prisma/client": "^5.7.0",
    "stripe": "^14.5.0"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "tsx": "^4.6.2",
    "@types/node": "^20.10.5",
    "@types/express": "^4.17.21",
    "prisma": "^5.7.0"
  }
}
```

**File: `services/api/src/index.ts`**
```typescript
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';
import { PrismaClient } from '@prisma/client';
import Redis from 'redis';
import { z } from 'zod';
import winston from 'winston';
import Stripe from 'stripe';

const app = express();
const prisma = new PrismaClient();
const redis = Redis.createClient({ url: process.env.REDIS_URL });
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, { apiVersion: '2023-10-16' });

// Logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

// Middleware
app.use(helmet());
app.use(cors());
app.use(express.json());

// Rate limiting
const apiLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res) => {
    res.status(429).json({
      error: 'Too many requests',
      retryAfter: 60
    });
  }
});

// Validation schemas
const CreateProjectSchema = z.object({
  projectName: z.string().min(3).max(50),
  description: z.string().optional(),
  template: z.enum(['nextjs-saas', 'api-backend', 'fullstack']).default('nextjs-saas'),
  features: z.array(z.string()).optional()
});

// Authentication middleware
async function authenticate(req: express.Request, res: express.Response, next: express.NextFunction) {
  const apiKey = req.headers['x-api-key'] as string;
  
  if (!apiKey) {
    return res.status(401).json({ error: 'API key required' });
  }
  
  try {
    // Check cache first
    const cached = await redis.get(`apikey:${apiKey}`);
    if (cached) {
      req.tenant = JSON.parse(cached);
      return next();
    }
    
    // Check database
    const tenant = await prisma.tenant.findUnique({
      where: { apiKey }
    });
    
    if (!tenant || tenant.status !== 'active') {
      return res.status(401).json({ error: 'Invalid API key' });
    }
    
    // Cache for 5 minutes
    await redis.setex(`apikey:${apiKey}`, 300, JSON.stringify(tenant));
    
    req.tenant = tenant;
    next();
  } catch (error) {
    logger.error('Authentication error:', error);
    res.status(500).json({ error: 'Authentication failed' });
  }
}

// Routes
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy',
    timestamp: new Date().toISOString(),
    services: {
      database: prisma ? 'connected' : 'disconnected',
      redis: redis.isReady ? 'connected' : 'disconnected'
    }
  });
});

// Create project endpoint
app.post('/api/projects', authenticate, apiLimiter, async (req, res) => {
  try {
    const data = CreateProjectSchema.parse(req.body);
    
    // Check tenant limits
    const projectCount = await prisma.project.count({
      where: { tenantId: req.tenant.id }
    });
    
    if (req.tenant.planLimits.projects !== -1 && projectCount >= req.tenant.planLimits.projects) {
      return res.status(403).json({
        error: 'Project limit reached',
        limit: req.tenant.planLimits.projects,
        current: projectCount
      });
    }
    
    // Create project in database
    const project = await prisma.project.create({
      data: {
        tenantId: req.tenant.id,
        name: data.projectName,
        slug: data.projectName.toLowerCase().replace(/\s+/g, '-'),
        description: data.description,
        template: data.template,
        status: 'creating'
      }
    });
    
    // Trigger n8n workflow
    const n8nResponse = await fetch(`http://n8n:5678/webhook/create-project`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        projectId: project.id,
        ...data,
        tenantId: req.tenant.id,
        coolifyApiToken: process.env.COOLIFY_API_TOKEN
      })
    });
    
    // Log activity
    await prisma.activity.create({
      data: {
        tenantId: req.tenant.id,
        action: 'project.created',
        metadata: { projectId: project.id }
      }
    });
    
    res.json({
      success: true,
      project: {
        id: project.id,
        name: project.name,
        slug: project.slug,
        status: project.status,
        dashboardUrl: `https://${process.env.DOMAIN}/projects/${project.id}`
      }
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return res.status(400).json({ error: 'Validation failed', details: error.errors });
    }
    logger.error('Project creation error:', error);
    res.status(500).json({ error: 'Failed to create project' });
  }
});

// List projects
app.get('/api/projects', authenticate, apiLimiter, async (req, res) => {
  const projects = await prisma.project.findMany({
    where: { tenantId: req.tenant.id },
    orderBy: { createdAt: 'desc' }
  });
  
  res.json(projects);
});

// Get usage
app.get('/api/usage', authenticate, async (req, res) => {
  const [projectCount, deploymentCount, storageUsed] = await Promise.all([
    prisma.project.count({ where: { tenantId: req.tenant.id } }),
    prisma.deployment.count({ where: { tenantId: req.tenant.id } }),
    // Calculate storage from Coolify
    Promise.resolve('0GB')
  ]);
  
  res.json({
    projects: projectCount,
    deployments: deploymentCount,
    storage: storageUsed,
    limits: req.tenant.planLimits
  });
});

// Stripe webhook
app.post('/webhook/stripe', express.raw({ type: 'application/json' }), async (req, res) => {
  const sig = req.headers['stripe-signature']!;
  
  try {
    const event = stripe.webhooks.constructEvent(
      req.body,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
    
    switch (event.type) {
      case 'customer.subscription.created':
      case 'customer.subscription.updated':
        const subscription = event.data.object as Stripe.Subscription;
        await prisma.tenant.update({
          where: { stripeCustomerId: subscription.customer as string },
          data: {
            plan: subscription.items.data[0].price.lookup_key || 'starter',
            subscriptionStatus: subscription.status
          }
        });
        break;
    }
    
    res.json({ received: true });
  } catch (error) {
    logger.error('Stripe webhook error:', error);
    res.status(400).json({ error: 'Webhook error' });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  logger.info(`API Gateway running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  await prisma.$disconnect();
  await redis.quit();
  process.exit(0);
});
```

### 4.2 Deploy API in Coolify

1. Create GitHub repository for the API code
2. In Coolify: Add Resource → Application
3. Source: GitHub repository
4. Build Pack: Dockerfile
5. Port: 3001
6. Domain: `api.yourdomain.com`

## Step 5: Deploy Dashboard

**File: `services/dashboard/Dockerfile`**
```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["node", "server.js"]
```

## Step 6: Database Schema

**File: `services/api/prisma/schema.prisma`**
```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Tenant {
  id                String   @id @default(cuid())
  name              String
  email             String   @unique
  company           String?
  apiKey            String   @unique
  plan              String   @default("free")
  planLimits        Json     @default("{\"projects\": 1, \"users\": 3}")
  status            String   @default("active")
  stripeCustomerId  String?  @unique
  subscriptionStatus String?
  createdAt         DateTime @default(now())
  updatedAt         DateTime @updatedAt
  
  projects          Project[]
  activities        Activity[]
  deployments       Deployment[]
  
  @@index([apiKey])
  @@index([email])
}

model Project {
  id          String   @id @default(cuid())
  tenantId    String
  name        String
  slug        String   @unique
  description String?
  template    String   @default("nextjs-saas")
  status      String   @default("creating")
  repository  String?
  deployUrl   String?
  coolifyId   String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  tenant      Tenant   @relation(fields: [tenantId], references: [id])
  deployments Deployment[]
  
  @@index([tenantId])
  @@index([slug])
}

model Deployment {
  id         String   @id @default(cuid())
  projectId  String
  tenantId   String
  status     String   @default("pending")
  commitSha  String?
  buildLog   String?
  createdAt  DateTime @default(now())
  
  project    Project  @relation(fields: [projectId], references: [id])
  tenant     Tenant   @relation(fields: [tenantId], references: [id])
  
  @@index([projectId])
  @@index([tenantId])
}

model Activity {
  id        String   @id @default(cuid())
  tenantId  String
  action    String
  metadata  Json?
  createdAt DateTime @default(now())
  
  tenant    Tenant   @relation(fields: [tenantId], references: [id])
  
  @@index([tenantId])
  @@index([createdAt])
}
```

## Step 7: Coolify Integration Service

**File: `services/builder/coolify-service.ts`**
```typescript
import axios from 'axios';

export class CoolifyService {
  private apiUrl: string;
  private apiToken: string;

  constructor() {
    this.apiUrl = process.env.COOLIFY_INSTANCE_URL || 'http://localhost:3000';
    this.apiToken = process.env.COOLIFY_API_TOKEN!;
  }

  async createApplication(projectData: any) {
    const response = await axios.post(
      `${this.apiUrl}/api/v1/applications`,
      {
        name: projectData.slug,
        gitRepository: projectData.repositoryUrl,
        gitBranch: 'main',
        buildPack: 'nixpacks',
        port: 3000,
        projectId: process.env.COOLIFY_PROJECT_ID,
        environmentId: process.env.COOLIFY_ENVIRONMENT_ID,
        destinationId: process.env.COOLIFY_DESTINATION_ID,
        gitCommitSha: 'HEAD',
        dockerComposeConfiguration: this.generateDockerCompose(projectData),
        env: this.generateEnvVars(projectData)
      },
      {
        headers: {
          Authorization: `Bearer ${this.apiToken}`,
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data;
  }

  async createDatabase(projectData: any) {
    const response = await axios.post(
      `${this.apiUrl}/api/v1/databases`,
      {
        name: `${projectData.slug}-db`,
        type: 'postgresql',
        version: '16',
        projectId: process.env.COOLIFY_PROJECT_ID,
        environmentId: process.env.COOLIFY_ENVIRONMENT_ID,
        destinationId: process.env.COOLIFY_DESTINATION_ID
      },
      {
        headers: {
          Authorization: `Bearer ${this.apiToken}`
        }
      }
    );

    return response.data;
  }

  async deployApplication(applicationId: string) {
    const response = await axios.post(
      `${this.apiUrl}/api/v1/applications/${applicationId}/deploy`,
      {},
      {
        headers: {
          Authorization: `Bearer ${this.apiToken}`
        }
      }
    );

    return response.data;
  }

  private generateDockerCompose(projectData: any) {
    return `
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=\${DATABASE_URL}
    labels:
      - coolify.managed=true
      - coolify.applicationId=${projectData.slug}
      - traefik.enable=true
      - traefik.http.routers.${projectData.slug}.rule=Host(\`${projectData.slug}.${process.env.DOMAIN}\`)
    `;
  }

  private generateEnvVars(projectData: any) {
    return [
      { key: 'NODE_ENV', value: 'production' },
      { key: 'NEXT_PUBLIC_APP_NAME', value: projectData.name },
      { key: 'DATABASE_URL', value: `\${${projectData.slug}_DATABASE_URL}` },
      { key: 'NEXTAUTH_SECRET', value: this.generateSecret() },
      { key: 'NEXTAUTH_URL', value: `https://${projectData.slug}.${process.env.DOMAIN}` }
    ];
  }

  private generateSecret(): string {
    return require('crypto').randomBytes(32).toString('hex');
  }
}
```

## Step 8: Complete Installation Script

**File: `install-in-coolify.sh`**
```bash
#!/bin/bash

echo "🚀 SaaS Automation System - Coolify Installation"
echo "================================================"

# Configuration
read -p "Enter your Coolify URL (e.g., https://coolify.yourdomain.com): " COOLIFY_URL
read -p "Enter your Coolify API Token: " COOLIFY_TOKEN
read -p "Enter your domain for the SaaS platform: " DOMAIN
read -p "Enter GitHub organization: " GITHUB_ORG
read -p "Enter GitHub token: " GITHUB_TOKEN

# Create project structure
mkdir -p saas-automation/{services,workflows,scripts}
cd saas-automation

# Create environment file
cat > .env << EOF
COOLIFY_URL=$COOLIFY_URL
COOLIFY_API_TOKEN=$COOLIFY_TOKEN
DOMAIN=$DOMAIN
GITHUB_ORG=$GITHUB_ORG
GITHUB_TOKEN=$GITHUB_TOKEN
EOF

echo "✅ Configuration saved"

# Create Coolify resources via API
echo "📦 Creating Coolify resources..."

# Create project
curl -X POST "$COOLIFY_URL/api/v1/projects" \
  -H "Authorization: Bearer $COOLIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "saas-automation",
    "description": "SaaS Automation Platform"
  }'

echo "✅ Coolify project created"

# Instructions for manual steps
cat << EOF

====================================
NEXT STEPS - Manual Configuration
====================================

1. Login to Coolify: $COOLIFY_URL

2. Create these resources in the 'saas-automation' project:
   
   a) PostgreSQL Database:
      - Name: saas-db
      - Version: 16
   
   b) Redis:
      - Name: saas-redis
      - Version: 7
   
   c) n8n Service:
      - Use Docker Compose from: services/n8n/docker-compose.yml
      - Domain: n8n.$DOMAIN
   
   d) API Gateway:
      - GitHub Repo: $GITHUB_ORG/saas-api
      - Port: 3001
      - Domain: api.$DOMAIN
   
   e) Dashboard:
      - GitHub Repo: $GITHUB_ORG/saas-dashboard
      - Port: 3000
      - Domain: dashboard.$DOMAIN

3. Set environment variables for each service in Coolify UI

4. Deploy each service

5. Access your platform:
   - n8n: https://n8n.$DOMAIN
   - API: https://api.$DOMAIN
   - Dashboard: https://dashboard.$DOMAIN

====================================

EOF
```

## Step 9: GitHub Repository Structure

Create these repositories in your GitHub organization:

```
your-org/
├── saas-api/            # API Gateway
├── saas-dashboard/      # Admin Dashboard
├── saas-builder/        # Project Builder Service
├── saas-workflows/      # n8n Workflows
└── saas-templates/      # Project Templates
```

## Step 10: Deploy Everything

1. Push code to GitHub repositories
2. In Coolify, create applications pointing to these repos
3. Configure environment variables
4. Deploy each service
5. Services will auto-deploy on push to main branch

## Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Coolify Platform                      │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │     n8n      │  │   API Gateway │  │  Dashboard   │  │
│  │   (Port 5678)│  │  (Port 3001)  │  │  (Port 3000) │  │
│  └──────┬───────┘  └──────┬────────┘  └──────┬──────┘  │
│         │                  │                   │          │
│  ┌──────▼──────────────────▼───────────────────▼──────┐  │
│  │              PostgreSQL Database                   │  │
│  │                 (saas-db)                          │  │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                  Redis Cache                        │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │         Generated Client Applications                │ │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐           │ │
│  │  │ App1 │  │ App2 │  │ App3 │  │ App4 │  ...      │ │
│  └─────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

This setup:
- ✅ Uses Coolify for all deployments
- ✅ Manages everything through Coolify UI
- ✅ Auto-deploys on GitHub push
- ✅ Scales horizontally
- ✅ Uses Coolify's built-in SSL, monitoring, and logs
- ✅ Integrates with Coolify API for dynamic project creation

Ready to deploy this in your Coolify instance?