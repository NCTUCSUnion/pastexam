import { describe, it, expect, beforeEach, vi } from 'vitest'
import { nextTick } from 'vue'

const THEME_KEY = 'theme-preference'

async function loadUseTheme() {
  const module = await import('@/utils/useTheme.js')
  return module.useTheme()
}

describe('useTheme composable', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('reads initial preference from localStorage', async () => {
    localStorage.setItem(THEME_KEY, 'light')

    const { isDarkTheme } = await loadUseTheme()

    await nextTick()

    expect(isDarkTheme.value).toBe(false)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('toggles theme and persists preference', async () => {
    localStorage.setItem(THEME_KEY, 'light')

    const { isDarkTheme, toggleTheme } = await loadUseTheme()

    toggleTheme()
    await nextTick()

    expect(isDarkTheme.value).toBe(true)
    expect(localStorage.getItem(THEME_KEY)).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})
