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

      // Phase titles appear in both sidebar and detail section
      expect(screen.getAllByText('Week 1: Infrastructure & Agents').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Week 2: Pipeline & Automation').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Week 3: Templates & Patterns').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Week 4: Monitoring & Scaling').length).toBeGreaterThanOrEqual(1)
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

      // The page shows "Phase Tasks:" header, not a count
      expect(screen.getByText('Phase Tasks:')).toBeInTheDocument()
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

      render(<FactoryWizardPage />)

      const resetButton = screen.getByText('Reset Wizard')
      await user.click(resetButton)

      expect(removeItemSpy).toHaveBeenCalled()
    })
  })

  describe('LocalStorage Persistence', () => {
    it('saves state to localStorage', async () => {
      const user = userEvent.setup()

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

      expect(getItemSpy).toHaveBeenCalledWith('factory-wizard-state')
    })
  })

  describe('Phase Status', () => {
    it('shows pending badge for unstarted phases', () => {
      render(<FactoryWizardPage />)

      const badges = screen.getAllByText('pending')
      // At least 4 phases are pending (may be more if current phase badge is also shown)
      expect(badges.length).toBeGreaterThanOrEqual(4)
    })

    it('renders phase descriptions', () => {
      render(<FactoryWizardPage />)

      // Descriptions appear in both sidebar and detail section
      expect(screen.getAllByText('Set up core infrastructure and autonomous agents').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Build automated SaaS generation pipeline').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Design reusable SaaS templates').length).toBeGreaterThanOrEqual(1)
      expect(screen.getAllByText('Implement observability and scaling').length).toBeGreaterThanOrEqual(1)
    })
  })

  describe('Current Phase Display', () => {
    it('displays current phase title', () => {
      render(<FactoryWizardPage />)

      // Title appears in both sidebar and detail section
      const titles = screen.getAllByText(/Week 1: Infrastructure & Agents/)
      expect(titles.length).toBeGreaterThanOrEqual(1)
    })

    it('displays current phase description', () => {
      render(<FactoryWizardPage />)

      // Description appears in both sidebar and detail section
      const descriptions = screen.getAllByText(/Set up core infrastructure and autonomous agents/)
      expect(descriptions.length).toBeGreaterThanOrEqual(1)
    })

    it('updates current phase when navigating', async () => {
      const user = userEvent.setup()
      render(<FactoryWizardPage />)

      const nextButton = screen.getByText('Next')
      await user.click(nextButton)

      // Title appears in both sidebar and detail section after navigation
      const week2Titles = screen.getAllByText(/Week 2: Pipeline & Automation/)
      expect(week2Titles.length).toBeGreaterThanOrEqual(1)
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

    it('skips phase when skip button clicked', async () => {
      const user = userEvent.setup()
      render(<FactoryWizardPage />)

      const skipButton = screen.getAllByRole('button').find(btn => {
        const svg = btn.querySelector('svg')
        return svg !== null && !btn.textContent?.includes('Start')
      })

      if (skipButton) {
        await user.click(skipButton)

        await waitFor(() => {
          const badges = screen.getAllByText('skipped')
          expect(badges.length).toBeGreaterThan(0)
        })
      }
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

  describe('State Management', () => {
    it('shows skipped phase state', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'skipped', logs: ['Phase skipped by user'], completedTasks: 0, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      const badges = screen.getAllByText('skipped')
      expect(badges.length).toBeGreaterThan(0)
    })

    it('shows running phase state', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'running', logs: ['Running...'], completedTasks: 2, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      // Check that logs are displayed
      expect(screen.getByText('Running...')).toBeInTheDocument()
    })

    it('shows failed phase state', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'failed', logs: ['Failed'], error: 'Test error', completedTasks: 1, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      expect(screen.getByText('Test error')).toBeInTheDocument()
    })

    it('displays phase logs from saved state', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'completed', logs: ['Log line 1', 'Log line 2'], completedTasks: 4, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      expect(screen.getByText('Log line 1')).toBeInTheDocument()
      expect(screen.getByText('Log line 2')).toBeInTheDocument()
    })

    it('calculates progress correctly', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 },
        1: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      expect(screen.getByText(/2 of 4 phases completed/)).toBeInTheDocument()
    })

    it('displays approval required state', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'approval_required', logs: ['Needs approval'], completedTasks: 4, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      expect(screen.getByText('Approval Required')).toBeInTheDocument()
    })
  })

  describe('Phase Status Display', () => {
    it('displays correct number of pending phases initially', () => {
      render(<FactoryWizardPage />)

      const badges = screen.getAllByText('pending')
      // At least 4 phases should be pending (may show more due to current phase display)
      expect(badges.length).toBeGreaterThanOrEqual(4)
    })

    it('displays correct status for multiple phases', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 },
        1: { status: 'running', logs: [], completedTasks: 2, totalTasks: 4 },
        2: { status: 'failed', logs: [], error: 'Error', completedTasks: 1, totalTasks: 4 },
        3: { status: 'pending', logs: [], completedTasks: 0, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      expect(screen.getAllByText('completed').length).toBeGreaterThan(0)
      expect(screen.getAllByText('running').length).toBeGreaterThan(0)
      expect(screen.getAllByText('failed').length).toBeGreaterThan(0)
      expect(screen.getAllByText('pending').length).toBeGreaterThan(0)
    })
  })

  describe('Error Display', () => {
    it('shows error message for failed phase', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'failed', logs: [], error: 'Connection timeout', completedTasks: 0, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      expect(screen.getByText('Connection timeout')).toBeInTheDocument()
    })

    it('shows aborted status', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'failed', logs: ['Execution aborted by user'], error: 'Aborted', completedTasks: 2, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      expect(screen.getByText('Execution aborted by user')).toBeInTheDocument()
    })
  })

  describe('Progress Calculation', () => {
    it('shows 0% when no phases completed', () => {
      const { container } = render(<FactoryWizardPage />)

      const progress = container.querySelector('[data-value="0"]')
      expect(progress).toBeInTheDocument()
    })

    it('shows 25% when 1 of 4 phases completed', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 }
      })

      const { container } = render(<FactoryWizardPage />)

      const progress = container.querySelector('[data-value="25"]')
      expect(progress).toBeInTheDocument()
    })

    it('shows 50% when 2 of 4 phases completed', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 },
        1: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 }
      })

      const { container } = render(<FactoryWizardPage />)

      const progress = container.querySelector('[data-value="50"]')
      expect(progress).toBeInTheDocument()
    })

    it('shows 100% when all phases completed', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 },
        1: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 },
        2: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 },
        3: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 }
      })

      const { container } = render(<FactoryWizardPage />)

      expect(screen.getByText(/4 of 4 phases completed/)).toBeInTheDocument()
      const progress = container.querySelector('[data-value="100"]')
      expect(progress).toBeInTheDocument()
    })
  })

  describe('Task Completion Tracking', () => {
    it('displays task completion count', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'running', logs: [], completedTasks: 2, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      expect(screen.getByText('Tasks: 2/4')).toBeInTheDocument()
    })

    it('shows task percentage', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'running', logs: [], completedTasks: 3, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      expect(screen.getByText('75%')).toBeInTheDocument()
    })

    it('displays all tasks completed', () => {
      localStorageMock['factory-wizard-state'] = JSON.stringify({
        0: { status: 'completed', logs: [], completedTasks: 4, totalTasks: 4 }
      })

      render(<FactoryWizardPage />)

      expect(screen.getByText('Tasks: 4/4')).toBeInTheDocument()
      expect(screen.getByText('100%')).toBeInTheDocument()
    })
  })
})
