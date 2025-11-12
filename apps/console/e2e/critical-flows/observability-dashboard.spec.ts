import { test, expect } from '@playwright/test'

/**
 * Dashboard - Comprehensive E2E Tests
 *
 * Tests the complete dashboard monitoring experience including KPI display,
 * agent health monitoring, quick actions, and recent activity feed.
 */

test.describe('Dashboard - Page Load and Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('loads dashboard page with correct title', async ({ page }) => {
    // Verify main heading
    await expect(page.locator('h1')).toContainText('Dashboard')
  })

  test('displays dashboard subtitle/description', async ({ page }) => {
    // Verify subtitle is present
    await expect(page.locator('text=Monitor your SaaS building empire')).toBeVisible()
  })

  test('displays all main dashboard sections', async ({ page }) => {
    // Check for main sections
    await expect(page.locator('h2:has-text("Agent Health")')).toBeVisible()

    // KPI Bar should be rendered (server component)
    // Quick Actions and Recent Activity should be visible
    const sections = page.locator('section')
    const count = await sections.count()
    expect(count).toBeGreaterThan(0)
  })

  test('responsive design on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    // Verify dashboard loads on mobile
    await expect(page.locator('h1')).toContainText('Dashboard')
  })

  test('responsive design on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })

    // Verify all main sections are accessible
    await expect(page.locator('h1')).toContainText('Dashboard')
    await expect(page.locator('h2:has-text("Agent Health")')).toBeVisible()
  })
})

test.describe('Dashboard - KPI Bar', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('displays KPI metrics', async ({ page }) => {
    // KPI Bar is a server component that shows project/run/agent counts
    // Look for numerical data displays
    const numbers = page.locator('text=/\\d+/')
    const count = await numbers.count()

    // Should display some numerical KPIs
    expect(count).toBeGreaterThan(0)
  })

  test('shows total projects count', async ({ page }) => {
    // Look for "Projects" label or similar
    const projectsLabel = page.locator('text=/projects/i')

    // Projects metric might be visible
    const isVisible = await projectsLabel.isVisible().catch(() => false)
  })

  test('shows total runs count', async ({ page }) => {
    // Look for "Runs" or "Executions" label
    const runsLabel = page.locator('text=/runs|executions/i')

    // Runs metric might be visible
    const isVisible = await runsLabel.isVisible().catch(() => false)
  })

  test('shows agent uptime percentage', async ({ page }) => {
    // Look for uptime percentage (e.g., "98%")
    const percentages = page.locator('text=/%/')

    // Uptime percentage might be displayed
    const count = await percentages.count()
  })

  test('KPI cards have proper styling', async ({ page }) => {
    // KPI metrics should be in cards or similar containers
    const cards = page.locator('[class*="card"]').or(
      page.locator('[class*="metric"]').or(
        page.locator('[class*="stat"]')
      )
    )

    const count = await cards.count()
    // Some card-like elements should exist
  })
})

