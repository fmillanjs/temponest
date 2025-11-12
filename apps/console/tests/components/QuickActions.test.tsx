import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QuickActions } from '@/components/QuickActions'

describe('QuickActions Component', () => {
  describe('Rendering', () => {
    it('renders component title', () => {
      render(<QuickActions />)
      expect(screen.getByText('Quick Actions')).toBeInTheDocument()
    })

    it('renders all three action cards', () => {
      render(<QuickActions />)

      expect(screen.getByText('Start Single-SaaS Wizard')).toBeInTheDocument()
      expect(screen.getByText('Initialize Factory')).toBeInTheDocument()
      expect(screen.getByText('Run Calculator')).toBeInTheDocument()
    })

    it('renders action descriptions', () => {
      render(<QuickActions />)

      expect(screen.getByText('Launch a new SaaS product in 1-8 weeks')).toBeInTheDocument()
      expect(screen.getByText('Set up your complete 4-week factory system')).toBeInTheDocument()
      expect(screen.getByText('Model financials and projections')).toBeInTheDocument()
    })
  })

  describe('Links', () => {
    it('has correct href for Single-SaaS Wizard', () => {
      render(<QuickActions />)
      const link = screen.getByRole('link', { name: /Start Single-SaaS Wizard/i })
      expect(link).toHaveAttribute('href', '/wizards/single')
    })

    it('has correct href for Initialize Factory', () => {
      render(<QuickActions />)
      const link = screen.getByRole('link', { name: /Initialize Factory/i })
      expect(link).toHaveAttribute('href', '/wizards/factory')
    })

    it('has correct href for Run Calculator', () => {
      render(<QuickActions />)
      const link = screen.getByRole('link', { name: /Run Calculator/i })
      expect(link).toHaveAttribute('href', '/financials')
    })

    it('all action cards are clickable links', () => {
      render(<QuickActions />)
      const links = screen.getAllByRole('link')
      expect(links).toHaveLength(3)
    })
  })

  describe('Icons', () => {
    it('renders icons for all action cards', () => {
      render(<QuickActions />)
      const links = screen.getAllByRole('link')

      links.forEach((link) => {
        const svg = link.querySelector('svg')
        expect(svg).toBeInTheDocument()
      })
    })

    it('icons are inside colored containers', () => {
      render(<QuickActions />)
      const links = screen.getAllByRole('link')

      links.forEach((link) => {
        // Check that SVG is inside a div with background color classes
        const iconContainer = link.querySelector('[class*="bg-"]')
        expect(iconContainer).toBeInTheDocument()
        const svg = iconContainer?.querySelector('svg')
        expect(svg).toBeInTheDocument()
      })
    })
  })

  describe('Styling', () => {
    it('applies custom className prop', () => {
      const { container } = render(<QuickActions className="custom-class" />)
      const wrapper = container.firstChild
      expect(wrapper).toHaveClass('custom-class')
    })

    it('uses grid layout for action cards', () => {
      render(<QuickActions />)
      const grid = screen.getByText('Quick Actions').nextElementSibling
      expect(grid).toHaveClass('grid')
    })

    it('action cards have hover effects', () => {
      render(<QuickActions />)
      const links = screen.getAllByRole('link')

      links.forEach((link) => {
        expect(link).toHaveClass('group')
        expect(link.className).toContain('hover:')
      })
    })
  })

  describe('Accessibility', () => {
    it('all actions are accessible as links', () => {
      render(<QuickActions />)
      const links = screen.getAllByRole('link')

      links.forEach((link) => {
        expect(link).toHaveAttribute('href')
      })
    })

    it('has proper heading structure', () => {
      render(<QuickActions />)
      const heading = screen.getByRole('heading', { name: 'Quick Actions' })
      expect(heading).toBeInTheDocument()
    })

    it('action titles are descriptive', () => {
      render(<QuickActions />)

      const wizardLink = screen.getByRole('link', { name: /Start Single-SaaS Wizard/i })
      expect(wizardLink).toHaveAccessibleName()

      const factoryLink = screen.getByRole('link', { name: /Initialize Factory/i })
      expect(factoryLink).toHaveAccessibleName()

      const calculatorLink = screen.getByRole('link', { name: /Run Calculator/i })
      expect(calculatorLink).toHaveAccessibleName()
    })
  })

  describe('Color Schemes', () => {
    it('Single-SaaS Wizard has sky color scheme', () => {
      render(<QuickActions />)
      const link = screen.getByRole('link', { name: /Start Single-SaaS Wizard/i })
      const iconContainer = link.querySelector('[class*="bg-sky"]')
      expect(iconContainer).toBeInTheDocument()
    })

    it('Initialize Factory has emerald color scheme', () => {
      render(<QuickActions />)
      const link = screen.getByRole('link', { name: /Initialize Factory/i })
      const iconContainer = link.querySelector('[class*="bg-emerald"]')
      expect(iconContainer).toBeInTheDocument()
    })

    it('Run Calculator has amber color scheme', () => {
      render(<QuickActions />)
      const link = screen.getByRole('link', { name: /Run Calculator/i })
      const iconContainer = link.querySelector('[class*="bg-amber"]')
      expect(iconContainer).toBeInTheDocument()
    })
  })
})
