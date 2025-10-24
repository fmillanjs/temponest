import { Worker, Job } from 'bullmq'
import { prisma } from '@temponest/database'
import { redis, config } from '../config'
import type { CleanupJob } from '@temponest/types'

/**
 * Process cleanup job
 * EXPORTED FOR TESTING - Contains all business logic
 */
export async function processCleanup(job: Job<CleanupJob>): Promise<{ success: true; deletedCount: number }> {
  const { type, olderThanDays } = job.data

  console.log(`🧹 Running cleanup: ${type} (older than ${olderThanDays} days)`)

  const cutoffDate = new Date()
  cutoffDate.setDate(cutoffDate.getDate() - olderThanDays)

  try {
    let deletedCount = 0

    switch (type) {
      case 'deployments': {
        // Delete old failed deployments
        const result = await prisma.deployment.deleteMany({
          where: {
            status: 'failed',
            createdAt: {
              lt: cutoffDate,
            },
          },
        })
        deletedCount = result.count
        break
      }

      case 'logs': {
        // Delete old activity logs
        const result = await prisma.activity.deleteMany({
          where: {
            createdAt: {
              lt: cutoffDate,
            },
          },
        })
        deletedCount = result.count
        break
      }

      case 'expired-sessions': {
        // Delete expired sessions
        const result = await prisma.session.deleteMany({
          where: {
            expiresAt: {
              lt: new Date(),
            },
          },
        })
        deletedCount = result.count
        break
      }

      default:
        throw new Error(`Unknown cleanup type: ${type}`)
    }

    console.log(`✅ Cleanup completed: ${deletedCount} records deleted`)

    return { success: true, deletedCount }
  } catch (error) {
    console.error(`❌ Cleanup failed:`, error)
    throw error
  }
}

/**
 * Cleanup processor worker
 * Handles cleanup of old data (deployments, logs, sessions, etc.)
 */
export const cleanupWorker = new Worker<CleanupJob>(
  'cleanup',
  processCleanup,
  {
    connection: redis,
    concurrency: 1, // Run cleanup jobs sequentially
  }
)

cleanupWorker.on('completed', (job) => {
  console.log(`✅ Cleanup job completed: ${job.id}`)
})

cleanupWorker.on('failed', (job, err) => {
  console.error(`❌ Cleanup job ${job?.id} failed:`, err.message)
})
