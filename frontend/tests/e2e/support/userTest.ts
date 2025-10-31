import { test as base, expect } from '@playwright/test'
import { buildJwt } from './jwt'

const userTest = base.extend({
  context: async ({ browser }, use) => {
    const context = await browser.newContext()

    const token = buildJwt({
      uid: 2,
      email: 'user@example.com',
      name: '一般使用者',
      is_admin: false,
      exp: Math.floor(Date.now() / 1000) + 3600,
    })

    await context.addInitScript((value: string) => {
      window.sessionStorage.setItem('authToken', value)
      window.localStorage.setItem('authToken', value)
    }, token)

    await use(context)
  },
})

export { userTest }
export { expect }
