import { describe, it, expect, vi, beforeEach } from 'vitest'
import { GET } from '@/app/api/observability/metrics/route'
import { prisma } from '@/lib/db/client'

// Mock Prisma
vi.mock('@/lib/db/client', () => ({
  prisma: {
    run: {
      count: vi.fn(),
      findMany: vi.fn(),
    },
    $queryRaw: vi.fn(),
  },
}))

describe('API Route: /api/observability/metrics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('GET /api/observability/metrics', () => {
    it('should return comprehensive metrics summary', async () => {
      // Mock all database calls
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(5) // activeJobs
        .mockResolvedValueOnce(3) // queueDepth
        .mockResolvedValueOnce(20) // totalRuns
        .mockResolvedValueOnce(18) // successfulRuns

      const mockCompletedRuns = [
        {
          startedAt: new Date('2025-01-01T10:00:00Z'),
          finishedAt: new Date('2025-01-01T10:02:00Z'),
        },
        {
          startedAt: new Date('2025-01-01T10:05:00Z'),
          finishedAt: new Date('2025-01-01T10:06:30Z'),
        },
      ]
      const mockStatusDistribution = [
        { status: 'success', count: BigInt(15) },
        { status: 'failed', count: BigInt(3) },
        { status: 'running', count: BigInt(2) },
      ]
      const mockRunsByAgent = [
        { agent: 'Developer', count: BigInt(10) },
        { agent: 'QA', count: BigInt(5) },
        { agent: 'DevOps', count: BigInt(3) },
      ]
      const mockRecentErrors = [
        {
          id: 'error-1',
          step: 'Developer: Build failed',
          finishedAt: new Date('2025-01-01T11:00:00Z'),
          logs: 'Error: Compilation failed due to syntax error in file.ts',
        },
      ]

      // Set up mocks in correct order: first findMany is for completedRuns, second is for recentErrors
      vi.mocked(prisma.run.findMany)
        .mockResolvedValueOnce(mockCompletedRuns as any)
        .mockResolvedValueOnce(mockRecentErrors as any)

      vi.mocked(prisma.$queryRaw)
        .mockResolvedValueOnce(mockStatusDistribution)
        .mockResolvedValueOnce(mockRunsByAgent)

      const response = await GET()

      expect(response.status).toBe(200)
      const data = await response.json()

      // Verify summary
      expect(data.summary).toMatchObject({
        activeJobs: 5,
        queueDepth: 3,
        successRate: 90, // 18/20 * 100
      })
      expect(data.summary.avgDuration).toBeGreaterThan(0)
      expect(data.summary.avgDurationFormatted).toBeDefined()

      // Verify charts
      expect(data.charts.statusDistribution).toEqual([
        { status: 'success', count: 15 },
        { status: 'failed', count: 3 },
        { status: 'running', count: 2 },
      ])
      expect(data.charts.runsByAgent).toEqual([
        { agent: 'Developer', count: 10 },
        { agent: 'QA', count: 5 },
        { agent: 'DevOps', count: 3 },
      ])

      // Verify recent errors
      expect(data.recentErrors).toHaveLength(1)
      expect(data.recentErrors[0]).toMatchObject({
        id: 'error-1',
        step: 'Developer: Build failed',
        preview: 'Error: Compilation failed due to syntax error in file.ts',
      })
    })

    it('should handle zero completed runs (no duration data)', async () => {
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(0) // activeJobs
        .mockResolvedValueOnce(0) // queueDepth
        .mockResolvedValueOnce(0) // totalRuns
        .mockResolvedValueOnce(0) // successfulRuns

      vi.mocked(prisma.run.findMany).mockResolvedValue([])
      vi.mocked(prisma.$queryRaw)
        .mockResolvedValueOnce([])
        .mockResolvedValueOnce([])

      const response = await GET()

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.summary.avgDuration).toBe(0)
      expect(data.summary.successRate).toBe(0)
      expect(data.charts.statusDistribution).toEqual([])
      expect(data.charts.runsByAgent).toEqual([])
      expect(data.recentErrors).toEqual([])
    })

    it('should calculate average duration correctly', async () => {
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(2)
        .mockResolvedValueOnce(1)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(9)

      const mockCompletedRuns = [
        {
          startedAt: new Date('2025-01-01T10:00:00Z'),
          finishedAt: new Date('2025-01-01T10:01:00Z'), // 60 seconds
        },
        {
          startedAt: new Date('2025-01-01T10:05:00Z'),
          finishedAt: new Date('2025-01-01T10:07:00Z'), // 120 seconds
        },
      ]
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce(mockCompletedRuns as any)
      vi.mocked(prisma.$queryRaw).mockResolvedValue([])
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce([])

      const response = await GET()

      expect(response.status).toBe(200)
      const data = await response.json()

      // Average: (60 + 120) / 2 = 90 seconds
      expect(data.summary.avgDuration).toBe(90)
      expect(data.summary.avgDurationFormatted).toBe('1m 30s')
    })

    it('should format duration correctly for seconds', async () => {
      vi.mocked(prisma.run.count).mockResolvedValue(0)

      const mockCompletedRuns = [
        {
          startedAt: new Date('2025-01-01T10:00:00Z'),
          finishedAt: new Date('2025-01-01T10:00:45Z'), // 45 seconds
        },
      ]
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce(mockCompletedRuns as any)
      vi.mocked(prisma.$queryRaw).mockResolvedValue([])
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce([])

      const response = await GET()
      const data = await response.json()

      expect(data.summary.avgDurationFormatted).toBe('45s')
    })

    it('should format duration correctly for hours', async () => {
      vi.mocked(prisma.run.count).mockResolvedValue(0)

      const mockCompletedRuns = [
        {
          startedAt: new Date('2025-01-01T10:00:00Z'),
          finishedAt: new Date('2025-01-01T12:30:00Z'), // 2h 30m
        },
      ]
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce(mockCompletedRuns as any)
      vi.mocked(prisma.$queryRaw).mockResolvedValue([])
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce([])

      const response = await GET()
      const data = await response.json()

      expect(data.summary.avgDurationFormatted).toBe('2h 30m')
    })

    it('should truncate error logs preview to 200 characters', async () => {
      vi.mocked(prisma.run.count).mockResolvedValue(0)
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce([])
      vi.mocked(prisma.$queryRaw).mockResolvedValue([])

      const longErrorLog = 'A'.repeat(300)
      const mockRecentErrors = [
        {
          id: 'error-1',
          step: 'Test',
          finishedAt: new Date(),
          logs: longErrorLog,
        },
      ]
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce(mockRecentErrors as any)

      const response = await GET()
      const data = await response.json()

      expect(data.recentErrors[0].preview).toHaveLength(200)
      expect(data.recentErrors[0].preview).toBe('A'.repeat(200))
    })

    it('should classify agents from step descriptions', async () => {
      vi.mocked(prisma.run.count).mockResolvedValue(0)
      vi.mocked(prisma.run.findMany).mockResolvedValue([])

      const mockRunsByAgent = [
        { agent: 'Developer', count: BigInt(5) },
        { agent: 'QA', count: BigInt(3) },
        { agent: 'DevOps', count: BigInt(2) },
        { agent: 'Designer', count: BigInt(1) },
        { agent: 'Security', count: BigInt(1) },
        { agent: 'Overseer', count: BigInt(1) },
        { agent: 'UX', count: BigInt(1) },
        { agent: 'Other', count: BigInt(2) },
      ]

      vi.mocked(prisma.$queryRaw)
        .mockResolvedValueOnce([])
        .mockResolvedValueOnce(mockRunsByAgent)

      const response = await GET()
      const data = await response.json()

      expect(data.charts.runsByAgent).toHaveLength(8)
      expect(data.charts.runsByAgent.map((r: any) => r.agent)).toContain('Developer')
      expect(data.charts.runsByAgent.map((r: any) => r.agent)).toContain('Other')
    })

    it('should return 500 when database query fails', async () => {
      vi.mocked(prisma.run.count).mockRejectedValue(new Error('Database error'))

      const response = await GET()

      expect(response.status).toBe(500)
      const data = await response.json()

      expect(data).toEqual({
        error: 'Failed to fetch metrics',
      })
    })

    it('should handle runs without timestamps gracefully', async () => {
      vi.mocked(prisma.run.count).mockResolvedValue(0)

      const mockCompletedRuns = [
        {
          startedAt: null,
          finishedAt: null,
        },
        {
          startedAt: new Date('2025-01-01T10:00:00Z'),
          finishedAt: null,
        },
      ]
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce(mockCompletedRuns as any)
      vi.mocked(prisma.$queryRaw).mockResolvedValue([])
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce([])

      const response = await GET()

      expect(response.status).toBe(200)
      const data = await response.json()

      // Should not crash and should skip invalid runs
      expect(data.summary.avgDuration).toBe(0)
    })

    it('should limit recent errors to 10 items', async () => {
      vi.mocked(prisma.run.count).mockResolvedValue(0)
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce([])
      vi.mocked(prisma.$queryRaw).mockResolvedValue([])

      const mockManyErrors = Array.from({ length: 15 }, (_, i) => ({
        id: `error-${i}`,
        step: `Error ${i}`,
        finishedAt: new Date(),
        logs: `Error log ${i}`,
      }))
      vi.mocked(prisma.run.findMany).mockResolvedValueOnce(mockManyErrors as any)

      const response = await GET()
      const data = await response.json()

      // The query itself uses 'take: 10' to limit the results
      expect(prisma.run.findMany).toHaveBeenCalledWith(
        expect.objectContaining({ take: 10 })
      )
    })
  })
})
