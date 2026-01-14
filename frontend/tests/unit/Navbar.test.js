import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { shallowMount } from '@vue/test-utils'
import Navbar from '@/components/Navbar.vue'

const localLoginMock = vi.hoisted(() => vi.fn())
const logoutMock = vi.hoisted(() => vi.fn())
const loginRedirectMock = vi.hoisted(() => vi.fn())
const trackEventMock = vi.hoisted(() => vi.fn())
const setTokenMock = vi.hoisted(() => vi.fn())
const getCurrentUserMock = vi.hoisted(() => vi.fn())
const isAuthenticatedMock = vi.hoisted(() => vi.fn())
const toastAddMock = vi.hoisted(() => vi.fn())
const courseServiceListMock = vi.hoisted(() => vi.fn())
const isUnauthorizedErrorMock = vi.hoisted(() => vi.fn(() => false))
const notificationStoreMock = vi.hoisted(() => ({
  state: {
    modalVisible: false,
    centerVisible: false,
    all: [],
    active: [],
    initialized: false,
    loadingAll: false,
  },
  initNotifications: vi.fn(),
  openCenter: vi.fn(),
  markNotificationAsSeen: vi.fn(),
  latestUnseenNotification: null,
}))

let consoleErrorSpy

vi.mock('@/api', () => ({
  authService: {
    localLogin: localLoginMock,
    logout: logoutMock,
    login: loginRedirectMock,
  },
  courseService: {
    listCourses: courseServiceListMock,
  },
}))

vi.mock('@/utils/auth.js', () => ({
  getCurrentUser: getCurrentUserMock,
  isAuthenticated: isAuthenticatedMock,
  setToken: setTokenMock,
}))

vi.mock('@/utils/useTheme', () => {
  const themeState = { value: false }
  return {
    useTheme: () => ({
      isDarkTheme: themeState,
      toggleTheme: vi.fn(),
    }),
  }
})

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({
    add: toastAddMock,
  }),
}))

vi.mock('@/utils/analytics', () => ({
  trackEvent: trackEventMock,
  EVENTS: {
    TOGGLE_THEME: 'toggle-theme',
    LOGIN: 'login',
    LOGIN_LOCAL: 'login-local',
    LOGOUT: 'logout',
    NAVIGATE_ARCHIVE: 'navigate-archive',
    NAVIGATE_ADMIN: 'navigate-admin',
    OPEN_NOTIFICATION_CENTER: 'open-notification-center',
    OPEN_ISSUE_REPORT: 'open-issue-report',
    SUBMIT_ISSUE_REPORT: 'submit-issue-report',
    OPEN_MORE_ACTIONS_MENU: 'open-more-actions-menu',
  },
}))

vi.mock('@/utils/useNotifications', () => ({
  useNotifications: () => notificationStoreMock,
}))

vi.mock('@/utils/http', () => ({
  isUnauthorizedError: isUnauthorizedErrorMock,
}))

vi.mock('@/components/GenerateAIExamModal.vue', () => ({
  default: {
    name: 'GenerateAIExamModal',
    template: '<div class="ai-exam-modal"></div>',
  },
}))
vi.mock('@/components/NotificationModal.vue', () => ({
  default: {
    name: 'NotificationModal',
    props: ['visible', 'notification'],
    template: '<div class="notification-modal"></div>',
  },
}))
vi.mock('@/components/NotificationCenterModal.vue', () => ({
  default: {
    name: 'NotificationCenterModal',
    props: ['visible', 'notifications'],
    template: '<div class="notification-center"></div>',
  },
}))

