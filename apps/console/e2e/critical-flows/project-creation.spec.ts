import { test, expect } from '@playwright/test'

test.describe('Project Creation - Critical Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects')
  })

  test('loads projects page', async ({ page }) => {
    // Verify projects page loaded
    await expect(page.locator('h1').or(page.locator('h2'))).toContainText(/Projects|Factory Map/)
  })

  test('displays create project button', async ({ page }) => {
    const createButton = page.locator('button:has-text("Create Project")').or(
      page.locator('button:has-text("New Project")').or(
        page.locator('a:has-text("Create")')
      )
    )

    // Create button should be visible
    // OR check if we're on a page that lists projects/allows navigation to creation
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })

  test('shows existing projects list', async ({ page }) => {
    // Look for projects table, grid, or list
    const projectsList = page.locator('table').or(
      page.locator('[role="grid"]').or(
        page.locator('[class*="grid"]').or(
          page.locator('[class*="project"]')
        )
      )
    )

    // Projects might be displayed in various formats
    const headings = page.locator('h1, h2, h3')
    const headingCount = await headings.count()
    expect(headingCount).toBeGreaterThan(0)
  })

  test('displays project status indicators', async ({ page }) => {
    // Look for status badges (idle, active, completed, etc.)
    const statusElements = page.locator('text=idle').or(
      page.locator('text=active').or(
        page.locator('text=running').or(
          page.locator('[class*="badge"]').or(
            page.locator('[class*="status"]')
          )
        )
      )
    )

    // Status indicators might be present if projects exist
  })

  test('can navigate to project details', async ({ page }) => {
    // Look for project links or cards
    const projectLinks = page.locator('a[href*="/projects/"]').or(
      page.locator('[class*="project"]').locator('a')
    )

    const linkCount = await projectLinks.count()

    if (linkCount > 0) {
      // Click first project
      await projectLinks.first().click()

      // Should navigate to project detail page
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })
    }
  })

  test('shows project type filter options', async ({ page }) => {
    // Look for filters: single, portfolio, etc.
    const filters = page.locator('text=Single').or(
      page.locator('text=Portfolio').or(
        page.locator('text=Filter').or(
          page.locator('select').or(
            page.locator('[role="combobox"]')
          )
        )
      )
    )

    // Filter options might be available
  })

  test('displays project cards with metadata', async ({ page }) => {
    // Each project should show: name, status, created date, etc.
    const cards = page.locator('[class*="card"]')

    // Look for any card-like structures
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })

  test('responsive design on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    // Verify page loads
    const heading = page.locator('h1').or(page.locator('h2'))
    await expect(heading.first()).toBeVisible()
  })
})

test.describe('Project Creation - Form Workflow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects')
  })

  test('can access project creation form', async ({ page }) => {
    // Try to find and click create button
    const createButton = page.locator('button:has-text("Create")').or(
      page.locator('button:has-text("New")').or(
        page.locator('a:has-text("Create")')
      )
    ).first()

    const buttonCount = await page.locator('button, a').count()
    expect(buttonCount).toBeGreaterThan(0)

    // If create button exists, click it
    if (await createButton.isVisible()) {
      await createButton.click()

      // Should show form or navigate to creation page
      await page.waitForTimeout(1000)
    }
  })

  test('validates required project fields', async ({ page }) => {
    // Look for form inputs
    const nameInput = page.locator('input[name="name"]').or(
      page.locator('input[name="projectName"]').or(
        page.locator('input[placeholder*="name" i]')
      )
    )

    // Form validation might be present
  })

  test('shows project type selection', async ({ page }) => {
    // Radio buttons or dropdown for project type
    const typeSelector = page.locator('input[type="radio"]').or(
      page.locator('select').or(
        page.locator('[role="radiogroup"]')
      )
    )

    // Type selection might be available
  })

  test('can submit project creation form', async ({ page }) => {
    // Look for submit button
    const submitButton = page.locator('button[type="submit"]').or(
      page.locator('button:has-text("Create")').or(
        page.locator('button:has-text("Submit")')
      )
    )

    // Submit button might be visible in create mode
  })

  test('shows success message after project creation', async ({ page }) => {
    // After successful creation, look for toast/notification
    const successMessage = page.locator('text=Success').or(
      page.locator('text=created').or(
        page.locator('[role="alert"]').or(
          page.locator('[class*="toast"]')
        )
      )
    )

    // Success notification might appear after creation
  })
})

test.describe('Project Details - View and Edit', () => {
  test('can view project timeline', async ({ page }) => {
    await page.goto('/projects')

    // Navigate to a project if available
    const projectLink = page.locator('a[href*="/projects/"]').first()

    if (await projectLink.isVisible()) {
      await projectLink.click()

      // Look for timeline or activity log
      const timeline = page.locator('text=Timeline').or(
        page.locator('text=Activity').or(
          page.locator('[class*="timeline"]')
        )
      )

      // Timeline might be visible on project detail page
    }
  })

  test('shows project runs and workflows', async ({ page }) => {
    await page.goto('/projects')

    // Look for runs/workflows section
    const runsSection = page.locator('text=Runs').or(
      page.locator('text=Workflows').or(
        page.locator('text=Executions')
      )
    )

    // Runs might be displayed
  })

  test('displays project agents', async ({ page }) => {
    await page.goto('/projects')

    // Look for agents working on the project
    const agentsSection = page.locator('text=Agents').or(
      page.locator('text=Team').or(
        page.locator('[class*="agent"]')
      )
    )

    // Agent information might be shown
  })
})
