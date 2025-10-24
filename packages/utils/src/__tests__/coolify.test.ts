import { CoolifyService, createCoolifyService, isCoolifyConfigured } from '../coolify'

// Mock fetch
global.fetch = jest.fn()

describe('Coolify Service', () => {
  let coolify: CoolifyService
  const mockConfig = {
    apiUrl: 'https://coolify.example.com/api',
    apiKey: 'test-api-key',
    teamId: 'team-123',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    coolify = new CoolifyService(mockConfig)
  })

  describe('Constructor', () => {
    it('should create service with valid config', () => {
      expect(coolify).toBeInstanceOf(CoolifyService)
    })

    it('should throw error if API URL is missing', () => {
      expect(() => {
        new CoolifyService({ ...mockConfig, apiUrl: '' })
      }).toThrow('Coolify API URL is required')
    })

    it('should throw error if API key is missing', () => {
      expect(() => {
        new CoolifyService({ ...mockConfig, apiKey: '' })
      }).toThrow('Coolify API key is required')
    })

    it('should accept config without teamId', () => {
      const service = new CoolifyService({
        apiUrl: mockConfig.apiUrl,
        apiKey: mockConfig.apiKey,
      })

      expect(service).toBeInstanceOf(CoolifyService)
    })
  })

  describe('createApplication', () => {
    it('should create application with all options', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          data: {
            uuid: 'app-123',
            name: 'test-app',
            fqdn: 'test-app.example.com',
            repository: 'https://github.com/test/repo',
            branch: 'main',
            status: 'active',
          },
        }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      const result = await coolify.createApplication({
        projectId: 'proj-123',
        name: 'test-app',
        repository: 'https://github.com/test/repo',
        branch: 'main',
        buildCommand: 'npm build',
        startCommand: 'npm start',
        environmentVariables: { NODE_ENV: 'production' },
        domains: ['test-app.example.com'],
      })

      expect(result.uuid).toBe('app-123')
      expect(result.name).toBe('test-app')
      expect(global.fetch).toHaveBeenCalledWith(
        `${mockConfig.apiUrl}/applications`,
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${mockConfig.apiKey}`,
          }),
        })
      )
    })

    it('should handle application creation failure', async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        text: jest.fn().mockResolvedValue('Invalid request'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await expect(
        coolify.createApplication({
          projectId: 'proj-123',
          name: 'test-app',
          repository: 'https://github.com/test/repo',
          branch: 'main',
        })
      ).rejects.toThrow('Failed to create Coolify application')
    })

    it('should format environment variables correctly', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({ data: {} }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await coolify.createApplication({
        projectId: 'proj-123',
        name: 'test-app',
        repository: 'https://github.com/test/repo',
        branch: 'main',
        environmentVariables: {
          NODE_ENV: 'production',
          PORT: '3000',
        },
      })

      const callBody = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body)
      expect(callBody.environment_variables).toBe('NODE_ENV=production\nPORT=3000')
    })
  })

  describe('deployApplication', () => {
    it('should deploy application with options', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          data: {
            uuid: 'deploy-123',
            status: 'queued',
          },
        }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      const result = await coolify.deployApplication('app-123', {
        force: true,
        commitSha: 'abc123',
      })

      expect(result.uuid).toBe('deploy-123')
      expect(result.status).toBe('queued')
      expect(global.fetch).toHaveBeenCalledWith(
        `${mockConfig.apiUrl}/applications/app-123/deploy`,
        expect.objectContaining({
          method: 'POST',
        })
      )
    })

    it('should deploy without options', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          data: { uuid: 'deploy-456', status: 'in_progress' },
        }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      const result = await coolify.deployApplication('app-123')

      expect(result.uuid).toBe('deploy-456')
    })

    it('should handle deployment failure', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        text: jest.fn().mockResolvedValue('Server error'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await expect(coolify.deployApplication('app-123')).rejects.toThrow(
        'Failed to deploy Coolify application'
      )
    })
  })

  describe('getApplication', () => {
    it('should fetch application details', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          data: {
            uuid: 'app-123',
            name: 'test-app',
            fqdn: 'test-app.example.com',
            repository: 'https://github.com/test/repo',
            branch: 'main',
            status: 'active',
          },
        }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      const result = await coolify.getApplication('app-123')

      expect(result.uuid).toBe('app-123')
      expect(result.name).toBe('test-app')
      expect(result.fqdn).toBe('test-app.example.com')
      expect(global.fetch).toHaveBeenCalledWith(
        `${mockConfig.apiUrl}/applications/app-123`,
        expect.objectContaining({
          method: 'GET',
        })
      )
    })

    it('should handle application not found', async () => {
      const mockResponse = {
        ok: false,
        status: 404,
        text: jest.fn().mockResolvedValue('Not found'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await expect(coolify.getApplication('app-999')).rejects.toThrow(
        'Failed to get Coolify application'
      )
    })
  })

  describe('getDeployment', () => {
    it('should fetch deployment status', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          data: {
            uuid: 'deploy-123',
            status: 'finished',
            finishedAt: '2024-01-01T12:00:00Z',
          },
        }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      const result = await coolify.getDeployment('deploy-123')

      expect(result.uuid).toBe('deploy-123')
      expect(result.status).toBe('finished')
      expect(result.finishedAt).toBe('2024-01-01T12:00:00Z')
      expect(global.fetch).toHaveBeenCalledWith(
        `${mockConfig.apiUrl}/deployments/deploy-123`,
        expect.objectContaining({
          method: 'GET',
        })
      )
    })

    it('should handle deployment not found', async () => {
      const mockResponse = {
        ok: false,
        status: 404,
        text: jest.fn().mockResolvedValue('Deployment not found'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await expect(coolify.getDeployment('deploy-999')).rejects.toThrow(
        'Failed to get Coolify deployment'
      )
    })
  })

  describe('getDeploymentLogs', () => {
    it('should fetch deployment logs', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          data: {
            logs: ['Log line 1', 'Log line 2', 'Log line 3'],
          },
        }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      const result = await coolify.getDeploymentLogs('deploy-123')

      expect(result).toEqual(['Log line 1', 'Log line 2', 'Log line 3'])
      expect(global.fetch).toHaveBeenCalledWith(
        `${mockConfig.apiUrl}/deployments/deploy-123/logs`,
        expect.objectContaining({
          method: 'GET',
        })
      )
    })

    it('should return empty array if logs are missing', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          data: {},
        }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      const result = await coolify.getDeploymentLogs('deploy-123')

      expect(result).toEqual([])
    })

    it('should return empty array on error', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        text: jest.fn().mockResolvedValue('Server error'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      const result = await coolify.getDeploymentLogs('deploy-123')

      expect(result).toEqual([])
    })
  })

  describe('cancelDeployment', () => {
    it('should cancel deployment', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({ data: {} }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await coolify.cancelDeployment('deploy-123')

      expect(global.fetch).toHaveBeenCalledWith(
        `${mockConfig.apiUrl}/deployments/deploy-123/cancel`,
        expect.objectContaining({
          method: 'POST',
        })
      )
    })

    it('should handle cancel failure', async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        text: jest.fn().mockResolvedValue('Cannot cancel'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await expect(coolify.cancelDeployment('deploy-123')).rejects.toThrow(
        'Failed to cancel Coolify deployment'
      )
    })
  })

  describe('updateEnvironmentVariables', () => {
    it('should update environment variables', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({ data: {} }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await coolify.updateEnvironmentVariables('app-123', {
        NODE_ENV: 'production',
        API_URL: 'https://api.example.com',
      })

      expect(global.fetch).toHaveBeenCalledWith(
        `${mockConfig.apiUrl}/applications/app-123/environment`,
        expect.objectContaining({
          method: 'PUT',
        })
      )

      const callBody = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body)
      expect(callBody.environment_variables).toBe('NODE_ENV=production\nAPI_URL=https://api.example.com')
    })

    it('should handle update failure', async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        text: jest.fn().mockResolvedValue('Invalid variables'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await expect(
        coolify.updateEnvironmentVariables('app-123', {})
      ).rejects.toThrow('Failed to update environment variables')
    })
  })

  describe('deleteApplication', () => {
    it('should delete application', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({ data: {} }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await coolify.deleteApplication('app-123')

      expect(global.fetch).toHaveBeenCalledWith(
        `${mockConfig.apiUrl}/applications/app-123`,
        expect.objectContaining({
          method: 'DELETE',
        })
      )
    })

    it('should handle delete failure', async () => {
      const mockResponse = {
        ok: false,
        status: 404,
        text: jest.fn().mockResolvedValue('Not found'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await expect(coolify.deleteApplication('app-123')).rejects.toThrow(
        'Failed to delete Coolify application'
      )
    })
  })

  describe('Factory Functions', () => {
    const originalEnv = process.env

    beforeEach(() => {
      jest.resetModules()
      process.env = { ...originalEnv }
    })

    afterAll(() => {
      process.env = originalEnv
    })

    it('should create service from environment variables', () => {
      process.env.COOLIFY_API_URL = 'https://coolify.test'
      process.env.COOLIFY_API_KEY = 'test-key'

      const service = createCoolifyService()

      expect(service).toBeInstanceOf(CoolifyService)
    })

    it('should return null if not configured', () => {
      delete process.env.COOLIFY_API_URL
      delete process.env.COOLIFY_API_KEY

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation()
      const service = createCoolifyService()

      expect(service).toBeNull()
      expect(consoleWarnSpy).toHaveBeenCalled()
      consoleWarnSpy.mockRestore()
    })

    it('should use provided config over environment', () => {
      process.env.COOLIFY_API_URL = 'https://wrong.url'
      process.env.COOLIFY_API_KEY = 'wrong-key'

      const service = createCoolifyService({
        apiUrl: 'https://correct.url',
        apiKey: 'correct-key',
      })

      expect(service).toBeInstanceOf(CoolifyService)
    })

    it('should check if Coolify is configured', () => {
      process.env.COOLIFY_API_URL = 'https://coolify.test'
      process.env.COOLIFY_API_KEY = 'test-key'

      expect(isCoolifyConfigured()).toBe(true)
    })

    it('should return false if not configured', () => {
      delete process.env.COOLIFY_API_URL
      delete process.env.COOLIFY_API_KEY

      expect(isCoolifyConfigured()).toBe(false)
    })
  })

  describe('HTTP Request Handling', () => {
    it('should include authorization header', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({ data: {} }),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await coolify.getApplication('app-123')

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': `Bearer ${mockConfig.apiKey}`,
          }),
        })
      )
    })

    it('should handle network errors', async () => {
      ;(global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'))

      await expect(coolify.getApplication('app-123')).rejects.toThrow('Network error')
    })

    it('should parse error responses', async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        text: jest.fn().mockResolvedValue('Unauthorized'),
      }
      ;(global.fetch as jest.Mock).mockResolvedValue(mockResponse)

      await expect(coolify.getApplication('app-123')).rejects.toThrow(
        'Coolify API error (401): Unauthorized'
      )
    })
  })
})
