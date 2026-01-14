<template>
  <div class="h-full" ref="archiveView" @toggle-sidebar="toggleSidebar">
    <div class="flex h-full relative">
      <!-- Desktop/Tablet Sidebar -->
      <div class="sidebar hidden md:block" :class="{ collapsed: !sidebarVisible }">
        <div class="flex flex-column h-full">
          <!-- Fixed search section -->
          <div class="search-section p-3">
            <div class="relative w-full">
              <i class="pi pi-search absolute left-4 top-1/2 -mt-2 text-500"></i>
              <InputText v-model="searchQuery" placeholder="搜尋課程" class="w-full pl-6" />
            </div>
          </div>

          <!-- Scrollable content section -->
          <div class="flex-1 overflow-auto p-3 pt-0">
            <div v-if="searchQuery" class="search-results">
              <div v-if="filteredCategories.length === 0" class="p-3 text-center text-500">
                <i class="pi pi-search text-2xl mb-2"></i>
                <div>查無搜尋結果</div>
              </div>
              <div v-for="category in filteredCategories" :key="category.label" class="mb-2">
                <div class="text-sm mb-1" style="color: var(--text-secondary)">
                  {{ category.label }}
                </div>
                <div class="flex flex-col gap-1">
                  <Button
                    v-for="course in category.items"
                    :key="course.label"
                    class="p-button-text search-result-btn text-color"
                    @click="filterBySubject({ label: course.label, id: course.id })"
                  >
                    <span class="ellipsis">{{ course.label }}</span>
                  </Button>
                </div>
              </div>
            </div>
            <PanelMenu
              v-else
              :model="menuItems"
              :expandedKeys="expandedMenuItems"
              @update:expandedKeys="expandedMenuItems = $event"
              class="w-full"
            />
          </div>

          <!-- Fixed upload section for desktop -->
          <div v-if="isAuthenticatedRef" class="upload-section p-3">
            <Button
              icon="pi pi-cloud-upload"
              label="上傳考古題"
              severity="success"
              @click="showUploadDialog = true"
              class="w-full"
              size="small"
            />
          </div>
        </div>
      </div>

      <!-- Mobile Drawer -->
      <Drawer
        v-if="isMobile"
        :visible="sidebarVisible"
        @update:visible="sidebarVisible = $event"
        class="mobile-drawer"
        position="left"
        :style="{ width: '300px', maxWidth: '85vw' }"
        :autoFocus="false"
      >
        <template #header>
          <div class="flex justify-content-between align-items-center w-full">
            <span class="font-semibold">選單</span>
          </div>
        </template>
        <div class="flex flex-column h-full">
          <!-- Fixed search section -->
          <div class="search-section pb-3">
            <div class="relative w-full">
              <i class="pi pi-search absolute left-4 top-1/2 -mt-2 text-500"></i>
              <InputText v-model="searchQuery" placeholder="搜尋課程" class="w-full pl-6" />
            </div>
          </div>

          <!-- Scrollable course selection section -->
          <div class="flex-1 overflow-auto">
            <div v-if="searchQuery" class="search-results">
              <div v-if="filteredCategories.length === 0" class="p-3 text-center text-500">
                <i class="pi pi-search text-2xl mb-2"></i>
                <div>查無搜尋結果</div>
              </div>
              <div v-for="category in filteredCategories" :key="category.label" class="mb-2">
                <div class="text-sm mb-1" style="color: var(--text-secondary)">
                  {{ category.label }}
                </div>
                <div class="flex flex-col gap-1">
                  <Button
                    v-for="course in category.items"
                    :key="course.label"
                    class="p-button-text search-result-btn text-color"
                    @click="
                      () => {
                        filterBySubject({ label: course.label, id: course.id })
                        sidebarVisible = false
                      }
                    "
                  >
                    <span class="ellipsis">{{ course.label }}</span>
                  </Button>
                </div>
              </div>
            </div>
            <PanelMenu v-else :model="mobileMenuItems" multiple class="w-full" />
          </div>
        </div>
      </Drawer>

      <div class="main-content flex-1 h-full overflow-auto">
        <div class="card h-full flex flex-col">
          <div v-if="selectedSubject" class="p-3 subject-header">
            <div class="flex align-items-center gap-2">
              <Tag severity="secondary" class="text-sm">
                {{ getCategoryTag(getCategoryName(getCurrentCategory)) }}
              </Tag>
              <span class="text-xl font-medium">{{ selectedSubject }}</span>
            </div>
          </div>
          <Toolbar v-if="selectedSubject" class="m-3">
            <template #start>
              <div class="flex flex-wrap gap-3 w-full">
                <Select
                  v-model="filters.year"
                  :options="years"
                  optionLabel="name"
                  optionValue="code"
                  placeholder="選擇年份"
                  class="w-full md:w-14rem"
                  showClear
                  filter
                />
                <Select
                  v-model="filters.professor"
                  :options="professors"
                  optionLabel="name"
                  optionValue="code"
                  placeholder="選擇教授"
                  class="w-full md:w-14rem"
                  showClear
                  filter
                />
                <Select
                  v-model="filters.type"
                  :options="archiveTypes"
                  optionLabel="name"
                  optionValue="code"
                  placeholder="選擇類型"
                  class="w-full md:w-14rem"
                  showClear
                />
                <div class="flex align-items-center">
                  <Checkbox v-model="filters.hasAnswers" :binary="true" />
                  <label class="ml-2">附解答</label>
                </div>
              </div>
            </template>
          </Toolbar>

          <ProgressSpinner
            v-if="loading"
            class="w-full flex justify-content-center mt-4"
            strokeWidth="4"
          />

          <div v-else>
            <div v-if="selectedSubject">
              <Accordion
                v-model:value="expandedPanels"
                multiple
                class="max-w-[calc(100%-2rem)] mx-auto"
              >
                <AccordionPanel
                  v-for="group in groupedArchives"
                  :key="group.year"
                  :value="group.year.toString()"
                >
                  <AccordionHeader>{{ group.year }} 年</AccordionHeader>
                  <AccordionContent>
                    <DataTable :value="group.list">
                      <Column header="教授" field="professor" style="width: 10%"></Column>
                      <Column header="類型" style="width: 10%">
                        <template #body="{ data }">
                          <Tag :severity="archiveTypeConfig[data.type]?.severity || 'secondary'">
                            {{ archiveTypeConfig[data.type]?.name || data.type }}
                          </Tag>
                        </template>
                      </Column>
                      <Column header="考試名稱" field="name" style="width: 15%"></Column>
                      <Column header="解答" style="width: 10%">
                        <template #body="{ data }">
                          <Tag :severity="data.hasAnswers ? 'info' : 'secondary'">
                            {{ data.hasAnswers ? '附解答' : '僅題目' }}
                          </Tag>
                        </template>
                      </Column>
                      <Column header="下載次數" style="width: 10%">
                        <template #body="{ data }">
                          <span>{{ formatDownloadCount(data.downloadCount) }}</span>
                        </template>
                      </Column>
                      <Column header="操作" style="width: 35%">
                        <template #body="{ data }">
                          <div class="flex gap-2.5">
                            <Button
                              icon="pi pi-eye"
                              @click="previewArchive(data)"
                              size="small"
                              severity="secondary"
                              label="預覽"
                            />
                            <Button
                              icon="pi pi-download"
                              @click="downloadArchive(data)"
                              size="small"
                              severity="success"
                              label="下載"
                              :loading="downloadingId === data.id"
                            />
                            <Button
                              v-if="canEditArchive(data)"
                              icon="pi pi-pencil"
                              @click="openEditDialog(data)"
                              size="small"
                              severity="warning"
                              label="編輯"
                            />
                            <Button
                              v-if="canDeleteArchive(data)"
                              icon="pi pi-trash"
                              @click="confirmDelete(data)"
                              size="small"
                              severity="danger"
                              label="刪除"
                            />
                          </div>
                        </template>
                      </Column>
                    </DataTable>
                  </AccordionContent>
                </AccordionPanel>
              </Accordion>
            </div>
            <div
              v-else
              class="flex flex-column align-items-center justify-content-center h-full"
              style="min-height: calc(100vh - 200px)"
            >
              <i class="pi pi-book text-6xl" style="color: var(--text-secondary)"></i>
              <div class="text-xl font-medium mt-4" style="color: var(--text-secondary)">
                請從左側選單選擇課程
              </div>
              <div class="text-sm mt-2" style="color: var(--text-secondary)">
                選擇課程後即可瀏覽相關考古題
              </div>
            </div>
          </div>

          <PdfPreviewModal
            :visible="showPreview"
            @update:visible="showPreview = $event"
            :courseId="selectedCourse"
            :archiveId="selectedArchive?.id"
            :previewUrl="selectedArchive?.previewUrl"
            :title="selectedArchive?.name || ''"
            :academicYear="selectedArchive?.year"
            :archiveType="selectedArchive?.type || ''"
            :courseName="selectedSubject || ''"
            :professorName="selectedArchive?.professor || ''"
            :loading="previewLoading"
            :error="previewError"
            @hide="closePreview"
            @error="handlePreviewError"
            @download="handlePreviewDownload"
          />

          <UploadArchiveDialog
            v-model="showUploadDialog"
            :coursesList="coursesList"
            @upload-success="handleUploadSuccess"
          />

          <Dialog
            :visible="showEditDialog"
            @update:visible="showEditDialog = $event"
            :modal="true"
            :draggable="false"
            :closeOnEscape="false"
            header="編輯考古題"
            :style="{ width: '600px', maxWidth: '90vw' }"
            :autoFocus="false"
          >
            <div class="flex flex-column">
              <div class="flex flex-column gap-2">
                <label>考試名稱</label>
                <InputText v-model="editForm.name" placeholder="輸入考試名稱" class="w-full" />
              </div>

              <div class="flex flex-column gap-2 mt-3">
                <label>授課教授</label>
                <AutoComplete
                  :modelValue="editForm.professor"
                  @update:modelValue="(val) => (editForm.professor = val)"
                  :suggestions="availableEditProfessors"
                  @complete="searchEditProfessor"
                  @item-select="onEditProfessorSelect"
                  @focus="() => searchEditProfessor({ query: '' })"
                  @click="() => searchEditProfessor({ query: '' })"
                  optionLabel="name"
                  placeholder="選擇授課教授"
                  class="w-full"
                  dropdown
                  completeOnFocus
                  :minLength="0"
                  autoHighlight="true"
                >
                  <template #item="{ item }">
                    <div>{{ item.name }}</div>
                  </template>
                </AutoComplete>
              </div>

              <div class="flex flex-column gap-2 mt-3">
                <label>考試年份</label>
                <DatePicker
                  v-model="editForm.academicYear"
                  @update:modelValue="(val) => (editForm.academicYear = val)"
                  view="year"
                  dateFormat="yy"
                  :showIcon="true"
                  placeholder="選擇考試年份"
                  class="w-full"
                  :maxDate="new Date()"
                  :minDate="new Date(2000, 0, 1)"
                />
              </div>

              <div class="flex flex-column gap-2 mt-3">
                <label>考試類型</label>
                <Select
                  v-model="editForm.type"
                  :options="[
                    { name: '期中考', value: 'midterm' },
                    { name: '期末考', value: 'final' },
                    { name: '小考', value: 'quiz' },
                    { name: '其他', value: 'other' },
                  ]"
                  optionLabel="name"
                  optionValue="value"
                  placeholder="選擇考試類型"
                  class="w-full"
                />
              </div>

              <div class="flex align-items-center gap-2 mt-3">
                <Checkbox v-model="editForm.hasAnswers" :binary="true" />
                <label>附解答</label>
              </div>

              <Divider class="mt-3" />

              <div class="flex align-items-center gap-2">
                <Checkbox v-model="editForm.shouldTransfer" :binary="true" />
                <label class="font-semibold">轉移到其他課程</label>
              </div>

              <div v-if="editForm.shouldTransfer" class="flex flex-column pl-4 mt-3">
                <div class="flex flex-column gap-2">
                  <label>目標課程類別</label>
                  <Select
                    v-model="editForm.targetCategory"
                    :options="categoryOptions"
                    optionLabel="name"
                    optionValue="value"
                    placeholder="選擇課程類別"
                    class="w-full"
                  />
                </div>

                <div class="flex flex-column gap-2 mt-3">
                  <label>目標課程名稱</label>
                  <AutoComplete
                    v-model="editForm.targetCourse"
                    :suggestions="availableCoursesForTransfer"
                    @complete="searchTargetCourse"
                    @item-select="onTargetCourseSelect"
                    @focus="() => searchTargetCourse({ query: '' })"
                    @click="() => searchTargetCourse({ query: '' })"
                    optionLabel="label"
                    placeholder="搜尋或輸入目標課程名稱"
                    class="w-full"
                    :disabled="!editForm.targetCategory"
                    dropdown
                    completeOnFocus
                    :minLength="0"
                    autoHighlight="true"
                  >
                    <template #item="{ item }">
                      <div>{{ item.label }}</div>
                    </template>
                  </AutoComplete>
                </div>
              </div>
            </div>
            <div class="flex pt-6 justify-end gap-2.5">
              <Button
                label="取消"
                icon="pi pi-times"
                severity="secondary"
                @click="closeEditDialog"
              />
              <Button
                :label="editForm.shouldTransfer ? '儲存並轉移' : '儲存'"
                :icon="editForm.shouldTransfer ? 'pi pi-arrow-right-arrow-left' : 'pi pi-check'"
                severity="success"
                @click="handleEdit"
                :loading="editLoading"
              />
            </div>
          </Dialog>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: 'ArchiveView',
})

