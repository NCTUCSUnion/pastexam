<template>
  <div class="h-full px-2 md:px-4 admin-container">
    <div class="card h-full flex flex-col">
      <Tabs :value="currentTab" class="flex-1" @update:value="handleTabChange">
        <TabList>
          <Tab value="0">課程管理</Tab>
          <Tab value="1">使用者管理</Tab>
          <Tab value="2">公告管理</Tab>
        </TabList>
        <TabPanels>
          <TabPanel value="0">
            <div class="p-2 md:p-4">
              <div
                class="flex flex-column md:flex-row justify-content-between align-items-start md:align-items-center mb-4 gap-3"
              >
                <div class="flex flex-column md:flex-row gap-3 w-full md:w-auto">
                  <div class="relative w-full md:w-auto">
                    <i class="pi pi-search search-icon"></i>
                    <InputText v-model="searchQuery" placeholder="搜尋課程" class="w-full pl-6" />
                  </div>
                  <Select
                    v-model="filterCategory"
                    :options="categoryOptions"
                    optionLabel="name"
                    optionValue="value"
                    placeholder="篩選分類"
                    showClear
                    class="w-full md:w-14rem"
                  />
                </div>
                <Button
                  label="新增課程"
                  icon="pi pi-plus"
                  severity="success"
                  @click="openCreateDialog"
                  class="w-full md:w-auto"
                />
              </div>

              <ProgressSpinner
                v-if="coursesLoading"
                class="w-full flex justify-content-center mt-4"
                strokeWidth="4"
              />
              <DataTable
                v-else
                :value="filteredCourses"
                paginator
                :rows="10"
                :rowsPerPageOptions="[5, 10, 15, 25, 50]"
                tableStyle="min-width: 50rem"
                scrollable
                scrollHeight="65vh"
                :multiSortMeta="courseSortMeta"
                sortMode="multiple"
                removableSort
              >
                <Column field="name" header="課程名稱" sortable style="width: 35%"></Column>
                <Column field="category" header="分類" sortable style="width: 25%">
                  <template #body="{ data }">
                    <Tag :severity="getCategorySeverity(data.category)" class="text-sm">
                      {{ getCategoryName(data.category) }}
                    </Tag>
                  </template>
                </Column>
                <Column header="操作" style="width: 18%">
                  <template #body="{ data }">
                    <div class="flex gap-2">
                      <Button
                        icon="pi pi-pencil"
                        severity="warning"
                        size="small"
                        @click="openEditDialog(data)"
                        label="編輯"
                      />
                      <Button
                        icon="pi pi-trash"
                        severity="danger"
                        size="small"
                        @click="confirmDeleteCourse(data)"
                        label="刪除"
                      />
                    </div>
                  </template>
                </Column>
              </DataTable>
            </div>
          </TabPanel>

          <TabPanel value="1">
            <div class="p-2 md:p-4">
              <div
                class="flex flex-column md:flex-row justify-content-between align-items-start md:align-items-center mb-4 gap-3"
              >
                <div class="flex flex-column md:flex-row gap-3 w-full md:w-auto">
                  <div class="relative w-full md:w-auto">
                    <i class="pi pi-search search-icon"></i>
                    <InputText
                      v-model="userSearchQuery"
                      placeholder="搜尋使用者"
                      class="w-full pl-6"
                    />
                  </div>
                  <Select
                    v-model="filterUserType"
                    :options="userTypeFilterOptions"
                    optionLabel="name"
                    optionValue="value"
                    placeholder="篩選類型"
                    showClear
                    class="w-full md:w-14rem"
                  />
                </div>
                <Button
                  label="新增使用者"
                  icon="pi pi-plus"
                  severity="success"
                  @click="openCreateUserDialog"
                  class="w-full md:w-auto"
                />
              </div>

              <ProgressSpinner
                v-if="usersLoading"
                class="w-full flex justify-content-center mt-4"
                strokeWidth="4"
              />
              <DataTable
                v-else
                :value="filteredUsers"
                paginator
                :rows="10"
                :rowsPerPageOptions="[5, 10, 15, 25, 50]"
                tableStyle="min-width: 50rem"
                scrollable
                scrollHeight="65vh"
                :multiSortMeta="userSortMeta"
                sortMode="multiple"
                removableSort
              >
                <Column field="name" header="使用者名稱" sortable style="width: 15%"></Column>
                <Column field="email" header="電子郵件" sortable style="width: 20%"></Column>
                <Column field="is_admin" header="管理員權限" sortable style="width: 15%">
                  <template #body="{ data }">
                    <Tag :severity="data.is_admin ? 'success' : 'secondary'" class="text-sm">
                      {{ data.is_admin ? '是' : '否' }}
                    </Tag>
                  </template>
                </Column>
                <Column field="is_local" header="帳號類型" sortable style="width: 15%">
                  <template #body="{ data }">
                    <Tag :severity="data.is_local ? 'info' : 'warning'" class="text-sm">
                      {{ data.is_local ? '本地帳號' : 'OAuth 帳號' }}
                    </Tag>
                  </template>
                </Column>
                <Column field="last_login" header="最近登入" sortable style="width: 15%">
                  <template #body="{ data }">
                    <span v-if="data.last_login" class="text-sm">
                      {{ formatDateTime(data.last_login) }}
                    </span>
                    <span v-else class="text-sm text-500"> 從未登入 </span>
                  </template>
                </Column>
                <Column header="操作" style="width: 20%">
                  <template #body="{ data }">
                    <div class="flex gap-2">
                      <Button
                        icon="pi pi-pencil"
                        severity="warning"
                        size="small"
                        @click="openEditUserDialog(data)"
                        label="編輯"
                      />
                      <Button
                        icon="pi pi-trash"
                        severity="danger"
                        size="small"
                        @click="confirmDeleteUser(data)"
                        label="刪除"
                        :disabled="data.id === currentUserId"
                      />
                    </div>
                  </template>
                </Column>
              </DataTable>
            </div>
          </TabPanel>

          <TabPanel value="2">
            <div class="p-2 md:p-4">
              <div
                class="flex flex-column md:flex-row justify-content-between align-items-start md:align-items-center mb-4 gap-3"
              >
                <div class="flex flex-column md:flex-row gap-3 w-full md:w-auto">
                  <div class="relative w-full md:w-auto">
                    <i class="pi pi-search search-icon"></i>
                    <InputText
                      v-model="notificationSearchQuery"
                      placeholder="搜尋公告"
                      class="w-full pl-6"
                    />
                  </div>
                  <Select
                    v-model="notificationSeverityFilter"
                    :options="notificationSeverityFilterOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="篩選重要程度"
                    showClear
                    class="w-full md:w-14rem"
                  />
                </div>
                <Button
                  label="新增公告"
                  icon="pi pi-plus"
                  severity="success"
                  @click="openNotificationCreateDialog"
                  class="w-full md:w-auto"
                />
              </div>

              <ProgressSpinner
                v-if="notificationsLoading"
                class="w-full flex justify-content-center mt-4"
                strokeWidth="4"
              />
              <DataTable
                v-else
                :value="filteredNotifications"
                paginator
                :rows="10"
                :rowsPerPageOptions="[5, 10, 15, 25, 50]"
                tableStyle="min-width: 50rem"
                scrollable
                scrollHeight="65vh"
                sortMode="multiple"
                :multiSortMeta="notificationSortMeta"
                removableSort
              >
                <Column field="title" header="標題" sortable style="width: 26%"></Column>
                <Column field="severity" header="重要程度" sortable style="width: 12%">
                  <template #body="{ data }">
                    <Tag :severity="getNotificationSeverity(data.severity)">
                      {{ getNotificationSeverityLabel(data.severity) }}
                    </Tag>
                  </template>
                </Column>
                <Column
                  field="is_active"
                  sortField="is_active"
                  header="啟用中"
                  sortable
                  style="width: 12%"
                >
                  <template #body="{ data }">
                    <Tag :severity="data.is_active ? 'success' : 'secondary'">
                      {{ data.is_active ? '啟用中' : '已停用' }}
                    </Tag>
                  </template>
                </Column>
                <Column header="生效中" sortField="effectiveOrder" sortable style="width: 12%">
                  <template #body="{ data }">
                    <Tag :severity="isNotificationEffective(data) ? 'success' : 'secondary'">
                      {{ isNotificationEffective(data) ? '生效中' : '未生效' }}
                    </Tag>
                  </template>
                </Column>
                <Column
                  field="updated_at"
                  sortField="updated_at"
                  header="最近更新"
                  sortable
                  style="width: 18%"
                >
                  <template #body="{ data }">
                    <span class="text-sm text-700">
                      {{ formatNotificationDate(data.updated_at || data.created_at) }}
                    </span>
                  </template>
                </Column>
                <Column header="操作" style="width: 20%">
                  <template #body="{ data }">
                    <div class="flex gap-2">
                      <Button
                        icon="pi pi-pencil"
                        severity="warning"
                        size="small"
                        @click="openNotificationEditDialog(data)"
                        label="編輯"
                      />
                      <Button
                        icon="pi pi-trash"
                        severity="danger"
                        size="small"
                        @click="confirmDeleteNotification(data)"
                        label="刪除"
                      />
                    </div>
                  </template>
                </Column>
              </DataTable>
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>

      <Dialog
        :visible="showCourseDialog"
        @update:visible="showCourseDialog = $event"
        :modal="true"
        :draggable="false"
        :closeOnEscape="false"
        :header="editingCourse ? '編輯課程' : '新增課程'"
        :style="{ width: '450px', maxWidth: '90vw' }"
        :autoFocus="false"
      >
        <div class="flex flex-column gap-4">
          <div class="flex flex-column gap-2">
            <label>課程名稱</label>
            <InputText
              v-model="courseForm.name"
              placeholder="輸入課程名稱"
              class="w-full"
              :class="{ 'p-invalid': courseFormErrors.name }"
            />
            <small v-if="courseFormErrors.name" class="p-error">
              {{ courseFormErrors.name }}
            </small>
          </div>

          <div class="flex flex-column gap-2">
            <label>分類</label>
            <Select
              v-model="courseForm.category"
              :options="categoryOptions"
              optionLabel="name"
              optionValue="value"
              placeholder="選擇分類"
              class="w-full"
              :class="{ 'p-invalid': courseFormErrors.category }"
            />
            <small v-if="courseFormErrors.category" class="p-error">
              {{ courseFormErrors.category }}
            </small>
          </div>
        </div>

        <div class="flex pt-6 justify-end gap-2.5">
          <Button label="取消" icon="pi pi-times" severity="secondary" @click="closeCourseDialog" />
          <Button
            :label="editingCourse ? '更新' : '新增'"
            :icon="editingCourse ? 'pi pi-check' : 'pi pi-plus'"
            severity="success"
            @click="saveCourse"
            :loading="saveLoading"
          />
        </div>
      </Dialog>

      <Dialog
        :visible="showUserDialog"
        @update:visible="showUserDialog = $event"
        :modal="true"
        :draggable="false"
        :closeOnEscape="false"
        :header="editingUser ? '編輯使用者' : '新增使用者'"
        :style="{ width: '450px', maxWidth: '90vw' }"
        :autoFocus="false"
      >
        <div class="flex flex-column gap-4">
          <div class="flex flex-column gap-2">
            <label>使用者名稱</label>
            <InputText
              v-model="userForm.name"
              placeholder="輸入使用者名稱"
              class="w-full"
              :class="{ 'p-invalid': userFormErrors.name }"
            />
            <small v-if="userFormErrors.name" class="p-error">
              {{ userFormErrors.name }}
            </small>
          </div>

          <div class="flex flex-column gap-2">
            <label>電子郵件</label>
            <InputText
              v-model="userForm.email"
              placeholder="輸入電子郵件"
              class="w-full"
              :class="{ 'p-invalid': userFormErrors.email }"
            />
            <small v-if="userFormErrors.email" class="p-error">
              {{ userFormErrors.email }}
            </small>
          </div>

          <div v-if="!editingUser" class="flex flex-column gap-2">
            <label>密碼</label>
            <Password
              v-model="userForm.password"
              placeholder="輸入密碼"
              class="w-full"
              inputClass="w-full"
              :class="{ 'p-invalid': userFormErrors.password }"
              toggleMask
              :feedback="false"
            />
            <small v-if="userFormErrors.password" class="p-error">
              {{ userFormErrors.password }}
            </small>
          </div>

          <div class="flex align-items-center gap-2">
            <Checkbox v-model="userForm.is_admin" :binary="true" />
            <label>管理員權限</label>
          </div>
        </div>

        <div class="flex pt-6 justify-end gap-2.5">
          <Button label="取消" icon="pi pi-times" severity="secondary" @click="closeUserDialog" />
          <Button
            :label="editingUser ? '更新' : '新增'"
            :icon="editingUser ? 'pi pi-check' : 'pi pi-plus'"
            severity="success"
            @click="saveUser"
            :loading="userSaveLoading"
          />
        </div>
      </Dialog>

      <Dialog
        :visible="showNotificationDialog"
        @update:visible="showNotificationDialog = $event"
        :modal="true"
        :draggable="false"
        :closeOnEscape="false"
        :header="editingNotification ? '編輯公告' : '新增公告'"
        :style="{ width: '540px', maxWidth: '92vw' }"
        :autoFocus="false"
      >
        <div class="flex flex-column gap-4">
          <div class="flex flex-column gap-2">
            <label>標題</label>
            <InputText
              v-model="notificationForm.title"
              placeholder="輸入公告標題"
              class="w-full"
              :class="{ 'p-invalid': notificationFormErrors.title }"
            />
            <small v-if="notificationFormErrors.title" class="p-error">
              {{ notificationFormErrors.title }}
            </small>
          </div>

          <div class="flex flex-column md:flex-row gap-3">
            <div class="flex-1 flex flex-column gap-2">
              <label>重要程度</label>
              <Select
                v-model="notificationForm.severity"
                :options="notificationSeverityOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="選擇重要程度"
                class="w-full"
              />
            </div>
            <div class="flex align-items-center gap-2 mt-3 md:mt-5">
              <ToggleSwitch v-model="notificationForm.is_active" />
              <label class="m-0 font-medium">啟用公告</label>
            </div>
          </div>

          <div class="flex flex-column gap-2">
            <label>內容</label>
            <Textarea
              v-model="notificationForm.body"
              rows="6"
              autoResize
              class="w-full"
              placeholder="輸入公告內容"
              :class="{ 'p-invalid': notificationFormErrors.body }"
            />
            <small v-if="notificationFormErrors.body" class="p-error">
              {{ notificationFormErrors.body }}
            </small>
          </div>

          <div class="flex flex-column gap-3">
            <div class="flex flex-column gap-2">
              <label>生效時間 (選填)</label>
              <DatePicker
                v-model="notificationForm.starts_at"
                showTime
                hourFormat="24"
                :showIcon="true"
                placeholder="選擇生效時間"
                class="w-full"
              />
            </div>
            <div class="flex flex-column gap-2">
              <label>結束時間 (選填)</label>
              <DatePicker
                v-model="notificationForm.ends_at"
                showTime
                hourFormat="24"
                :showIcon="true"
                placeholder="選擇結束時間"
                class="w-full"
                :class="{ 'p-invalid': notificationFormErrors.ends_at }"
              />
              <small v-if="notificationFormErrors.ends_at" class="p-error">
                {{ notificationFormErrors.ends_at }}
              </small>
            </div>
          </div>
        </div>

        <div class="flex pt-6 justify-end gap-2.5">
          <Button
            label="取消"
            icon="pi pi-times"
            severity="secondary"
            @click="closeNotificationDialog"
          />
          <Button
            :label="editingNotification ? '更新' : '新增'"
            :icon="editingNotification ? 'pi pi-check' : 'pi pi-plus'"
            severity="success"
            @click="saveNotification"
            :loading="notificationSaveLoading"
          />
        </div>
      </Dialog>
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: 'AdminView',
})

