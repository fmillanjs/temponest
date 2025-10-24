import { Worker, Job } from 'bullmq'
import { prisma } from '@temponest/database'
import { redis, config } from '../config'
import type { ProcessWebhookJob } from '@temponest/types'
import crypto from 'crypto'

/**
 * Process webhook job
 * EXPORTED FOR TESTING - Contains all business logic
 */
export async function processWebhook(job: Job<ProcessWebhookJob>): Promise<{ success: true; status: number }> {
  const { webhookId, event, payload, url, secret } = job.data

  console.log(`🔔 Processing webhook: ${event} -> ${url}`)

  try {
    // Generate signature for webhook verification
    const signature = secret
      ? crypto.createHmac('sha256', secret).update(JSON.stringify(payload)).digest('hex')
      : undefined

    // Send webhook request
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-TempoNest-Event': event,
        'X-TempoNest-Signature': signature || '',
        'User-Agent': 'TempoNest-Webhook/1.0',
      },
      body: JSON.stringify(payload),
    })

    const responseText = await response.text()

    // Update webhook delivery log
    await prisma.webhookDelivery.create({
      data: {
        webhookId,
        event,
        url,
        status: response.ok ? 'success' : 'failed',
        statusCode: response.status,
        response: responseText,
        attempt: job.attemptsMade,
      },
    })

    if (!response.ok) {
      throw new Error(`Webhook failed with status ${response.status}: ${responseText}`)
    }

    console.log(`✅ Webhook delivered: ${event}`)

    return { success: true, status: response.status }
  } catch (error) {
    console.error(`❌ Webhook delivery failed:`, error)

    // Log failed attempt
    await prisma.webhookDelivery.create({
      data: {
        webhookId,
        event,
        url,
        status: 'failed',
        statusCode: 0,
        response: error instanceof Error ? error.message : 'Unknown error',
        attempt: job.attemptsMade,
      },
    })

    throw error
  }
}

/**
 * Webhook processor worker
 * Sends webhook events to registered endpoints
 */
export const webhookWorker = new Worker<ProcessWebhookJob>(
  'webhooks',
  processWebhook,
  {
    connection: redis,
    concurrency: config.workers.concurrency,
  }
)

webhookWorker.on('completed', (job) => {
  console.log(`✅ Webhook delivered: ${job.id}`)
})

webhookWorker.on('failed', (job, err) => {
  console.error(`❌ Webhook job ${job?.id} failed:`, err.message)
})
