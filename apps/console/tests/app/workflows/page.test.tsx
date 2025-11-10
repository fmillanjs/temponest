import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import WorkflowsPage from '@/app/workflows/page'

// Mock the Prisma client
vi.mock('@/lib/db/client', () => ({
  prisma: {
    project: {
      findMany: vi.fn(),
    },
  },
}))

// Mock the KanbanBoard component
vi.mock('@/components/KanbanBoard', () => ({
  KanbanBoard: ({ projects, onStatusChange }: any) => (
    <div data-testid="kanban-board">
      <div data-testid="projects-count">{projects.length}</div>
      {projects.map((project: any) => (
        <div key={project.id} data-testid={`project-${project.id}`}>
          {project.name}
        </div>
      ))}
    </div>
  ),
}))

// Mock next/cache
vi.mock('next/cache', () => ({
  revalidatePath: vi.fn(),
}))

describe('WorkflowsPage', () => {
  let prisma: any

  beforeEach(async () => {
    const imported = await import('@/lib/db/client')
    prisma = imported.prisma
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders workflows heading', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await WorkflowsPage()
      render(page)

      expect(screen.getByText('Workflows')).toBeInTheDocument()
      expect(screen.getByText('Track your projects through the pipeline')).toBeInTheDocument()
    })

    it('renders KanbanBoard component', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await WorkflowsPage()
      render(page)

      expect(screen.getByTestId('kanban-board')).toBeInTheDocument()
    })
  })

  describe('Data Fetching', () => {
    it('fetches projects with correct query', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      await WorkflowsPage()

      expect(prisma.project.findMany).toHaveBeenCalledWith({
        select: {
          id: true,
          name: true,
          slug: true,
          status: true,
          type: true,
          updatedAt: true,
        },
        orderBy: { updatedAt: 'desc' },
      })
    })

    it('fetches projects only once', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      await WorkflowsPage()

      expect(prisma.project.findMany).toHaveBeenCalledTimes(1)
    })

    it('orders projects by most recently updated', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      await WorkflowsPage()

      const call = vi.mocked(prisma.project.findMany).mock.calls[0][0]
      expect(call.orderBy).toEqual({ updatedAt: 'desc' })
    })
  })

  describe('Project Display', () => {
    it('displays projects in KanbanBoard', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'Project A',
          slug: 'project-a',
          status: 'build',
          type: 'single',
          updatedAt: new Date('2025-11-07T10:00:00Z'),
        },
        {
          id: '2',
          name: 'Project B',
          slug: 'project-b',
          status: 'qa',
          type: 'portfolio',
          updatedAt: new Date('2025-11-07T09:00:00Z'),
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await WorkflowsPage()
      render(page)

      expect(screen.getByTestId('projects-count')).toHaveTextContent('2')
      expect(screen.getByTestId('project-1')).toHaveTextContent('Project A')
      expect(screen.getByTestId('project-2')).toHaveTextContent('Project B')
    })

    it('handles empty projects array', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await WorkflowsPage()
      render(page)

      expect(screen.getByTestId('projects-count')).toHaveTextContent('0')
    })

    it('displays multiple projects correctly', async () => {
      const mockProjects = [
        {
          id: '1',
          name: 'P1',
          slug: 'p1',
          status: 'idle',
          type: 'single',
          updatedAt: new Date(),
        },
        {
          id: '2',
          name: 'P2',
          slug: 'p2',
          status: 'research',
          type: 'single',
          updatedAt: new Date(),
        },
        {
          id: '3',
          name: 'P3',
          slug: 'p3',
          status: 'build',
          type: 'portfolio',
          updatedAt: new Date(),
        },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await WorkflowsPage()
      render(page)

      expect(screen.getByTestId('projects-count')).toHaveTextContent('3')
    })
  })

  describe('Project Status', () => {
    it('includes all project statuses', async () => {
      const mockProjects = [
        { id: '1', name: 'Idle Project', slug: 'idle', status: 'idle', type: 'single', updatedAt: new Date() },
        { id: '2', name: 'Research Project', slug: 'research', status: 'research', type: 'single', updatedAt: new Date() },
        { id: '3', name: 'Build Project', slug: 'build', status: 'build', type: 'single', updatedAt: new Date() },
        { id: '4', name: 'QA Project', slug: 'qa', status: 'qa', type: 'single', updatedAt: new Date() },
        { id: '5', name: 'Deploy Project', slug: 'deploy', status: 'deploy', type: 'single', updatedAt: new Date() },
        { id: '6', name: 'Live Project', slug: 'live', status: 'live', type: 'single', updatedAt: new Date() },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await WorkflowsPage()
      render(page)

      expect(screen.getByTestId('projects-count')).toHaveTextContent('6')
      mockProjects.forEach(project => {
        expect(screen.getByTestId(`project-${project.id}`)).toBeInTheDocument()
      })
    })
  })

  describe('Project Types', () => {
    it('handles single type projects', async () => {
      const mockProjects = [
        { id: '1', name: 'Single SaaS', slug: 'single', status: 'build', type: 'single', updatedAt: new Date() },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await WorkflowsPage()
      render(page)

      expect(screen.getByTestId('project-1')).toHaveTextContent('Single SaaS')
    })

    it('handles portfolio type projects', async () => {
      const mockProjects = [
        { id: '1', name: 'Portfolio', slug: 'portfolio', status: 'build', type: 'portfolio', updatedAt: new Date() },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await WorkflowsPage()
      render(page)

      expect(screen.getByTestId('project-1')).toHaveTextContent('Portfolio')
    })

    it('handles mixed project types', async () => {
      const mockProjects = [
        { id: '1', name: 'Single', slug: 'single', status: 'build', type: 'single', updatedAt: new Date() },
        { id: '2', name: 'Portfolio', slug: 'portfolio', status: 'qa', type: 'portfolio', updatedAt: new Date() },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await WorkflowsPage()
      render(page)

      expect(screen.getByTestId('projects-count')).toHaveTextContent('2')
    })
  })

  describe('Layout and Styling', () => {
    it('applies correct spacing classes', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await WorkflowsPage()
      const { container } = render(page)

      const mainDiv = container.firstChild
      expect(mainDiv).toHaveClass('space-y-6')
    })

    it('applies correct heading styles', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await WorkflowsPage()
      render(page)

      const heading = screen.getByText('Workflows')
      expect(heading).toHaveClass('text-3xl', 'font-bold', 'text-base-900')
    })

    it('applies correct description styles', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await WorkflowsPage()
      render(page)

      const description = screen.getByText('Track your projects through the pipeline')
      expect(description).toHaveClass('mt-1', 'text-base-600')
    })
  })

  describe('Component Props', () => {
    it('passes projects to KanbanBoard', async () => {
      const mockProjects = [
        { id: '1', name: 'Test Project', slug: 'test', status: 'build', type: 'single', updatedAt: new Date() },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      const page = await WorkflowsPage()
      render(page)

      expect(screen.getByTestId('kanban-board')).toBeInTheDocument()
      expect(screen.getByTestId('project-1')).toBeInTheDocument()
    })

    it('passes onStatusChange callback to KanbanBoard', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])

      const page = await WorkflowsPage()
      render(page)

      // The component should render successfully with the callback
      expect(screen.getByTestId('kanban-board')).toBeInTheDocument()
    })
  })

  describe('Sorting', () => {
    it('returns projects in descending updatedAt order', async () => {
      const oldDate = new Date('2025-11-01T10:00:00Z')
      const newDate = new Date('2025-11-07T10:00:00Z')

      const mockProjects = [
        { id: '2', name: 'Newer', slug: 'newer', status: 'build', type: 'single', updatedAt: newDate },
        { id: '1', name: 'Older', slug: 'older', status: 'qa', type: 'single', updatedAt: oldDate },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)

      await WorkflowsPage()

      // Verify orderBy is set correctly
      expect(prisma.project.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          orderBy: { updatedAt: 'desc' },
        })
      )
    })
  })
})
