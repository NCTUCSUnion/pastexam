import { test, expect } from '@playwright/test'

const AUTH_FILE = 'playwright/.auth/admin.json'

test.use({ storageState: AUTH_FILE })

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    const token = window.localStorage.getItem('authToken')
    if (token) {
      window.sessionStorage.setItem('authToken', token)
    }
  })
})

test.describe('Archive page', () => {
  test('allows admin to search courses and open upload dialog', async ({ page }) => {
    await page.goto('/archive')

    await expect(page).toHaveURL(/\/archive$/)

    const uploadButton = page.getByRole('button', { name: '上傳考古題' })
    await expect(uploadButton).toBeVisible({ timeout: 15000 })

    const searchInput = page.getByPlaceholder('搜尋課程')
    await expect(searchInput).toBeVisible({ timeout: 15000 })
    await searchInput.fill('資料結構')

    const courseButton = page.getByRole('button', { name: '資料結構與物件導向程式設計' }).first()
    await expect(courseButton).toBeVisible({ timeout: 15000 })
    await Promise.all([
      page.waitForResponse((response) => {
        return (
          response.url().includes('/api/courses/') &&
          response.url().endsWith('/archives') &&
          response.request().method() === 'GET'
        )
      }),
      courseButton.click(),
    ])

    const selectedSubject = page.locator('span.font-medium', {
      hasText: '資料結構與物件導向程式設計',
    })
    await expect(selectedSubject).toBeVisible({ timeout: 15000 })

    await uploadButton.click()

    const uploadDialog = page.getByRole('dialog', { name: '上傳考古題' })
    await expect(uploadDialog).toBeVisible({ timeout: 10000 })
    await expect(uploadDialog.getByRole('tab', { name: '選擇課程' })).toBeVisible()
    await expect(uploadDialog.getByRole('tab', { name: '考試資訊' })).toBeVisible()
  })

  test('persists last selected course across reloads', async ({ page }) => {
    await page.goto('/archive')

    const searchInput = page.getByPlaceholder('搜尋課程')
    await searchInput.fill('演算法概論')

    const courseButton = page.getByRole('button', { name: '演算法概論' }).first()
    await Promise.all([
      page.waitForResponse((response) => {
        return (
          response.url().includes('/api/courses/') &&
          response.url().endsWith('/archives') &&
          response.request().method() === 'GET'
        )
      }),
      courseButton.click(),
    ])

    const selectionTag = page.locator('span.font-medium', { hasText: '演算法概論' })
    await expect(selectionTag).toBeVisible({ timeout: 15000 })

    await page.reload()

    await expect(page).toHaveURL(/\/archive$/)
    await expect(selectionTag).toBeVisible({ timeout: 15000 })
  })
})
