import { ref } from 'vue'
import { getLocalItem, setLocalItem } from './storage'

export function getBooleanPreference(key, defaultValue = false) {
  try {
    const raw = getLocalItem(key)
    if (raw === null) return defaultValue
    if (raw === '1' || raw === 'true') return true
    if (raw === '0' || raw === 'false') return false
    return defaultValue
  } catch {
    return defaultValue
  }
}

export function setBooleanPreference(key, value) {
  try {
    setLocalItem(key, value ? '1' : '0')
  } catch {
    // ignore
  }
}

export function useBooleanPreference(key, defaultValue = false) {
  const preference = ref(getBooleanPreference(key, defaultValue))
  const setPreference = (value) => {
    const next = Boolean(value)
    preference.value = next
    setBooleanPreference(key, next)
  }
  return { preference, setPreference }
}
