import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

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

const isUnauthorizedErrorMock = vi.hoisted(() => vi.fn(() => false))

vi.mock('@/api', () => ({
  notificationService: {
    getActive: getActiveMock,
    getAll: getAllMock,
  },
}))

vi.mock('@/utils/http', () => ({
  isUnauthorizedError: isUnauthorizedErrorMock,
}))

async function importComposable() {
  const module = await import('@/utils/useNotifications.js')
  return module.useNotifications()
}

describe('useNotifications composable', () => {
  let consoleErrorSpy
  let consoleWarnSpy

  beforeEach(() => {
    vi.resetModules()
    getActiveMock.mockClear()
    getAllMock.mockClear()
    getActiveMock.mockImplementation(async () => ({
      data: activeNotifications.map((item) => ({ ...item })),
    }))
    getAllMock.mockImplementation(async () => ({
      data: allNotifications.map((item) => ({ ...item })),
    }))
    isUnauthorizedErrorMock.mockImplementation(() => false)
    localStorage.clear()
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
    consoleWarnSpy.mockRestore()
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

  it('logs warning when reading stored last seen id fails', async () => {
    const getItemSpy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('read fail')
    })

    const composable = await importComposable()

    expect(consoleWarnSpy).toHaveBeenCalledWith(
      expect.stringContaining('Failed to read notification last seen id:'),
      expect.any(Error)
    )
    expect(composable.lastSeenId.value).toBe(0)

    getItemSpy.mockRestore()
  })

  it('handles refreshActive errors gracefully', async () => {
    const error = new Error('active fail')
    getActiveMock.mockRejectedValueOnce(error)

    const composable = await importComposable()
    consoleErrorSpy.mockClear()

    await composable.refreshActive()

    expect(composable.errors.active).toBe(error)
    expect(composable.state.modalVisible).toBe(false)
    expect(consoleErrorSpy).toHaveBeenCalledWith('Failed to load active notifications:', error)
  })

  it('handles refreshAll unauthorized errors without opening center', async () => {
    const error = new Error('unauthorized')
    getAllMock.mockRejectedValueOnce(error)
    isUnauthorizedErrorMock.mockImplementation(() => true)

    const composable = await importComposable()
    consoleErrorSpy.mockClear()

    await composable.openCenter()

    expect(composable.errors.all).toBe(error)
    expect(composable.state.centerVisible).toBe(false)
    expect(consoleErrorSpy).not.toHaveBeenCalled()

    isUnauthorizedErrorMock.mockImplementation(() => false)
  })

  it('skips refreshing all notifications when already loading', async () => {
    const composable = await importComposable()
    composable.state.loadingAll = true

    await composable.refreshAll()

    expect(getAllMock).not.toHaveBeenCalled()
  })

  it('logs errors when persisting last seen id fails', async () => {
    const composable = await importComposable()
    await composable.initNotifications()

    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('persist fail')
    })

    consoleErrorSpy.mockClear()
    composable.markNotificationAsSeen({ id: 10 })

    expect(composable.lastSeenId.value).toBe(10)
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Failed to persist notification last seen id:',
      expect.any(Error)
    )

    setItemSpy.mockRestore()
  })
})
