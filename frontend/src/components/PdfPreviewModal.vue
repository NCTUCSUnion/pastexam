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
    @hide="onHide"
  >
    <template #header>
      <div class="flex align-items-center gap-2">
        <i class="pi pi-file-pdf text-2xl" />
        <span class="text-xl">{{ title }}</span>
      </div>
    </template>

    <div class="w-full h-full flex flex-column">
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

      <div v-else-if="pdf" class="flex-1 pdf-container" ref="pdfContainerRef">
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
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { VuePDF, usePDF } from '@tato30/vue-pdf'
import '@tato30/vue-pdf/style.css'
import { useUnauthorizedEvent } from '../utils/useUnauthorizedEvent'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  previewUrl: {
    type: String,
    default: '',
  },
  title: {
    type: String,
    default: '預覽文件',
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
})

const emit = defineEmits(['update:visible', 'hide', 'load', 'error', 'download'])

useUnauthorizedEvent(() => {
  emit('update:visible', false)
})

const localVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value),
})

const downloading = ref(false)
const pdfLoading = ref(false)
const pdfError = ref(false)
let activeLoadId = 0
let resizeObserver = null
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
  emit('hide')
}

watch(
  pdfContainerRef,
  (el) => {
    if (resizeObserver) {
      resizeObserver.disconnect()
    }
    if (!ResizeObserverCtor) return
    if (!el) return
    resizeObserver = new ResizeObserverCtor((entries) => {
      const entry = entries[0]
      if (!entry) return
      resizeKey.value = Math.round(entry.contentRect.width)
    })
    resizeObserver.observe(el)
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
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

/* Mobile responsive adjustments */
@media (max-width: 768px) {
  :deep(.p-dialog .p-dialog-header) {
    font-size: 1rem;
  }

  :deep(.p-dialog .p-button) {
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
  }
}
</style>
