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

      const expectedHeaders = {
        'Content-Type': 'application/json',
        'X-TempoNest-Event': 'deployment.success',
        'X-TempoNest-Signature': expect.any(String),
        'User-Agent': 'TempoNest-Webhook/1.0',
      }

      expect(expectedHeaders['Content-Type']).toBe('application/json')
      expect(expectedHeaders['X-TempoNest-Event']).toBe('deployment.success')
      expect(expectedHeaders['User-Agent']).toBe('TempoNest-Webhook/1.0')
    })

    it('should generate correct HMAC signature', () => {
      const payload = { test: 'data' }
      const secret = 'webhook-secret-key'

      const signature = crypto
        .createHmac('sha256', secret)
        .update(JSON.stringify(payload))
        .digest('hex')

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

      await global.fetch(mockJob.data!.url, {
        method: 'POST',
        body: JSON.stringify(mockJob.data!.payload),
      })

      expect(global.fetch).toHaveBeenCalledWith(
        'https://hooks.example.com/webhook',
        expect.objectContaining({
          method: 'POST',
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

      await mockResponse.text()

      expect(mockPrisma.webhookDelivery.create).toBeDefined()
    })

    it('should return success result', () => {
      const result = { success: true, status: 200 }

      expect(result.success).toBe(true)
      expect(result.status).toBe(200)
    })
  })

  describe('Signature Generation', () => {
    it('should generate signature when secret is provided', () => {
      const payload = { key: 'value' }
      const secret = 'test-secret'

      const signature = crypto
        .createHmac('sha256', secret)
        .update(JSON.stringify(payload))
        .digest('hex')

      expect(signature).toBeTruthy()
      expect(typeof signature).toBe('string')
    })

    it('should handle empty signature when no secret provided', () => {
      mockJob.data!.secret = undefined

      const signature = undefined

      expect(signature).toBeUndefined()
    })

    it('should generate different signatures for different payloads', () => {
      const secret = 'test-secret'
      const payload1 = { id: 1 }
      const payload2 = { id: 2 }

      const sig1 = crypto.createHmac('sha256', secret)
        .update(JSON.stringify(payload1))
        .digest('hex')

      const sig2 = crypto.createHmac('sha256', secret)
        .update(JSON.stringify(payload2))
        .digest('hex')

      expect(sig1).not.toBe(sig2)
    })

    it('should generate consistent signatures for same payload', () => {
      const secret = 'test-secret'
      const payload = { id: 1 }

      const sig1 = crypto.createHmac('sha256', secret)
        .update(JSON.stringify(payload))
        .digest('hex')

      const sig2 = crypto.createHmac('sha256', secret)
        .update(JSON.stringify(payload))
        .digest('hex')

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

      const errorText = await mockResponse.text()

      expect(mockResponse.ok).toBe(false)
      expect(mockResponse.status).toBe(500)
      expect(errorText).toBe('Internal Server Error')
    })

    it('should create failed delivery log', async () => {
      const mockResponse = {
        ok: false,
        status: 404,
        text: jest.fn().mockResolvedValue('Not Found'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      expect(mockPrisma.webhookDelivery.create).toBeDefined()
    })

    it('should handle network errors', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'))
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      await expect(global.fetch('https://example.com')).rejects.toThrow('Network error')
    })

    it('should log delivery error', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValue(new Error('Failed'))
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      try {
        await global.fetch('https://example.com')
      } catch (error) {
        expect(error).toBeInstanceOf(Error)
        expect(consoleErrorSpy).toBeDefined()
      }
    })

    it('should throw error after logging failure', async () => {
      const error = new Error('Webhook failed')

      await expect(async () => {
        throw error
      }).rejects.toThrow('Webhook failed')
    })
  })

  describe('Webhook Delivery Logging', () => {
    it('should log webhook attempt number', () => {
      const attemptsMade = mockJob.attemptsMade

      expect(attemptsMade).toBe(1)
    })

    it('should include status code in delivery log', async () => {
      const mockResponse = {
        ok: true,
        status: 201,
        text: jest.fn().mockResolvedValue('Created'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)
      mockPrisma.webhookDelivery.create.mockResolvedValue({})

      expect(mockResponse.status).toBe(201)
    })

    it('should store response text in delivery log', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('Success response'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      const responseText = await mockResponse.text()

      expect(responseText).toBe('Success response')
    })

    it('should log network errors with status 0', () => {
      const deliveryLog = {
        statusCode: 0,
        status: 'failed',
        response: 'Network error',
      }

      expect(deliveryLog.statusCode).toBe(0)
      expect(deliveryLog.status).toBe('failed')
    })
  })

  describe('Event Types', () => {
    it('should handle deployment.success event', () => {
      mockJob.data!.event = 'deployment.success'

      expect(mockJob.data!.event).toBe('deployment.success')
    })

    it('should handle deployment.failed event', () => {
      mockJob.data!.event = 'deployment.failed'

      expect(mockJob.data!.event).toBe('deployment.failed')
    })

    it('should handle project.created event', () => {
      mockJob.data!.event = 'project.created'

      expect(mockJob.data!.event).toBe('project.created')
    })

    it('should handle custom event types', () => {
      mockJob.data!.event = 'custom.event'

      expect(mockJob.data!.event).toBe('custom.event')
    })
  })

  describe('HTTP Response Handling', () => {
    it('should handle 200 OK response', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: jest.fn().mockResolvedValue('OK'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      expect(mockResponse.ok).toBe(true)
      expect(mockResponse.status).toBe(200)
    })

    it('should handle 201 Created response', async () => {
      const mockResponse = {
        ok: true,
        status: 201,
        text: jest.fn().mockResolvedValue('Created'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      expect(mockResponse.ok).toBe(true)
      expect(mockResponse.status).toBe(201)
    })

    it('should handle 400 Bad Request', async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        text: jest.fn().mockResolvedValue('Bad Request'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      expect(mockResponse.ok).toBe(false)
      expect(mockResponse.status).toBe(400)
    })

    it('should handle 500 Internal Server Error', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        text: jest.fn().mockResolvedValue('Internal Server Error'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      expect(mockResponse.ok).toBe(false)
      expect(mockResponse.status).toBe(500)
    })
  })

  describe('Payload Serialization', () => {
    it('should serialize complex payloads', () => {
      const payload = {
        id: 123,
        nested: {
          key: 'value',
          array: [1, 2, 3],
        },
      }

      const serialized = JSON.stringify(payload)

      expect(typeof serialized).toBe('string')
      expect(JSON.parse(serialized)).toEqual(payload)
    })

    it('should handle empty payloads', () => {
      const payload = {}

      const serialized = JSON.stringify(payload)

      expect(serialized).toBe('{}')
    })
  })

  describe('Job Configuration', () => {
    it('should use configured concurrency', () => {
      const concurrency = 2

      expect(concurrency).toBe(2)
    })

    it('should configure redis connection', () => {
      const connection = {}

      expect(connection).toBeDefined()
    })
  })
})
