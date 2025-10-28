import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import HomeView from '@/views/Home.vue'

const memeResponse = vi.hoisted(() => ({
  content: "console.log('Hello Vitest!')",
  language: 'javascript',
}))

const statisticsPayload = vi.hoisted(() => ({
  totalUsers: 120,
  totalDownloads: 45,
  onlineUsers: 7,
  totalArchives: 15,
  totalCourses: 8,
  activeToday: 3,
}))

const memeServiceMock = vi.hoisted(() => ({
  getRandomMeme: vi.fn(() => Promise.resolve({ data: memeResponse })),
}))

const statisticsServiceMock = vi.hoisted(() => ({
  getSystemStatistics: vi.fn(() => Promise.resolve({ data: { data: statisticsPayload } })),
}))

vi.mock('@/api', () => ({
  memeService: memeServiceMock,
  statisticsService: statisticsServiceMock,
}))

vi.mock('highlight.js', () => ({
  default: {
    highlight: vi.fn(() => ({ value: memeResponse.content })),
  },
}))

describe('HomeView', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.useRealTimers()
  })

  it('renders fetched meme text and statistics', async () => {
    const wrapper = mount(HomeView)

    await flushPromises()
    vi.runAllTimers()
    await flushPromises()

    const languageBadge = wrapper.get('.language-badge')
    expect(languageBadge.text()).toBe(memeResponse.language)

    const codeBlock = wrapper.get('code')
    expect(codeBlock.html()).toContain('console.log')

    const statCards = wrapper.findAll('.stat-card')
    expect(statCards.length).toBe(6)
    expect(statCards[0].text()).toContain('總用戶數')
    expect(statCards[0].text()).toContain(String(statisticsPayload.totalUsers))
  })
})
