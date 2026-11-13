import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

const exchangeOAuthCode = vi.hoisted(() => vi.fn())

vi.mock('@/api', () => ({
  authService: { exchangeOAuthCode },
}))

vi.mock('@/utils/svgBg', () => ({
  getCodeBgSvg: vi.fn(() => 'mocked-bg'),
}))

import LoginCallback from '@/views/LoginCallback.vue'

const routerMock = {
  push: vi.fn(),
  replace: vi.fn(),
}

let consoleErrorSpy

const visitCallback = async (search) => {
  window.history.replaceState({}, '', `/login/callback${search}`)
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
  return wrapper
}

describe('LoginCallback view', () => {
  beforeEach(() => {
    routerMock.push.mockReset()
    routerMock.replace.mockReset()
    exchangeOAuthCode.mockReset()
    sessionStorage.clear()
    localStorage.clear()
    document.body.innerHTML = '<div class="code-background"></div>'
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    document.body.innerHTML = ''
    window.history.replaceState({}, '', '/')
    consoleErrorSpy.mockRestore()
  })

  it('exchanges the one-time code, stores the token and redirects to archive', async () => {
    exchangeOAuthCode.mockResolvedValue({ access_token: 'test-token' })

    await visitCallback('?code=one-time')

    expect(exchangeOAuthCode).toHaveBeenCalledWith('one-time')
    expect(sessionStorage.getItem('auth-token')).toBe('test-token')
    expect(routerMock.replace).toHaveBeenCalledWith('/archive')
  })

  it('shows an error when the code cannot be exchanged', async () => {
    exchangeOAuthCode.mockRejectedValue(new Error('400'))

    const wrapper = await visitCallback('?code=expired')

    expect(sessionStorage.getItem('auth-token')).toBeNull()
    expect(routerMock.replace).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('登入連結已失效')
  })

  it.each([
    ['suspended', '此帳號已被停權'],
    ['conflict', '已被其他帳號使用'],
    ['denied', '已取消 NYCU 授權'],
    ['state', '登入逾時'],
    ['provider', '無法向 NYCU 取得帳號資料'],
    ['unknown', '驗證失敗'],
  ])('shows the message for error=%s', async (error, message) => {
    const wrapper = await visitCallback(`?error=${error}`)

    expect(exchangeOAuthCode).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('登入失敗')
    expect(wrapper.text()).toContain(message)
  })

  it('ignores a token in the URL', async () => {
    const wrapper = await visitCallback('?token=forged')

    expect(exchangeOAuthCode).not.toHaveBeenCalled()
    expect(sessionStorage.getItem('auth-token')).toBeNull()
    expect(wrapper.text()).toContain('驗證失敗')
  })
})
