import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import NotificationCenterModal from '@/components/NotificationCenterModal.vue'

vi.mock('@/utils/markdown', () => ({
  renderMarkdown: vi.fn((text) => `<p>${text}</p>`),
}))

const notifications = [
  {
    id: 1,
    title: '公告一',
    body: '內容一',
    severity: 'info',
    created_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 2,
    title: 'Markdown 公告',
    body: '這是 **粗體** 和 [連結](https://example.com)',
    severity: 'danger',
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-03T00:00:00Z',
  },
]

const stubComponent = { template: '<div><slot /></div>' }

describe('NotificationCenterModal', () => {
  it('handles detail modal and formatting helpers', async () => {
    const wrapper = mount(NotificationCenterModal, {
      props: {
        visible: true,
        notifications,
        loading: false,
      },
      global: {
        stubs: {
          Dialog: stubComponent,
          DataTable: stubComponent,
          Column: { template: '<template />' },
          Tag: stubComponent,
          Button: stubComponent,
          ProgressSpinner: stubComponent,
        },
      },
    })

    const vm = wrapper.vm

    expect(vm.resolveSeverity('danger')).toBe('danger')
    expect(vm.resolveSeverityLabel('danger')).toBe('重要')
    expect(vm.formatDate('2024-01-01')).toContain('01')
    expect(vm.formatTimestamp('2024-01-01T00:00:00Z')).toContain('00')

    vm.openDetail(notifications[0])
    expect(vm.detailVisible).toBe(true)
    expect(wrapper.emitted('mark-seen')).toBeTruthy()

    await wrapper.setProps({ visible: false })
    expect(vm.detailVisible).toBe(false)
    expect(vm.selectedNotification).toBeNull()

    vm.handleDetailVisibility(true)
    expect(vm.detailVisible).toBe(true)
    vm.handleDetailVisibility(false)
    expect(vm.detailVisible).toBe(false)

    vm.handleVisibility(false)
    expect(wrapper.emitted('update:visible')).toBeTruthy()

    wrapper.unmount()
  })

  it('renders markdown content in notification body', async () => {
    const { renderMarkdown } = await import('@/utils/markdown')

    const wrapper = mount(NotificationCenterModal, {
      props: {
        visible: true,
        notifications,
        loading: false,
      },
      global: {
        stubs: {
          Dialog: stubComponent,
          DataTable: stubComponent,
          Column: { template: '<template />' },
          Tag: stubComponent,
          Button: stubComponent,
          ProgressSpinner: stubComponent,
        },
      },
    })

    const vm = wrapper.vm

    // Open detail with markdown content
    vm.openDetail(notifications[1])
    await wrapper.vm.$nextTick()

    expect(vm.selectedNotification).toEqual(notifications[1])
    expect(vm.renderedBody).toBeTruthy()
    expect(renderMarkdown).toHaveBeenCalledWith(notifications[1].body)

    // Test with empty body
    const emptyNotification = { ...notifications[0], body: '' }
    vm.openDetail(emptyNotification)
    await wrapper.vm.$nextTick()

    expect(renderMarkdown).toHaveBeenCalledWith('')

    wrapper.unmount()
  })

  it('renders list markdown correctly', async () => {
    vi.resetModules()
    vi.doUnmock('@/utils/markdown')
    const { renderMarkdown } = await import('@/utils/markdown')

    const listNotification = {
      id: 3,
      title: '列表測試',
      body: '- 項目一\n- 項目二\n- 項目三',
      severity: 'info',
      created_at: '2025-01-01T00:00:00Z',
    }

    const wrapper = mount(NotificationCenterModal, {
      props: {
        visible: true,
        notifications: [listNotification],
        loading: false,
      },
      global: {
        stubs: {
          Dialog: stubComponent,
          DataTable: stubComponent,
          Column: { template: '<template />' },
          Tag: stubComponent,
          Button: stubComponent,
          ProgressSpinner: stubComponent,
        },
      },
    })

    const vm = wrapper.vm
    vm.openDetail(listNotification)
    await wrapper.vm.$nextTick()

    const rendered = renderMarkdown(listNotification.body)
    expect(rendered).toContain('<ul>')
    expect(rendered).toContain('<li>')

    wrapper.unmount()
  })
})
