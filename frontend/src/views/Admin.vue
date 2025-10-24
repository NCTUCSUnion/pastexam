<template>
  <div class="h-full px-2 md:px-4 admin-container">
    <div class="card h-full flex flex-col">
      <Tabs :value="currentTab" class="flex-1" @update:value="handleTabChange">
        <TabList>
          <Tab value="0">課程管理</Tab>
          <Tab value="1">使用者管理</Tab>
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
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: 'AdminView',
})

import { ref, computed, onMounted } from 'vue'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import { getCurrentUser } from '../utils/auth'
import {
  getCourses,
  createCourse,
  updateCourse,
  deleteCourse,
  getUsers,
  createUser,
  updateUser,
  deleteUser,
} from '../api'
import { trackEvent, EVENTS } from '../utils/analytics'

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

const currentUserId = computed(() => getCurrentUser()?.id)

const TAB_STORAGE_KEY = 'adminCurrentTab'

const getInitialTab = () => {
  try {
    const savedTab = localStorage.getItem(TAB_STORAGE_KEY)
    if (savedTab && ['0', '1'].includes(savedTab)) {
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

const loadCourses = async () => {
  coursesLoading.value = true
  try {
    const response = await getCourses()
    courses.value = response.data
  } catch (error) {
    console.error('載入課程失敗:', error)
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
    toast.add({
      severity: 'error',
      summary: '錯誤',
      detail: '使用者刪除失敗',
      life: 3000,
    })
  }
}

const formatDateTime = (dateString) => {
  if (!dateString) return '從未登入'

  const date = new Date(dateString)
  const now = new Date()
  const diffInMs = now - date
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60))
  const diffInDays = Math.floor(diffInHours / 24)

  if (diffInDays === 0) {
    if (diffInHours === 0) {
      const diffInMinutes = Math.floor(diffInMs / (1000 * 60))
      if (diffInMinutes < 1) {
        return '剛剛'
      } else if (diffInMinutes < 60) {
        return `${diffInMinutes} 分鐘前`
      }
    }
    return `${diffInHours} 小時前`
  } else if (diffInDays === 1) {
    return '昨天'
  } else if (diffInDays < 7) {
    return `${diffInDays} 天前`
  } else {
    return date.toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }
}

// Persist the current tab in localStorage
const saveTabToStorage = (tabValue) => {
  try {
    localStorage.setItem(TAB_STORAGE_KEY, tabValue)
  } catch (e) {
    console.error('Failed to save tab to storage:', e)
  }
}

const handleTabChange = (value) => {
  currentTab.value = value
  saveTabToStorage(value)

  const tabNames = {
    0: 'courses',
    1: 'users',
  }

  trackEvent(EVENTS.SWITCH_TAB, {
    tab: tabNames[value] || value,
  })
}

onMounted(() => {
  loadCourses()
  loadUsers()
})
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

:deep(.p-accordionheader),
:deep(.p-panelmenu-header-link),
:deep(.p-panelmenu-content),
:deep(.p-button),
:deep(.p-button-outlined),
:deep(.p-inputtext),
:deep(.p-dropdown),
:deep(.p-select),
:deep(.p-checkbox),
:deep(.p-checkbox-box),
:deep(.p-checkbox-icon),
:deep(.p-tag),
:deep(.p-toolbar),
:deep(.p-datatable),
:deep(.p-datatable-thead > tr > th),
:deep(.p-datatable-tbody > *),
:deep(.p-dialog),
:deep(.p-dialog-header),
:deep(.p-dialog-content),
:deep(.p-dialog-footer) {
  transition: none !important;
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