import { ref, computed, onMounted, watch, inject, onBeforeUnmount } from 'vue'
import { courseService, archiveService } from '../api'
import PdfPreviewModal from '../components/PdfPreviewModal.vue'
import UploadArchiveDialog from '../components/UploadArchiveDialog.vue'
import { getCurrentUser, isAuthenticated } from '../utils/auth'
import { useTheme } from '../utils/useTheme'
import { trackEvent, EVENTS } from '../utils/analytics'
import { isUnauthorizedError } from '../utils/http'
import {
  STORAGE_KEYS,
  getLocalJson,
  setLocalJson,
  removeLocalItem,
  setSessionJson,
} from '../utils/storage'

const toast = inject('toast')
const confirm = inject('confirm')

const { isDarkTheme } = useTheme()
const sidebarVisible = inject('sidebarVisible')

// Check if we're on mobile
const isMobile = ref(false)

const checkDevice = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkDevice()
  window.addEventListener('resize', checkDevice)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkDevice)
  if (searchDebounceTimer) {
    clearTimeout(searchDebounceTimer)
  }
})

// Auth related data
const isAuthenticatedRef = ref(false)
const userData = ref(null)

const archives = ref([])
const loading = ref(true)
const filters = ref({
  year: '',
  professor: '',
  type: '',
  hasAnswers: false,
})

