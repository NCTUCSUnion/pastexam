<template>
  <Dialog
    :visible="localVisible"
    @update:visible="localVisible = $event"
    :style="{ width: 'min(1200px, 95vw)', height: 'min(90vh, 90dvh)' }"
    :contentStyle="{ flex: '1 1 auto' }"
    :modal="true"
    :draggable="false"
    :closeOnEscape="false"
    :dismissableMask="true"
    :maximizable="true"
    :autoFocus="false"
    @maximize="handleMaximize"
    @unmaximize="handleUnmaximize"
    @hide="onHide"
  >
    <template #maximizebutton="{ maximized, maximizeCallback }">
      <Button
        v-if="discussionEnabled"
        :icon="discussionOpen ? 'pi pi-comments' : 'pi pi-comment'"
        severity="secondary"
        text
        rounded
        :aria-label="isMobile ? '開啟討論區' : discussionOpen ? '關閉討論區' : '開啟討論區'"
        style="width: 2.5rem; height: 2.5rem; padding: 0"
        @click="handleDiscussionClick"
      />
      <Button
        :icon="maximized ? 'pi pi-window-minimize' : 'pi pi-window-maximize'"
        severity="secondary"
        text
        rounded
        :aria-label="maximized ? '還原' : '最大化'"
        style="width: 2.5rem; height: 2.5rem; padding: 0"
        @click="maximizeCallback"
      />
    </template>
    <template #header>
      <div class="flex align-items-center gap-2.5">
        <i class="pi pi-file-pdf text-2xl" />
        <div class="flex flex-column">
          <div class="text-xl leading-tight">
            {{ title }}
          </div>
          <div
            v-if="metaTextItems.length && !isMobile"
            class="text-sm mt-1 flex flex-wrap gap-3"
            style="color: var(--text-secondary)"
          >
            <span v-for="item in metaTextItems" :key="item.key" class="flex align-items-center">
              <i :class="`pi ${item.icon} mr-1`"></i>
              {{ item.value }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <div class="w-full h-full flex flex-column">
      <div class="flex-1 flex min-h-0">
        <div class="flex-1 flex flex-column min-w-0">
          <div
            v-if="error || pdfError"
            class="flex-1 flex flex-column align-items-center justify-content-center gap-4"
          >
            <i class="pi pi-exclamation-circle text-6xl text-red-500" />
            <div class="text-xl">無法載入預覽</div>
            <div class="text-sm text-gray-600">請嘗試下載檔案查看</div>
          </div>

          <div
            v-else-if="loading || pdfLoading"
            class="flex-1 flex align-items-center justify-content-center"
          >
            <ProgressSpinner strokeWidth="4" />
          </div>

          <div v-else-if="pdf && renderPdf" class="flex-1 pdf-container" ref="pdfContainerRef">
            <div class="pdf-pages">
              <VuePDF
                v-for="page in pages"
                :key="`${page}-${resizeKey}`"
                :pdf="pdf"
                :page="page"
                :fitParent="true"
                class="pdf-page"
                @loaded="handlePdfLoaded"
              />
            </div>
          </div>

          <div v-else class="flex-1 flex align-items-center justify-content-center">
            <ProgressSpinner strokeWidth="4" />
          </div>
        </div>

        <div
          v-if="discussionEnabled && !isMobile"
          class="discussion-wrapper"
          :class="{ 'is-open': discussionOpen, 'is-closed': !discussionOpen }"
        >
          <ArchiveDiscussionPanel
            :courseId="courseId"
            :archiveId="archiveId"
            width="100%"
            @desktop-default-open-change="handleDesktopDefaultOpenChange"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <Button
        v-if="showDownload"
        label="下載"
        icon="pi pi-download"
        @click="handleDownload"
        severity="success"
        :loading="downloading"
      />
    </template>
  </Dialog>

  <Dialog
    v-if="discussionEnabled"
    :visible="discussionModalVisible"
    @update:visible="discussionModalVisible = $event"
    :modal="true"
    :draggable="false"
    :dismissableMask="true"
    :closeOnEscape="true"
    :style="{ width: 'min(520px, 95vw)', height: 'min(90vh, 90dvh)' }"
    :contentStyle="{ flex: '1 1 auto' }"
    :autoFocus="false"
  >
    <template #header>
      <div class="flex align-items-center gap-2.5">
        <i class="pi pi-comments text-2xl" />
        <div class="text-xl leading-tight">討論區</div>
      </div>
    </template>
    <template #closebutton="{ closeCallback }">
      <Button
        icon="pi pi-cog"
        severity="secondary"
        text
        rounded
        aria-label="暱稱設定"
        style="width: 2.5rem; height: 2.5rem; padding: 0"
        @click="openDiscussionSettings"
      />
      <Button
        icon="pi pi-times"
        severity="secondary"
        text
        rounded
        aria-label="關閉"
        style="width: 2.5rem; height: 2.5rem; padding: 0"
        @click="closeCallback"
      />
    </template>
    <div class="h-full min-h-0">
      <ArchiveDiscussionPanel
        ref="discussionPanelRef"
        :courseId="courseId"
        :archiveId="archiveId"
        width="100%"
        class="discussion-modal-panel"
        :showHeader="false"
        :showSettings="false"
        @desktop-default-open-change="handleDesktopDefaultOpenChange"
      />
    </div>
  </Dialog>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { VuePDF, usePDF } from '@tato30/vue-pdf'
import '@tato30/vue-pdf/style.css'
import { useUnauthorizedEvent } from '../utils/useUnauthorizedEvent'
import ArchiveDiscussionPanel from './ArchiveDiscussionPanel.vue'
import { getBooleanPreference } from '../utils/usePreferences'
import { STORAGE_KEYS } from '../utils/storage'

const DESKTOP_DEFAULT_OPEN_KEY = STORAGE_KEYS.local.DISCUSSION_DESKTOP_DEFAULT_OPEN

const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  courseId: {
    type: [Number, String],
    default: null,
  },
  archiveId: {
    type: [Number, String],
    default: null,
  },
  previewUrl: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: '預覽文件',
  },
  academicYear: {
    type: [Number, String, Date],
    default: null,
  },
  archiveType: {
    type: String,
    default: '',
  },
  courseName: {
    type: String,
    default: '',
  },
  professorName: {
    type: String,
    default: '',
  },
  loading: {
    type: Boolean,
    default: false,
  },
  error: {
    type: Boolean,
    default: false,
  },
  showDownload: {
    type: Boolean,
    default: true,
  },
  showDiscussion: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:visible', 'hide', 'load', 'error', 'download'])

