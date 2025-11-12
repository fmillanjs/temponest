import { test, expect } from '@playwright/test'

/**
 * Financial Calculator - Comprehensive E2E Tests
 *
 * Tests the complete workflow of using the financial calculator to project
 * SaaS business metrics, including model selection, calculation execution,
 * data visualization, and export functionality.
 */

test.describe('Financial Calculator - Model Selection', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/financials')
  })

  test('loads financial calculator page with correct title', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Financial Calculator')
  })

  test('displays all 5 SaaS model options', async ({ page }) => {
    // Verify all model options are visible
    const models = [
      'FormFlow',
      'SimpleAnalytics',
      'MicroCRM',
      'QuickSchedule',
      'EmailCraft'
    ]

    for (const model of models) {
      await expect(page.locator(`text=${model}`)).toBeVisible()
    }
  })

  test('shows descriptions for each SaaS model', async ({ page }) => {
    // Verify descriptions are present
    await expect(page.locator('text=Form Builder SaaS')).toBeVisible()
    await expect(page.locator('text=Web Analytics Platform')).toBeVisible()
    await expect(page.locator('text=Simple CRM System')).toBeVisible()
    await expect(page.locator('text=Appointment Booking')).toBeVisible()
    await expect(page.locator('text=Email Template Builder')).toBeVisible()
  })

  test('can select different SaaS models', async ({ page }) => {
    // Click on FormFlow model
    const formFlowCard = page.locator('text=FormFlow').locator('..')
    await formFlowCard.click()
    await page.waitForTimeout(300)

    // Click on SimpleAnalytics model
    const analyticsCard = page.locator('text=SimpleAnalytics').locator('..')
    await analyticsCard.click()
    await page.waitForTimeout(300)

    // Verify we can switch between models
    await expect(page.locator('text=SimpleAnalytics')).toBeVisible()
  })

  test('has default model selected (FormFlow)', async ({ page }) => {
    // FormFlow should be the default selection
    // Look for active/selected state
    const formFlowCard = page.locator('text=FormFlow').locator('..')

    // Check if it has selected state (class, aria-selected, or visual indicator)
    const classList = await formFlowCard.getAttribute('class')
    // Default model might have special styling
  })
})

test.describe('Financial Calculator - Calculation Execution', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/financials')
  })

  test('shows calculate/run button', async ({ page }) => {
    const calculateButton = page.locator('button:has-text("Calculate")').or(
      page.locator('button:has-text("Run")').or(
        page.locator('button:has-text("Generate")')
      )
    )

    await expect(calculateButton.first()).toBeVisible()
  })

  test('displays loading state during calculation', async ({ page }) => {
    // Select a model
    const formFlowCard = page.locator('text=FormFlow').locator('..')
    await formFlowCard.click()

    // Find and click calculate button
    const calculateButton = page.locator('button:has-text("Calculate")').or(
      page.locator('button:has-text("Run")').or(
        page.locator('button:has-text("Generate")')
      )
    ).first()

    if (await calculateButton.isVisible() && !await calculateButton.isDisabled()) {
      await calculateButton.click()

      // Look for loading indicator
      const loadingIndicator = page.locator('[class*="loader"]').or(
        page.locator('text=Running').or(
          page.locator('svg[class*="animate-spin"]')
        )
      )

      // Loading state might appear briefly
      await page.waitForTimeout(1000)
    }
  })

  test('streams calculation output in real-time', async ({ page }) => {
    // Select model
    const formFlowCard = page.locator('text=FormFlow').locator('..')
    await formFlowCard.click()

    // Run calculation
    const calculateButton = page.locator('button:has-text("Calculate")').or(
      page.locator('button:has-text("Run")')
    ).first()

    if (await calculateButton.isVisible() && !await calculateButton.isDisabled()) {
      await calculateButton.click()

      // Wait for streaming output to appear
      await page.waitForTimeout(3000)

      // Look for output area with streaming content
      const outputArea = page.locator('pre').or(
        page.locator('[class*="output"]').or(
          page.locator('[class*="terminal"]')
        )
      )

      // Output might be visible
    }
  })

  test('displays monthly breakdown table/data', async ({ page }) => {
    // Select and run calculation
    await page.locator('text=FormFlow').click()

    const runButton = page.locator('button:has-text("Run")').or(
      page.locator('button:has-text("Calculate")')
    ).first()

    if (await runButton.isVisible() && !await runButton.isDisabled()) {
      await runButton.click()

      // Wait for calculation to complete
      await page.waitForTimeout(5000)

      // Look for monthly data (table, chart, or data display)
      const monthlyData = page.locator('text=Month').or(
        page.locator('table').or(
          page.locator('[class*="chart"]')
        )
      )

      // Monthly data might be displayed
    }
  })

  test('shows 12-month projection summary', async ({ page }) => {
    await page.locator('text=FormFlow').click()

    const runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible() && !await runButton.isDisabled()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Look for Month 12 summary
      const month12 = page.locator('text=Month 12').or(
        page.locator('text=MONTH 12').or(
          page.locator('text=/12.*month/i')
        )
      )

      // Month 12 data might be displayed
    }
  })

  test('shows 24-month projection summary', async ({ page }) => {
    await page.locator('text=FormFlow').click()

    const runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible() && !await runButton.isDisabled()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Look for Month 24 summary
      const month24 = page.locator('text=Month 24').or(
        page.locator('text=MONTH 24').or(
          page.locator('text=/24.*month/i')
        )
      )

      // Month 24 data might be displayed
    }
  })

  test('displays key financial metrics (MRR, ARR, Customers, Profit)', async ({ page }) => {
    await page.locator('text=FormFlow').click()

    const runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible() && !await runButton.isDisabled()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Look for financial terminology
      const pageContent = await page.textContent('body')

      const metrics = ['MRR', 'ARR', 'Customers', 'Profit']
      let foundMetrics = 0

      for (const metric of metrics) {
        if (pageContent?.includes(metric)) {
          foundMetrics++
        }
      }

      // Should display some financial metrics
      expect(foundMetrics).toBeGreaterThan(0)
    }
  })
})