// Track filter changes
watch(
  filters,
  (newFilters, oldFilters) => {
    shouldResetPanels.value = true

    // Only track if at least one filter is active and different from old value
    const hasActiveFilter =
      newFilters.year || newFilters.professor || newFilters.type || newFilters.hasAnswers

    if (hasActiveFilter && oldFilters) {
      const changedFilters = {}
      if (newFilters.year !== oldFilters.year) changedFilters.year = !!newFilters.year
      if (newFilters.professor !== oldFilters.professor)
        changedFilters.professor = !!newFilters.professor
      if (newFilters.type !== oldFilters.type) changedFilters.type = !!newFilters.type
      if (newFilters.hasAnswers !== oldFilters.hasAnswers)
        changedFilters.hasAnswers = newFilters.hasAnswers

      if (Object.keys(changedFilters).length > 0) {
        trackEvent(EVENTS.FILTER_ARCHIVES, {
          activeFilters: {
            year: !!newFilters.year,
            professor: !!newFilters.professor,
            type: !!newFilters.type,
            hasAnswers: newFilters.hasAnswers,
          },
          changedFilters,
        })
      }
    }
  },
  { deep: true }
)

const showPreview = ref(false)
const selectedArchive = ref(null)
const selectedSubject = ref(null)
const selectedCourse = ref(null)
const showUploadDialog = ref(false)
const uploadFormProfessors = ref([])
const expandedPanels = ref([])
const expandedMenuItems = ref({})
const shouldResetPanels = ref(true)

const CATEGORIES = {
  freshman: { name: '大一課程', icon: 'pi pi-fw pi-book', tag: '大一' },
  sophomore: { name: '大二課程', icon: 'pi pi-fw pi-book', tag: '大二' },
  junior: { name: '大三課程', icon: 'pi pi-fw pi-book', tag: '大三' },
  senior: { name: '大四課程', icon: 'pi pi-fw pi-book', tag: '大四' },
  graduate: {
    name: '研究所課程',
    icon: 'pi pi-fw pi-graduation-cap',
    tag: '研究所',
  },
  interdisciplinary: {
    name: '跨領域課程',
    icon: 'pi pi-fw pi-globe',
    tag: '跨領域',
  },
  general: { name: '通識課程', icon: 'pi pi-fw pi-lightbulb', tag: '通識' },
}

const coursesList = ref({
  freshman: [],
  sophomore: [],
  junior: [],
  senior: [],
  graduate: [],
  interdisciplinary: [],
  general: [],
})

const archiveTypeConfig = {
  midterm: {
    name: '期中考',
    severity: 'secondary',
  },
  final: {
    name: '期末考',
    severity: 'secondary',
  },
  quiz: {
    name: '小考',
    severity: 'secondary',
  },
  other: {
    name: '其他',
    severity: 'secondary',
  },
}

const years = ref([])
const professors = ref([])
const archiveTypes = ref([])

const searchQuery = ref('')

// Track search query changes with debounce
let searchDebounceTimer = null
watch(searchQuery, (newValue) => {
  if (searchDebounceTimer) {
    clearTimeout(searchDebounceTimer)
  }

  if (newValue && newValue.trim().length > 0) {
    searchDebounceTimer = setTimeout(() => {
      trackEvent(EVENTS.SEARCH_COURSE, {
        query: newValue,
        queryLength: newValue.length,
      })
    }, 1000) // 1 second debounce
  }
})

const ISSUE_CONTEXT_STORAGE_KEY = STORAGE_KEYS.session.ISSUE_CONTEXT

