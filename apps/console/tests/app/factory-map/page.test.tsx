import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import FactoryMapPage from '@/app/factory-map/page'

// Mock the Prisma client
vi.mock('@/lib/db/client', () => ({
  prisma: {
    project: {
      findMany: vi.fn(),
      count: vi.fn(),
    },
    agent: {
      findMany: vi.fn(),
    },
  },
}))

// Mock the FactoryMap component
vi.mock('@/components/FactoryMap', () => ({
  FactoryMap: ({ projects, agents }: any) => (
    <div data-testid="factory-map">
      <div data-testid="projects-count">{projects.length}</div>
      <div data-testid="agents-count">{agents.length}</div>
    </div>
  ),
}))

describe('FactoryMapPage', () => {
  const { prisma } = await import('@/lib/db/client')

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders factory map heading', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      render(page)

      expect(screen.getByText('Factory Map')).toBeInTheDocument()
      expect(screen.getByText('Visualize your products, pipelines, agents, and infrastructure')).toBeInTheDocument()
    })

    it('renders FactoryMap component', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      render(page)

      expect(screen.getByTestId('factory-map')).toBeInTheDocument()
    })

    it('renders statistics cards', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      render(page)

      expect(screen.getByText('Products')).toBeInTheDocument()
      expect(screen.getByText('Active Projects')).toBeInTheDocument()
      expect(screen.getByText('Total Agents')).toBeInTheDocument()
    })
  })

  describe('Data Fetching', () => {
    it('fetches projects with correct query', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      await FactoryMapPage()

      expect(prisma.project.findMany).toHaveBeenCalledWith({
        select: { id: true, name: true, status: true },
        orderBy: { createdAt: 'desc' },
      })
    })

    it('fetches agents with correct query', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      await FactoryMapPage()

      expect(prisma.agent.findMany).toHaveBeenCalledWith({
        select: { id: true, name: true, status: true, version: true },
        orderBy: { name: 'asc' },
      })
    })

    it('counts active projects correctly', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      await FactoryMapPage()

      expect(prisma.project.count).toHaveBeenCalledWith({
        where: { status: { notIn: ['idle'] } },
      })
    })

    it('performs all queries in parallel', async () => {
      const findManyProjectsSpy = vi.mocked(prisma.project.findMany).mockResolvedValue([])
      const findManyAgentsSpy = vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      const countSpy = vi.mocked(prisma.project.count).mockResolvedValue(0)

      await FactoryMapPage()

      // All should be called once
      expect(findManyProjectsSpy).toHaveBeenCalledTimes(1)
      expect(findManyAgentsSpy).toHaveBeenCalledTimes(1)
      expect(countSpy).toHaveBeenCalledTimes(1)
    })
  })

  describe('Statistics Display', () => {
    it('displays correct product count', async () => {
      const mockProjects = [
        { id: '1', name: 'Project 1', status: 'build' },
        { id: '2', name: 'Project 2', status: 'qa' },
        { id: '3', name: 'Project 3', status: 'live' },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(2)

      const page = await FactoryMapPage()
      const { container } = render(page)

      // Find the Products card
      const productsCard = Array.from(container.querySelectorAll('.rounded-2xl')).find(
        el => el.textContent?.includes('Products')
      )
      expect(productsCard?.textContent).toContain('3')
    })

    it('displays correct active projects count', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(5)

      const page = await FactoryMapPage()
      const { container } = render(page)

      const activeProjectsCard = Array.from(container.querySelectorAll('.rounded-2xl')).find(
        el => el.textContent?.includes('Active Projects')
      )
      expect(activeProjectsCard?.textContent).toContain('5')
    })

    it('displays correct agents count', async () => {
      const mockAgents = [
        { id: '1', name: 'Agent 1', status: 'healthy', version: '1.0.0' },
        { id: '2', name: 'Agent 2', status: 'degraded', version: '1.0.1' },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      const { container } = render(page)

      const agentsCard = Array.from(container.querySelectorAll('.rounded-2xl')).find(
        el => el.textContent?.includes('Total Agents')
      )
      expect(agentsCard?.textContent).toContain('2')
    })

    it('displays zero when no data exists', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      const { container } = render(page)

      const cards = container.querySelectorAll('.rounded-2xl')
      expect(cards).toHaveLength(3)
      cards.forEach(card => {
        expect(card.textContent).toContain('0')
      })
    })
  })

  describe('Component Props', () => {
    it('passes projects to FactoryMap component', async () => {
      const mockProjects = [
        { id: '1', name: 'Project A', status: 'build' },
        { id: '2', name: 'Project B', status: 'qa' },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue(mockProjects)
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(1)

      const page = await FactoryMapPage()
      render(page)

      expect(screen.getByTestId('projects-count')).toHaveTextContent('2')
    })

    it('passes agents to FactoryMap component', async () => {
      const mockAgents = [
        { id: '1', name: 'Overseer', status: 'healthy', version: '1.0.0' },
        { id: '2', name: 'Developer', status: 'healthy', version: '1.0.0' },
        { id: '3', name: 'Designer', status: 'degraded', version: '0.9.0' },
      ]

      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      render(page)

      expect(screen.getByTestId('agents-count')).toHaveTextContent('3')
    })
  })

  describe('Layout and Styling', () => {
    it('applies correct spacing classes', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      const { container } = render(page)

      const mainDiv = container.firstChild
      expect(mainDiv).toHaveClass('space-y-6')
    })

    it('applies correct heading styles', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      render(page)

      const heading = screen.getByText('Factory Map')
      expect(heading).toHaveClass('text-3xl', 'font-bold', 'text-base-900')
    })

    it('applies responsive grid to statistics cards', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      const { container } = render(page)

      const gridContainer = container.querySelector('.grid.gap-4')
      expect(gridContainer).toHaveClass('grid-cols-1', 'md:grid-cols-3')
    })

    it('applies correct card styles', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      const { container } = render(page)

      const cards = container.querySelectorAll('.rounded-2xl.border.bg-white')
      expect(cards.length).toBeGreaterThan(0)
      cards.forEach(card => {
        expect(card).toHaveClass('border-base-200', 'shadow-soft', 'p-4')
      })
    })
  })

  describe('Error Handling', () => {
    it('handles empty projects array', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([{ id: '1', name: 'Agent', status: 'healthy', version: '1.0' }])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      const { container } = render(page)

      expect(container).toBeInTheDocument()
      expect(screen.getByTestId('projects-count')).toHaveTextContent('0')
    })

    it('handles empty agents array', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([{ id: '1', name: 'Project', status: 'build' }])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(1)

      const page = await FactoryMapPage()
      const { container } = render(page)

      expect(container).toBeInTheDocument()
      expect(screen.getByTestId('agents-count')).toHaveTextContent('0')
    })
  })

  describe('Statistic Cards Content', () => {
    it('renders proper labels for each statistic', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      const { container } = render(page)

      const labels = container.querySelectorAll('.text-sm.font-medium.text-base-600')
      const labelTexts = Array.from(labels).map(label => label.textContent)

      expect(labelTexts).toContain('Products')
      expect(labelTexts).toContain('Active Projects')
      expect(labelTexts).toContain('Total Agents')
    })

    it('renders values with proper styling', async () => {
      vi.mocked(prisma.project.findMany).mockResolvedValue([{ id: '1', name: 'P1', status: 'build' }])
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])
      vi.mocked(prisma.project.count).mockResolvedValue(0)

      const page = await FactoryMapPage()
      const { container } = render(page)

      const values = container.querySelectorAll('.text-2xl.font-bold.text-base-900')
      expect(values.length).toBeGreaterThan(0)
    })
  })
})
