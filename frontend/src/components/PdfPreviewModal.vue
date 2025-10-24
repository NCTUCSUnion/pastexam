<template>
  <Dialog
    :visible="localVisible"
    @update:visible="localVisible = $event"
    :style="{ width: '1200px', height: '90vh' }"
    :contentStyle="{ height: '80vh' }"
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
        v-if="loading || pdfLoading"
        class="flex-1 flex align-items-center justify-content-center"
      >
        <ProgressSpinner strokeWidth="4" />
      </div>

      <div
        v-else-if="error || pdfError"
        class="flex-1 flex flex-column align-items-center justify-content-center gap-4"
      >
        <i class="pi pi-exclamation-circle text-6xl text-red-500" />
        <div class="text-xl">無法載入預覽</div>
        <div class="text-sm text-gray-600">請嘗試下載檔案查看</div>
      </div>

      <div v-else-if="previewUrl" class="flex-1 pdf-container">
        <VuePdfEmbed
          :source="previewUrl"
          class="pdf-viewer"
          @loaded="handlePdfLoaded"
          @loading-failed="handlePdfError"
        />
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
import { computed, ref } from 'vue'
import VuePdfEmbed from 'vue-pdf-embed'
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

function onHide() {
  // Reset PDF states when modal is hidden
  pdfLoading.value = false
  pdfError.value = false
  emit('hide')
}

function handlePdfLoaded() {
  pdfLoading.value = false
  pdfError.value = false
  emit('load')
}

function handlePdfError(error) {
  console.error('PDF loading failed:', error)
  pdfLoading.value = false
  pdfError.value = true
  emit('error')
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
  display: flex;
  justify-content: center;
  background-color: #525659;
}

.pdf-viewer {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

:deep(.vue-pdf-embed) {
  width: 100%;
}

:deep(.vue-pdf-embed > div) {
  margin-bottom: 10px;
  box-shadow: 0 2px 8px 4px rgba(0, 0, 0, 0.1);
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