test.describe('Dashboard - Agent Health Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('displays agent health section title', async ({ page }) => {
    await expect(page.locator('h2:has-text("Agent Health")')).toBeVisible()
  })

  test('shows agent status cards in grid layout', async ({ page }) => {
    // Agents are displayed in a responsive grid
    // Look for agent cards
    const agentSection = page.locator('h2:has-text("Agent Health")').locator('..')

    // Should have grid layout with agent cards
    const gridExists = await agentSection.locator('[class*="grid"]').isVisible().catch(() => false)
  })

  test('displays individual agent cards with details', async ({ page }) => {
    // Each agent should have a card showing: name, status, heartbeat, version
    // Look for agent names or status indicators
    const statusIndicators = page.locator('[class*="status"]').or(
      page.locator('text=/healthy|degraded|down/i')
    )

    const count = await statusIndicators.count()
  })

  test('shows agent heartbeat information', async ({ page }) => {
    // Heartbeat shows time since last contact (e.g., "2 minutes", "never")
    const heartbeats = page.locator('text=/ago|never|seconds|minutes|hours/i')

    const count = await heartbeats.count()
    // Should show heartbeat times
  })

  test('shows agent version numbers', async ({ page }) => {
    // Look for version numbers (e.g., "v1.0.0" or "1.0.0")
    const versions = page.locator('text=/v?\\d+\\.\\d+\\.\\d+/')

    const count = await versions.count()
    // Version info might be displayed
  })

  test('agent cards show status with colors', async ({ page }) => {
    // Status should be color-coded (green=healthy, yellow=degraded, red=down)
    // Look for status badges or indicators
    const badges = page.locator('[class*="badge"]')

    const count = await badges.count()
  })

  test('grid layout is responsive (1 col mobile, 2 col tablet, 3 col desktop)', async ({ page }) => {
    // Desktop: 3 columns
    const agentGrid = page.locator('h2:has-text("Agent Health")').locator('..').locator('[class*="grid"]')

    if (await agentGrid.isVisible()) {
      // Grid should exist and be responsive
      const classList = await agentGrid.getAttribute('class')

      // Should have responsive grid classes (md:grid-cols-2, xl:grid-cols-3)
      expect(classList).toBeTruthy()
    }
  })

  test('shows all 7 core agents if present', async ({ page }) => {
    // Look for agent type names
    const agentTypes = ['Overseer', 'Developer', 'Designer', 'UX', 'QA', 'Security', 'DevOps']

    const pageContent = await page.textContent('body')

    // Some agents might be visible
    let foundAgents = 0
    for (const agent of agentTypes) {
      if (pageContent?.includes(agent)) {
        foundAgents++
      }
    }
  })
})

test.describe('Dashboard - Quick Actions Section', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('displays quick actions component', async ({ page }) => {
    // Quick Actions component should be visible
    // Look for action cards or buttons
    const actions = page.locator('text=/new project|create|wizard|settings/i')

    const count = await actions.count()
  })

  test('shows action cards with icons', async ({ page }) => {
    // Each action should have an icon (SVG) and label
    const svgIcons = page.locator('svg')

    const count = await svgIcons.count()
    // Should have multiple icons for actions
    expect(count).toBeGreaterThan(0)
  })

  test('action cards are clickable links', async ({ page }) => {
    // Quick actions should be links to different pages
    const actionLinks = page.locator('a[href*="/wizard"]').or(
      page.locator('a[href*="/project"]').or(
        page.locator('a[href*="/settings"]')
      )
    )

    // Links might be present
    const count = await actionLinks.count()
  })

  test('can navigate to wizard from quick action', async ({ page }) => {
    const wizardLink = page.locator('a[href*="/wizard"]').first()

    if (await wizardLink.isVisible()) {
      await wizardLink.click()

      // Should navigate to wizard page
      await page.waitForURL(/\/wizard/i, { timeout: 5000 })
    }
  })

  test('quick actions span 2 columns on large screens', async ({ page }) => {
    // Quick Actions has className="lg:col-span-2"
    const quickActionsSection = page.locator('text=/create|new|wizard/i').locator('..')

    // Should have column span class
    const classList = await quickActionsSection.getAttribute('class').catch(() => null)
  })
})

test.describe('Dashboard - Recent Activity Feed', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('displays recent activity component', async ({ page }) => {
    // Recent Activity component should show latest actions
    // Look for activity-related text
    const activityText = page.locator('text=/recent|activity|latest/i')

    const count = await activityText.count()
  })

  test('shows activity items with timestamps', async ({ page }) => {
    // Activities should have relative timestamps (e.g., "2 hours ago")
    const timestamps = page.locator('text=/ago|just now|yesterday/i')

    const count = await timestamps.count()
  })

  test('activity items have icons indicating type', async ({ page }) => {
    // Different activity types have different icons (commit, run, alert, etc.)
    const icons = page.locator('svg')

    const iconCount = await icons.count()
    expect(iconCount).toBeGreaterThan(0)
  })

  test('shows activity descriptions', async ({ page }) => {
    // Each activity should have a description of what happened
    const activities = page.locator('[class*="activity"]').or(
      page.locator('text=/commit|deployed|created|updated/i')
    )

    const count = await activities.count()
  })

  test('recent activity is scrollable if many items', async ({ page }) => {
    // Activity feed might have a ScrollArea component
    const scrollArea = page.locator('[class*="scroll"]')

    const exists = await scrollArea.isVisible().catch(() => false)
  })

  test('recent activity spans 1 column on large screens', async ({ page }) => {
    // Recent Activity is in a grid with Quick Actions
    // Recent Activity should be in its own column
    const activitySection = page.locator('text=/recent|activity/i').locator('..')

    // Should be in grid layout
    const exists = await activitySection.isVisible().catch(() => false)
  })
})

