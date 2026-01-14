import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

let requestSuccess
let requestError
let responseSuccess
let responseError

let axiosCreateSpy
let toastAddMock
let routerPushMock
let handlerStore
let currentRouteMock

const setupClientModule = async () => {
  handlerStore = {
    request: [],
    requestErr: [],
    response: [],
    responseErr: [],
  }

  axiosCreateSpy = vi.fn(() => ({
    interceptors: {
      request: {
        use: (success, error) => {
          handlerStore.request.push(success)
          handlerStore.requestErr.push(error)
        },
      },
      response: {
        use: (success, error) => {
          handlerStore.response.push(success)
          handlerStore.responseErr.push(error)
        },
      },
    },
  }))

  vi.doMock('axios', () => ({
    default: {
      create: axiosCreateSpy,
    },
  }))

  toastAddMock = vi.fn()
  vi.doMock('@/utils/toast', () => ({
    getGlobalToast: () => ({ add: toastAddMock }),
  }))

  routerPushMock = vi.fn()
  vi.doMock('@/router', () => ({
    default: {
      currentRoute: currentRouteMock || { value: { path: '/archive' } },
      push: routerPushMock,
    },
  }))

  vi.resetModules()
  await import('@/api/services/client.js')

  requestSuccess = handlerStore.request[0]
  requestError = handlerStore.requestErr[0]
  responseSuccess = handlerStore.response[0]
  responseError = handlerStore.responseErr[0]
}

describe('api client interceptors', () => {
  beforeEach(async () => {
    vi.restoreAllMocks()
    vi.resetModules()
    sessionStorage.clear()
    currentRouteMock = undefined
    await setupClientModule()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('sets authorization header when token present', () => {
    const config = { headers: {} }
    requestSuccess(config)
    expect(config.headers.Authorization).toBeUndefined()

    sessionStorage.setItem('auth-token', 'token-xyz')
    const configWithToken = { headers: {} }
    expect(requestSuccess(configWithToken).headers.Authorization).toBe('Bearer token-xyz')
  })

  it('propagates request errors', async () => {
    const error = new Error('request failed')
    await expect(requestError(error)).rejects.toThrow('request failed')
  })

  it('passes through successful responses', () => {
    const response = { data: 1 }
    expect(responseSuccess(response)).toBe(response)
  })

  it('flags invalid credentials on login failure', async () => {
    const error = {
      response: { status: 401 },
      config: { method: 'post', url: '/auth/login' },
    }
    await expect(responseError(error)).rejects.toBe(error)
    expect(error.isInvalidCredentials).toBe(true)
    expect(toastAddMock).not.toHaveBeenCalled()
  })

  it('handles general unauthorized responses', async () => {
    sessionStorage.setItem('auth-token', 'token-xyz')
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')
    vi.useFakeTimers()

    const error = {
      response: { status: 401 },
      config: { method: 'get', url: '/api/resource' },
    }

    await expect(responseError(error)).rejects.toBe(error)

    expect(sessionStorage.getItem('auth-token')).toBeNull()
    expect(error.isUnauthorized).toBe(true)
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({
        severity: 'warn',
        summary: '登入階段已過期',
      })
    )
    expect(dispatchSpy).toHaveBeenCalledWith(expect.any(CustomEvent))
    expect(routerPushMock).toHaveBeenCalledWith('/')

    vi.runAllTimers()
    dispatchSpy.mockRestore()
  })

  it('handles unauthorized websocket close code', async () => {
    sessionStorage.setItem('auth-token', 'token-xyz')
    localStorage.setItem('auth-token', 'token-xyz')
    const dispatchSpy = vi.spyOn(window, 'dispatchEvent')

    const { bindUnauthorizedWebSocket, WS_UNAUTHORIZED_CLOSE_CODE } =
      await import('@/api/services/client.js')

    const closeHandlers = []
    const ws = {
      addEventListener: vi.fn((type, handler) => {
        if (type === 'close') closeHandlers.push(handler)
      }),
    }

    bindUnauthorizedWebSocket(ws)
    closeHandlers.forEach((handler) => handler({ code: WS_UNAUTHORIZED_CLOSE_CODE }))

    expect(sessionStorage.getItem('auth-token')).toBeNull()
    expect(localStorage.getItem('auth-token')).toBeNull()
    expect(dispatchSpy).toHaveBeenCalledWith(expect.any(CustomEvent))
    expect(routerPushMock).toHaveBeenCalledWith('/')

    dispatchSpy.mockRestore()
  })

  it('does not redirect when already on root path', async () => {
    vi.resetModules()
    currentRouteMock = { value: { path: '/', fullPath: '/' } }
    await setupClientModule()

    const error = {
      response: { status: 401 },
      config: { method: 'get', url: '/api/resource' },
    }

    await expect(responseError(error)).rejects.toBe(error)
    expect(routerPushMock).not.toHaveBeenCalled()
  })

  it('propagates non-401 errors unchanged', async () => {
    const error = {
      response: { status: 500 },
      config: { method: 'get', url: '/api/resource' },
    }
    await expect(responseError(error)).rejects.toBe(error)
    expect(toastAddMock).not.toHaveBeenCalled()
  })
})
