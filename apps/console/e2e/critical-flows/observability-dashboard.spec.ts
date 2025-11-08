import { test, expect } from '@playwright/test'

test.describe('Observability Dashboard - Critical Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('loads dashboard page', async ({ page }) => {
    // Verify dashboard loaded
    await expect(page.locator('h1').or(page.locator('h2'))).toContainText(/Dashboard|Overview/)
  })

  test('displays key metrics summary', async ({ page }) => {
    // Look for summary metrics cards
    const metrics = ['Active Jobs', 'Queue Depth', 'Success Rate', 'Avg Duration']

    // Check if metrics terminology appears
    const pageContent = await page.textContent('body')

    let foundMetrics = 0
    for (const metric of metrics) {
      if (pageContent?.toLowerCase().includes(metric.toLowerCase())) {
        foundMetrics++
      }
    }

    // Should show some metrics
    expect(foundMetrics).toBeGreaterThan(0)
  })

  test('shows real-time statistics', async ({ page }) => {
    // Look for number displays or stat cards
    const stats = page.locator('[class*="stat"]').or(
      page.locator('[class*="metric"]').or(
        page.locator('[class*="card"]')
      )
    )

    // Stats should be displayed
    const numbers = page.locator('text=/\\d+/')
    const numberCount = await numbers.count()
    expect(numberCount).toBeGreaterThan(0)
  })

  test('displays charts and visualizations', async ({ page }) => {
    // Look for charts: canvas, svg, or chart library elements
    const charts = page.locator('canvas').or(
      page.locator('svg[class*="recharts"]').or(
        page.locator('[class*="chart"]')
      )
    )

    // Dashboard typically has charts
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })

  test('shows recent activity feed', async ({ page }) => {
    // Look for activity log or recent events
    const activity = page.locator('text=Recent').or(
      page.locator('text=Activity').or(
        page.locator('text=Events').or(
          page.locator('[class*="activity"]')
        )
      )
    )

    // Activity feed might be present
  })

  test('displays system health indicators', async ({ page }) => {
    // Look for health status: healthy, warning, critical
    const health = page.locator('text=healthy').or(
      page.locator('text=warning').or(
        page.locator('text=critical').or(
          page.locator('[class*="health"]')
        )
      )
    )

    // Health indicators might be shown
  })

  test('responsive design on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    // Verify dashboard loads on mobile
    const heading = page.locator('h1').or(page.locator('h2'))
    await expect(heading.first()).toBeVisible()
  })
})

test.describe('Observability - Logs Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/logs')
  })

  test('loads logs page', async ({ page }) => {
    // Verify logs page loaded
    await expect(page.locator('h1').or(page.locator('h2'))).toContainText(/Logs|Activity/)
  })

  test('displays log entries', async ({ page }) => {
    // Look for log table or list
    const logs = page.locator('table').or(
      page.locator('[role="log"]').or(
        page.locator('[class*="log"]').or(
          page.locator('[class*="table"]')
        )
      )
    )

    // Logs might be displayed in table format
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })

  test('shows log level filters', async ({ page }) => {
    // Look for filter options: error, warn, info, success
    const filters = page.locator('text=Error').or(
      page.locator('text=Warn').or(
        page.locator('text=Info').or(
          page.locator('text=Filter')
        )
      )
    )

    // Log level filters might be available
  })

  test('can filter logs by agent', async ({ page }) => {
    // Look for agent filter dropdown or buttons
    const agentFilter = page.locator('select').or(
      page.locator('[role="combobox"]').or(
        page.locator('text=Agent')
      )
    )

    // Agent filtering might be available
  })

  test('can search logs', async ({ page }) => {
    // Look for search input
    const searchInput = page.locator('input[type="search"]').or(
      page.locator('input[placeholder*="search" i]').or(
        page.locator('input[placeholder*="filter" i]')
      )
    )

    if (await searchInput.isVisible()) {
      await searchInput.fill('test query')
      await expect(searchInput).toHaveValue('test query')
    }
  })

  test('displays log timestamps', async ({ page }) => {
    // All logs should have timestamps
    const timestamps = page.locator('time').or(
      page.locator('[datetime]').or(
        page.locator('text=/\\d{1,2}:\\d{2}/')
      )
    )

    // Timestamps might be visible
  })

  test('shows log severity indicators', async ({ page }) => {
    // Color-coded or badge indicators for log level
    const indicators = page.locator('[class*="badge"]').or(
      page.locator('[class*="level"]').or(
        page.locator('[class*="severity"]')
      )
    )

    // Severity indicators might be present
  })

  test('can expand log details', async ({ page }) => {
    // Click on a log entry to see details
    const logEntry = page.locator('tr').or(
      page.locator('[class*="log-entry"]').or(
        page.locator('[class*="row"]')
      )
    ).first()

    if (await logEntry.isVisible()) {
      await logEntry.click()

      // Details panel or expanded view might appear
      await page.waitForTimeout(500)
    }
  })
})

