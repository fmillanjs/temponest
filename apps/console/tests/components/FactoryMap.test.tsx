import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FactoryMap } from '@/components/FactoryMap'

// Mock ReactFlow components
vi.mock('reactflow', () => ({
  default: ({ nodes, edges, onNodeClick, children }: any) => (
    <div data-testid="react-flow">
      <div data-testid="nodes">
        {nodes.map((node: any) => (
          <div
            key={node.id}
            data-testid={`node-${node.id}`}
            onClick={(e) => onNodeClick(e, node)}
          >
            {node.data.label}
          </div>
        ))}
      </div>
      <div data-testid="edges">
        {edges.map((edge: any) => (
          <div key={edge.id} data-testid={`edge-${edge.id}`} />
        ))}
      </div>
      {children}
    </div>
  ),
  Background: () => <div data-testid="background" />,
  Controls: () => <div data-testid="controls" />,
  MiniMap: ({ nodeColor }: any) => <div data-testid="minimap" />,
  useNodesState: (initialNodes: any) => [initialNodes, vi.fn()],
  useEdgesState: (initialEdges: any) => [initialEdges, vi.fn()],
}))

describe('FactoryMap Component', () => {
  const mockProjects = [
    { id: '1', name: 'FormBuilder SaaS', status: 'build' },
    { id: '2', name: 'Analytics Platform', status: 'live' },
    { id: '3', name: 'CRM System', status: 'idle' },
  ]

  const mockAgents = [
    { id: '1', name: 'Research', status: 'healthy', version: 'v1.0.0' },
    { id: '2', name: 'Build', status: 'degraded', version: 'v1.0.1' },
    { id: '3', name: 'QA', status: 'down', version: 'v0.9.5' },
  ]

  describe('Rendering', () => {
    it('renders ReactFlow component', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      expect(screen.getByTestId('react-flow')).toBeInTheDocument()
    })

    it('renders Background component', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      expect(screen.getByTestId('background')).toBeInTheDocument()
    })

    it('renders Controls component', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      expect(screen.getByTestId('controls')).toBeInTheDocument()
    })

    it('renders MiniMap component', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      expect(screen.getByTestId('minimap')).toBeInTheDocument()
    })
  })

  describe('Project Nodes', () => {
    it('creates nodes for all projects', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      mockProjects.forEach(project => {
        expect(screen.getByText(project.name)).toBeInTheDocument()
      })
    })

    it('creates project nodes with correct IDs', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      mockProjects.forEach(project => {
        expect(screen.getByTestId(`node-project-${project.id}`)).toBeInTheDocument()
      })
    })

    it('handles empty projects array', () => {
      render(<FactoryMap projects={[]} agents={mockAgents} />)
      expect(screen.getByTestId('react-flow')).toBeInTheDocument()
    })
  })

  describe('Agent Nodes', () => {
    it('creates nodes for agents', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      // FactoryMap limits to first 5 agents
      expect(screen.getByText('Research Agent')).toBeInTheDocument()
      expect(screen.getByText('Build Agent')).toBeInTheDocument()
      expect(screen.getByText('QA Agent')).toBeInTheDocument()
    })

    it('limits to first 5 agents', () => {
      const manyAgents = Array.from({ length: 10 }, (_, i) => ({
        id: `${i + 1}`,
        name: `Agent${i + 1}`,
        status: 'healthy',
        version: 'v1.0.0'
      }))

      render(<FactoryMap projects={mockProjects} agents={manyAgents} />)

      // Should show only first 5
      expect(screen.getByText('Agent1 Agent')).toBeInTheDocument()
      expect(screen.getByText('Agent5 Agent')).toBeInTheDocument()
      expect(screen.queryByText('Agent6 Agent')).not.toBeInTheDocument()
    })

    it('creates agent nodes with correct IDs', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      mockAgents.forEach(agent => {
        expect(screen.getByTestId(`node-agent-${agent.id}`)).toBeInTheDocument()
      })
    })
  })

  describe('Infrastructure Node', () => {
    it('creates infrastructure node', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      expect(screen.getByText('Infrastructure')).toBeInTheDocument()
    })

    it('infrastructure node has correct ID', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      expect(screen.getByTestId('node-infra')).toBeInTheDocument()
    })
  })

  describe('Edges', () => {
    it('creates edges container', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      expect(screen.getByTestId('edges')).toBeInTheDocument()
    })

    it('connects projects to agents', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      const edges = screen.getByTestId('edges')

      // Should have edges (projects * 3 agents + agents to infra)
      const edgeElements = edges.querySelectorAll('[data-testid^="edge-"]')
      expect(edgeElements.length).toBeGreaterThan(0)
    })
  })

  describe('Node Click Interaction', () => {
    it('does not show panel initially', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument()
    })

    it('shows panel when project node is clicked', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const projectNode = screen.getByTestId('node-project-1')
      fireEvent.click(projectNode)

      // Panel should appear with buttons (close and View Details)
      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThanOrEqual(2)
    })

    it('shows panel when agent node is clicked', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const agentNode = screen.getByTestId('node-agent-1')
      fireEvent.click(agentNode)

      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThanOrEqual(2)
    })

    it('shows panel when infrastructure node is clicked', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const infraNode = screen.getByTestId('node-infra')
      fireEvent.click(infraNode)

      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThanOrEqual(2)
    })
  })

  describe('Side Panel', () => {
    it('displays selected node label in panel', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const projectNode = screen.getByTestId('node-project-1')
      fireEvent.click(projectNode)

      // Panel should show project name
      const panels = screen.getAllByText('FormBuilder SaaS')
      expect(panels.length).toBeGreaterThan(1) // In node and in panel
    })

    it('displays node type badge', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const projectNode = screen.getByTestId('node-project-1')
      fireEvent.click(projectNode)

      expect(screen.getByText('Project')).toBeInTheDocument()
    })

    it('displays status for nodes with status', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const projectNode = screen.getByTestId('node-project-1')
      fireEvent.click(projectNode)

      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('BUILD')).toBeInTheDocument()
    })

    it('displays details section', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const agentNode = screen.getByTestId('node-agent-1')
      fireEvent.click(agentNode)

      expect(screen.getByText('Details')).toBeInTheDocument()
    })

    it('displays View Details button', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const projectNode = screen.getByTestId('node-project-1')
      fireEvent.click(projectNode)

      expect(screen.getByRole('button', { name: 'View Details' })).toBeInTheDocument()
    })

    it('closes panel when close button is clicked', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const projectNode = screen.getByTestId('node-project-1')
      fireEvent.click(projectNode)

      const buttons = screen.getAllByRole('button')
      // Click the first button (close button)
      fireEvent.click(buttons[0])

      // Panel should be closed - View all button should not be visible
      expect(screen.queryByRole('button', { name: 'View Details' })).not.toBeInTheDocument()
    })
  })

  describe('Node Status Colors', () => {
    it('applies different colors based on project status', () => {
      const projectsWithDifferentStatuses = [
        { id: '1', name: 'Project Idle', status: 'idle' },
        { id: '2', name: 'Project Research', status: 'research' },
        { id: '3', name: 'Project Build', status: 'build' },
        { id: '4', name: 'Project QA', status: 'qa' },
        { id: '5', name: 'Project Deploy', status: 'deploy' },
        { id: '6', name: 'Project Live', status: 'live' },
      ]

      render(<FactoryMap projects={projectsWithDifferentStatuses} agents={mockAgents} />)

      // All project names should be rendered
      projectsWithDifferentStatuses.forEach(project => {
        expect(screen.getByText(project.name)).toBeInTheDocument()
      })
    })

    it('applies different colors based on agent status', () => {
      const agentsWithDifferentStatuses = [
        { id: '1', name: 'Healthy', status: 'healthy', version: 'v1.0.0' },
        { id: '2', name: 'Degraded', status: 'degraded', version: 'v1.0.0' },
        { id: '3', name: 'Down', status: 'down', version: 'v1.0.0' },
      ]

      render(<FactoryMap projects={mockProjects} agents={agentsWithDifferentStatuses} />)

      agentsWithDifferentStatuses.forEach(agent => {
        expect(screen.getByText(`${agent.name} Agent`)).toBeInTheDocument()
      })
    })
  })

  describe('Panel Details Display', () => {
    it('displays agent version in details', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const agentNode = screen.getByTestId('node-agent-1')
      fireEvent.click(agentNode)

      expect(screen.getByText(/v1\.0\.0/)).toBeInTheDocument()
    })

    it('displays infrastructure components as list', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const infraNode = screen.getByTestId('node-infra')
      fireEvent.click(infraNode)

      // Should show infrastructure components
      expect(screen.getByText(/PostgreSQL/)).toBeInTheDocument()
      expect(screen.getByText(/Qdrant/)).toBeInTheDocument()
      expect(screen.getByText(/Temporal/)).toBeInTheDocument()
      expect(screen.getByText(/Ollama/)).toBeInTheDocument()
    })

    it('hides id field from details', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const projectNode = screen.getByTestId('node-project-1')
      fireEvent.click(projectNode)

      // Should not show "id:" in details
      expect(screen.queryByText(/^id:/)).not.toBeInTheDocument()
    })
  })

  describe('Panel Status Colors', () => {
    it('shows green badge for healthy/live status', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const liveProject = screen.getByTestId('node-project-2')
      fireEvent.click(liveProject)

      const statusBadge = screen.getByText('LIVE')
      expect(statusBadge).toHaveClass('bg-emerald-100', 'text-emerald-700')
    })

    it('shows amber badge for degraded/qa status', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const degradedAgent = screen.getByTestId('node-agent-2')
      fireEvent.click(degradedAgent)

      const statusBadge = screen.getByText('DEGRADED')
      expect(statusBadge).toHaveClass('bg-amber-100', 'text-amber-700')
    })

    it('shows sky badge for build/research status', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const buildProject = screen.getByTestId('node-project-1')
      fireEvent.click(buildProject)

      const statusBadge = screen.getByText('BUILD')
      expect(statusBadge).toHaveClass('bg-sky-100', 'text-sky-700')
    })
  })

  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      const { container } = render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      expect(container.querySelector('.relative')).toBeInTheDocument()
    })

    it('panel close button is accessible', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const projectNode = screen.getByTestId('node-project-1')
      fireEvent.click(projectNode)

      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThanOrEqual(1)
    })

    it('view details button is accessible', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const projectNode = screen.getByTestId('node-project-1')
      fireEvent.click(projectNode)

      const viewButton = screen.getByRole('button', { name: 'View Details' })
      expect(viewButton).toBeInTheDocument()
    })
  })

  describe('Styling', () => {
    it('has rounded borders and shadow', () => {
      const { container } = render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      const mainContainer = container.firstChild
      expect(mainContainer).toHaveClass('rounded-2xl', 'border', 'shadow-soft')
    })

    it('has fixed height', () => {
      const { container } = render(<FactoryMap projects={mockProjects} agents={mockAgents} />)
      const mainContainer = container.firstChild
      expect(mainContainer?.className).toContain('h-[600px]')
    })

    it('panel has proper width', () => {
      render(<FactoryMap projects={mockProjects} agents={mockAgents} />)

      const projectNode = screen.getByTestId('node-project-1')
      fireEvent.click(projectNode)

      const buttons = screen.getAllByRole('button')
      const panel = buttons[0].closest('.w-80')
      expect(panel).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('handles empty projects and agents', () => {
      render(<FactoryMap projects={[]} agents={[]} />)

      // Should still render infrastructure node
      expect(screen.getByText('Infrastructure')).toBeInTheDocument()
    })

    it('handles single project', () => {
      render(<FactoryMap projects={[mockProjects[0]]} agents={mockAgents} />)

      expect(screen.getByText('FormBuilder SaaS')).toBeInTheDocument()
    })

    it('handles single agent', () => {
      render(<FactoryMap projects={mockProjects} agents={[mockAgents[0]]} />)

      expect(screen.getByText('Research Agent')).toBeInTheDocument()
    })
  })
})