function persistIssueContext() {
  try {
    if (typeof window === 'undefined') return

    const selectedSubjectStored = getLocalJson(STORAGE_KEYS.local.SELECTED_SUBJECT)

    const payload = {
      page: 'archive',
      timestamp: new Date().toISOString(),
      course: {
        id: selectedCourse.value ?? selectedSubjectStored?.id ?? null,
        name: selectedSubject.value ?? selectedSubjectStored?.label ?? null,
      },
      filters: {
        year: filters.value?.year || null,
        professor: filters.value?.professor || null,
        type: filters.value?.type || null,
        hasAnswers: Boolean(filters.value?.hasAnswers),
        searchQuery: searchQuery.value || null,
      },
      preview: {
        open: Boolean(showPreview.value),
        archiveId: selectedArchive.value?.id ?? null,
        name: selectedArchive.value?.name ?? null,
        year: selectedArchive.value?.year ?? null,
        professor: selectedArchive.value?.professor ?? null,
        type: selectedArchive.value?.type ?? null,
        hasAnswers: selectedArchive.value?.hasAnswers ?? null,
      },
    }

    setSessionJson(ISSUE_CONTEXT_STORAGE_KEY, payload)
  } catch {
    // ignore
  }
}

watch(
  () => [
    selectedCourse.value,
    selectedSubject.value,
    showPreview.value,
    selectedArchive.value?.id,
    filters.value?.year,
    filters.value?.professor,
    filters.value?.type,
    filters.value?.hasAnswers,
    searchQuery.value,
  ],
  () => persistIssueContext(),
  { immediate: true }
)

const menuItems = computed(() => {
  if (!coursesList.value) return []

  return Object.entries(CATEGORIES).map(([key, category]) => ({
    key: key,
    label: category.name,
    icon: category.icon,
    items: (coursesList.value[key] || [])
      .map((course) => ({
        label: course.name,
        command: () => filterBySubject({ label: course.name, id: course.id }),
      }))
      .sort((a, b) => a.label.localeCompare(b.label)),
  }))
})

const filteredCategories = computed(() => {
  if (!searchQuery.value) {
    return []
  }

  const query = searchQuery.value.trim().toLowerCase().normalize('NFKC')
  const filtered = []

  menuItems.value.forEach((category) => {
    const filteredItems = category.items.filter((item) => {
      const itemLabelLower = item.label.toLowerCase().normalize('NFKC')
      const isIncluded = itemLabelLower.includes(query)
      return isIncluded
    })

    if (filteredItems.length > 0) {
      filtered.push({
        ...category,
        items: filteredItems
          .map((item) => {
            const course = coursesList.value[getCategoryKey(category.label)].find(
              (c) => c.name === item.label
            )
            return {
              label: item.label,
              id: course?.id,
            }
          })
          .sort((a, b) => a.label.localeCompare(b.label)),
      })
    }
  })

  return filtered
})

function getCategoryKey(categoryLabel) {
  return Object.keys(CATEGORIES).find((key) => CATEGORIES[key].name === categoryLabel) || ''
}

function getCategoryKeyForCourse(courseId) {
  for (const [categoryKey, courses] of Object.entries(coursesList.value)) {
    if (courses.some((course) => course.id === courseId)) {
      return categoryKey
    }
  }
  return null
}

const groupedArchives = computed(() => {
  if (!archives.value) return []

  const filteredArchives = archives.value.filter((archive) => {
    if (filters.value.year && archive.year.toString() !== filters.value.year) return false
    if (filters.value.professor && archive.professor !== filters.value.professor) return false
    if (filters.value.type && archive.type !== filters.value.type) return false
    if (filters.value.hasAnswers && !archive.hasAnswers) return false
    return true
  })

  const groups = {}
  filteredArchives.forEach((archive) => {
    if (!groups[archive.year]) {
      groups[archive.year] = {
        year: archive.year,
        list: [],
      }
    }
    groups[archive.year].list.push(archive)
  })

  Object.values(groups).forEach((group) => {
    group.list.sort((a, b) => {
      // Define exam type priority
      const typePriority = {
        midterm: 1,
        final: 2,
        quiz: 3,
        other: 4,
      }

      const aPriority = typePriority[a.type] || 4
      const bPriority = typePriority[b.type] || 4

      if (aPriority !== bPriority) {
        return aPriority - bPriority
      }

      return a.name.localeCompare(b.name, 'en')
    })
  })

  return Object.values(groups).sort((a, b) => b.year - a.year)
})

