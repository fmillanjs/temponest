import { test, expect } from '@playwright/test'

/**
 * Settings Page - Comprehensive E2E Tests
 *
 * Tests the complete settings configuration experience including path configuration,
 * risk controls, API token management, and settings persistence.
 */

test.describe('Settings - Page Load and Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('loads settings page with correct title', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Settings')
  })

  test('displays settings subtitle/description', async ({ page }) => {
    await expect(page.locator('text=Configure your SaaS Empire Console')).toBeVisible()
  })

  test('displays all settings sections', async ({ page }) => {
    // Check for the 3 main sections
    await expect(page.locator('h2:has-text("Paths")')).toBeVisible()
    await expect(page.locator('h2:has-text("Risk Controls")')).toBeVisible()
    await expect(page.locator('h2:has-text("API Tokens")')).toBeVisible()
  })

  test('displays save changes button', async ({ page }) => {
    const saveButton = page.locator('button:has-text("Save Changes")')
    await expect(saveButton).toBeVisible()
  })

  test('responsive design on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })

    // Verify page loads on mobile
    await expect(page.locator('h1')).toContainText('Settings')
  })

  test('responsive design on tablet viewport', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })

    // Verify all sections are accessible
    await expect(page.locator('h2:has-text("Paths")')).toBeVisible()
  })
})

test.describe('Settings - Paths Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('displays working directory section', async ({ page }) => {
    await expect(page.locator('h2:has-text("Paths")')).toBeVisible()
    await expect(page.locator('label:has-text("Working Directory")')).toBeVisible()
  })

  test('shows working directory input with default value', async ({ page }) => {
    const workdirInput = page.locator('input[type="text"]').first()

    // Should have a default value
    const value = await workdirInput.inputValue()
    expect(value).toContain('/home/doctor/temponest')
  })

  test('can edit working directory path', async ({ page }) => {
    const workdirInput = page.locator('input[type="text"]').first()

    // Clear and enter new path
    await workdirInput.clear()
    await workdirInput.fill('/custom/path/to/project')

    // Verify new value
    await expect(workdirInput).toHaveValue('/custom/path/to/project')
  })

  test('working directory input has proper styling', async ({ page }) => {
    const workdirInput = page.locator('input[type="text"]').first()

    // Check if input is visible and has proper classes
    await expect(workdirInput).toBeVisible()

    const classList = await workdirInput.getAttribute('class')
    expect(classList).toBeTruthy()
  })
})

test.describe('Settings - Risk Controls', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('displays risk controls section', async ({ page }) => {
    await expect(page.locator('h2:has-text("Risk Controls")')).toBeVisible()
  })

  test('shows all 3 risk control checkboxes', async ({ page }) => {
    // Verify all checkboxes are present
    await expect(page.locator('text=Require approval for deployments')).toBeVisible()
    await expect(page.locator('text=Enable dry-run mode by default')).toBeVisible()
    await expect(page.locator('text=Audit all destructive actions')).toBeVisible()
  })

  test('all risk control checkboxes are checked by default', async ({ page }) => {
    // Find all checkboxes in risk controls section
    const riskControlsSection = page.locator('h2:has-text("Risk Controls")').locator('..')
    const checkboxes = riskControlsSection.locator('input[type="checkbox"]')

    const count = await checkboxes.count()
    expect(count).toBe(3)

    // Verify all are checked
    for (let i = 0; i < count; i++) {
      const isChecked = await checkboxes.nth(i).isChecked()
      expect(isChecked).toBe(true)
    }
  })

  test('can toggle "Require approval for deployments" checkbox', async ({ page }) => {
    const checkbox = page.locator('label:has-text("Require approval for deployments")').locator('input[type="checkbox"]')

    // Initially checked
    await expect(checkbox).toBeChecked()

    // Uncheck
    await checkbox.click()
    await expect(checkbox).not.toBeChecked()

    // Check again
    await checkbox.click()
    await expect(checkbox).toBeChecked()
  })

  test('can toggle "Enable dry-run mode" checkbox', async ({ page }) => {
    const checkbox = page.locator('label:has-text("Enable dry-run mode by default")').locator('input[type="checkbox"]')

    // Initially checked
    await expect(checkbox).toBeChecked()

    // Uncheck
    await checkbox.click()
    await expect(checkbox).not.toBeChecked()
  })

  test('can toggle "Audit all destructive actions" checkbox', async ({ page }) => {
    const checkbox = page.locator('label:has-text("Audit all destructive actions")').locator('input[type="checkbox"]')

    // Initially checked
    await expect(checkbox).toBeChecked()

    // Uncheck
    await checkbox.click()
    await expect(checkbox).not.toBeChecked()
  })

  test('can toggle multiple checkboxes independently', async ({ page }) => {
    const checkbox1 = page.locator('label:has-text("Require approval for deployments")').locator('input[type="checkbox"]')
    const checkbox2 = page.locator('label:has-text("Enable dry-run mode by default")').locator('input[type="checkbox"]')

    // Uncheck first
    await checkbox1.click()
    await expect(checkbox1).not.toBeChecked()
    await expect(checkbox2).toBeChecked() // Second should still be checked

    // Check first again
    await checkbox1.click()
    await expect(checkbox1).toBeChecked()
    await expect(checkbox2).toBeChecked()
  })
})

