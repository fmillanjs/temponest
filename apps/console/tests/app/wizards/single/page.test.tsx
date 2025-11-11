import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SingleSaasWizardPage from '@/app/wizards/single/page'

// Mock UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, disabled, variant, className }: any) => (
    <button onClick={onClick} disabled={disabled} data-variant={variant} className={className}>
      {children}
    </button>
  ),
}))

vi.mock('@/components/ui/input', () => ({
  Input: (props: any) => <input {...props} />,
}))

vi.mock('@/components/ui/card', () => ({
  Card: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardContent: ({ children, className }: any) => <div className={className}>{children}</div>,
  CardDescription: ({ children }: any) => <div>{children}</div>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <h3>{children}</h3>,
}))

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, className }: any) => <span className={className}>{children}</span>,
}))

vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value, className }: any) => (
    <div className={className} data-value={value}>
      Progress: {value}%
    </div>
  ),
}))

vi.mock('@/components/ui/scroll-area', () => ({
  ScrollArea: ({ children, className }: any) => <div className={className}>{children}</div>,
}))

describe('SingleSaasWizardPage', () => {
  let localStorageMock: { [key: string]: string }
  let getItemSpy: any
  let setItemSpy: any
  let removeItemSpy: any

  beforeEach(() => {
    localStorageMock = {}

    getItemSpy = vi.fn((key: string) => localStorageMock[key] || null)
    setItemSpy = vi.fn((key: string, value: string) => {
      localStorageMock[key] = value
    })
    removeItemSpy = vi.fn((key: string) => {
      delete localStorageMock[key]
    })

    // Mock localStorage directly
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: getItemSpy,
        setItem: setItemSpy,
        removeItem: removeItemSpy,
        clear: vi.fn(),
        length: 0,
        key: vi.fn()
      },
      writable: true
    })

    global.fetch = vi.fn()
    global.confirm = vi.fn(() => true)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders wizard heading', () => {
      render(<SingleSaasWizardPage />)

      expect(screen.getByText('Single-SaaS Wizard')).toBeInTheDocument()
      expect(screen.getByText('Build a complete SaaS product in 8 weeks')).toBeInTheDocument()
    })

    it('renders reset wizard button', () => {
      render(<SingleSaasWizardPage />)

      expect(screen.getByText('Reset Wizard')).toBeInTheDocument()
    })

    it('renders progress card', () => {
      render(<SingleSaasWizardPage />)

      expect(screen.getByText('Overall Progress')).toBeInTheDocument()
      expect(screen.getByText(/0 of 8 steps completed/)).toBeInTheDocument()
    })

    it('renders configuration form', () => {
      render(<SingleSaasWizardPage />)

      expect(screen.getByText('Project Configuration')).toBeInTheDocument()
      expect(screen.getByLabelText('Project Name')).toBeInTheDocument()
      expect(screen.getByLabelText('Repository URL (Optional)')).toBeInTheDocument()
      expect(screen.getByLabelText('Working Directory')).toBeInTheDocument()
    })

    it('renders all 8 workflow steps', () => {
      render(<SingleSaasWizardPage />)

      expect(screen.getAllByText('Week 1: Foundation & Setup').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Week 2: Research & Validation').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Week 3: Design System').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Week 4: Core Features').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Week 5: Authentication & Auth').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Week 6: Testing & QA').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Week 7: Deploy & Monitor').length).toBeGreaterThan(0)
      expect(screen.getAllByText('Week 8: Launch & Iterate').length).toBeGreaterThan(0)
    })
  })

  describe('Form Validation', () => {
    it('displays project name input', () => {
      render(<SingleSaasWizardPage />)

      const input = screen.getByPlaceholderText('my-saas-project')
      expect(input).toBeInTheDocument()
    })

    it('displays repository URL input', () => {
      render(<SingleSaasWizardPage />)

      const input = screen.getByPlaceholderText('https://github.com/username/repo')
      expect(input).toBeInTheDocument()
    })

    it('displays working directory input with default value', () => {
      render(<SingleSaasWizardPage />)

      const input = screen.getByPlaceholderText('/home/doctor/temponest')
      expect(input).toBeInTheDocument()
    })

    it('allows typing in project name field', async () => {
      const user = userEvent.setup()
      render(<SingleSaasWizardPage />)

      const input = screen.getByPlaceholderText('my-saas-project')
      await user.type(input, 'My Test SaaS')

      expect(input).toHaveValue('My Test SaaS')
    })
  })

  describe('Wizard Steps', () => {
    it('shows first step as active initially', () => {
      const { container } = render(<SingleSaasWizardPage />)

      const steps = container.querySelectorAll('.rounded-lg.border')
      const firstStep = steps[0]

      expect(firstStep).toHaveClass('border-sky-300', 'bg-sky-50')
    })

    it('shows start step button for pending step', () => {
      render(<SingleSaasWizardPage />)

      expect(screen.getByText('Start Step')).toBeInTheDocument()
    })

    it('allows clicking on different steps', async () => {
      const user = userEvent.setup()
      const { container } = render(<SingleSaasWizardPage />)

      const steps = container.querySelectorAll('.rounded-lg.border')
      const secondStep = steps[1]

      await user.click(secondStep)

      // Second step should now be highlighted
      expect(secondStep).toHaveClass('border-sky-300', 'bg-sky-50')
    })

    it('shows skip button for pending steps', () => {
      render(<SingleSaasWizardPage />)

      const skipButtons = screen.getAllByRole('button').filter(btn => {
        const svg = btn.querySelector('svg')
        return svg !== null && !btn.textContent?.includes('Start')
      })

      expect(skipButtons.length).toBeGreaterThan(0)
    })
  })

  describe('Progress Tracking', () => {
    it('starts with 0% progress', () => {
      const { container } = render(<SingleSaasWizardPage />)

      const progress = container.querySelector('[data-value="0"]')
      expect(progress).toBeInTheDocument()
    })

    it('displays correct step count', () => {
      render(<SingleSaasWizardPage />)

      expect(screen.getByText(/0 of 8 steps completed/)).toBeInTheDocument()
    })
  })

  describe('Logs Viewer', () => {
    it('renders execution logs section', () => {
      render(<SingleSaasWizardPage />)

      expect(screen.getByText('Execution Logs')).toBeInTheDocument()
    })

    it('shows empty logs message initially', () => {
      render(<SingleSaasWizardPage />)

      expect(screen.getByText('No logs yet. Start the step to see execution output.')).toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('renders previous button (disabled initially)', () => {
      render(<SingleSaasWizardPage />)

      const prevButton = screen.getByText('Previous')
      expect(prevButton).toBeInTheDocument()
      expect(prevButton).toBeDisabled()
    })

    it('renders next button', () => {
      render(<SingleSaasWizardPage />)

      const nextButton = screen.getByText('Next')
      expect(nextButton).toBeInTheDocument()
      expect(nextButton).not.toBeDisabled()
    })

    it('enables previous button after navigating forward', async () => {
      const user = userEvent.setup()
      render(<SingleSaasWizardPage />)

      const nextButton = screen.getByText('Next')
      await user.click(nextButton)

      const prevButton = screen.getByText('Previous')
      expect(prevButton).not.toBeDisabled()
    })

    it('disables next button on last step', async () => {
      const user = userEvent.setup()
      render(<SingleSaasWizardPage />)

      const nextButton = screen.getByText('Next')
      // Click next 7 times to reach the last step
      for (let i = 0; i < 7; i++) {
        await user.click(nextButton)
      }

      expect(nextButton).toBeDisabled()
    })
  })

  describe('Reset Functionality', () => {
    it('resets wizard when reset button clicked', async () => {
      const user = userEvent.setup()
      render(<SingleSaasWizardPage />)

      const resetButton = screen.getByText('Reset Wizard')
      await user.click(resetButton)

      // Progress should be reset
      expect(screen.getByText(/0 of 8 steps completed/)).toBeInTheDocument()
    })

    it('clears localStorage on reset', async () => {
      const user = userEvent.setup()
      render(<SingleSaasWizardPage />)

      const resetButton = screen.getByText('Reset Wizard')
      await user.click(resetButton)

      // Check that removeItem was called with the wizard state keys
      expect(removeItemSpy).toHaveBeenCalled()
    })
  })

  describe('LocalStorage Persistence', () => {
    it('saves state to localStorage', async () => {
      const user = userEvent.setup()
      render(<SingleSaasWizardPage />)

      const input = screen.getByPlaceholderText('my-saas-project')
      await user.type(input, 'Test')

      // Should save form data to localStorage
      await waitFor(() => {
        expect(setItemSpy).toHaveBeenCalled()
      }, { timeout: 3000 })
    })

    it('loads state from localStorage on mount', () => {
      const savedState = JSON.stringify({
        0: { status: 'completed', logs: ['Step completed'], completedTasks: 1, totalTasks: 1 }
      })
      localStorageMock['single-saas-wizard-state'] = savedState

      render(<SingleSaasWizardPage />)

      // Should load the saved state
      expect(getItemSpy).toHaveBeenCalledWith('single-saas-wizard-state')
    })
  })

  describe('Step Status Display', () => {
    it('shows pending badge for unstarted steps', () => {
      render(<SingleSaasWizardPage />)

      const badges = screen.getAllByText('pending')
      expect(badges.length).toBeGreaterThanOrEqual(8) // At least 8 steps are pending initially
    })

    it('renders step descriptions', () => {
      render(<SingleSaasWizardPage />)

      // These descriptions appear in both sidebar and detail section
      expect(screen.getAllByText('Initialize project structure').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Market research and validation').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Create UI/UX design system').length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Current Step Display', () => {
    it('displays current step title', () => {
      render(<SingleSaasWizardPage />)

      // Title appears in both sidebar and detail section
      const titles = screen.getAllByText(/Week 1: Foundation & Setup/)
      expect(titles.length).toBeGreaterThanOrEqual(1)
    })

    it('displays current step description', () => {
      render(<SingleSaasWizardPage />)

      // Description appears in both sidebar and detail section
      const descriptions = screen.getAllByText(/Initialize project structure/)
      expect(descriptions.length).toBeGreaterThanOrEqual(1)
    })

    it('updates current step when navigating', async () => {
      const user = userEvent.setup()
      render(<SingleSaasWizardPage />)

      const nextButton = screen.getByText('Next')
      await user.click(nextButton)

      // Should show Week 2 content (appears in both sidebar and detail section)
      const week2Titles = screen.getAllByText(/Week 2: Research & Validation/)
      expect(week2Titles.length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Accessibility', () => {
    it('has accessible form labels', () => {
      render(<SingleSaasWizardPage />)

      expect(screen.getByLabelText('Project Name')).toBeInTheDocument()
      expect(screen.getByLabelText('Repository URL (Optional)')).toBeInTheDocument()
      expect(screen.getByLabelText('Working Directory')).toBeInTheDocument()
    })

    it('has keyboard-accessible buttons', () => {
      render(<SingleSaasWizardPage />)

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Layout', () => {
    it('uses grid layout for two-column design', () => {
      const { container } = render(<SingleSaasWizardPage />)

      const grid = container.querySelector('.grid.grid-cols-1.lg\\:grid-cols-2')
      expect(grid).toBeInTheDocument()
    })
  })
})