import { ref, computed, watch } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { getCurrentUser } from '../utils/auth'
import { isUnauthorizedError } from '../utils/http'
import { formatRelativeTime } from '../utils/time'
import {
  getCourses,
  createCourse,
  updateCourse,
  deleteCourse,
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  notificationService,
} from '../api'
import { trackEvent, EVENTS } from '../utils/analytics'
import { STORAGE_KEYS, getLocalItem, setLocalItem } from '../utils/storage'

const confirm = useConfirm()
const toast = useToast()

const courses = ref([])
const coursesLoading = ref(false)
const searchQuery = ref('')
const filterCategory = ref(null)

const courseSortMeta = ref([
  { field: 'category', order: 1 },
  { field: 'name', order: 1 },
])

const showCourseDialog = ref(false)
const editingCourse = ref(null)
const saveLoading = ref(false)

const courseForm = ref({
  name: '',
  category: '',
})

const courseFormErrors = ref({})
const users = ref([])
const usersLoading = ref(false)
const userSearchQuery = ref('')
const filterUserType = ref(null)

const userSortMeta = ref([
  { field: 'is_admin', order: -1 },
  { field: 'name', order: 1 },
])

const showUserDialog = ref(false)
const editingUser = ref(null)
const userSaveLoading = ref(false)

