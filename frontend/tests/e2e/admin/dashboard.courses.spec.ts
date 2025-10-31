import { adminTest as test, expect } from '../support/adminTest'
import { mockAdminCourseEndpoints } from '../support/adminFixtures'
import { JSON_HEADERS } from '../support/constants'

test.describe('Admin Dashboard › Courses', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/notifications/active', async (route) => {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify([]),
      })
    })
  })

  test('allows creating, editing, and deleting courses', async ({ page }) => {
    const { createPayloads, updatePayloads, deleteIds } = await mockAdminCourseEndpoints(page)

    await page.goto('/admin', { waitUntil: 'domcontentloaded' })
    await expect(page).toHaveURL(/\/admin$/)

    const tabs = page.getByRole('tab')
    await expect(tabs).toHaveCount(3)
    await tabs.first().click()
    await expect(page.getByRole('row', { name: /資料結構/ })).toBeVisible()
    await expect(page.getByRole('row', { name: /演算法/ })).toBeVisible()

    await page.getByRole('button', { name: '新增課程' }).click()

    const createDialog = page.getByRole('dialog', { name: '新增課程' })
    await expect(createDialog).toBeVisible()

    await createDialog.getByPlaceholder('輸入課程名稱').fill('線性代數')

    const categoryTrigger = createDialog
      .locator('label', { hasText: '分類' })
      .locator('xpath=following-sibling::*[1]')
    await categoryTrigger.click()
    await page.getByRole('option', { name: '大二課程' }).click()

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/courses/admin/courses') &&
          response.request().method() === 'POST'
      ),
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/courses/admin/courses') &&
          response.request().method() === 'GET'
      ),
      createDialog.getByRole('button', { name: '新增' }).click(),
    ])

    await expect(page.getByRole('row', { name: /線性代數/ })).toBeVisible()
    expect(createPayloads.at(-1)).toMatchObject({ name: '線性代數', category: 'sophomore' })

    const editRow = page.getByRole('row', { name: /資料結構/ })
    await editRow.getByRole('button', { name: '編輯' }).click()

    const editDialog = page.getByRole('dialog', { name: '編輯課程' })
    await expect(editDialog).toBeVisible()

    const nameInput = editDialog.getByPlaceholder('輸入課程名稱')
    await nameInput.fill('資料結構 (更新)')

    const editCategoryTrigger = editDialog
      .locator('label', { hasText: '分類' })
      .locator('xpath=following-sibling::*[1]')
    await editCategoryTrigger.click()
    await page.getByRole('option', { name: '研究所課程' }).click()

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/courses/admin/courses') &&
          response.request().method() === 'PUT'
      ),
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/courses/admin/courses') &&
          response.request().method() === 'GET'
      ),
      editDialog.getByRole('button', { name: '更新' }).click(),
    ])

    expect(updatePayloads.at(-1)).toMatchObject({
      payload: { name: '資料結構 (更新)', category: 'graduate' },
    })
    await expect(page.getByRole('row', { name: /資料結構 \(更新\)/ })).toBeVisible()
    await expect(page.getByRole('row', { name: /研究所課程/ })).toBeVisible()

    const deleteRow = page.getByRole('row', { name: /線性代數/ })
    await deleteRow.getByRole('button', { name: '刪除' }).click()

    const dialog = page.getByRole('alertdialog', { name: '刪除確認' })
    await expect(dialog).toBeVisible()

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/courses/admin/courses') &&
          response.request().method() === 'DELETE'
      ),
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/courses/admin/courses') &&
          response.request().method() === 'GET'
      ),
      dialog.getByLabel('刪除').click(),
    ])

    expect(deleteIds.length).toBeGreaterThan(0)
    await expect(page.getByRole('row', { name: /線性代數/ })).toHaveCount(0)
  })
})
