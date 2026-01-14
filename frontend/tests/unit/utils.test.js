import { Buffer } from 'node:buffer'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'

describe('utils/http', () => {
  let isUnauthorizedError

  beforeEach(async () => {
    const module = await import('@/utils/http.js')
    isUnauthorizedError = module.isUnauthorizedError
  })

  it('returns false for null error', () => {
    expect(isUnauthorizedError(null)).toBe(false)
  })

  it('detects explicit unauthorized flag', () => {
    expect(isUnauthorizedError({ isUnauthorized: true })).toBe(true)
  })

  it('checks nested response status', () => {
    expect(isUnauthorizedError({ response: { status: 401 } })).toBe(true)
    expect(isUnauthorizedError({ response: { status: 500 } })).toBe(false)
  })

  it('checks direct status', () => {
    expect(isUnauthorizedError({ status: 401 })).toBe(true)
  })
})

describe('utils/toast', () => {
  it('sets and retrieves global toast instance', async () => {
    const module = await import('@/utils/toast.js')
    const { setGlobalToast, getGlobalToast } = module

    expect(getGlobalToast()).toBeNull()

    const toastInstance = { add: () => {} }
    setGlobalToast(toastInstance)
    expect(getGlobalToast()).toBe(toastInstance)
  })
})

describe('utils/svgBg', () => {
  const originalGetComputedStyle = window.getComputedStyle

  afterEach(() => {
    window.getComputedStyle = originalGetComputedStyle
  })

  it('returns SVG background using computed style variable', async () => {
    window.getComputedStyle = vi.fn(() => ({
      getPropertyValue: vi.fn(() => 'rgba(10, 20, 30, 0.5)'),
    }))

    const module = await import('@/utils/svgBg.js')
    const result = module.getCodeBgSvg()

    expect(result).toContain('data:image/svg+xml')
    expect(result).toContain(encodeURIComponent('rgba(10, 20, 30, 0.5)'))
  })
})

describe('utils/time', () => {
  it('formats future dates as 剛剛', async () => {
    const { formatRelativeTime } = await import('@/utils/time.js')
    const future = new Date(Date.now() + 5 * 60 * 1000).toISOString()
    expect(formatRelativeTime(future)).toBe('剛剛')
  })
})

describe('utils/analytics', () => {
  let analyticsModule
  let consoleErrorSpy

  beforeEach(async () => {
    vi.resetModules()
    analyticsModule = await import('@/utils/analytics.js')
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    delete window.umami
    consoleErrorSpy.mockRestore()
  })

  it('tracks event when umami is available', () => {
    const trackSpy = vi.fn()
    window.umami = { track: trackSpy }

    analyticsModule.trackEvent('test-event', { foo: 'bar' })

    expect(trackSpy).toHaveBeenCalledWith('test-event', { foo: 'bar' })
  })

  it('handles missing umami without throwing', () => {
    expect(() => analyticsModule.trackEvent('test-event')).not.toThrow()
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('delegates trackPageView to trackEvent when umami available', () => {
    const trackSpy = vi.fn()
    window.umami = { track: trackSpy }

    analyticsModule.trackPageView('home')

    expect(trackSpy).toHaveBeenCalledWith('pageview', { page: 'home' })
  })
})

describe('utils/auth', () => {
  let originalAtob

  const createToken = (payload) => {
    const header = { alg: 'HS256', typ: 'JWT' }
    const base64UrlEncode = (obj) => Buffer.from(JSON.stringify(obj)).toString('base64url')
    return `${base64UrlEncode(header)}.${base64UrlEncode(payload)}.signature`
  }

  const importModule = async () => await import('@/utils/auth.js')

  beforeEach(() => {
    sessionStorage.clear()
    originalAtob = globalThis.atob
    globalThis.atob = (base64) => Buffer.from(base64, 'base64').toString('binary')
  })

  afterEach(() => {
    if (originalAtob) {
      globalThis.atob = originalAtob
    } else {
      delete globalThis.atob
    }
  })

  it('decodes valid tokens and reports authentication state', async () => {
    const payload = {
      uid: 42,
      email: 'user@example.com',
      name: 'User',
      is_admin: true,
      avatar_url: 'https://avatar',
      realm_roles: { admin: true },
      exp: Math.floor(Date.now() / 1000) + 3600,
    }
    const token = createToken(payload)

    sessionStorage.setItem('auth-token', token)

    const { decodeToken, getCurrentUser, isAuthenticated } = await importModule()

    expect(decodeToken(token)).toEqual(payload)
    expect(getCurrentUser()).toEqual({
      id: 42,
      email: 'user@example.com',
      name: 'User',
      is_admin: true,
      avatar: 'https://avatar',
      roles: { admin: true },
    })
    expect(isAuthenticated()).toBe(true)
  })

  it('handles invalid tokens gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    sessionStorage.setItem('auth-token', 'invalid-token')

    const pastPayload = {
      uid: 1,
      email: 'old@example.com',
      name: 'Past',
      is_admin: false,
      exp: Math.floor(Date.now() / 1000) - 120,
    }
    const expiredToken = createToken(pastPayload)

    const { decodeToken, getCurrentUser, isAuthenticated } = await importModule()

    expect(decodeToken('not-a-token')).toBeNull()
    expect(getCurrentUser()).toBeNull()
    expect(consoleErrorSpy).toHaveBeenCalled()

    sessionStorage.setItem('auth-token', expiredToken)
    expect(isAuthenticated()).toBe(false)

    consoleErrorSpy.mockRestore()
  })

  it('persists tokens via helpers', async () => {
    const { setToken, getToken, removeToken } = await importModule()

    setToken('stored-token')
    expect(getToken()).toBe('stored-token')

    removeToken()
    expect(getToken()).toBeNull()
  })
})
