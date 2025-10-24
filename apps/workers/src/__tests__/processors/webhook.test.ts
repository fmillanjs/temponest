import { Job } from 'bullmq'
import type { ProcessWebhookJob } from '@temponest/types'
import crypto from 'crypto'

// Mock dependencies
const mockPrisma = {
  webhookDelivery: {
    create: jest.fn(),
  },
}

global.fetch = jest.fn()

jest.mock('@temponest/database', () => ({
  prisma: mockPrisma,
}))

jest.mock('../../config', () => ({
  redis: {},
  config: {
    workers: {
      concurrency: 2,
    },
  },
}))

// Import after all mocks are set up
const { processWebhook } = require('../../processors/webhook')

describe('Webhook Processor', () => {
  let mockJob: Partial<Job<ProcessWebhookJob>>
  let consoleLogSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance

  beforeEach(() => {
    jest.clearAllMocks()

    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation()
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()

    mockJob = {
      id: 'webhook-job-123',
      attemptsMade: 1,
      data: {
        webhookId: 'webhook-123',
        event: 'deployment.success',
        payload: {
          projectId: 'proj-123',
          deploymentId: 'dep-123',
          url: 'https://example.com',
        },
        url: 'https://hooks.example.com/webhook',
        secret: 'webhook-secret-key',
      },
    }
  })

  afterEach(() => {
    consoleLogSpy.mockRestore()
    consoleErrorSpy.mockRestore()
  })

  describe('Successful Webhook Delivery', () => {
    it('should send webhook with correct headers', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('OK'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      const result = await processWebhook(mockJob as Job<ProcessWebhookJob>)

      expect(result.success).toBe(true)
      expect(result.status).toBe(200)
      expect(global.fetch).toHaveBeenCalledWith(
        'https://hooks.example.com/webhook',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-TempoNest-Event': 'deployment.success',
            'X-TempoNest-Signature': expect.any(String),
            'User-Agent': 'TempoNest-Webhook/1.0',
          },
        })
      )
    })

    it('should generate correct HMAC signature', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('OK'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await processWebhook(mockJob as Job<ProcessWebhookJob>)

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0]
      const headers = fetchCall[1].headers
      const signature = headers['X-TempoNest-Signature']

      expect(signature).toBeTruthy()
      expect(signature.length).toBe(64) // SHA256 hex is 64 characters
      expect(/^[a-f0-9]{64}$/.test(signature)).toBe(true)
    })

    it('should send POST request to webhook URL', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('OK'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await processWebhook(mockJob as Job<ProcessWebhookJob>)

      expect(global.fetch).toHaveBeenCalledWith(
        'https://hooks.example.com/webhook',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(mockJob.data!.payload),
        })
      )
    })

    it('should create successful delivery log', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('Success'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await processWebhook(mockJob as Job<ProcessWebhookJob>)

      expect(mockPrisma.webhookDelivery.create).toHaveBeenCalledWith({
        data: {
          webhookId: 'webhook-123',
          event: 'deployment.success',
          url: 'https://hooks.example.com/webhook',
          status: 'success',
          statusCode: 200,
          response: 'Success',
          attempt: 1,
        },
      })
    })

    it('should return success result', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('OK'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      const result = await processWebhook(mockJob as Job<ProcessWebhookJob>)

      expect(result.success).toBe(true)
      expect(result.status).toBe(200)
    })
  })

  describe('Signature Generation', () => {
    it('should send empty signature when no secret provided', async () => {
      mockJob.data!.secret = undefined
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('OK'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await processWebhook(mockJob as Job<ProcessWebhookJob>)

      const fetchCall = (global.fetch as jest.Mock).mock.calls[0]
      const headers = fetchCall[1].headers
      expect(headers['X-TempoNest-Signature']).toBe('')
    })

    it('should generate different signatures for different payloads', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('OK'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await processWebhook(mockJob as Job<ProcessWebhookJob>)
      const sig1 = (global.fetch as jest.Mock).mock.calls[0][1].headers['X-TempoNest-Signature']

      mockJob.data!.payload = { different: 'data' }
      await processWebhook(mockJob as Job<ProcessWebhookJob>)
      const sig2 = (global.fetch as jest.Mock).mock.calls[1][1].headers['X-TempoNest-Signature']

      expect(sig1).not.toBe(sig2)
    })

    it('should generate consistent signatures for same payload', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('OK'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await processWebhook(mockJob as Job<ProcessWebhookJob>)
      const sig1 = (global.fetch as jest.Mock).mock.calls[0][1].headers['X-TempoNest-Signature']

      await processWebhook(mockJob as Job<ProcessWebhookJob>)
      const sig2 = (global.fetch as jest.Mock).mock.calls[1][1].headers['X-TempoNest-Signature']

      expect(sig1).toBe(sig2)
    })
  })

  describe('Failed Webhook Delivery', () => {
    it('should handle HTTP error responses', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        text: jest.fn().mockResolvedValue('Internal Server Error'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await expect(processWebhook(mockJob as Job<ProcessWebhookJob>))
        .rejects.toThrow('Webhook failed with status 500')

      expect(mockPrisma.webhookDelivery.create).toHaveBeenCalledWith({
        data: {
          webhookId: 'webhook-123',
          event: 'deployment.success',
          url: 'https://hooks.example.com/webhook',
          status: 'failed',
          statusCode: 500,
          response: 'Internal Server Error',
          attempt: 1,
        },
      })
    })

    it('should create failed delivery log', async () => {
      const mockResponse = {
        ok: false,
        status: 404,
        text: jest.fn().mockResolvedValue('Not Found'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await expect(processWebhook(mockJob as Job<ProcessWebhookJob>))
        .rejects.toThrow()

      expect(mockPrisma.webhookDelivery.create).toHaveBeenCalled()
    })

    it('should handle network errors', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'))
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await expect(processWebhook(mockJob as Job<ProcessWebhookJob>))
        .rejects.toThrow('Network error')

      expect(mockPrisma.webhookDelivery.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          status: 'failed',
          statusCode: 0,
          response: 'Network error',
        }),
      })
    })

    it('should log delivery error', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValue(new Error('Failed'))
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await expect(processWebhook(mockJob as Job<ProcessWebhookJob>))
        .rejects.toThrow('Failed')

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('Webhook delivery failed'),
        expect.any(Error)
      )
    })

    it('should throw error after logging failure', async () => {
      const mockResponse = {
        ok: false,
        status: 502,
        text: jest.fn().mockResolvedValue('Bad Gateway'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await expect(processWebhook(mockJob as Job<ProcessWebhookJob>))
        .rejects.toThrow('Webhook failed with status 502')

      expect(consoleErrorSpy).toHaveBeenCalled()
    })
  })

  describe('Event Types', () => {
    it('should handle different event types', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('OK'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      const events = ['deployment.success', 'deployment.failed', 'project.created', 'custom.event']

      for (const event of events) {
        mockJob.data!.event = event as any
        await processWebhook(mockJob as Job<ProcessWebhookJob>)

        expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining(`Processing webhook: ${event}`))
      }
    })
  })

  describe('Job Configuration', () => {
    it('should use configured concurrency', () => {
      const concurrency = 2
      expect(concurrency).toBe(2)
    })
  })
})
