import { describe, it, expect, vi, beforeEach } from 'vitest'
import { POST } from '@/app/api/wizard/single/step/route'
import { NextRequest } from 'next/server'
import * as execModule from '@/lib/server/exec'

// Mock the execStream function
vi.mock('@/lib/server/exec', () => ({
  execStream: vi.fn(),
}))

describe('API Route: /api/wizard/single/step', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('POST /api/wizard/single/step', () => {
    it('should successfully execute wizard step with valid request', async () => {
      const mockChild = {
        stdout: {
          on: vi.fn((event, callback) => {
            if (event === 'data') {
              setTimeout(() => callback(Buffer.from('Executing step...\n')), 10)
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

      const request = new NextRequest('http://localhost:3000/api/wizard/single/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'init',
          args: ['--project', 'test-saas'],
          workdir: '/tmp/test-project',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(response.headers.get('Content-Type')).toBe('text/plain; charset=utf-8')
      expect(response.headers.get('Cache-Control')).toBe('no-cache')
      expect(response.headers.get('Connection')).toBe('keep-alive')

      expect(execModule.execStream).toHaveBeenCalledWith(
        '/bin/bash',
        ['-lc', './cli/saas-builder.sh init --project test-saas'],
        { cwd: '/tmp/test-project' }
      )
    })

    it('should handle empty args array', async () => {
      const mockChild = {
        stdout: { on: vi.fn() },
        stderr: { on: vi.fn() },
        on: vi.fn((event, callback) => {
          if (event === 'close') callback(0)
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/wizard/single/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'deploy',
          workdir: '/tmp/test-project',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(execModule.execStream).toHaveBeenCalledWith(
        '/bin/bash',
        ['-lc', './cli/saas-builder.sh deploy '],
        { cwd: '/tmp/test-project' }
      )
    })

    it('should stream both stdout and stderr', async () => {
      const mockChild = {
        stdout: {
          on: vi.fn((event, callback) => {
            if (event === 'data') {
              setTimeout(() => callback(Buffer.from('stdout message\n')), 10)
            }
          }),
        },
        stderr: {
          on: vi.fn((event, callback) => {
            if (event === 'data') {
              setTimeout(() => callback(Buffer.from('stderr message\n')), 15)
            }
          }),
        },
        on: vi.fn((event, callback) => {
          if (event === 'close') {
            setTimeout(() => callback(0), 50)
          }
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/wizard/single/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'build',
          workdir: '/tmp/test-project',
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

      const request = new NextRequest('http://localhost:3000/api/wizard/single/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'test',
          workdir: '/tmp/test-project',
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
            callback(new Error('Process execution failed'))
          }
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/wizard/single/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'validate',
          workdir: '/tmp/test-project',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
    })

    it('should return 400 for invalid request body (missing step)', async () => {
      const request = new NextRequest('http://localhost:3000/api/wizard/single/step', {
        method: 'POST',
        body: JSON.stringify({
          workdir: '/tmp/test-project',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })

    it('should use default workdir when not provided', async () => {
      const mockChild = {
        stdout: { on: vi.fn() },
        stderr: { on: vi.fn() },
        on: vi.fn((event, callback) => {
          if (event === 'close') callback(0)
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/wizard/single/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'init',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(execModule.execStream).toHaveBeenCalledWith(
        '/bin/bash',
        ['-lc', './cli/saas-builder.sh init '],
        { cwd: '/home/doctor/temponest' }
      )
    })

    it('should return 400 for malformed JSON', async () => {
      const request = new NextRequest('http://localhost:3000/api/wizard/single/step', {
        method: 'POST',
        body: 'invalid json',
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })

    it('should handle args with special characters', async () => {
      const mockChild = {
        stdout: { on: vi.fn() },
        stderr: { on: vi.fn() },
        on: vi.fn((event, callback) => {
          if (event === 'close') callback(0)
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/wizard/single/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'configure',
          args: ['--name', 'My SaaS App', '--tag', 'v1.0'],
          workdir: '/tmp/test-project',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(execModule.execStream).toHaveBeenCalledWith(
        '/bin/bash',
        ['-lc', './cli/saas-builder.sh configure --name My SaaS App --tag v1.0'],
        { cwd: '/tmp/test-project' }
      )
    })
  })
})