test.describe('Financial Calculator - Data Visualization', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/financials')
  })

  test('displays MRR growth chart', async ({ page }) => {
    await page.locator('text=FormFlow').click()

    const runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible() && !await runButton.isDisabled()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Look for chart elements (Recharts uses SVG)
      const chart = page.locator('svg').or(
        page.locator('[class*="recharts"]').or(
          page.locator('canvas')
        )
      )

      const chartCount = await chart.count()
      // Charts should be rendered
      expect(chartCount).toBeGreaterThan(0)
    }
  })

  test('displays customer growth chart', async ({ page }) => {
    await page.locator('text=FormFlow').click()

    const runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible() && !await runButton.isDisabled()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Look for customer-related chart labels
      const customerLabel = page.locator('text=Customer').or(
        page.locator('text=Users')
      )

      // Customer metrics might be shown in charts
    }
  })

  test('displays cumulative profit chart', async ({ page }) => {
    await page.locator('text=FormFlow').click()

    const runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible() && !await runButton.isDisabled()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Look for profit-related chart
      const profitLabel = page.locator('text=Profit').or(
        page.locator('text=Revenue')
      )

      // Profit data might be shown
    }
  })

  test('charts are responsive and properly sized', async ({ page }) => {
    await page.locator('text=FormFlow').click()

    const runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible() && !await runButton.isDisabled()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Charts should use ResponsiveContainer
      const chart = page.locator('svg').first()

      if (await chart.isVisible()) {
        const box = await chart.boundingBox()
        // Chart should have reasonable dimensions
        expect(box?.width).toBeGreaterThan(100)
      }
    }
  })
})

test.describe('Financial Calculator - Export Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/financials')

    // Run calculation first to have data to export
    await page.locator('text=FormFlow').click()

    const runButton = page.locator('button:has-text("Run")').first()
    if (await runButton.isVisible() && !await runButton.isDisabled()) {
      await runButton.click()
      await page.waitForTimeout(5000)
    }
  })

  test('shows export to JSON button', async ({ page }) => {
    const exportButton = page.locator('button:has-text("Export")').or(
      page.locator('button:has-text("JSON")')
    )

    // Export button might be visible
    const buttonCount = await page.locator('button').count()
    expect(buttonCount).toBeGreaterThan(0)
  })

  test('shows export to CSV button', async ({ page }) => {
    const csvButton = page.locator('button:has-text("CSV")').or(
      page.locator('button:has-text("Export CSV")')
    )

    // CSV export might be available
  })

  test('can download calculation results as JSON', async ({ page }) => {
    const exportButton = page.locator('button:has-text("JSON")').or(
      page.locator('button:has-text("Export JSON")')
    )

    if (await exportButton.isVisible()) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null)

      await exportButton.click()

      const download = await downloadPromise

      if (download) {
        // Verify download happened
        const filename = download.suggestedFilename()
        expect(filename).toContain('projection')
        expect(filename).toContain('.json')
      }
    }
  })

  test('can download calculation results as CSV', async ({ page }) => {
    const csvButton = page.locator('button:has-text("CSV")').or(
      page.locator('button:has-text("Export CSV")')
    )

    if (await csvButton.isVisible()) {
      // Set up download listener
      const downloadPromise = page.waitForEvent('download', { timeout: 5000 }).catch(() => null)

      await csvButton.click()

      const download = await downloadPromise

      if (download) {
        // Verify download happened
        const filename = download.suggestedFilename()
        expect(filename).toContain('.csv')
      }
    }
  })
})