const userForm = ref({
  name: '',
  email: '',
  password: '',
  is_admin: false,
})

const userFormErrors = ref({})

const notifications = ref([])
const notificationsLoading = ref(false)
const notificationSearchQuery = ref('')
const notificationSeverityFilter = ref(null)

const notificationSortMeta = ref([
  { field: 'is_active', order: -1 },
  { field: 'effectiveOrder', order: -1 },
  { field: 'updated_at', order: -1 },
])

const notificationSeverityOptions = [
  { label: '一般', value: 'info' },
  { label: '重要', value: 'danger' },
]

const notificationSeverityFilterOptions = notificationSeverityOptions

const showNotificationDialog = ref(false)
const editingNotification = ref(null)
const notificationSaveLoading = ref(false)
const notificationForm = ref({
  title: '',
  body: '',
  severity: 'info',
  is_active: true,
  starts_at: null,
  ends_at: null,
})
const notificationFormErrors = ref({})

const currentUserId = computed(() => getCurrentUser()?.id)

const TAB_STORAGE_KEY = STORAGE_KEYS.local.ADMIN_CURRENT_TAB

const getInitialTab = () => {
  try {
    const savedTab = getLocalItem(TAB_STORAGE_KEY)
    if (savedTab && ['0', '1', '2'].includes(savedTab)) {
      return savedTab
    }
  } catch (e) {
    console.error('Failed to load tab from storage:', e)
  }
  return '0'
}

