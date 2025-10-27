import { reactive, ref, computed } from 'vue'
import { notificationService } from '../api'
import { isUnauthorizedError } from './http'

const STORAGE_KEY = 'pastexam_notification_last_seen'

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

const lastSeenId = ref(loadLastSeenId())

const latestUnseenNotification = computed(() => {
  if (!state.active.length) {
    return null
  }

  const unseen = state.active.filter((notification) => notification.id > (lastSeenId.value || 0))
  if (!unseen.length) {
    return null
  }

  return unseen.reduce((latest, candidate) => {
    if (!latest) return candidate
    return candidate.id > latest.id ? candidate : latest
  }, unseen[0])
})

function loadLastSeenId() {
  if (typeof window === 'undefined') return 0
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return 0
    const parsed = parseInt(raw, 10)
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 0
  } catch (error) {
    console.warn('Failed to read notification last seen id:', error)
    return 0
  }
}

function persistLastSeenId(id) {
  lastSeenId.value = id
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, String(id))
  } catch (error) {
    console.error('Failed to persist notification last seen id:', error)
  }
}

function markNotificationAsSeen(notification) {
  if (!notification?.id) return
  const id = notification.id
  if (id > (lastSeenId.value || 0)) {
    persistLastSeenId(id)
  }
  state.modalVisible = false
}

async function refreshActive() {
  state.loadingActive = true
  errors.active = null
  try {
    const { data } = await notificationService.getActive()
    state.active = Array.isArray(data) ? data : []
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
    state.all = Array.isArray(data) ? data : []
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
    lastSeenId,
  }
}