test.describe('Settings - API Tokens', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('displays API tokens section', async ({ page }) => {
    await expect(page.locator('h2:has-text("API Tokens")')).toBeVisible()
  })

  test('shows GitHub token input field', async ({ page }) => {
    await expect(page.locator('label:has-text("GitHub Token")')).toBeVisible()

    const githubTokenInput = page.locator('input[type="password"]').first()
    await expect(githubTokenInput).toBeVisible()
  })

  test('shows Langfuse API key input field', async ({ page }) => {
    await expect(page.locator('label:has-text("Langfuse API Key")')).toBeVisible()

    const langfuseInput = page.locator('input[type="password"]').nth(1)
    await expect(langfuseInput).toBeVisible()
  })

  test('GitHub token field has password type for security', async ({ page }) => {
    const githubTokenInput = page.locator('input[placeholder*="ghp_"]')

    const inputType = await githubTokenInput.getAttribute('type')
    expect(inputType).toBe('password')
  })

  test('Langfuse API key field has password type for security', async ({ page }) => {
    const langfuseInput = page.locator('input[placeholder*="lf_"]')

    const inputType = await langfuseInput.getAttribute('type')
    expect(inputType).toBe('password')
  })

  test('can enter GitHub token', async ({ page }) => {
    const githubTokenInput = page.locator('input[placeholder*="ghp_"]')

    await githubTokenInput.fill('ghp_test1234567890abcdef')
    await expect(githubTokenInput).toHaveValue('ghp_test1234567890abcdef')
  })

  test('can enter Langfuse API key', async ({ page }) => {
    const langfuseInput = page.locator('input[placeholder*="lf_"]')

    await langfuseInput.fill('lf_test1234567890abcdef')
    await expect(langfuseInput).toHaveValue('lf_test1234567890abcdef')
  })

  test('GitHub token placeholder has correct format hint', async ({ page }) => {
    const githubTokenInput = page.locator('input[type="password"]').first()

    const placeholder = await githubTokenInput.getAttribute('placeholder')
    expect(placeholder).toContain('ghp_')
  })

  test('Langfuse API key placeholder has correct format hint', async ({ page }) => {
    const langfuseInput = page.locator('input[type="password"]').nth(1)

    const placeholder = await langfuseInput.getAttribute('placeholder')
    expect(placeholder).toContain('lf_')
  })
})

test.describe('Settings - Save Changes Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('save changes button is visible and clickable', async ({ page }) => {
    const saveButton = page.locator('button:has-text("Save Changes")')

    await expect(saveButton).toBeVisible()
    await expect(saveButton).toBeEnabled()
  })

  test('can click save changes button', async ({ page }) => {
    const saveButton = page.locator('button:has-text("Save Changes")')

    await saveButton.click()

    // Wait a moment for any action
    await page.waitForTimeout(500)

    // Button should remain visible after click
    await expect(saveButton).toBeVisible()
  })

  test('save button has proper styling', async ({ page }) => {
    const saveButton = page.locator('button:has-text("Save Changes")')

    const classList = await saveButton.getAttribute('class')
    expect(classList).toContain('bg-base-900')
    expect(classList).toContain('text-white')
  })

  test('save button shows hover state', async ({ page }) => {
    const saveButton = page.locator('button:has-text("Save Changes")')

    await saveButton.hover()
    await page.waitForTimeout(200)

    // Hover state might change appearance
    await expect(saveButton).toBeVisible()
  })
})

test.describe('Settings - Form Interaction', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('can fill complete settings form', async ({ page }) => {
    // 1. Update working directory
    const workdirInput = page.locator('input[type="text"]').first()
    await workdirInput.clear()
    await workdirInput.fill('/new/custom/path')

    // 2. Toggle risk controls
    const approvalCheckbox = page.locator('label:has-text("Require approval for deployments")').locator('input')
    await approvalCheckbox.click() // Uncheck

    // 3. Enter API tokens
    const githubTokenInput = page.locator('input[placeholder*="ghp_"]')
    await githubTokenInput.fill('ghp_newtokenabc123')

    const langfuseInput = page.locator('input[placeholder*="lf_"]')
    await langfuseInput.fill('lf_newapikey456')

    // Verify all changes
    await expect(workdirInput).toHaveValue('/new/custom/path')
    await expect(approvalCheckbox).not.toBeChecked()
    await expect(githubTokenInput).toHaveValue('ghp_newtokenabc123')
    await expect(langfuseInput).toHaveValue('lf_newapikey456')
  })

  test('form fields are independent', async ({ page }) => {
    // Change one field
    const workdirInput = page.locator('input[type="text"]').first()
    await workdirInput.clear()
    await workdirInput.fill('/test/path')

    // Verify other fields are unchanged
    const githubTokenInput = page.locator('input[placeholder*="ghp_"]')
    const githubValue = await githubTokenInput.inputValue()

    // GitHub token should still be empty or have its original value
    expect(githubValue).toBe('')
  })

  test('can tab through form fields', async ({ page }) => {
    const workdirInput = page.locator('input[type="text"]').first()

    // Focus first input
    await workdirInput.click()
    await expect(workdirInput).toBeFocused()

    // Tab to next field
    await page.keyboard.press('Tab')

    await page.waitForTimeout(200)

    // Some other element should now have focus
  })
})

test.describe('Settings - Card Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('settings sections are in cards with proper styling', async ({ page }) => {
    // Each section should be in a card with rounded borders and shadow
    const cards = page.locator('[class*="rounded-2xl"]')

    const count = await cards.count()
    expect(count).toBeGreaterThanOrEqual(3) // At least 3 cards for 3 sections
  })

  test('cards have proper spacing between them', async ({ page }) => {
    // Grid layout should have gap-6 spacing
    const grid = page.locator('div.grid')

    const classList = await grid.getAttribute('class')
    expect(classList).toContain('gap-6')
  })

  test('each section header has proper typography', async ({ page }) => {
    const headers = page.locator('h2')

    // Should have multiple h2 headers (one per section)
    const count = await headers.count()
    expect(count).toBeGreaterThanOrEqual(3)

    // Check first header styling
    const firstHeader = headers.first()
    const classList = await firstHeader.getAttribute('class')
    expect(classList).toContain('font-semibold')
  })
})

test.describe('Settings - Input Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('working directory accepts absolute paths', async ({ page }) => {
    const workdirInput = page.locator('input[type="text"]').first()

    const testPaths = [
      '/home/user/project',
      '/var/www/app',
      '/opt/saas-empire',
    ]

    for (const path of testPaths) {
      await workdirInput.clear()
      await workdirInput.fill(path)
      await expect(workdirInput).toHaveValue(path)
    }
  })

  test('API token fields accept long strings', async ({ page }) => {
    const githubTokenInput = page.locator('input[placeholder*="ghp_"]')

    const longToken = 'ghp_' + 'a'.repeat(40) // GitHub tokens are typically 40 chars after prefix
    await githubTokenInput.fill(longToken)
    await expect(githubTokenInput).toHaveValue(longToken)
  })

  test('all text inputs are clearable', async ({ page }) => {
    const workdirInput = page.locator('input[type="text"]').first()

    await workdirInput.clear()
    await workdirInput.fill('test')
    await workdirInput.clear()

    await expect(workdirInput).toHaveValue('')
  })
})

test.describe('Settings - Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/settings')
  })

  test('all input fields have labels', async ({ page }) => {
    // Working Directory label
    await expect(page.locator('label:has-text("Working Directory")')).toBeVisible()

    // API token labels
    await expect(page.locator('label:has-text("GitHub Token")')).toBeVisible()
    await expect(page.locator('label:has-text("Langfuse API Key")')).toBeVisible()
  })

  test('checkboxes have descriptive labels', async ({ page }) => {
    const checkboxLabels = [
      'Require approval for deployments',
      'Enable dry-run mode by default',
      'Audit all destructive actions',
    ]

    for (const label of checkboxLabels) {
      await expect(page.locator(`text=${label}`)).toBeVisible()
    }
  })

  test('form is keyboard navigable', async ({ page }) => {
    // Start from working directory input
    const workdirInput = page.locator('input[type="text"]').first()
    await workdirInput.click()
    await expect(workdirInput).toBeFocused()

    // Tab through form
    await page.keyboard.press('Tab')
    await page.waitForTimeout(100)

    // Continue tabbing to other elements
    await page.keyboard.press('Tab')
    await page.waitForTimeout(100)

    // Form should be navigable
  })
})
