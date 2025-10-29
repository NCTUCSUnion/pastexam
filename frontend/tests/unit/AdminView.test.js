import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import AdminView from '@/views/Admin.vue'

const sampleCourses = [
  { id: 1, name: 'Algorithms', category: 'junior' },
  { id: 2, name: 'Calculus', category: 'freshman' },
]

const sampleUsers = [
  { id: 1, name: 'Alice', email: 'alice@example.com', is_admin: true, is_local: true },
  { id: 2, name: 'Bob', email: 'bob@example.com', is_admin: false, is_local: false },
]

const now = new Date()
const sampleNotifications = [
  {
    id: 1,
    title: '維護通知',
    body: '系統維護中',
    severity: 'info',
    is_active: true,
    starts_at: new Date(now.getTime() - 3600_000).toISOString(),
    ends_at: new Date(now.getTime() + 3600_000).toISOString(),
    created_at: now.toISOString(),
  },
  {
    id: 2,
    title: '過期公告',
    body: '過期',
    severity: 'danger',
    is_active: true,
    starts_at: new Date(now.getTime() - 7200_000).toISOString(),
    ends_at: new Date(now.getTime() - 3600_000).toISOString(),
    created_at: new Date(now.getTime() - 86400_000).toISOString(),
  },
]

const getCoursesMock = vi.hoisted(() => vi.fn())
const createCourseMock = vi.hoisted(() => vi.fn())
const updateCourseMock = vi.hoisted(() => vi.fn())
const deleteCourseMock = vi.hoisted(() => vi.fn())

const getUsersMock = vi.hoisted(() => vi.fn())
const createUserMock = vi.hoisted(() => vi.fn())
const updateUserMock = vi.hoisted(() => vi.fn())
const deleteUserMock = vi.hoisted(() => vi.fn())

const notificationGetAllMock = vi.hoisted(() => vi.fn())
const notificationCreateMock = vi.hoisted(() => vi.fn())
const notificationUpdateMock = vi.hoisted(() => vi.fn())
const notificationRemoveMock = vi.hoisted(() => vi.fn())

const trackEventMock = vi.hoisted(() => vi.fn())
const refreshActiveMock = vi.hoisted(() => vi.fn())
const isUnauthorizedErrorMock = vi.hoisted(() => vi.fn(() => false))

const confirmRequireMock = vi.hoisted(() => vi.fn((options) => options.accept && options.accept()))
const toastAddMock = vi.hoisted(() => vi.fn())

vi.mock('primevue/useconfirm', () => ({
  useConfirm: () => ({
    require: confirmRequireMock,
  }),
}))

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({
    add: toastAddMock,
  }),
}))

vi.mock('@/utils/auth', () => ({
  getCurrentUser: () => ({ id: 99 }),
}))

vi.mock('@/utils/http', () => ({
  isUnauthorizedError: isUnauthorizedErrorMock,
}))

vi.mock('@/utils/analytics', () => ({
  trackEvent: trackEventMock,
  EVENTS: {
    CREATE_COURSE: 'create-course',
    UPDATE_COURSE: 'update-course',
    DELETE_COURSE: 'delete-course',
    CREATE_USER: 'create-user',
    UPDATE_USER: 'update-user',
    DELETE_USER: 'delete-user',
    CREATE_NOTIFICATION: 'create-notification',
    UPDATE_NOTIFICATION: 'update-notification',
    DELETE_NOTIFICATION: 'delete-notification',
  },
}))

vi.mock('@/utils/useNotifications', () => ({
  useNotifications: () => ({
    refreshActive: refreshActiveMock,
  }),
}))

vi.mock('@/api', () => ({
  getCourses: getCoursesMock,
  createCourse: createCourseMock,
  updateCourse: updateCourseMock,
  deleteCourse: deleteCourseMock,
  getUsers: getUsersMock,
  createUser: createUserMock,
  updateUser: updateUserMock,
  deleteUser: deleteUserMock,
  notificationService: {
    getAllAdmin: notificationGetAllMock,
    create: notificationCreateMock,
    update: notificationUpdateMock,
    remove: notificationRemoveMock,
  },
}))

function createWrapper() {
  return shallowMount(AdminView)
}

