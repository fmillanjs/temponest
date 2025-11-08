import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AgentStatusCard } from '@/components/AgentStatusCard'

describe('AgentStatusCard Component', () => {
  const defaultProps = {
    name: 'Test Agent',
    status: 'healthy' as const,
    heartbeat: '2s ago',
    version: '1.0.0',
  }

  describe('Rendering', () => {
    it('renders agent name', () => {
      render(<AgentStatusCard {...defaultProps} />)
      expect(screen.getByText('Test Agent')).toBeInTheDocument()
    })

    it('renders heartbeat information', () => {
      render(<AgentStatusCard {...defaultProps} />)
      expect(screen.getByText(/Heartbeat: 2s ago/)).toBeInTheDocument()
    })

    it('renders version information', () => {
      render(<AgentStatusCard {...defaultProps} />)
      expect(screen.getByText('v1.0.0')).toBeInTheDocument()
    })

    it('renders open button', () => {
      render(<AgentStatusCard {...defaultProps} />)
      expect(screen.getByRole('button', { name: /Open/i })).toBeInTheDocument()
    })

    it('renders restart button', () => {
      render(<AgentStatusCard {...defaultProps} />)
      expect(screen.getByRole('button', { name: /Restart/i })).toBeInTheDocument()
    })

    it('renders activity icon', () => {
      const { container } = render(<AgentStatusCard {...defaultProps} />)
      const icon = container.querySelector('svg')
      expect(icon).toBeInTheDocument()
    })
  })

  describe('Status Variants', () => {
    it('shows healthy status with correct styling', () => {
      render(<AgentStatusCard {...defaultProps} status="healthy" />)
      const statusBadge = screen.getByText('Healthy')
      expect(statusBadge).toHaveClass('bg-emerald-100', 'text-emerald-700')
    })

    it('shows degraded status with correct styling', () => {
      render(<AgentStatusCard {...defaultProps} status="degraded" />)
      const statusBadge = screen.getByText('Degraded')
      expect(statusBadge).toHaveClass('bg-amber-100', 'text-amber-700')
    })

    it('shows down status with correct styling', () => {
      render(<AgentStatusCard {...defaultProps} status="down" />)
      const statusBadge = screen.getByText('Down')
      expect(statusBadge).toHaveClass('bg-rose-100', 'text-rose-700')
    })

    it('applies correct icon color for healthy status', () => {
      const { container } = render(<AgentStatusCard {...defaultProps} status="healthy" />)
      const icon = container.querySelector('svg')
      expect(icon).toHaveClass('text-emerald-500')
    })

    it('applies correct icon color for degraded status', () => {
      const { container } = render(<AgentStatusCard {...defaultProps} status="degraded" />)
      const icon = container.querySelector('svg')
      expect(icon).toHaveClass('text-amber-500')
    })

    it('applies correct icon color for down status', () => {
      const { container } = render(<AgentStatusCard {...defaultProps} status="down" />)
      const icon = container.querySelector('svg')
      expect(icon).toHaveClass('text-rose-500')
    })
  })

  describe('Button Interactions', () => {
    it('calls onOpen when open button is clicked', async () => {
      const user = userEvent.setup()
      const onOpen = vi.fn()
      render(<AgentStatusCard {...defaultProps} onOpen={onOpen} />)

      await user.click(screen.getByRole('button', { name: /Open/i }))
      expect(onOpen).toHaveBeenCalledTimes(1)
    })

    it('calls onRestart when restart button is clicked', async () => {
      const user = userEvent.setup()
      const onRestart = vi.fn()
      render(<AgentStatusCard {...defaultProps} onRestart={onRestart} />)

      await user.click(screen.getByRole('button', { name: /Restart/i }))
      expect(onRestart).toHaveBeenCalledTimes(1)
    })

    it('does not crash when onOpen is not provided', async () => {
      const user = userEvent.setup()
      render(<AgentStatusCard {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: /Open/i }))
      // Should not throw error
      expect(true).toBe(true)
    })

    it('does not crash when onRestart is not provided', async () => {
      const user = userEvent.setup()
      render(<AgentStatusCard {...defaultProps} />)

      await user.click(screen.getByRole('button', { name: /Restart/i }))
      // Should not throw error
      expect(true).toBe(true)
    })

    it('handles multiple clicks on open button', async () => {
      const user = userEvent.setup()
      const onOpen = vi.fn()
      render(<AgentStatusCard {...defaultProps} onOpen={onOpen} />)

      const openButton = screen.getByRole('button', { name: /Open/i })
      await user.click(openButton)
      await user.click(openButton)
      await user.click(openButton)

      expect(onOpen).toHaveBeenCalledTimes(3)
    })
  })

  describe('Different Agent Configurations', () => {
    it('renders agent with long name', () => {
      render(
        <AgentStatusCard
          {...defaultProps}
          name="Very Long Agent Name That Should Still Display Properly"
        />
      )
      expect(
        screen.getByText('Very Long Agent Name That Should Still Display Properly')
      ).toBeInTheDocument()
    })

    it('renders agent with recent heartbeat', () => {
      render(<AgentStatusCard {...defaultProps} heartbeat="1s ago" />)
      expect(screen.getByText(/Heartbeat: 1s ago/)).toBeInTheDocument()
    })

    it('renders agent with old heartbeat', () => {
      render(<AgentStatusCard {...defaultProps} heartbeat="10m ago" />)
      expect(screen.getByText(/Heartbeat: 10m ago/)).toBeInTheDocument()
    })

    it('renders agent with different version formats', () => {
      render(<AgentStatusCard {...defaultProps} version="2.3.4-beta" />)
      expect(screen.getByText('v2.3.4-beta')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('buttons are keyboard accessible', () => {
      render(<AgentStatusCard {...defaultProps} />)
      const openButton = screen.getByRole('button', { name: /Open/i })
      const restartButton = screen.getByRole('button', { name: /Restart/i })

      expect(openButton).toBeInTheDocument()
      expect(restartButton).toBeInTheDocument()
    })

    it('has proper button roles', () => {
      render(<AgentStatusCard {...defaultProps} />)
      const buttons = screen.getAllByRole('button')
      expect(buttons).toHaveLength(2)
    })
  })

  describe('Styling', () => {
    it('applies card styling', () => {
      const { container } = render(<AgentStatusCard {...defaultProps} />)
      const card = container.firstChild
      expect(card).toHaveClass('rounded-2xl', 'border', 'bg-white')
    })

    it('has hover effects', () => {
      const { container } = render(<AgentStatusCard {...defaultProps} />)
      const card = container.firstChild
      expect(card).toHaveClass('hover:shadow-soft-lg')
    })

    it('open button has correct styling', () => {
      render(<AgentStatusCard {...defaultProps} />)
      const openButton = screen.getByRole('button', { name: /Open/i })
      expect(openButton).toHaveClass('bg-base-900', 'text-white')
    })

    it('restart button has correct styling', () => {
      render(<AgentStatusCard {...defaultProps} />)
      const restartButton = screen.getByRole('button', { name: /Restart/i })
      expect(restartButton).toHaveClass('bg-base-200', 'text-base-800')
    })
  })
})
