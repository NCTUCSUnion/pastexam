import { test as base, expect } from '@playwright/test'

const AUTH_FILE = 'playwright/.auth/admin.json'

const adminTest = base.extend({
  context: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: AUTH_FILE,
    })

    await context.addInitScript(() => {
      const token = window.localStorage.getItem('authToken')
      if (token) {
        window.sessionStorage.setItem('authToken', token)
      }
    })

    await use(context)
  },
})

export { adminTest }
export { expect }
