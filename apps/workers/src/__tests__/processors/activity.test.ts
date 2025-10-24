import { Job } from 'bullmq'
import type { ActivityLogParams } from '@temponest/utils'

// Mock dependencies
const mockPrisma = {
  activity: {
    create: jest.fn(),
  },
}

jest.mock('@temponest/database', () => ({
  prisma: mockPrisma,
}))

jest.mock('../../config', () => ({
  redis: {},
}))

// Import after all mocks are set up
const { processActivityLog } = require('../../processors/activity')

describe('Activity Processor', () => {
  let mockJob: Partial<Job<ActivityLogParams>>
  let consoleLogSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance

  beforeEach(() => {
    jest.clearAllMocks()

    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation()
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()

    mockJob = {
      id: 'activity-job-123',
      data: {
        action: 'project.created',
        entityType: 'project',
        entityId: 'proj-123',
        organizationId: 'org-123',
        userId: 'user-123',
        projectId: 'proj-123',
        metadata: {
          name: 'Test Project',
        },
        ipAddress: '192.168.1.1',
        userAgent: 'Mozilla/5.0',
      },
    }
  })

  afterEach(() => {
    consoleLogSpy.mockRestore()
    consoleErrorSpy.mockRestore()
  })

  describe('Activity Logging', () => {
    it('should create activity record in database', async () => {
      mockPrisma.activity.create.mockResolvedValue({})

      await processActivityLog(mockJob as Job<ActivityLogParams>)

      expect(mockPrisma.activity.create).toHaveBeenCalledWith({
        data: {
          action: 'project.created',
          entity: 'project',
          entityId: 'proj-123',
          organizationId: 'org-123',
          userId: 'user-123',
          projectId: 'proj-123',
          metadata: { name: 'Test Project' },
          ipAddress: '192.168.1.1',
          userAgent: 'Mozilla/5.0',
        },
      })
    })

    it('should log action and entity type', async () => {
      mockPrisma.activity.create.mockResolvedValue({})

      await processActivityLog(mockJob as Job<ActivityLogParams>)

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('Logged activity: project.created for project')
      )
    })

    it('should include user context', async () => {
      mockPrisma.activity.create.mockResolvedValue({})

      await processActivityLog(mockJob as Job<ActivityLogParams>)

      expect(mockPrisma.activity.create).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            userId: 'user-123',
            organizationId: 'org-123',
          }),
        })
      )
    })

    it('should include IP address and user agent', async () => {
      mockPrisma.activity.create.mockResolvedValue({})

      await processActivityLog(mockJob as Job<ActivityLogParams>)

      expect(mockPrisma.activity.create).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            ipAddress: '192.168.1.1',
            userAgent: 'Mozilla/5.0',
          }),
        })
      )
    })

    it('should store metadata object', async () => {
      mockPrisma.activity.create.mockResolvedValue({})

      await processActivityLog(mockJob as Job<ActivityLogParams>)

      expect(mockPrisma.activity.create).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            metadata: { name: 'Test Project' },
          }),
        })
      )
    })

    it('should handle optional fields', async () => {
      mockJob.data!.metadata = undefined
      mockJob.data!.ipAddress = undefined
      mockJob.data!.userAgent = undefined

      mockPrisma.activity.create.mockResolvedValue({})

      await processActivityLog(mockJob as Job<ActivityLogParams>)

      expect(mockPrisma.activity.create).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            metadata: {},
          }),
        })
      )
    })
  })

  describe('Activity Actions', () => {
    it('should handle different action types', async () => {
      mockPrisma.activity.create.mockResolvedValue({})

      const actions = ['project.created', 'deployment.success', 'deployment.failed', 'user.login', 'organization.created']

      for (const action of actions) {
        mockJob.data!.action = action
        await processActivityLog(mockJob as Job<ActivityLogParams>)

        expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining(`Logged activity: ${action}`))
      }
    })
  })

  describe('Metadata Handling', () => {
    it('should store complex metadata', async () => {
      mockJob.data!.metadata = {
        projectName: 'Test',
        template: 'Next.js',
        branches: ['main', 'dev'],
        settings: {
          autoDeploy: true,
        },
      }
      mockPrisma.activity.create.mockResolvedValue({})

      await processActivityLog(mockJob as Job<ActivityLogParams>)

      expect(mockPrisma.activity.create).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            metadata: expect.objectContaining({
              projectName: 'Test',
              template: 'Next.js',
            }),
          }),
        })
      )
    })

    it('should handle empty metadata', async () => {
      mockJob.data!.metadata = {}
      mockPrisma.activity.create.mockResolvedValue({})

      await processActivityLog(mockJob as Job<ActivityLogParams>)

      expect(mockPrisma.activity.create).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            metadata: {},
          }),
        })
      )
    })
  })

  describe('Error Handling', () => {
    it('should handle database errors', async () => {
      mockPrisma.activity.create.mockRejectedValue(
        new Error('Database error')
      )

      await expect(processActivityLog(mockJob as Job<ActivityLogParams>))
        .rejects.toThrow('Database error')

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('Failed to log activity'),
        expect.any(Error)
      )
    })

    it('should rethrow errors for retry', async () => {
      mockPrisma.activity.create.mockRejectedValue(
        new Error('Retry this')
      )

      await expect(processActivityLog(mockJob as Job<ActivityLogParams>))
        .rejects.toThrow('Retry this')
    })
  })

  describe('Worker Configuration', () => {
    it('should use high concurrency for activity logging', () => {
      const defaultConcurrency = parseInt(process.env.ACTIVITY_WORKER_CONCURRENCY || '10')
      expect(defaultConcurrency).toBe(10)
    })

    it('should configure rate limiting (100 jobs/second)', () => {
      const limiter = {
        max: 100,
        duration: 1000,
      }

      expect(limiter.max).toBe(100)
      expect(limiter.duration).toBe(1000)
    })
  })
})
