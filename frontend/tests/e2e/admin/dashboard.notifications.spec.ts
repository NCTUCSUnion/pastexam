import { adminTest as test, expect } from '../support/adminTest'
import { mockAdminCourseEndpoints, mockAdminNotificationEndpoints } from '../support/adminFixtures'
import { JSON_HEADERS } from '../support/constants'

test.describe('Admin Dashboard › Notifications', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/notifications/active', async (route) => {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify([]),
      })
    })
  })

  test('allows managing notifications end-to-end', async ({ page }) => {
    await mockAdminCourseEndpoints(page)
    const { createPayloads, updatePayloads, deleteIds } = await mockAdminNotificationEndpoints(page)

    await page.goto('/admin', { waitUntil: 'domcontentloaded' })
    await expect(page).toHaveURL(/\/admin$/)

    const tabs = page.getByRole('tab')
    await expect(tabs).toHaveCount(3)
    await tabs.nth(2).click()

    const maintenanceRow = page.getByRole('row', { name: /系統維護公告/ })
    await expect(maintenanceRow).toBeVisible()
    await expect(maintenanceRow).toContainText('啟用中')

    await page.getByRole('button', { name: '新增公告' }).click()

    const createDialog = page.getByRole('dialog', { name: '新增公告' })
    await expect(createDialog).toBeVisible()

    await createDialog.getByPlaceholder('輸入公告標題').fill('版本更新公告')
    await createDialog.getByPlaceholder('輸入公告內容').fill('新版功能已上線，歡迎使用。')

    const severitySelect = createDialog
      .locator('label', { hasText: '重要程度' })
      .locator('xpath=following-sibling::*[1]')
    await severitySelect.click()
    await page.getByRole('option', { name: '重要' }).click()

    await createDialog.locator('.p-toggleswitch').click()

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/notifications/admin/notifications') &&
          response.request().method() === 'POST'
      ),
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/notifications/admin/notifications') &&
          response.request().method() === 'GET'
      ),
      createDialog.getByRole('button', { name: '新增' }).click(),
    ])

    const newNotificationRow = page.getByRole('row', { name: /版本更新公告/ })
    await expect(newNotificationRow).toBeVisible()
    await expect(newNotificationRow).toContainText('已停用')
    expect(createPayloads.at(-1)).toMatchObject({
      title: '版本更新公告',
      severity: 'danger',
      is_active: false,
    })

    await maintenanceRow.getByRole('button', { name: '編輯' }).click()

    const editDialog = page.getByRole('dialog', { name: '編輯公告' })
    await expect(editDialog).toBeVisible()

    await editDialog.getByPlaceholder('輸入公告內容').fill('維護作業提前結束。')

    const editSeveritySelect = editDialog
      .locator('label', { hasText: '重要程度' })
      .locator('xpath=following-sibling::*[1]')
    await editSeveritySelect.click()
    await page.getByRole('option', { name: '一般' }).click()

    await editDialog.locator('.p-toggleswitch').click()

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/notifications/admin/notifications') &&
          response.request().method() === 'PUT'
      ),
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/notifications/admin/notifications') &&
          response.request().method() === 'GET'
      ),
      editDialog.getByRole('button', { name: '更新' }).click(),
    ])

    expect(updatePayloads.at(-1)).toMatchObject({
      payload: {
        body: '維護作業提前結束。',
        severity: 'info',
        is_active: false,
      },
    })
    const updatedMaintenanceRow = page.getByRole('row', { name: /系統維護公告/ })
    await expect(updatedMaintenanceRow).toContainText('一般')
    await expect(updatedMaintenanceRow).toContainText('未生效')

    await newNotificationRow.getByRole('button', { name: '刪除' }).click()

    const dialog = page.getByRole('alertdialog', { name: '刪除確認' })
    await expect(dialog).toBeVisible()

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/notifications/admin/notifications') &&
          response.request().method() === 'DELETE'
      ),
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/notifications/admin/notifications') &&
          response.request().method() === 'GET'
      ),
      dialog.getByLabel('刪除').click(),
    ])

    expect(deleteIds.length).toBeGreaterThan(0)
    await expect(page.getByRole('row', { name: /版本更新公告/ })).toHaveCount(0)
  })
})
