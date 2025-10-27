<template>
  <div>
    <Dialog
      :visible="visible"
      @update:visible="handleVisibility"
      modal
      :style="{ width: '700px', maxWidth: '95vw' }"
      :draggable="false"
      header="公告中心"
      :blockScroll="true"
    >
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
          <Column field="created_at" header="建立日期" style="width: 140px">
            <template #body="{ data }">
              <span class="text-sm text-500">
                {{ formatDate(data.created_at) }}
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
      header="公告內容"
      :blockScroll="true"
    >
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
          <p class="m-0 whitespace-pre-line leading-normal text-sm">
            {{ selectedNotification.body }}
          </p>
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

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
}
</style>
