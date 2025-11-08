import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Sidebar } from '@/components/Sidebar'

// Mock Next.js navigation
const mockPathname = vi.fn()
vi.mock('next/navigation', () => ({
  usePathname: () => mockPathname(),
}))

describe('Sidebar Component', () => {
  beforeEach(() => {
    mockPathname.mockReturnValue('/dashboard')
  })

  describe('Rendering', () => {
    it('renders sidebar element', () => {
      render(<Sidebar />)
      expect(screen.getByText('SaaS Empire')).toBeInTheDocument()
    })

    it('renders logo/brand', () => {
      render(<Sidebar />)
      expect(screen.getByRole('heading', { name: 'SaaS Empire' })).toBeInTheDocument()
    })

    it('renders version information', () => {
      render(<Sidebar />)
      expect(screen.getByText('v0.1.0')).toBeInTheDocument()
      expect(screen.getByText('Powered by Claude Code')).toBeInTheDocument()
    })
  })

  describe('Navigation Links', () => {
    it('renders all navigation links', () => {
      render(<Sidebar />)

      expect(screen.getByRole('link', { name: /Dashboard/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Factory Map/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Workflows/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Projects/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Agents/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Wizards/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Financials/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Docs/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Observability/i })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /Settings/i })).toBeInTheDocument()
    })

    it('has correct href for dashboard link', () => {
      render(<Sidebar />)
      const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
      expect(dashboardLink).toHaveAttribute('href', '/dashboard')
    })

    it('has correct href for factory map link', () => {
      render(<Sidebar />)
      const factoryMapLink = screen.getByRole('link', { name: /Factory Map/i })
      expect(factoryMapLink).toHaveAttribute('href', '/factory-map')
    })

    it('has correct href for workflows link', () => {
      render(<Sidebar />)
      const workflowsLink = screen.getByRole('link', { name: /Workflows/i })
      expect(workflowsLink).toHaveAttribute('href', '/workflows')
    })

    it('has correct href for projects link', () => {
      render(<Sidebar />)
      const projectsLink = screen.getByRole('link', { name: /Projects/i })
      expect(projectsLink).toHaveAttribute('href', '/projects')
    })

    it('has correct href for agents link', () => {
      render(<Sidebar />)
      const agentsLink = screen.getByRole('link', { name: /Agents/i })
      expect(agentsLink).toHaveAttribute('href', '/agents')
    })
  })

  describe('Active State', () => {
    it('highlights active link for exact path match', () => {
      mockPathname.mockReturnValue('/dashboard')
      render(<Sidebar />)

      const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
      expect(dashboardLink).toHaveClass('bg-base-800', 'text-white')
    })

    it('highlights active link for sub-path', () => {
      mockPathname.mockReturnValue('/projects/my-project')
      render(<Sidebar />)

      const projectsLink = screen.getByRole('link', { name: /Projects/i })
      expect(projectsLink).toHaveClass('bg-base-800', 'text-white')
    })

    it('does not highlight inactive links', () => {
      mockPathname.mockReturnValue('/dashboard')
      render(<Sidebar />)

      const projectsLink = screen.getByRole('link', { name: /Projects/i })
      expect(projectsLink).toHaveClass('text-base-300')
      expect(projectsLink).not.toHaveClass('bg-base-800')
    })

    it('highlights workflows link when on workflows page', () => {
      mockPathname.mockReturnValue('/workflows')
      render(<Sidebar />)

      const workflowsLink = screen.getByRole('link', { name: /Workflows/i })
      expect(workflowsLink).toHaveClass('bg-base-800', 'text-white')

      // Dashboard should not be highlighted
      const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
      expect(dashboardLink).toHaveClass('text-base-300')
      expect(dashboardLink).not.toHaveClass('text-white')
    })
  })

  describe('Icons', () => {
    it('renders icons for all navigation items', () => {
      render(<Sidebar />)

      // Each navigation item should have an icon
      const links = screen.getAllByRole('link')
      links.forEach((link) => {
        const svg = link.querySelector('svg')
        expect(svg).toBeInTheDocument()
      })
    })

    it('changes icon color for active item', () => {
      mockPathname.mockReturnValue('/dashboard')
      render(<Sidebar />)

      const dashboardLink = screen.getByRole('link', { name: /Dashboard/i })
      const icon = dashboardLink.querySelector('svg')
      expect(icon).toHaveClass('text-accent-info')
    })
  })

  describe('Accessibility', () => {
    it('navigation links are keyboard accessible', () => {
      render(<Sidebar />)
      const links = screen.getAllByRole('link')

      links.forEach((link) => {
        expect(link).toHaveAttribute('href')
      })
    })

    it('has proper navigation semantic structure', () => {
      render(<Sidebar />)
      const nav = screen.getByRole('navigation')
      expect(nav).toBeInTheDocument()
    })

    it('has proper heading for logo', () => {
      render(<Sidebar />)
      const heading = screen.getByRole('heading', { level: 1 })
      expect(heading).toHaveTextContent('SaaS Empire')
    })
  })

  describe('Styling', () => {
    it('applies correct background color', () => {
      const { container } = render(<Sidebar />)
      const sidebar = container.firstChild
      expect(sidebar).toHaveClass('bg-base-900', 'text-white')
    })

    it('has fixed width', () => {
      const { container } = render(<Sidebar />)
      const sidebar = container.firstChild
      expect(sidebar).toHaveClass('w-64')
    })

    it('is full height', () => {
      const { container } = render(<Sidebar />)
      const sidebar = container.firstChild
      expect(sidebar).toHaveClass('h-full')
    })
  })
})