const currentTab = ref(getInitialTab())

const categoryOptions = [
  { name: '大一課程', value: 'freshman' },
  { name: '大二課程', value: 'sophomore' },
  { name: '大三課程', value: 'junior' },
  { name: '大四課程', value: 'senior' },
  { name: '研究所課程', value: 'graduate' },
  { name: '跨領域課程', value: 'interdisciplinary' },
  { name: '通識課程', value: 'general' },
]

const userTypeFilterOptions = [
  { name: '管理員', value: true },
  { name: '一般使用者', value: false },
]

const getCategoryName = (category) => {
  const categoryMap = {
    freshman: '大一課程',
    sophomore: '大二課程',
    junior: '大三課程',
    senior: '大四課程',
    graduate: '研究所課程',
    interdisciplinary: '跨領域課程',
    general: '通識課程',
  }
  return categoryMap[category] || category
}

const getCategorySeverity = (category) => {
  const severityMap = {
    freshman: 'info',
    sophomore: 'success',
    junior: 'warning',
    senior: 'danger',
    graduate: 'contrast',
    interdisciplinary: 'secondary',
  }
  return severityMap[category] || 'secondary'
}

const getNotificationSeverity = (severity) => {
  const map = {
    info: 'info',
    success: 'success',
    warning: 'warning',
    danger: 'danger',
  }
  return map[severity] || 'secondary'
}

