/**
 * Activity Log Processor
 * Processes queued activity logs and writes them to the database
 * PERFORMANCE OPTIMIZATION: Batch processing for efficiency
 */

import { Worker, Job } from 'bullmq'
import { prisma } from '@temponest/database'
import type { ActivityLogParams } from '@temponest/utils'
import { redis } from '../config'

const WORKER_CONCURRENCY = parseInt(process.env.ACTIVITY_WORKER_CONCURRENCY || '10')

/**
 * Process activity log job
 * EXPORTED FOR TESTING - Contains all business logic
 */
export async function processActivityLog(job: Job<ActivityLogParams>): Promise<void> {
  const params = job.data

  try {
    await prisma.activity.create({
      data: {
        action: params.action,
        entity: params.entityType,
        entityId: params.entityId,
        organizationId: params.organizationId,
        userId: params.userId,
        projectId: params.projectId,
        metadata: params.metadata || {},
        ipAddress: params.ipAddress,
        userAgent: params.userAgent,
      },
    })

    console.log(`[Activity Worker] Logged activity: ${params.action} for ${params.entityType}`)
  } catch (error) {
    console.error('[Activity Worker] Failed to log activity:', error)
    throw error // Will trigger retry
  }
}

/**
 * Activity processor worker
 * Processes queued activity logs and writes them to the database
 */
export const activityWorker = new Worker<ActivityLogParams>(
  'activities',
  processActivityLog,
  {
    connection: redis,
    concurrency: WORKER_CONCURRENCY,
    limiter: {
      max: 100, // Process max 100 jobs
      duration: 1000, // per second
    },
  }
)

// Event handlers
activityWorker.on('completed', (job) => {
  console.log(`[Activity Worker] Job ${job.id} completed`)
})

activityWorker.on('failed', (job, err) => {
  console.error(`[Activity Worker] Job ${job?.id} failed:`, err.message)
})

activityWorker.on('error', (err) => {
  console.error('[Activity Worker] Error:', err)
})

console.log('[Activity Worker] Started with concurrency:', WORKER_CONCURRENCY)
