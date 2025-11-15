import { adminTest as test, expect } from '../support/adminTest'
import { mockAdminCourseEndpoints, mockAdminUserEndpoints } from '../support/adminFixtures'
import { JSON_HEADERS } from '../support/constants'
import { clickWhenVisible } from '../support/ui'

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
    await clickWhenVisible(userTab)

    await expect(page.getByRole('row', { name: /Admin/ })).toBeVisible()
    await expect(page.getByRole('row', { name: /一般使用者/ })).toBeVisible()

    await clickWhenVisible(page.getByRole('button', { name: '新增使用者' }))

    const createDialog = page.getByRole('dialog', { name: '新增使用者' })
    await expect(createDialog).toBeVisible()

    await createDialog.getByPlaceholder('輸入使用者名稱').fill('新用戶')
    await createDialog.getByPlaceholder('輸入電子郵件').fill('newuser@example.com')
    await createDialog.getByPlaceholder('輸入密碼').fill('Passw0rd!')
    await clickWhenVisible(createDialog.locator('.p-checkbox').first())

    const previousCreateCount = createPayloads.length
    await clickWhenVisible(createDialog.getByRole('button', { name: '新增' }))
    await expect
      .poll(() => createPayloads.length, { message: '等待建立 API 完成' })
      .toBe(previousCreateCount + 1)

    expect(createPayloads.at(-1)).toMatchObject({
      name: '新用戶',
      email: 'newuser@example.com',
      is_admin: true,
    })
    await expect(page.getByRole('row', { name: /新用戶/ })).toBeVisible()

    const targetRow = page.getByRole('row', { name: /一般使用者/ })
    await clickWhenVisible(targetRow.getByRole('button', { name: '編輯' }))

    const editDialog = page.getByRole('dialog', { name: '編輯使用者' })
    await expect(editDialog).toBeVisible()

    await editDialog.getByPlaceholder('輸入使用者名稱').fill('一般使用者 (更新)')
    await clickWhenVisible(editDialog.locator('.p-checkbox').first())

    const previousUpdateCount = updatePayloads.length
    await clickWhenVisible(editDialog.getByRole('button', { name: '更新' }))
    await expect
      .poll(() => updatePayloads.length, { message: '等待更新 API 完成' })
      .toBe(previousUpdateCount + 1)

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
    await clickWhenVisible(deleteRow.getByRole('button', { name: '刪除' }))

    const dialog = page.getByRole('alertdialog', { name: '刪除確認' })
    await expect(dialog).toBeVisible()

    const previousDeleteCount = deleteIds.length
    await clickWhenVisible(dialog.getByLabel('刪除'))
    await expect
      .poll(() => deleteIds.length, { message: '等待刪除 API 完成' })
      .toBe(previousDeleteCount + 1)

    expect(deleteIds.length).toBeGreaterThan(0)
    await expect(page.getByRole('row', { name: /新用戶/ })).toHaveCount(0)
  })
})
