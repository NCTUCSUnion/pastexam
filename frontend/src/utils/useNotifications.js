import { reactive, ref, computed } from 'vue'
import { notificationService } from '../api'
import { isUnauthorizedError } from './http'
import { STORAGE_KEYS, getLocalItem, getLocalJson, setLocalJson } from './storage'

const state = reactive({
  active: [],
  all: [],
  modalVisible: false,
  centerVisible: false,
  detailNotification: null,
  initialized: false,
  loadingActive: false,
  loadingAll: false,
})

const errors = reactive({
  active: null,
  all: null,
})

// Read state is kept per notification: { [id]: effective time when it was seen }.
// A single "last seen" time hid scheduled notices whose updated_at predates it,
// and dismissing one of two unread notices marked both as read.
const seenNotifications = ref(loadSeenNotifications())
// Read state from older versions, which only stored one timestamp
const legacyLastSeen = loadLegacyLastSeen()

// When a notice becomes visible to users: edited later, or scheduled to start later
function effectiveTime(notification) {
  const updated = new Date(notification.updated_at || notification.created_at).getTime() || 0
  const starts = notification.starts_at ? new Date(notification.starts_at).getTime() || 0 : 0
  return Math.max(updated, starts)
}

function isSeen(notification) {
  const time = effectiveTime(notification)
  return (seenNotifications.value[notification.id] ?? 0) >= time || legacyLastSeen >= time
}

const latestUnseenNotification = computed(() => {
  const unseen = state.active.filter((notification) => !isSeen(notification))
  if (!unseen.length) {
    return null
  }
  return unseen.reduce((latest, candidate) =>
    effectiveTime(candidate) > effectiveTime(latest) ? candidate : latest
  )
})

function loadSeenNotifications() {
  try {
    const stored = getLocalJson(STORAGE_KEYS.local.NOTIFICATION_SEEN)
    return stored && typeof stored === 'object' && !Array.isArray(stored) ? stored : {}
  } catch (error) {
    console.warn('Failed to read seen notifications:', error)
    return {}
  }
}

function loadLegacyLastSeen() {
  try {
    const raw = getLocalItem(STORAGE_KEYS.local.NOTIFICATION_LAST_SEEN)
    if (!raw) return 0
    const parsed = parseInt(raw, 10)
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 0
  } catch (error) {
    console.warn('Failed to read notification last seen timestamp:', error)
    return 0
  }
}

function persistSeenNotifications(seen) {
  seenNotifications.value = seen
  try {
    setLocalJson(STORAGE_KEYS.local.NOTIFICATION_SEEN, seen)
  } catch (error) {
    console.error('Failed to persist seen notifications:', error)
  }
}

function markNotificationAsSeen(notification) {
  if (!notification) return
  persistSeenNotifications({
    ...seenNotifications.value,
    [notification.id]: effectiveTime(notification),
  })
  // Show the next unread notice, if any
  state.modalVisible = !!latestUnseenNotification.value
}

async function refreshActive() {
  state.loadingActive = true
  errors.active = null
  try {
    const { data } = await notificationService.getActive()
    state.active = Array.isArray(data)
      ? [...data].sort((a, b) => {
          const aTime = new Date(a.updated_at || a.created_at).getTime()
          const bTime = new Date(b.updated_at || b.created_at).getTime()
          return bTime - aTime
        })
      : []
    // Forget notices that are no longer active so the map does not grow forever
    const activeIds = new Set(state.active.map((notification) => String(notification.id)))
    const kept = Object.fromEntries(
      Object.entries(seenNotifications.value).filter(([id]) => activeIds.has(id))
    )
    if (Object.keys(kept).length !== Object.keys(seenNotifications.value).length) {
      persistSeenNotifications(kept)
    }
    const latest = latestUnseenNotification.value
    state.modalVisible = !!latest
  } catch (error) {
    errors.active = error
    if (!isUnauthorizedError(error)) {
      console.error('Failed to load active notifications:', error)
    }
  } finally {
    state.loadingActive = false
  }
}

async function refreshAll() {
  if (state.loadingAll) return
  state.loadingAll = true
  errors.all = null
  try {
    const { data } = await notificationService.getAll()
    state.all = Array.isArray(data)
      ? [...data].sort((a, b) => {
          const aTime = new Date(a.updated_at || a.created_at).getTime()
          const bTime = new Date(b.updated_at || b.created_at).getTime()
          return bTime - aTime
        })
      : []
  } catch (error) {
    errors.all = error
    if (!isUnauthorizedError(error)) {
      console.error('Failed to load notifications:', error)
    }
  } finally {
    state.loadingAll = false
  }
}

async function initNotifications() {
  if (state.initialized) return
  await refreshActive()
  // Try again next time if loading failed
  state.initialized = !errors.active
}

function openModal() {
  if (!latestUnseenNotification.value) {
    return
  }
  state.modalVisible = true
}

function closeModal() {
  state.modalVisible = false
}

async function openCenter() {
  await refreshAll()
  if (errors.all && isUnauthorizedError(errors.all)) {
    return
  }
  state.centerVisible = true
}

function closeCenter() {
  state.centerVisible = false
}

export function useNotifications() {
  return {
    state,
    errors,
    latestUnseenNotification,
    initNotifications,
    refreshActive,
    refreshAll,
    openModal,
    closeModal,
    openCenter,
    closeCenter,
    markNotificationAsSeen,
    seenNotifications,
  }
}
