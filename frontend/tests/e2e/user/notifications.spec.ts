import { userTest as test, expect } from '../support/userTest'
import { JSON_HEADERS } from '../support/constants'
import { clickWhenVisible } from '../support/ui'

const COURSES_FIXTURE = {
  freshman: [
    { id: 101, name: '資料結構與物件導向程式設計' },
    { id: 102, name: '離散數學' },
  ],
  sophomore: [],
  junior: [],
  senior: [],
  graduate: [],
  interdisciplinary: [],
  general: [],
}

const ACTIVE_NOTIFICATION = {
  id: 9001,
  title: '系統維護公告',
  body: '系統將於今晚 23:00-23:30 進行維護，請提前完成手邊作業。',
  severity: 'danger',
  created_at: '2025-10-30T15:00:00Z',
  updated_at: '2025-10-30T15:05:00Z',
  is_active: true,
}

test.describe('User › Notifications', () => {
  test('shows notification modal and persists dismissal state', async ({ page }) => {
    await page.route('**/api/courses', async (route) => {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify(COURSES_FIXTURE),
      })
    })

    await page.route('**/api/notifications/active', async (route) => {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify([ACTIVE_NOTIFICATION]),
      })
    })

    await page.goto('/archive')

    const modal = page.getByRole('dialog', { name: '系統公告' })
    await expect(modal).toBeVisible({ timeout: 15000 })

    await expect(modal.getByText('系統維護公告')).toBeVisible()
    await expect(modal.getByText('重要')).toBeVisible()

    await clickWhenVisible(modal.getByRole('button', { name: '不再顯示' }))

    await expect(modal).toBeHidden({ timeout: 5000 })

    const expectedTimestamp = new Date(ACTIVE_NOTIFICATION.updated_at).getTime()
    await expect
      .poll(async () => {
        return page.evaluate(() => window.localStorage.getItem('notification-last-seen'))
      })
      .toBe(String(expectedTimestamp))
  })

  test('opens notification center and shows detail content', async ({ page }) => {
    const ALL_NOTIFICATIONS = [
      ACTIVE_NOTIFICATION,
      {
        id: 8999,
        title: '版本更新通知',
        body: '新版本已上線，歡迎回饋使用心得。',
        severity: 'info',
        created_at: '2025-10-28T10:00:00Z',
        updated_at: '2025-10-28T10:00:00Z',
        is_active: true,
      },
    ]

    await page.route('**/api/courses', async (route) => {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify(COURSES_FIXTURE),
      })
    })

    await page.route('**/api/notifications/active', async (route) => {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify([ACTIVE_NOTIFICATION]),
      })
    })

    await page.route('**/api/notifications', async (route) => {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify(ALL_NOTIFICATIONS),
      })
    })

    await page.goto('/archive', { waitUntil: 'networkidle' })

    const modal = page.getByRole('dialog', { name: '系統公告' })
    await expect(modal).toBeVisible()

    await clickWhenVisible(modal.getByRole('button', { name: '顯示全部' }))

    const centerDialog = page.getByRole('dialog', { name: '公告中心' })
    await expect(centerDialog).toBeVisible({ timeout: 10000 })

    await expect(centerDialog.getByText('系統維護公告')).toBeVisible()
    await expect(centerDialog.getByText('版本更新通知')).toBeVisible()

    await clickWhenVisible(centerDialog.getByRole('button', { name: '檢視' }).first())

    const detailDialog = page.getByRole('dialog', { name: '公告內容' })
    await expect(detailDialog).toBeVisible({ timeout: 5000 })
    await expect(detailDialog.getByText('系統維護公告')).toBeVisible()
    await expect(detailDialog.getByText('23:00-23:30')).toBeVisible()

    const expectedTimestamp = new Date(ACTIVE_NOTIFICATION.updated_at).getTime()
    await expect
      .poll(async () => {
        return page.evaluate(() => window.localStorage.getItem('notification-last-seen'))
      })
      .toBe(String(expectedTimestamp))
  })
})
