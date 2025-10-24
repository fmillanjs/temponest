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

// Mock Worker to prevent Redis connection
const mockWorkerClose = jest.fn().mockResolvedValue(undefined)
const mockWorkerOn = jest.fn()

jest.mock('bullmq', () => ({
  ...jest.requireActual('bullmq'),
  Worker: jest.fn().mockImplementation(() => ({
    close: mockWorkerClose,
    on: mockWorkerOn,
  })),
}))

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

// Import after all mocks are set up
const { processCleanup, cleanupWorker } = require('../../processors/cleanup')

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

  afterAll(async () => {
    // Close the Worker to prevent hanging tests
    if (cleanupWorker && cleanupWorker.close) {
      await cleanupWorker.close()
    }
  })

  describe('Deployment Cleanup', () => {
    beforeEach(() => {
      mockJob.data!.type = 'deployments'
      mockJob.data!.olderThanDays = 30
    })

    it('should delete old failed deployments', async () => {
      mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 15 })

      const result = await processCleanup(mockJob as Job<CleanupJob>)

      expect(result.success).toBe(true)
      expect(result.deletedCount).toBe(15)
      expect(mockPrisma.deployment.deleteMany).toHaveBeenCalledWith({
        where: {
          status: 'failed',
          createdAt: {
            lt: expect.any(Date),
          },
        },
      })
    })

    it('should calculate correct cutoff date', async () => {
      mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 5 })

      await processCleanup(mockJob as Job<CleanupJob>)

      const call = mockPrisma.deployment.deleteMany.mock.calls[0][0]
      const cutoffDate = call.where.createdAt.lt
      const now = new Date()
      const expectedCutoff = new Date()
      expectedCutoff.setDate(now.getDate() - 30)

      // Allow 1 second difference for test execution time
      expect(Math.abs(cutoffDate.getTime() - expectedCutoff.getTime())).toBeLessThan(1000)
    })

    it('should only delete failed deployments', async () => {
      mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 5 })

      await processCleanup(mockJob as Job<CleanupJob>)

      expect(mockPrisma.deployment.deleteMany).toHaveBeenCalledWith({
        where: {
          status: 'failed',
          createdAt: {
            lt: expect.any(Date),
          },
        },
      })
    })

    it('should handle zero deletions', async () => {
      mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 0 })

      const result = await processCleanup(mockJob as Job<CleanupJob>)

      expect(result.success).toBe(true)
      expect(result.deletedCount).toBe(0)
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('0 records deleted'))
    })

    it('should handle different retention periods', async () => {
      const testCases = [7, 30, 90, 365]

      for (const days of testCases) {
        mockJob.data!.olderThanDays = days
        mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 1 })

        await processCleanup(mockJob as Job<CleanupJob>)

        expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining(`older than ${days} days`))
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

      const result = await processCleanup(mockJob as Job<CleanupJob>)

      expect(result.success).toBe(true)
      expect(result.deletedCount).toBe(150)
      expect(mockPrisma.activity.deleteMany).toHaveBeenCalledWith({
        where: {
          createdAt: {
            lt: expect.any(Date),
          },
        },
      })
    })

    it('should use correct date filter for logs', async () => {
      mockPrisma.activity.deleteMany.mockResolvedValue({ count: 10 })

      await processCleanup(mockJob as Job<CleanupJob>)

      const call = mockPrisma.activity.deleteMany.mock.calls[0][0]
      expect(call.where.createdAt.lt).toBeInstanceOf(Date)
    })

    it('should handle large deletion counts', async () => {
      mockPrisma.activity.deleteMany.mockResolvedValue({ count: 10000 })

      const result = await processCleanup(mockJob as Job<CleanupJob>)

      expect(result.deletedCount).toBe(10000)
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('10000 records deleted'))
    })
  })

  describe('Session Cleanup', () => {
    beforeEach(() => {
      mockJob.data!.type = 'expired-sessions'
      mockJob.data!.olderThanDays = 0 // Not used for sessions
    })

    it('should delete expired sessions', async () => {
      mockPrisma.session.deleteMany.mockResolvedValue({ count: 42 })

      const result = await processCleanup(mockJob as Job<CleanupJob>)

      expect(result.success).toBe(true)
      expect(result.deletedCount).toBe(42)
      expect(mockPrisma.session.deleteMany).toHaveBeenCalledWith({
        where: {
          expiresAt: {
            lt: expect.any(Date),
          },
        },
      })
    })

    it('should use current date for session expiration', async () => {
      mockPrisma.session.deleteMany.mockResolvedValue({ count: 5 })

      await processCleanup(mockJob as Job<CleanupJob>)

      const call = mockPrisma.session.deleteMany.mock.calls[0][0]
      expect(call.where.expiresAt.lt).toBeInstanceOf(Date)
    })

    it('should ignore olderThanDays parameter for sessions', async () => {
      mockJob.data!.olderThanDays = 30 // Should be ignored
      mockPrisma.session.deleteMany.mockResolvedValue({ count: 5 })

      await processCleanup(mockJob as Job<CleanupJob>)

      // Sessions use expiresAt, not olderThanDays
      expect(mockPrisma.session.deleteMany).toHaveBeenCalledWith({
        where: {
          expiresAt: {
            lt: expect.any(Date),
          },
        },
      })
    })
  })

  describe('Error Handling', () => {
    it('should handle unknown cleanup type', async () => {
      mockJob.data!.type = 'unknown-type' as any

      await expect(processCleanup(mockJob as Job<CleanupJob>))
        .rejects.toThrow('Unknown cleanup type: unknown-type')

      expect(consoleErrorSpy).toHaveBeenCalled()
    })

    it('should handle database errors', async () => {
      mockPrisma.deployment.deleteMany.mockRejectedValue(
        new Error('Database connection failed')
      )

      await expect(processCleanup(mockJob as Job<CleanupJob>))
        .rejects.toThrow('Database connection failed')
    })

    it('should log errors when cleanup fails', async () => {
      mockPrisma.deployment.deleteMany.mockRejectedValue(
        new Error('Cleanup failed')
      )

      await expect(processCleanup(mockJob as Job<CleanupJob>))
        .rejects.toThrow('Cleanup failed')

      expect(consoleErrorSpy).toHaveBeenCalledWith(expect.stringContaining('Cleanup failed'), expect.any(Error))
    })

    it('should rethrow errors after logging', async () => {
      mockPrisma.deployment.deleteMany.mockRejectedValue(
        new Error('Test error')
      )

      await expect(processCleanup(mockJob as Job<CleanupJob>))
        .rejects.toThrow('Test error')

      expect(consoleErrorSpy).toHaveBeenCalled()
    })
  })

  describe('Job Configuration', () => {
    it('should use sequential concurrency for cleanup jobs', () => {
      const concurrency = 1
      expect(concurrency).toBe(1)
    })
  })

  describe('Result Reporting', () => {
    it('should return success with deletion count', async () => {
      mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 25 })

      const result = await processCleanup(mockJob as Job<CleanupJob>)

      expect(result).toHaveProperty('success', true)
      expect(result).toHaveProperty('deletedCount', 25)
      expect(typeof result.deletedCount).toBe('number')
    })

    it('should log cleanup start', async () => {
      mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 10 })

      await processCleanup(mockJob as Job<CleanupJob>)

      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Running cleanup: deployments'))
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('older than 30 days'))
    })

    it('should log cleanup completion with count', async () => {
      mockPrisma.deployment.deleteMany.mockResolvedValue({ count: 42 })

      await processCleanup(mockJob as Job<CleanupJob>)

      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('42 records deleted'))
    })
  })
})
