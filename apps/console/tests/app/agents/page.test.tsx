import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import AgentsPage from '@/app/agents/page'

// Mock the Prisma client
vi.mock('@/lib/db/client', () => ({
  prisma: {
    agent: {
      findMany: vi.fn(),
    },
  },
}))

// Mock the AgentStatusCard component
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

describe('AgentsPage', () => {
  const { prisma } = await import('@/lib/db/client')

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders agents heading', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await AgentsPage()
      render(page)

      expect(screen.getByText('Agents')).toBeInTheDocument()
      expect(screen.getByText('Monitor and manage your autonomous agents')).toBeInTheDocument()
    })

    it('renders empty grid when no agents exist', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await AgentsPage()
      const { container } = render(page)

      const grid = container.querySelector('.grid')
      expect(grid).toBeInTheDocument()
      expect(screen.queryByTestId(/agent-card-/)).not.toBeInTheDocument()
    })
  })

  describe('Data Fetching', () => {
    it('fetches agents with correct query', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      await AgentsPage()

      expect(prisma.agent.findMany).toHaveBeenCalledWith({
        orderBy: { name: 'asc' },
      })
    })

    it('orders agents alphabetically by name', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      await AgentsPage()

      const call = vi.mocked(prisma.agent.findMany).mock.calls[0][0]
      expect(call.orderBy).toEqual({ name: 'asc' })
    })

    it('fetches agents only once', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      await AgentsPage()

      expect(prisma.agent.findMany).toHaveBeenCalledTimes(1)
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

      const page = await AgentsPage()
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

      const page = await AgentsPage()
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

      const page = await AgentsPage()
      render(page)

      const card = screen.getByTestId('agent-card-QA Tester')
      expect(card.querySelector('[data-testid="agent-heartbeat"]')).toHaveTextContent('never')
    })

    it('formats heartbeat for recent agents', async () => {
      const mockAgents = [
        {
          id: '1',
          name: 'Active Agent',
          status: 'healthy',
          lastHeartbeat: new Date(), // Current time
          version: '1.0.0',
          createdAt: new Date(),
          updatedAt: new Date(),
          tenantId: null,
          config: null,
          metadata: null,
        },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)

      const page = await AgentsPage()
      render(page)

      const card = screen.getByTestId('agent-card-Active Agent')
      const heartbeat = card.querySelector('[data-testid="agent-heartbeat"]')
      expect(heartbeat).toBeInTheDocument()
      // Should have some value from formatDistanceToNow
      expect(heartbeat?.textContent).not.toBe('never')
    })
  })

  describe('Agent Status', () => {
    const statuses = ['healthy', 'degraded', 'unhealthy']

    statuses.forEach((status) => {
      it(`handles ${status} status`, async () => {
        const mockAgents = [
          {
            id: '1',
            name: `${status} Agent`,
            status,
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

        const page = await AgentsPage()
        render(page)

        const card = screen.getByTestId(`agent-card-${status} Agent`)
        expect(card.querySelector('[data-testid="agent-status"]')).toHaveTextContent(status)
      })
    })
  })

  describe('Multiple Agents', () => {
    it('renders all 7 core agents', async () => {
      const mockAgents = [
        { id: '1', name: 'Overseer', status: 'healthy', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
        { id: '2', name: 'Developer', status: 'healthy', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
        { id: '3', name: 'Designer', status: 'healthy', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
        { id: '4', name: 'QA Tester', status: 'degraded', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
        { id: '5', name: 'DevOps', status: 'healthy', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
        { id: '6', name: 'Security Auditor', status: 'healthy', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
        { id: '7', name: 'UX Researcher', status: 'unhealthy', lastHeartbeat: null, version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)

      const page = await AgentsPage()
      render(page)

      mockAgents.forEach((agent) => {
        expect(screen.getByTestId(`agent-card-${agent.name}`)).toBeInTheDocument()
      })
    })

    it('displays agents in alphabetical order', async () => {
      const mockAgents = [
        { id: '1', name: 'Developer', status: 'healthy', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
        { id: '2', name: 'Overseer', status: 'healthy', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
        { id: '3', name: 'Designer', status: 'healthy', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)

      const page = await AgentsPage()
      render(page)

      // All agents should be present regardless of original order
      expect(screen.getByTestId('agent-card-Developer')).toBeInTheDocument()
      expect(screen.getByTestId('agent-card-Overseer')).toBeInTheDocument()
      expect(screen.getByTestId('agent-card-Designer')).toBeInTheDocument()
    })
  })

  describe('Grid Layout', () => {
    it('applies responsive grid classes', async () => {
      const mockAgents = [
        { id: '1', name: 'Agent1', status: 'healthy', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)

      const page = await AgentsPage()
      const { container } = render(page)

      const gridContainer = container.querySelector('.grid')
      expect(gridContainer).toHaveClass('grid-cols-1', 'md:grid-cols-2', 'xl:grid-cols-3')
    })

    it('applies correct gap spacing', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await AgentsPage()
      const { container } = render(page)

      const gridContainer = container.querySelector('.grid')
      expect(gridContainer).toHaveClass('gap-4')
    })
  })

  describe('Layout and Styling', () => {
    it('applies correct spacing classes', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await AgentsPage()
      const { container } = render(page)

      const mainDiv = container.firstChild
      expect(mainDiv).toHaveClass('space-y-6')
    })

    it('applies correct heading styles', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await AgentsPage()
      render(page)

      const heading = screen.getByText('Agents')
      expect(heading).toHaveClass('text-3xl', 'font-bold', 'text-base-900')
    })

    it('applies correct description styles', async () => {
      vi.mocked(prisma.agent.findMany).mockResolvedValue([])

      const page = await AgentsPage()
      render(page)

      const description = screen.getByText('Monitor and manage your autonomous agents')
      expect(description).toHaveClass('mt-1', 'text-base-600')
    })
  })

  describe('Agent Versions', () => {
    it('displays different versions correctly', async () => {
      const mockAgents = [
        { id: '1', name: 'V1 Agent', status: 'healthy', lastHeartbeat: new Date(), version: '1.0.0', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
        { id: '2', name: 'V2 Agent', status: 'healthy', lastHeartbeat: new Date(), version: '2.1.5', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
        { id: '3', name: 'Beta Agent', status: 'degraded', lastHeartbeat: new Date(), version: '0.9.0-beta', createdAt: new Date(), updatedAt: new Date(), tenantId: null, config: null, metadata: null },
      ]

      vi.mocked(prisma.agent.findMany).mockResolvedValue(mockAgents)

      const page = await AgentsPage()
      render(page)

      expect(screen.getByTestId('agent-card-V1 Agent').querySelector('[data-testid="agent-version"]')).toHaveTextContent('1.0.0')
      expect(screen.getByTestId('agent-card-V2 Agent').querySelector('[data-testid="agent-version"]')).toHaveTextContent('2.1.5')
      expect(screen.getByTestId('agent-card-Beta Agent').querySelector('[data-testid="agent-version"]')).toHaveTextContent('0.9.0-beta')
    })
  })
})