async function fetchCourses() {
  try {
    loading.value = true
    const response = await courseService.listCourses()

    // Only update coursesList if the data has actually changed to prevent unnecessary re-renders
    const newData = response.data
    const currentData = coursesList.value

    // Simple comparison - if structure looks the same, don't update
    let hasChanged = false
    if (!currentData || Object.keys(currentData).length === 0) {
      hasChanged = true
    } else {
      for (const category of Object.keys(newData)) {
        if (!currentData[category] || currentData[category].length !== newData[category].length) {
          hasChanged = true
          break
        }
      }
    }

    if (hasChanged) {
      coursesList.value = newData
    }
  } catch (error) {
    console.error('Error fetching courses:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '載入失敗',
      detail: '無法載入課程資料',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

function filterBySubject(course) {
  if (!course || !course.id) {
    selectedSubject.value = null
    selectedCourse.value = null
    archives.value = []
    expandedMenuItems.value = {}
    shouldResetPanels.value = true
    removeLocalItem(STORAGE_KEYS.local.SELECTED_SUBJECT)
    return
  }

  trackEvent(EVENTS.SELECT_COURSE, {
    courseName: course.label,
    courseId: course.id,
  })

  selectedSubject.value = course.label
  selectedCourse.value = course.id
  filters.value.professor = ''
  filters.value.year = ''
  filters.value.type = ''
  expandedPanels.value = []
  shouldResetPanels.value = true

  const categoryKey = getCategoryKeyForCourse(course.id)
  if (categoryKey) {
    expandedMenuItems.value = { [categoryKey]: true }
    // console.log("Expanding category:", categoryKey, expandedMenuItems.value);
  }

  setLocalJson(STORAGE_KEYS.local.SELECTED_SUBJECT, { label: course.label, id: course.id })

  fetchArchives()
}

async function fetchArchives() {
  try {
    loading.value = true
    const response = await courseService.getCourseArchives(selectedCourse.value)
    archives.value = response.data.map((archive) => ({
      id: archive.id,
      year: archive.academic_year,
      name: archive.name,
      type: archive.archive_type,
      professor: archive.professor,
      hasAnswers: archive.has_answers,
      subject: selectedSubject.value,
      uploader_id: archive.uploader_id,
      downloadCount: archive.download_count,
    }))

    const uniqueYears = new Set()
    const uniqueProfessors = new Set()
    const uniqueTypes = new Set()

    archives.value.forEach((archive) => {
      if (archive.year) uniqueYears.add(archive.year.toString())
      if (archive.professor) uniqueProfessors.add(archive.professor)
      if (archive.type) uniqueTypes.add(archive.type)
    })

    years.value = Array.from(uniqueYears)
      .sort((a, b) => b - a)
      .map((year) => ({
        name: year,
        code: year,
      }))

    professors.value = Array.from(uniqueProfessors)
      .sort()
      .map((professor) => ({
        name: professor,
        code: professor,
      }))

    archiveTypes.value = Array.from(uniqueTypes)
      .sort()
      .map((type) => ({
        name: archiveTypeConfig[type]?.name || type,
        code: type,
      }))
  } catch (error) {
    console.error('Error fetching archives:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '載入失敗',
      detail: '無法載入考古題資料',
      life: 3000,
    })
  } finally {
    loading.value = false
  }
}

const downloadingId = ref(null)

async function syncArchiveDownloadCount(archiveId) {
  if (!selectedCourse.value) return

  const previousExpandedPanels = [...expandedPanels.value]
  const resetRequested = shouldResetPanels.value

  try {
    const response = await courseService.getCourseArchives(selectedCourse.value)
    const serverMap = new Map(response.data.map((item) => [item.id, item]))

    archives.value = archives.value.map((archive) => {
      const serverArchive = serverMap.get(archive.id)
      if (!serverArchive || serverArchive.download_count === archive.downloadCount) {
        return archive
      }
      return {
        ...archive,
        downloadCount: serverArchive.download_count,
      }
    })

    const serverArchive = serverMap.get(archiveId)
    if (serverArchive && selectedArchive.value?.id === archiveId) {
      selectedArchive.value = {
        ...selectedArchive.value,
        downloadCount: serverArchive.download_count,
      }
    }

    if (!resetRequested) {
      const availableYears = Array.from(
        new Set(
          archives.value
            .map((item) =>
              item.year !== undefined && item.year !== null ? item.year.toString() : null
            )
            .filter((year) => year !== null)
        )
      )

      const preservedPanels = previousExpandedPanels.filter((year) => availableYears.includes(year))
      expandedPanels.value = preservedPanels
    }
  } catch (error) {
    console.error('Sync download count error:', error)
  }
}

async function downloadArchive(archive) {
  try {
    downloadingId.value = archive.id

    const { data } = await archiveService.getArchiveDownloadUrl(selectedCourse.value, archive.id)

    const response = await fetch(data.url)
    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`)
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    const fileName = `${archive.year}_${selectedSubject.value}_${archive.professor}_${archive.name}.pdf`
    link.download = fileName
    link.style.display = 'none'

    document.body.appendChild(link)
    link.click()
    setTimeout(() => {
      window.URL.revokeObjectURL(url)
      link.remove()
    }, 100)

    trackEvent(EVENTS.DOWNLOAD_ARCHIVE, {
      archiveName: archive.name,
      year: archive.year,
      professor: archive.professor,
      type: archive.type,
      courseName: selectedSubject.value,
      source: 'archive-list',
    })

    toast.add({
      severity: 'success',
      summary: '下載成功',
      detail: `已下載 ${fileName}`,
      life: 3000,
    })

    await syncArchiveDownloadCount(archive.id)
  } catch (error) {
    console.error('Download error:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '下載失敗',
      detail: '無法取得下載連結',
      life: 3000,
    })
  } finally {
    downloadingId.value = null
  }
}

const previewLoading = ref(false)
const previewError = ref(false)

async function previewArchive(archive) {
  try {
    previewLoading.value = true
    previewError.value = false
    showPreview.value = true

    const { data } = await archiveService.getArchivePreviewUrl(selectedCourse.value, archive.id)

    selectedArchive.value = {
      ...archive,
      previewUrl: data.url,
    }

    trackEvent(EVENTS.PREVIEW_ARCHIVE, {
      archiveName: archive.name,
      year: archive.year,
      professor: archive.professor,
      type: archive.type,
      courseName: selectedSubject.value,
    })
  } catch (error) {
    console.error('Preview error:', error)
    previewError.value = true
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '預覽失敗',
      detail: '無法取得預覽連結',
      life: 3000,
    })
  } finally {
    previewLoading.value = false
  }
}

function handlePreviewError() {
  previewError.value = true
}

function closePreview() {
  showPreview.value = false
  selectedArchive.value = null
  previewError.value = false
}

function getCategoryName(code) {
  return CATEGORIES[code]?.name || code
}

const availableEditProfessors = ref([])

const categoryOptions = Object.entries(CATEGORIES).map(([value, category]) => ({
  name: category.name,
  value: value,
}))

watch(
  () => groupedArchives.value,
  (newGroups) => {
    if (!newGroups.length) {
      // Clear expanded panels if no groups available
      expandedPanels.value = []
      shouldResetPanels.value = true
      return
    }

    const availableYears = newGroups.map((group) => group.year.toString())
    const preservedPanels = expandedPanels.value.filter((year) => availableYears.includes(year))

    if (shouldResetPanels.value) {
      // Default to expanding the most recent three years when reset is requested
      expandedPanels.value = newGroups.slice(0, 3).map((group) => group.year.toString())
    } else {
      expandedPanels.value = preservedPanels
    }

    shouldResetPanels.value = false
  },
  { immediate: true }
)

const isAdmin = ref(false)
const showEditDialog = ref(false)
const editForm = ref({
  id: null,
  name: '',
  professor: '',
  type: '',
  hasAnswers: false,
  academicYear: null,
  shouldTransfer: false,
  targetCategory: null,
  targetCourse: null,
  targetCourseId: null,
})

const editLoading = ref(false)

const allAvailableCoursesForTransfer = computed(() => {
  if (!editForm.value.targetCategory || !coursesList.value) {
    return []
  }

  const categoryData = coursesList.value[editForm.value.targetCategory]
  if (!categoryData) {
    return []
  }

  return categoryData
    .filter((course) => course.id !== selectedCourse.value)
    .map((course) => ({
      id: course.id,
      label: course.name,
    }))
    .sort((a, b) => a.label.localeCompare(b.label))
})

const availableCoursesForTransfer = ref([])

const canDeleteArchive = (archive) => {
  const currentUser = getCurrentUser()
  if (!currentUser) return false

  return isAdmin.value || (archive.uploader_id && archive.uploader_id === currentUser.id)
}

const canEditArchive = () => {
  return isAdmin.value
}

const confirmDelete = (archive) => {
  confirm.require({
    message: '確定要刪除此考古題嗎？',
    header: '確認刪除',
    icon: 'pi pi-exclamation-triangle',
    accept: () => {
      deleteArchive(archive)
    },
  })
}

const deleteArchive = async (archive) => {
  try {
    await archiveService.deleteArchive(selectedCourse.value, archive.id)

    trackEvent(EVENTS.DELETE_ARCHIVE, {
      archiveName: archive.name,
      year: archive.year,
      professor: archive.professor,
      type: archive.type,
      courseName: selectedSubject.value,
    })

    shouldResetPanels.value = true
    await fetchArchives()
    toast.add({
      severity: 'success',
      summary: '刪除成功',
      detail: '考古題已成功刪除',
      life: 3000,
    })
  } catch (error) {
    console.error('Delete error:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '刪除失敗',
      detail: '發生錯誤，請稍後再試',
      life: 3000,
    })
  }
}

const openEditDialog = async (archive) => {
  try {
    const response = await courseService.getCourseArchives(selectedCourse.value)
    const archiveData = response.data

    const uniqueProfessors = new Set()
    archiveData.forEach((item) => {
      if (item.professor) uniqueProfessors.add(item.professor)
    })

    uploadFormProfessors.value = Array.from(uniqueProfessors)
      .sort()
      .map((professor) => ({
        name: professor,
        code: professor,
      }))

    editForm.value = {
      id: archive.id,
      name: archive.name,
      professor: archive.professor,
      type: archive.type,
      hasAnswers: archive.hasAnswers,
      academicYear: archive.year ? new Date(parseInt(archive.year), 0, 1) : null,
      shouldTransfer: false,
      targetCategory: null,
      targetCourse: null,
      targetCourseId: null,
    }

    availableEditProfessors.value = uploadFormProfessors.value

    trackEvent(EVENTS.EDIT_ARCHIVE, {
      action: 'open-dialog',
      archiveName: archive.name,
      year: archive.year,
    })

    showEditDialog.value = true
  } catch (error) {
    console.error('Error fetching professors:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '載入失敗',
      detail: '無法載入教授清單',
      life: 3000,
    })
  }
}

const handleEdit = async () => {
  try {
    editLoading.value = true

    await archiveService.updateArchive(selectedCourse.value, editForm.value.id, {
      name: editForm.value.name,
      professor: editForm.value.professor,
      archive_type: editForm.value.type,
      has_answers: editForm.value.hasAnswers,
      academic_year: editForm.value.academicYear ? editForm.value.academicYear.getFullYear() : null,
    })

    if (editForm.value.shouldTransfer && editForm.value.targetCategory) {
      if (editForm.value.targetCourseId) {
        // Transfer to existing course
        await archiveService.updateArchiveCourse(
          selectedCourse.value,
          editForm.value.id,
          editForm.value.targetCourseId
        )
      } else if (editForm.value.targetCourse) {
        // Transfer to new course (create if not exists)
        await archiveService.updateArchiveCourseByCategoryAndName(
          selectedCourse.value,
          editForm.value.id,
          editForm.value.targetCourse,
          editForm.value.targetCategory
        )
      }
    }

    trackEvent(EVENTS.EDIT_ARCHIVE, {
      action: 'submit',
      transferred: editForm.value.shouldTransfer,
      targetCategory: editForm.value.shouldTransfer ? editForm.value.targetCategory : null,
    })

    shouldResetPanels.value = true
    await fetchArchives()

    // If transfer was performed, refresh the course list to show the new course
    if (editForm.value.shouldTransfer) {
      await fetchCourses()
    }

    closeEditDialog()

    const successMessage = editForm.value.shouldTransfer
      ? '考古題已更新並轉移到新課程'
      : '考古題資訊已更新'

    toast.add({
      severity: 'success',
      summary: '更新成功',
      detail: successMessage,
      life: 3000,
    })
  } catch (error) {
    console.error('Update error:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '更新失敗',
      detail: '發生錯誤，請稍後再試',
      life: 3000,
    })
  } finally {
    editLoading.value = false
  }
}

onMounted(async () => {
  const user = getCurrentUser()
  isAdmin.value = user?.is_admin || false
  checkAuthentication()
  await fetchCourses()

  const subjectData = getLocalJson(STORAGE_KEYS.local.SELECTED_SUBJECT)
  if (subjectData) {
    try {
      // Verify the course still exists in the current course list
      const courseExists = Object.values(coursesList.value).some((category) =>
        category.some((course) => course.id === subjectData.id && course.name === subjectData.label)
      )

      if (courseExists) {
        selectedSubject.value = subjectData.label
        selectedCourse.value = subjectData.id

        const categoryKey = getCategoryKeyForCourse(subjectData.id)
        if (categoryKey) {
          expandedMenuItems.value = { [categoryKey]: true }
        }

        await fetchArchives()
      } else {
        removeLocalItem(STORAGE_KEYS.local.SELECTED_SUBJECT)
      }
    } catch (error) {
      console.error('Error parsing saved subject:', error)
      removeLocalItem(STORAGE_KEYS.local.SELECTED_SUBJECT)
    }
  }
})

watch(isDarkTheme, () => {})

async function handleUploadSuccess() {
  trackEvent(EVENTS.UPLOAD_ARCHIVE, {
    courseName: selectedSubject.value,
  })

  await fetchCourses()
  shouldResetPanels.value = true
  if (selectedCourse.value) {
    await fetchArchives()
  }
}

function getCategoryTag(categoryLabel) {
  const category = Object.values(CATEGORIES).find((cat) => cat.name === categoryLabel)
  return category?.tag || categoryLabel
}

function formatDownloadCount(count) {
  if (count === 0 || count === null || count === undefined) {
    return '0'
  }
  return count.toString()
}

function toggleSidebar() {
  trackEvent(EVENTS.TOGGLE_SIDEBAR, { visible: !sidebarVisible.value })
  sidebarVisible.value = !sidebarVisible.value
}

async function handlePreviewDownload(onComplete) {
  if (!selectedArchive.value) return

  try {
    const { data } = await archiveService.getArchiveDownloadUrl(
      selectedCourse.value,
      selectedArchive.value.id
    )

    const response = await fetch(data.url)
    if (!response.ok) {
      throw new Error(`Download failed with status ${response.status}`)
    }
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    const fileName = `${selectedArchive.value.year}_${selectedSubject.value}_${selectedArchive.value.professor}_${selectedArchive.value.name}.pdf`
    link.download = fileName
    link.style.display = 'none'

    document.body.appendChild(link)
    link.click()
    setTimeout(() => {
      window.URL.revokeObjectURL(url)
      link.remove()
    }, 100)

    trackEvent(EVENTS.DOWNLOAD_ARCHIVE, {
      archiveName: selectedArchive.value.name,
      year: selectedArchive.value.year,
      professor: selectedArchive.value.professor,
      type: selectedArchive.value.type,
      courseName: selectedSubject.value,
      source: 'preview-modal',
    })

    toast.add({
      severity: 'success',
      summary: '下載成功',
      detail: `已下載 ${fileName}`,
      life: 3000,
    })

    await syncArchiveDownloadCount(selectedArchive.value.id)
  } catch (error) {
    console.error('Download error:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '下載失敗',
      detail: '無法取得下載連結',
      life: 3000,
    })
  } finally {
    onComplete()
  }
}

const getCurrentCategory = computed(() => {
  if (!selectedCourse.value) return ''

  for (const [category, courses] of Object.entries(coursesList.value)) {
    const course = courses.find((c) => c.id === selectedCourse.value)
    if (course) return category
  }
  return ''
})

const searchEditProfessor = (event) => {
  const query = event?.query?.toLowerCase() || ''
  const filteredProfessors = uploadFormProfessors.value
    .filter((professor) => professor.name.toLowerCase().includes(query))
    .sort((a, b) => a.name.localeCompare(b.name))

  availableEditProfessors.value = filteredProfessors
}

const onEditProfessorSelect = (event) => {
  if (event.value && typeof event.value === 'object') {
    editForm.value.professor = event.value.name
  }
}

const closeEditDialog = () => {
  showEditDialog.value = false
  editForm.value = {
    id: null,
    name: '',
    professor: '',
    type: '',
    hasAnswers: false,
    academicYear: null,
    shouldTransfer: false,
    targetCategory: null,
    targetCourse: null,
    targetCourseId: null,
  }
}

const searchTargetCourse = (event) => {
  const query = event?.query?.toLowerCase() || ''
  const filteredCourses = allAvailableCoursesForTransfer.value
    .filter((course) => course.label.toLowerCase().includes(query))
    .sort((a, b) => a.label.localeCompare(b.label))

  availableCoursesForTransfer.value = filteredCourses
}

const onTargetCourseSelect = (event) => {
  if (event.value && typeof event.value === 'object') {
    editForm.value.targetCourse = event.value.label
    editForm.value.targetCourseId = event.value.id
  } else if (typeof event.value === 'string') {
    // User typed a new course name
    editForm.value.targetCourse = event.value
    editForm.value.targetCourseId = null
  }
}

// Handle direct input of course name
watch(
  () => editForm.value.targetCourse,
  (newValue) => {
    if (typeof newValue === 'string' && newValue) {
      // Check if it's an existing course
      const existingCourse = allAvailableCoursesForTransfer.value.find(
        (course) => course.label === newValue
      )
      if (existingCourse) {
        editForm.value.targetCourseId = existingCourse.id
      } else {
        editForm.value.targetCourseId = null
      }
    }
  }
)

watch(
  () => editForm.value.targetCategory,
  () => {
    editForm.value.targetCourseId = null
    editForm.value.targetCourse = null
    availableCoursesForTransfer.value = allAvailableCoursesForTransfer.value
  }
)

const checkAuthentication = () => {
  isAuthenticatedRef.value = isAuthenticated()
  if (isAuthenticatedRef.value) {
    const user = getCurrentUser()
    if (user) {
      userData.value = user
    } else {
      isAuthenticatedRef.value = false
      userData.value = null
    }
  } else {
    isAuthenticatedRef.value = false
    userData.value = null
  }
}

const mobileMenuItems = computed(() => {
  return menuItems.value.map((item) => ({
    ...item,
    items: item.items?.map((subItem) => ({
      ...subItem,
      command: () => {
        subItem.command()
        sidebarVisible.value = false
      },
    })),
  }))
})
</script>

<style scoped>
.card {
  position: relative;
  z-index: 1;
  background-color: var(--bg-primary);
}

:deep(.p-sidebar) {
  padding: 0;
  background-color: var(--bg-primary);
  z-index: 2;
  border-right: 1px solid var(--border-color);
}

:deep(.p-sidebar-header) {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-primary);
}

:deep(.p-sidebar-content) {
  padding: 1rem;
  background-color: var(--bg-primary);
}

:deep(.p-accordioncontent),
:deep(.p-accordioncontent-wrapper),
:deep(.p-accordioncontent-content) {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  overflow-x: hidden;
}

:deep(.p-input-icon-left) {
  width: 100%;
}

:deep(.p-input-icon-left i) {
  left: 0.75rem;
}

:deep(.p-input-icon-left input) {
  padding-left: 2.5rem;
  background: var(--bg-primary);
  border-color: var(--border-color);
  color: var(--text-color);
}

:deep(.p-input-icon-left input:focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 1px var(--primary-color);
}

.sidebar {
  width: 300px;
  min-width: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  transition: width 0.2s ease-in-out;
  overflow: hidden;
  position: relative;
  z-index: 1;
  height: calc(100% - 0.25rem);
  margin-left: 0.25rem;
  margin-bottom: 0.25rem;
  display: flex;
  flex-direction: column;
  box-shadow: none;
}

.upload-section {
  flex-shrink: 0;
  border-top: 1px solid var(--border-color);
}

.sidebar .flex-column {
  width: 100%;
  opacity: 1;
  white-space: nowrap;
  height: 100%;
  transition: opacity 0.2s ease-in-out;
  display: flex;
  flex-direction: column;
}

.sidebar .search-section {
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 0;
  min-width: 0;
  margin-left: 0;
  margin-bottom: 0;
  height: 100%;
  border-right: none;
}

.sidebar.collapsed .flex-column {
  opacity: 0;
  pointer-events: none;
}

.main-content {
  flex: 1 1 0%;
  min-width: 0;
  background: var(--bg-primary);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.subject-header {
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-primary);
  position: relative;
  z-index: 1;
}

.ellipsis {
  display: inline-block;
  max-width: 90%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
}

.search-result-btn {
  width: 100%;
  justify-content: flex-start;
  text-align: left;
  padding: 0.5rem;
  border-radius: 4px;
}

.search-results .text-sm {
  font-size: 0.875rem;
}

/* Mobile sidebar specific styles */
.mobile-drawer {
  display: none;
}

@media (max-width: 768px) {
  .mobile-drawer {
    display: block;
  }
}

:deep(.mobile-drawer .p-sidebar) {
  z-index: 1000;
}

:deep(.mobile-drawer .p-sidebar-content) {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  height: 100%;
}

:deep(.mobile-drawer .p-sidebar-header) {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-primary);
  position: relative;
}

:deep(.mobile-drawer .p-sidebar-close) {
  position: absolute;
  top: 50%;
  right: 1rem;
  transform: translateY(-50%);
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s;
}

:deep(.mobile-drawer .p-sidebar-close:hover) {
  background: var(--highlight-bg);
}

/* Ensure proper mobile responsiveness */
@media (max-width: 768px) {
  .main-content {
    width: 100%;
  }

  /* Dialog font size adjustments for mobile */
  :deep(.p-dialog .p-dialog-content) {
    font-size: 0.875rem;
  }

  :deep(.p-dialog .p-dialog-header) {
    font-size: 1rem;
  }

  :deep(.p-dialog label) {
    font-size: 0.875rem;
  }

  :deep(.p-dialog .p-inputtext) {
    font-size: 0.875rem;
  }

  :deep(.p-dialog .p-button) {
    font-size: 0.875rem;
    padding: 0.5rem 0.75rem;
  }

  :deep(.p-dialog .p-dropdown-label),
  :deep(.p-dialog .p-autocomplete-input),
  :deep(.p-dialog .p-calendar-input) {
    font-size: 0.875rem;
  }

  :deep(.p-dialog .p-checkbox-label) {
    font-size: 0.875rem;
  }

  /* Table responsive design for mobile */
  :deep(.p-accordioncontent-content .p-datatable) {
    font-size: 0.75rem;
    width: 100%;
    max-width: 100%;
  }

  :deep(.p-accordioncontent-content .p-datatable-table-container) {
    width: 100%;
    max-width: 100%;
    overflow-x: auto;
  }

  :deep(.p-datatable-table) {
    font-size: 0.75rem;
    min-width: 600px;
    width: 100%;
  }

  :deep(.p-datatable .p-datatable-thead > tr > th) {
    font-size: 0.75rem;
    padding: 0.5rem 0.25rem;
    white-space: nowrap;
  }

  :deep(.p-datatable .p-datatable-tbody > tr > td) {
    font-size: 0.75rem;
    padding: 0.5rem 0.25rem;
    white-space: nowrap;
  }

  :deep(.p-datatable .p-button) {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    white-space: nowrap;
  }

  :deep(.p-tag) {
    font-size: 0.625rem;
    padding: 0.125rem 0.375rem;
    white-space: nowrap;
  }

  /* Make table container scrollable on mobile */
  :deep(.p-accordion-content) {
    padding: 0.5rem;
    overflow-x: auto;
  }

  /* Adjust button groups for mobile */
  :deep(.p-datatable .p-column-header-content) {
    justify-content: center;
  }

  /* Ensure buttons don't wrap */
  :deep(.p-datatable .flex.gap-2\.5) {
    flex-wrap: nowrap;
    gap: 0.25rem;
  }

  /* Accordion adjustments for mobile */
  :deep(.p-accordion .p-accordion-header) {
    font-size: 0.875rem;
  }

  :deep(.p-accordion .p-accordion-content) {
    padding: 0.5rem;
  }
}

/* Desktop table overflow handling */
@media (min-width: 769px) {
  :deep(.p-accordioncontent-content .p-datatable) {
    width: 100%;
    max-width: 100%;
  }

  :deep(.p-accordioncontent-content .p-datatable-table-container) {
    width: 100%;
    max-width: 100%;
    overflow-x: auto;
  }

  :deep(.p-datatable-table) {
    min-width: 800px;
    width: 100%;
  }

  :deep(.p-datatable .p-datatable-thead > tr > th),
  :deep(.p-datatable .p-datatable-tbody > tr > td) {
    white-space: nowrap;
  }

  :deep(.p-datatable .p-button) {
    white-space: nowrap;
  }

  :deep(.p-tag) {
    white-space: nowrap;
  }

  /* Make accordion content scrollable on desktop too */
  :deep(.p-accordion-content) {
    overflow-x: auto;
  }

  /* Ensure buttons don't wrap on desktop */
  :deep(.p-datatable .flex.gap-2\.5) {
    flex-wrap: nowrap;
    gap: 0.5rem;
  }
}

/* Search section styles */
.search-section {
  flex-shrink: 0;
}

/* Scrollable content styles */
.sidebar .search-results,
.mobile-drawer .search-results {
  padding: 0.5rem;
}

.sidebar .search-results {
  white-space: nowrap;
  overflow: hidden;
}

.sidebar .search-results .p-button {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar :deep(.p-panelmenu) {
  white-space: nowrap;
}

.sidebar :deep(.p-panelmenu .p-panelmenu-content) {
  overflow: hidden;
}

.admin-section {
  flex-shrink: 0;
}
</style>