const getNotificationSeverityLabel = (severity) => {
  const map = {
    info: '一般',
    success: '成功',
    warning: '提醒',
    danger: '重要',
  }
  return map[severity] || '未知'
}

const isNotificationEffective = (notification) => {
  if (!notification || !notification.is_active) {
    return false
  }

  const now = new Date()

  if (notification.starts_at) {
    const startsAt = new Date(notification.starts_at)
    if (!Number.isNaN(startsAt.getTime()) && startsAt > now) {
      return false
    }
  }

  if (notification.ends_at) {
    const endsAt = new Date(notification.ends_at)
    if (!Number.isNaN(endsAt.getTime()) && endsAt < now) {
      return false
    }
  }

  return true
}

const formatNotificationDate = (value) => {
  return formatRelativeTime(value)
}

const resetNotificationForm = () => {
  notificationForm.value = {
    title: '',
    body: '',
    severity: 'info',
    is_active: true,
    starts_at: null,
    ends_at: null,
  }
  notificationFormErrors.value = {}
  editingNotification.value = null
}

const toDate = (value) => {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

const filteredCourses = computed(() => {
  let filtered = courses.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter((course) => course.name.toLowerCase().includes(query))
  }

  if (filterCategory.value) {
    filtered = filtered.filter((course) => course.category === filterCategory.value)
  }

  return filtered
})

const filteredUsers = computed(() => {
  let filtered = users.value

  if (userSearchQuery.value) {
    const query = userSearchQuery.value.toLowerCase()
    filtered = filtered.filter(
      (user) => user.name.toLowerCase().includes(query) || user.email.toLowerCase().includes(query)
    )
  }

  if (filterUserType.value !== null) {
    filtered = filtered.filter((user) => user.is_admin === filterUserType.value)
  }

  return filtered
})

const filteredNotifications = computed(() => {
  let filtered = notifications.value

  if (notificationSearchQuery.value) {
    const query = notificationSearchQuery.value.toLowerCase()
    filtered = filtered.filter(
      (notification) =>
        notification.title.toLowerCase().includes(query) ||
        notification.body.toLowerCase().includes(query)
    )
  }

  if (notificationSeverityFilter.value) {
    filtered = filtered.filter(
      (notification) => notification.severity === notificationSeverityFilter.value
    )
  }

  return filtered.map((notification) => {
    const effectiveOrder = isNotificationEffective(notification) ? 1 : 0
    return {
      ...notification,
      effectiveOrder,
    }
  })
})

const loadCourses = async () => {
  coursesLoading.value = true
  try {
    const response = await getCourses()
    courses.value = response.data
  } catch (error) {
    console.error('載入課程失敗:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '錯誤',
      detail: '載入課程失敗',
      life: 3000,
    })
  } finally {
    coursesLoading.value = false
  }
}

const loadUsers = async () => {
  usersLoading.value = true
  try {
    const response = await getUsers()
    users.value = response.data
  } catch (error) {
    console.error('載入使用者失敗:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '錯誤',
      detail: '載入使用者失敗',
      life: 3000,
    })
  } finally {
    usersLoading.value = false
  }
}

const loadNotifications = async () => {
  notificationsLoading.value = true
  try {
    const { data } = await notificationService.getAllAdmin()
    notifications.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('載入公告失敗:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '錯誤',
      detail: '載入公告失敗',
      life: 3000,
    })
  } finally {
    notificationsLoading.value = false
  }
}

