export const STORAGE_KEYS = {
  local: {
    THEME_PREFERENCE: 'theme-preference',
    NOTIFICATION_LAST_SEEN: 'notification-last-seen',
    SELECTED_SUBJECT: 'selected-subject',
    ADMIN_CURRENT_TAB: 'admin-current-tab',
    AI_EXAM_CURRENT_TASK: 'ai-exam-current-task',
    AUTH_TOKEN: 'auth-token',
    DISCUSSION_DESKTOP_DEFAULT_OPEN: 'discussion-desktop-default-open',
  },
  session: {
    AUTH_TOKEN: 'auth-token',
    ISSUE_CONTEXT: 'pastexam-issue-context',
  },
}

const LEGACY_KEYS = {
  local: {
    [STORAGE_KEYS.local.NOTIFICATION_LAST_SEEN]: ['notification_last_seen'],
    [STORAGE_KEYS.local.SELECTED_SUBJECT]: ['selectedSubject'],
    [STORAGE_KEYS.local.ADMIN_CURRENT_TAB]: ['adminCurrentTab'],
    [STORAGE_KEYS.local.AI_EXAM_CURRENT_TASK]: ['aiExamCurrentTask'],
    [STORAGE_KEYS.local.AUTH_TOKEN]: ['authToken'],
  },
  session: {
    [STORAGE_KEYS.session.AUTH_TOKEN]: ['authToken'],
    [STORAGE_KEYS.session.ISSUE_CONTEXT]: ['pastexam:issueContext'],
  },
}

function getStore(type) {
  if (typeof window === 'undefined') return null
  return type === 'session' ? window.sessionStorage : window.localStorage
}

function migrateStorageKey(type, key) {
  const store = getStore(type)
  if (!store) return

  const legacyKeys = LEGACY_KEYS?.[type]?.[key] || []
  if (!legacyKeys.length) return

  try {
    if (store.getItem(key) !== null) return
  } catch {
    return
  }

  for (const legacyKey of legacyKeys) {
    try {
      const legacyValue = store.getItem(legacyKey)
      if (legacyValue === null) continue
      store.setItem(key, legacyValue)
      for (const k of legacyKeys) {
        try {
          store.removeItem(k)
        } catch {
          // ignore
        }
      }
      return
    } catch {
      // ignore
    }
  }
}

function cleanupLegacyKeys(type, key) {
  const store = getStore(type)
  if (!store) return

  const legacyKeys = LEGACY_KEYS?.[type]?.[key] || []
  if (!legacyKeys.length) return

  for (const legacyKey of legacyKeys) {
    try {
      if (store.getItem(legacyKey) !== null) {
        store.removeItem(legacyKey)
      }
    } catch {
      // ignore
    }
  }
}

export function getStorageItem(type, key) {
  migrateStorageKey(type, key)
  const store = getStore(type)
  if (!store) return null
  return store.getItem(key)
}

export function setStorageItem(type, key, value) {
  const store = getStore(type)
  if (!store) return
  store.setItem(key, value)
  cleanupLegacyKeys(type, key)
}

export function removeStorageItem(type, key) {
  const store = getStore(type)
  if (!store) return
  store.removeItem(key)
}

export function getStorageJson(type, key) {
  const raw = getStorageItem(type, key)
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function setStorageJson(type, key, value) {
  setStorageItem(type, key, JSON.stringify(value))
}

export function getLocalItem(key) {
  return getStorageItem('local', key)
}

export function setLocalItem(key, value) {
  setStorageItem('local', key, value)
}

export function removeLocalItem(key) {
  removeStorageItem('local', key)
}

export function getLocalJson(key) {
  return getStorageJson('local', key)
}

export function setLocalJson(key, value) {
  setStorageJson('local', key, value)
}

export function getSessionItem(key) {
  return getStorageItem('session', key)
}

export function setSessionItem(key, value) {
  setStorageItem('session', key, value)
}

export function removeSessionItem(key) {
  removeStorageItem('session', key)
}

export function getSessionJson(key) {
  return getStorageJson('session', key)
}

export function setSessionJson(key, value) {
  setStorageJson('session', key, value)
}
