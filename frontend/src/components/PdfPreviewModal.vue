<template>
  <Dialog
    v-model:visible="localVisible"
    :style="{ width: '90vw', height: '90vh' }"
    :contentStyle="{ height: '80vh' }"
    :modal="true"
    :draggable="false"
    :dismissableMask="true"
    :closeOnEscape="true"
    :maximizable="true"
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
        <ProgressSpinner />
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
      <slot name="footer"></slot>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue";

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
});

const emit = defineEmits(["update:visible", "hide", "load", "error"]);

const localVisible = computed({
  get: () => props.visible,
  set: (value) => emit("update:visible", value),
});

function onHide() {
  emit("hide");
}

function handleLoad() {
  emit("load");
}

function handleError() {
  emit("error");
}
</script>