const openCreateDialog = () => {
  courseForm.value = {
    name: '',
    category: '',
  }
  courseFormErrors.value = {}
  editingCourse.value = null
  showCourseDialog.value = true
  trackEvent(EVENTS.CREATE_COURSE, { action: 'open-dialog' })
}

const openEditDialog = (course) => {
  courseForm.value = {
    name: course.name,
    category: course.category,
  }
  courseFormErrors.value = {}
  editingCourse.value = course
  showCourseDialog.value = true
  trackEvent(EVENTS.UPDATE_COURSE, { action: 'open-dialog', courseName: course.name })
}

const closeCourseDialog = () => {
  showCourseDialog.value = false
  courseForm.value = {
    name: '',
    category: '',
  }
  courseFormErrors.value = {}
  editingCourse.value = null
}

const validateCourseForm = () => {
  const errors = {}

  if (!courseForm.value.name.trim()) {
    errors.name = '課程名稱是必填欄位'
  }

  if (!courseForm.value.category) {
    errors.category = '分類是必填欄位'
  }

  courseFormErrors.value = errors
  return Object.keys(errors).length === 0
}

const saveCourse = async () => {
  if (!validateCourseForm()) return

  saveLoading.value = true
  try {
    if (editingCourse.value) {
      await updateCourse(editingCourse.value.id, courseForm.value)
      trackEvent(EVENTS.UPDATE_COURSE, {
        action: 'submit',
        courseName: courseForm.value.name,
        category: courseForm.value.category,
      })
      toast.add({
        severity: 'success',
        summary: '成功',
        detail: '課程更新成功',
        life: 3000,
      })
    } else {
      await createCourse(courseForm.value)
      trackEvent(EVENTS.CREATE_COURSE, {
        action: 'submit',
        courseName: courseForm.value.name,
        category: courseForm.value.category,
      })
      toast.add({
        severity: 'success',
        summary: '成功',
        detail: '課程新增成功',
        life: 3000,
      })
    }
    closeCourseDialog()
    await loadCourses()
  } catch (error) {
    console.error('儲存課程失敗:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '錯誤',
      detail: editingCourse.value ? '課程更新失敗' : '課程新增失敗',
      life: 3000,
    })
  } finally {
    saveLoading.value = false
  }
}

const confirmDeleteCourse = (course) => {
  confirm.require({
    message: `確定要刪除課程「${course.name}」嗎？`,
    header: '刪除確認',
    icon: 'pi pi-exclamation-triangle',
    rejectClass: 'p-button-secondary p-button-outlined',
    acceptClass: 'p-button-danger',
    rejectLabel: '取消',
    acceptLabel: '刪除',
    accept: () => deleteCourseAction(course),
  })
}

const deleteCourseAction = async (course) => {
  try {
    await deleteCourse(course.id)
    trackEvent(EVENTS.DELETE_COURSE, {
      courseName: course.name,
      category: course.category,
    })
    toast.add({
      severity: 'success',
      summary: '成功',
      detail: '課程刪除成功',
      life: 3000,
    })
    await loadCourses()
  } catch (error) {
    console.error('刪除課程失敗:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '錯誤',
      detail: '課程刪除失敗',
      life: 3000,
    })
  }
}

const openCreateUserDialog = () => {
  userForm.value = {
    name: '',
    email: '',
    password: '',
    is_admin: false,
  }
  userFormErrors.value = {}
  editingUser.value = null
  showUserDialog.value = true
  trackEvent(EVENTS.CREATE_USER, { action: 'open-dialog' })
}

const openEditUserDialog = (user) => {
  userForm.value = {
    name: user.name,
    email: user.email,
    password: '',
    is_admin: user.is_admin,
  }
  userFormErrors.value = {}
  editingUser.value = user
  showUserDialog.value = true
  trackEvent(EVENTS.UPDATE_USER, { action: 'open-dialog', userName: user.name })
}

const closeUserDialog = () => {
  showUserDialog.value = false
  userForm.value = {
    name: '',
    email: '',
    password: '',
    is_admin: false,
  }
  userFormErrors.value = {}
  editingUser.value = null
}

const validateUserForm = () => {
  const errors = {}

  if (!userForm.value.name.trim()) {
    errors.name = '使用者名稱是必填欄位'
  }

  if (!userForm.value.email.trim()) {
    errors.email = '電子郵件是必填欄位'
  } else if (!/\S+@\S+\.\S+/.test(userForm.value.email)) {
    errors.email = '電子郵件格式不正確'
  }

  if (!editingUser.value && !userForm.value.password.trim()) {
    errors.password = '密碼是必填欄位'
  }

  userFormErrors.value = errors
  return Object.keys(errors).length === 0
}

