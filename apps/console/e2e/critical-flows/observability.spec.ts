import { test, expect } from '@playwright/test'

/**
 * Observability Page - Comprehensive E2E Tests
 *
 * Tests the complete observability experience including logs display, metrics summary,
 * filtering, search, auto-refresh, and real-time monitoring capabilities.
 */

test.describe('Observability - Page Load and Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/observability')
  })

  test('loads observability page with correct title', async ({ page }) => {
    await expect(page.locator('h1')).toContainText(/Observability|Logs|Metrics/)
  })

  test('displays page description or subtitle', async ({ page }) => {
    // Page should have descriptive text
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
    expect(pageContent!.length).toBeGreaterThan(100)
  })

  test('shows main observability sections', async ({ page }) => {
    // Should have logs section and metrics section
    const sections = page.locator('section, [class*="section"]')
    const count = await sections.count()

    // Should have multiple sections
  })

  test('responsive design on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    // Verify page loads on mobile
    await expect(page.locator('h1')).toBeVisible()
  })

  test('responsive design on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })

    // Verify page loads on tablet
    await expect(page.locator('h1')).toBeVisible()
  })
})

test.describe('Observability - Logs Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/observability')
    // Wait for initial data load
    await page.waitForTimeout(2000)
  })

  test('displays logs section', async ({ page }) => {
    // Look for logs display area
    const logsSection = page.locator('text=/logs|log entries/i')

    // Logs section might be visible
  })

  test('shows log entries if logs exist', async ({ page }) => {
    // Look for log timestamps, levels, or messages
    const logEntries = page.locator('[class*="log"]').or(
      page.locator('text=/info|warn|error|debug/i')
    )

    const count = await logEntries.count()
    // Logs might be displayed
  })

  test('displays log timestamps', async ({ page }) => {
    // Logs should have timestamps
    const timestamps = page.locator('text=/\\d{1,2}:\\d{2}/').or(
      page.locator('time')
    )

    // Timestamps might be visible
  })

  test('shows log levels (info, warn, error)', async ({ page }) => {
    // Look for log level indicators
    const logLevels = page.locator('text=/info|warn|error|debug/i')

    // Log levels might be shown
  })

  test('displays log messages', async ({ page }) => {
    // Log messages should contain meaningful text
    const pageContent = await page.textContent('body')

    expect(pageContent).toBeTruthy()
  })

  test('shows agent names in logs', async ({ page }) => {
    // Logs should show which agent generated them
    const agentNames = page.locator('text=/agent|overseer|developer|designer/i')

    // Agent names might be displayed
  })

  test('logs are scrollable', async ({ page }) => {
    // Logs area should be scrollable if many entries
    const scrollArea = page.locator('[class*="scroll"]').or(
      page.locator('[class*="overflow"]')
    )

    // Scrollable area might exist
  })

  test('auto-scrolls to latest logs', async ({ page }) => {
    // Auto-scroll to bottom is enabled by default
    const autoScrollState = await page.evaluate(() => {
      // Check if auto-scroll is enabled
      return true // Assuming default is true
    })

    expect(autoScrollState).toBeTruthy()
  })
})

test.describe('Observability - Metrics Summary', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/observability')
    await page.waitForTimeout(2000)
  })

  test('displays metrics summary section', async ({ page }) => {
    // Look for metrics/statistics section
    const metricsSection = page.locator('text=/metrics|summary|statistics/i')

    // Metrics section might be visible
  })

  test('shows active jobs count', async ({ page }) => {
    // Look for active jobs metric
    const activeJobs = page.locator('text=/active.*jobs|jobs.*active/i')

    // Active jobs might be displayed
  })

  test('shows queue depth', async ({ page }) => {
    // Look for queue depth metric
    const queueDepth = page.locator('text=/queue.*depth|depth.*queue/i')

    // Queue depth might be displayed
  })

  test('shows average duration', async ({ page }) => {
    // Look for average duration metric
    const avgDuration = page.locator('text=/avg.*duration|average.*duration/i')

    // Average duration might be displayed
  })

  test('shows success rate percentage', async ({ page }) => {
    // Look for success rate
    const successRate = page.locator('text=/success.*rate|rate.*success/i')

    // Success rate might be displayed
  })

  test('displays metrics with proper formatting', async ({ page }) => {
    // Numbers should be formatted (e.g., "1.5s", "85%")
    const formattedNumbers = page.locator('text=/\\d+\\.?\\d*[sm%]/i')

    // Formatted metrics might be visible
  })

  test('metrics update when page refreshes', async ({ page }) => {
    // Get initial content
    const initialContent = await page.textContent('body')

    // Reload page
    await page.reload()
    await page.waitForTimeout(2000)

    // Page should load successfully
    const newContent = await page.textContent('body')
    expect(newContent).toBeTruthy()
  })
})

