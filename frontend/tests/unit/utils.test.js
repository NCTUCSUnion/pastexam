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
