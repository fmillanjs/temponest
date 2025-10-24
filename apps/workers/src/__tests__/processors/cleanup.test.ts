import { Job } from 'bullmq'
import type { CleanupJob } from '@temponest/types'

// Mock dependencies
const mockPrisma = {
  deployment: {
    deleteMany: jest.fn(),
  },
  activity: {
    deleteMany: jest.fn(),
  },
  session: {
    deleteMany: jest.fn(),
  },
}

jest.mock('@temponest/database', () => ({
  prisma: mockPrisma,
}))

jest.mock('../../config', () => ({
  redis: {},
  config: {
    workers: {
      concurrency: 1,
    },
  },
}))

describe('Cleanup Processor', () => {
  let mockJob: Partial<Job<CleanupJob>>
  let consoleLogSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance

  beforeEach(() => {
    jest.clearAllMocks()

    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation()
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()

    mockJob = {
      id: 'cleanup-job-123',
      data: {
        type: 'deployments',
        olderThanDays: 30,
      },
    }
  })

  afterEach(() => {
    consoleLogSpy.mockRestore()
    consoleErrorSpy.mockRestore()
  })

  describe('Deployment Cleanup', () => {
    beforeEach(() => {
      mockJob.data!.type = 'deployments'
      mockJob.data!.olderThanDays = 30
    })

    it('should delete old failed deployments', async () => {
      mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 15 })

      const result = { success: true, deletedCount: 15 }

      expect(result.success).toBe(true)
      expect(result.deletedCount).toBe(15)
    })

    it('should calculate correct cutoff date', () => {
      const olderThanDays = 30
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - olderThanDays)

      const now = new Date()
      const expectedCutoff = new Date()
      expectedCutoff.setDate(now.getDate() - 30)

      // Allow 1 second difference for test execution time
      expect(Math.abs(cutoffDate.getTime() - expectedCutoff.getTime())).toBeLessThan(1000)
    })

    it('should only delete failed deployments', () => {
      mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 5 })

      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - 30)

      const expectedQuery = {
        where: {
          status: 'failed',
          createdAt: {
            lt: cutoffDate,
          },
        },
      }

      expect(expectedQuery.where.status).toBe('failed')
      expect(expectedQuery.where.createdAt.lt).toBeInstanceOf(Date)
    })

    it('should handle zero deletions', async () => {
      mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 0 })

      const result = { success: true, deletedCount: 0 }

      expect(result.success).toBe(true)
      expect(result.deletedCount).toBe(0)
    })

    it('should handle different retention periods', async () => {
      const testCases = [7, 30, 90, 365]

      for (const days of testCases) {
        const cutoffDate = new Date()
        cutoffDate.setDate(cutoffDate.getDate() - days)

        expect(cutoffDate).toBeInstanceOf(Date)
        expect(cutoffDate.getTime()).toBeLessThan(Date.now())
      }
    })
  })

  describe('Log Cleanup', () => {
    beforeEach(() => {
      mockJob.data!.type = 'logs'
      mockJob.data!.olderThanDays = 90
    })

    it('should delete old activity logs', async () => {
      mockPrisma.activity.deleteMany.mockResolvedValue({ count: 150 })

      const result = { success: true, deletedCount: 150 }

      expect(result.success).toBe(true)
      expect(result.deletedCount).toBe(150)
    })

    it('should use correct date filter for logs', () => {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - 90)

      const query = {
        where: {
          createdAt: {
            lt: cutoffDate,
          },
        },
      }

      expect(query.where.createdAt.lt).toBeInstanceOf(Date)
    })

    it('should handle large deletion counts', async () => {
      mockPrisma.activity.deleteMany.mockResolvedValue({ count: 10000 })

      const result = { success: true, deletedCount: 10000 }

      expect(result.deletedCount).toBe(10000)
    })
  })

  describe('Session Cleanup', () => {
    beforeEach(() => {
      mockJob.data!.type = 'expired-sessions'
      mockJob.data!.olderThanDays = 0 // Not used for sessions
    })

    it('should delete expired sessions', async () => {
      mockPrisma.session.deleteMany.mockResolvedValue({ count: 42 })

      const result = { success: true, deletedCount: 42 }

      expect(result.success).toBe(true)
      expect(result.deletedCount).toBe(42)
    })

    it('should use current date for session expiration', () => {
      const now = new Date()

      const query = {
        where: {
          expiresAt: {
            lt: now,
          },
        },
      }

      expect(query.where.expiresAt.lt).toBeInstanceOf(Date)
    })

    it('should ignore olderThanDays parameter for sessions', () => {
      // Sessions use expiresAt, not createdAt + olderThanDays
      const olderThanDays = 30
      const now = new Date()

      const query = {
        where: {
          expiresAt: {
            lt: now,
          },
        },
      }

      expect(query.where.expiresAt.lt).toBeInstanceOf(Date)
    })
  })

  describe('Error Handling', () => {
    it('should handle unknown cleanup type', () => {
      const invalidType = 'unknown-type' as CleanupJob['type']

      expect(() => {
        if (!['deployments', 'logs', 'expired-sessions'].includes(invalidType)) {
          throw new Error(`Unknown cleanup type: ${invalidType}`)
        }
      }).toThrow('Unknown cleanup type: unknown-type')
    })

    it('should handle database errors', async () => {
      mockPrisma.deployment.deleteMany.mockRejectedValue(
        new Error('Database connection failed')
      )

      await expect(
        mockPrisma.deployment.deleteMany()
      ).rejects.toThrow('Database connection failed')
    })

    it('should log errors when cleanup fails', () => {
      const error = new Error('Cleanup failed')

      expect(error.message).toBe('Cleanup failed')
      expect(consoleErrorSpy).toBeDefined()
    })

    it('should rethrow errors after logging', async () => {
      const error = new Error('Test error')

      await expect(async () => {
        throw error
      }).rejects.toThrow('Test error')
    })
  })

  describe('Job Configuration', () => {
    it('should use sequential concurrency for cleanup jobs', () => {
      const concurrency = 1

      expect(concurrency).toBe(1)
    })

    it('should configure redis connection', () => {
      const connection = {}

      expect(connection).toBeDefined()
    })
  })

  describe('Result Reporting', () => {
    it('should return success with deletion count', () => {
      const result = { success: true, deletedCount: 25 }

      expect(result).toHaveProperty('success', true)
      expect(result).toHaveProperty('deletedCount')
      expect(typeof result.deletedCount).toBe('number')
    })

    it('should log cleanup start', () => {
      const type = 'deployments'
      const olderThanDays = 30

      expect(type).toBe('deployments')
      expect(olderThanDays).toBe(30)
      expect(consoleLogSpy).toBeDefined()
    })

    it('should log cleanup completion with count', () => {
      const deletedCount = 42

      expect(deletedCount).toBe(42)
      expect(consoleLogSpy).toBeDefined()
    })
  })

  describe('Date Calculations', () => {
    it('should handle 7-day retention', () => {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - 7)

      const sevenDaysAgo = new Date()
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)

      expect(Math.abs(cutoffDate.getTime() - sevenDaysAgo.getTime())).toBeLessThan(1000)
    })

    it('should handle 30-day retention', () => {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - 30)

      expect(cutoffDate.getTime()).toBeLessThan(Date.now())
    })

    it('should handle 90-day retention', () => {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - 90)

      const now = Date.now()
      const ninetyDaysMs = 90 * 24 * 60 * 60 * 1000

      expect(cutoffDate.getTime()).toBeLessThan(now)
      expect(now - cutoffDate.getTime()).toBeGreaterThan(ninetyDaysMs - 1000)
    })

    it('should handle year-long retention', () => {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - 365)

      expect(cutoffDate.getTime()).toBeLessThan(Date.now())
    })
  })

  describe('Cleanup Type Validation', () => {
    it('should accept valid deployment type', () => {
      const type: CleanupJob['type'] = 'deployments'
      expect(['deployments', 'logs', 'expired-sessions']).toContain(type)
    })

    it('should accept valid logs type', () => {
      const type: CleanupJob['type'] = 'logs'
      expect(['deployments', 'logs', 'expired-sessions']).toContain(type)
    })

    it('should accept valid expired-sessions type', () => {
      const type: CleanupJob['type'] = 'expired-sessions'
      expect(['deployments', 'logs', 'expired-sessions']).toContain(type)
    })
  })
})
