import { PrismaClient, AgentName, AgentStatus } from '@prisma/client'

const prisma = new PrismaClient()

async function main() {
  console.log('🌱 Seeding database...')

  // Seed the 7 agents
  const agents = [
    {
      name: AgentName.Overseer,
      status: AgentStatus.healthy,
      version: '1.0.0',
      lastHeartbeat: new Date(),
      config: {
        description: 'Decomposes complex goals into executable tasks',
        provider: 'ollama',
        model: 'mistral:7b-instruct',
        capabilities: ['task-decomposition', 'goal-planning', 'risk-assessment']
      }
    },
    {
      name: AgentName.Developer,
      status: AgentStatus.healthy,
      version: '1.0.0',
      lastHeartbeat: new Date(),
      config: {
        description: 'Generates production code for APIs, schemas, and UI',
        provider: 'ollama',
        model: 'qwen2.5-coder:7b',
        capabilities: ['code-generation', 'api-design', 'database-schema', 'testing']
      }
    },
    {
      name: AgentName.Designer,
      status: AgentStatus.degraded,
      version: '0.8.0',
      lastHeartbeat: new Date(Date.now() - 1000 * 60 * 30), // 30 mins ago
      config: {
        description: 'Creates UI/UX designs and visual assets',
        provider: 'placeholder',
        model: 'tbd',
        capabilities: ['ui-design', 'branding', 'asset-generation']
      }
    },
    {
      name: AgentName.UX,
      status: AgentStatus.down,
      version: '0.5.0',
      lastHeartbeat: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
      config: {
        description: 'Analyzes user experience and suggests improvements',
        provider: 'placeholder',
        model: 'tbd',
        capabilities: ['ux-analysis', 'user-research', 'a-b-testing']
      }
    },
    {
      name: AgentName.QA,
      status: AgentStatus.down,
      version: '0.3.0',
      lastHeartbeat: null,
      config: {
        description: 'Performs automated testing and quality assurance',
        provider: 'placeholder',
        model: 'tbd',
        capabilities: ['test-generation', 'integration-testing', 'bug-detection']
      }
    },
    {
      name: AgentName.Security,
      status: AgentStatus.down,
      version: '0.2.0',
      lastHeartbeat: null,
      config: {
        description: 'Scans for vulnerabilities and security issues',
        provider: 'placeholder',
        model: 'tbd',
        capabilities: ['security-scanning', 'vulnerability-detection', 'compliance']
      }
    },
    {
      name: AgentName.DevOps,
      status: AgentStatus.down,
      version: '0.1.0',
      lastHeartbeat: null,
      config: {
        description: 'Manages deployments and infrastructure',
        provider: 'placeholder',
        model: 'tbd',
        capabilities: ['deployment', 'monitoring', 'infrastructure-management']
      }
    }
  ]

  for (const agent of agents) {
    await prisma.agent.upsert({
      where: { name: agent.name },
      update: agent,
      create: agent
    })
    console.log(`✓ Created/updated agent: ${agent.name}`)
  }

  // Create a sample user
  await prisma.user.upsert({
    where: { email: 'admin@example.com' },
    update: {},
    create: {
      email: 'admin@example.com',
      name: 'Admin User',
      role: 'owner'
    }
  })
  console.log('✓ Created admin user')

  // Create a sample project
  const project = await prisma.project.upsert({
    where: { slug: 'sample-saas' },
    update: {},
    create: {
      name: 'Sample SaaS',
      slug: 'sample-saas',
      type: 'single',
      status: 'research',
      repoUrl: 'https://github.com/example/sample-saas'
    }
  })
  console.log('✓ Created sample project')

  // Create a sample run for the project
  await prisma.run.create({
    data: {
      projectId: project.id,
      kind: 'wizard',
      step: 'market-research',
      status: 'running',
      startedAt: new Date(),
      logs: 'Starting market research analysis...\nAnalyzing competitors...\nGenerating product recommendations...'
    }
  })
  console.log('✓ Created sample run')

  console.log('🎉 Seeding completed!')
}

main()
  .catch((e) => {
    console.error('❌ Seeding failed:', e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })
