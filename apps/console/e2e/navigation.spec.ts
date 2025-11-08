import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the home page before each test
    await page.goto('/')
  })

  test('loads the homepage', async ({ page }) => {
    await expect(page).toHaveURL('/')
  })

  test('has the app title', async ({ page }) => {
    await expect(page).toHaveTitle(/SaaS Empire/i)
  })

  test('sidebar navigation is visible', async ({ page }) => {
    // Check if sidebar with brand name exists
    const sidebar = page.locator('text=SaaS Empire').first()
    await expect(sidebar).toBeVisible()
  })

  test('can navigate using sidebar links', async ({ page }) => {
    // Click on Dashboard link
    const dashboardLink = page.locator('a:has-text("Dashboard")').first()
    await dashboardLink.click()

    // Verify navigation
    await expect(page).toHaveURL(/\/dashboard/)
  })

  test('header search is visible', async ({ page }) => {
    // Check if search input exists
    const searchInput = page.locator('input[placeholder*="Search"]')
    await expect(searchInput).toBeVisible()
  })

  test('can type in search input', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="Search"]')
    await searchInput.fill('test query')
    await expect(searchInput).toHaveValue('test query')
  })

  test('notification bell is visible', async ({ page }) => {
    // Check if notification button exists (contains bell SVG)
    const notificationButton = page.locator('button').filter({ has: page.locator('svg.lucide-bell') })
    await expect(notificationButton).toBeVisible()
  })
})

test.describe('Command Palette', () => {
  test('opens command palette with Cmd+K', async ({ page }) => {
    await page.goto('/')

    // Open command palette with keyboard shortcut
    await page.keyboard.press('Meta+K')

    // Check if command palette is visible
    const commandInput = page.locator('input[placeholder*="Type a command"]')
    await expect(commandInput).toBeVisible()
  })

  test('closes command palette with Escape', async ({ page }) => {
    await page.goto('/')

    // Open command palette
    await page.keyboard.press('Meta+K')

    // Verify it's open
    const commandInput = page.locator('input[placeholder*="Type a command"]')
    await expect(commandInput).toBeVisible()

    // Close with Escape
    await page.keyboard.press('Escape')

    // Verify it's closed
    await expect(commandInput).not.toBeVisible()
  })

  test('can search in command palette', async ({ page }) => {
    await page.goto('/')

    // Open command palette
    await page.keyboard.press('Meta+K')

    // Type in search
    const commandInput = page.locator('input[placeholder*="Type a command"]')
    await commandInput.fill('dashboard')

    // Verify input has value
    await expect(commandInput).toHaveValue('dashboard')
  })
})

test.describe('Responsive Design', () => {
  test('renders correctly on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Verify page loads
    await expect(page.locator('text=SaaS Empire')).toBeVisible()
  })

  test('renders correctly on tablet', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/')

    // Verify page loads
    await expect(page.locator('text=SaaS Empire')).toBeVisible()
  })

  test('renders correctly on desktop', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('/')

    // Verify page loads
    await expect(page.locator('text=SaaS Empire')).toBeVisible()
  })
})
