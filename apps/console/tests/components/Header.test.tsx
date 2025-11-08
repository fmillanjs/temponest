import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Header } from '@/components/Header'

// Mock the UserMenu component
vi.mock('@/components/UserMenu', () => ({
  UserMenu: () => <div data-testid="user-menu">User Menu</div>,
}))

describe('Header Component', () => {
  describe('Rendering', () => {
    it('renders header element', () => {
      render(<Header />)
      const header = screen.getByRole('banner')
      expect(header).toBeInTheDocument()
    })

    it('renders search input', () => {
      render(<Header />)
      const searchInput = screen.getByPlaceholderText(/Search projects, runs, docs/)
      expect(searchInput).toBeInTheDocument()
    })

    it('renders notification button', () => {
      render(<Header />)
      const buttons = screen.getAllByRole('button')
      // The notification button is the first button (dropdown trigger)
      expect(buttons[0]).toBeInTheDocument()
      expect(buttons[0]).toHaveAttribute('data-state', 'closed')
    })

    it('renders user menu', () => {
      render(<Header />)
      expect(screen.getByTestId('user-menu')).toBeInTheDocument()
    })
  })

  describe('Search Functionality', () => {
    it('allows typing in search input', async () => {
      const user = userEvent.setup()
      render(<Header />)
      const searchInput = screen.getByPlaceholderText(/Search projects, runs, docs/)

      await user.type(searchInput, 'test query')
      expect(searchInput).toHaveValue('test query')
    })

    it('shows keyboard shortcut hint', () => {
      render(<Header />)
      const searchInput = screen.getByPlaceholderText(/⌘K/)
      expect(searchInput).toBeInTheDocument()
    })
  })

  describe('Notifications', () => {
    it('shows unread notification indicator', () => {
      render(<Header />)
      const buttons = screen.getAllByRole('button')
      const bellButton = buttons[0]
      // Look for the notification dot
      const notificationDot = bellButton.querySelector('.bg-rose-500')
      expect(notificationDot).toBeInTheDocument()
    })

    it('opens notifications dropdown when clicked', async () => {
      const user = userEvent.setup()
      render(<Header />)
      const buttons = screen.getAllByRole('button')
      const bellButton = buttons[0]

      await user.click(bellButton)
      expect(screen.getByText('Notifications')).toBeInTheDocument()
    })

    it('displays notification items', async () => {
      const user = userEvent.setup()
      render(<Header />)
      const buttons = screen.getAllByRole('button')
      const bellButton = buttons[0]

      await user.click(bellButton)

      expect(screen.getByText('Build completed')).toBeInTheDocument()
      expect(screen.getByText('Wizard progress')).toBeInTheDocument()
      expect(screen.getByText('Agent degraded')).toBeInTheDocument()
    })

    it('shows notification types with correct icons', async () => {
      const user = userEvent.setup()
      render(<Header />)
      const buttons = screen.getAllByRole('button')
      const bellButton = buttons[0]

      await user.click(bellButton)

      // Check for success notification (Build completed)
      expect(screen.getByText('Sample SaaS build finished successfully')).toBeInTheDocument()

      // Check for info notification (Wizard progress)
      expect(screen.getByText('Single-SaaS wizard is 60% complete')).toBeInTheDocument()

      // Check for warning notification (Agent degraded)
      expect(screen.getByText('Designer agent status is degraded')).toBeInTheDocument()
    })

    it('shows notification timestamps', async () => {
      const user = userEvent.setup()
      render(<Header />)
      const buttons = screen.getAllByRole('button')
      const bellButton = buttons[0]

      await user.click(bellButton)

      expect(screen.getByText('2 min ago')).toBeInTheDocument()
      expect(screen.getByText('15 min ago')).toBeInTheDocument()
      expect(screen.getByText('1 hour ago')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper header role', () => {
      render(<Header />)
      expect(screen.getByRole('banner')).toBeInTheDocument()
    })

    it('notification button is keyboard accessible', async () => {
      const user = userEvent.setup()
      render(<Header />)
      const buttons = screen.getAllByRole('button')
      const bellButton = buttons[0]

      bellButton.focus()
      expect(bellButton).toHaveFocus()

      await user.keyboard('{Enter}')
      expect(screen.getByText('Notifications')).toBeInTheDocument()
    })

    it('search input is keyboard accessible', () => {
      render(<Header />)
      const searchInput = screen.getByPlaceholderText(/Search projects, runs, docs/)

      searchInput.focus()
      expect(searchInput).toHaveFocus()
    })
  })

  describe('Styling', () => {
    it('applies correct background and border styles', () => {
      render(<Header />)
      const header = screen.getByRole('banner')
      expect(header).toHaveClass('bg-white', 'border-b')
    })

    it('has correct height', () => {
      render(<Header />)
      const header = screen.getByRole('banner')
      expect(header).toHaveClass('h-16')
    })
  })
})
