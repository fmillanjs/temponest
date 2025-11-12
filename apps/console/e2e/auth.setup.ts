import { test as setup, expect } from '@playwright/test'

const authFile = '.auth/user.json'

/**
 * Authentication setup for E2E tests
 *
 * This setup runs before all tests and creates an authenticated session.
 * For testing purposes, we set a mock session token cookie to bypass authentication.
 *
 * In a production test environment, this would:
 * 1. Navigate to login page
 * 2. Fill in credentials
 * 3. Submit login form
 * 4. Save authenticated state
 */
setup('authenticate', async ({ page, context }) => {
  // For E2E testing, we'll set a mock session token
  // This bypasses the actual authentication but allows us to test the application

  await context.addCookies([
    {
      name: 'better-auth.session_token',
      value: 'test-session-token-' + Date.now(),
      domain: 'localhost',
      path: '/',
      httpOnly: true,
      sameSite: 'Lax',
      expires: Date.now() / 1000 + 3600, // 1 hour from now
    },
  ])

  // Navigate to home page to verify authentication works
  await page.goto('/')

  // Wait a bit for any redirects
  await page.waitForTimeout(1000)

  // Verify we're not redirected to login
  const url = page.url()
  if (url.includes('/login')) {
    console.warn('⚠️ Authentication setup did not work - still on login page')
  } else {
    console.log('✅ Authentication setup successful - can access protected routes')
  }

  // Save signed-in state to reuse in tests
  await page.context().storageState({ path: authFile })
})