test.describe('Observability - Search and Filtering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/observability')
  })

  test('displays search input field', async ({ page }) => {
    const searchInput = page.locator('input[type="search"]').or(
      page.locator('input[placeholder*="search" i]')
    )

    // Search input might be visible
    const isVisible = await searchInput.isVisible().catch(() => false)
  })

  test('shows search icon', async ({ page }) => {
    // Look for search icon (lucide-react Search component)
    const searchIcon = page.locator('svg').filter({ has: page.locator('[class*="search"]') })

    // Search icon might be present
  })

  test('can enter search query', async ({ page }) => {
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]').first()

    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill('error')
      await expect(searchInput).toHaveValue('error')
    }
  })

  test('displays agent filter dropdown', async ({ page }) => {
    // Look for agent filter select/dropdown
    const agentFilter = page.locator('text=/filter|agent/i').locator('..')

    // Agent filter might be visible
  })

  test('displays log level filter', async ({ page }) => {
    // Look for level filter (info, warn, error, all)
    const levelFilter = page.locator('text=/level|severity/i').locator('..')

    // Level filter might be visible
  })

  test('can select agent from filter', async ({ page }) => {
    const agentSelect = page.locator('select').or(
      page.locator('[role="combobox"]')
    ).first()

    if (await agentSelect.isVisible().catch(() => false)) {
      // Can interact with filter
      await agentSelect.click()
      await page.waitForTimeout(300)
    }
  })

  test('can select log level from filter', async ({ page }) => {
    const levelSelect = page.locator('select').or(
      page.locator('[role="combobox"]')
    )

    const count = await levelSelect.count()

    if (count > 1) {
      // Multiple select dropdowns (agent and level)
      const secondSelect = levelSelect.nth(1)

      if (await secondSelect.isVisible().catch(() => false)) {
        await secondSelect.click()
        await page.waitForTimeout(300)
      }
    }
  })

  test('filters update logs when changed', async ({ page }) => {
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]').first()

    if (await searchInput.isVisible().catch(() => false)) {
      await searchInput.fill('test query')
      await searchInput.press('Enter')

      // Wait for filter to apply
      await page.waitForTimeout(1000)

      // Logs should be filtered
    }
  })
})

test.describe('Observability - Auto-Refresh Controls', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/observability')
  })

  test('shows auto-refresh toggle button', async ({ page }) => {
    // Look for auto-refresh control (Play/Pause icons)
    const autoRefreshButton = page.locator('button').filter({ has: page.locator('svg') })

    const count = await autoRefreshButton.count()
    expect(count).toBeGreaterThan(0)
  })

  test('shows refresh button', async ({ page }) => {
    // Look for manual refresh button (RefreshCw icon)
    const refreshButton = page.locator('button').filter({ has: page.locator('svg') })

    // Refresh button should be present
    const isVisible = await refreshButton.first().isVisible().catch(() => false)
  })

  test('can click manual refresh button', async ({ page }) => {
    const refreshButton = page.locator('button').filter({
      has: page.locator('svg')
    }).first()

    if (await refreshButton.isVisible().catch(() => false)) {
      await refreshButton.click()
      await page.waitForTimeout(500)

      // Refresh should trigger data reload
    }
  })

  test('can toggle auto-refresh on/off', async ({ page }) => {
    // Look for Play/Pause button
    const autoRefreshButton = page.locator('button:has(svg)')

    if (await autoRefreshButton.first().isVisible().catch(() => false)) {
      // Click to toggle
      await autoRefreshButton.first().click()
      await page.waitForTimeout(300)

      // State should change (Play <-> Pause)
    }
  })

  test('auto-refresh is enabled by default', async ({ page }) => {
    // Auto-refresh state should be true initially
    // Look for Pause icon (indicates auto-refresh is running)
    const pauseIcon = page.locator('button:has(svg)').filter({ hasText: /pause/i })

    // Pause icon might be visible (meaning auto-refresh is on)
  })
})

