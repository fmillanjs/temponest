import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import DashboardPage from '@/app/(dashboard)/dashboard/page'

// Mock the Prisma client
vi.mock('@/lib/db/client', () => ({
  prisma: {
    agent: {
      findMany: vi.fn(),
    },
  },
}))

// Mock the child components
vi.mock('@/components/KpiBar', () => ({
  KpiBar: () => <div data-testid="kpi-bar">KPI Bar</div>,
}))

vi.mock('@/components/AgentStatusCard', () => ({
  AgentStatusCard: ({ name, status, heartbeat, version }: any) => (
    <div data-testid={`agent-card-${name}`}>
      <div data-testid="agent-name">{name}</div>
      <div data-testid="agent-status">{status}</div>
      <div data-testid="agent-heartbeat">{heartbeat}</div>
      <div data-testid="agent-version">{version}</div>
    </div>
  ),
}))

vi.mock('@/components/QuickActions', () => ({
  QuickActions: ({ className }: any) => (
    <div data-testid="quick-actions" className={className}>Quick Actions</div>
  ),
}))

vi.mock('@/components/RecentActivity', () => ({
  RecentActivity: () => <div data-testid="recent-activity">Recent Activity</div>,
}))

describe('DashboardPage', () => {
  let prisma: any

  beforeEach(async () => {
    const imported = await import('@/lib/db/client')
    prisma = imported.prisma
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders dashboard heading', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await DashboardPage()
      render(page)

      expect(screen.getByText('Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Monitor your SaaS building empire')).toBeInTheDocument()
    })

    it('renders all dashboard sections', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await DashboardPage()
      render(page)

      expect(screen.getByTestId('kpi-bar')).toBeInTheDocument()
      expect(screen.getByTestId('quick-actions')).toBeInTheDocument()
      expect(screen.getByTestId('recent-activity')).toBeInTheDocument()
    })

    it('renders agent health section heading', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await DashboardPage()
      render(page)

      expect(screen.getByText('Agent Health')).toBeInTheDocument()
    })
  })

  describe('Agent Display', () => {
    it('displays agent cards when agents exist', async () => {
      const mockAgents = [
        {
          id: '1',
          name: 'Overseer',
          status: 'healthy',
          lastHeartbeat: new Date('2025-11-07T10:00:00Z'),
          version: '1.0.0',
          createdAt: new Date(),
          updatedAt: new Date(),
          tenantId: null,
          config: null,
          metadata: null,
        },
        {
          id: '2',
          name: 'Developer',
          status: 'degraded',
          lastHeartbeat: new Date('2025-11-07T09:50:00Z'),
          version: '1.0.1',
          createdAt: new Date(),
          updatedAt: new Date(),
          tenantId: null,
          config: null,
          metadata: null,
        },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)

      const page = await DashboardPage()
      render(page)

      expect(screen.getByTestId('agent-card-Overseer')).toBeInTheDocument()
      expect(screen.getByTestId('agent-card-Developer')).toBeInTheDocument()
    })

    it('passes correct props to AgentStatusCard', async () => {
      const mockAgents = [
        {
          id: '1',
          name: 'Designer',
          status: 'healthy',
          lastHeartbeat: new Date('2025-11-07T10:00:00Z'),
          version: '2.0.0',
          createdAt: new Date(),
          updatedAt: new Date(),
          tenantId: null,
          config: null,
          metadata: null,
        },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)

      const page = await DashboardPage()
      render(page)

      const card = screen.getByTestId('agent-card-Designer')
      expect(card.querySelector('[data-testid="agent-name"]')).toHaveTextContent('Designer')
      expect(card.querySelector('[data-testid="agent-status"]')).toHaveTextContent('healthy')
      expect(card.querySelector('[data-testid="agent-version"]')).toHaveTextContent('2.0.0')
    })

    it('handles agents with null lastHeartbeat', async () => {
      const mockAgents = [
        {
          id: '1',
          name: 'QA Tester',
          status: 'unhealthy',
          lastHeartbeat: null,
          version: '1.0.0',
          createdAt: new Date(),
          updatedAt: new Date(),
          tenantId: null,
          config: null,
          metadata: null,
        },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)

      const page = await DashboardPage()
      render(page)

      const card = screen.getByTestId('agent-card-QA Tester')
      expect(card.querySelector('[data-testid="agent-heartbeat"]')).toHaveTextContent('never')
    })

    it('renders no agents when database is empty', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await DashboardPage()
      render(page)

      expect(screen.queryByTestId(/agent-card-/)).not.toBeInTheDocument()
    })
  })

  describe('Data Fetching', () => {
    it('fetches agents ordered by name ascending', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      await DashboardPage()

      expect(prisma.agent.findMany).toHaveBeenCalledWith({
        orderBy: { name: 'asc' },
      })
    })

    it('fetches agents only once', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      await DashboardPage()

      expect(prisma.agent.findMany).toHaveBeenCalledTimes(1)
    })
  })

  describe('Grid Layout', () => {
    it('applies responsive grid classes to agent cards container', async () => {
      const mockAgents = [
        {
          id: '1',
          name: 'Agent1',
          status: 'healthy',
          lastHeartbeat: new Date(),
          version: '1.0.0',
          createdAt: new Date(),
          updatedAt: new Date(),
          tenantId: null,
          config: null,
          metadata: null,
        },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)

      const page = await DashboardPage()
      const { container } = render(page)

      const gridContainer = container.querySelector('.grid')
      expect(gridContainer).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'xl:grid-cols-3')
    })

    it('applies correct grid layout to bottom section', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await DashboardPage()
      const { container } = render(page)

      // Find the grid containing QuickActions and RecentActivity
      const sections = container.querySelectorAll('section')
      const bottomSection = sections[sections.length - 1]
      expect(bottomSection).toHaveClass('grid', 'lg:grid-cols-3')
    })

    it('applies correct column span to QuickActions', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await DashboardPage()
      render(page)

      const quickActions = screen.getByTestId('quick-actions')
      expect(quickActions).toHaveClass('lg:col-span-2')
    })
  })

  describe('Styling', () => {
    it('applies correct spacing classes', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await DashboardPage()
      const { container } = render(page)

      const mainDiv = container.firstChild
      expect(mainDiv).toHaveClass('space-y-6')
    })

    it('applies correct heading styles', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await DashboardPage()
      render(page)

      const heading = screen.getByText('Dashboard')
      expect(heading).toHaveClass('text-3xl', 'font-bold', 'text-base-900')
    })

    it('applies correct description styles', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await DashboardPage()
      render(page)

      const description = screen.getByText('Monitor your SaaS building empire')
      expect(description).toHaveClass('mt-1', 'text-base-600')
    })
  })

  describe('Multiple Agents', () => {
    it('renders multiple agents correctly', async () => {
      const mockAgents = [
        {
          id: '1',
          name: 'Agent A',
          status: 'healthy',
          lastHeartbeat: new Date(),
          version: '1.0.0',
          createdAt: new Date(),
          updatedAt: new Date(),
          tenantId: null,
          config: null,
          metadata: null,
        },
        {
          id: '2',
          name: 'Agent B',
          status: 'degraded',
          lastHeartbeat: new Date(),
          version: '1.1.0',
          createdAt: new Date(),
          updatedAt: new Date(),
          tenantId: null,
          config: null,
          metadata: null,
        },
        {
          id: '3',
          name: 'Agent C',
          status: 'unhealthy',
          lastHeartbeat: null,
          version: '0.9.0',
          createdAt: new Date(),
          updatedAt: new Date(),
          tenantId: null,
          config: null,
          metadata: null,
        },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)

      const page = await DashboardPage()
      render(page)

      expect(screen.getByTestId('agent-card-Agent A')).toBeInTheDocument()
      expect(screen.getByTestId('agent-card-Agent B')).toBeInTheDocument()
      expect(screen.getByTestId('agent-card-Agent C')).toBeInTheDocument()
    })
  })
})
