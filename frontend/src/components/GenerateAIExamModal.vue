<template>
  <div>
    <Dialog
      :visible="visible"
      @update:visible="$emit('update:visible', $event)"
      :modal="true"
      :draggable="false"
      header="AI 生成模擬試題"
      :style="{ width: '900px', maxWidth: '95vw' }"
      :autoFocus="false"
    >
      <div
        v-if="currentStep === 'loading'"
        class="flex flex-column align-items-center justify-content-center p-6"
      >
        <ProgressSpinner strokeWidth="4" />
        <p class="mt-4 text-lg font-semibold">載入中...</p>
      </div>

      <div v-else-if="currentStep === 'selectProfessor'" class="flex flex-column gap-4">
        <div class="flex flex-column gap-2">
          <label class="font-semibold">課程分類</label>
          <Select
            v-model="form.category"
            :options="categoryOptions"
            optionLabel="name"
            optionValue="value"
            placeholder="選擇課程分類"
            class="w-full"
            @change="onCategoryChange"
          />
        </div>

        <div class="flex flex-column gap-2">
          <label class="font-semibold">課程名稱</label>
          <Select
            v-model="form.course_name"
            :options="availableCourses"
            optionLabel="name"
            optionValue="name"
            placeholder="選擇課程"
            class="w-full"
            :disabled="!form.category"
            filter
            @change="onCourseChange"
          />
        </div>

        <div class="flex flex-column gap-2">
          <label class="font-semibold">教授</label>
          <Select
            v-model="form.professor"
            :options="availableProfessors"
            placeholder="選擇教授"
            class="w-full"
            :disabled="!form.course_name"
            filter
            @change="onProfessorChange"
          />
        </div>
      </div>

      <!-- Step 2: Select past exams -->
      <div v-else-if="currentStep === 'selectArchives'" class="flex flex-column gap-3">
        <div class="font-semibold">{{ form.course_name }} - {{ form.professor }}</div>

        <!-- Type filter -->
        <div class="field">
          <label for="archiveTypeFilter" class="block mb-2 font-semibold">考古題類型</label>
          <Select
            id="archiveTypeFilter"
            v-model="archiveTypeFilter"
            :options="archiveTypeOptions"
            optionLabel="name"
            optionValue="value"
            placeholder="選擇類型"
            class="w-full"
            showClear
          />
        </div>

        <div class="text-sm text-500">找到 {{ filteredArchives.length }} 份考古題</div>

        <div v-if="filteredArchives.length === 0" class="p-4 text-center text-500">
          <i class="pi pi-inbox text-4xl mb-3"></i>
          <div>找不到該教授的期中考或期末考</div>
        </div>

        <div v-else class="flex flex-column gap-2" style="max-height: 30vh; overflow-y: auto">
          <div
            v-for="archive in filteredArchives"
            :key="archive.id"
            class="p-3 border-round surface-50"
            :class="{
              'surface-200': selectedArchiveIds.includes(archive.id),
              'opacity-50': isArchiveDisabled(archive.id),
            }"
          >
            <div class="flex align-items-center gap-3">
              <Checkbox
                :modelValue="selectedArchiveIds.includes(archive.id)"
                :binary="true"
                :disabled="isArchiveDisabled(archive.id)"
                @change="toggleArchiveSelection(archive.id)"
              />
              <div
                class="flex-1 cursor-pointer"
                @click="!isArchiveDisabled(archive.id) && toggleArchiveSelection(archive.id)"
              >
                <div class="font-semibold">{{ archive.name }}</div>
                <div class="text-sm text-500 mt-1">
                  <span class="mr-3">
                    <i class="pi pi-calendar mr-1"></i>
                    {{ archive.academic_year }}
                  </span>
                  <span>
                    <i class="pi pi-bookmark mr-1"></i>
                    {{ getArchiveTypeName(archive.archive_type) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="flex flex-column gap-2">
          <div class="text-sm text-500">
            建議選擇 2-3 份考古題以獲得最佳生成效果
            <span v-if="selectedArchiveIds.length > 0" class="font-semibold text-green-600">
              （已選擇 {{ selectedArchiveIds.length }}/3）
            </span>
          </div>
        </div>
      </div>

      <div
        v-else-if="currentStep === 'generating'"
        class="flex flex-column align-items-center justify-content-center p-6"
      >
        <ProgressSpinner strokeWidth="4" />
        <p class="mt-4 text-lg font-semibold">AI 正在分析考古題並生成模擬試題...</p>
        <p class="text-sm text-500 mt-2">這可能需要 2-5 分鐘，您可以關閉視窗稍後再回來查看結果</p>
        <div class="mt-4 text-center">
          <p class="text-sm text-500">正在分析：</p>
          <p class="font-semibold">{{ form.course_name }} - {{ form.professor }}</p>
        </div>
      </div>

      <div
        v-else-if="currentStep === 'error'"
        class="flex flex-column align-items-center justify-content-center p-6"
      >
        <i class="pi pi-exclamation-triangle text-6xl text-red-500 mb-4"></i>
        <p class="text-lg font-semibold text-red-600 mb-2">生成失敗</p>
        <p class="text-500">{{ errorMessage }}</p>
      </div>

      <!-- Result step -->
      <div v-else-if="currentStep === 'result'" class="flex flex-column gap-3">
        <div class="font-semibold">{{ form.course_name }} - {{ form.professor }}</div>
        <div class="p-3 surface-100 border-round">
          <div class="text-sm text-500 mb-2">使用的考古題</div>
          <div v-for="(archive, index) in result.archives_used" :key="index" class="text-sm mb-1">
            <i class="pi pi-file-pdf text-red-500 mr-2"></i>
            <span class="font-semibold">{{ archive.academic_year }}</span> -
            {{ archive.name }}
          </div>
        </div>

        <Divider />

        <div class="generated-content" style="max-height: 50vh; overflow-y: auto">
          <div class="flex justify-content-between align-items-center mb-3">
            <div class="text-lg font-semibold">生成的模擬試題</div>
            <Button
              icon="pi pi-copy"
              label="複製"
              size="small"
              severity="secondary"
              @click="copyContent"
            />
          </div>
          <div class="whitespace-pre-wrap p-3 surface-50 border-round" style="line-height: 1.8">
            {{ result.generated_content }}
          </div>
        </div>
      </div>

      <!-- Footer actions -->

      <template #footer>
        <div class="flex items-center gap-2 w-full">
          <Button
            icon="pi pi-cog"
            label="API Key 設定"
            severity="secondary"
            @click="openApiKeyModal"
          />

          <div class="flex gap-2 ml-auto">
            <Button
              v-if="currentStep === 'selectArchives'"
              label="上一步"
              icon="pi pi-arrow-left"
              severity="secondary"
              @click="goBackToProfessorSelection"
            />
            <Button
              v-if="currentStep === 'selectProfessor'"
              label="下一步"
              icon="pi pi-arrow-right"
              severity="success"
              @click="goToArchiveSelection"
              :disabled="!canGoToNextStep"
            />
            <Button
              v-else-if="currentStep === 'selectArchives'"
              label="開始生成"
              icon="pi pi-sparkles"
              severity="info"
              @click="generateExam"
              :disabled="selectedArchiveIds.length === 0"
            />
            <Button
              v-else-if="currentStep === 'result'"
              label="重新生成"
              icon="pi pi-refresh"
              severity="secondary"
              @click="confirmRegenerate"
            />
            <Button
              v-if="currentStep === 'result'"
              label="下載 TXT"
              icon="pi pi-download"
              severity="success"
              @click="downloadResult"
            />
            <Button
              v-else-if="currentStep === 'error'"
              label="重試"
              icon="pi pi-refresh"
              severity="warning"
              @click="resetToSelect"
            />
          </div>
        </div>
      </template>
    </Dialog>

    <!-- API key settings modal -->
    <Dialog
      :visible="showApiKeyModal"
      @update:visible="handleApiKeyModalClose"
      :modal="true"
      header="API Key 設定"
      :style="{ width: '500px' }"
      :draggable="false"
      :closable="true"
    >
      <div class="flex flex-column gap-4">
        <div class="text-sm text-500">請設定您的 Google Gemini API Key 以使用 AI 生成功能</div>

        <div class="flex flex-column gap-2">
          <label class="font-semibold">API Key 狀態</label>
          <div v-if="apiKeyStatus.has_api_key" class="p-3 bg-green-50 border-round">
            <div class="flex align-items-center gap-2">
              <i class="pi pi-check-circle text-green-600"></i>
              <span class="text-green-700">已設定：{{ apiKeyStatus.api_key_masked }}</span>
            </div>
          </div>
          <div v-else class="p-3 bg-orange-50 border-round">
            <div class="flex align-items-center gap-2">
              <i class="pi pi-exclamation-triangle text-orange-600"></i>
              <span class="text-orange-700">尚未設定 API Key</span>
            </div>
          </div>
        </div>

        <div v-if="!apiKeyStatus.has_api_key" class="flex flex-column gap-2">
          <label class="font-semibold">Google Gemini API Key</label>
          <Password
            v-model="apiKeyForm.key"
            placeholder="輸入 Gemini API Key"
            class="w-full"
            inputClass="w-full"
            toggleMask
            :feedback="false"
          />
          <small class="text-500">
            您可以在
            <a href="https://aistudio.google.com/app/apikey" target="_blank" class="text-blue-300"
              >Google AI Studio</a
            >
            獲取免費的 API Key
          </small>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-content-end gap-2">
          <Button
            v-if="apiKeyStatus.has_api_key"
            label="移除"
            icon="pi pi-trash"
            severity="danger"
            @click="clearApiKey"
            :loading="apiKeyLoading"
          />
          <Button
            v-if="!apiKeyStatus.has_api_key"
            label="儲存"
            icon="pi pi-check"
            severity="success"
            @click="saveApiKey"
            :loading="apiKeyLoading"
            :disabled="!apiKeyForm.key.trim()"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, inject } from 'vue'
import { aiExamService, courseService } from '../api'
import { trackEvent, EVENTS } from '../utils/analytics'

const props = defineProps({
  visible: Boolean,
  coursesList: Object,
})

const emit = defineEmits(['update:visible'])

const toast = inject('toast')
const confirm = inject('confirm')

const currentStep = ref('loading')
const errorMessage = ref('')
const result = ref(null)
const availableArchives = ref([])
const selectedArchiveIds = ref([])
const currentTaskId = ref(null)

const showApiKeyModal = ref(false)
const apiKeyStatus = ref({ has_api_key: false, api_key_masked: null })
const apiKeyForm = ref({ key: '' })
const apiKeyLoading = ref(false)

const TASK_STORAGE_KEY = 'aiExamCurrentTask'

const form = ref({
  category: null,
  course_name: null,
  professor: null,
})

const categoryOptions = [
  { name: '大一課程', value: 'freshman' },
  { name: '大二課程', value: 'sophomore' },
  { name: '大三課程', value: 'junior' },
  { name: '大四課程', value: 'senior' },
  { name: '研究所課程', value: 'graduate' },
  { name: '跨領域課程', value: 'interdisciplinary' },
  { name: '通識課程', value: 'general' },
]

const archiveTypeMap = {
  midterm: '期中考',
  final: '期末考',
  quiz: '小考',
  other: '其他',
}

const getArchiveTypeName = (type) => {
  return archiveTypeMap[type] || type
}

const availableCourses = computed(() => {
  if (!form.value.category || !props.coursesList) return []
  return props.coursesList[form.value.category] || []
})

const availableProfessors = ref([])
const archiveTypeFilter = ref(null)

const archiveTypeOptions = [
  { name: '期中考', value: 'midterm' },
  { name: '期末考', value: 'final' },
]

const filteredArchives = computed(() => {
  let archives = availableArchives.value.filter(
    (archive) => archive.archive_type === 'midterm' || archive.archive_type === 'final'
  )

  if (archiveTypeFilter.value) {
    archives = archives.filter((archive) => archive.archive_type === archiveTypeFilter.value)
  }

  return archives
})

const canGoToNextStep = computed(() => {
  return form.value.category && form.value.course_name && form.value.professor
})

const MAX_ARCHIVES = 3

const isArchiveDisabled = (archiveId) => {
  return (
    selectedArchiveIds.value.length >= MAX_ARCHIVES && !selectedArchiveIds.value.includes(archiveId)
  )
}

const toggleArchiveSelection = (archiveId) => {
  if (isArchiveDisabled(archiveId)) {
    return
  }

  const index = selectedArchiveIds.value.indexOf(archiveId)
  if (index > -1) {
    selectedArchiveIds.value.splice(index, 1)
  } else {
    selectedArchiveIds.value.push(archiveId)
  }
}

const onCategoryChange = () => {
  form.value.course_name = null
  form.value.professor = null
  availableProfessors.value = []
  availableArchives.value = []
  selectedArchiveIds.value = []
}

const onCourseChange = async () => {
  form.value.professor = null
  availableArchives.value = []
  selectedArchiveIds.value = []

  if (!form.value.course_name) {
    availableProfessors.value = []
    return
  }

  try {
    const course = availableCourses.value.find((c) => c.name === form.value.course_name)
    if (!course) return

    const { data } = await courseService.getCourseArchives(course.id)

    const professorsSet = new Set()
    data.forEach((archive) => {
      if (archive.professor) {
        professorsSet.add(archive.professor)
      }
    })

    availableProfessors.value = Array.from(professorsSet).sort()
  } catch (error) {
    console.error('Error fetching professors:', error)
    toast.add({
      severity: 'error',
      summary: '載入失敗',
      detail: '無法載入教授清單',
      life: 3000,
    })
  }
}

const onProfessorChange = () => {
  availableArchives.value = []
  selectedArchiveIds.value = []
}

const goToArchiveSelection = async () => {
  if (!canGoToNextStep.value) return

  try {
    const course = availableCourses.value.find((c) => c.name === form.value.course_name)
    if (!course) return

    const { data } = await courseService.getCourseArchives(course.id)

    availableArchives.value = data
      .filter((archive) => archive.professor === form.value.professor)
      .sort((a, b) => b.academic_year - a.academic_year)

    if (availableArchives.value.length === 0) {
      toast.add({
        severity: 'warning',
        summary: '找不到考古題',
        detail: '該教授沒有考古題',
        life: 3000,
      })
      return
    }

    const hasValidArchives = availableArchives.value.some(
      (archive) => archive.archive_type === 'midterm' || archive.archive_type === 'final'
    )

    if (!hasValidArchives) {
      toast.add({
        severity: 'error',
        summary: '找不到考古題',
        detail: '該教授沒有期中考或期末考',
        life: 3000,
      })
      return
    }

    currentStep.value = 'selectArchives'
  } catch (error) {
    console.error('Error fetching archives:', error)
    toast.add({
      severity: 'error',
      summary: '載入失敗',
      detail: '服務暫時無法使用，請稍後再試',
      life: 3000,
    })
  }
}

const goBackToProfessorSelection = () => {
  currentStep.value = 'selectProfessor'
  selectedArchiveIds.value = []
  archiveTypeFilter.value = null
}

let pollInterval = null

const saveTaskToStorage = (taskId, displayInfo = {}) => {
  try {
    localStorage.setItem(
      TASK_STORAGE_KEY,
      JSON.stringify({
        taskId,
        displayInfo, // Store only the presentation-ready fields
        timestamp: Date.now(),
      })
    )
  } catch (e) {
    console.error('Failed to save task to storage:', e)
  }
}

const clearTaskFromStorage = () => {
  try {
    localStorage.removeItem(TASK_STORAGE_KEY)
  } catch (e) {
    console.error('Failed to clear task from storage:', e)
  }
}

const loadTaskFromStorage = () => {
  try {
    const stored = localStorage.getItem(TASK_STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.error('Failed to load task from storage:', e)
  }
  return null
}

const resumeTask = async (taskId) => {
  currentTaskId.value = taskId
  currentStep.value = 'generating'

  pollInterval = setInterval(async () => {
    try {
      const { data: statusData } = await aiExamService.getTaskStatus(taskId)

      if (statusData.status === 'complete') {
        clearInterval(pollInterval)
        pollInterval = null

        if (statusData.result && statusData.result.generated_content) {
          result.value = statusData.result
          currentStep.value = 'result'

          toast.add({
            severity: 'success',
            summary: '生成成功',
            detail: '模擬試題已成功生成',
            life: 3000,
          })

          trackEvent(EVENTS.GENERATE_AI_EXAM, {
            category: form.value.category || 'resumed',
            courseName: form.value.course_name || 'resumed',
            professor: form.value.professor || 'resumed',
            archivesUsed: statusData.result.archives_used.length,
          })
        } else {
          clearTaskFromStorage()
          errorMessage.value = '生成失敗，請稍後再試'
          currentStep.value = 'error'

          toast.add({
            severity: 'error',
            summary: '生成失敗',
            detail: errorMessage.value,
            life: 3000,
          })
        }
      } else if (statusData.status === 'failed' || statusData.status === 'not_found') {
        clearInterval(pollInterval)
        pollInterval = null
        clearTaskFromStorage()

        errorMessage.value = '生成失敗，請稍後再試'
        currentStep.value = 'error'

        toast.add({
          severity: 'error',
          summary: '生成失敗',
          detail: errorMessage.value,
          life: 3000,
        })
      }
    } catch (error) {
      console.error('Error polling task status:', error)
      clearInterval(pollInterval)
      pollInterval = null
      clearTaskFromStorage()

      errorMessage.value = '服務暫時無法使用，請稍後再試'
      currentStep.value = 'error'

      toast.add({
        severity: 'error',
        summary: '查詢失敗',
        detail: errorMessage.value,
        life: 3000,
      })
    }
  }, 10000)
}

const generateExam = async () => {
  if (selectedArchiveIds.value.length === 0) return

  clearTaskFromStorage()
  currentStep.value = 'generating'

  try {
    const { data: taskData } = await aiExamService.generateMockExam({
      archive_ids: selectedArchiveIds.value,
    })

    const taskId = taskData.task_id
    currentTaskId.value = taskId

    saveTaskToStorage(taskId, {
      course_name: form.value.course_name,
      professor: form.value.professor,
    })

    pollInterval = setInterval(async () => {
      try {
        const { data: statusData } = await aiExamService.getTaskStatus(taskId)

        if (statusData.status === 'complete') {
          clearInterval(pollInterval)
          pollInterval = null

          if (statusData.result && statusData.result.generated_content) {
            result.value = statusData.result
            currentStep.value = 'result'

            toast.add({
              severity: 'success',
              summary: '生成成功',
              detail: '模擬試題已成功生成',
              life: 3000,
            })

            trackEvent(EVENTS.GENERATE_AI_EXAM, {
              category: form.value.category,
              courseName: form.value.course_name,
              professor: form.value.professor,
              archivesUsed: statusData.result.archives_used.length,
            })
          } else {
            clearTaskFromStorage()
            errorMessage.value = '生成失敗，請稍後再試'
            currentStep.value = 'error'

            toast.add({
              severity: 'error',
              summary: '生成失敗',
              detail: errorMessage.value,
              life: 3000,
            })
          }
        } else if (statusData.status === 'failed' || statusData.status === 'not_found') {
          clearInterval(pollInterval)
          pollInterval = null
          clearTaskFromStorage()

          errorMessage.value = '生成失敗，請稍後再試'
          currentStep.value = 'error'

          toast.add({
            severity: 'error',
            summary: '生成失敗',
            detail: errorMessage.value,
            life: 3000,
          })
        }
      } catch (error) {
        console.error('Error polling task status:', error)
        clearInterval(pollInterval)
        pollInterval = null
        clearTaskFromStorage()

        errorMessage.value = '服務暫時無法使用，請稍後再試'
        currentStep.value = 'error'

        toast.add({
          severity: 'error',
          summary: '查詢失敗',
          detail: errorMessage.value,
          life: 3000,
        })
      }
    }, 10000)
  } catch (error) {
    console.error('AI generation error:', error)
    clearTaskFromStorage()

    // Handle specific error cases
    if (error.response?.status === 409) {
      errorMessage.value = '您已有一個進行中的任務，請等待完成後再提交新任務'
      toast.add({
        severity: 'warn',
        summary: '任務衝突',
        detail: errorMessage.value,
        life: 3000,
      })
    } else {
      errorMessage.value = '提交失敗，請稍後再試'
      toast.add({
        severity: 'error',
        summary: '提交失敗',
        detail: errorMessage.value,
        life: 3000,
      })
    }

    currentStep.value = 'error'
  }
}

const copyContent = async () => {
  if (!result.value) return

  try {
    await navigator.clipboard.writeText(result.value.generated_content)
    toast.add({
      severity: 'success',
      summary: '複製成功',
      detail: '內容已複製到剪貼簿',
      life: 3000,
    })
  } catch (error) {
    console.error('Copy error:', error)
    toast.add({
      severity: 'error',
      summary: '複製失敗',
      detail: '無法複製到剪貼簿',
      life: 3000,
    })
  }
}

const downloadResult = () => {
  if (!result.value) return

  const content = result.value.generated_content
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${form.value.course_name}_${form.value.professor}_模擬試題.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  toast.add({
    severity: 'success',
    summary: '下載成功',
    detail: '模擬試題已下載',
    life: 3000,
  })
}

const resetToSelect = () => {
  clearTaskFromStorage()
  currentStep.value = 'selectProfessor'
  errorMessage.value = ''
  result.value = null
  selectedArchiveIds.value = []
  availableArchives.value = []
  archiveTypeFilter.value = null
  currentTaskId.value = null
}

const confirmRegenerate = () => {
  confirm.require({
    message:
      '你將回到一開始選擇的介面，並且現在的內容將無法再取得。如需保留請先下載。確定要繼續嗎？',
    header: '確認重新生成',
    icon: 'pi pi-exclamation-triangle',
    accept: () => {
      resetToSelect()
    },
  })
}

watch(
  () => props.visible,
  async (newVal) => {
    if (newVal) {
      // Load API key status
      loadApiKeyStatus()

      // Check for unfinished task when modal opens
      const savedTask = loadTaskFromStorage()
      if (savedTask && savedTask.taskId) {
        try {
          const { data: statusData } = await aiExamService.getTaskStatus(savedTask.taskId)

          if (statusData.status === 'complete') {
            if (statusData.result && statusData.result.generated_content) {
              result.value = statusData.result
              currentStep.value = 'result'
              currentTaskId.value = savedTask.taskId

              if (savedTask.displayInfo) {
                if (savedTask.displayInfo.course_name)
                  form.value.course_name = savedTask.displayInfo.course_name
                if (savedTask.displayInfo.professor)
                  form.value.professor = savedTask.displayInfo.professor
              }
            } else {
              clearTaskFromStorage()
              currentStep.value = 'selectProfessor'
            }
          } else if (statusData.status === 'pending' || statusData.status === 'in_progress') {
            if (savedTask.displayInfo) {
              if (savedTask.displayInfo.course_name)
                form.value.course_name = savedTask.displayInfo.course_name
              if (savedTask.displayInfo.professor)
                form.value.professor = savedTask.displayInfo.professor
            }
            await resumeTask(savedTask.taskId)
          } else {
            clearTaskFromStorage()
            currentStep.value = 'selectProfessor'
          }
        } catch (error) {
          console.error('Failed to check saved task:', error)
          clearTaskFromStorage()
          currentStep.value = 'selectProfessor'
        }
      } else {
        // No saved task, go to professor selection
        currentStep.value = 'selectProfessor'
      }
    } else {
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }

      // Reset form only if no task has started
      setTimeout(() => {
        if (currentStep.value === 'selectProfessor' || currentStep.value === 'selectArchives') {
          // Only reset form if still in selection phase (no task started)
          form.value = {
            category: null,
            course_name: null,
            professor: null,
          }
          availableProfessors.value = []
          selectedArchiveIds.value = []
          availableArchives.value = []
          archiveTypeFilter.value = null
          errorMessage.value = ''
        }
        // Don't reset currentTaskId and result if task has been started
      }, 300)
    }
  }
)

// API key helpers
const loadApiKeyStatus = async () => {
  try {
    const response = await aiExamService.getApiKeyStatus()
    apiKeyStatus.value = response.data

    // Automatically open the settings modal if no API key is configured
    if (!apiKeyStatus.value.has_api_key) {
      showApiKeyModal.value = true
    }
  } catch (error) {
    console.error('Failed to load API key status:', error)
  }
}

const openApiKeyModal = async () => {
  try {
    const response = await aiExamService.getApiKeyStatus()
    apiKeyStatus.value = response.data
    showApiKeyModal.value = true
  } catch (error) {
    console.error('Failed to load API key status:', error)
    showApiKeyModal.value = true
  }
}

const saveApiKey = async () => {
  if (!apiKeyForm.value.key.trim()) return

  apiKeyLoading.value = true
  try {
    const response = await aiExamService.updateApiKey(apiKeyForm.value.key)
    apiKeyStatus.value = response.data
    apiKeyForm.value.key = ''

    toast.add({
      severity: 'success',
      summary: '設定成功',
      detail: 'API Key 測試通過並已成功設定',
      life: 3000,
    })
  } catch (error) {
    console.error('Failed to save API key:', error)
    toast.add({
      severity: 'error',
      summary: '設定失敗',
      detail: '請確認 API Key 是否正確',
      life: 3000,
    })
  } finally {
    apiKeyLoading.value = false
  }
}

const clearApiKey = async () => {
  apiKeyLoading.value = true
  try {
    const response = await aiExamService.updateApiKey('')
    apiKeyStatus.value = response.data
    apiKeyForm.value.key = ''

    toast.add({
      severity: 'success',
      summary: '移除成功',
      detail: 'API Key 已移除',
      life: 3000,
    })
  } catch (error) {
    console.error('Failed to clear API key:', error)
    toast.add({
      severity: 'error',
      summary: '移除失敗',
      detail: 'API Key 移除失敗，請稍後再試',
      life: 3000,
    })
  } finally {
    apiKeyLoading.value = false
  }
}

const handleApiKeyModalClose = (visible) => {
  showApiKeyModal.value = visible

  if (!visible && !apiKeyStatus.value.has_api_key) {
    emit('update:visible', false)
  }
}
</script>

<style scoped>
.generated-content {
  font-family: 'Courier New', monospace;
}
</style>
