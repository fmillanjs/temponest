/**
 * Database Seed Script
 *
 * Value Proposition: Fast Development Setup
 * - Creates sample data for development
 * - Consistent test data across team
 * - Demonstrates all features
 */

import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 Seeding database...')

  // Create subscription plans
  console.log('📦 Creating subscription plans...')
  const freePlan = await prisma.subscriptionPlan.upsert({
    where: { slug: 'free' },
    update: {},
    create: {
      name: 'Free',
      slug: 'free',
      description: 'Perfect for getting started with TempoNest',
      priceMonthly: 0,
      priceYearly: 0,
      limits: {
        projects: 1,
        templates: 3,
        members: 2,
        deployments: 10,
        storage: 500, // MB
        apiCalls: 1000,
      },
      features: [
        '1 Project',
        '3 Templates',
        '2 Team Members',
        '10 Deployments/month',
        'Community Support',
      ],
      isActive: true,
    },
  })

  const starterPlan = await prisma.subscriptionPlan.upsert({
    where: { slug: 'starter' },
    update: {},
    create: {
      name: 'Starter',
      slug: 'starter',
      description: 'For individuals and small teams',
      priceMonthly: 2900, // $29.00
      priceYearly: 29000, // $290.00 (2 months free)
      limits: {
        projects: 5,
        templates: 20,
        members: 5,
        deployments: 100,
        storage: 5000, // MB
        apiCalls: 10000,
      },
      features: [
        '5 Projects',
        '20 Templates',
        '5 Team Members',
        '100 Deployments/month',
        'Email Support',
        'Custom Domains',
        'Analytics Dashboard',
      ],
      isActive: true,
      isPopular: true,
    },
  })

  const proPlan = await prisma.subscriptionPlan.upsert({
    where: { slug: 'pro' },
    update: {},
    create: {
      name: 'Pro',
      slug: 'pro',
      description: 'For growing businesses and teams',
      priceMonthly: 9900, // $99.00
      priceYearly: 99000, // $990.00 (2 months free)
      limits: {
        projects: 25,
        templates: -1, // unlimited
        members: 20,
        deployments: 500,
        storage: 50000, // MB
        apiCalls: 100000,
      },
      features: [
        '25 Projects',
        'Unlimited Templates',
        '20 Team Members',
        '500 Deployments/month',
        'Priority Support',
        'Custom Domains',
        'Advanced Analytics',
        'Webhooks',
        'API Access',
      ],
      isActive: true,
    },
  })

  const enterprisePlan = await prisma.subscriptionPlan.upsert({
    where: { slug: 'enterprise' },
    update: {},
    create: {
      name: 'Enterprise',
      slug: 'enterprise',
      description: 'For large organizations with custom needs',
      priceMonthly: 29900, // $299.00
      priceYearly: 299000, // $2,990.00
      limits: {
        projects: -1, // unlimited
        templates: -1, // unlimited
        members: -1, // unlimited
        deployments: -1, // unlimited
        storage: -1, // unlimited
        apiCalls: -1, // unlimited
      },
      features: [
        'Unlimited Everything',
        'Dedicated Support',
        'Custom SLA',
        'Onboarding & Training',
        'Custom Integrations',
        'White-label Options',
        'Advanced Security',
        'Audit Logs',
      ],
      isActive: true,
    },
  })

  console.log('✅ Subscription plans created')

  // Create sample templates
  console.log('🎨 Creating sample templates...')
  const nextjsSaasTemplate = await prisma.template.upsert({
    where: { slug: 'nextjs-saas-starter' },
    update: {},
    create: {
      name: 'Next.js SaaS Starter',
      slug: 'nextjs-saas-starter',
      description:
        'Complete SaaS starter with authentication, billing, and multi-tenancy',
      category: 'saas',
      isPublic: true,
      isFeatured: true,
      repositoryUrl: 'https://github.com/temponest/template-nextjs-saas',
      repositoryRef: 'main',
      image: 'https://via.placeholder.com/400x300',
      tags: ['nextjs', 'saas', 'typescript', 'tailwind', 'prisma'],
      techStack: [
        { name: 'Next.js', version: '15', icon: 'nextjs' },
        { name: 'TypeScript', version: '5', icon: 'typescript' },
        { name: 'Tailwind CSS', version: '3', icon: 'tailwind' },
        { name: 'Prisma', version: '5', icon: 'prisma' },
        { name: 'Better Auth', version: '1', icon: 'shield' },
        { name: 'Stripe', version: 'latest', icon: 'stripe' },
      ],
      features: [
        'User authentication with Better Auth',
        'Multi-tenant architecture',
        'Stripe subscription billing',
        'Team & role management',
        'Dark mode support',
        'Responsive design',
        'Email templates with React Email',
        'Admin dashboard',
        'API with tRPC',
        'Database with Prisma',
      ],
      defaultConfig: {
        features: {
          auth: true,
          billing: true,
          teams: true,
          api: true,
          admin: true,
        },
      },
      requiredEnvVars: [
        'DATABASE_URL',
        'BETTER_AUTH_SECRET',
        'BETTER_AUTH_URL',
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY',
        'RESEND_API_KEY',
      ],
      usageCount: 0,
    },
  })

  const apiTemplate = await prisma.template.upsert({
    where: { slug: 'nodejs-api' },
    update: {},
    create: {
      name: 'Node.js API',
      slug: 'nodejs-api',
      description: 'RESTful API with Express, TypeScript, and PostgreSQL',
      category: 'api',
      isPublic: true,
      isFeatured: false,
      repositoryUrl: 'https://github.com/temponest/template-nodejs-api',
      repositoryRef: 'main',
      tags: ['nodejs', 'api', 'typescript', 'express', 'postgresql'],
      techStack: [
        { name: 'Node.js', version: '20', icon: 'nodejs' },
        { name: 'Express', version: '4', icon: 'express' },
        { name: 'TypeScript', version: '5', icon: 'typescript' },
        { name: 'Prisma', version: '5', icon: 'prisma' },
      ],
      features: [
        'RESTful API architecture',
        'JWT authentication',
        'Rate limiting',
        'Request validation with Zod',
        'Error handling middleware',
        'API documentation with Swagger',
        'Database migrations',
        'Unit & integration tests',
      ],
      defaultConfig: {},
      requiredEnvVars: ['DATABASE_URL', 'JWT_SECRET'],
      usageCount: 0,
    },
  })

  const landingTemplate = await prisma.template.upsert({
    where: { slug: 'nextjs-landing' },
    update: {},
    create: {
      name: 'Next.js Landing Page',
      slug: 'nextjs-landing',
      description: 'Modern landing page with Tailwind CSS and animations',
      category: 'landing',
      isPublic: true,
      isFeatured: true,
      repositoryUrl: 'https://github.com/temponest/template-nextjs-landing',
      repositoryRef: 'main',
      tags: ['nextjs', 'landing', 'tailwind', 'framer-motion'],
      techStack: [
        { name: 'Next.js', version: '15', icon: 'nextjs' },
        { name: 'Tailwind CSS', version: '3', icon: 'tailwind' },
        { name: 'Framer Motion', version: '11', icon: 'motion' },
      ],
      features: [
        'Responsive design',
        'Smooth animations',
        'SEO optimized',
        'Contact form',
        'Newsletter signup',
        'Dark mode',
        'Fast page loads',
      ],
      defaultConfig: {},
      requiredEnvVars: ['RESEND_API_KEY'],
      usageCount: 0,
    },
  })

  console.log('✅ Sample templates created')

  console.log('✨ Database seeded successfully!')
}

main()
  .then(async () => {
    await prisma.$disconnect()
  })
  .catch(async (e) => {
    console.error('❌ Error seeding database:', e)
    await prisma.$disconnect()
    process.exit(1)
  })
