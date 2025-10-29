import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import NotificationCenterModal from '@/components/NotificationCenterModal.vue'

const notifications = [
  {
    id: 1,
    title: '公告一',
    body: '內容一',
    severity: 'info',
    created_at: '2025-01-01T00:00:00Z',
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
})
