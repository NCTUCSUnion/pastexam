import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const sockets = vi.hoisted(() => [])

vi.mock('@/api', () => ({
  discussionService: {
    openArchiveDiscussionWebSocket: vi.fn(() => {
      const ws = {
        readyState: 1,
        send: vi.fn(),
        close: vi.fn(),
      }
      sockets.push(ws)
      return ws
    }),
    deleteArchiveMessage: vi.fn(),
  },
  userService: {
    getMe: vi.fn(() => Promise.resolve({ data: { id: 1, nickname: '', name: 'me' } })),
    updateMyNickname: vi.fn(),
  },
}))

vi.mock('@/utils/auth', () => ({
  getCurrentUser: () => ({ id: 1, is_admin: false }),
}))

vi.mock('@/utils/analytics', () => ({
  trackEvent: vi.fn(),
  EVENTS: { DISCUSSION_SEND_MESSAGE: 'discussion-send-message' },
}))

import ArchiveDiscussionPanel from '@/components/ArchiveDiscussionPanel.vue'

const ButtonStub = {
  props: ['label'],
  emits: ['click'],
  template: '<button @click="$emit(\'click\')">{{ label }}<slot /></button>',
}

const TextareaStub = {
  props: ['modelValue'],
  emits: ['update:modelValue'],
  template:
    '<textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
}

const mountPanel = () =>
  mount(ArchiveDiscussionPanel, {
    props: { courseId: 1, archiveId: 2, enabled: true },
    global: {
      provide: { toast: { add: vi.fn() } },
      stubs: {
        Button: ButtonStub,
        Textarea: TextareaStub,
        Dialog: true,
        ProgressSpinner: true,
        InputText: true,
        Checkbox: true,
      },
    },
  })

const lastSocket = () => sockets[sockets.length - 1]

const receive = async (ws, data) => {
  await ws.onmessage({ data: JSON.stringify(data) })
  await flushPromises()
}

const message = (id, userId = 2, content = `msg ${id}`) => ({
  id,
  archive_id: 2,
  user_id: userId,
  user_name: `user ${userId}`,
  content,
  created_at: '2026-11-13T00:00:00Z',
})

describe('ArchiveDiscussionPanel', () => {
  beforeEach(() => {
    sockets.length = 0
    vi.useRealTimers()
  })

  it('shows a reconnect prompt instead of the empty state when history never arrives', async () => {
    const wrapper = mountPanel()
    await flushPromises()
    const ws = lastSocket()

    ws.onclose({ code: 4401 })
    await flushPromises()

    expect(wrapper.text()).toContain('無法連線到討論區')
    expect(wrapper.text()).not.toContain('還沒有人發起討論')

    await wrapper
      .findAll('button')
      .find((b) => b.text().includes('重新連線'))
      .trigger('click')
    expect(sockets.length).toBe(2)
  })

  it('shows the empty state once history is loaded', async () => {
    const wrapper = mountPanel()
    await flushPromises()

    await receive(lastSocket(), { type: 'history', messages: [] })

    expect(wrapper.text()).toContain('還沒有人發起討論')
  })

  it('restores the draft when the server rejects the message', async () => {
    const wrapper = mountPanel()
    await flushPromises()
    const ws = lastSocket()
    ws.onopen()
    await receive(ws, { type: 'history', messages: [] })

    const textarea = wrapper.find('textarea')
    await textarea.setValue('my long answer')
    await wrapper
      .findAll('button')
      .find((b) => b.text().includes('送出'))
      .trigger('click')
    expect(ws.send).toHaveBeenCalledTimes(1)
    expect(textarea.element.value).toBe('')

    await receive(ws, { type: 'error', code: 'rate_limited', detail: 'too fast' })

    expect(textarea.element.value).toBe('my long answer')
  })

  it('ignores duplicate messages and keeps them ordered by id', async () => {
    const wrapper = mountPanel()
    await flushPromises()
    const ws = lastSocket()
    await receive(ws, { type: 'history', messages: [message(1), message(3)] })

    await receive(ws, { type: 'message', message: message(3) })
    await receive(ws, { type: 'message', message: message(2) })

    const texts = wrapper.text()
    expect(texts.match(/msg 3/g)).toHaveLength(1)
    expect(texts.indexOf('msg 1')).toBeLessThan(texts.indexOf('msg 2'))
    expect(texts.indexOf('msg 2')).toBeLessThan(texts.indexOf('msg 3'))
  })
})
