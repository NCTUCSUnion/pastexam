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
    SWITCH_TAB: 'switch-tab',
  },
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

let consoleErrorSpy

describe('AdminView', () => {
  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
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

    trackEventMock.mockReset()
    toastAddMock.mockReset()
    confirmRequireMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValue(false)

    localStorage.clear()
  })

  afterEach(() => {
    consoleErrorSpy?.mockRestore()
    vi.useRealTimers()
    vi.resetModules()
  })

  it('loads data and handles admin actions', async () => {
    const wrapper = createWrapper()

    await flushPromises()

    expect(getCoursesMock).toHaveBeenCalled()
    expect(getUsersMock).not.toHaveBeenCalled()
    expect(wrapper.vm.filteredCourses.length).toBe(2)

    await wrapper.vm.handleTabChange('1')
    await flushPromises()

    expect(getUsersMock).toHaveBeenCalled()
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

  it('validates forms and handles failure branches', async () => {
    const wrapper = createWrapper()

    await flushPromises()

    createCourseMock.mockClear()
    createUserMock.mockClear()
    notificationCreateMock.mockClear()
    toastAddMock.mockClear()

    wrapper.vm.openCreateDialog()
    wrapper.vm.courseForm.name = '   '
    wrapper.vm.courseForm.category = ''
    await wrapper.vm.saveCourse()
    expect(createCourseMock).not.toHaveBeenCalled()
    expect(wrapper.vm.courseFormErrors).toMatchObject({
      name: '課程名稱是必填欄位',
      category: '分類是必填欄位',
    })

    wrapper.vm.openCreateUserDialog()
    wrapper.vm.userForm.name = ' '
    wrapper.vm.userForm.email = 'invalid-email'
    wrapper.vm.userForm.password = ''
    await wrapper.vm.saveUser()
    expect(createUserMock).not.toHaveBeenCalled()
    expect(wrapper.vm.userFormErrors).toMatchObject({
      name: '使用者名稱是必填欄位',
      email: '電子郵件格式不正確',
      password: '密碼是必填欄位',
    })

    wrapper.vm.openNotificationCreateDialog()
    wrapper.vm.notificationForm.title = ' '
    wrapper.vm.notificationForm.body = ''
    wrapper.vm.notificationForm.starts_at = new Date(now.getTime() + 10_000)
    wrapper.vm.notificationForm.ends_at = new Date(now.getTime() - 10_000)
    await wrapper.vm.saveNotification()
    expect(notificationCreateMock).not.toHaveBeenCalled()
    expect(wrapper.vm.notificationFormErrors).toMatchObject({
      title: '公告標題是必填欄位',
      body: '公告內容是必填欄位',
      ends_at: '結束時間需晚於生效時間',
    })

    toastAddMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    getCoursesMock.mockRejectedValueOnce(new Error('unauthorized'))
    await wrapper.vm.loadCourses()
    expect(toastAddMock).not.toHaveBeenCalled()

    toastAddMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    getUsersMock.mockRejectedValueOnce(new Error('boom'))
    await wrapper.vm.loadUsers()
    expect(toastAddMock).toHaveBeenCalledWith(expect.objectContaining({ detail: '載入使用者失敗' }))

    toastAddMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    notificationGetAllMock.mockRejectedValueOnce(new Error('fail'))
    await wrapper.vm.loadNotifications()
    expect(toastAddMock).toHaveBeenCalledWith(expect.objectContaining({ detail: '載入公告失敗' }))

    expect(wrapper.vm.formatNotificationDate(null)).toBe('—')
    expect(wrapper.vm.formatDateTime(null)).toBe('從未登入')
    expect(wrapper.vm.formatDateTime(new Date(now.getTime() - 30_000).toISOString())).toBe('剛剛')
    expect(wrapper.vm.formatDateTime(new Date(now.getTime() - 10 * 60_000).toISOString())).toBe(
      '10 分鐘前'
    )
    expect(wrapper.vm.formatDateTime(new Date(now.getTime() - 2 * 60 * 60_000).toISOString())).toBe(
      '2 小時前'
    )
    expect(
      wrapper.vm.formatDateTime(new Date(now.getTime() - 24 * 60 * 60_000).toISOString())
    ).toBe('昨天')
    expect(
      wrapper.vm.formatDateTime(new Date(now.getTime() - 3 * 24 * 60 * 60_000).toISOString())
    ).toBe('3 天前')
    expect(
      wrapper.vm.formatDateTime(new Date(now.getTime() - 10 * 24 * 60 * 60_000).toISOString())
    ).toMatch(/\d{4}\//)

    notificationGetAllMock.mockReset()
    notificationGetAllMock.mockResolvedValue({ data: sampleNotifications })
    trackEventMock.mockClear()

    wrapper.vm.notifications = []
    await wrapper.vm.handleTabChange('2')

    expect(localStorage.getItem('admin-current-tab')).toBe('2')
    expect(trackEventMock).toHaveBeenCalledWith(
      'switch-tab',
      expect.objectContaining({ tab: 'notifications' })
    )

    await flushPromises()
    expect(notificationGetAllMock).toHaveBeenCalledTimes(1)

    wrapper.unmount()
  })

  it('handles create and delete error branches with unauthorized checks', async () => {
    const wrapper = createWrapper()

    await flushPromises()

    toastAddMock.mockClear()

    wrapper.vm.openCreateDialog()
    wrapper.vm.courseForm.name = 'Linear Algebra'
    wrapper.vm.courseForm.category = 'freshman'
    createCourseMock.mockRejectedValueOnce(new Error('create-fail'))
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    await wrapper.vm.saveCourse()
    expect(toastAddMock).toHaveBeenCalledWith(expect.objectContaining({ detail: '課程新增失敗' }))

    toastAddMock.mockClear()
    createCourseMock.mockRejectedValueOnce(new Error('unauthorized'))
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    await wrapper.vm.saveCourse()
    expect(toastAddMock).not.toHaveBeenCalled()

    wrapper.vm.openCreateUserDialog()
    wrapper.vm.userForm.name = 'Dave'
    wrapper.vm.userForm.email = 'dave@example.com'
    wrapper.vm.userForm.password = 'secret'
    createUserMock.mockRejectedValueOnce(new Error('user-fail'))
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    await wrapper.vm.saveUser()
    expect(toastAddMock).toHaveBeenCalledWith(expect.objectContaining({ detail: '使用者新增失敗' }))

    toastAddMock.mockClear()
    createUserMock.mockRejectedValueOnce(new Error('unauthorized'))
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    await wrapper.vm.saveUser()
    expect(toastAddMock).not.toHaveBeenCalled()

    wrapper.vm.openNotificationCreateDialog()
    wrapper.vm.notificationForm.title = 'System Notice'
    wrapper.vm.notificationForm.body = 'Content'
    notificationCreateMock.mockRejectedValueOnce(new Error('notify-fail'))
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    await wrapper.vm.saveNotification()
    expect(toastAddMock).toHaveBeenCalledWith(expect.objectContaining({ detail: '公告新增失敗' }))

    toastAddMock.mockClear()
    notificationCreateMock.mockRejectedValueOnce(new Error('unauthorized'))
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    wrapper.vm.notificationForm.title = 'System Notice'
    wrapper.vm.notificationForm.body = 'Content'
    await wrapper.vm.saveNotification()
    expect(toastAddMock).not.toHaveBeenCalled()

    toastAddMock.mockClear()
    deleteCourseMock.mockRejectedValueOnce(new Error('delete-fail'))
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    await wrapper.vm.deleteCourseAction({ id: 3, name: 'Course', category: 'junior' })
    expect(toastAddMock).toHaveBeenCalledWith(expect.objectContaining({ detail: '課程刪除失敗' }))

    trackEventMock.mockClear()
    localStorage.clear()
    await wrapper.vm.handleTabChange('1')
    expect(localStorage.getItem('admin-current-tab')).toBe('1')
    expect(trackEventMock).toHaveBeenCalledWith('switch-tab', { tab: 'users' })

    wrapper.unmount()
  })

  it('covers filtering utilities and helper branches', async () => {
    const wrapper = createWrapper()

    await flushPromises()

    await wrapper.vm.loadNotifications()
    await flushPromises()

    await wrapper.vm.handleTabChange('1')
    await flushPromises()

    wrapper.vm.searchQuery = 'alg'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.filteredCourses).toEqual([sampleCourses[0]])

    wrapper.vm.searchQuery = ''
    await wrapper.vm.$nextTick()
    wrapper.vm.filterCategory = 'freshman'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.filteredCourses).toEqual([sampleCourses[1]])

    wrapper.vm.userSearchQuery = 'bob'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.filteredUsers).toEqual([sampleUsers[1]])

    wrapper.vm.userSearchQuery = ''
    await wrapper.vm.$nextTick()
    wrapper.vm.filterUserType = true
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.filteredUsers).toEqual([sampleUsers[0]])

    wrapper.vm.notificationSearchQuery = '維護'
    wrapper.vm.notificationSeverityFilter = 'info'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.filteredNotifications).toHaveLength(1)

    wrapper.vm.notificationSearchQuery = ''
    wrapper.vm.notificationSeverityFilter = 'danger'
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.filteredNotifications).toHaveLength(1)

    const originalSetItem = localStorage.setItem
    localStorage.setItem = vi.fn(() => {
      throw new Error('storage disabled')
    })
    expect(() => wrapper.vm.saveTabToStorage('0')).not.toThrow()
    localStorage.setItem = originalSetItem

    expect(wrapper.vm.toDate('invalid')).toBeNull()
    expect(wrapper.vm.toDate(now.toISOString())).toBeInstanceOf(Date)

    updateUserMock.mockClear()
    wrapper.vm.openEditUserDialog(sampleUsers[0])
    wrapper.vm.userForm.password = 'new-secret'
    await wrapper.vm.saveUser()
    expect(updateUserMock).toHaveBeenLastCalledWith(
      sampleUsers[0].id,
      expect.objectContaining({ password: 'new-secret' })
    )

    toastAddMock.mockClear()
    deleteUserMock.mockRejectedValueOnce(new Error('forbidden'))
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    await wrapper.vm.deleteUserAction(sampleUsers[0])
    expect(toastAddMock).not.toHaveBeenCalled()

    toastAddMock.mockClear()
    notificationRemoveMock.mockRejectedValueOnce(new Error('unauthorized'))
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    await wrapper.vm.deleteNotificationAction(sampleNotifications[0])
    expect(toastAddMock).not.toHaveBeenCalled()

    toastAddMock.mockClear()
    wrapper.vm.closeCourseDialog()
    wrapper.vm.closeUserDialog()
    wrapper.vm.closeNotificationDialog()
    expect(wrapper.vm.showCourseDialog).toBe(false)
    expect(wrapper.vm.showUserDialog).toBe(false)
    expect(wrapper.vm.showNotificationDialog).toBe(false)

    wrapper.unmount()
  })
})