const saveUser = async () => {
  if (!validateUserForm()) return

  userSaveLoading.value = true
  try {
    if (editingUser.value) {
      const updateData = {
        name: userForm.value.name,
        email: userForm.value.email,
        is_admin: userForm.value.is_admin,
      }
      if (userForm.value.password.trim()) {
        updateData.password = userForm.value.password
      }
      await updateUser(editingUser.value.id, updateData)
      trackEvent(EVENTS.UPDATE_USER, {
        action: 'submit',
        userName: userForm.value.name,
        isAdmin: userForm.value.is_admin,
      })
      toast.add({
        severity: 'success',
        summary: '成功',
        detail: '使用者更新成功',
        life: 3000,
      })
    } else {
      await createUser(userForm.value)
      trackEvent(EVENTS.CREATE_USER, {
        action: 'submit',
        userName: userForm.value.name,
        isAdmin: userForm.value.is_admin,
      })
      toast.add({
        severity: 'success',
        summary: '成功',
        detail: '使用者新增成功',
        life: 3000,
      })
    }
    closeUserDialog()
    await loadUsers()
  } catch (error) {
    console.error('儲存使用者失敗:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '錯誤',
      detail: editingUser.value ? '使用者更新失敗' : '使用者新增失敗',
      life: 3000,
    })
  } finally {
    userSaveLoading.value = false
  }
}

const confirmDeleteUser = (user) => {
  confirm.require({
    message: `確定要刪除使用者「${user.name}」嗎？`,
    header: '刪除確認',
    icon: 'pi pi-exclamation-triangle',
    rejectClass: 'p-button-secondary p-button-outlined',
    acceptClass: 'p-button-danger',
    rejectLabel: '取消',
    acceptLabel: '刪除',
    accept: () => deleteUserAction(user),
  })
}

const deleteUserAction = async (user) => {
  try {
    await deleteUser(user.id)
    trackEvent(EVENTS.DELETE_USER, {
      userName: user.name,
      isAdmin: user.is_admin,
    })
    toast.add({
      severity: 'success',
      summary: '成功',
      detail: '使用者刪除成功',
      life: 3000,
    })
    await loadUsers()
  } catch (error) {
    console.error('刪除使用者失敗:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '錯誤',
      detail: '使用者刪除失敗',
      life: 3000,
    })
  }
}

const openNotificationCreateDialog = () => {
  resetNotificationForm()
  showNotificationDialog.value = true
  trackEvent(EVENTS.CREATE_NOTIFICATION, { action: 'open-dialog' })
}

const openNotificationEditDialog = (notification) => {
  notificationForm.value = {
    title: notification.title,
    body: notification.body,
    severity: notification.severity,
    is_active: notification.is_active,
    starts_at: toDate(notification.starts_at),
    ends_at: toDate(notification.ends_at),
  }
  notificationFormErrors.value = {}
  editingNotification.value = notification
  showNotificationDialog.value = true
  trackEvent(EVENTS.UPDATE_NOTIFICATION, {
    action: 'open-dialog',
    notificationId: notification.id,
  })
}

const closeNotificationDialog = () => {
  showNotificationDialog.value = false
  resetNotificationForm()
}

const validateNotificationForm = () => {
  const errors = {}

  if (!notificationForm.value.title.trim()) {
    errors.title = '公告標題是必填欄位'
  }

  if (!notificationForm.value.body.trim()) {
    errors.body = '公告內容是必填欄位'
  }

  if (notificationForm.value.starts_at && notificationForm.value.ends_at) {
    if (notificationForm.value.ends_at.getTime() < notificationForm.value.starts_at.getTime()) {
      errors.ends_at = '結束時間需晚於生效時間'
    }
  }

  notificationFormErrors.value = errors
  return Object.keys(errors).length === 0
}

const saveNotification = async () => {
  if (!validateNotificationForm()) {
    return
  }

  notificationSaveLoading.value = true
  const payload = {
    title: notificationForm.value.title.trim(),
    body: notificationForm.value.body.trim(),
    severity: notificationForm.value.severity,
    is_active: notificationForm.value.is_active,
    starts_at: notificationForm.value.starts_at
      ? notificationForm.value.starts_at.toISOString()
      : null,
    ends_at: notificationForm.value.ends_at ? notificationForm.value.ends_at.toISOString() : null,
  }

  try {
    if (editingNotification.value) {
      await notificationService.update(editingNotification.value.id, payload)
      trackEvent(EVENTS.UPDATE_NOTIFICATION, {
        action: 'submit',
        notificationId: editingNotification.value.id,
      })
      toast.add({
        severity: 'success',
        summary: '成功',
        detail: '公告更新成功',
        life: 3000,
      })
    } else {
      await notificationService.create(payload)
      trackEvent(EVENTS.CREATE_NOTIFICATION, { action: 'submit' })
      toast.add({
        severity: 'success',
        summary: '成功',
        detail: '公告新增成功',
        life: 3000,
      })
    }
    closeNotificationDialog()
    await loadNotifications()
  } catch (error) {
    console.error('儲存公告失敗:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '錯誤',
      detail: editingNotification.value ? '公告更新失敗' : '公告新增失敗',
      life: 3000,
    })
  } finally {
    notificationSaveLoading.value = false
  }
}

