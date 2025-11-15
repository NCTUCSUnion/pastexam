import { test, expect } from '@playwright/test'
import { clickWhenVisible } from '../support/ui'

const STAT_LABELS = ['總用戶數', '總下載次數', '在線用戶', '考古題總數', '課程總數', '今日活躍']

test.describe('Home page', () => {
  test('login button initiates OAuth redirect', async ({ page }) => {
    await page.route('**/api/auth/oauth/login', async (route) => {
      await route.fulfill({
        status: 200,
        body: '<html><body>OAuth Mock</body></html>',
        headers: { 'content-type': 'text/html' },
      })
    })

    await page.goto('/')

    const loginButton = page.getByRole('button', { name: 'Login' })
    await expect(loginButton).toBeVisible({ timeout: 15000 })

    await Promise.all([
      page.waitForURL('**/api/auth/oauth/login'),
      clickWhenVisible(loginButton),
    ])

    await expect(page).toHaveURL(/\/api\/auth\/oauth\/login$/)
  })

  test('renders hero section with backend data and interactive navbar', async ({ page }) => {
    await page.goto('/')

    const navbar = page.locator('.navbar')
    await expect(navbar).toBeVisible()
    await expect(page.locator('img[alt="favicon"]').first()).toBeVisible()
    const loginButton = page.getByRole('button', { name: 'Login' })
    await expect(loginButton).toBeVisible({ timeout: 15000 })

    const themeToggle = navbar.locator('button:has(.pi.pi-sun), button:has(.pi.pi-moon)').first()
    await expect(themeToggle).toBeVisible()
    const initialTheme = await page.evaluate(() =>
      document.documentElement.classList.contains('dark')
    )
    await clickWhenVisible(themeToggle)
    await expect
      .poll(async () => page.evaluate(() => document.documentElement.classList.contains('dark')))
      .not.toBe(initialTheme)

    await expect(page.getByRole('heading', { name: '交大資工考古題系統' })).toBeVisible()

    await page.evaluate(() => {
      const globalWindow = window as typeof window & {
        __pastexam?: {
          openLoginModal?: () => void
        }
      }
      const pastexam = globalWindow.__pastexam
      if (pastexam && typeof pastexam.openLoginModal === 'function') {
        pastexam.openLoginModal()
      }
    })
    const loginDialog = page.getByRole('dialog', { name: '登入' })
    await expect(loginDialog).toBeVisible()
    const closeButton = page.getByRole('button', { name: 'Close' })
    await expect(closeButton).toBeVisible()
    await clickWhenVisible(closeButton)
    await expect(loginDialog).toBeHidden({ timeout: 5000 })

    const loader = page.getByText('Initializing source...', { exact: false })
    await expect(loader).toBeHidden({ timeout: 15000 })

    const codeBlock = page.locator('.code-container code')
    await expect(codeBlock).toHaveText(/\S/, { timeout: 15000 })
    await expect(codeBlock).not.toContainText('API connection failed')

    const languageBadge = page.locator('.language-badge')
    await expect(languageBadge).toHaveText(/[a-z]+/i)

    const statCards = page.locator('.stat-card')
    await expect(statCards).toHaveCount(STAT_LABELS.length, { timeout: 15000 })

    for (const label of STAT_LABELS) {
      const card = statCards.filter({ hasText: label })
      await expect(card, `${label} card should be visible`).toBeVisible()
      const value = card.locator('.text-xs').last()
      await expect(value).toHaveText(/^[0-9]+$/, { timeout: 15000 })
    }
  })
})
