import { describe, it, expect, vi, beforeEach } from 'vitest'
import { GET } from '@/app/api/git/summary/route'
import { NextRequest } from 'next/server'
import * as execModule from '@/lib/server/exec'

// Mock the execCollect function
vi.mock('@/lib/server/exec', () => ({
  execCollect: vi.fn(),
}))

describe('API Route: /api/git/summary', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('GET /api/git/summary', () => {
    it('should return git summary with status, branch, and last commit', async () => {
      vi.mocked(execModule.execCollect)
        .mockResolvedValueOnce({ stdout: 'M file1.txt\nA file2.txt\n', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: 'main\n', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: 'abc123 Latest commit message\n', stderr: '', code: 0 })

      const request = new NextRequest('http://localhost:3000/api/git/summary?workdir=/tmp/repo')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data).toEqual({
        status: 'M file1.txt\nA file2.txt\n',
        branch: 'main',
        lastCommit: 'abc123 Latest commit message',
        hasChanges: true,
      })

      expect(execModule.execCollect).toHaveBeenNthCalledWith(1, 'git', ['status', '--short'], { cwd: '/tmp/repo' })
      expect(execModule.execCollect).toHaveBeenNthCalledWith(2, 'git', ['branch', '--show-current'], { cwd: '/tmp/repo' })
      expect(execModule.execCollect).toHaveBeenNthCalledWith(3, 'git', ['log', '-1', '--oneline'], { cwd: '/tmp/repo' })
    })

    it('should use default workdir when not provided', async () => {
      vi.mocked(execModule.execCollect)
        .mockResolvedValueOnce({ stdout: '', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: 'develop', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: 'def456 Initial commit', stderr: '', code: 0 })

      const request = new NextRequest('http://localhost:3000/api/git/summary')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data).toEqual({
        status: '',
        branch: 'develop',
        lastCommit: 'def456 Initial commit',
        hasChanges: false,
      })

      expect(execModule.execCollect).toHaveBeenNthCalledWith(1, 'git', ['status', '--short'], { cwd: '/home/doctor/temponest' })
    })

    it('should indicate hasChanges=false when status is empty', async () => {
      vi.mocked(execModule.execCollect)
        .mockResolvedValueOnce({ stdout: '', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: 'main', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: 'xyz789 Clean state', stderr: '', code: 0 })

      const request = new NextRequest('http://localhost:3000/api/git/summary?workdir=/tmp/clean-repo')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.hasChanges).toBe(false)
      expect(data.status).toBe('')
    })

    it('should indicate hasChanges=true when status has content', async () => {
      vi.mocked(execModule.execCollect)
        .mockResolvedValueOnce({ stdout: 'M modified.txt\n', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: 'feature-branch', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: 'aaa111 Feature work', stderr: '', code: 0 })

      const request = new NextRequest('http://localhost:3000/api/git/summary?workdir=/tmp/dirty-repo')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.hasChanges).toBe(true)
      expect(data.status).toBe('M modified.txt\n')
    })

    it('should trim branch name whitespace', async () => {
      vi.mocked(execModule.execCollect)
        .mockResolvedValueOnce({ stdout: '', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: '  feature/test-branch  \n', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: 'bbb222 Test commit\n', stderr: '', code: 0 })

      const request = new NextRequest('http://localhost:3000/api/git/summary?workdir=/tmp/repo')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.branch).toBe('feature/test-branch')
    })

    it('should trim last commit whitespace', async () => {
      vi.mocked(execModule.execCollect)
        .mockResolvedValueOnce({ stdout: '', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: 'main', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: '  ccc333 Commit with spaces  \n\n', stderr: '', code: 0 })

      const request = new NextRequest('http://localhost:3000/api/git/summary?workdir=/tmp/repo')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data.lastCommit).toBe('ccc333 Commit with spaces')
    })

    it('should return 500 when git command fails', async () => {
      vi.mocked(execModule.execCollect).mockRejectedValue(new Error('git command failed'))

      const request = new NextRequest('http://localhost:3000/api/git/summary?workdir=/tmp/invalid-repo')
      const response = await GET(request)

      expect(response.status).toBe(500)
      const data = await response.json()

      expect(data).toEqual({
        error: 'git command failed',
      })
    })

    it('should return 500 with generic error for unknown errors', async () => {
      vi.mocked(execModule.execCollect).mockRejectedValue('Unknown error')

      const request = new NextRequest('http://localhost:3000/api/git/summary?workdir=/tmp/repo')
      const response = await GET(request)

      expect(response.status).toBe(500)
      const data = await response.json()

      expect(data).toEqual({
        error: 'Unknown error',
      })
    })

    it('should handle empty git output', async () => {
      vi.mocked(execModule.execCollect)
        .mockResolvedValueOnce({ stdout: '', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: '', stderr: '', code: 0 })
        .mockResolvedValueOnce({ stdout: '', stderr: '', code: 0 })

      const request = new NextRequest('http://localhost:3000/api/git/summary')
      const response = await GET(request)

      expect(response.status).toBe(200)
      const data = await response.json()

      expect(data).toEqual({
        status: '',
        branch: '',
        lastCommit: '',
        hasChanges: false,
      })
    })
  })
})
