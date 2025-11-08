import { describe, it, expect, vi, beforeEach } from 'vitest'
import { POST } from '@/app/api/wizard/factory/step/route'
import { NextRequest } from 'next/server'
import * as execModule from '@/lib/server/exec'

// Mock the execStream function
vi.mock('@/lib/server/exec', () => ({
  execStream: vi.fn(),
}))

describe('API Route: /api/wizard/factory/step', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('POST /api/wizard/factory/step', () => {
    it('should successfully execute factory wizard step', async () => {
      const mockChild = {
        stdout: {
          on: vi.fn((event, callback) => {
            if (event === 'data') {
              setTimeout(() => callback(Buffer.from('Initializing factory...\n')), 10)
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

      const request = new NextRequest('http://localhost:3000/api/wizard/factory/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'init',
          args: ['--factory', 'saas-factory'],
          workdir: '/tmp/factory-project',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(response.headers.get('Content-Type')).toBe('text/plain; charset=utf-8')
      expect(response.headers.get('Cache-Control')).toBe('no-cache')

      expect(execModule.execStream).toHaveBeenCalledWith(
        '/bin/bash',
        ['-lc', './cli/saas-factory-init.sh init --factory saas-factory'],
        { cwd: '/tmp/factory-project' }
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

      const request = new NextRequest('http://localhost:3000/api/wizard/factory/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'setup',
          workdir: '/tmp/factory-project',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(execModule.execStream).toHaveBeenCalledWith(
        '/bin/bash',
        ['-lc', './cli/saas-factory-init.sh setup '],
        { cwd: '/tmp/factory-project' }
      )
    })

    it('should stream stdout and stderr', async () => {
      const mockChild = {
        stdout: {
          on: vi.fn((event, callback) => {
            if (event === 'data') {
              callback(Buffer.from('stdout\n'))
            }
          }),
        },
        stderr: {
          on: vi.fn((event, callback) => {
            if (event === 'data') {
              callback(Buffer.from('stderr\n'))
            }
          }),
        },
        on: vi.fn((event, callback) => {
          if (event === 'close') {
            callback(0)
          }
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/wizard/factory/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'build',
          workdir: '/tmp/factory-project',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
      expect(response.body).toBeTruthy()
    })

    it('should return 400 for invalid schema (missing step)', async () => {
      const request = new NextRequest('http://localhost:3000/api/wizard/factory/step', {
        method: 'POST',
        body: JSON.stringify({
          workdir: '/tmp/factory-project',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })

    it('should return 400 for invalid schema (missing workdir)', async () => {
      const request = new NextRequest('http://localhost:3000/api/wizard/factory/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'init',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })

    it('should handle process error gracefully', async () => {
      const mockChild = {
        stdout: { on: vi.fn() },
        stderr: { on: vi.fn() },
        on: vi.fn((event, callback) => {
          if (event === 'error') {
            callback(new Error('Failed to execute'))
          }
        }),
      }

      vi.mocked(execModule.execStream).mockReturnValue(mockChild as any)

      const request = new NextRequest('http://localhost:3000/api/wizard/factory/step', {
        method: 'POST',
        body: JSON.stringify({
          step: 'deploy',
          workdir: '/tmp/factory-project',
        }),
      })

      const response = await POST(request)

      expect(response.status).toBe(200)
    })

    it('should return 400 for malformed JSON', async () => {
      const request = new NextRequest('http://localhost:3000/api/wizard/factory/step', {
        method: 'POST',
        body: 'not valid json',
      })

      const response = await POST(request)

      expect(response.status).toBe(400)
      const data = await response.json()
      expect(data).toHaveProperty('error')
    })
  })
})