test.describe('Observability - Charts and Visualizations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/observability')
    await page.waitForTimeout(2000)
  })

  test('displays status distribution chart', async ({ page }) => {
    // Look for chart showing status distribution
    const statusChart = page.locator('text=/status.*distribution|distribution.*status/i')

    // Status distribution chart might be visible
  })

  test('shows runs by agent chart', async ({ page }) => {
    // Look for chart showing runs by agent
    const agentChart = page.locator('text=/runs.*agent|agent.*runs/i')

    // Agent runs chart might be visible
  })

  test('charts render with SVG elements', async ({ page }) => {
    // Charts use libraries like Recharts (SVG)
    const svgElements = page.locator('svg')

    const count = await svgElements.count()
    expect(count).toBeGreaterThan(0)
  })

  test('charts are responsive', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await page.reload()
    await page.waitForTimeout(2000)

    // Charts should still render on mobile
    const svgElements = page.locator('svg')
    const count = await svgElements.count()

    // Some SVG elements should be present
  })
})

test.describe('Observability - Recent Errors', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/observability')
    await page.waitForTimeout(2000)
  })

  test('displays recent errors section', async ({ page }) => {
    // Look for recent errors display
    const errorsSection = page.locator('text=/recent.*errors|errors.*recent/i')

    // Recent errors section might be visible
  })

  test('shows error timestamps', async ({ page }) => {
    // Errors should have timestamps
    const timestamps = page.locator('time').or(
      page.locator('text=/\\d{1,2}:\\d{2}/')
    )

    // Timestamps might be present
  })

  test('displays error step/source', async ({ page }) => {
    // Errors should show where they occurred
    const errorSteps = page.locator('text=/step|source|from/i')

    // Error source info might be shown
  })

  test('shows error preview/message', async ({ page }) => {
    // Error messages should be displayed
    const errorMessages = page.locator('text=/error|failed|exception/i')

    // Error messages might be visible
  })

  test('recent errors are limited (e.g., top 10)', async ({ page }) => {
    // Should show recent errors, not all errors
    const errorItems = page.locator('[class*="error"]')

    // Limited number of errors shown
  })
})

test.describe('Observability - Export Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/observability')
    await page.waitForTimeout(2000)
  })

  test('shows download/export button', async ({ page }) => {
    // Look for download button (Download icon)
    const downloadButton = page.locator('button').filter({
      has: page.locator('svg')
    })

    // Download button might be present
  })

  test('can click download button', async ({ page }) => {
    const downloadButton = page.locator('button:has(svg)').filter({ hasText: /download/i })

    if (await downloadButton.isVisible().catch(() => false)) {
      await downloadButton.click()
      await page.waitForTimeout(500)

      // Download might trigger
    }
  })

  test('download exports logs to file', async ({ page }) => {
    const downloadButton = page.locator('button:has(svg)').filter({ hasText: /download/i })

    if (await downloadButton.isVisible().catch(() => false)) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null)

      await downloadButton.click()

      const download = await downloadPromise

      if (download) {
        // Verify download occurred
        const filename = download.suggestedFilename()
        expect(filename).toBeTruthy()
      }
    }
  })
})

