import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KpiBar } from '@/components/KpiBar'

// Mock the Prisma client
vi.mock('@/lib/db/client', () => ({
  prisma: {
    project: {
      count: vi.fn(),
    },
    run: {
      count: vi.fn(),
    },
    agent: {
      count: vi.fn(),
    },
  },
}))

describe('KpiBar Component', () => {
  let prisma: any

  beforeEach(async () => {
    const imported = await import('@/lib/db/client')
    prisma = imported.prisma
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders all 5 KPI cards', async () => {
      // Setup mock data
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10) // totalProjects
        .mockResolvedValueOnce(5)  // activeProjects
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25) // runsToday
        .mockResolvedValueOnce(3)  // queueDepth
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)  // healthyAgents
        .mockResolvedValueOnce(10) // totalAgents

      const component = await KpiBar()
      render(component)

      expect(screen.getByText('Active Projects')).toBeInTheDocument()
      expect(screen.getByText('Build Runs Today')).toBeInTheDocument()
      expect(screen.getByText('Agent Uptime')).toBeInTheDocument()
      expect(screen.getByText('Queue Depth')).toBeInTheDocument()
      expect(screen.getByText('Total Projects')).toBeInTheDocument()
    })

    it('displays correct KPI values', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      const component = await KpiBar()
      render(component)

      expect(screen.getByText('5')).toBeInTheDocument() // Active Projects
      expect(screen.getByText('25')).toBeInTheDocument() // Build Runs Today
      expect(screen.getByText('80.0%')).toBeInTheDocument() // Agent Uptime (8/10 * 100)
      expect(screen.getByText('3')).toBeInTheDocument() // Queue Depth
      expect(screen.getByText('10')).toBeInTheDocument() // Total Projects
    })

    it('renders icons for all KPIs', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      const component = await KpiBar()
      const { container } = render(component)

      const svgs = container.querySelectorAll('svg')
      expect(svgs).toHaveLength(5)
    })
  })

  describe('Database Queries', () => {
    it('queries total projects count', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      await KpiBar()

      expect(prisma.project.count).toHaveBeenCalledWith()
      expect(prisma.project.count).toHaveBeenCalledTimes(2)
    })

    it('queries active projects with correct filter', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      await KpiBar()

      const calls = vi.mocked(prisma.project.count).mock.calls
      expect(calls[1][0]).toEqual({
        where: { status: { notIn: ['idle'] } }
      })
    })

    it('queries runs today with date filter', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      await KpiBar()

      const calls = vi.mocked(prisma.run.count).mock.calls
      expect(calls[0][0]).toHaveProperty('where')
      expect(calls[0][0].where).toHaveProperty('createdAt')
      expect(calls[0][0].where.createdAt).toHaveProperty('gte')
    })

    it('queries pending runs for queue depth', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      await KpiBar()

      const calls = vi.mocked(prisma.run.count).mock.calls
      expect(calls[1][0]).toEqual({
        where: { status: 'pending' }
      })
    })

    it('queries healthy agents count', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      await KpiBar()

      const calls = vi.mocked(prisma.agent.count).mock.calls
      expect(calls[0][0]).toEqual({
        where: { status: 'healthy' }
      })
    })

    it('queries total agents count', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      await KpiBar()

      expect(prisma.agent.count).toHaveBeenCalledWith()
      expect(prisma.agent.count).toHaveBeenCalledTimes(2)
    })
  })

  describe('Agent Uptime Calculation', () => {
    it('calculates uptime percentage correctly with healthy agents', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(7)  // healthyAgents
        .mockResolvedValueOnce(10) // totalAgents

      const component = await KpiBar()
      render(component)

      expect(screen.getByText('70.0%')).toBeInTheDocument()
    })

    it('shows 100% uptime when all agents are healthy', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(10) // healthyAgents
        .mockResolvedValueOnce(10) // totalAgents

      const component = await KpiBar()
      render(component)

      expect(screen.getByText('100.0%')).toBeInTheDocument()
    })

    it('shows 0% uptime when no agents are healthy', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(0)  // healthyAgents
        .mockResolvedValueOnce(10) // totalAgents

      const component = await KpiBar()
      render(component)

      expect(screen.getByText('0.0%')).toBeInTheDocument()
    })

    it('shows 0.0% uptime when no agents exist', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(0) // healthyAgents
        .mockResolvedValueOnce(0) // totalAgents

      const component = await KpiBar()
      render(component)

      expect(screen.getByText('0.0%')).toBeInTheDocument()
    })
  })

  describe('Zero Values', () => {
    it('handles zero active projects', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(0)  // activeProjects
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(0)
        .mockResolvedValueOnce(0)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(0)
        .mockResolvedValueOnce(0)

      const component = await KpiBar()
      render(component)

      expect(screen.getByText('Active Projects')).toBeInTheDocument()
      // Check that the "0" value appears somewhere in the component
      const zeroValues = screen.getAllByText('0')
      expect(zeroValues.length).toBeGreaterThan(0)
    })

    it('handles zero runs today', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(0)  // runsToday
        .mockResolvedValueOnce(0)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(0)
        .mockResolvedValueOnce(0)

      const component = await KpiBar()
      render(component)

      expect(screen.getByText('Build Runs Today')).toBeInTheDocument()
      // Check that the "0" value appears for runs today
      const zeroValues = screen.getAllByText('0')
      expect(zeroValues.length).toBeGreaterThan(0)
    })
  })

  describe('Styling', () => {
    it('uses grid layout for KPIs', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      const component = await KpiBar()
      const { container } = render(component)

      const grid = container.firstChild
      expect(grid).toHaveClass('grid')
      expect(grid).toHaveClass('lg:grid-cols-5')
    })

    it('KPI cards have rounded borders and shadows', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      const component = await KpiBar()
      const { container } = render(component)

      const cards = container.querySelectorAll('.rounded-2xl')
      expect(cards.length).toBeGreaterThan(0)

      const shadowCards = container.querySelectorAll('.shadow-soft')
      expect(shadowCards.length).toBeGreaterThan(0)
    })

    it('all KPIs show positive trend styling', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      const component = await KpiBar()
      const { container } = render(component)

      const successElements = container.querySelectorAll('.text-accent-success')
      expect(successElements.length).toBeGreaterThan(0)
    })
  })

  describe('Accessibility', () => {
    it('KPI values are readable as text', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      const component = await KpiBar()
      render(component)

      expect(screen.getByText('5')).toBeVisible()
      expect(screen.getByText('25')).toBeVisible()
      expect(screen.getByText('80.0%')).toBeVisible()
    })

    it('KPI labels are descriptive', async () => {
      vi.mocked(prisma.project.count)
        .mockResolvedValueOnce(10)
        .mockResolvedValueOnce(5)
      vi.mocked(prisma.run.count)
        .mockResolvedValueOnce(25)
        .mockResolvedValueOnce(3)
      vi.mocked(prisma.agent.count)
        .mockResolvedValueOnce(8)
        .mockResolvedValueOnce(10)

      const component = await KpiBar()
      render(component)

      const labels = [
        'Active Projects',
        'Build Runs Today',
        'Agent Uptime',
        'Queue Depth',
        'Total Projects'
      ]

      labels.forEach(label => {
        expect(screen.getByText(label)).toBeVisible()
      })
    })
  })
})
