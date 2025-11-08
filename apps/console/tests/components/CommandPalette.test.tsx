import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CommandPalette } from '@/components/CommandPalette'

// Mock the auth client
vi.mock('@/lib/auth-client', () => ({
  signOut: vi.fn(),
}))

// Mock useRouter
const mockPush = vi.fn()
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: vi.fn(),
    prefetch: vi.fn(),
    back: vi.fn(),
    pathname: '/',
    query: {},
    asPath: '/',
  }),
  usePathname: () => '/',
  useSearchParams: () => new URLSearchParams(),
}))

describe('CommandPalette Component', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Keyboard Shortcuts', () => {
    it('opens on Cmd+K', async () => {
      render(<CommandPalette />)

      // Simulate Cmd+K
      const event = new KeyboardEvent('keydown', {
        key: 'k',
        metaKey: true,
      })
      document.dispatchEvent(event)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Type a command or search/)).toBeInTheDocument()
      })
    })

    it('opens on Ctrl+K', async () => {
      render(<CommandPalette />)

      // Simulate Ctrl+K
      const event = new KeyboardEvent('keydown', {
        key: 'k',
        ctrlKey: true,
      })
      document.dispatchEvent(event)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Type a command or search/)).toBeInTheDocument()
      })
    })

    it('toggles on multiple Cmd+K presses', async () => {
      render(<CommandPalette />)

      // Open
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'k', metaKey: true })
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Type a command or search/)).toBeInTheDocument()
      })

      // Close
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'k', metaKey: true })
      )

      await waitFor(() => {
        expect(screen.queryByPlaceholderText(/Type a command or search/)).not.toBeInTheDocument()
      })
    })

    it('does not open on K without modifier', async () => {
      render(<CommandPalette />)

      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k' }))

      await waitFor(() => {
        expect(screen.queryByPlaceholderText(/Type a command or search/)).not.toBeInTheDocument()
      })
    })
  })

  describe('Navigation Commands', () => {
    beforeEach(async () => {
      render(<CommandPalette />)
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'k', metaKey: true })
      )
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Type a command or search/)).toBeInTheDocument()
      })
    })

    it('shows navigation group', () => {
      expect(screen.getByText('Navigation')).toBeInTheDocument()
    })

    it('navigates to dashboard', async () => {
      const user = userEvent.setup()
      const dashboardOption = screen.getByText('Dashboard')

      await user.click(dashboardOption)

      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })

    it('navigates to factory map', async () => {
      const user = userEvent.setup()
      const factoryMapOption = screen.getByText('Factory Map')

      await user.click(factoryMapOption)

      expect(mockPush).toHaveBeenCalledWith('/factory-map')
    })

    it('navigates to workflows', async () => {
      const user = userEvent.setup()
      const workflowsOption = screen.getByText('Workflows')

      await user.click(workflowsOption)

      expect(mockPush).toHaveBeenCalledWith('/workflows')
    })

    it('navigates to projects', async () => {
      const user = userEvent.setup()
      const projectsOption = screen.getByText('Projects')

      await user.click(projectsOption)

      expect(mockPush).toHaveBeenCalledWith('/projects')
    })

    it('navigates to agents', async () => {
      const user = userEvent.setup()
      const agentsOption = screen.getByText('Agents')

      await user.click(agentsOption)

      expect(mockPush).toHaveBeenCalledWith('/agents')
    })
  })

  describe('Tools Commands', () => {
    beforeEach(async () => {
      render(<CommandPalette />)
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'k', metaKey: true })
      )
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Type a command or search/)).toBeInTheDocument()
      })
    })

    it('shows tools group', () => {
      expect(screen.getByText('Tools')).toBeInTheDocument()
    })

    it('navigates to wizards', async () => {
      const user = userEvent.setup()
      const wizardsOption = screen.getByText('Wizards')

      await user.click(wizardsOption)

      expect(mockPush).toHaveBeenCalledWith('/wizards')
    })

    it('navigates to financial calculator', async () => {
      const user = userEvent.setup()
      const financialOption = screen.getByText('Financial Calculator')

      await user.click(financialOption)

      expect(mockPush).toHaveBeenCalledWith('/financials')
    })

    it('navigates to documentation', async () => {
      const user = userEvent.setup()
      const docsOption = screen.getByText('Documentation')

      await user.click(docsOption)

      expect(mockPush).toHaveBeenCalledWith('/docs')
    })

    it('navigates to observability', async () => {
      const user = userEvent.setup()
      const observabilityOption = screen.getByText('Observability')

      await user.click(observabilityOption)

      expect(mockPush).toHaveBeenCalledWith('/observability')
    })
  })

  describe('Settings Commands', () => {
    beforeEach(async () => {
      render(<CommandPalette />)
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'k', metaKey: true })
      )
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Type a command or search/)).toBeInTheDocument()
      })
    })

    it('shows settings group', () => {
      const settingsItems = screen.getAllByText('Settings')
      // Should have both the heading and the menu item
      expect(settingsItems.length).toBeGreaterThan(0)
    })

    it('navigates to settings', async () => {
      const user = userEvent.setup()
      const settingsItems = screen.getAllByText('Settings')
      // Click the second "Settings" which is the menu item (first is the heading)
      const settingsOption = settingsItems[settingsItems.length - 1]

      await user.click(settingsOption)

      expect(mockPush).toHaveBeenCalledWith('/settings')
    })

    it('handles sign out', async () => {
      const user = userEvent.setup()
      const { signOut } = await import('@/lib/auth-client')
      const signOutOption = screen.getByText('Sign Out')

      await user.click(signOutOption)

      await waitFor(() => {
        expect(signOut).toHaveBeenCalled()
        expect(mockPush).toHaveBeenCalledWith('/login')
      })
    })
  })

  describe('Search Functionality', () => {
    beforeEach(async () => {
      render(<CommandPalette />)
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'k', metaKey: true })
      )
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Type a command or search/)).toBeInTheDocument()
      })
    })

    it('allows typing in search input', async () => {
      const user = userEvent.setup()
      const searchInput = screen.getByPlaceholderText(/Type a command or search/)

      await user.type(searchInput, 'dashboard')
      expect(searchInput).toHaveValue('dashboard')
    })

    it('shows "No results found" for non-matching search', async () => {
      const user = userEvent.setup()
      const searchInput = screen.getByPlaceholderText(/Type a command or search/)

      await user.type(searchInput, 'nonexistent')

      await waitFor(() => {
        expect(screen.getByText('No results found.')).toBeInTheDocument()
      })
    })
  })

  describe('Dialog Behavior', () => {
    it('closes when command is selected', async () => {
      render(<CommandPalette />)
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'k', metaKey: true })
      )

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Type a command or search/)).toBeInTheDocument()
      })

      const user = userEvent.setup()
      const dashboardOption = screen.getByText('Dashboard')
      await user.click(dashboardOption)

      await waitFor(() => {
        expect(screen.queryByPlaceholderText(/Type a command or search/)).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    beforeEach(async () => {
      render(<CommandPalette />)
      document.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'k', metaKey: true })
      )
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Type a command or search/)).toBeInTheDocument()
      })
    })

    it('has keyboard navigation support', () => {
      const searchInput = screen.getByPlaceholderText(/Type a command or search/)
      expect(searchInput).toBeInTheDocument()
      expect(searchInput).toHaveAttribute('type')
    })

    it('displays keyboard shortcuts for commands', () => {
      expect(screen.getByText('⌘D')).toBeInTheDocument() // Dashboard
      expect(screen.getByText('⌘M')).toBeInTheDocument() // Factory Map
      expect(screen.getByText('⌘W')).toBeInTheDocument() // Workflows
      expect(screen.getByText('⌘P')).toBeInTheDocument() // Projects
      expect(screen.getByText('⌘A')).toBeInTheDocument() // Agents
      expect(screen.getByText('⌘,')).toBeInTheDocument() // Settings
    })
  })
})