describe('AdminView', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(now)
    getCoursesMock.mockResolvedValue({ data: sampleCourses })
    createCourseMock.mockResolvedValue()
    updateCourseMock.mockResolvedValue()
    deleteCourseMock.mockResolvedValue()

    getUsersMock.mockResolvedValue({ data: sampleUsers })
    createUserMock.mockResolvedValue()
    updateUserMock.mockResolvedValue()
    deleteUserMock.mockResolvedValue()

    notificationGetAllMock.mockResolvedValue({ data: sampleNotifications })
    notificationCreateMock.mockResolvedValue()
    notificationUpdateMock.mockResolvedValue()
    notificationRemoveMock.mockResolvedValue()

    refreshActiveMock.mockResolvedValue()
    trackEventMock.mockReset()
    toastAddMock.mockReset()
    confirmRequireMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValue(false)

    localStorage.clear()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.resetModules()
  })

  it('loads data and handles admin actions', async () => {
    const wrapper = createWrapper()

    await flushPromises()

    expect(getCoursesMock).toHaveBeenCalled()
    expect(getUsersMock).toHaveBeenCalled()
    expect(wrapper.vm.filteredCourses.length).toBe(2)
    expect(wrapper.vm.filteredUsers.length).toBe(2)

    wrapper.vm.openCreateDialog()
    wrapper.vm.courseForm.name = 'Discrete Math'
    wrapper.vm.courseForm.category = 'freshman'
    await wrapper.vm.saveCourse()

    expect(createCourseMock).toHaveBeenCalledWith({
      name: 'Discrete Math',
      category: 'freshman',
    })
    expect(trackEventMock).toHaveBeenCalledWith('create-course', expect.any(Object))

    wrapper.vm.openEditDialog(sampleCourses[0])
    wrapper.vm.courseForm.name = 'Algorithms Advanced'
    await wrapper.vm.saveCourse()
    expect(updateCourseMock).toHaveBeenCalled()

    wrapper.vm.confirmDeleteCourse(sampleCourses[0])
    expect(deleteCourseMock).toHaveBeenCalledWith(sampleCourses[0].id)

    wrapper.vm.openCreateUserDialog()
    wrapper.vm.userForm.name = 'Charlie'
    wrapper.vm.userForm.email = 'charlie@example.com'
    wrapper.vm.userForm.password = 'secret'
    wrapper.vm.userForm.is_admin = true
    await wrapper.vm.saveUser()
    expect(createUserMock).toHaveBeenCalledWith({
      name: 'Charlie',
      email: 'charlie@example.com',
      password: 'secret',
      is_admin: true,
    })

    wrapper.vm.openEditUserDialog(sampleUsers[1])
    wrapper.vm.userForm.name = 'Bob Updated'
    wrapper.vm.userForm.password = ''
    await wrapper.vm.saveUser()
    expect(updateUserMock).toHaveBeenCalledWith(sampleUsers[1].id, {
      name: 'Bob Updated',
      email: sampleUsers[1].email,
      is_admin: sampleUsers[1].is_admin,
    })

    wrapper.vm.confirmDeleteUser(sampleUsers[1])
    expect(deleteUserMock).toHaveBeenCalledWith(sampleUsers[1].id)

    wrapper.vm.openNotificationCreateDialog()
    wrapper.vm.notificationForm.title = '新公告'
    wrapper.vm.notificationForm.body = '內容'
    wrapper.vm.notificationForm.starts_at = new Date(now.getTime() - 1000)
    wrapper.vm.notificationForm.ends_at = new Date(now.getTime() + 1000)
    await wrapper.vm.saveNotification()
    expect(notificationCreateMock).toHaveBeenCalled()
    expect(wrapper.vm.notifications.length).toBe(2)
    expect(wrapper.vm.filteredNotifications.length).toBe(2)

    wrapper.vm.openNotificationEditDialog(sampleNotifications[0])
    wrapper.vm.notificationForm.body = '更新內容'
    await wrapper.vm.saveNotification()
    expect(notificationUpdateMock).toHaveBeenCalledWith(
      sampleNotifications[0].id,
      expect.objectContaining({ body: '更新內容' })
    )

    wrapper.vm.confirmDeleteNotification(sampleNotifications[0])
    expect(notificationRemoveMock).toHaveBeenCalledWith(sampleNotifications[0].id)
    expect(notificationGetAllMock).toHaveBeenCalled()
    expect(refreshActiveMock).toHaveBeenCalled()

    expect(wrapper.vm.getCategoryName('freshman')).toBe('大一課程')
    expect(wrapper.vm.getCategorySeverity('graduate')).toBe('contrast')
    expect(wrapper.vm.getNotificationSeverity('danger')).toBe('danger')
    expect(wrapper.vm.getNotificationSeverityLabel('info')).toBe('一般')
    expect(wrapper.vm.isNotificationEffective(sampleNotifications[0])).toBe(true)
    expect(wrapper.vm.isNotificationEffective(sampleNotifications[1])).toBe(false)
    expect(wrapper.vm.formatNotificationDate('invalid')).toBe('invalid')
    expect(wrapper.vm.formatNotificationDate(now.toISOString())).not.toBe('—')

    wrapper.unmount()
  })
})
