<template>
  <div>
    <Dialog
      :visible="visible"
      @update:visible="handleVisibility"
      modal
      :style="{ width: '700px', maxWidth: '95vw' }"
      :draggable="false"
      :blockScroll="true"
      :pt="{ root: { 'aria-label': '公告中心', 'aria-labelledby': null } }"
    >
      <template #header>
        <div class="flex align-items-center gap-2.5">
          <i class="pi pi-bell text-2xl" />
          <div class="text-xl leading-tight font-semibold">公告中心</div>
        </div>
      </template>
      <div v-if="loading" class="flex justify-content-center py-5">
        <ProgressSpinner style="width: 40px; height: 40px" strokeWidth="4" />
      </div>
      <div v-else>
        <div
          v-if="notifications.length === 0"
          class="flex flex-column align-items-center gap-2 py-5 text-500"
        >
          <i class="pi pi-megaphone text-4xl"></i>
          <span class="text-sm mt-2">目前沒有公告</span>
        </div>
        <DataTable
          v-else
          :value="notifications"
          :rows="5"
          paginator
          :rowsPerPageOptions="[5]"
          paginatorTemplate="PrevPageLink NextPageLink"
          class="notification-table"
        >
          <Column field="title" header="標題">
            <template #body="{ data }">
              <span class="font-medium">{{ data.title }}</span>
            </template>
          </Column>
          <Column field="severity" header="重要程度" style="width: 120px">
            <template #body="{ data }">
              <Tag :severity="resolveSeverity(data.severity)" class="text-xs">
                {{ resolveSeverityLabel(data.severity) }}
              </Tag>
            </template>
          </Column>
          <Column field="updated_at" header="最近更新" style="width: 140px">
            <template #body="{ data }">
              <span class="text-sm text-500">
                {{ formatDate(data.updated_at || data.created_at) }}
              </span>
            </template>
          </Column>
          <Column header="操作" style="width: 100px">
            <template #body="{ data }">
              <Button
                label="檢視"
                size="small"
                severity="secondary"
                outlined
                @click="openDetail(data)"
              />
            </template>
          </Column>
        </DataTable>
      </div>
    </Dialog>

    <Dialog
      v-if="detailVisible"
      :visible="detailVisible"
      @update:visible="handleDetailVisibility"
      modal
      :style="{ width: '520px', maxWidth: '90vw' }"
      :draggable="false"
      :blockScroll="true"
      :pt="{ root: { 'aria-label': '公告內容', 'aria-labelledby': null } }"
    >
      <template #header>
        <div class="flex align-items-center gap-2.5">
          <i class="pi pi-bell text-2xl" />
          <div class="text-xl leading-tight font-semibold">公告內容</div>
        </div>
      </template>
      <div v-if="selectedNotification" class="flex flex-column gap-3">
        <div class="flex justify-content-between align-items-start gap-3">
          <div class="flex flex-column gap-1">
            <span class="text-lg font-semibold">{{ selectedNotification.title }}</span>
            <small class="text-500">
              更新於
              {{
                formatTimestamp(selectedNotification.updated_at || selectedNotification.created_at)
              }}
            </small>
          </div>
          <Tag :severity="resolveSeverity(selectedNotification.severity)">
            {{ resolveSeverityLabel(selectedNotification.severity) }}
          </Tag>
        </div>
        <div class="notification-body">
          <div class="markdown-content text-sm leading-normal" v-html="renderedBody"></div>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { renderMarkdown } from '@/utils/markdown'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  notifications: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:visible', 'mark-seen'])

const resolveSeverity = (value) => (value === 'danger' ? 'danger' : 'info')
const resolveSeverityLabel = (value) => (value === 'danger' ? '重要' : '一般')

const detailVisible = ref(false)
const selectedNotification = ref(null)
const renderedBody = computed(() =>
  selectedNotification.value ? renderMarkdown(selectedNotification.value.body || '') : ''
)

const handleVisibility = (value) => {
  emit('update:visible', value)
}

const openDetail = (notification) => {
  selectedNotification.value = notification
  detailVisible.value = true
  emit('mark-seen', notification)
}

const handleDetailClose = () => {
  detailVisible.value = false
  selectedNotification.value = null
}

watch(
  () => props.visible,
  (value) => {
    if (!value) {
      handleDetailClose()
    }
  }
)

const handleDetailVisibility = (value) => {
  if (!value) {
    handleDetailClose()
  } else {
    detailVisible.value = true
  }
}

const formatDate = (value) => {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
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
.notification-row {
  transition: background-color 0.2s ease;
}

.notification-row:hover {
  background-color: var(--highlight-bg);
}

.notification-badge {
  min-width: 3.5rem;
  text-align: center;
  white-space: nowrap;
}

.notification-body {
  min-height: 120px;
  max-height: 55vh;
  overflow-y: auto;
  padding-right: 0.5rem;
}

:deep(.notification-table) {
  font-size: 0.875rem;
  overflow-x: auto;
}

:deep(.notification-table .p-datatable-wrapper) {
  overflow-x: auto;
}

:deep(.notification-table .p-datatable-table) {
  min-width: 640px;
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
  background-color: rgba(0, 0, 0, 0.08);
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
  color: inherit;
}

:global(.dark) .markdown-content :deep(code) {
  background-color: rgba(255, 255, 255, 0.1);
}

.markdown-content :deep(pre) {
  background-color: rgba(0, 0, 0, 0.08);
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.75rem 0;
  color: inherit;
}

:global(.dark) .markdown-content :deep(pre) {
  background-color: rgba(255, 255, 255, 0.1);
}

.markdown-content :deep(pre code) {
  background-color: transparent !important;
  padding: 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid rgba(0, 0, 0, 0.15);
  padding-left: 1rem;
  margin: 0.75rem 0;
  color: inherit;
  opacity: 0.8;
}

:global(.dark) .markdown-content :deep(blockquote) {
  border-left-color: rgba(255, 255, 255, 0.2);
}

.markdown-content :deep(blockquote p) {
  margin: 0;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid rgba(0, 0, 0, 0.15);
  margin: 1rem 0;
}

:global(.dark) .markdown-content :deep(hr) {
  border-top-color: rgba(255, 255, 255, 0.2);
}

.markdown-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 0.75rem 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid rgba(0, 0, 0, 0.15);
  padding: 0.5rem;
  text-align: left;
}

:global(.dark) .markdown-content :deep(th),
:global(.dark) .markdown-content :deep(td) {
  border-color: rgba(255, 255, 255, 0.2);
}

.markdown-content :deep(th) {
  background-color: rgba(0, 0, 0, 0.05);
  font-weight: 600;
}

:global(.dark) .markdown-content :deep(th) {
  background-color: rgba(255, 255, 255, 0.05);
}

.markdown-content :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  margin: 0.5rem 0;
}
</style>

<style>
/* Dark mode styles - must be in non-scoped style block */
.dark .markdown-content code {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.dark .markdown-content pre {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

.dark .markdown-content blockquote {
  border-left-color: rgba(255, 255, 255, 0.2) !important;
}

.dark .markdown-content hr {
  border-top-color: rgba(255, 255, 255, 0.2) !important;
}

.dark .markdown-content th,
.dark .markdown-content td {
  border-color: rgba(255, 255, 255, 0.2) !important;
}

.dark .markdown-content th {
  background-color: rgba(255, 255, 255, 0.05) !important;
}
</style>
