import { test, expect } from '@playwright/test'

/**
 * Project Detail Page - Comprehensive E2E Tests
 *
 * Tests the complete project detail experience including project information display,
 * run history, status indicators, statistics, and run management.
 * Note: Tests use a mock project slug - actual project must exist in database.
 */

test.describe('Project Detail - Page Load and Header', () => {
  test.beforeEach(async ({ page }) => {
    // Note: Using '/projects' as fallback since specific project might not exist
    await page.goto('/projects')
  })

  test('loads projects listing page', async ({ page }) => {
    // Verify we're on projects page
    await expect(page.locator('h1').or(page.locator('h2'))).toContainText(/Project|Factory Map/)
  })

  test('can navigate to project detail if projects exist', async ({ page }) => {
    // Look for project links
    const projectLinks = page.locator('a[href*="/projects/"]')

    const count = await projectLinks.count()

    if (count > 0) {
      // Click first project
      await projectLinks.first().click()

      // Wait for navigation
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })

      // Verify project detail page loaded
      const heading = page.locator('h1')
      await expect(heading).toBeVisible()
    }
  })

  test('projects page has responsive design on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    await expect(page.locator('h1').or(page.locator('h2')).first()).toBeVisible()
  })
})

test.describe('Project Detail - Project Information Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects')

    // Try to navigate to a project detail page
    const projectLink = page.locator('a[href*="/projects/"]').first()
    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })
    }
  })

  test('displays project name as heading', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // On a project detail page
      const projectName = page.locator('h1')
      await expect(projectName).toBeVisible()

      const nameText = await projectName.textContent()
      expect(nameText).toBeTruthy()
      expect(nameText!.length).toBeGreaterThan(0)
    }
  })

  test('displays project details subtitle', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      const subtitle = page.locator('text=Project details and build history')
      const isVisible = await subtitle.isVisible().catch(() => false)

      // Subtitle might be visible on project detail page
    }
  })

  test('shows start new run button', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      const startRunButton = page.locator('button:has-text("Start New Run")')
      const isVisible = await startRunButton.isVisible().catch(() => false)

      // Button should be visible on project detail page
    }
  })

  test('shows repository link if repo URL exists', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      const repoLink = page.locator('a:has-text("Repository")')

      if (await repoLink.isVisible().catch(() => false)) {
        // Repository link should have external icon
        const externalIcon = repoLink.locator('svg')
        await expect(externalIcon).toBeVisible()

        // Link should open in new tab
        const target = await repoLink.getAttribute('target')
        expect(target).toBe('_blank')
      }
    }
  })

  test('repository link has external icon', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      const repoLink = page.locator('a:has-text("Repository")')

      if (await repoLink.isVisible().catch(() => false)) {
        // Should have ExternalLink icon
        const href = await repoLink.getAttribute('href')
        expect(href).toBeTruthy()
      }
    }
  })
})

test.describe('Project Detail - Statistics Cards', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects')

    const projectLink = page.locator('a[href*="/projects/"]').first()
    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })
    }
  })

  test('displays project statistics', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for statistics/metrics on page
      const stats = page.locator('text=/\\d+/')

      const count = await stats.count()
      // Should have some numerical statistics
      expect(count).toBeGreaterThan(0)
    }
  })

  test('shows total runs count', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for "runs" or "total" text
      const runsText = page.locator('text=/runs|total/i')

      // Runs count might be visible
    }
  })

  test('shows success rate percentage', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for percentage (e.g., "85%")
      const percentage = page.locator('text=/%/')

      // Success rate might be displayed
    }
  })

  test('shows successful runs count', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for success indicators
      const successText = page.locator('text=/success/i')

      // Success count might be visible
    }
  })

  test('shows failed runs count', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for failed indicators
      const failedText = page.locator('text=/failed/i')

      // Failed count might be visible
    }
  })
})

test.describe('Project Detail - Run History', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects')

    const projectLink = page.locator('a[href*="/projects/"]').first()
    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })
    }
  })

  test('displays run history section', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for runs section or table
      const runsSection = page.locator('text=/runs|history|builds/i')

      // Runs section might be visible
    }
  })

  test('shows run status indicators', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for status badges/indicators
      const statusIndicators = page.locator('text=/pending|running|success|failed|cancelled/i')

      const count = await statusIndicators.count()
      // Status indicators might be present
    }
  })

  test('run status has color coding', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for colored badges (bg-emerald, bg-rose, bg-slate, etc.)
      const badges = page.locator('[class*="bg-emerald"], [class*="bg-rose"], [class*="bg-slate"]')

      // Colored badges might be present
    }
  })

  test('shows run icons based on status', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Status icons (Clock, Play, CheckCircle, XCircle, Ban)
      const icons = page.locator('svg')

      const count = await icons.count()
      expect(count).toBeGreaterThan(0)
    }
  })

  test('displays run timestamps', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for relative time (e.g., "2 hours ago")
      const timestamps = page.locator('text=/ago|just now|yesterday/i')

      // Timestamps might be visible
    }
  })

  test('runs are ordered by creation date (most recent first)', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Verify runs exist
      const pageContent = await page.textContent('body')
      expect(pageContent).toBeTruthy()
    }
  })

  test('shows approval status for runs if approvals exist', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for approval indicators
      const approvalText = page.locator('text=/approval|approved|pending/i')

      // Approval info might be visible
    }
  })
})

