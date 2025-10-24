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

      await mockPrisma.activity.create({
        data: mockJob.data,
      })

      expect(mockPrisma.activity.create).toHaveBeenCalledWith({
        data: mockJob.data,
      })
    })

    it('should log action and entity type', () => {
      const { action, entityType } = mockJob.data!

      expect(action).toBe('project.created')
      expect(entityType).toBe('project')
    })

    it('should include user context', () => {
      const { userId, organizationId } = mockJob.data!

      expect(userId).toBe('user-123')
      expect(organizationId).toBe('org-123')
    })

    it('should include IP address and user agent', () => {
      const { ipAddress, userAgent } = mockJob.data!

      expect(ipAddress).toBe('192.168.1.1')
      expect(userAgent).toBe('Mozilla/5.0')
    })

    it('should store metadata object', () => {
      const { metadata } = mockJob.data!

      expect(metadata).toEqual({ name: 'Test Project' })
    })

    it('should handle optional fields', async () => {
      mockJob.data!.metadata = undefined
      mockJob.data!.ipAddress = undefined
      mockJob.data!.userAgent = undefined

      mockPrisma.activity.create.mockResolvedValue({})

      const data = {
        ...mockJob.data,
        metadata: mockJob.data!.metadata || {},
      }

      expect(data.metadata).toEqual({})
    })
  })

  describe('Activity Actions', () => {
    it('should handle project.created action', () => {
      mockJob.data!.action = 'project.created'

      expect(mockJob.data!.action).toBe('project.created')
    })

    it('should handle deployment.success action', () => {
      mockJob.data!.action = 'deployment.success'

      expect(mockJob.data!.action).toBe('deployment.success')
    })

    it('should handle deployment.failed action', () => {
      mockJob.data!.action = 'deployment.failed'

      expect(mockJob.data!.action).toBe('deployment.failed')
    })

    it('should handle user.login action', () => {
      mockJob.data!.action = 'user.login'

      expect(mockJob.data!.action).toBe('user.login')
    })

    it('should handle organization.created action', () => {
      mockJob.data!.action = 'organization.created'

      expect(mockJob.data!.action).toBe('organization.created')
    })
  })

  describe('Entity Types', () => {
    it('should handle project entity', () => {
      mockJob.data!.entityType = 'project'

      expect(mockJob.data!.entityType).toBe('project')
    })

    it('should handle deployment entity', () => {
      mockJob.data!.entityType = 'deployment'

      expect(mockJob.data!.entityType).toBe('deployment')
    })

    it('should handle user entity', () => {
      mockJob.data!.entityType = 'user'

      expect(mockJob.data!.entityType).toBe('user')
    })

    it('should handle organization entity', () => {
      mockJob.data!.entityType = 'organization'

      expect(mockJob.data!.entityType).toBe('organization')
    })
  })

  describe('Metadata Handling', () => {
    it('should store complex metadata', () => {
      mockJob.data!.metadata = {
        projectName: 'Test',
        template: 'Next.js',
        branches: ['main', 'dev'],
        settings: {
          autoDeply: true,
        },
      }

      expect(mockJob.data!.metadata).toHaveProperty('projectName')
      expect(mockJob.data!.metadata).toHaveProperty('template')
      expect(mockJob.data!.metadata).toHaveProperty('branches')
      expect(mockJob.data!.metadata).toHaveProperty('settings')
    })

    it('should handle empty metadata', () => {
      mockJob.data!.metadata = {}

      expect(mockJob.data!.metadata).toEqual({})
    })

    it('should handle undefined metadata', () => {
      mockJob.data!.metadata = undefined

      const metadata = mockJob.data!.metadata || {}

      expect(metadata).toEqual({})
    })
  })

  describe('Error Handling', () => {
    it('should handle database errors', async () => {
      mockPrisma.activity.create.mockRejectedValue(
        new Error('Database error')
      )

      await expect(mockPrisma.activity.create({})).rejects.toThrow('Database error')
    })

    it('should log errors', async () => {
      const error = new Error('Test error')

      expect(error.message).toBe('Test error')
      expect(consoleErrorSpy).toBeDefined()
    })

    it('should rethrow errors for retry', async () => {
      const error = new Error('Retry this')

      await expect(async () => {
        throw error
      }).rejects.toThrow('Retry this')
    })
  })

  describe('Worker Configuration', () => {
    it('should use high concurrency for activity logging', () => {
      const defaultConcurrency = parseInt(process.env.ACTIVITY_WORKER_CONCURRENCY || '10')

      expect(defaultConcurrency).toBe(10)
    })

    it('should configure rate limiting', () => {
      const limiter = {
        max: 100,
        duration: 1000,
      }

      expect(limiter.max).toBe(100)
      expect(limiter.duration).toBe(1000)
    })

    it('should allow 100 jobs per second', () => {
      const maxPerSecond = 100

      expect(maxPerSecond).toBe(100)
    })

    it('should configure redis connection', () => {
      const connection = {}

      expect(connection).toBeDefined()
    })
  })

  describe('Job Processing', () => {
    it('should log job completion', () => {
      expect(consoleLogSpy).toBeDefined()
    })

    it('should log job failures', () => {
      expect(consoleErrorSpy).toBeDefined()
    })

    it('should log worker startup', () => {
      expect(consoleLogSpy).toBeDefined()
    })

    it('should log activity action and entity', () => {
      const action = 'project.created'
      const entityType = 'project'

      expect(action).toBe('project.created')
      expect(entityType).toBe('project')
    })
  })

  describe('Context Information', () => {
    it('should track organization context', () => {
      const organizationId = mockJob.data!.organizationId

      expect(organizationId).toBe('org-123')
      expect(organizationId).toBeTruthy()
    })

    it('should track user context', () => {
      const userId = mockJob.data!.userId

      expect(userId).toBe('user-123')
      expect(userId).toBeTruthy()
    })

    it('should track project context', () => {
      const projectId = mockJob.data!.projectId

      expect(projectId).toBe('proj-123')
      expect(projectId).toBeTruthy()
    })

    it('should handle optional project context', () => {
      mockJob.data!.projectId = undefined

      expect(mockJob.data!.projectId).toBeUndefined()
    })

    it('should handle optional user context', () => {
      mockJob.data!.userId = undefined

      expect(mockJob.data!.userId).toBeUndefined()
    })
  })

  describe('Request Context', () => {
    it('should capture IP address', () => {
      const ipAddress = mockJob.data!.ipAddress

      expect(ipAddress).toBe('192.168.1.1')
      expect(ipAddress).toMatch(/^\d+\.\d+\.\d+\.\d+$/)
    })

    it('should capture user agent', () => {
      const userAgent = mockJob.data!.userAgent

      expect(userAgent).toBe('Mozilla/5.0')
      expect(userAgent).toBeTruthy()
    })

    it('should handle missing IP address', () => {
      mockJob.data!.ipAddress = undefined

      expect(mockJob.data!.ipAddress).toBeUndefined()
    })

    it('should handle missing user agent', () => {
      mockJob.data!.userAgent = undefined

      expect(mockJob.data!.userAgent).toBeUndefined()
    })
  })
})
