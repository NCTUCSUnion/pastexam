import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import NotFound from '@/views/NotFound.vue'

const routerMock = {
  push: vi.fn(),
}

const { getCodeBgSvgMock } = vi.hoisted(() => ({
  getCodeBgSvgMock: vi.fn(() => 'mocked-bg'),
}))

vi.mock('@/utils/svgBg', () => ({
  getCodeBgSvg: getCodeBgSvgMock,
}))

vi.mock('@/utils/useTheme', () => ({
  useTheme: () => ({ isDarkTheme: ref(false) }),
}))

const componentStubs = {
  Card: { template: '<div><slot name="title"></slot><slot name="content"></slot></div>' },
  Button: {
    template: '<button type="button" @click="$emit(\'click\', $event)"><slot /></button>',
  },
}

function mountView() {
  return mount(NotFound, {
    attachTo: document.body,
    global: {
      mocks: { $router: routerMock },
      stubs: componentStubs,
    },
  })
}

describe('NotFound view', () => {
  beforeEach(() => {
    routerMock.push.mockReset()
    getCodeBgSvgMock.mockClear()
    document.body.innerHTML = ''
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('renders 404 heading and helpful message', () => {
    const wrapper = mountView()
    expect(wrapper.text()).toContain('404')
    expect(wrapper.text()).toContain('頁面不存在')
    expect(wrapper.text()).toContain('抱歉，我們找不到您要找的頁面。')
    wrapper.unmount()
  })

  it('routes back home when the button is clicked', async () => {
    const wrapper = mountView()
    await wrapper.find('button').trigger('click')
    expect(routerMock.push).toHaveBeenCalledWith('/')
    wrapper.unmount()
  })

  it('applies the code background style on mount', () => {
    const backgroundElement = {
      style: {
        setProperty: vi.fn(),
      },
    }
    const querySpy = vi.spyOn(document, 'querySelector').mockReturnValue(backgroundElement)
    const wrapper = mountView()
    expect(getCodeBgSvgMock).toHaveBeenCalled()
    expect(backgroundElement.style.setProperty).toHaveBeenCalledWith(
      'background-image',
      'mocked-bg'
    )
    querySpy.mockRestore()
    wrapper.unmount()
  })
})
