import { test as setup, expect } from '@playwright/test'

type PastexamHelpers = {
  openLoginModal?: () => void
}

declare global {
  interface Window {
    __pastexam?: PastexamHelpers
  }
}

const AUTH_FILE = 'playwright/.auth/admin.json'

const resolveEnv = () => {
  const globalProcess = (globalThis as { process?: { env?: Record<string, string | undefined> } })
    .process
  return globalProcess?.env ?? {}
}

const env = resolveEnv()
const ADMIN_USERNAME = env.PLAYWRIGHT_ADMIN_USERNAME ?? 'admin'
const ADMIN_PASSWORD = env.PLAYWRIGHT_ADMIN_PASSWORD ?? 'admin'

setup('authenticate as admin', async ({ page }) => {
  await page.goto('/')

  await page.waitForFunction(
    () => typeof window.__pastexam?.openLoginModal === 'function',
    undefined,
    { timeout: 15000 }
  )

  await page.evaluate(() => {
    window.__pastexam?.openLoginModal?.()
  })

  const loginDialog = page.getByRole('dialog', { name: '登入' })
  await expect(loginDialog).toBeVisible()

  const usernameInput = loginDialog.locator('input#username')
  const passwordInput = loginDialog.locator('input[type="password"]')
  await expect(usernameInput).toBeVisible()
  await expect(passwordInput).toBeVisible()

  await usernameInput.fill(ADMIN_USERNAME)
  await passwordInput.fill(ADMIN_PASSWORD)

  const submitButton = page.getByRole('button', { name: '登入' })
  await submitButton.click()

  await page.waitForURL('**/archive', { timeout: 15000 })
  await expect(page).toHaveURL(/\/archive$/)

  const token = await page.evaluate(() => window.sessionStorage.getItem('authToken'))
  if (token) {
    await page.evaluate((value) => {
      window.localStorage.setItem('authToken', value)
    }, token)
  } else {
    throw new Error('Expected auth token after login but none was found')
  }

  await page.context().storageState({ path: AUTH_FILE })
})

export {}
