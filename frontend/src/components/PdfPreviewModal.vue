<template>
  <Dialog
    :visible="localVisible"
    @update:visible="localVisible = $event"
    :style="{ width: '1200px', maxWidth: '95vw', height: '90vh' }"
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
        v-if="loading"
        class="flex-1 flex align-items-center justify-content-center"
      >
        <ProgressSpinner strokeWidth="4" />
      </div>

      <div
        v-else-if="error"
        class="flex-1 flex flex-column align-items-center justify-content-center gap-4"
      >
        <i class="pi pi-exclamation-circle text-6xl text-red-500" />
        <div class="text-xl">無法載入預覽</div>
        <div class="text-sm text-gray-600">請嘗試下載檔案查看</div>
      </div>

      <div v-else-if="previewUrl" class="flex-1 relative">
        <iframe
          :src="previewUrl"
          class="absolute top-0 left-0 w-full h-full"
          type="application/pdf"
          frameborder="0"
          @load="handleLoad"
          @error="handleError"
          allow="fullscreen"
          referrerpolicy="no-referrer"
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
import { computed, ref } from "vue";

const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
  },
  previewUrl: {
    type: String,
    default: "",
  },
  title: {
    type: String,
    default: "預覽文件",
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
});

const emit = defineEmits([
  "update:visible",
  "hide",
  "load",
  "error",
  "download",
]);

const localVisible = computed({
  get: () => props.visible,
  set: (value) => emit("update:visible", value),
});

const downloading = ref(false);

function onHide() {
  emit("hide");
}

function handleLoad() {
  emit("load");
}

function handleError() {
  emit("error");
}

function handleDownload() {
  downloading.value = true;
  emit("download", () => {
    downloading.value = false;
  });
}
</script>

<style scoped>
.pdf-viewer {
  width: 100%;
  height: 80vh;
  display: flex;
  justify-content: center;
  align-items: center;
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

  .pdf-viewer {
    height: 70vh;
  }
}
</style>
