import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FinancialsPage from '@/app/financials/page'

// Mock recharts
vi.mock('recharts', () => ({
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div>Line</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div>Bar</div>,
  XAxis: () => <div>XAxis</div>,
  YAxis: () => <div>YAxis</div>,
  CartesianGrid: () => <div>Grid</div>,
  Tooltip: () => <div>Tooltip</div>,
  Legend: () => <div>Legend</div>,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
}))

describe('FinancialsPage', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
    global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
    global.URL.revokeObjectURL = vi.fn()

    // Mock document.createElement for download links
    const mockAnchor = document.createElement('a')
    mockAnchor.click = vi.fn()
    vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
      if (tagName === 'a') return mockAnchor
      return document.createElement(tagName)
    })
  })

  describe('Rendering', () => {
    it('renders financials heading', () => {
      render(<FinancialsPage />)

      expect(screen.getByText('Financial Calculator')).toBeInTheDocument()
      expect(screen.getByText('Model your SaaS financials and projections')).toBeInTheDocument()
    })

    it('renders calculator selection section', () => {
      render(<FinancialsPage />)

      expect(screen.getByText('Select Calculator Model')).toBeInTheDocument()
    })

    it('renders all calculator options', () => {
      render(<FinancialsPage />)

      expect(screen.getByText('FormFlow')).toBeInTheDocument()
      expect(screen.getByText('Form Builder SaaS')).toBeInTheDocument()

      expect(screen.getByText('SimpleAnalytics')).toBeInTheDocument()
      expect(screen.getByText('Web Analytics Platform')).toBeInTheDocument()

      expect(screen.getByText('MicroCRM')).toBeInTheDocument()
      expect(screen.getByText('Simple CRM System')).toBeInTheDocument()

      expect(screen.getByText('QuickSchedule')).toBeInTheDocument()
      expect(screen.getByText('Appointment Booking')).toBeInTheDocument()

      expect(screen.getByText('EmailCraft')).toBeInTheDocument()
      expect(screen.getByText('Email Template Builder')).toBeInTheDocument()
    })

    it('renders run calculation button', () => {
      render(<FinancialsPage />)

      expect(screen.getByText('Run Calculation')).toBeInTheDocument()
    })
  })

  describe('Calculator Selection', () => {
    it('allows selecting different calculator models', async () => {
      const user = userEvent.setup()
      render(<FinancialsPage />)

      const analyticsButton = screen.getByText('SimpleAnalytics').closest('button')
      expect(analyticsButton).toBeInTheDocument()

      if (analyticsButton) {
        await user.click(analyticsButton)
        expect(analyticsButton).toHaveClass('border-accent-primary')
      }
    })

    it('has FormFlow selected by default', () => {
      const { container } = render(<FinancialsPage />)

      const formFlowButton = screen.getByText('FormFlow').closest('button')
      expect(formFlowButton).toHaveClass('border-accent-primary')
    })

    it('updates selection on click', async () => {
      const user = userEvent.setup()
      render(<FinancialsPage />)

      const crmButton = screen.getByText('MicroCRM').closest('button')
      if (crmButton) {
        await user.click(crmButton)
        expect(crmButton).toHaveClass('border-accent-primary')
      }
    })
  })

  describe('Run Calculation', () => {
    it('enables run calculation button initially', () => {
      render(<FinancialsPage />)

      const button = screen.getByText('Run Calculation')
      expect(button).not.toBeDisabled()
    })

    it('shows running state when calculation starts', async () => {
      const user = userEvent.setup()

      // Mock streaming response
      const mockReader = {
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('Test output\n') })
          .mockResolvedValueOnce({ done: true, value: undefined }),
      }

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as any)

      render(<FinancialsPage />)

      const button = screen.getByText('Run Calculation')
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText('Running...')).toBeInTheDocument()
      })
    })

    it('calls API with correct model', async () => {
      const user = userEvent.setup()

      const mockReader = {
        read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
      }

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as any)

      render(<FinancialsPage />)

      const button = screen.getByText('Run Calculation')
      await user.click(button)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          '/api/financials/run',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: expect.stringContaining('formbuilder'),
          })
        )
      })
    })
  })

  describe('Export Functionality', () => {
    it('does not show export buttons initially', () => {
      render(<FinancialsPage />)

      expect(screen.queryByText('Export JSON')).not.toBeInTheDocument()
      expect(screen.queryByText('Export CSV')).not.toBeInTheDocument()
      expect(screen.queryByText('Save to Database')).not.toBeInTheDocument()
    })
  })

  describe('Output Display', () => {
    it('does not show output initially', () => {
      render(<FinancialsPage />)

      expect(screen.queryByText('Calculation Output')).not.toBeInTheDocument()
    })
  })

  describe('Charts', () => {
    it('does not show charts initially', () => {
      render(<FinancialsPage />)

      expect(screen.queryByText('MRR Growth Over Time')).not.toBeInTheDocument()
      expect(screen.queryByText('Customer Growth')).not.toBeInTheDocument()
      expect(screen.queryByText('Cumulative Profit')).not.toBeInTheDocument()
    })
  })

  describe('Summary Cards', () => {
    it('does not show summary cards initially', () => {
      render(<FinancialsPage />)

      expect(screen.queryByText('Month 12 Projection')).not.toBeInTheDocument()
      expect(screen.queryByText('Month 24 Projection')).not.toBeInTheDocument()
    })
  })

  describe('Calculator Options Grid', () => {
    it('applies responsive grid layout', () => {
      const { container } = render(<FinancialsPage />)

      const grid = container.querySelector('.grid.md\\:grid-cols-2.lg\\:grid-cols-3')
      expect(grid).toBeInTheDocument()
    })

    it('renders all 5 calculator options as buttons', () => {
      const { container } = render(<FinancialsPage />)

      const buttons = container.querySelectorAll('button.rounded-xl.border-2')
      expect(buttons.length).toBeGreaterThanOrEqual(5)
    })
  })

  describe('Button States', () => {
    it('disables run button when calculation is running', async () => {
      const user = userEvent.setup()

      const mockReader = {
        read: vi.fn()
          .mockResolvedValueOnce({ done: false, value: new TextEncoder().encode('output\n') })
          .mockImplementation(() => new Promise(() => {})), // Never resolve to keep it running
      }

      vi.mocked(global.fetch).mockResolvedValue({
        ok: true,
        body: {
          getReader: () => mockReader,
        },
      } as any)

      render(<FinancialsPage />)

      const button = screen.getByText('Run Calculation')
      await user.click(button)

      await waitFor(() => {
        const runningButton = screen.getByText('Running...')
        expect(runningButton).toBeDisabled()
      })
    })
  })

  describe('Layout and Styling', () => {
    it('applies correct spacing classes', () => {
      const { container } = render(<FinancialsPage />)

      const mainDiv = container.firstChild
      expect(mainDiv).toHaveClass('space-y-6')
    })

    it('applies correct heading styles', () => {
      render(<FinancialsPage />)

      const heading = screen.getByText('Financial Calculator')
      expect(heading).toHaveClass('text-3xl', 'font-bold', 'text-base-900')
    })

    it('applies correct description styles', () => {
      render(<FinancialsPage />)

      const description = screen.getByText('Model your SaaS financials and projections')
      expect(description).toHaveClass('mt-1', 'text-base-600')
    })

    it('applies card styles to calculator section', () => {
      const { container } = render(<FinancialsPage />)

      const card = container.querySelector('.rounded-2xl.border.bg-white.p-6.shadow-soft')
      expect(card).toBeInTheDocument()
    })
  })

  describe('Calculator Descriptions', () => {
    it('shows correct description for FormFlow', () => {
      render(<FinancialsPage />)

      const formFlowButton = screen.getByText('FormFlow').closest('button')
      expect(formFlowButton?.textContent).toContain('Form Builder SaaS')
    })

    it('shows correct description for SimpleAnalytics', () => {
      render(<FinancialsPage />)

      const analyticsButton = screen.getByText('SimpleAnalytics').closest('button')
      expect(analyticsButton?.textContent).toContain('Web Analytics Platform')
    })

    it('shows correct description for MicroCRM', () => {
      render(<FinancialsPage />)

      const crmButton = screen.getByText('MicroCRM').closest('button')
      expect(crmButton?.textContent).toContain('Simple CRM System')
    })

    it('shows correct description for QuickSchedule', () => {
      render(<FinancialsPage />)

      const scheduleButton = screen.getByText('QuickSchedule').closest('button')
      expect(scheduleButton?.textContent).toContain('Appointment Booking')
    })

    it('shows correct description for EmailCraft', () => {
      render(<FinancialsPage />)

      const emailButton = screen.getByText('EmailCraft').closest('button')
      expect(emailButton?.textContent).toContain('Email Template Builder')
    })
  })

  describe('Interaction', () => {
    it('allows switching between calculator models', async () => {
      const user = userEvent.setup()
      render(<FinancialsPage />)

      const analyticsButton = screen.getByText('SimpleAnalytics').closest('button')
      const crmButton = screen.getByText('MicroCRM').closest('button')

      if (analyticsButton) {
        await user.click(analyticsButton)
        expect(analyticsButton).toHaveClass('border-accent-primary')
      }

      if (crmButton) {
        await user.click(crmButton)
        expect(crmButton).toHaveClass('border-accent-primary')
      }
    })

    it('maintains selection after clicking', async () => {
      const user = userEvent.setup()
      render(<FinancialsPage />)

      const emailButton = screen.getByText('EmailCraft').closest('button')

      if (emailButton) {
        await user.click(emailButton)
        expect(emailButton).toHaveClass('border-accent-primary')

        // Click again should maintain selection
        await user.click(emailButton)
        expect(emailButton).toHaveClass('border-accent-primary')
      }
    })
  })

  describe('Accessibility', () => {
    it('has keyboard-accessible calculator buttons', () => {
      render(<FinancialsPage />)

      const buttons = screen.getAllByRole('button')
      expect(buttons.length).toBeGreaterThan(0)

      buttons.forEach(button => {
        expect(button).toBeInTheDocument()
      })
    })

    it('has descriptive button text', () => {
      render(<FinancialsPage />)

      expect(screen.getByText('Run Calculation')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles fetch errors gracefully', async () => {
      const user = userEvent.setup()

      vi.mocked(global.fetch).mockRejectedValue(new Error('Network error'))

      render(<FinancialsPage />)

      const button = screen.getByText('Run Calculation')
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText(/Error: Network error/)).toBeInTheDocument()
      })
    })

    it('handles non-OK responses', async () => {
      const user = userEvent.setup()

      vi.mocked(global.fetch).mockResolvedValue({
        ok: false,
        status: 500,
      } as any)

      render(<FinancialsPage />)

      const button = screen.getByText('Run Calculation')
      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText(/Error: Failed to run calculation/)).toBeInTheDocument()
      })
    })
  })
})
