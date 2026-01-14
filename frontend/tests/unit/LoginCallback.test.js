import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import LoginCallback from '@/views/LoginCallback.vue'

const routerMock = {
  push: vi.fn(),
  replace: vi.fn(),
}

let consoleErrorSpy

vi.mock('@/utils/svgBg', () => ({
  getCodeBgSvg: vi.fn(() => 'mocked-bg'),
}))

const originalURLSearchParams = window.URLSearchParams

function mockURLSearchParams(tokenValue) {
  window.URLSearchParams = class {
    constructor() {}
    get(key) {
      if (key === 'token') {
        return tokenValue
      }
      return null
    }
  }
}

describe('LoginCallback view', () => {
  beforeEach(() => {
    routerMock.push.mockReset()
    routerMock.replace.mockReset()
    sessionStorage.clear()
    localStorage.clear()
    document.body.innerHTML = '<div class="code-background"></div>'
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    document.body.innerHTML = ''
    window.URLSearchParams = originalURLSearchParams
    consoleErrorSpy.mockRestore()
  })

  it('stores token and redirects to archive when token present', async () => {
    mockURLSearchParams('test-token')

    mount(LoginCallback, {
      global: {
        mocks: {
          $router: routerMock,
        },
        stubs: {
          Card: { template: '<div><slot name="title"></slot><slot name="content"></slot></div>' },
          Button: { template: '<button><slot /></button>' },
          ProgressSpinner: { template: '<div class="spinner"></div>' },
        },
      },
    })

    await flushPromises()

    expect(sessionStorage.getItem('auth-token')).toBe('test-token')
    expect(routerMock.replace).toHaveBeenCalledWith('/archive')
  })

  it('shows error message when token missing', async () => {
    mockURLSearchParams(null)

    const wrapper = mount(LoginCallback, {
      global: {
        mocks: {
          $router: routerMock,
        },
        stubs: {
          Card: { template: '<div><slot name="title"></slot><slot name="content"></slot></div>' },
          Button: { template: '<button><slot /></button>' },
          ProgressSpinner: { template: '<div class="spinner"></div>' },
        },
      },
    })

    await flushPromises()

    expect(routerMock.push).not.toHaveBeenCalledWith('/archive')
    expect(sessionStorage.getItem('auth-token')).toBeNull()
    expect(wrapper.text()).toContain('登入失敗')
    expect(wrapper.text()).toContain('驗證失敗')
  })
})