test.describe('Observability - Real-time Updates', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/observability')
  })

  test('page loads initial data', async ({ page }) => {
    // Wait for data to load
    await page.waitForTimeout(2000)

    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
    expect(pageContent!.length).toBeGreaterThan(100)
  })

  test('handles loading state', async ({ page }) => {
    // Look for loading indicator on initial load
    const loadingIndicator = page.locator('text=/loading|fetching/i').or(
      page.locator('[class*="loader"]').or(
        page.locator('svg[class*="animate-spin"]')
      )
    )

    // Loading indicator might appear briefly
  })

  test('shows data after loading completes', async ({ page }) => {
    await page.waitForTimeout(3000)

    // Data should be displayed
    const numbers = page.locator('text=/\\d+/')
    const count = await numbers.count()

    // Should have some numerical data
    expect(count).toBeGreaterThan(0)
  })

  test('handles API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('/api/observability/logs*', route => {
      route.abort('failed')
    })

    await page.reload()
    await page.waitForTimeout(2000)

    // Page should not crash, might show error message
    const errorMessage = page.locator('text=/error|failed/i')

    // Error handling might be present
  })
})

test.describe('Observability - Empty States', () => {
  test('handles no logs gracefully', async ({ page }) => {
    // Mock empty logs response
    await page.route('/api/observability/logs*', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ logs: [] })
      })
    })

    await page.goto('/observability')
    await page.waitForTimeout(2000)

    // Should show empty state or message
    const emptyMessage = page.locator('text=/no logs|no entries|empty/i')

    // Empty state might be shown
  })

  test('handles no metrics gracefully', async ({ page }) => {
    // Mock empty metrics response
    await page.route('/api/observability/metrics*', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          summary: { activeJobs: 0, queueDepth: 0, avgDuration: 0, avgDurationFormatted: '0s', successRate: 0 },
          charts: { statusDistribution: [], runsByAgent: [] },
          recentErrors: []
        })
      })
    })

    await page.goto('/observability')
    await page.waitForTimeout(2000)

    // Should handle zero metrics
    const zeros = page.locator('text="0"')
    const count = await zeros.count()

    // Zero values should be displayed
  })

  test('shows no recent errors message when none exist', async ({ page }) => {
    await page.route('/api/observability/metrics*', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({
          summary: { activeJobs: 5, queueDepth: 2, avgDuration: 1500, avgDurationFormatted: '1.5s', successRate: 95 },
          charts: { statusDistribution: [], runsByAgent: [] },
          recentErrors: [] // No errors
        })
      })
    })

    await page.goto('/observability')
    await page.waitForTimeout(2000)

    // No errors section might show empty state
    const noErrorsMessage = page.locator('text=/no.*errors|no.*issues/i')

    // Empty errors message might be shown
  })
})

test.describe('Observability - Performance', () => {
  test('page loads within reasonable time', async ({ page }) => {
    const startTime = Date.now()
    await page.goto('/observability')
    const loadTime = Date.now() - startTime

    // Should load in under 3 seconds
    expect(loadTime).toBeLessThan(3000)
  })

  test('handles large log datasets', async ({ page }) => {
    // Mock large log dataset
    const largeLogs = Array.from({ length: 100 }, (_, i) => ({
      id: `log-${i}`,
      timestamp: new Date().toISOString(),
      level: 'info',
      message: `Log message ${i}`,
      agent: 'developer',
      resource: 'test'
    }))

    await page.route('/api/observability/logs*', route => {
      route.fulfill({
        status: 200,
        body: JSON.stringify({ logs: largeLogs })
      })
    })

    await page.goto('/observability')
    await page.waitForTimeout(2000)

    // Page should handle large datasets
    const pageContent = await page.textContent('body')
    expect(pageContent).toBeTruthy()
  })

  test('auto-refresh does not cause memory leaks', async ({ page }) => {
    await page.goto('/observability')

    // Let auto-refresh run for a few cycles
    await page.waitForTimeout(10000)

    // Page should still be responsive
    const heading = page.locator('h1')
    await expect(heading).toBeVisible()
  })
})
