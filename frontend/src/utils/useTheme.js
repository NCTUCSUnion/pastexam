import { ref, watch } from 'vue'
import { STORAGE_KEYS, getLocalItem, setLocalItem } from './storage'

const initialThemeIsDark = (() => {
  const raw = getLocalItem(STORAGE_KEYS.local.THEME_PREFERENCE)
  return raw ? raw === 'dark' : true
})()
const isDarkTheme = ref(initialThemeIsDark)

export function useTheme() {
  const toggleTheme = () => {
    isDarkTheme.value = !isDarkTheme.value
    setLocalItem(STORAGE_KEYS.local.THEME_PREFERENCE, isDarkTheme.value ? 'dark' : 'light')
  }

  watch(
    isDarkTheme,
    (newValue) => {
      if (newValue) {
        document.documentElement.classList.add('dark')
      } else {
        document.documentElement.classList.remove('dark')
      }
    },
    { immediate: true }
  )

  return {
    isDarkTheme,
    toggleTheme,
  }
}