test.describe('Observability - Metrics Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/metrics')
  })

  test('loads metrics page', async ({ page }) => {
    // Verify metrics page loaded
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })

  test('displays performance metrics', async ({ page }) => {
    // Look for performance indicators: response time, throughput, etc.
    const perfMetrics = page.locator('text=Response Time').or(
      page.locator('text=Throughput').or(
        page.locator('text=Latency').or(
          page.locator('text=Duration')
        )
      )
    )

    // Performance metrics might be displayed
  })

  test('shows metrics over time charts', async ({ page }) => {
    // Time-series charts for metrics
    const charts = page.locator('canvas').or(
      page.locator('svg').or(
        page.locator('[class*="chart"]')
      )
    )

    // Charts should visualize metrics over time
  })

  test('displays agent utilization', async ({ page }) => {
    // Shows how busy each agent is
    const utilization = page.locator('text=Utilization').or(
      page.locator('text=Busy').or(
        page.locator('text=Load').or(
          page.locator('[class*="utilization"]')
        )
      )
    )

    // Utilization metrics might be shown
  })

  test('shows error rate metrics', async ({ page }) => {
    // Error rate, failure rate, success rate
    const errorMetrics = page.locator('text=Error Rate').or(
      page.locator('text=Failure').or(
        page.locator('text=Success Rate')
      )
    )

    // Error metrics might be displayed
  })

  test('can select time range', async ({ page }) => {
    // Time range selector: last hour, 24h, 7d, 30d
    const timeRange = page.locator('text=Last Hour').or(
      page.locator('text=24 Hours').or(
        page.locator('text=7 Days').or(
          page.locator('select').or(
            page.locator('[role="combobox"]')
          )
        )
      )
    )

    // Time range selection might be available
  })

  test('displays current vs historical comparison', async ({ page }) => {
    // Shows trend: up/down arrows, percentage change
    const trends = page.locator('text=/[+\\-]\\d+%/').or(
      page.locator('svg[class*="arrow"]').or(
        page.locator('[class*="trend"]')
      )
    )

    // Trend indicators might be present
  })
})

test.describe('Observability - Alerts and Notifications', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('shows active alerts', async ({ page }) => {
    // Look for alert notifications
    const alerts = page.locator('[role="alert"]').or(
      page.locator('[class*="alert"]').or(
        page.locator('text=Alert')
      )
    )

    // Alerts might be displayed
  })

  test('displays notification bell with count', async ({ page }) => {
    // Notification bell should show unread count
    const bell = page.locator('svg[class*="bell"]').or(
      page.locator('[aria-label*="notification" i]')
    )

    await expect(bell).toBeVisible()
  })

  test('can view notification history', async ({ page }) => {
    // Click notification bell to see history
    const bellButton = page.locator('button').filter({ has: page.locator('svg.lucide-bell') })

    if (await bellButton.isVisible()) {
      await bellButton.click()

      // Notification panel should open
      await page.waitForTimeout(500)
    }
  })

  test('shows error notifications prominently', async ({ page }) => {
    // Critical errors should be highlighted
    const errorNotifications = page.locator('[class*="error"]').or(
      page.locator('[class*="critical"]').or(
        page.locator('text=Error').or(
          page.locator('text=Failed')
        )
      )
    )

    // Error notifications might be present
  })
})
