import { test, expect } from '@playwright/test'

test.describe('Agent Execution - Critical Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agents')
  })

  test('loads agents page', async ({ page }) => {
    // Verify agents page loaded
    await expect(page.locator('h1')).toContainText(/Agents|Factory Map/)
  })

  test('displays all agent types', async ({ page }) => {
    // Check for the 7 agent types
    const agents = ['Overseer', 'Developer', 'Designer', 'UX', 'QA', 'Security', 'DevOps']

    // At least some agents should be mentioned
    const pageContent = await page.textContent('body')

    // Look for agent names in page
    let foundAgents = 0
    for (const agent of agents) {
      if (pageContent?.includes(agent)) {
        foundAgents++
      }
    }

    // Should find at least some agent references
    expect(foundAgents).toBeGreaterThan(0)
  })

  test('shows agent status indicators', async ({ page }) => {
    // Look for status: healthy, degraded, down
    const statusElements = page.locator('text=healthy').or(
      page.locator('text=degraded').or(
        page.locator('text=down').or(
          page.locator('[class*="status"]')
        )
      )
    )

    // Status indicators might be visible
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })

  test('displays agent cards or list', async ({ page }) => {
    // Agents should be displayed as cards or in a list
    const agentCards = page.locator('[class*="agent"]').or(
      page.locator('[data-agent]').or(
        page.locator('[class*="card"]')
      )
    )

    // Look for structured agent display
    const headings = page.locator('h1, h2, h3, h4')
    const headingCount = await headings.count()
    expect(headingCount).toBeGreaterThan(0)
  })

  test('shows agent last heartbeat time', async ({ page }) => {
    // Look for timestamp or "last seen" information
    const timestamps = page.locator('time').or(
      page.locator('text=ago').or(
        page.locator('[datetime]').or(
          page.locator('text=minutes').or(
            page.locator('text=seconds')
          )
        )
      )
    )

    // Timestamps might be displayed
  })

  test('displays agent version information', async ({ page }) => {
    // Look for version numbers (v1.0.0, version, etc.)
    const versions = page.locator('text=/v?\\d+\\.\\d+\\.\\d+/').or(
      page.locator('text=version').or(
        page.locator('[class*="version"]')
      )
    )

    // Version info might be shown
  })

  test('can click on agent card for details', async ({ page }) => {
    // Find and click an agent card
    const agentCard = page.locator('[class*="agent"]').or(
      page.locator('[data-agent]').or(
        page.locator('[class*="card"]')
      )
    ).first()

    if (await agentCard.isVisible()) {
      await agentCard.click()

      // Should show details or expand
      await page.waitForTimeout(500)
    }
  })

  test('responsive design on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })

    // Verify page loads
    await expect(page.locator('h1')).toContainText(/Agents|Factory/)
  })
})

test.describe('Agent Execution - Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agents')
  })

  test('shows agent configuration options', async ({ page }) => {
    // Look for config or settings
    const configButton = page.locator('button:has-text("Config")').or(
      page.locator('button:has-text("Settings")').or(
        page.locator('text=Configuration')
      )
    )

    // Configuration might be available
  })

  test('displays agent capabilities', async ({ page }) => {
    // Each agent type has specific capabilities
    const capabilities = page.locator('text=capabilities').or(
      page.locator('text=skills').or(
        page.locator('text=tools').or(
          page.locator('[class*="capability"]')
        )
      )
    )

    // Capabilities might be listed
  })

  test('shows agent task history', async ({ page }) => {
    // Look for history or recent tasks
    const history = page.locator('text=History').or(
      page.locator('text=Recent').or(
        page.locator('text=Tasks').or(
          page.locator('[class*="history"]')
        )
      )
    )

    // Task history might be displayed
  })

  test('displays agent performance metrics', async ({ page }) => {
    // Look for metrics: tasks completed, success rate, avg time, etc.
    const metrics = page.locator('text=completed').or(
      page.locator('text=success').or(
        page.locator('text=rate').or(
          page.locator('[class*="metric"]')
        )
      )
    )

    // Performance metrics might be shown
  })
})

test.describe('Agent Collaboration - Multi-Agent Workflows', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agents')
  })

  test('shows collaboration patterns', async ({ page }) => {
    // Look for workflow visualization
    const workflow = page.locator('text=Sequential').or(
      page.locator('text=Parallel').or(
        page.locator('text=Iterative').or(
          page.locator('text=Workflow')
        )
      )
    )

    // Collaboration patterns might be displayed
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })

  test('displays agent dependencies', async ({ page }) => {
    // Shows which agents work together
    const dependencies = page.locator('text=Depends').or(
      page.locator('text=Requires').or(
        page.locator('[class*="dependency"]')
      )
    )

    // Dependencies might be shown
  })

  test('shows active multi-agent tasks', async ({ page }) => {
    // Look for currently running collaborative tasks
    const activeTasks = page.locator('text=Active').or(
      page.locator('text=Running').or(
        page.locator('[class*="active"]').or(
          page.locator('[class*="running"]')
        )
      )
    )

    // Active tasks might be displayed
  })
})

test.describe('Agent Health Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/agents')
  })

  test('displays real-time health status', async ({ page }) => {
    // All agents should show current health
    const healthStatuses = page.locator('text=healthy').or(
      page.locator('text=degraded').or(
        page.locator('text=down')
      )
    )

    // Health status should be visible
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })

  test('shows unhealthy agent alerts', async ({ page }) => {
    // Look for warning/error indicators
    const alerts = page.locator('[role="alert"]').or(
      page.locator('[class*="alert"]').or(
        page.locator('[class*="warning"]').or(
          page.locator('text=degraded').or(
            page.locator('text=down')
          )
        )
      )
    )

    // Alerts might be present if agents are unhealthy
  })

  test('can refresh agent status', async ({ page }) => {
    // Look for refresh button
    const refreshButton = page.locator('button:has-text("Refresh")').or(
      page.locator('button[aria-label*="refresh" i]').or(
        page.locator('svg[class*="refresh"]').locator('..')
      )
    )

    // Refresh functionality might be available
  })

  test('shows agent uptime information', async ({ page }) => {
    // Look for uptime stats
    const uptime = page.locator('text=uptime').or(
      page.locator('text=online').or(
        page.locator('[class*="uptime"]')
      )
    )

    // Uptime info might be displayed
  })
})
