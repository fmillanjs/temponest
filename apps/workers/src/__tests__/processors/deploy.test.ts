import { Job } from 'bullmq'
import type { DeployProjectJob } from '@temponest/types'

// Mock dependencies using jest.mock factory functions
jest.mock('@temponest/database', () => ({
  prisma: {
    deployment: {
      update: jest.fn(),
    },
    project: {
      findUnique: jest.fn(),
      update: jest.fn(),
    },
    activity: {
      create: jest.fn(),
    },
  },
}))

jest.mock('@temponest/utils', () => ({
  createCoolifyService: jest.fn(() => ({
    createApplication: jest.fn(),
    deployApplication: jest.fn(),
    getDeployment: jest.fn(),
    getApplication: jest.fn(),
    updateEnvironmentVariables: jest.fn(),
  })),
  isCoolifyConfigured: jest.fn(),
}))

jest.mock('../../config', () => ({
  redis: {},
  config: {
    workers: {
      concurrency: 1,
    },
  },
}))

// Now we can import the module after mocks are set up
import { prisma } from '@temponest/database'
import { createCoolifyService, isCoolifyConfigured } from '@temponest/utils'
import { processDeployment } from '../../processors/deploy'

// Get references to the mock functions
const mockPrisma = prisma as jest.Mocked<typeof prisma>
const mockCreateCoolifyService = createCoolifyService as jest.MockedFunction<typeof createCoolifyService>
const mockCoolifyService = mockCreateCoolifyService() as any

