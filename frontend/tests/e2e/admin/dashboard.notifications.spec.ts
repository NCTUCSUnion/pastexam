import { adminTest as test, expect } from '../support/adminTest'
import { mockAdminCourseEndpoints, mockAdminNotificationEndpoints } from '../support/adminFixtures'
import { JSON_HEADERS } from '../support/constants'
import { clickWhenVisible } from '../support/ui'

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

    await page.goto('/admin', { waitUntil: 'networkidle' })
    await expect(page).toHaveURL(/\/admin$/)

    const tabs = page.getByRole('tab')
    await expect(tabs).toHaveCount(3)
    await clickWhenVisible(tabs.nth(2))

    const maintenanceRow = page.getByRole('row', { name: /系統維護公告/ })
    await expect(maintenanceRow).toBeVisible()
    await expect(maintenanceRow).toContainText('啟用中')

    await clickWhenVisible(page.getByRole('button', { name: '新增公告' }))

    const createDialog = page.getByRole('dialog', { name: '新增公告' })
    await expect(createDialog).toBeVisible()

    await createDialog.getByPlaceholder('輸入公告標題').fill('版本更新公告')
    await createDialog.getByPlaceholder('輸入公告內容').fill('新版功能已上線，歡迎使用。')

    const severitySelect = createDialog
      .locator('label', { hasText: '重要程度' })
      .locator('xpath=following-sibling::*[1]')
    await clickWhenVisible(severitySelect)
    await clickWhenVisible(page.getByRole('option', { name: '重要' }))

    await clickWhenVisible(createDialog.locator('.p-toggleswitch'))

    const previousCreateCount = createPayloads.length
    await clickWhenVisible(createDialog.getByRole('button', { name: '新增' }))
    await expect
      .poll(() => createPayloads.length, { message: '等待新增 API 完成' })
      .toBe(previousCreateCount + 1)

    const newNotificationRow = page.getByRole('row', { name: /版本更新公告/ })
    await expect(newNotificationRow).toBeVisible()
    await expect(newNotificationRow).toContainText('已停用')
    expect(createPayloads.at(-1)).toMatchObject({
      title: '版本更新公告',
      severity: 'danger',
      is_active: false,
    })

    await clickWhenVisible(maintenanceRow.getByRole('button', { name: '編輯' }))

    const editDialog = page.getByRole('dialog', { name: '編輯公告' })
    await expect(editDialog).toBeVisible()

    const bodyInput = editDialog.getByPlaceholder('輸入公告內容')
    await expect(bodyInput).toHaveValue('系統將於週末進行維護')
    await bodyInput.fill('維護作業提前結束。')

    const editSeveritySelect = editDialog
      .locator('label', { hasText: '重要程度' })
      .locator('xpath=following-sibling::*[1]')
    await clickWhenVisible(editSeveritySelect)
    await clickWhenVisible(page.getByRole('option', { name: '一般' }))

    await clickWhenVisible(editDialog.locator('.p-toggleswitch'))

    const previousUpdateCount = updatePayloads.length
    await clickWhenVisible(editDialog.getByRole('button', { name: '更新' }))
    await expect
      .poll(() => updatePayloads.length, { message: '等待更新 API 完成' })
      .toBe(previousUpdateCount + 1)

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

    await clickWhenVisible(newNotificationRow.getByRole('button', { name: '刪除' }))

    const dialog = page.getByRole('alertdialog', { name: '刪除確認' })
    await expect(dialog).toBeVisible()

    const previousDeleteCount = deleteIds.length
    await clickWhenVisible(dialog.getByLabel('刪除'))
    await expect
      .poll(() => deleteIds.length, { message: '等待刪除 API 完成' })
      .toBe(previousDeleteCount + 1)

    expect(deleteIds.length).toBeGreaterThan(0)
    await expect(page.getByRole('row', { name: /版本更新公告/ })).toHaveCount(0)
  })
})
