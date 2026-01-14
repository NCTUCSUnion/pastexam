import { ref } from 'vue'

function canUseStorage() {
  return typeof window !== 'undefined' && typeof localStorage !== 'undefined'
}

export function getBooleanPreference(key, defaultValue = false) {
  if (!canUseStorage()) return defaultValue
  try {
    const raw = localStorage.getItem(key)
    if (raw === null) return defaultValue
    if (raw === '1' || raw === 'true') return true
    if (raw === '0' || raw === 'false') return false
    return defaultValue
  } catch {
    return defaultValue
  }
}

export function setBooleanPreference(key, value) {
  if (!canUseStorage()) return
  try {
    localStorage.setItem(key, value ? '1' : '0')
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
