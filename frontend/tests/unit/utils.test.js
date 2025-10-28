import { describe, it, expect, beforeEach } from 'vitest'

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
