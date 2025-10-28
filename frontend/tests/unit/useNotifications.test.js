import { describe, it, expect, beforeEach, vi } from 'vitest'

const activeNotifications = vi.hoisted(() => [
  { id: 2, title: 'Old' },
  { id: 5, title: 'New' },
])

const allNotifications = vi.hoisted(() => [
  { id: 1, title: 'Archived' },
  { id: 3, title: 'Another' },
])

const getActiveMock = vi.hoisted(() =>
  vi.fn(async () => ({
    data: activeNotifications.map((item) => ({ ...item })),
  }))
)

const getAllMock = vi.hoisted(() =>
  vi.fn(async () => ({
    data: allNotifications.map((item) => ({ ...item })),
  }))
)

vi.mock('@/api', () => ({
  notificationService: {
    getActive: getActiveMock,
    getAll: getAllMock,
  },
}))

async function importComposable() {
  const module = await import('@/utils/useNotifications.js')
  return module.useNotifications()
}

describe('useNotifications composable', () => {
  beforeEach(() => {
    vi.resetModules()
    getActiveMock.mockClear()
    getAllMock.mockClear()
    localStorage.clear()
  })

  it('initializes by fetching active notifications and opens modal when unseen exists', async () => {
    const composable = await importComposable()

    await composable.initNotifications()

    expect(getActiveMock).toHaveBeenCalledTimes(1)
    expect(composable.state.active.map((n) => n.id)).toEqual([5, 2])
    expect(composable.state.modalVisible).toBe(true)
    expect(composable.latestUnseenNotification.value?.id).toBe(5)
  })

  it('marks notification as seen and persists last seen id', async () => {
    const composable = await importComposable()
    await composable.initNotifications()

    composable.markNotificationAsSeen({ id: 5 })

    expect(composable.state.modalVisible).toBe(false)
    expect(composable.lastSeenId.value).toBe(5)
    expect(localStorage.getItem('pastexam_notification_last_seen')).toBe('5')
  })

  it('loads all notifications when opening center', async () => {
    const composable = await importComposable()

    await composable.openCenter()

    expect(getAllMock).toHaveBeenCalledTimes(1)
    expect(composable.state.centerVisible).toBe(true)
    expect(composable.state.all.map((n) => n.id)).toEqual([3, 1])
  })
})
