import { adminTest as test, expect } from '../support/adminTest'
import { mockAdminCourseEndpoints, mockAdminUserEndpoints } from '../support/adminFixtures'
import { JSON_HEADERS } from '../support/constants'

test.describe('Admin Dashboard › Users', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/notifications/active', async (route) => {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify([]),
      })
    })
  })

  test('allows creating, editing, and deleting users', async ({ page }) => {
    await mockAdminCourseEndpoints(page)
    const { createPayloads, updatePayloads, deleteIds } = await mockAdminUserEndpoints(page)

    await page.goto('/admin', { waitUntil: 'networkidle' })
    await expect(page).toHaveURL(/\/admin$/)

    const tabs = page.getByRole('tab')
    await expect(tabs).toHaveCount(3)
    const userTab = tabs.nth(1)
    await userTab.click()

    await expect(page.getByRole('row', { name: /Admin/ })).toBeVisible()
    await expect(page.getByRole('row', { name: /一般使用者/ })).toBeVisible()

    await page.getByRole('button', { name: '新增使用者' }).click()

    const createDialog = page.getByRole('dialog', { name: '新增使用者' })
    await expect(createDialog).toBeVisible()

    await createDialog.getByPlaceholder('輸入使用者名稱').fill('新用戶')
    await createDialog.getByPlaceholder('輸入電子郵件').fill('newuser@example.com')
    await createDialog.getByPlaceholder('輸入密碼').fill('Passw0rd!')
    await createDialog.locator('.p-checkbox').first().click()

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/users/admin/users') &&
          response.request().method() === 'POST'
      ),
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/users/admin/users') && response.request().method() === 'GET'
      ),
      createDialog.getByRole('button', { name: '新增' }).click(),
    ])

    expect(createPayloads.at(-1)).toMatchObject({
      name: '新用戶',
      email: 'newuser@example.com',
      is_admin: true,
    })
    await expect(page.getByRole('row', { name: /新用戶/ })).toBeVisible()

    const targetRow = page.getByRole('row', { name: /一般使用者/ })
    await targetRow.getByRole('button', { name: '編輯' }).click()

    const editDialog = page.getByRole('dialog', { name: '編輯使用者' })
    await expect(editDialog).toBeVisible()

    await editDialog.getByPlaceholder('輸入使用者名稱').fill('一般使用者 (更新)')
    await editDialog.locator('.p-checkbox').first().click()

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/users/admin/users') && response.request().method() === 'PUT'
      ),
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/users/admin/users') && response.request().method() === 'GET'
      ),
      editDialog.getByRole('button', { name: '更新' }).click(),
    ])

    expect(updatePayloads.at(-1)).toMatchObject({
      payload: {
        name: '一般使用者 (更新)',
        email: 'user@example.com',
        is_admin: true,
      },
    })
    const updatedUserRow = page.getByRole('row', { name: /一般使用者 \(更新\)/ })
    await expect(updatedUserRow).toBeVisible()
    await expect(updatedUserRow).toContainText('是')

    const deleteRow = page.getByRole('row', { name: /新用戶/ })
    await deleteRow.getByRole('button', { name: '刪除' }).click()

    const dialog = page.getByRole('alertdialog', { name: '刪除確認' })
    await expect(dialog).toBeVisible()

    await Promise.all([
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/users/admin/users') &&
          response.request().method() === 'DELETE'
      ),
      page.waitForResponse(
        (response) =>
          response.url().includes('/api/users/admin/users') && response.request().method() === 'GET'
      ),
      dialog.getByLabel('刪除').click(),
    ])

    expect(deleteIds.length).toBeGreaterThan(0)
    await expect(page.getByRole('row', { name: /新用戶/ })).toHaveCount(0)
  })
})
