import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import FactoryWizardPage from '@/app/wizards/factory/page'

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

describe('FactoryWizardPage', () => {
  let localStorageMock: { [key: string]: string }

  beforeEach(() => {
    localStorageMock = {}

    global.Storage.prototype.getItem = vi.fn((key: string) => localStorageMock[key] || null)
    global.Storage.prototype.setItem = vi.fn((key: string, value: string) => {
      localStorageMock[key] = value
    })
    global.Storage.prototype.removeItem = vi.fn((key: string) => {
      delete localStorageMock[key]
    })

    global.fetch = vi.fn()
    global.confirm = vi.fn(() => true)
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders wizard heading', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText('Factory Setup Wizard')).toBeInTheDocument()
      expect(screen.getByText('Initialize your autonomous SaaS factory')).toBeInTheDocument()
    })

    it('renders reset wizard button', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText('Reset Wizard')).toBeInTheDocument()
    })

    it('renders progress card', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText('Factory Setup Progress')).toBeInTheDocument()
      expect(screen.getByText(/0 of 4 phases completed/)).toBeInTheDocument()
    })

    it('renders configuration form', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText('Factory Configuration')).toBeInTheDocument()
      expect(screen.getByLabelText('Factory Name')).toBeInTheDocument()
      expect(screen.getByLabelText('GitHub Organization')).toBeInTheDocument()
      expect(screen.getByLabelText('Coolify URL')).toBeInTheDocument()
      expect(screen.getByLabelText('Agent Count')).toBeInTheDocument()
      expect(screen.getByLabelText('Working Directory')).toBeInTheDocument()
    })

    it('renders all 4 setup phases', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText('Week 1: Infrastructure & Agents')).toBeInTheDocument()
      expect(screen.getByText('Week 2: Pipeline & Automation')).toBeInTheDocument()
      expect(screen.getByText('Week 3: Templates & Patterns')).toBeInTheDocument()
      expect(screen.getByText('Week 4: Monitoring & Scaling')).toBeInTheDocument()
    })
  })

  describe('Form Fields', () => {
    it('displays factory name input with default value', () => {
      render(<FactoryWizardPage />)

      const input = screen.getByPlaceholderText('SaaS-Empire-Factory')
      expect(input).toBeInTheDocument()
      expect(input).toHaveValue('SaaS-Empire-Factory')
    })

    it('displays GitHub organization input', () => {
      render(<FactoryWizardPage />)

      const input = screen.getByPlaceholderText('your-org')
      expect(input).toBeInTheDocument()
    })

    it('displays Coolify URL input', () => {
      render(<FactoryWizardPage />)

      const input = screen.getByPlaceholderText('https://coolify.yourdomain.com')
      expect(input).toBeInTheDocument()
    })

    it('displays agent count input with default value of 7', () => {
      render(<FactoryWizardPage />)

      const input = screen.getByPlaceholderText('7')
      expect(input).toBeInTheDocument()
    })

    it('allows typing in form fields', async () => {
      const user = userEvent.setup()
      render(<FactoryWizardPage />)

      const githubInput = screen.getByPlaceholderText('your-org')
      await user.type(githubInput, 'my-company')

      expect(githubInput).toHaveValue('my-company')
    })

    it('validates agent count min/max', () => {
      render(<FactoryWizardPage />)

      const input = screen.getByPlaceholderText('7')
      expect(input).toHaveAttribute('min', '1')
      expect(input).toHaveAttribute('max', '10')
    })
  })

  describe('Phase Display', () => {
    it('shows first phase as active initially', () => {
      const { container } = render(<FactoryWizardPage />)

      const phases = container.querySelectorAll('.rounded-lg.border')
      const firstPhase = phases[0]

      expect(firstPhase).toHaveClass('border-sky-300', 'bg-sky-50')
    })

    it('shows start phase button for pending phase', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText('Start Phase')).toBeInTheDocument()
    })

    it('displays phase tasks', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText('Phase Tasks:')).toBeInTheDocument()
      expect(screen.getByText('Configure PostgreSQL')).toBeInTheDocument()
      expect(screen.getByText('Deploy Coolify')).toBeInTheDocument()
      expect(screen.getByText('Set up 7 core agents')).toBeInTheDocument()
      expect(screen.getByText('Configure message queue')).toBeInTheDocument()
    })

    it('allows clicking on different phases', async () => {
      const user = userEvent.setup()
      const { container } = render(<FactoryWizardPage />)

      const phases = container.querySelectorAll('.rounded-lg.border')
      const secondPhase = phases[1]

      await user.click(secondPhase)

      expect(secondPhase).toHaveClass('border-sky-300', 'bg-sky-50')
    })

    it('shows task progress indicators', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText(/Tasks: 0\//)).toBeInTheDocument()
    })
  })

  describe('Progress Tracking', () => {
    it('starts with 0% progress', () => {
      const { container } = render(<FactoryWizardPage />)

      const progress = container.querySelector('[data-value="0"]')
      expect(progress).toBeInTheDocument()
    })

    it('displays correct phase count', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText(/0 of 4 phases completed/)).toBeInTheDocument()
    })
  })

  describe('Execution Logs', () => {
    it('renders execution logs section', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText('Execution Logs')).toBeInTheDocument()
    })

    it('shows empty logs message initially', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText('No logs yet. Start the phase to see execution output.')).toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('renders previous button (disabled initially)', () => {
      render(<FactoryWizardPage />)

      const prevButton = screen.getByText('Previous')
      expect(prevButton).toBeInTheDocument()
      expect(prevButton).toBeDisabled()
    })

    it('renders next button', () => {
      render(<FactoryWizardPage />)

      const nextButton = screen.getByText('Next')
      expect(nextButton).toBeInTheDocument()
      expect(nextButton).not.toBeDisabled()
    })

    it('enables previous button after navigating forward', async () => {
      const user = userEvent.setup()
      render(<FactoryWizardPage />)

      const nextButton = screen.getByText('Next')
      await user.click(nextButton)

      const prevButton = screen.getByText('Previous')
      expect(prevButton).not.toBeDisabled()
    })

    it('disables next button on last phase', async () => {
      const user = userEvent.setup()
      render(<FactoryWizardPage />)

      const nextButton = screen.getByText('Next')
      // Click next 3 times to reach the last phase
      for (let i = 0; i < 3; i++) {
        await user.click(nextButton)
      }

      expect(nextButton).toBeDisabled()
    })
  })

  describe('Reset Functionality', () => {
    it('resets wizard when reset button clicked', async () => {
      const user = userEvent.setup()
      render(<FactoryWizardPage />)

      const resetButton = screen.getByText('Reset Wizard')
      await user.click(resetButton)

      expect(screen.getByText(/0 of 4 phases completed/)).toBeInTheDocument()
    })

    it('clears localStorage on reset', async () => {
      const user = userEvent.setup()
      const removeItemSpy = vi.spyOn(Storage.prototype, 'removeItem')

      render(<FactoryWizardPage />)

      const resetButton = screen.getByText('Reset Wizard')
      await user.click(resetButton)

      expect(removeItemSpy).toHaveBeenCalled()
    })
  })

  describe('LocalStorage Persistence', () => {
    it('saves state to localStorage', async () => {
      const user = userEvent.setup()
      const setItemSpy = vi.spyOn(Storage.prototype, 'setItem')

      render(<FactoryWizardPage />)

      const input = screen.getByPlaceholderText('your-org')
      await user.type(input, 'test')

      await waitFor(() => {
        expect(setItemSpy).toHaveBeenCalled()
      })
    })

    it('loads state from localStorage on mount', () => {
      const savedState = JSON.stringify({
        0: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 }
      })
      localStorageMock['factory-wizard-state'] = savedState

      render(<FactoryWizardPage />)

      expect(Storage.prototype.getItem).toHaveBeenCalledWith('factory-wizard-state')
    })
  })

  describe('Phase Status', () => {
    it('shows pending badge for unstarted phases', () => {
      render(<FactoryWizardPage />)

      const badges = screen.getAllByText('pending')
      expect(badges.length).toBe(4) // All 4 phases are pending initially
    })

    it('renders phase descriptions', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText('Set up core infrastructure and autonomous agents')).toBeInTheDocument()
      expect(screen.getByText('Build automated SaaS generation pipeline')).toBeInTheDocument()
      expect(screen.getByText('Design reusable SaaS templates')).toBeInTheDocument()
      expect(screen.getByText('Implement observability and scaling')).toBeInTheDocument()
    })
  })

  describe('Current Phase Display', () => {
    it('displays current phase title', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText(/Week 1: Infrastructure & Agents/)).toBeInTheDocument()
    })

    it('displays current phase description', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByText(/Set up core infrastructure and autonomous agents/)).toBeInTheDocument()
    })

    it('updates current phase when navigating', async () => {
      const user = userEvent.setup()
      render(<FactoryWizardPage />)

      const nextButton = screen.getByText('Next')
      await user.click(nextButton)

      expect(screen.getByText(/Week 2: Pipeline & Automation/)).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has accessible form labels', () => {
      render(<FactoryWizardPage />)

      expect(screen.getByLabelText('Factory Name')).toBeInTheDocument()
      expect(screen.getByLabelText('GitHub Organization')).toBeInTheDocument()
      expect(screen.getByLabelText('Coolify URL')).toBeInTheDocument()
      expect(screen.getByLabelText('Agent Count')).toBeInTheDocument()
      expect(screen.getByLabelText('Working Directory')).toBeInTheDocument()
    })

    it('has keyboard-accessible buttons', () => {
      render(<FactoryWizardPage />)

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toBeInTheDocument()
      })
    })
  })

  describe('Responsive Layout', () => {
    it('uses grid layout for two-column design', () => {
      const { container } = render(<FactoryWizardPage />)

      const grid = container.querySelector('.grid.grid-cols-1.lg\\:grid-cols-2')
      expect(grid).toBeInTheDocument()
    })

    it('uses two-column grid for form fields', () => {
      const { container } = render(<FactoryWizardPage />)

      const grids = container.querySelectorAll('.grid.grid-cols-2')
      expect(grids.length).toBeGreaterThan(0)
    })
  })

  describe('Skip Functionality', () => {
    it('shows skip button for pending phases', () => {
      render(<FactoryWizardPage />)

      const skipButtons = screen.getAllByRole('button').filter(btn => {
        const svg = btn.querySelector('svg')
        return svg !== null && !btn.textContent?.includes('Start')
      })

      expect(skipButtons.length).toBeGreaterThan(0)
    })
  })

  describe('Setup Phases Content', () => {
    it('displays all tasks for each phase', () => {
      render(<FactoryWizardPage />)

      // Phase 1 tasks
      expect(screen.getByText('Configure PostgreSQL')).toBeInTheDocument()
      expect(screen.getByText('Deploy Coolify')).toBeInTheDocument()
    })

    it('shows 4 tasks for phase 1', () => {
      render(<FactoryWizardPage />)

      const phaseTasksSection = screen.getByText('Phase Tasks:').parentElement
      const tasks = phaseTasksSection?.querySelectorAll('.flex.items-center.gap-2')
      expect(tasks?.length).toBe(4)
    })
  })
})
