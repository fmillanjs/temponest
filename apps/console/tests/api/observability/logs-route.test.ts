import { describe, it, expect, vi, beforeEach } from 'vitest'
import { GET } from '@/app/api/observability/logs/route'
import { NextRequest } from 'next/server'
import { prisma } from '@/lib/db/client'

// Mock Prisma
vi.mock('@/lib/db/client', () => ({
  prisma: {
    auditLog: {
      findMany: vi.fn(),
    },
  },
}))

describe('API Route: /api/observability/logs', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('GET /api/observability/logs', () => {
    it('should return logs with default limit of 50', async () => {
      const mockLogs = [
        {
          id: 'log-1',
          action: 'Developer.completed',
          resource: 'project-123',
          details: { task: 'build' },
          userId: 'user-1',
          createdAt: new Date('2025-01-01T10:00:00Z'),
        },
        {
          id: 'log-2',
          action: 'QA.started',
          resource: 'project-456',
          details: { task: 'test' },
          userId: 'user-2',
          createdAt: new Date('2025-01-01T09:00:00Z'),
        },
      ]

      vi.mocked(prisma.auditLog.findMany).mockResolvedValue(mockLogs as any)

      const request = new NextRequest('http://localhost:3000/api/observability/logs')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.logs).toHaveLength(2)
      expect(data.total).toBe(2)

      expect(prisma.auditLog.findMany).toHaveBeenCalledWith({
        where: {},
        orderBy: { createdAt: 'desc' },
        take: 50,
      })
    })

    it('should respect custom limit parameter', async () => {
      vi.mocked(prisma.auditLog.findMany).mockResolvedValue([])

      const request = new NextRequest('http://localhost:3000/api/observability/logs?limit=100')
      const response = await GET(request)

      expect(response.status).toBe(200)

      expect(prisma.auditLog.findMany).toHaveBeenCalledWith({
        where: {},
        orderBy: { createdAt: 'desc' },
        take: 100,
      })
    })

    it('should filter by agent parameter', async () => {
      vi.mocked(prisma.auditLog.findMany).mockResolvedValue([])

      const request = new NextRequest('http://localhost:3000/api/observability/logs?agent=Developer')
      const response = await GET(request)

      expect(response.status).toBe(200)

      expect(prisma.auditLog.findMany).toHaveBeenCalledWith({
        where: {
          action: { contains: 'Developer', mode: 'insensitive' },
        },
        orderBy: { createdAt: 'desc' },
        take: 50,
      })
    })

    it('should filter by project parameter', async () => {
      vi.mocked(prisma.auditLog.findMany).mockResolvedValue([])

      const request = new NextRequest('http://localhost:3000/api/observability/logs?project=project-123')
      const response = await GET(request)

      expect(response.status).toBe(200)

      expect(prisma.auditLog.findMany).toHaveBeenCalledWith({
        where: {
          resource: { contains: 'project-123', mode: 'insensitive' },
        },
        orderBy: { createdAt: 'desc' },
        take: 50,
      })
    })

    it('should filter by search parameter (searches action and resource)', async () => {
      vi.mocked(prisma.auditLog.findMany).mockResolvedValue([])

      const request = new NextRequest('http://localhost:3000/api/observability/logs?search=build')
      const response = await GET(request)

      expect(response.status).toBe(200)

      expect(prisma.auditLog.findMany).toHaveBeenCalledWith({
        where: {
          OR: [
            { action: { contains: 'build', mode: 'insensitive' } },
            { resource: { contains: 'build', mode: 'insensitive' } },
          ],
        },
        orderBy: { createdAt: 'desc' },
        take: 50,
      })
    })

    it('should transform logs to unified format with correct level detection', async () => {
      const mockLogs = [
        {
          id: 'log-1',
          action: 'Developer.error.compilation',
          resource: 'file.ts',
          details: {},
          userId: 'user-1',
          createdAt: new Date('2025-01-01T10:00:00Z'),
        },
        {
          id: 'log-2',
          action: 'QA.warn.slowtest',
          resource: 'test-suite',
          details: {},
          userId: 'user-2',
          createdAt: new Date('2025-01-01T09:00:00Z'),
        },
        {
          id: 'log-3',
          action: 'DevOps.success.deployed',
          resource: 'production',
          details: {},
          userId: 'user-3',
          createdAt: new Date('2025-01-01T08:00:00Z'),
        },
        {
          id: 'log-4',
          action: 'System.info',
          resource: 'config',
          details: {},
          userId: null,
          createdAt: new Date('2025-01-01T07:00:00Z'),
        },
      ]

      vi.mocked(prisma.auditLog.findMany).mockResolvedValue(mockLogs as any)

      const request = new NextRequest('http://localhost:3000/api/observability/logs')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.logs[0]).toMatchObject({
        id: 'log-1',
        level: 'error',
        agent: 'Developer',
        message: 'Developer.error.compilation',
      })

      expect(data.logs[1]).toMatchObject({
        id: 'log-2',
        level: 'warn',
        agent: 'QA',
      })

      expect(data.logs[2]).toMatchObject({
        id: 'log-3',
        level: 'success',
        agent: 'DevOps',
      })

      expect(data.logs[3]).toMatchObject({
        id: 'log-4',
        level: 'info',
        agent: 'System',
      })
    })

    it('should filter by level parameter after transformation', async () => {
      const mockLogs = [
        {
          id: 'log-1',
          action: 'Developer.error.build',
          resource: 'project',
          details: {},
          userId: 'user-1',
          createdAt: new Date(),
        },
        {
          id: 'log-2',
          action: 'QA.completed',
          resource: 'tests',
          details: {},
          userId: 'user-2',
          createdAt: new Date(),
        },
        {
          id: 'log-3',
          action: 'DevOps.warn.resources',
          resource: 'server',
          details: {},
          userId: 'user-3',
          createdAt: new Date(),
        },
      ]

      vi.mocked(prisma.auditLog.findMany).mockResolvedValue(mockLogs as any)

      const request = new NextRequest('http://localhost:3000/api/observability/logs?level=error')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.logs).toHaveLength(1)
      expect(data.logs[0].level).toBe('error')
      expect(data.total).toBe(1)
    })

    it('should extract agent name from action correctly', async () => {
      const mockLogs = [
        {
          id: 'log-1',
          action: 'Developer.build.success',
          resource: 'project',
          details: {},
          userId: 'user-1',
          createdAt: new Date(),
        },
        {
          id: 'log-2',
          action: 'build.success', // No dot-separated agent
          resource: 'project',
          details: {},
          userId: 'user-2',
          createdAt: new Date(),
        },
      ]

      vi.mocked(prisma.auditLog.findMany).mockResolvedValue(mockLogs as any)

      const request = new NextRequest('http://localhost:3000/api/observability/logs')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.logs[0].agent).toBe('Developer')
      expect(data.logs[1].agent).toBe('build') // First part before dot, or the whole action
    })

    it('should return empty array when no logs found', async () => {
      vi.mocked(prisma.auditLog.findMany).mockResolvedValue([])

      const request = new NextRequest('http://localhost:3000/api/observability/logs')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.logs).toEqual([])
      expect(data.total).toBe(0)
    })

    it('should return 500 when database query fails', async () => {
      vi.mocked(prisma.auditLog.findMany).mockRejectedValue(new Error('Database error'))

      const request = new NextRequest('http://localhost:3000/api/observability/logs')
      const response = await GET(request)

      expect(response.status).toBe(500)
      const data = await response.json()

      expect(data).toEqual({
        error: 'Failed to fetch logs',
      })
    })

    it('should combine search with agent filter correctly', async () => {
      vi.mocked(prisma.auditLog.findMany).mockResolvedValue([])

      const request = new NextRequest(
        'http://localhost:3000/api/observability/logs?search=build&agent=Developer'
      )
      const response = await GET(request)

      expect(response.status).toBe(200)

      // When both search and agent are provided, both filters are applied
      expect(prisma.auditLog.findMany).toHaveBeenCalledWith({
        where: {
          OR: [
            { action: { contains: 'build', mode: 'insensitive' } },
            { resource: { contains: 'build', mode: 'insensitive' } },
          ],
          action: { contains: 'Developer', mode: 'insensitive' },
        },
        orderBy: { createdAt: 'desc' },
        take: 50,
      })
    })

    it('should handle failed action as error level', async () => {
      const mockLogs = [
        {
          id: 'log-1',
          action: 'Developer.failed',
          resource: 'build',
          details: {},
          userId: 'user-1',
          createdAt: new Date(),
        },
      ]

      vi.mocked(prisma.auditLog.findMany).mockResolvedValue(mockLogs as any)

      const request = new NextRequest('http://localhost:3000/api/observability/logs')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.logs[0].level).toBe('error')
    })

    it('should handle degraded action as warn level', async () => {
      const mockLogs = [
        {
          id: 'log-1',
          action: 'System.degraded.performance',
          resource: 'api',
          details: {},
          userId: null,
          createdAt: new Date(),
        },
      ]

      vi.mocked(prisma.auditLog.findMany).mockResolvedValue(mockLogs as any)

      const request = new NextRequest('http://localhost:3000/api/observability/logs')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.logs[0].level).toBe('warn')
    })

    it('should handle completed action as success level', async () => {
      const mockLogs = [
        {
          id: 'log-1',
          action: 'QA.completed.tests',
          resource: 'test-suite',
          details: {},
          userId: 'user-1',
          createdAt: new Date(),
        },
      ]

      vi.mocked(prisma.auditLog.findMany).mockResolvedValue(mockLogs as any)

      const request = new NextRequest('http://localhost:3000/api/observability/logs')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.logs[0].level).toBe('success')
    })
  })
})