useUnauthorizedEvent(() => {
  emit('update:visible', false)
})

const localVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
})

const isMaximized = ref(false)
const isMobile = ref(false)
const discussionOpen = ref(false)
const discussionModalVisible = ref(false)
const discussionPanelRef = ref(null)
const discussionEnabled = computed(
  () => props.showDiscussion && Boolean(props.courseId) && Boolean(props.archiveId)
)

const archiveTypeLabel = computed(() => {
  const archiveTypeKey = (props.archiveType || '').trim().toLowerCase()
  const map = {
    midterm: '期中考',
    final: '期末考',
    quiz: '小考',
    other: '其他',
  }
  return map[archiveTypeKey] || (props.archiveType || '').trim()
})

const metaTextItems = computed(() => {
  let year = ''
  if (props.academicYear instanceof Date) {
    year = String(props.academicYear.getFullYear())
  } else if (props.academicYear !== null && props.academicYear !== undefined) {
    year = String(props.academicYear).trim()
  }

  const courseName = (props.courseName || '').trim()
  const professorName = (props.professorName || '').trim()
  const typeLabel = (archiveTypeLabel.value || '').trim()

  return [
    year ? { key: 'year', icon: 'pi-calendar', value: year } : null,
    courseName ? { key: 'course', icon: 'pi-book', value: courseName } : null,
    professorName ? { key: 'professor', icon: 'pi-user', value: professorName } : null,
    typeLabel ? { key: 'type', icon: 'pi-bookmark', value: typeLabel } : null,
  ].filter(Boolean)
})

const downloading = ref(false)
const pdfLoading = ref(false)
const pdfError = ref(false)
let activeLoadId = 0
const renderPdf = ref(false)
let resizeObserver = null
let resizeDebounceTimer = null
const ResizeObserverCtor = typeof ResizeObserver !== 'undefined' ? ResizeObserver : null
const pdfContainerRef = ref(null)
const resizeKey = ref(0)

const currentPdf = computed(() => props.previewUrl || '')
const { pdf, pages } = usePDF(currentPdf, {
  onError: handlePdfError,
})

watch(
  currentPdf,
  (val) => {
    pdfError.value = false
    pdfLoading.value = !!val
  },
  { immediate: true }
)

watch(
  () => props.visible,
  async (visible) => {
    renderPdf.value = false
    if (!visible) return

    // PrimeVue Dialog teleports + transitions; defer mounting the PDF renderer until the
    // content is actually attached to the DOM to avoid null `parentNode` errors.
    await nextTick()
    requestAnimationFrame(() => {
      if (props.visible) renderPdf.value = true
    })
  },
  { immediate: true }
)

