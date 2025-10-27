<template>
  <Dialog
    :visible="visible"
    @update:visible="handleVisibility"
    modal
    :style="{ width: '480px', maxWidth: '90vw' }"
    :draggable="false"
    :showHeader="true"
    header="系統公告"
    :blockScroll="true"
  >
    <div v-if="notification" class="flex flex-column gap-3">
      <div class="flex justify-content-between align-items-start gap-3">
        <div class="flex flex-column gap-1">
          <span class="text-lg font-semibold">{{ notification.title }}</span>
          <small class="text-500">
            更新於 {{ formatTimestamp(notification.updated_at || notification.created_at) }}
          </small>
        </div>
        <Tag :severity="resolveSeverity(notification.severity)">
          {{ resolveSeverityLabel(notification.severity) }}
        </Tag>
      </div>

      <div class="notification-body">
        <p class="m-0 whitespace-pre-line leading-normal text-sm">
          {{ notification.body }}
        </p>
      </div>

      <div class="flex justify-content-between align-items-center">
        <Button
          label="不再顯示"
          severity="secondary"
          outlined
          size="small"
          @click="handleDismiss"
        />
        <Button label="顯示全部" severity="secondary" size="small" @click="openCenter" />
      </div>
    </div>
    <div v-else class="p-3 text-sm text-500 text-center">目前沒有新的公告</div>
  </Dialog>
</template>

<script setup>
const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  notification: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['update:visible', 'dismiss', 'open-center'])

const resolveSeverity = (value) => (value === 'danger' ? 'danger' : 'info')
const resolveSeverityLabel = (value) => (value === 'danger' ? '重要' : '一般')

const handleVisibility = (value) => {
  emit('update:visible', value)
}

const handleClose = () => {
  emit('update:visible', false)
}

const handleDismiss = () => {
  if (!props.notification?.id) return
  emit('dismiss', props.notification)
  handleClose()
}

const openCenter = () => {
  emit('open-center')
}

const formatTimestamp = (value) => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<style scoped>
.notification-body {
  min-height: 120px;
}
</style>
