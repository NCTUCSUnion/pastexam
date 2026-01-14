import { reactive, ref, computed } from 'vue'
import { notificationService } from '../api'
import { isUnauthorizedError } from './http'
import { STORAGE_KEYS, getLocalItem, setLocalItem } from './storage'

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

const lastSeenTimestamp = ref(loadLastSeenTimestamp())

const latestUnseenNotification = computed(() => {
  if (!state.active.length) {
    return null
  }

  const unseen = state.active.filter((notification) => {
    const notificationTime = new Date(notification.updated_at || notification.created_at).getTime()
    return notificationTime > (lastSeenTimestamp.value || 0)
  })

  if (!unseen.length) {
    return null
  }

  return unseen.reduce((latest, candidate) => {
    if (!latest) return candidate
    const latestTime = new Date(latest.updated_at || latest.created_at).getTime()
    const candidateTime = new Date(candidate.updated_at || candidate.created_at).getTime()
    return candidateTime > latestTime ? candidate : latest
  }, unseen[0])
})

function loadLastSeenTimestamp() {
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

function persistLastSeenTimestamp(timestamp) {
  lastSeenTimestamp.value = timestamp
  try {
    setLocalItem(STORAGE_KEYS.local.NOTIFICATION_LAST_SEEN, String(timestamp))
  } catch (error) {
    console.error('Failed to persist notification last seen timestamp:', error)
  }
}

function markNotificationAsSeen(notification) {
  if (!notification) return
  const notificationTime = new Date(notification.updated_at || notification.created_at).getTime()
  if (notificationTime > (lastSeenTimestamp.value || 0)) {
    persistLastSeenTimestamp(notificationTime)
  }
  state.modalVisible = false
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
  state.initialized = true
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
    lastSeenTimestamp,
  }
}