describe('Deploy Processor', () => {
  let mockJob: Partial<Job<DeployProjectJob>>
  let consoleLogSpy: jest.SpyInstance
  let consoleErrorSpy: jest.SpyInstance

  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()

    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation()
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation()

    // Reset coolify service mock
    mockCreateCoolifyService.mockReturnValue({
      createApplication: mockCoolifyService.createApplication,
      deployApplication: mockCoolifyService.deployApplication,
      getDeployment: mockCoolifyService.getDeployment,
      getApplication: mockCoolifyService.getApplication,
      updateEnvironmentVariables: mockCoolifyService.updateEnvironmentVariables,
    } as any)

    // Create mock job
    mockJob = {
      id: 'job-123',
      data: {
        projectId: 'proj-123',
        deploymentId: 'dep-123',
        organizationId: 'org-123',
        branch: 'main',
        commitSha: 'abc123',
      },
      updateProgress: jest.fn(),
    }
  })

  afterEach(() => {
    consoleLogSpy.mockRestore()
    consoleErrorSpy.mockRestore()
    jest.useRealTimers()
  })

  describe('Simulated Deployment', () => {
    beforeEach(() => {
      ;(isCoolifyConfigured as jest.Mock).mockReturnValue(false)
    })

    it('should successfully deploy with simulation', async () => {
      const mockProject = {
        id: 'proj-123',
        slug: 'test-project',
        organizationId: 'org-123',
        template: {
          buildCommand: 'npm build',
          startCommand: 'npm start',
        },
        organization: {
          id: 'org-123',
          name: 'Test Org',
        },
        metadata: {},
      }

      mockPrisma.project.findUnique.mockResolvedValue(mockProject)
      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)

      // Fast-forward through all simulation timeouts
      await jest.runAllTimersAsync()

      const result = await deploymentPromise

      expect(result.success).toBe(true)
      expect(result.url).toBe('https://test-project.temponest.app')
      expect(mockPrisma.project.findUnique).toHaveBeenCalledWith({
        where: { id: 'proj-123' },
        include: {
          template: true,
          organization: true,
        },
      })
      expect(mockPrisma.deployment.update).toHaveBeenCalledTimes(2)
      expect(mockPrisma.activity.create).toHaveBeenCalledWith({
        data: {
          action: 'deployment.success',
          entityType: 'deployment',
          entityId: 'dep-123',
          organizationId: 'org-123',
          metadata: {
            projectId: 'proj-123',
            branch: 'main',
            commitSha: 'abc123',
            url: 'https://test-project.temponest.app',
          },
        },
      })
    })

    it('should update deployment status to in_progress', async () => {
      const mockProject = {
        id: 'proj-123',
        slug: 'test-project',
        template: { buildCommand: 'npm build' },
        organization: { id: 'org-123' },
        metadata: {},
      }

      mockPrisma.project.findUnique.mockResolvedValue(mockProject)
      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)
      await jest.runAllTimersAsync()
      await deploymentPromise

      expect(mockPrisma.deployment.update).toHaveBeenCalledWith({
        where: { id: 'dep-123' },
        data: { status: 'in_progress' },
      })
    })

    it('should create activity log on successful deployment', async () => {
      const mockProject = {
        id: 'proj-123',
        slug: 'test-project',
        template: {},
        organization: { id: 'org-123' },
        metadata: {},
      }

      mockPrisma.project.findUnique.mockResolvedValue(mockProject)
      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)
      await jest.runAllTimersAsync()
      await deploymentPromise

      expect(mockPrisma.activity.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          action: 'deployment.success',
          entityType: 'deployment',
          entityId: 'dep-123',
          organizationId: 'org-123',
        }),
      })
    })
  })

  describe('Coolify Deployment', () => {
    beforeEach(() => {
      ;(isCoolifyConfigured as jest.Mock).mockReturnValue(true)
    })

    it('should create new Coolify application if not exists', async () => {
      const mockProject = {
        id: 'proj-123',
        slug: 'test-project',
        repositoryUrl: 'https://github.com/test/repo',
        environmentVariables: { NODE_ENV: 'production' },
        template: {
          buildCommand: 'npm build',
          startCommand: 'npm start',
        },
        organization: { id: 'org-123' },
        metadata: {},
      }

      mockPrisma.project.findUnique.mockResolvedValue(mockProject)
      mockCoolifyService.createApplication.mockResolvedValue({
        uuid: 'coolify-app-123',
      })
      mockCoolifyService.deployApplication.mockResolvedValue({
        uuid: 'deploy-uuid-123',
        status: 'success',
      })
      mockCoolifyService.getDeployment.mockResolvedValue({
        status: 'success',
      })
      mockCoolifyService.getApplication.mockResolvedValue({
        fqdn: 'test-project.temponest.app',
      })

      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)
      await jest.runAllTimersAsync()
      const result = await deploymentPromise

      expect(result.success).toBe(true)
      expect(mockCoolifyService.createApplication).toHaveBeenCalledWith({
        projectId: 'proj-123',
        name: 'test-project',
        repository: 'https://github.com/test/repo',
        branch: 'main',
        buildCommand: 'npm build',
        startCommand: 'npm start',
        environmentVariables: { NODE_ENV: 'production' },
        domains: ['test-project.temponest.app'],
      })
    })

    it('should use existing Coolify application if available', async () => {
      const mockProject = {
        id: 'proj-123',
        slug: 'test-project',
        environmentVariables: { NODE_ENV: 'production' },
        metadata: { coolifyApplicationUuid: 'existing-app-123' },
        template: {},
        organization: { id: 'org-123' },
      }

      mockPrisma.project.findUnique.mockResolvedValue(mockProject)
      mockCoolifyService.updateEnvironmentVariables.mockResolvedValue({})
      mockCoolifyService.deployApplication.mockResolvedValue({
        uuid: 'deploy-uuid-456',
        status: 'success',
      })
      mockCoolifyService.getDeployment.mockResolvedValue({
        status: 'success',
      })
      mockCoolifyService.getApplication.mockResolvedValue({
        fqdn: 'test-project.temponest.app',
      })

      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)
      await jest.runAllTimersAsync()
      await deploymentPromise

      expect(mockCoolifyService.createApplication).not.toHaveBeenCalled()
      expect(mockCoolifyService.updateEnvironmentVariables).toHaveBeenCalledWith(
        'existing-app-123',
        { NODE_ENV: 'production' }
      )
    })
  })

  describe('Error Handling', () => {
    beforeEach(() => {
      ;(isCoolifyConfigured as jest.Mock).mockReturnValue(false)
    })

    it('should handle project not found error', async () => {
      mockPrisma.project.findUnique.mockResolvedValue(null)
      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      await expect(
        processDeployment(mockJob as Job<DeployProjectJob>)
      ).rejects.toThrow('Project not found')

      expect(mockPrisma.deployment.update).toHaveBeenCalledWith({
        where: { id: 'dep-123' },
        data: {
          status: 'failed',
          error: 'Project not found',
          finishedAt: expect.any(Date),
        },
      })
    })

    it('should update deployment status to failed on error', async () => {
      mockPrisma.project.findUnique.mockRejectedValue(
        new Error('Database error')
      )
      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      await expect(
        processDeployment(mockJob as Job<DeployProjectJob>)
      ).rejects.toThrow('Database error')

      expect(mockPrisma.deployment.update).toHaveBeenCalledWith({
        where: { id: 'dep-123' },
        data: expect.objectContaining({
          status: 'failed',
          error: 'Database error',
        }),
      })
    })

    it('should create failed activity log on deployment error', async () => {
      mockPrisma.project.findUnique.mockResolvedValue(null)
      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      try {
        const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)
      await jest.runAllTimersAsync()
      await deploymentPromise
      } catch (error) {
        // Expected to throw
      }

      expect(mockPrisma.activity.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          action: 'deployment.failed',
          entityType: 'deployment',
          entityId: 'dep-123',
          organizationId: 'org-123',
        }),
      })
    })
  })

  describe('Deployment Progress', () => {
    beforeEach(() => {
      ;(isCoolifyConfigured as jest.Mock).mockReturnValue(true)
    })

    it('should update job progress during Coolify deployment', async () => {
      const mockProject = {
        id: 'proj-123',
        slug: 'test-project',
        metadata: { coolifyApplicationUuid: 'app-123' },
        template: {},
        organization: { id: 'org-123' },
      }

      mockPrisma.project.findUnique.mockResolvedValue(mockProject)
      mockCoolifyService.deployApplication.mockResolvedValue({
        uuid: 'deploy-123',
        status: 'in_progress',
      })
      mockCoolifyService.getDeployment.mockResolvedValue({
        status: 'success',
      })
      mockCoolifyService.getApplication.mockResolvedValue({
        fqdn: 'test.app',
      })

      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)
      await jest.runAllTimersAsync()
      await deploymentPromise

      expect(mockJob.updateProgress).toHaveBeenCalledWith(10)
      expect(mockJob.updateProgress).toHaveBeenCalledWith(100)
    })
  })

  describe('Deployment URL Generation', () => {
    it('should generate correct deployment URL for simulated deployment', async () => {
      ;(isCoolifyConfigured as jest.Mock).mockReturnValue(false)

      const mockProject = {
        id: 'proj-123',
        slug: 'my-project',
        template: {},
        organization: { id: 'org-123' },
        metadata: {},
      }

      mockPrisma.project.findUnique.mockResolvedValue(mockProject)
      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)
      await jest.runAllTimersAsync()
      const result = await deploymentPromise

      expect(result.url).toBe('https://my-project.temponest.app')
      expect(result.url).toMatch(/^https:\/\/[\w-]+\.temponest\.app$/)
    })

    it('should use Coolify FQDN for real deployments', async () => {
      ;(isCoolifyConfigured as jest.Mock).mockReturnValue(true)

      const mockProject = {
        id: 'proj-123',
        slug: 'test-project',
        metadata: { coolifyApplicationUuid: 'app-123' },
        template: {},
        organization: { id: 'org-123' },
      }

      mockPrisma.project.findUnique.mockResolvedValue(mockProject)
      mockCoolifyService.deployApplication.mockResolvedValue({
        uuid: 'deploy-123',
        status: 'success',
      })
      mockCoolifyService.getDeployment.mockResolvedValue({
        status: 'success',
      })
      mockCoolifyService.getApplication.mockResolvedValue({
        fqdn: 'custom-domain.example.com',
      })

      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)
      await jest.runAllTimersAsync()
      const result = await deploymentPromise

      expect(result.url).toBe('https://custom-domain.example.com')
    })
  })

  describe('Metadata Updates', () => {
    it('should store Coolify deployment UUID in metadata', async () => {
      ;(isCoolifyConfigured as jest.Mock).mockReturnValue(true)

      const mockProject = {
        id: 'proj-123',
        slug: 'test',
        metadata: { coolifyApplicationUuid: 'app-123' },
        template: {},
        organization: { id: 'org-123' },
      }

      mockPrisma.project.findUnique.mockResolvedValue(mockProject)
      mockCoolifyService.deployApplication.mockResolvedValue({
        uuid: 'deploy-uuid-789',
        status: 'success',
      })
      mockCoolifyService.getDeployment.mockResolvedValue({
        status: 'success',
      })
      mockCoolifyService.getApplication.mockResolvedValue({
        fqdn: 'test.app',
      })

      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)
      await jest.runAllTimersAsync()
      await deploymentPromise

      expect(mockPrisma.deployment.update).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { id: 'dep-123' },
          data: expect.objectContaining({
            metadata: { coolifyDeploymentUuid: 'deploy-uuid-789' },
          }),
        })
      )
    })

    it('should update project metadata with last deployment ID', async () => {
      ;(isCoolifyConfigured as jest.Mock).mockReturnValue(false)

      const mockProject = {
        id: 'proj-123',
        slug: 'test',
        metadata: { existingKey: 'value' },
        template: {},
        organization: { id: 'org-123' },
      }

      mockPrisma.project.findUnique.mockResolvedValue(mockProject)
      mockPrisma.deployment.update.mockResolvedValue({})
      mockPrisma.project.update.mockResolvedValue({})
      mockPrisma.activity.create.mockResolvedValue({})

      const deploymentPromise = processDeployment(mockJob as Job<DeployProjectJob>)
      await jest.runAllTimersAsync()
      await deploymentPromise

      expect(mockPrisma.project.update).toHaveBeenCalledWith({
        where: { id: 'proj-123' },
        data: expect.objectContaining({
          status: 'active',
          metadata: {
            existingKey: 'value',
            lastDeploymentId: 'dep-123',
          },
        }),
      })
    })
  })
})
