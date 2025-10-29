import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import NotificationModal from '@/components/NotificationModal.vue'

const notification = {
  id: 12,
  title: '系統維護',
  body: '維護通知',
  severity: 'danger',
  created_at: '2025-01-01T00:00:00Z',
}

const stubComponent = { template: '<div><slot /></div>' }

describe('NotificationModal', () => {
  it('handles severity, dismiss, and timestamp formatting', () => {
    const wrapper = mount(NotificationModal, {
      props: {
        visible: true,
        notification,
      },
      global: {
        stubs: {
          Dialog: stubComponent,
          Button: stubComponent,
          Tag: stubComponent,
        },
      },
    })

    const vm = wrapper.vm

    expect(vm.resolveSeverity('danger')).toBe('danger')
    expect(vm.resolveSeverity('info')).toBe('info')
    expect(vm.resolveSeverityLabel('danger')).toBe('重要')
    expect(vm.resolveSeverityLabel('info')).toBe('一般')

    const formatted = vm.formatTimestamp(notification.created_at)
    expect(formatted).toContain('01')

    vm.handleDismiss()
    expect(wrapper.emitted('dismiss')).toBeTruthy()
    expect(wrapper.emitted('update:visible')).toBeTruthy()

    vm.openCenter()
    expect(wrapper.emitted('open-center')).toBeTruthy()

    vm.handleVisibility(false)
    expect(wrapper.emitted('update:visible').pop()).toEqual([false])

    wrapper.unmount()
  })
})
