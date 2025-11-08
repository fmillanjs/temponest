import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import ProjectsPage from '@/app/projects/page'

// Mock the Prisma client
vi.mock('@/lib/db/client', () => ({
  prisma: {
    project: {
      findMany: vi.fn(),
    },
  },
}))

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: any) => <a href={href}>{children}</a>,
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  FolderKanban: () => <div data-testid="folder-icon">Folder Icon</div>,
  ArrowRight: () => <div data-testid="arrow-icon">Arrow Icon</div>,
}))

describe('ProjectsPage', () => {
  const { prisma } = await import('@/lib/db/client')

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders projects heading', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await ProjectsPage()
      render(page)

      expect(screen.getByText('Projects')).toBeInTheDocument()
      expect(screen.getByText('Manage your SaaS products')).toBeInTheDocument()
    })

    it('renders new project button', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await ProjectsPage()
      render(page)

      expect(screen.getByText('New Project')).toBeInTheDocument()
    })

    it('shows empty state when no projects exist', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await ProjectsPage()
      render(page)

      expect(screen.getByText('No projects yet. Create your first SaaS project!')).toBeInTheDocument()
    })
  })

  describe('Data Fetching', () => {
    it('fetches projects with correct query', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      await ProjectsPage()

      expect(prisma.project.findMany).toHaveBeenCalledWith({
        orderBy: { updatedAt: 'desc' },
        include: {
          _count: {
            select: { runs: true },
          },
        },
      })
    })

    it('orders projects by most recently updated', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      await ProjectsPage()

      const call = vi.mocked(prisma.project.findMany).mock.calls[0][0]
      expect(call.orderBy).toEqual({ updatedAt: 'desc' })
    })

    it('includes runs count in query', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      await ProjectsPage()

      const call = vi.mocked(prisma.project.findMany).mock.calls[0][0]
      expect(call.include?._count?.select).toEqual({ runs: true })
    })
  })

  describe('Project Display', () => {
    it('displays project cards when projects exist', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'Test SaaS',
          slug: 'test-saas',
          status: 'build',
          type: 'single',
          updatedAt: new Date('2025-11-07T10:00:00Z'),
          repoUrl: 'https://github.com/user/test',
          _count: { runs: 5 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await ProjectsPage()
      render(page)

      expect(screen.getByText('Test SaaS')).toBeInTheDocument()
    })

    it('displays project type correctly', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'Single SaaS',
          slug: 'single',
          status: 'build',
          type: 'single',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 0 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
        {
          id: '2',
          name: 'Portfolio',
          slug: 'portfolio',
          status: 'qa',
          type: 'portfolio',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 0 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await ProjectsPage()
      render(page)

      expect(screen.getByText(/Single SaaS • 0 runs/)).toBeInTheDocument()
      expect(screen.getByText(/Portfolio • 0 runs/)).toBeInTheDocument()
    })

    it('displays runs count', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'Test Project',
          slug: 'test',
          status: 'build',
          type: 'single',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 42 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await ProjectsPage()
      render(page)

      expect(screen.getByText(/42 runs/)).toBeInTheDocument()
    })

    it('displays project status badge', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'Build Project',
          slug: 'build',
          status: 'build',
          type: 'single',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 0 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await ProjectsPage()
      render(page)

      expect(screen.getByText('BUILD')).toBeInTheDocument()
    })

    it('displays repository connection status', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'With Repo',
          slug: 'with-repo',
          status: 'build',
          type: 'single',
          updatedAt: new Date(),
          repoUrl: 'https://github.com/user/repo',
          _count: { runs: 0 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
        {
          id: '2',
          name: 'Without Repo',
          slug: 'without-repo',
          status: 'idle',
          type: 'single',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 0 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await ProjectsPage()
      const { container } = render(page)

      expect(container.textContent).toContain('Connected')
      expect(container.textContent).toContain('Not set')
    })
  })

  describe('Project Links', () => {
    it('creates links to project detail pages', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'My SaaS',
          slug: 'my-saas',
          status: 'build',
          type: 'single',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 0 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await ProjectsPage()
      const { container } = render(page)

      const link = container.querySelector('a[href="/projects/my-saas"]')
      expect(link).toBeInTheDocument()
    })
  })

  describe('Status Colors', () => {
    const statuses = [
      { status: 'idle', expected: true },
      { status: 'research', expected: true },
      { status: 'build', expected: true },
      { status: 'qa', expected: true },
      { status: 'deploy', expected: true },
      { status: 'live', expected: true },
    ]

    statuses.forEach(({ status }) => {
      it(`handles ${status} status`, async () => {
        const mockProjects = [
          {
            id: '1',
            name: `${status} Project`,
            slug: status,
            status,
            type: 'single',
            updatedAt: new Date(),
            repoUrl: null,
            _count: { runs: 0 },
            createdAt: new Date(),
            tenantId: null,
            config: null,
            workdir: null,
          },
        ]

        vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

        const page = await ProjectsPage()
        render(page)

        expect(screen.getByText(status.toUpperCase())).toBeInTheDocument()
      })
    })
  })

  describe('Multiple Projects', () => {
    it('renders multiple project cards', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'Project 1',
          slug: 'p1',
          status: 'build',
          type: 'single',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 1 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
        {
          id: '2',
          name: 'Project 2',
          slug: 'p2',
          status: 'qa',
          type: 'portfolio',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 2 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
        {
          id: '3',
          name: 'Project 3',
          slug: 'p3',
          status: 'live',
          type: 'single',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 3 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await ProjectsPage()
      render(page)

      expect(screen.getByText('Project 1')).toBeInTheDocument()
      expect(screen.getByText('Project 2')).toBeInTheDocument()
      expect(screen.getByText('Project 3')).toBeInTheDocument()
    })
  })

  describe('Layout and Styling', () => {
    it('applies correct spacing classes', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await ProjectsPage()
      const { container } = render(page)

      const mainDiv = container.firstChild
      expect(mainDiv).toHaveClass('space-y-6')
    })

    it('applies correct heading styles', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await ProjectsPage()
      render(page)

      const heading = screen.getByText('Projects')
      expect(heading).toHaveClass('text-3xl', 'font-bold', 'text-base-900')
    })

    it('applies correct button styles', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await ProjectsPage()
      render(page)

      const button = screen.getByText('New Project')
      expect(button).toHaveClass('rounded-xl', 'bg-base-900', 'text-white')
    })

    it('applies hover styles to project cards', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'Test',
          slug: 'test',
          status: 'build',
          type: 'single',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 0 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await ProjectsPage()
      const { container } = render(page)

      const link = container.querySelector('a')
      expect(link).toHaveClass('group', 'hover:shadow-soft-lg', 'hover:border-base-300')
    })
  })

  describe('Empty State', () => {
    it('shows centered empty message when no projects', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await ProjectsPage()
      const { container } = render(page)

      const emptyMessage = screen.getByText('No projects yet. Create your first SaaS project!')
      expect(emptyMessage).toBeInTheDocument()
      expect(emptyMessage).toHaveClass('text-center', 'py-12', 'text-base-600')
    })

    it('does not show empty message when projects exist', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'Test',
          slug: 'test',
          status: 'build',
          type: 'single',
          updatedAt: new Date(),
          repoUrl: null,
          _count: { runs: 0 },
          createdAt: new Date(),
          tenantId: null,
          config: null,
          workdir: null,
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await ProjectsPage()
      render(page)

      expect(screen.queryByText('No projects yet. Create your first SaaS project!')).not.toBeInTheDocument()
    })
  })
})
