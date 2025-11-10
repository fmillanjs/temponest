import { describe, it, expect, vi, beforeEach } from 'vitest'
import { GET, POST } from '@/app/api/agents/health/route'
import { NextRequest } from 'next/server'
import { prisma } from '@/lib/db/client'

// Mock Prisma
vi.mock('@/lib/db/client', () => ({
  prisma: {
    agent: {
      findMany: vi.fn(),
      upsert: vi.fn(),
    },
  },
}))

describe('API Route: /api/agents/health', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('GET /api/agents/health', () => {
    it('should return list of agents ordered by name', async () => {
      const mockDate1 = new Date('2025-11-07T10:00:00Z')
      const mockDate2 = new Date('2025-11-07T11:00:00Z')
      const mockAgents = [
        {
          id: '1',
          name: 'agent-1',
          version: '1.0.0',
          status: 'healthy',
          lastHeartbeat: mockDate1,
          config: {},
        },
        {
          id: '2',
          name: 'agent-2',
          version: '1.0.1',
          status: 'unhealthy',
          lastHeartbeat: mockDate2,
          config: {},
        },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents as any)

      const request = new NextRequest('http://localhost:3000/api/agents/health')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()
      // Dates are serialized to strings in JSON
      expect(data).toMatchObject({
        agents: [
          { id: '1', name: 'agent-1', version: '1.0.0', status: 'healthy', config: {} },
          { id: '2', name: 'agent-2', version: '1.0.1', status: 'unhealthy', config: {} },
        ]
      })
      expect(typeof data.agents[0].lastHeartbeat).toBe('string')
      expect(typeof data.agents[1].lastHeartbeat).toBe('string')

      expect(prisma.agent.findMany).toHaveBeenCalledWith({
        orderBy: { name: 'asc' },
      })
    })

    it('should return empty array when no agents exist', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const request = new NextRequest('http://localhost:3000/api/agents/health')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()
      expect(data).toEqual({ agents: [] })
    })

    it('should return 500 when database query fails', async () => {
      vi.mocked(prisma.agent.findMany).mockRejectedValue(new Error('Database connection failed'))

      const request = new NextRequest('http://localhost:3000/api/agents/health')
      const response = await GET(request)

      expect(response.status).toBe(500)
      const data = await response.json()
      expect(data).toEqual({ error: 'Database connection failed' })
    })

    it('should return 500 with generic error for unknown errors', async () => {
      vi.mocked(prisma.agent.findMany).mockRejectedValue('Unknown error')

      const request = new NextRequest('http://localhost:3000/api/agents/health')
      const response = await GET(request)

      expect(response.status).toBe(500)
      const data = await response.json()
      expect(data).toEqual({ error: 'Unknown error' })
    })
  })

  describe('POST /api/agents/health', () => {
    it('should create new agent with heartbeat', async () => {
      const mockDate = new Date('2025-11-07T12:00:00Z')
      const mockAgent = {
        id: 'new-agent-id',
        name: 'test-agent',
        version: '2.0.0',
        status: 'healthy',
        lastHeartbeat: mockDate,
        config: { key: 'value' },
      }

      vi.mocked(prisma.agent.upsert).mockResolvedValue(mockAgent as any)

      const request = new NextRequest('http://localhost:3000/api/agents/health', {
        method: 'POST',
        body: JSON.stringify({
          name: 'test-agent',
          version: '2.0.0',
          config: { key: 'value' },
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      const data = await response.json()
      // Dates are serialized to strings in JSON
      expect(data).toMatchObject({
        agent: {
          id: 'new-agent-id',
          name: 'test-agent',
          version: '2.0.0',
          status: 'healthy',
          config: { key: 'value' },
        }
      })
      expect(typeof data.agent.lastHeartbeat).toBe('string')

      expect(prisma.agent.upsert).toHaveBeenCalledWith({
        where: { name: 'test-agent' },
        update: {
          lastHeartbeat: expect.any(Date),
          version: '2.0.0',
          config: { key: 'value' },
          status: 'healthy',
        },
        create: {
          name: 'test-agent',
          version: '2.0.0',
          config: { key: 'value' },
          status: 'healthy',
        },
      })
    })

    it('should update existing agent heartbeat', async () => {
      const mockDate = new Date('2025-11-07T13:00:00Z')
      const mockAgent = {
        id: 'existing-agent-id',
        name: 'existing-agent',
        version: '2.1.0',
        status: 'healthy',
        lastHeartbeat: mockDate,
        config: {},
      }

      vi.mocked(prisma.agent.upsert).mockResolvedValue(mockAgent as any)

      const request = new NextRequest('http://localhost:3000/api/agents/health', {
        method: 'POST',
        body: JSON.stringify({
          name: 'existing-agent',
          version: '2.1.0',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      const data = await response.json()
      // Dates are serialized to strings in JSON
      expect(data).toMatchObject({
        agent: {
          id: 'existing-agent-id',
          name: 'existing-agent',
          version: '2.1.0',
          status: 'healthy',
          config: {},
        }
      })
      expect(typeof data.agent.lastHeartbeat).toBe('string')
    })

    it('should default config to empty object if not provided', async () => {
      const mockAgent = {
        id: 'agent-id',
        name: 'agent-no-config',
        version: '1.0.0',
        status: 'healthy',
        lastHeartbeat: new Date(),
        config: {},
      }

      vi.mocked(prisma.agent.upsert).mockResolvedValue(mockAgent as any)

      const request = new NextRequest('http://localhost:3000/api/agents/health', {
        method: 'POST',
        body: JSON.stringify({
          name: 'agent-no-config',
          version: '1.0.0',
        }),
      })

      await POST(request)

      expect(prisma.agent.upsert).toHaveBeenCalledWith({
        where: { name: 'agent-no-config' },
        update: expect.objectContaining({
          config: {},
        }),
        create: expect.objectContaining({
          config: {},
        }),
      })
    })

    it('should return 400 when name is missing', async () => {
      const request = new NextRequest('http://localhost:3000/api/agents/health', {
        method: 'POST',
        body: JSON.stringify({
          version: '1.0.0',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toEqual({ error: 'Name and version are required' })
    })

    it('should return 400 when version is missing', async () => {
      const request = new NextRequest('http://localhost:3000/api/agents/health', {
        method: 'POST',
        body: JSON.stringify({
          name: 'test-agent',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toEqual({ error: 'Name and version are required' })
    })

    it('should return 400 when both name and version are missing', async () => {
      const request = new NextRequest('http://localhost:3000/api/agents/health', {
        method: 'POST',
        body: JSON.stringify({}),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toEqual({ error: 'Name and version are required' })
    })

    it('should return 500 when database operation fails', async () => {
      vi.mocked(prisma.agent.upsert).mockRejectedValue(new Error('Database write error'))

      const request = new NextRequest('http://localhost:3000/api/agents/health', {
        method: 'POST',
        body: JSON.stringify({
          name: 'test-agent',
          version: '1.0.0',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(500)
      const data = await response.json()
      expect(data).toEqual({ error: 'Database write error' })
    })

    it('should return 500 for malformed JSON', async () => {
      const request = new NextRequest('http://localhost:3000/api/agents/health', {
        method: 'POST',
        body: 'invalid json',
      })

      const response = await POST(request)

      expect(response.status).toBe(500)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })
  })
})
