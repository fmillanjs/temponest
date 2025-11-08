import { describe, it, expect, vi, beforeEach } from 'vitest'
import { POST } from '@/app/api/financials/run/route'
import { NextRequest } from 'next/server'
import * as execModule from '@/lib/server/exec'

// Mock the execStream function
vi.mock('@/lib/server/exec', () => ({
  execStream: vi.fn(),
}))

describe('API Route: /api/financials/run', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('POST /api/financials/run', () => {
    it('should successfully start financial calculation with valid request', async () => {
      const mockChild = {
        stdout: {
          on: vi.fn((event, callback) => {
            if (event === 'data') {
              setTimeout(() => callback(Buffer.from('Calculating...\n')), 10)
            }
          }),
        },
        stderr: {
          on: vi.fn(),
        },
        on: vi.fn((event, callback) => {
          if (event === 'close') {
            setTimeout(() => callback(0), 50)
          }
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/financials/run', {
        method: 'POST',
        body: JSON.stringify({
          model: 'conservative',
          args: ['arg1', 'arg2'],
          workdir: '/tmp/test',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(response.headers.get('Content-Type')).toBe('text/plain; charset=utf-8')
      expect(response.headers.get('Cache-Control')).toBe('no-cache')
      expect(response.headers.get('Connection')).toBe('keep-alive')

      expect(execModule.execStream).toHaveBeenCalledWith(
        'python3',
        ['tools/saas-calculator.py', 'conservative', 'arg1', 'arg2'],
        { cwd: '/tmp/test' }
      )
    })

    it('should handle missing args parameter (defaults to empty array)', async () => {
      const mockChild = {
        stdout: { on: vi.fn() },
        stderr: { on: vi.fn() },
        on: vi.fn((event, callback) => {
          if (event === 'close') callback(0)
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/financials/run', {
        method: 'POST',
        body: JSON.stringify({
          model: 'aggressive',
          workdir: '/tmp/test',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(execModule.execStream).toHaveBeenCalledWith(
        'python3',
        ['tools/saas-calculator.py', 'aggressive'],
        { cwd: '/tmp/test' }
      )
    })

    it('should stream stderr as error messages', async () => {
      const mockChild = {
        stdout: { on: vi.fn() },
        stderr: {
          on: vi.fn((event, callback) => {
            if (event === 'data') {
              setTimeout(() => callback(Buffer.from('Error occurred\n')), 10)
            }
          }),
        },
        on: vi.fn((event, callback) => {
          if (event === 'close') {
            setTimeout(() => callback(1), 50)
          }
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/financials/run', {
        method: 'POST',
        body: JSON.stringify({
          model: 'conservative',
          workdir: '/tmp/test',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(response.body).toBeTruthy()
    })

    it('should handle process exit with non-zero code', async () => {
      const mockChild = {
        stdout: { on: vi.fn() },
        stderr: { on: vi.fn() },
        on: vi.fn((event, callback) => {
          if (event === 'close') {
            callback(1)
          }
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/financials/run', {
        method: 'POST',
        body: JSON.stringify({
          model: 'conservative',
          workdir: '/tmp/test',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(response.body).toBeTruthy()
    })

    it('should handle process error event', async () => {
      const mockChild = {
        stdout: { on: vi.fn() },
        stderr: { on: vi.fn() },
        on: vi.fn((event, callback) => {
          if (event === 'error') {
            callback(new Error('Process failed'))
          }
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/financials/run', {
        method: 'POST',
        body: JSON.stringify({
          model: 'conservative',
          workdir: '/tmp/test',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
    })

    it('should return 400 for invalid request body (missing model)', async () => {
      const request = new NextRequest('http://localhost:3000/api/financials/run', {
        method: 'POST',
        body: JSON.stringify({
          workdir: '/tmp/test',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })

    it('should return 400 for invalid request body (missing workdir)', async () => {
      const request = new NextRequest('http://localhost:3000/api/financials/run', {
        method: 'POST',
        body: JSON.stringify({
          model: 'conservative',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })

    it('should return 400 for malformed JSON', async () => {
      const request = new NextRequest('http://localhost:3000/api/financials/run', {
        method: 'POST',
        body: 'invalid json',
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })

    it('should return 400 for invalid args type', async () => {
      const request = new NextRequest('http://localhost:3000/api/financials/run', {
        method: 'POST',
        body: JSON.stringify({
          model: 'conservative',
          args: 'not-an-array',
          workdir: '/tmp/test',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })
  })
})
