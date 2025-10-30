import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import NotificationModal from '@/components/NotificationModal.vue'

vi.mock('@/utils/markdown', () => ({
  renderMarkdown: vi.fn((text) => `<p>${text}</p>`),
}))

const notification = {
  id: 12,
  title: '系統維護',
  body: '維護通知',
  severity: 'danger',
  created_at: '2025-01-01T00:00:00Z',
}

const markdownNotification = {
  id: 13,
  title: 'Markdown 測試',
  body: '這是 **粗體** 和 [連結](https://example.com)',
  severity: 'info',
  created_at: '2025-01-02T00:00:00Z',
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

  it('renders markdown content in notification body', async () => {
    const { renderMarkdown } = await import('@/utils/markdown')

    const wrapper = mount(NotificationModal, {
      props: {
        visible: true,
        notification: markdownNotification,
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

    expect(vm.renderedBody).toBeTruthy()
    expect(renderMarkdown).toHaveBeenCalledWith(markdownNotification.body)

    // Test computed property with null notification
    await wrapper.setProps({ notification: null })
    expect(vm.renderedBody).toBe('')

    // Test with empty body
    await wrapper.setProps({
      notification: { ...notification, body: '' },
    })
    expect(renderMarkdown).toHaveBeenCalledWith('')

    wrapper.unmount()
  })

  it('renders list markdown correctly', async () => {
    vi.resetModules()
    vi.doUnmock('@/utils/markdown')
    const { renderMarkdown } = await import('@/utils/markdown')

    const listNotification = {
      id: 14,
      title: '列表測試',
      body: '1. 第一項\n2. 第二項\n3. 第三項',
      severity: 'info',
      created_at: '2025-01-01T00:00:00Z',
    }

    const wrapper = mount(NotificationModal, {
      props: {
        visible: true,
        notification: listNotification,
      },
      global: {
        stubs: {
          Dialog: stubComponent,
          Button: stubComponent,
          Tag: stubComponent,
        },
      },
    })

    const rendered = renderMarkdown(listNotification.body)
    expect(rendered).toContain('<ol>')
    expect(rendered).toContain('<li>')

    wrapper.unmount()
  })
})
