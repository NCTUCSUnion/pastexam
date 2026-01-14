import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

const activeNotifications = vi.hoisted(() => [
  { id: 2, title: 'Old', created_at: '2025-10-01T10:00:00Z', updated_at: '2025-10-01T10:00:00Z' },
  { id: 5, title: 'New', created_at: '2025-11-01T10:00:00Z', updated_at: '2025-11-01T10:00:00Z' },
])

const allNotifications = vi.hoisted(() => [
  {
    id: 1,
    title: 'Archived',
    created_at: '2025-09-01T10:00:00Z',
    updated_at: '2025-09-01T10:00:00Z',
  },
  {
    id: 3,
    title: 'Another',
    created_at: '2025-10-15T10:00:00Z',
    updated_at: '2025-10-15T10:00:00Z',
  },
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
    // Sort by updated_at descending
    expect(composable.state.active.map((n) => n.id)).toEqual([5, 2])
    expect(composable.state.modalVisible).toBe(true)
    expect(composable.latestUnseenNotification.value?.id).toBe(5)
  })

  it('marks notification as seen and persists last seen timestamp', async () => {
    const composable = await importComposable()
    await composable.initNotifications()

    const notification = {
      id: 5,
      created_at: '2025-11-01T10:00:00Z',
      updated_at: '2025-11-01T10:00:00Z',
    }
    composable.markNotificationAsSeen(notification)

    expect(composable.state.modalVisible).toBe(false)
    const expectedTimestamp = new Date('2025-11-01T10:00:00Z').getTime()
    expect(composable.lastSeenTimestamp.value).toBe(expectedTimestamp)
    expect(localStorage.getItem('notification-last-seen')).toBe(String(expectedTimestamp))
  })

  it('loads all notifications when opening center', async () => {
    const composable = await importComposable()

    await composable.openCenter()

    expect(getAllMock).toHaveBeenCalledTimes(1)
    expect(composable.state.centerVisible).toBe(true)
    // Sort by updated_at descending
    expect(composable.state.all.map((n) => n.id)).toEqual([3, 1])
  })

  it('logs warning when reading stored last seen timestamp fails', async () => {
    const getItemSpy = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('read fail')
    })

    const composable = await importComposable()

    expect(consoleWarnSpy).toHaveBeenCalledWith(
      expect.stringContaining('Failed to read notification last seen timestamp:'),
      expect.any(Error)
    )
    expect(composable.lastSeenTimestamp.value).toBe(0)

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

  it('logs errors when persisting last seen timestamp fails', async () => {
    const composable = await importComposable()
    await composable.initNotifications()

    const setItemSpy = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('persist fail')
    })

    consoleErrorSpy.mockClear()
    const notification = {
      id: 10,
      created_at: '2025-11-02T10:00:00Z',
      updated_at: '2025-11-02T10:00:00Z',
    }
    composable.markNotificationAsSeen(notification)

    const expectedTimestamp = new Date('2025-11-02T10:00:00Z').getTime()
    expect(composable.lastSeenTimestamp.value).toBe(expectedTimestamp)
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Failed to persist notification last seen timestamp:',
      expect.any(Error)
    )

    setItemSpy.mockRestore()
  })
})
