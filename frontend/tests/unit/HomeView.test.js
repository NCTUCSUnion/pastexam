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
    memeServiceMock.getRandomMeme.mockReset()
    memeServiceMock.getRandomMeme.mockResolvedValue({ data: memeResponse })
    statisticsServiceMock.getSystemStatistics.mockReset()
    statisticsServiceMock.getSystemStatistics.mockResolvedValue({
      data: { data: statisticsPayload },
    })
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

  it('falls back to default meme when API returns invalid payload', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    memeServiceMock.getRandomMeme.mockResolvedValueOnce({ data: { content: null } })

    const wrapper = mount(HomeView)
    await flushPromises()
    vi.runAllTimers()
    await flushPromises()

    expect(wrapper.vm.selectedMeme.code).toContain('API connection failed')
    expect(consoleErrorSpy).toHaveBeenCalledWith('Invalid API response format:', { content: null })

    consoleErrorSpy.mockRestore()
  })

  it('handles meme fetch failures gracefully', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    memeServiceMock.getRandomMeme.mockRejectedValueOnce(new Error('network'))

    const wrapper = mount(HomeView)
    await flushPromises()
    vi.runAllTimers()
    await flushPromises()

    expect(wrapper.vm.selectedMeme.code).toContain('API connection failed')
    expect(wrapper.vm.selectedMeme.language).toBe('javascript')
    expect(consoleErrorSpy).toHaveBeenLastCalledWith('Error fetching meme:', expect.any(Error))

    consoleErrorSpy.mockRestore()
  })

  it('uses NaN placeholders when statistics fetching fails', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    statisticsServiceMock.getSystemStatistics.mockRejectedValueOnce(new Error('stats'))

    const wrapper = mount(HomeView)
    await flushPromises()
    vi.runAllTimers()
    await flushPromises()

    expect(wrapper.vm.animatedValues.totalUsers).toBe('NaN')
    expect(wrapper.vm.statisticsData.totalDownloads).toBeNaN()
    expect(wrapper.vm.statsLoaded).toBe(true)
    expect(consoleErrorSpy).toHaveBeenLastCalledWith(
      'Error fetching statistics:',
      expect.any(Error)
    )

    consoleErrorSpy.mockRestore()
  })
})
