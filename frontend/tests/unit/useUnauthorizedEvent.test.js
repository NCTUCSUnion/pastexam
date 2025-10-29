import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { useUnauthorizedEvent } from '@/utils/useUnauthorizedEvent.js'

const TestComponent = {
  template: '<div />',
  props: {
    handler: {
      type: Function,
      required: true,
    },
  },
  setup(props) {
    useUnauthorizedEvent(props.handler)
  },
}

describe('useUnauthorizedEvent composable', () => {
  let addEventListenerSpy
  let removeEventListenerSpy

  beforeEach(() => {
    addEventListenerSpy = vi.spyOn(window, 'addEventListener')
    removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
  })

  afterEach(() => {
    addEventListenerSpy.mockRestore()
    removeEventListenerSpy.mockRestore()
  })

  it('registers and cleans up unauthorized event listener', () => {
    const handler = vi.fn()

    const wrapper = mount(TestComponent, {
      props: { handler },
    })

    expect(addEventListenerSpy).toHaveBeenCalledWith('app:unauthorized', handler)

    wrapper.unmount()

    expect(removeEventListenerSpy).toHaveBeenCalledWith('app:unauthorized', handler)
  })
})