const confirmDeleteNotification = (notification) => {
  confirm.require({
    message: `確定要刪除公告「${notification.title}」嗎？`,
    header: '刪除確認',
    icon: 'pi pi-exclamation-triangle',
    rejectClass: 'p-button-secondary p-button-outlined',
    acceptClass: 'p-button-danger',
    rejectLabel: '取消',
    acceptLabel: '刪除',
    accept: () => deleteNotificationAction(notification),
  })
}

const deleteNotificationAction = async (notification) => {
  try {
    await notificationService.remove(notification.id)
    trackEvent(EVENTS.DELETE_NOTIFICATION, { notificationId: notification.id })
    toast.add({
      severity: 'success',
      summary: '成功',
      detail: '公告刪除成功',
      life: 3000,
    })
    await loadNotifications()
  } catch (error) {
    console.error('刪除公告失敗:', error)
    if (isUnauthorizedError(error)) {
      return
    }
    toast.add({
      severity: 'error',
      summary: '錯誤',
      detail: '公告刪除失敗',
      life: 3000,
    })
  }
}

const formatDateTime = (dateString) => {
  if (!dateString) return '從未登入'
  return formatRelativeTime(dateString)
}

// Persist the current tab in localStorage
const saveTabToStorage = (tabValue) => {
  try {
    setLocalItem(TAB_STORAGE_KEY, tabValue)
  } catch (e) {
    console.error('Failed to save tab to storage:', e)
  }
}

const loadTabData = async (value) => {
  const tab = String(value)

  if (tab === '0') {
    await loadCourses()
    return
  }

  if (tab === '1') {
    await loadUsers()
    return
  }

  if (tab === '2') {
    await loadNotifications()
  }
}

const handleTabChange = (value) => {
  const tabValue = String(value)
  currentTab.value = tabValue
  saveTabToStorage(tabValue)

  const tabNames = {
    0: 'courses',
    1: 'users',
    2: 'notifications',
  }

  trackEvent(EVENTS.SWITCH_TAB, {
    tab: tabNames[tabValue] || tabValue,
  })
}

watch(
  currentTab,
  async (value) => {
    await loadTabData(value)
  },
  { immediate: true }
)
</script>

<style scoped>
.admin-container {
  background: var(--p-tabs-tabpanel-background);
}

.card {
  background-color: var(--bg-primary);
}

:deep(.p-tabs) {
  background: var(--p-tabs-tabpanel-background);
}

:deep(.p-tabview-header) {
  background: var(--bg-primary);
}

:deep(.p-tabview-content) {
  background: var(--bg-primary);
  padding: 0;
}

:deep(.p-datatable) {
  background: var(--bg-primary);
}

:deep(.p-datatable-thead > tr > th) {
  background: var(--bg-primary);
  border-color: var(--border-color);
}

:deep(.p-datatable-tbody > tr > td) {
  background: var(--bg-primary);
  border-color: var(--border-color);
}

:deep(.p-dialog) {
  background: var(--bg-primary);
}

:deep(.p-dialog-header) {
  background: var(--bg-primary);
  border-color: var(--border-color);
}

:deep(.p-dialog-content) {
  background: var(--bg-primary);
}

.search-icon {
  position: absolute;
  left: 1rem;
  top: 50%;
  margin-top: -0.5rem;
}

.relative {
  position: relative;
}

.search-container {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
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
  :deep(.p-dialog .p-password-input) {
    font-size: 0.875rem;
  }

  :deep(.p-dialog .p-checkbox-label) {
    font-size: 0.875rem;
  }

  /* Table adjustments for mobile */
  :deep(.p-datatable) {
    font-size: 0.875rem;
    overflow-x: auto;
  }

  :deep(.p-datatable-table) {
    min-width: 600px;
    width: 100%;
  }

  :deep(.p-datatable .p-datatable-thead > tr > th),
  :deep(.p-datatable .p-datatable-tbody > tr > td) {
    white-space: nowrap;
  }

  :deep(.p-datatable .p-button) {
    white-space: nowrap;
  }

  :deep(.p-paginator) {
    font-size: 0.875rem;
  }
}

/* Desktop table overflow handling */
@media (min-width: 769px) {
  :deep(.p-datatable) {
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

  /* Ensure buttons don't wrap on desktop */
  :deep(.p-datatable .flex.gap-2) {
    flex-wrap: nowrap;
    gap: 0.5rem;
  }
}
</style>