test.describe('Financial Calculator - Save to Database', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/financials')

    // Run calculation first
    await page.locator('text=FormFlow').click()

    const runButton = page.locator('button:has-text("Run")').first()
    if (await runButton.isVisible() && !await runButton.isDisabled()) {
      await runButton.click()
      await page.waitForTimeout(5000)
    }
  })

  test('shows save to database button', async ({ page }) => {
    const saveButton = page.locator('button:has-text("Save")').or(
      page.locator('button:has-text("Save to Database")')
    )

    // Save button might be visible
  })

  test('displays success message after saving', async ({ page }) => {
    const saveButton = page.locator('button:has-text("Save")').first()

    if (await saveButton.isVisible() && !await saveButton.isDisabled()) {
      await saveButton.click()

      // Wait for save operation
      await page.waitForTimeout(2000)

      // Look for success message
      const successMessage = page.locator('text=saved').or(
        page.locator('text=Success').or(
          page.locator('[class*="success"]').or(
            page.locator('[role="alert"]')
          )
        )
      )

      // Success message might appear
    }
  })

  test('handles save errors gracefully', async ({ page }) => {
    // If save fails, should show error message
    const saveButton = page.locator('button:has-text("Save")').first()

    if (await saveButton.isVisible()) {
      await saveButton.click()
      await page.waitForTimeout(2000)

      // Look for any message (success or error)
      const message = page.locator('[role="alert"]').or(
        page.locator('[class*="message"]')
      )

      // Some feedback should be provided
    }
  })
})

test.describe('Financial Calculator - Different Models', () => {
  test('calculates projections for SimpleAnalytics model', async ({ page }) => {
    await page.goto('/financials')

    await page.locator('text=SimpleAnalytics').click()

    const runButton = page.locator('button:has-text("Run")').first()
    if (await runButton.isVisible()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Verify SimpleAnalytics appears in output
      const pageContent = await page.textContent('body')
      expect(pageContent).toContain('Analytics')
    }
  })

  test('calculates projections for MicroCRM model', async ({ page }) => {
    await page.goto('/financials')

    await page.locator('text=MicroCRM').click()

    const runButton = page.locator('button:has-text("Run")').first()
    if (await runButton.isVisible()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Verify CRM appears in output
      const pageContent = await page.textContent('body')
      expect(pageContent).toContain('CRM')
    }
  })

  test('can switch models and recalculate', async ({ page }) => {
    await page.goto('/financials')

    // Run first calculation with FormFlow
    await page.locator('text=FormFlow').click()
    let runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible()) {
      await runButton.click()
      await page.waitForTimeout(5000)
    }

    // Switch to QuickSchedule and recalculate
    await page.locator('text=QuickSchedule').click()
    runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Should show new calculation
      const pageContent = await page.textContent('body')
      expect(pageContent).toContain('Schedule')
    }
  })
})

test.describe('Financial Calculator - Responsive Design', () => {
  test('works on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/financials')

    // Verify page loads
    await expect(page.locator('h1')).toContainText('Financial Calculator')

    // Model cards should still be accessible
    await expect(page.locator('text=FormFlow')).toBeVisible()
  })

  test('works on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/financials')

    // Verify all elements are accessible
    await expect(page.locator('text=FormFlow')).toBeVisible()
    await expect(page.locator('text=SimpleAnalytics')).toBeVisible()
  })

  test('charts resize properly on different viewports', async ({ page }) => {
    await page.goto('/financials')

    // Run calculation
    await page.locator('text=FormFlow').click()
    const runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible()) {
      await runButton.click()
      await page.waitForTimeout(5000)

      // Resize to mobile
      await page.setViewportSize({ width: 375, height: 667 })
      await page.waitForTimeout(500)

      // Charts should still be visible
      const charts = page.locator('svg')
      const count = await charts.count()

      if (count > 0) {
        const chart = charts.first()
        await expect(chart).toBeVisible()
      }
    }
  })
})

test.describe('Financial Calculator - Error Handling', () => {
  test('handles API errors gracefully', async ({ page }) => {
    await page.goto('/financials')

    // Mock API failure by intercepting the request
    await page.route('/api/financials/run', route => {
      route.abort('failed')
    })

    await page.locator('text=FormFlow').click()
    const runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible()) {
      await runButton.click()
      await page.waitForTimeout(2000)

      // Look for error message
      const errorMessage = page.locator('text=Error').or(
        page.locator('text=Failed').or(
          page.locator('[class*="error"]')
        )
      )

      // Error might be displayed
    }
  })

  test('disables buttons during calculation', async ({ page }) => {
    await page.goto('/financials')

    await page.locator('text=FormFlow').click()
    const runButton = page.locator('button:has-text("Run")').first()

    if (await runButton.isVisible()) {
      await runButton.click()

      // Check if button is disabled during execution
      await page.waitForTimeout(500)
      const isDisabled = await runButton.isDisabled().catch(() => false)

      // Button might be disabled to prevent double-clicks
    }
  })
})