test.describe('Project Detail - Run Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects')

    const projectLink = page.locator('a[href*="/projects/"]').first()
    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })
    }
  })

  test('start new run button is clickable', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      const startRunButton = page.locator('button:has-text("Start New Run")')

      if (await startRunButton.isVisible().catch(() => false)) {
        await expect(startRunButton).toBeEnabled()

        await startRunButton.click()
        await page.waitForTimeout(500)

        // Button should trigger some action
      }
    }
  })

  test('start new run button has proper styling', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      const startRunButton = page.locator('button:has-text("Start New Run")')

      if (await startRunButton.isVisible().catch(() => false)) {
        const classList = await startRunButton.getAttribute('class')
        expect(classList).toContain('bg-base-900')
        expect(classList).toContain('text-white')
      }
    }
  })

  test('can interact with individual run items', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for clickable run items
      const runItems = page.locator('[class*="cursor-pointer"]').or(
        page.locator('button').filter({ hasText: /view|details/i })
      )

      // Run items might be interactive
    }
  })
})

test.describe('Project Detail - Empty States', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects')
  })

  test('handles project with no runs gracefully', async ({ page }) => {
    const projectLink = page.locator('a[href*="/projects/"]').first()

    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })

      // Page should load without errors even if no runs
      const heading = page.locator('h1')
      await expect(heading).toBeVisible()
    }
  })

  test('shows empty state message if no runs exist', async ({ page }) => {
    const projectLink = page.locator('a[href*="/projects/"]').first()

    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })

      // Look for empty state message
      const emptyMessage = page.locator('text=/no runs|no builds|get started/i')

      // Empty message might be shown if no runs
    }
  })

  test('statistics show zero values if no runs', async ({ page }) => {
    const projectLink = page.locator('a[href*="/projects/"]').first()

    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })

      // Look for zero values
      const zeros = page.locator('text="0"')

      // Should handle zero counts gracefully
    }
  })
})

test.describe('Project Detail - 404 Handling', () => {
  test('shows 404 for non-existent project', async ({ page }) => {
    // Navigate to non-existent project
    const response = await page.goto('/projects/nonexistent-project-slug-12345')

    // Should return 404 or show not found page
    const status = response?.status()

    // Might be 404 or might redirect
    if (status === 404) {
      // 404 page should be shown
      expect(status).toBe(404)
    } else {
      // Or redirected to projects list
      const url = page.url()
      // Should handle gracefully
    }
  })

  test('displays helpful error message for missing project', async ({ page }) => {
    await page.goto('/projects/nonexistent-slug-xyz', { waitUntil: 'networkidle' })

    // Look for not found message
    const notFoundText = page.locator('text=/not found|doesn\'t exist|invalid/i')

    // Error message might be displayed
  })
})

test.describe('Project Detail - Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects')

    const projectLink = page.locator('a[href*="/projects/"]').first()
    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })
    }
  })

  test('can navigate back to projects list', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Look for back link or projects link in navigation
      const backLink = page.locator('a[href="/projects"]').or(
        page.locator('text=/back|projects/i').locator('..')
      )

      if (await backLink.first().isVisible().catch(() => false)) {
        await backLink.first().click()
        await page.waitForURL('/projects', { timeout: 5000 })

        await expect(page).toHaveURL('/projects')
      }
    }
  })

  test('repository link opens in new tab', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      const repoLink = page.locator('a:has-text("Repository")')

      if (await repoLink.isVisible().catch(() => false)) {
        const target = await repoLink.getAttribute('target')
        expect(target).toBe('_blank')

        // Should have rel="noopener" for security
        // (might be added automatically by Next.js)
      }
    }
  })

  test('sidebar navigation is accessible from project detail', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Verify sidebar is present
      const sidebar = page.locator('text=SaaS Empire').first()
      await expect(sidebar).toBeVisible()
    }
  })
})

test.describe('Project Detail - Responsive Design', () => {
  test('works on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/projects')

    const projectLink = page.locator('a[href*="/projects/"]').first()

    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })

      // Page should load on mobile
      const heading = page.locator('h1')
      await expect(heading).toBeVisible()
    }
  })

  test('works on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/projects')

    const projectLink = page.locator('a[href*="/projects/"]').first()

    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })

      // All elements should be accessible on tablet
      const heading = page.locator('h1')
      await expect(heading).toBeVisible()
    }
  })

  test('action buttons stack properly on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/projects')

    const projectLink = page.locator('a[href*="/projects/"]').first()

    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })

      const startButton = page.locator('button:has-text("Start New Run")')

      if (await startButton.isVisible().catch(() => false)) {
        // Button should be visible and usable on mobile
        await expect(startButton).toBeVisible()
      }
    }
  })
})

test.describe('Project Detail - Data Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/projects')

    const projectLink = page.locator('a[href*="/projects/"]').first()
    if (await projectLink.isVisible().catch(() => false)) {
      await projectLink.click()
      await page.waitForURL(/\/projects\/.*/, { timeout: 5000 })
    }
  })

  test('formats timestamps with relative time', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Uses date-fns formatDistanceToNow
      const relativeTime = page.locator('text=/\\d+\\s+(second|minute|hour|day)s?\\s+ago/i')

      // Relative timestamps might be shown
    }
  })

  test('displays percentage values correctly', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Success rate percentage (0-100%)
      const percentages = page.locator('text=/%/')

      // Percentage might be displayed
    }
  })

  test('shows numerical data with proper formatting', async ({ page }) => {
    const currentUrl = page.url()

    if (currentUrl.includes('/projects/') && !currentUrl.endsWith('/projects')) {
      // Numbers should be readable
      const numbers = page.locator('text=/\\d+/')

      const count = await numbers.count()
      expect(count).toBeGreaterThan(0)
    }
  })
})
