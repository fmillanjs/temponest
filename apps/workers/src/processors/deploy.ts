import { Worker, Job } from 'bullmq'
import { prisma } from '@temponest/database'
import { redis, config } from '../config'
import { createCoolifyService, isCoolifyConfigured } from '@temponest/utils'
import type { DeployProjectJob } from '@temponest/types'

/**
 * Process deployment job
 * EXPORTED FOR TESTING - Contains all business logic
 */
export async function processDeployment(job: Job<DeployProjectJob>): Promise<{ success: true; url: string }> {
  const { projectId, deploymentId, organizationId, branch, commitSha } = job.data

  console.log(`🚀 Starting deployment: ${deploymentId} for project: ${projectId}`)

  try {
    // Update deployment status to in_progress
    await prisma.deployment.update({
      where: { id: deploymentId },
      data: { status: 'in_progress' },
    })

    // Get project details
    const project = await prisma.project.findUnique({
      where: { id: projectId },
      include: {
        template: true,
        organization: true,
      },
    })

    if (!project) {
      throw new Error('Project not found')
    }

    let deploymentUrl: string
    let coolifyDeploymentUuid: string | undefined

    // Check if Coolify is configured
    if (isCoolifyConfigured()) {
      console.log('  🚀 Using real Coolify deployment')
      const result = await deployWithCoolify(project, branch, commitSha, job)
      deploymentUrl = result.url
      coolifyDeploymentUuid = result.deploymentUuid
    } else {
      console.log('  🧪 Using simulated deployment (Coolify not configured)')
      deploymentUrl = await simulateDeployment(project, job)
    }

    // Update deployment status to success
    await prisma.deployment.update({
      where: { id: deploymentId },
      data: {
        status: 'success',
        deploymentUrl,
        finishedAt: new Date(),
        metadata: coolifyDeploymentUuid
          ? { coolifyDeploymentUuid }
          : undefined,
      },
    })

    // Update project status
    await prisma.project.update({
      where: { id: projectId },
      data: {
        status: 'active',
        deploymentUrl,
        metadata: project.metadata
          ? { ...project.metadata, lastDeploymentId: deploymentId }
          : { lastDeploymentId: deploymentId },
      },
    })

    // Create activity log
    await prisma.activity.create({
      data: {
        action: 'deployment.success',
        entityType: 'deployment',
        entityId: deploymentId,
        organizationId,
        metadata: {
          projectId,
          branch,
          commitSha,
          url: deploymentUrl,
        },
      },
    })

    console.log(`✅ Deployment successful: ${deploymentUrl}`)

    return { success: true, url: deploymentUrl }
  } catch (error) {
    console.error(`❌ Deployment failed:`, error)

    // Update deployment status to failed
    await prisma.deployment.update({
      where: { id: deploymentId },
      data: {
        status: 'failed',
        error: error instanceof Error ? error.message : 'Unknown error',
        finishedAt: new Date(),
      },
    })

    // Update project status
    await prisma.project.update({
      where: { id: projectId },
      data: { status: 'failed' },
    })

    // Create activity log
    await prisma.activity.create({
      data: {
        action: 'deployment.failed',
        entityType: 'deployment',
        entityId: deploymentId,
        organizationId,
        metadata: {
          projectId,
          error: error instanceof Error ? error.message : 'Unknown error',
        },
      },
    })

    throw error
  }
}

/**
 * Deployment processor worker
 * Handles project deployments to Coolify
 */
export const deploymentWorker = new Worker<DeployProjectJob>(
  'deployments',
  processDeployment,
  {
    connection: redis,
    concurrency: config.workers.concurrency,
  }
)

/**
 * Deploy with real Coolify integration
 */
async function deployWithCoolify(
  project: any,
  branch: string,
  commitSha: string | undefined,
  job: Job<DeployProjectJob>
): Promise<{ url: string; deploymentUuid: string }> {
  const coolify = createCoolifyService()

  if (!coolify) {
    throw new Error('Coolify service not available')
  }

  // Check if project already has a Coolify application
  const coolifyAppUuid = (project.metadata as any)?.coolifyApplicationUuid

  let applicationUuid: string

  if (coolifyAppUuid) {
    // Use existing application
    console.log(`  📦 Using existing Coolify application: ${coolifyAppUuid}`)
    applicationUuid = coolifyAppUuid

    // Update environment variables if they've changed
    if (project.environmentVariables) {
      await coolify.updateEnvironmentVariables(
        applicationUuid,
        project.environmentVariables as Record<string, string>
      )
    }
  } else {
    // Create new application
    console.log('  📦 Creating new Coolify application')

    const app = await coolify.createApplication({
      projectId: project.id,
      name: project.slug,
      repository: project.repositoryUrl || project.template?.repositoryUrl || '',
      branch: branch,
      buildCommand: project.template?.buildCommand,
      startCommand: project.template?.startCommand,
      environmentVariables: project.environmentVariables as Record<string, string>,
      domains: [`${project.slug}.temponest.app`],
    })

    applicationUuid = app.uuid

    // Store Coolify app UUID in project metadata
    await prisma.project.update({
      where: { id: project.id },
      data: {
        metadata: {
          ...((project.metadata as any) || {}),
          coolifyApplicationUuid: applicationUuid,
        },
      },
    })
  }

  // Trigger deployment
  await job.updateProgress(10)
  console.log('  🚀 Triggering Coolify deployment')

  const deployment = await coolify.deployApplication(applicationUuid, {
    force: true,
    commitSha,
  })

  // Poll deployment status
  let deploymentStatus = deployment.status
  let attempts = 0
  const maxAttempts = 60 // 10 minutes with 10-second intervals

  while (
    deploymentStatus === 'queued' ||
    (deploymentStatus === 'in_progress' && attempts < maxAttempts)
  ) {
    await new Promise((resolve) => setTimeout(resolve, 10000)) // Wait 10 seconds

    const currentDeployment = await coolify.getDeployment(deployment.uuid)
    deploymentStatus = currentDeployment.status

    const progress = 10 + (attempts / maxAttempts) * 80
    await job.updateProgress(progress)

    console.log(`  ⏳ Deployment status: ${deploymentStatus}`)

    attempts++
  }

  await job.updateProgress(100)

  if (deploymentStatus === 'failed') {
    throw new Error('Coolify deployment failed')
  }

  if (deploymentStatus === 'cancelled') {
    throw new Error('Coolify deployment was cancelled')
  }

  // Get final application details
  const app = await coolify.getApplication(applicationUuid)

  return {
    url: `https://${app.fqdn}`,
    deploymentUuid: deployment.uuid,
  }
}

/**
 * Simulate deployment for development
 */
async function simulateDeployment(project: any, job: Job<DeployProjectJob>): Promise<string> {
  const steps = [
    { name: 'Cloning repository', duration: 2000 },
    { name: 'Installing dependencies', duration: 3000 },
    { name: 'Building application', duration: 4000 },
    { name: 'Creating Docker image', duration: 3000 },
    { name: 'Deploying to server', duration: 2000 },
    { name: 'Running health checks', duration: 1000 },
  ]

  for (const [index, step] of steps.entries()) {
    await job.updateProgress((index / steps.length) * 100)
    console.log(`  ⏳ ${step.name}...`)
    await new Promise((resolve) => setTimeout(resolve, step.duration))
  }

  await job.updateProgress(100)

  return `https://${project.slug}.temponest.app`
}

deploymentWorker.on('completed', (job) => {
  console.log(`✅ Job ${job.id} completed`)
})

deploymentWorker.on('failed', (job, err) => {
  console.error(`❌ Job ${job?.id} failed:`, err.message)
})