describe('Navbar methods', () => {
  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    trackEventMock.mockReset()
    localLoginMock.mockReset()
    logoutMock.mockReset()
    loginRedirectMock.mockReset()
    toastAddMock.mockReset()
    notificationStoreMock.state.modalVisible = false
    notificationStoreMock.state.centerVisible = false
    notificationStoreMock.state.all = []
    notificationStoreMock.state.active = []
    notificationStoreMock.state.initialized = false
    notificationStoreMock.state.loadingAll = false
    notificationStoreMock.initNotifications.mockReset()
    notificationStoreMock.openCenter.mockReset()
    notificationStoreMock.markNotificationAsSeen.mockReset()
    notificationStoreMock.latestUnseenNotification = null
    getCurrentUserMock.mockReset()
    isAuthenticatedMock.mockReset()
    setTokenMock.mockReset()
    courseServiceListMock.mockReset()
    isUnauthorizedErrorMock.mockReturnValue(false)
    sessionStorage.clear()
    localStorage.clear()
  })

  afterEach(() => {
    if (consoleErrorSpy) {
      consoleErrorSpy.mockRestore()
    }
  })

  it('toggles theme and tracks event', () => {
    const ctx = {
      isDarkTheme: true,
      toggleTheme: vi.fn(),
      toast: { add: toastAddMock },
      notificationStore: notificationStoreMock,
    }
    Navbar.methods.handleToggleTheme.call(ctx)
    expect(trackEventMock).toHaveBeenCalledWith('toggle-theme', expect.any(Object))
    expect(ctx.toggleTheme).toHaveBeenCalled()
  })

  it('handles local login success and failure', async () => {
    const routerPush = vi.fn()
    const ctx = {
      username: 'user',
      password: 'pass',
      toast: { add: toastAddMock },
      router: { push: routerPush },
      loginVisible: true,
      loading: false,
      checkAuthentication: vi.fn(),
    }

    localLoginMock.mockResolvedValue({ access_token: 'token123' })
    await Navbar.methods.handleLocalLogin.call(ctx)
    expect(localLoginMock).toHaveBeenCalledWith('user', 'pass')
    expect(setTokenMock).toHaveBeenCalledWith('token123')
    expect(routerPush).toHaveBeenCalledWith('/archive')
    expect(trackEventMock).toHaveBeenCalledWith('login-local', { success: true })

    ctx.username = ''
    ctx.password = ''
    await Navbar.methods.handleLocalLogin.call(ctx)
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '錯誤' })
    )
  })

  it('handles local login rejection with error toast', async () => {
    const routerPush = vi.fn()
    const ctx = {
      username: 'user',
      password: 'pass',
      toast: { add: toastAddMock },
      router: { push: routerPush },
      loginVisible: true,
      loading: false,
      checkAuthentication: vi.fn(),
    }

    toastAddMock.mockClear()
    localLoginMock.mockRejectedValueOnce(new Error('fail'))

    await Navbar.methods.handleLocalLogin.call(ctx)

    expect(trackEventMock).toHaveBeenCalledWith('login-local', { success: false })
    expect(toastAddMock).toHaveBeenCalledWith(expect.objectContaining({ summary: '登入失敗' }))
    expect(ctx.loading).toBe(false)
  })

  it('opens login dialog and tracks dialog event', () => {
    const ctx = {
      loginVisible: false,
    }

    Navbar.methods.openLoginDialog.call(ctx)

    expect(ctx.loginVisible).toBe(true)
    expect(trackEventMock).toHaveBeenCalledWith('login', { type: 'dialog-open' })
  })

  it('handles logout flow and cleans storage', async () => {
    const routerPush = vi.fn()
    const ctx = {
      toast: { add: toastAddMock },
      notificationStore: notificationStoreMock,
      $router: { push: routerPush },
      isAuthenticated: true,
      userData: { name: 'Alice' },
    }
    sessionStorage.setItem('auth-token', 'abc')
    localStorage.setItem('selected-subject', 'xyz')

    await Navbar.methods.handleLogout.call(ctx)
    expect(logoutMock).toHaveBeenCalled()
    expect(trackEventMock).toHaveBeenCalledWith('logout', { success: true })
    expect(sessionStorage.getItem('auth-token')).toBeNull()
    expect(localStorage.getItem('selected-subject')).toBeNull()
    expect(routerPush).toHaveBeenCalledWith('/')
  })

  it('tracks logout failure when API errors', async () => {
    const routerPush = vi.fn()
    const ctx = {
      toast: { add: toastAddMock },
      notificationStore: notificationStoreMock,
      $router: { push: routerPush },
      isAuthenticated: true,
      userData: { name: 'Alice' },
    }

    logoutMock.mockRejectedValueOnce(new Error('fail'))

    await Navbar.methods.handleLogout.call(ctx)

    expect(trackEventMock).toHaveBeenCalledWith('logout', { success: false })
    expect(routerPush).toHaveBeenCalledWith('/')
    expect(sessionStorage.getItem('auth-token')).toBeNull()
  })

  it('opens notification center with auth guard', async () => {
    const ctx = {
      toast: { add: toastAddMock },
      notificationStore: notificationStoreMock,
      isAuthenticated: false,
    }
    await Navbar.methods.openNotificationCenter.call(ctx, 'navbar')
    expect(toastAddMock).toHaveBeenCalled()

    ctx.isAuthenticated = true
    await Navbar.methods.openNotificationCenter.call(ctx, 'navbar')
    expect(notificationStoreMock.openCenter).toHaveBeenCalled()
    expect(trackEventMock).toHaveBeenCalledWith('open-notification-center', { from: 'navbar' })
  })

  it('handles notification modal visibility helpers', () => {
    const ctx = {
      notificationStore: notificationStoreMock,
    }
    Navbar.methods.handleNotificationModalVisible.call(ctx, true)
    expect(notificationStoreMock.state.modalVisible).toBe(true)

    Navbar.methods.handleNotificationDismiss.call(ctx, { id: 1 })
    expect(notificationStoreMock.markNotificationAsSeen).toHaveBeenCalledWith({ id: 1 })

    Navbar.methods.handleNotificationCenterVisible.call(ctx, true)
    expect(notificationStoreMock.state.centerVisible).toBe(true)

    Navbar.methods.handleNotificationDetailSeen.call(ctx, { id: 2 })
    expect(notificationStoreMock.markNotificationAsSeen).toHaveBeenCalledWith({ id: 2 })
  })

  it('toggles more actions menu and invokes menu actions', () => {
    const toggleSpy = vi.fn()
    const hideSpy = vi.fn()
    const actionSpy = vi.fn()
    const ctx = {
      moreActions: [actionSpy],
      $refs: {
        moreActionsMenu: {
          toggle: toggleSpy,
          hide: hideSpy,
        },
      },
      isDesktopView: true,
    }
    Navbar.methods.toggleMoreActions.call(ctx, {})
    expect(toggleSpy).toHaveBeenCalled()
    expect(trackEventMock).toHaveBeenCalledWith('open-more-actions-menu', {
      items: 1,
      viewport: 'desktop',
    })

    Navbar.methods.invokeMenuAction.call(ctx, actionSpy)
    expect(hideSpy).toHaveBeenCalled()
    expect(actionSpy).toHaveBeenCalled()

    toggleSpy.mockClear()
    trackEventMock.mockClear()
    Navbar.methods.toggleMoreActions.call({
      moreActions: [],
      $refs: ctx.$refs,
      isDesktopView: false,
    })
    expect(toggleSpy).not.toHaveBeenCalled()
    expect(trackEventMock).not.toHaveBeenCalled()

    hideSpy.mockClear()
    Navbar.methods.invokeMenuAction.call(ctx, 'not-a-function')
    expect(hideSpy).toHaveBeenCalled()
  })

  it('checks authentication and updates user data', () => {
    isAuthenticatedMock.mockReturnValue(true)
    getCurrentUserMock.mockReturnValue({ name: 'Alice' })

    const ctx = {
      isAuthenticated: false,
      userData: null,
    }

    Navbar.methods.checkAuthentication.call(ctx)
    expect(ctx.isAuthenticated).toBe(true)
    expect(ctx.userData.name).toBe('Alice')
  })

  it('handles authentication fallback cases', () => {
    const ctx = {
      isAuthenticated: true,
      userData: { name: 'Bob' },
    }

    isAuthenticatedMock.mockReturnValue(true)
    getCurrentUserMock.mockReturnValueOnce(null)

    Navbar.methods.checkAuthentication.call(ctx)
    expect(ctx.isAuthenticated).toBe(false)
    expect(ctx.userData).toBeNull()

    isAuthenticatedMock.mockReturnValue(false)
    Navbar.methods.checkAuthentication.call(ctx)
    expect(ctx.isAuthenticated).toBe(false)
    expect(ctx.userData).toBeNull()
  })

  it('manages issue dialogs and navigation actions', () => {
    const routerPush = vi.fn()
    const ctx = {
      isAuthenticated: true,
      $router: { push: routerPush },
      issueReportVisible: false,
      issueForm: {
        type: 'bug',
        title: 'Issue',
        description: 'desc',
        contact: 'contact',
      },
      notificationStore: notificationStoreMock,
    }

    Navbar.methods.handleTitleClick.call(ctx)
    expect(routerPush).toHaveBeenCalledWith('/archive')

    Navbar.methods.handleNavigateAdmin.call(ctx)
    expect(routerPush).toHaveBeenCalledWith('/admin')

    Navbar.methods.openIssueReportDialog.call(ctx)
    expect(trackEventMock).toHaveBeenCalledWith('open-issue-report')
    expect(ctx.issueReportVisible).toBe(true)

    Navbar.methods.closeIssueReportDialog.call(ctx)
    expect(ctx.issueReportVisible).toBe(false)
    expect(ctx.issueForm.title).toBe('')

    Navbar.methods.handleIssueReportDialogClose.call(ctx, false)
    expect(ctx.issueForm.description).toBe('')
  })

  it('skips archive navigation when not authenticated', () => {
    const routerPush = vi.fn()
    Navbar.methods.handleTitleClick.call({
      isAuthenticated: false,
      $router: { push: routerPush },
    })

    expect(routerPush).not.toHaveBeenCalled()
  })

  it('handles OAuth login shortcut', () => {
    const ctx = {
      loginVisible: true,
    }
    Navbar.methods.handleOAuthLogin.call(ctx)
    expect(loginRedirectMock).toHaveBeenCalled()
    expect(ctx.loginVisible).toBe(false)
  })

  it('opens AI exam dialog and handles loading outcomes', async () => {
    const ctx = {
      aiExamDialogVisible: false,
      coursesList: null,
      toast: { add: toastAddMock },
    }

    courseServiceListMock.mockResolvedValueOnce({ data: { freshman: [] } })
    await Navbar.methods.openAIExamDialog.call(ctx)
    expect(ctx.aiExamDialogVisible).toBe(true)
    expect(courseServiceListMock).toHaveBeenCalled()
    expect(ctx.coursesList).toEqual({ freshman: [] })

    const errorCtx = {
      aiExamDialogVisible: false,
      coursesList: null,
      toast: { add: toastAddMock },
    }
    toastAddMock.mockClear()
    courseServiceListMock.mockRejectedValueOnce(new Error('failed'))
    await Navbar.methods.openAIExamDialog.call(errorCtx)
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '載入失敗' })
    )

    const unauthorizedCtx = {
      aiExamDialogVisible: false,
      coursesList: null,
      toast: { add: toastAddMock },
    }
    toastAddMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    courseServiceListMock.mockRejectedValueOnce(new Error('unauthorized'))
    await Navbar.methods.openAIExamDialog.call(unauthorizedCtx)
    expect(toastAddMock).not.toHaveBeenCalled()

    const cachedCtx = {
      aiExamDialogVisible: false,
      coursesList: { freshman: [{ id: 1, name: 'Calc' }] },
      toast: { add: toastAddMock },
    }
    toastAddMock.mockClear()
    courseServiceListMock.mockClear()
    await Navbar.methods.openAIExamDialog.call(cachedCtx)
    expect(courseServiceListMock).not.toHaveBeenCalled()
    expect(cachedCtx.aiExamDialogVisible).toBe(true)
  })

  it('formats issue body with system information', () => {
    const ctx = {
      getBrowserInfo: vi.fn(() => 'Chrome 120'),
      getOSInfo: vi.fn(() => 'macOS 14.0'),
      formatTimestamp: vi.fn(() => '2025/10/30 12:00:00 (UTC+8)'),
    }
    const systemInfo = {
      userAgent: 'chrome ua',
      platform: 'MacIntel',
      language: 'zh-TW',
      url: 'https://example.com',
      route: { path: '/archive', name: 'ArchiveView', fullPath: '/archive?course=1' },
      pageContext: {
        archiveContext: {
          course: { id: 101, name: '資料結構' },
          filters: {
            year: '2024',
            professor: '王教授',
            type: 'final',
            hasAnswers: true,
            searchQuery: '資',
          },
          preview: { open: true, archiveId: 201, name: '期末考' },
        },
      },
      timestamp: '2025-10-30T00:00:00Z',
    }

    const bodyWithContact = Navbar.methods.formatIssueBody.call(
      ctx,
      '描述內容',
      'contact@example.com',
      systemInfo,
      'bug'
    )
    expect(ctx.getBrowserInfo).toHaveBeenCalledWith('chrome ua')
    expect(bodyWithContact).toContain('contact@example.com')
    expect(bodyWithContact).toContain('## 頁面資訊')
    expect(bodyWithContact).toContain('資料結構')
    expect(bodyWithContact).toContain('year=2024')
    expect(bodyWithContact).toContain('archiveId=201')

    const bodyWithoutContact = Navbar.methods.formatIssueBody.call(
      ctx,
      '描述內容',
      '',
      systemInfo,
      'question'
    )
    expect(bodyWithoutContact).not.toContain('聯絡方式')
  })

  it('detects browser and operating system variants', () => {
    const chrome = Navbar.methods.getBrowserInfo.call({}, 'Chrome/120.0')
    const firefox = Navbar.methods.getBrowserInfo.call({}, 'Firefox/118.0')
    const safari = Navbar.methods.getBrowserInfo.call({}, 'Version Safari/16.4')
    const edge = Navbar.methods.getBrowserInfo.call({}, 'Edge/118.0')
    const unknown = Navbar.methods.getBrowserInfo.call({}, 'Other UA')

    expect(chrome).toMatch(/Chrome/)
    expect(firefox).toMatch(/Firefox/)
    expect(safari).toMatch(/Safari/)
    expect(edge).toMatch(/Edge/)
    expect(unknown).toBe('Unknown Browser')

    expect(Navbar.methods.getOSInfo.call({}, 'MacIntel', 'Mac OS X 13_6')).toContain('macOS')
    expect(Navbar.methods.getOSInfo.call({}, 'Win', 'Windows NT 10.0')).toBe('Windows 10/11')
    expect(Navbar.methods.getOSInfo.call({}, 'Linux', 'Linux x86_64')).toBe('Linux')
    expect(Navbar.methods.getOSInfo.call({}, 'Android', 'Android 13.0')).toBe('Android 13.0')
    expect(Navbar.methods.getOSInfo.call({}, 'iPhone', 'Mozilla/5.0 (iPhone; CPU OS 16_4)')).toBe(
      'iOS 16.4'
    )
    expect(Navbar.methods.getOSInfo.call({}, 'Other', 'Unknown')).toBe('Other')
  })

  it('collects system info and formats timestamps', () => {
    sessionStorage.setItem(
      'pastexam-issue-context',
      JSON.stringify({
        page: 'archive',
        course: { id: 101, name: '資料結構' },
        filters: {
          year: '2024',
          professor: null,
          type: null,
          hasAnswers: false,
          searchQuery: null,
        },
        preview: { open: false, archiveId: null },
      })
    )

    const info = Navbar.methods.getSystemInfo.call({})
    expect(info).toMatchObject({
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      url: window.location.href,
      route: { path: null, name: null, fullPath: null },
    })
    expect(info).toHaveProperty('pageContext')
    expect(typeof info.timestamp).toBe('string')

    const formatted = Navbar.methods.formatTimestamp.call({}, '2024-01-01T00:00:00Z')
    expect(formatted).toContain('(UTC+8)')
  })

  it('submits issue report through GitHub redirect', () => {
    const openSpy = vi.spyOn(window, 'open').mockImplementation(() => {})
    const ctx = {
      issueForm: {
        type: 'bug',
        title: '系統問題',
        description: '詳細描述',
        contact: 'contact@example.com',
      },
      toast: { add: toastAddMock },
      closeIssueReportDialog: vi.fn(),
      getSystemInfo: vi.fn(() => ({
        userAgent: 'ua',
        platform: 'platform',
        language: 'zh-TW',
        url: 'https://example.com',
        timestamp: '2025-10-30T00:00:00Z',
      })),
      formatIssueBody: vi.fn(() => 'issue body'),
    }

    Navbar.methods.submitIssueReport.call(ctx)
    expect(trackEventMock).toHaveBeenCalledWith(
      'submit-issue-report',
      expect.objectContaining({ type: 'bug', hasContact: true })
    )
    expect(ctx.formatIssueBody).toHaveBeenCalled()
    expect(ctx.closeIssueReportDialog).toHaveBeenCalled()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'success', summary: '已跳轉到 GitHub' })
    )
    expect(openSpy).toHaveBeenCalled()
    openSpy.mockRestore()
  })

  it('computes menu helpers correctly', () => {
    const pendingCtx = {
      notificationStore: { latestUnseenNotification: { value: { id: 99 } } },
    }
    expect(Navbar.computed.pendingNotification.call(pendingCtx)).toEqual({ id: 99 })
    pendingCtx.notificationStore.latestUnseenNotification = null
    expect(Navbar.computed.pendingNotification.call(pendingCtx)).toBeNull()

    const actionsCtxDesktop = {
      isAuthenticated: true,
      userData: { is_admin: true },
      isDesktopView: true,
      invokeMenuAction: vi.fn((handler) => handler()),
      openAIExamDialog: vi.fn(),
      openNotificationCenter: vi.fn(),
      openIssueReportDialog: vi.fn(),
      handleNavigateAdmin: vi.fn(),
      handleLogout: vi.fn(),
    }
    const actionsDesktop = Navbar.computed.moreActions.call(actionsCtxDesktop)
    expect(actionsDesktop).toHaveLength(4)
    actionsDesktop[0].command()
    expect(actionsCtxDesktop.invokeMenuAction).toHaveBeenCalled()
    expect(actionsCtxDesktop.openAIExamDialog).toHaveBeenCalled()

    const actionsCtxMobile = {
      isAuthenticated: true,
      userData: { is_admin: true },
      isDesktopView: false,
      invokeMenuAction: vi.fn((handler) => handler()),
      openAIExamDialog: vi.fn(),
      openNotificationCenter: vi.fn(),
      openIssueReportDialog: vi.fn(),
      handleNavigateAdmin: vi.fn(),
      handleLogout: vi.fn(),
    }
    const actionsMobile = Navbar.computed.moreActions.call(actionsCtxMobile)
    expect(actionsMobile).toHaveLength(6)
    expect(actionsMobile[4]).toHaveProperty('separator')
    expect(actionsMobile[5].label).toBe('登出')

    const canSubmitCtx = {
      issueForm: { type: 'bug', title: 'Title', description: 'Desc' },
    }
    expect(Navbar.computed.canSubmitIssue.call(canSubmitCtx)).toBeTruthy()
    canSubmitCtx.issueForm.title = ' '
    expect(Navbar.computed.canSubmitIssue.call(canSubmitCtx)).toBeFalsy()
  })

  it('returns empty menu actions when unauthenticated', () => {
    const actionsCtx = {
      isAuthenticated: false,
    }

    expect(Navbar.computed.moreActions.call(actionsCtx)).toEqual([])
  })

  it('reacts to authentication watcher changes', async () => {
    const initSpy = vi.fn()
    const ctx = {
      notificationStore: notificationStoreMock,
      initializeNotifications: initSpy,
    }

    notificationStoreMock.state.modalVisible = true
    notificationStoreMock.state.centerVisible = true
    notificationStoreMock.state.active = [1]
    notificationStoreMock.state.all = [1, 2]
    notificationStoreMock.state.initialized = true

    await Navbar.watch.isAuthenticated.call(ctx, true)
    expect(initSpy).toHaveBeenCalled()

    await Navbar.watch.isAuthenticated.call(ctx, false)
    expect(notificationStoreMock.state.modalVisible).toBe(false)
    expect(notificationStoreMock.state.centerVisible).toBe(false)
    expect(notificationStoreMock.state.active).toEqual([])
    expect(notificationStoreMock.state.all).toEqual([])
    expect(notificationStoreMock.state.initialized).toBe(false)
  })

  it('renders template states for authentication transitions', async () => {
    const setIntervalSpy = vi.spyOn(window, 'setInterval').mockImplementation(() => 1)
    const baseData = Navbar.data ? Navbar.data.call({}) : {}
    const globalConfig = {
      stubs: {
        Menubar: {
          name: 'MenubarStub',
          template:
            '<div class="menubar"><slot name="start"></slot><slot></slot><slot name="end"></slot></div>',
        },
        Button: {
          name: 'ButtonStub',
          props: ['icon', 'label', 'ariaLabel'],
          template:
            '<button :data-icon="icon" :data-label="label" :data-testid="ariaLabel || icon" @click="$emit(\'click\', $event)"><slot /></button>',
        },
        Dialog: {
          name: 'DialogStub',
          props: ['visible'],
          emits: ['update:visible'],
          template: '<div v-if="visible" class="dialog"><slot /></div>',
        },
        Menu: {
          name: 'MenuStub',
          props: ['model', 'popup'],
          template: '<div data-testid="menu"></div>',
        },
        NotificationModal: false,
        NotificationCenterModal: false,
        GenerateAIExamModal: false,
        Select: { name: 'SelectStub', template: '<select><slot /></select>' },
        InputText: { name: 'InputTextStub', template: '<input />' },
        Textarea: { name: 'TextareaStub', template: '<textarea></textarea>' },
        FloatLabel: {
          name: 'FloatLabelStub',
          template: '<div><slot /><slot name="label" /></div>',
        },
        Password: { name: 'PasswordStub', template: '<input type="password" />' },
        Divider: { name: 'DividerStub', template: '<div class="divider"><slot /></div>' },
      },
      mocks: {
        $route: { path: '/archive' },
        $router: { push: vi.fn() },
      },
    }

    const unauthWrapper = shallowMount(Navbar, {
      global: globalConfig,
      data() {
        return { ...baseData }
      },
    })

    await nextTick()

    expect(unauthWrapper.find('[data-icon="pi pi-sign-in"]').exists()).toBe(true)
    expect(unauthWrapper.find('[data-icon="pi pi-sign-out"]').exists()).toBe(false)

    unauthWrapper.unmount()

    notificationStoreMock.latestUnseenNotification = { value: { id: 1 } }
    notificationStoreMock.state.modalVisible = true
    notificationStoreMock.state.centerVisible = true

    isAuthenticatedMock.mockReturnValue(true)
    getCurrentUserMock.mockReturnValue({ name: 'Alice', is_admin: true })

    const authWrapper = shallowMount(Navbar, {
      global: globalConfig,
      data() {
        return { ...baseData }
      },
    })

    await nextTick()

    expect(authWrapper.find('[data-icon="pi pi-sign-in"]').exists()).toBe(false)
    expect(authWrapper.find('[data-icon="pi pi-sign-out"]').exists()).toBe(true)
    expect(authWrapper.find('.notification-modal').exists()).toBe(true)
    expect(authWrapper.find('.notification-center').exists()).toBe(true)

    const menuProps = authWrapper.getComponent({ name: 'MenuStub' }).props('model')
    expect(Array.isArray(menuProps)).toBe(true)
    expect(menuProps.length).toBeGreaterThan(0)

    authWrapper.unmount()
    notificationStoreMock.latestUnseenNotification = null
    setIntervalSpy.mockRestore()
  })
})
