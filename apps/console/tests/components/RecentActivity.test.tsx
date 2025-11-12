import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RecentActivity } from '@/components/RecentActivity'
import * as utils from '@/lib/utils'

// Mock the formatRelativeTime utility
vi.mock('@/lib/utils', async () => {
  const actual = await vi.importActual('@/lib/utils')
  return {
    ...actual,
    formatRelativeTime: vi.fn((date: Date) => {
      const now = Date.now()
      const diff = now - date.getTime()
      const minutes = Math.floor(diff / 60000)
      if (minutes < 1) return 'just now'
      if (minutes === 1) return '1 minute ago'
      if (minutes < 60) return `${minutes} minutes ago`
      const hours = Math.floor(minutes / 60)
      if (hours === 1) return '1 hour ago'
      return `${hours} hours ago`
    })
  }
})

describe('RecentActivity Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders component title', () => {
      render(<RecentActivity />)
      expect(screen.getByText('Recent Activity')).toBeInTheDocument()
    })

    it('renders all activity items', () => {
      render(<RecentActivity />)

      expect(screen.getByText('Add user authentication')).toBeInTheDocument()
      expect(screen.getByText('Build completed successfully')).toBeInTheDocument()
      expect(screen.getByText('QA agent degraded performance')).toBeInTheDocument()
    })

    it('renders project names for each activity', () => {
      render(<RecentActivity />)

      expect(screen.getByText(/FormBuilder SaaS/)).toBeInTheDocument()
      expect(screen.getByText(/Analytics Platform/)).toBeInTheDocument()
      expect(screen.getByText(/System/)).toBeInTheDocument()
    })

    it('renders view all activity button', () => {
      render(<RecentActivity />)
      expect(screen.getByText('View all activity →')).toBeInTheDocument()
    })
  })

  describe('Activity Types', () => {
    it('displays commit activity with correct icon', () => {
      render(<RecentActivity />)
      const activities = screen.getAllByRole('generic')

      // Check that SVG icons are present
      const svgs = screen.getByText('Add user authentication')
        .closest('div')
        ?.parentElement
        ?.querySelector('svg')
      expect(svgs).toBeInTheDocument()
    })

    it('displays run activity with correct icon', () => {
      render(<RecentActivity />)
      const svgs = screen.getByText('Build completed successfully')
        .closest('div')
        ?.parentElement
        ?.querySelector('svg')
      expect(svgs).toBeInTheDocument()
    })

    it('displays alert activity with correct icon', () => {
      render(<RecentActivity />)
      const svgs = screen.getByText('QA agent degraded performance')
        .closest('div')
        ?.parentElement
        ?.querySelector('svg')
      expect(svgs).toBeInTheDocument()
    })
  })

  describe('Time Display', () => {
    it('calls formatRelativeTime for each activity', () => {
      const formatRelativeTimeSpy = vi.spyOn(utils, 'formatRelativeTime')
      render(<RecentActivity />)

      // Should be called 3 times for 3 activities
      expect(formatRelativeTimeSpy).toHaveBeenCalledTimes(3)
    })

    it('displays relative time for activities', () => {
      render(<RecentActivity />)

      // Check that time strings are displayed (mocked to show minutes/hours ago)
      const timeElements = screen.getAllByText(/ago|just now/)
      expect(timeElements.length).toBeGreaterThan(0)
    })

    it('formats time with project separator', () => {
      render(<RecentActivity />)

      // Check for the "·" separator between project and time
      expect(screen.getByText(/FormBuilder SaaS · /)).toBeInTheDocument()
      expect(screen.getByText(/Analytics Platform · /)).toBeInTheDocument()
      expect(screen.getByText(/System · /)).toBeInTheDocument()
    })
  })

  describe('Styling', () => {
    it('uses white background with shadow', () => {
      const { container } = render(<RecentActivity />)
      const mainCard = container.querySelector('.bg-white')
      expect(mainCard).toBeInTheDocument()
      expect(mainCard).toHaveClass('shadow-soft')
    })

    it('has rounded borders', () => {
      const { container } = render(<RecentActivity />)
      const mainCard = container.querySelector('.rounded-2xl')
      expect(mainCard).toBeInTheDocument()
    })

    it('activities are separated with dividers', () => {
      const { container } = render(<RecentActivity />)
      const divider = container.querySelector('.divide-y')
      expect(divider).toBeInTheDocument()
    })

    it('has border at the top of view all button', () => {
      const { container } = render(<RecentActivity />)
      const buttonContainer = screen.getByText('View all activity →').parentElement
      expect(buttonContainer).toHaveClass('border-t')
    })
  })

  describe('Icon Colors', () => {
    it('commit icon has base color', () => {
      render(<RecentActivity />)
      const commitActivity = screen.getByText('Add user authentication')
        .closest('div')
        ?.parentElement
      const icon = commitActivity?.querySelector('svg')
      expect(icon).toHaveClass('text-base-600')
    })

    it('success run icon has success color', () => {
      render(<RecentActivity />)
      const runActivity = screen.getByText('Build completed successfully')
        .closest('div')
        ?.parentElement
      const icon = runActivity?.querySelector('svg')
      expect(icon).toHaveClass('text-accent-success')
    })

    it('alert icon has warning color', () => {
      render(<RecentActivity />)
      const alertActivity = screen.getByText('QA agent degraded performance')
        .closest('div')
        ?.parentElement
      const icon = alertActivity?.querySelector('svg')
      expect(icon).toHaveClass('text-accent-warn')
    })
  })

  describe('Accessibility', () => {
    it('has proper heading structure', () => {
      render(<RecentActivity />)
      const heading = screen.getByRole('heading', { name: 'Recent Activity' })
      expect(heading).toBeInTheDocument()
    })

    it('view all button is accessible', () => {
      render(<RecentActivity />)
      const button = screen.getByRole('button', { name: /View all activity/i })
      expect(button).toBeInTheDocument()
    })

    it('activity messages are readable', () => {
      render(<RecentActivity />)

      const messages = [
        'Add user authentication',
        'Build completed successfully',
        'QA agent degraded performance'
      ]

      messages.forEach(message => {
        expect(screen.getByText(message)).toBeVisible()
      })
    })
  })

  describe('Button Interaction', () => {
    it('view all button has hover state', () => {
      render(<RecentActivity />)
      const button = screen.getByText('View all activity →')
      expect(button.className).toContain('hover:')
    })

    it('view all button has info color scheme', () => {
      render(<RecentActivity />)
      const button = screen.getByText('View all activity →')
      expect(button).toHaveClass('text-accent-info')
    })
  })

  describe('Layout', () => {
    it('uses flexbox for activity items', () => {
      render(<RecentActivity />)
      const firstActivity = screen.getByText('Add user authentication')
        .closest('div')
        ?.parentElement
      expect(firstActivity).toHaveClass('flex', 'gap-3')
    })

    it('icons are flex-shrink-0', () => {
      render(<RecentActivity />)
      const iconContainer = screen.getByText('Add user authentication')
        .closest('div')
        ?.parentElement
        ?.querySelector('.flex-shrink-0')
      expect(iconContainer).toBeInTheDocument()
    })

    it('content area is flex-1 for proper spacing', () => {
      render(<RecentActivity />)
      const contentArea = screen.getByText('Add user authentication')
        .closest('.flex-1')
      expect(contentArea).toBeInTheDocument()
    })
  })
})
