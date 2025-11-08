import { describe, it, expect, vi, beforeEach } from 'vitest'
import { POST } from '@/app/api/financials/save/route'
import { NextRequest } from 'next/server'
import { prisma } from '@/lib/db/client'

// Mock Prisma
vi.mock('@/lib/db/client', () => ({
  prisma: {
    run: {
      create: vi.fn(),
    },
  },
}))

describe('API Route: /api/financials/save', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('POST /api/financials/save', () => {
    it('should successfully save calculation with valid data', async () => {
      const mockRun = {
        id: 'test-run-id-123',
        projectId: '00000000-0000-0000-0000-000000000000',
        kind: 'calc',
        step: 'Financial calculation: conservative',
        status: 'success',
        startedAt: new Date(),
        finishedAt: new Date(),
      }

      vi.mocked(prisma.run.create).mockResolvedValue(mockRun as any)

      const validPayload = {
        model: 'conservative',
        summary: {
          productName: 'Test SaaS',
          month12: {
            customers: 100,
            mrr: 5000,
            arr: 60000,
            profit: 20000,
          },
          month24: {
            customers: 500,
            mrr: 25000,
            arr: 300000,
            profit: 150000,
          },
        },
        monthlyData: [
          {
            month: 1,
            customers: 10,
            mrr: 500,
            profit: 100,
            cumulative: 100,
          },
          {
            month: 2,
            customers: 20,
            mrr: 1000,
            profit: 300,
            cumulative: 400,
          },
        ],
      }

      const request = new NextRequest('http://localhost:3000/api/financials/save', {
        method: 'POST',
        body: JSON.stringify(validPayload),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      const data = await response.json()
      expect(data).toEqual({
        success: true,
        runId: 'test-run-id-123',
      })

      expect(prisma.run.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          projectId: '00000000-0000-0000-0000-000000000000',
          kind: 'calc',
          status: 'success',
          step: 'Financial calculation: conservative',
        }),
      })
    })

    it('should save calculation with custom project ID', async () => {
      const mockRun = {
        id: 'test-run-id-456',
        projectId: '11111111-1111-1111-1111-111111111111',
      }

      vi.mocked(prisma.run.create).mockResolvedValue(mockRun as any)

      const validPayload = {
        model: 'aggressive',
        projectId: '11111111-1111-1111-1111-111111111111',
        summary: {
          productName: 'Custom Project',
          month12: {
            customers: 200,
            mrr: 10000,
            arr: 120000,
            profit: 40000,
          },
          month24: {
            customers: 1000,
            mrr: 50000,
            arr: 600000,
            profit: 300000,
          },
        },
        monthlyData: [],
      }

      const request = new NextRequest('http://localhost:3000/api/financials/save', {
        method: 'POST',
        body: JSON.stringify(validPayload),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      const data = await response.json()
      expect(data.success).toBe(true)

      expect(prisma.run.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          projectId: '11111111-1111-1111-1111-111111111111',
        }),
      })
    })

    it('should store calculation data in artifacts', async () => {
      const mockRun = { id: 'test-run-id' }
      vi.mocked(prisma.run.create).mockResolvedValue(mockRun as any)

      const validPayload = {
        model: 'moderate',
        summary: {
          productName: 'Test Product',
          month12: { customers: 50, mrr: 2500, arr: 30000, profit: 10000 },
          month24: { customers: 250, mrr: 12500, arr: 150000, profit: 75000 },
        },
        monthlyData: [
          { month: 1, customers: 5, mrr: 250, profit: 50, cumulative: 50 },
        ],
      }

      const request = new NextRequest('http://localhost:3000/api/financials/save', {
        method: 'POST',
        body: JSON.stringify(validPayload),
      })

      await POST(request)

      const createCall = vi.mocked(prisma.run.create).mock.calls[0][0]
      expect(createCall.data.artifacts).toMatchObject({
        model: 'moderate',
        summary: validPayload.summary,
        monthlyData: validPayload.monthlyData,
      })
      expect(createCall.data.artifacts).toHaveProperty('timestamp')
    })

    it('should return 400 for invalid schema (missing model)', async () => {
      const invalidPayload = {
        summary: {
          productName: 'Test',
          month12: { customers: 100, mrr: 5000, arr: 60000, profit: 20000 },
          month24: { customers: 500, mrr: 25000, arr: 300000, profit: 150000 },
        },
        monthlyData: [],
      }

      const request = new NextRequest('http://localhost:3000/api/financials/save', {
        method: 'POST',
        body: JSON.stringify(invalidPayload),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })

    it('should return 400 for invalid schema (missing summary)', async () => {
      const invalidPayload = {
        model: 'conservative',
        monthlyData: [],
      }

      const request = new NextRequest('http://localhost:3000/api/financials/save', {
        method: 'POST',
        body: JSON.stringify(invalidPayload),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })

    it('should return 400 for invalid projectId format', async () => {
      const invalidPayload = {
        model: 'conservative',
        projectId: 'not-a-uuid',
        summary: {
          productName: 'Test',
          month12: { customers: 100, mrr: 5000, arr: 60000, profit: 20000 },
          month24: { customers: 500, mrr: 25000, arr: 300000, profit: 150000 },
        },
        monthlyData: [],
      }

      const request = new NextRequest('http://localhost:3000/api/financials/save', {
        method: 'POST',
        body: JSON.stringify(invalidPayload),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })

    it('should return 400 when database operation fails', async () => {
      vi.mocked(prisma.run.create).mockRejectedValue(new Error('Database error'))

      const validPayload = {
        model: 'conservative',
        summary: {
          productName: 'Test',
          month12: { customers: 100, mrr: 5000, arr: 60000, profit: 20000 },
          month24: { customers: 500, mrr: 25000, arr: 300000, profit: 150000 },
        },
        monthlyData: [],
      }

      const request = new NextRequest('http://localhost:3000/api/financials/save', {
        method: 'POST',
        body: JSON.stringify(validPayload),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data.error).toBe('Database error')
    })

    it('should return 400 for malformed JSON', async () => {
      const request = new NextRequest('http://localhost:3000/api/financials/save', {
        method: 'POST',
        body: 'invalid json',
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })
  })
})
