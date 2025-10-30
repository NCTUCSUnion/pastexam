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
        <div class="markdown-content text-sm leading-normal" v-html="renderedBody"></div>
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
import { computed } from 'vue'
import { renderMarkdown } from '@/utils/markdown'

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

const renderedBody = computed(() =>
  props.notification ? renderMarkdown(props.notification.body || '') : ''
)

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

.notification-body :deep(a) {
  color: var(--primary-color);
  text-decoration: underline;
  word-break: break-word;
}

.notification-body :deep(p) {
  margin: 0 0 0.75rem;
}

.notification-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3),
.markdown-content :deep(h4),
.markdown-content :deep(h5),
.markdown-content :deep(h6) {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-content :deep(h1) {
  font-size: 1.5rem;
}

.markdown-content :deep(h2) {
  font-size: 1.25rem;
}

.markdown-content :deep(h3) {
  font-size: 1.125rem;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content :deep(ul) {
  list-style-type: disc;
}

.markdown-content :deep(ol) {
  list-style-type: decimal;
}

.markdown-content :deep(li) {
  margin: 0.25rem 0;
  display: list-item;
}

.markdown-content :deep(code) {
  background-color: var(--surface-100);
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background-color: var(--surface-100);
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.75rem 0;
}

.markdown-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid rgba(0, 0, 0, 0.1);
  padding-left: 1rem;
  margin: 0.75rem 0;
  color: rgba(0, 0, 0, 0.65);
}

@media (prefers-color-scheme: dark) {
  .markdown-content :deep(blockquote) {
    border-left-color: rgba(255, 255, 255, 0.15);
    color: rgba(255, 255, 255, 0.65);
  }
}

.markdown-content :deep(blockquote p) {
  margin: 0;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  margin: 1rem 0;
}

@media (prefers-color-scheme: dark) {
  .markdown-content :deep(hr) {
    border-top-color: rgba(255, 255, 255, 0.15);
  }
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.75rem 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid rgba(0, 0, 0, 0.1);
  padding: 0.5rem;
  text-align: left;
}

@media (prefers-color-scheme: dark) {
  .markdown-content :deep(th),
  .markdown-content :deep(td) {
    border-color: rgba(255, 255, 255, 0.15);
  }
}

.markdown-content :deep(th) {
  background-color: var(--surface-50);
  font-weight: 600;
}

.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  margin: 0.5rem 0;
}
</style>