watch(
  pdfContainerRef,
  (el) => {
    if (resizeObserver) {
      resizeObserver.disconnect()
      resizeObserver = null
    }
    if (resizeDebounceTimer) {
      clearTimeout(resizeDebounceTimer)
      resizeDebounceTimer = null
    }
    if (!ResizeObserverCtor) return
    if (!el) return

    const scheduleResizeKeyUpdate = (nextWidth) => {
      if (resizeDebounceTimer) clearTimeout(resizeDebounceTimer)
      resizeDebounceTimer = setTimeout(() => {
        if (!renderPdf.value) return
        if (!el.isConnected) return
        if (resizeKey.value === nextWidth) return
        resizeKey.value = nextWidth
      }, 80)
    }

    resizeObserver = new ResizeObserverCtor((entries) => {
      const entry = entries[0]
      if (!entry) return
      if (!renderPdf.value) return
      if (!el.isConnected) return

      const nextWidth = Math.round(entry.contentRect.width)
      if (!nextWidth) return
      scheduleResizeKeyUpdate(nextWidth)
    })
    resizeObserver.observe(el)

    // PrimeVue Dialog transitions can delay layout; capture a stable initial width.
    requestAnimationFrame(() => {
      if (!renderPdf.value) return
      if (!el.isConnected) return
      const nextWidth = Math.round(el.getBoundingClientRect().width)
      if (!nextWidth) return
      scheduleResizeKeyUpdate(nextWidth)
    })
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  if (resizeDebounceTimer) {
    clearTimeout(resizeDebounceTimer)
    resizeDebounceTimer = null
  }
})

watch(
  pdf,
  async (task) => {
    if (!task) {
      pdfLoading.value = false
      return
    }

    const loadId = ++activeLoadId
    pdfLoading.value = true
    pdfError.value = false

    try {
      if (task.promise) {
        await task.promise
      }
      if (loadId === activeLoadId) {
        pdfLoading.value = false
      }
    } catch (err) {
      if (loadId === activeLoadId) {
        handlePdfError(err)
      }
    }
  },
  { immediate: true }
)

function onHide() {
  pdfLoading.value = false
  pdfError.value = false
  isMaximized.value = false
  discussionOpen.value = isMobile.value
    ? false
    : getBooleanPreference(DESKTOP_DEFAULT_OPEN_KEY, true)
  discussionModalVisible.value = false
  emit('hide')
}

function handleMaximize() {
  isMaximized.value = true
}

function handleUnmaximize() {
  isMaximized.value = false
}

function toggleDiscussion() {
  discussionOpen.value = !discussionOpen.value
}

function handleDiscussionClick() {
  if (isMobile.value) {
    discussionModalVisible.value = true
    return
  }
  toggleDiscussion()
}

function openDiscussionSettings() {
  discussionPanelRef.value?.openNicknameDialog?.()
}

function handleDesktopDefaultOpenChange(isOpen) {
  if (isMobile.value) return
  discussionOpen.value = Boolean(isOpen)
}

function updateIsMobile() {
  const prev = isMobile.value
  const next =
    typeof window !== 'undefined' && window.matchMedia
      ? window.matchMedia('(max-width: 768px)').matches
      : false

  isMobile.value = next
  if (next) {
    discussionOpen.value = false
  } else if (prev && !next) {
    discussionOpen.value = getBooleanPreference(DESKTOP_DEFAULT_OPEN_KEY, true)
  }
  if (prev && !next) {
    discussionModalVisible.value = false
  }
}

onMounted(() => {
  updateIsMobile()
  discussionOpen.value = isMobile.value
    ? false
    : getBooleanPreference(DESKTOP_DEFAULT_OPEN_KEY, true)
  if (typeof window !== 'undefined') {
    window.addEventListener('resize', updateIsMobile, { passive: true })
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateIsMobile)
  }
})

function handlePdfError(err) {
  console.error('PDF loading failed:', err)
  pdfError.value = true
  pdfLoading.value = false
  emit('error')
}

function handlePdfLoaded() {
  pdfLoading.value = false
  pdfError.value = false
  emit('load')
}

function handleDownload() {
  downloading.value = true
  emit('download', () => {
    downloading.value = false
  })
}
</script>

<style scoped>
.pdf-container {
  width: 100%;
  height: 100%;
  overflow: auto;
  scrollbar-gutter: stable;
  display: flex;
  flex-direction: column;
  background-color: #525659;
}

.pdf-pages {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.pdf-page {
  width: 100%;
  max-width: 100%;
}

.discussion-wrapper {
  min-width: 0;
  flex: 0 0 auto;
  overflow: hidden;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  transition:
    width 220ms ease,
    margin-left 220ms ease,
    opacity 220ms ease;
}

.discussion-wrapper :deep(.discussion-panel) {
  height: 100%;
  min-height: 0;
}

.discussion-wrapper.is-open {
  width: min(380px, 40%);
  margin-left: 1rem;
  opacity: 1;
  pointer-events: auto;
}

.discussion-wrapper.is-closed {
  width: 0;
  margin-left: 0;
  opacity: 0;
  pointer-events: none;
}

@media (prefers-reduced-motion: reduce) {
  .discussion-wrapper {
    transition: none;
  }
}

.discussion-modal-panel {
  height: 100%;
}

.discussion-modal-panel :deep(.discussion-panel) {
  height: 100%;
  max-width: none;
  border-radius: 0;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
  :deep(.p-dialog .p-dialog-header) {
    font-size: 1rem;
  }

  :deep(.p-dialog .p-dialog-footer .p-button) {
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
  }
}
</style>