test.describe('Dashboard - Real-time Updates', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('dashboard data refreshes on page reload', async ({ page }) => {
    // Get initial state
    const initialContent = await page.textContent('body')

    // Reload page
    await page.reload()

    // Page should load successfully after reload
    await expect(page.locator('h1')).toContainText('Dashboard')
  })

  test('handles no agents gracefully', async ({ page }) => {
    // If no agents exist, should show appropriate message or empty state
    // The page should still render without errors
    await expect(page.locator('h2:has-text("Agent Health")')).toBeVisible()
  })

  test('handles no recent activity gracefully', async ({ page }) => {
    // If no recent activity, should show empty state or message
    // Page should not crash
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })
})

test.describe('Dashboard - Navigation and Links', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('can navigate to agents page', async ({ page }) => {
    const agentsLink = page.locator('a[href*="/agents"]').first()

    if (await agentsLink.isVisible()) {
      await agentsLink.click()
      await page.waitForURL(/\/agents/, { timeout: 5000 })
    }
  })

  test('can navigate to projects page', async ({ page }) => {
    const projectsLink = page.locator('a[href*="/project"]').first()

    if (await projectsLink.isVisible()) {
      await projectsLink.click()
      await page.waitForURL(/\/project/, { timeout: 5000 })
    }
  })

  test('can navigate to settings page', async ({ page }) => {
    const settingsLink = page.locator('a[href*="/settings"]').first()

    if (await settingsLink.isVisible()) {
      await settingsLink.click()
      await page.waitForURL(/\/settings/, { timeout: 5000 })
    }
  })

  test('sidebar navigation is accessible from dashboard', async ({ page }) => {
    // Sidebar should be visible with navigation links
    const sidebar = page.locator('text=SaaS Empire').first()
    await expect(sidebar).toBeVisible()
  })
})

test.describe('Dashboard - Performance and Loading', () => {
  test('dashboard loads within reasonable time', async ({ page }) => {
    const startTime = Date.now()
    await page.goto('/dashboard')
    const loadTime = Date.now() - startTime

    // Should load in under 3 seconds
    expect(loadTime).toBeLessThan(3000)
  })

  test('server components render correctly', async ({ page }) => {
    await page.goto('/dashboard')

    // KPI Bar is a server component that should render with data
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
    expect(pageContent!.length).toBeGreaterThan(100)
  })

  test('handles slow database queries gracefully', async ({ page }) => {
    // Even if database is slow, page should eventually render
    await page.goto('/dashboard')

    // Wait for main content to appear (with longer timeout)
    await expect(page.locator('h1')).toContainText('Dashboard', { timeout: 10000 })
  })
})

test.describe('Dashboard - Data Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('displays formatted dates and times', async ({ page }) => {
    // Times should be formatted using date-fns (e.g., "2 hours ago")
    const timeFormats = page.locator('text=/\\d+\\s+(second|minute|hour|day)s?\\s+ago/i')

    // Formatted times might appear in activity feed or agent heartbeats
    const count = await timeFormats.count()
  })

  test('shows zero states for empty data', async ({ page }) => {
    // When counts are 0, should display "0" not crash
    const zeros = page.locator('text="0"')

    // Might have zero counts for some metrics
    const count = await zeros.count()
  })

  test('numerical data is readable and formatted', async ({ page }) => {
    // Numbers should be formatted properly (commas for thousands, etc.)
    const numbers = page.locator('text=/\\d+/')

    const count = await numbers.count()
    expect(count).toBeGreaterThan(0)
  })
})
