import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import ArchiveView from '@/views/Archive.vue'

const trackEventMock = vi.hoisted(() => vi.fn())
const isUnauthorizedErrorMock = vi.hoisted(() => vi.fn())
const getCurrentUserMock = vi.hoisted(() =>
  vi.fn(() => ({
    id: 10,
    is_admin: true,
  }))
)
const isAuthenticatedMock = vi.hoisted(() => vi.fn(() => true))

const listCoursesMock = vi.hoisted(() => vi.fn())
const getCourseArchivesMock = vi.hoisted(() => vi.fn())
const getArchiveDownloadUrlMock = vi.hoisted(() => vi.fn())
const getArchivePreviewUrlMock = vi.hoisted(() => vi.fn())
const deleteArchiveMock = vi.hoisted(() => vi.fn())
const updateArchiveMock = vi.hoisted(() => vi.fn())
const updateArchiveCourseMock = vi.hoisted(() => vi.fn())
const updateArchiveCourseByCategoryAndNameMock = vi.hoisted(() => vi.fn())

const toastAddMock = vi.hoisted(() => vi.fn())
const confirmRequireMock = vi.hoisted(() => vi.fn())

let originalCreateObjectURL
let originalRevokeObjectURL
let originalFetch
let consoleErrorSpy

const sampleCourses = {
  freshman: [
    { id: 'c1', name: 'Calculus I' },
    { id: 'c2', name: 'Linear Algebra' },
  ],
  sophomore: [{ id: 'c3', name: 'Data Structures' }],
  junior: [],
  senior: [],
  graduate: [],
  interdisciplinary: [],
  general: [],
}

const baseArchives = [
  {
    id: 'a1',
    academic_year: '2023',
    name: 'Midterm',
    archive_type: 'midterm',
    professor: 'Prof. Chen',
    has_answers: true,
    uploader_id: 10,
    download_count: 3,
  },
  {
    id: 'a2',
    academic_year: '2022',
    name: 'Final',
    archive_type: 'final',
    professor: 'Prof. Wang',
    has_answers: false,
    uploader_id: 11,
    download_count: 1,
  },
]

const updatedArchives = baseArchives.map((archive, index) => ({
  ...archive,
  download_count: archive.download_count + index + 1,
}))

vi.mock('@/api', () => ({
  courseService: {
    listCourses: listCoursesMock,
    getCourseArchives: getCourseArchivesMock,
  },
  archiveService: {
    getArchiveDownloadUrl: getArchiveDownloadUrlMock,
    getArchivePreviewUrl: getArchivePreviewUrlMock,
    deleteArchive: deleteArchiveMock,
    updateArchive: updateArchiveMock,
    updateArchiveCourse: updateArchiveCourseMock,
    updateArchiveCourseByCategoryAndName: updateArchiveCourseByCategoryAndNameMock,
  },
}))

vi.mock('@/components/PdfPreviewModal.vue', () => ({
  default: {
    template: '<div><slot /></div>',
    props: ['visible', 'previewUrl', 'courseId', 'archiveId', 'loading', 'error'],
    emits: ['update:visible', 'download', 'hide', 'error'],
  },
}))

vi.mock('@/components/UploadArchiveDialog.vue', () => ({
  default: {
    template: '<div></div>',
    props: ['visible'],
    emits: ['update:visible', 'success'],
  },
}))

vi.mock('@/utils/auth', () => ({
  getCurrentUser: getCurrentUserMock,
  isAuthenticated: isAuthenticatedMock,
}))

vi.mock('@/utils/useTheme', () => ({
  useTheme: () => ({ isDarkTheme: ref(false) }),
}))

vi.mock('@/utils/analytics', () => ({
  trackEvent: trackEventMock,
  EVENTS: {
    FILTER_ARCHIVES: 'filter-archives',
    SEARCH_COURSE: 'search-course',
    SELECT_COURSE: 'select-course',
    DOWNLOAD_ARCHIVE: 'download-archive',
    PREVIEW_ARCHIVE: 'preview-archive',
    EDIT_ARCHIVE: 'edit-archive',
    DELETE_ARCHIVE: 'delete-archive',
    UPLOAD_ARCHIVE: 'upload-archive',
    TOGGLE_SIDEBAR: 'toggle-sidebar',
  },
}))

vi.mock('@/utils/http', () => ({
  isUnauthorizedError: isUnauthorizedErrorMock,
}))

const componentStubs = {
  InputText: { template: '<div><slot /></div>' },
  Button: { template: '<div><slot /></div>' },
  PanelMenu: { template: '<div><slot /></div>' },
  Drawer: { template: '<div><slot /></div>' },
  Tag: { template: '<div><slot /></div>' },
  Toolbar: { template: '<div><slot /></div>' },
  Select: { template: '<div><slot /></div>' },
  Checkbox: { template: '<div><slot /></div>' },
  ProgressSpinner: { template: '<div class="spinner"><slot /></div>' },
  Accordion: { template: '<div><slot /></div>' },
  AccordionPanel: { template: '<div><slot /></div>' },
  AccordionHeader: { template: '<div><slot /></div>' },
  AccordionContent: { template: '<div><slot /></div>' },
  DataTable: { template: '<div><slot /></div>' },
  Column: { template: '<template />' },
  Tabs: { template: '<div><slot /></div>' },
  TabList: { template: '<div><slot /></div>' },
  TabPanels: { template: '<div><slot /></div>' },
  TabPanel: { template: '<div><slot /></div>' },
  Dialog: { template: '<div><slot /></div>' },
  AutoComplete: { template: '<div><slot /></div>' },
  DatePicker: { template: '<div><slot /></div>' },
  Divider: { template: '<div></div>' },
}

describe('ArchiveView', () => {
  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    vi.useFakeTimers()
    localStorage.clear()
    sessionStorage.clear()
    trackEventMock.mockReset()
    isUnauthorizedErrorMock.mockReturnValue(false)
    listCoursesMock.mockResolvedValue({ data: sampleCourses })
    getCourseArchivesMock.mockReset()
    getCourseArchivesMock
      .mockResolvedValueOnce({ data: baseArchives })
      .mockResolvedValueOnce({ data: updatedArchives })
      .mockResolvedValue({ data: baseArchives })

    getArchiveDownloadUrlMock.mockResolvedValue({
      data: { url: 'https://example.com/archive.pdf' },
    })
    getArchivePreviewUrlMock.mockResolvedValue({
      data: { url: 'https://example.com/preview.pdf' },
    })
    deleteArchiveMock.mockResolvedValue()
    updateArchiveMock.mockResolvedValue()
    updateArchiveCourseMock.mockResolvedValue()
    updateArchiveCourseByCategoryAndNameMock.mockResolvedValue()
    toastAddMock.mockReset()
    confirmRequireMock.mockReset()
    confirmRequireMock.mockImplementation(({ accept }) => accept && accept())

    originalFetch = globalThis.fetch
    originalCreateObjectURL = window.URL.createObjectURL
    originalRevokeObjectURL = window.URL.revokeObjectURL
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        blob: () => Promise.resolve(new Blob(['dummy'])),
      })
    )
    window.URL.createObjectURL = vi.fn(() => 'blob:url')
    window.URL.revokeObjectURL = vi.fn()
    window.innerWidth = 1024
  })

  afterEach(() => {
    consoleErrorSpy?.mockRestore()
    vi.useRealTimers()
    vi.clearAllMocks()
    globalThis.fetch = originalFetch
    window.URL.createObjectURL = originalCreateObjectURL
    window.URL.revokeObjectURL = originalRevokeObjectURL
  })

  it('handles core archive interactions', async () => {
    const sidebarInjected = ref(true)

    const wrapper = mount(ArchiveView, {
      global: {
        provide: {
          toast: { add: toastAddMock },
          confirm: { require: confirmRequireMock },
          sidebarVisible: sidebarInjected,
        },
        stubs: componentStubs,
      },
    })

    await flushPromises()
    vi.runAllTimers()
    await flushPromises()

    const initialIssueContextRaw = sessionStorage.getItem('pastexam-issue-context')
    expect(initialIssueContextRaw).toBeTruthy()
    const initialIssueContext = JSON.parse(initialIssueContextRaw)
    expect(initialIssueContext.page).toBe('archive')

    const vm = wrapper.vm

    vm.filterBySubject(null)
    expect(vm.selectedSubject).toBeNull()

    vm.filterBySubject({ label: 'Calculus I', id: 'c1' })
    await flushPromises()
    vi.runAllTimers()
    await flushPromises()

    expect(getCourseArchivesMock).toHaveBeenCalled()
    expect(vm.selectedSubject).toBe('Calculus I')
    expect(vm.groupedArchives.length).toBeGreaterThan(0)

    const issueContextAfterSelect = JSON.parse(sessionStorage.getItem('pastexam-issue-context'))
    expect(issueContextAfterSelect.course).toEqual({ id: 'c1', name: 'Calculus I' })

    vm.filters.year = '2023'
    vm.filters.professor = 'Prof. Chen'
    vm.filters.type = 'midterm'
    vm.filters.hasAnswers = true
    await nextTick()

    vm.searchQuery = 'calc'
    vi.runAllTimers()
    await flushPromises()

    const issueContextAfterFilters = JSON.parse(sessionStorage.getItem('pastexam-issue-context'))
    expect(issueContextAfterFilters.filters).toEqual(
      expect.objectContaining({
        year: '2023',
        professor: 'Prof. Chen',
        type: 'midterm',
        hasAnswers: true,
        searchQuery: 'calc',
      })
    )

    const archiveItem = vm.groupedArchives[0].list[0]
    await vm.downloadArchive(archiveItem)
    await flushPromises()

    expect(getArchiveDownloadUrlMock).toHaveBeenCalled()
    expect(toastAddMock).toHaveBeenCalled()

    await vm.previewArchive(archiveItem)
    await flushPromises()
    expect(vm.showPreview).toBe(true)
    expect(vm.selectedArchive.previewUrl).toContain('preview')

    const issueContextAfterPreview = JSON.parse(sessionStorage.getItem('pastexam-issue-context'))
    expect(issueContextAfterPreview.preview).toEqual(
      expect.objectContaining({
        open: true,
        archiveId: archiveItem.id,
      })
    )

    vm.handlePreviewError()
    expect(vm.previewError).toBe(true)

    const onDownloadComplete = vi.fn()
    await vm.handlePreviewDownload(onDownloadComplete)
    expect(onDownloadComplete).toHaveBeenCalled()

    vm.closePreview()
    expect(vm.showPreview).toBe(false)
    await nextTick()
    const issueContextAfterClosePreview = JSON.parse(
      sessionStorage.getItem('pastexam-issue-context')
    )
    expect(issueContextAfterClosePreview.preview?.open).toBe(false)

    vm.confirmDelete(archiveItem)
    await flushPromises()
    expect(deleteArchiveMock).toHaveBeenCalled()

    await vm.openEditDialog(archiveItem)
    vm.editForm.shouldTransfer = true
    vm.editForm.targetCategory = 'freshman'
    vm.editForm.targetCourseId = 'c2'
    await vm.handleEdit()

    await vm.openEditDialog(archiveItem)
    vm.editForm.shouldTransfer = true
    vm.editForm.targetCategory = 'freshman'
    vm.editForm.targetCourse = 'New Course'
    vm.editForm.targetCourseId = null
    await vm.handleEdit()

    await vm.handleUploadSuccess()
    expect(listCoursesMock.mock.calls.length).toBeGreaterThanOrEqual(3)

    expect(vm.getCategoryTag('大一課程')).toBe('大一')
    expect(vm.formatDownloadCount(0)).toBe('0')
    expect(vm.formatDownloadCount(12)).toBe('12')

    const initialSidebar = sidebarInjected.value
    vm.toggleSidebar()
    expect(sidebarInjected.value).toBe(!initialSidebar)

    await vm.syncArchiveDownloadCount('a1')
    expect(getCourseArchivesMock.mock.calls.length).toBeGreaterThanOrEqual(5)

    wrapper.unmount()
  })

  it('handles error and unauthorized branches gracefully', async () => {
    const sidebarInjected = ref(true)

    const wrapper = mount(ArchiveView, {
      global: {
        provide: {
          toast: { add: toastAddMock },
          confirm: { require: confirmRequireMock },
          sidebarVisible: sidebarInjected,
        },
        stubs: componentStubs,
      },
    })

    await flushPromises()

    toastAddMock.mockClear()
    listCoursesMock.mockReset()
    listCoursesMock.mockRejectedValueOnce(new Error('unauthorized'))
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    await wrapper.vm.fetchCourses()
    expect(toastAddMock).not.toHaveBeenCalled()

    toastAddMock.mockClear()
    listCoursesMock.mockRejectedValueOnce(new Error('fail'))
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    await wrapper.vm.fetchCourses()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ detail: '無法載入課程資料' })
    )

    listCoursesMock.mockReset()
    listCoursesMock.mockResolvedValue({ data: sampleCourses })

    wrapper.vm.selectedCourse = 'c1'
    wrapper.vm.selectedSubject = 'Calculus I'

    toastAddMock.mockClear()
    getCourseArchivesMock.mockReset()
    getCourseArchivesMock.mockRejectedValueOnce(new Error('archives'))
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    await wrapper.vm.fetchArchives()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ detail: '無法載入考古題資料' })
    )

    toastAddMock.mockClear()
    getArchiveDownloadUrlMock.mockRejectedValueOnce(new Error('unauthorized'))
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    await wrapper.vm.downloadArchive(baseArchives[0])
    expect(toastAddMock).not.toHaveBeenCalled()
    expect(wrapper.vm.downloadingId).toBeNull()

    toastAddMock.mockClear()
    getArchiveDownloadUrlMock.mockRejectedValueOnce(new Error('download'))
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    await wrapper.vm.downloadArchive(baseArchives[0])
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ detail: '無法取得下載連結' })
    )

    toastAddMock.mockClear()
    getArchivePreviewUrlMock.mockRejectedValueOnce(new Error('preview'))
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    await wrapper.vm.previewArchive(baseArchives[0])
    expect(wrapper.vm.previewError).toBe(true)
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ detail: '無法取得預覽連結' })
    )

    toastAddMock.mockClear()
    deleteArchiveMock.mockRejectedValueOnce(new Error('delete'))
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    await wrapper.vm.deleteArchive({ ...baseArchives[0], id: baseArchives[0].id, year: '2023' })
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ detail: '發生錯誤，請稍後再試' })
    )

    toastAddMock.mockClear()
    getArchiveDownloadUrlMock.mockRejectedValueOnce(new Error('preview-download'))
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    wrapper.vm.selectedArchive = { ...baseArchives[0], id: baseArchives[0].id }
    wrapper.vm.selectedCourse = 'c1'
    wrapper.vm.selectedSubject = 'Calculus I'
    await wrapper.vm.handlePreviewDownload(() => {})
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ detail: '無法取得下載連結' })
    )

    wrapper.unmount()
  })

  it('covers edit helpers and mobile menu utilities', async () => {
    const sidebarInjected = ref(true)

    const wrapper = mount(ArchiveView, {
      global: {
        provide: {
          toast: { add: toastAddMock },
          confirm: { require: confirmRequireMock },
          sidebarVisible: sidebarInjected,
        },
        stubs: componentStubs,
      },
    })

    await flushPromises()

    const vm = wrapper.vm

    vm.uploadFormProfessors = [
      { name: 'Prof. Chen', code: 'Prof. Chen' },
      { name: 'Prof. Wang', code: 'Prof. Wang' },
    ]

    vm.searchEditProfessor({ query: 'chen' })
    expect(vm.availableEditProfessors).toEqual([expect.objectContaining({ name: 'Prof. Chen' })])

    vm.onEditProfessorSelect({ value: { name: 'Prof. Hsu' } })
    expect(vm.editForm.professor).toBe('Prof. Hsu')

    vm.editForm.targetCategory = 'freshman'
    vm.selectedCourse = 'c1'
    await nextTick()

    vm.searchTargetCourse({ query: 'linear' })
    expect(vm.availableCoursesForTransfer[0].label.toLowerCase()).toContain('linear')

    vm.onTargetCourseSelect({ value: { label: 'Linear Algebra', id: 'c2' } })
    expect(vm.editForm.targetCourseId).toBe('c2')

    vm.onTargetCourseSelect({ value: 'New Course' })
    expect(vm.editForm.targetCourse).toBe('New Course')
    expect(vm.editForm.targetCourseId).toBeNull()

    vm.editForm.targetCourse = 'Linear Algebra'
    await nextTick()
    expect(vm.editForm.targetCourseId).toBe('c2')

    vm.editForm.targetCourse = 'Brand New'
    await nextTick()
    expect(vm.editForm.targetCourseId).toBeNull()

    vm.closeEditDialog()
    expect(vm.showEditDialog).toBe(false)
    expect(vm.editForm.id).toBeNull()

    vm.checkAuthentication()
    expect(vm.isAuthenticatedRef).toBe(true)
    expect(vm.userData?.id).toBe(10)

    const mobileMenu = vm.mobileMenuItems
    expect(Array.isArray(mobileMenu)).toBe(true)

    wrapper.unmount()
  })

  it('covers remaining utility branches', async () => {
    const sidebarInjected = ref(true)

    const wrapper = mount(ArchiveView, {
      global: {
        provide: {
          toast: { add: toastAddMock },
          confirm: { require: confirmRequireMock },
          sidebarVisible: sidebarInjected,
        },
        stubs: componentStubs,
      },
    })

    await flushPromises()

    // getCurrentCategory fallback when no course selected
    wrapper.vm.selectedCourse = null
    expect(wrapper.vm.getCurrentCategory).toBe('')

    // Unauthorized preview download branch
    wrapper.vm.selectedCourse = 'c1'
    wrapper.vm.selectedSubject = 'Calculus I'
    wrapper.vm.selectedArchive = { id: 'a1', year: '2023', professor: 'Prof', name: 'Midterm' }
    getArchiveDownloadUrlMock.mockRejectedValueOnce(new Error('unauthorized'))
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    const onComplete = vi.fn()
    await wrapper.vm.handlePreviewDownload(onComplete)
    expect(onComplete).toHaveBeenCalled()
    expect(toastAddMock).not.toHaveBeenCalled()

    // checkAuthentication when user missing
    isAuthenticatedMock.mockReturnValueOnce(true)
    getCurrentUserMock.mockReturnValueOnce(null)
    wrapper.vm.checkAuthentication()
    expect(wrapper.vm.isAuthenticatedRef).toBe(false)
    expect(wrapper.vm.userData).toBeNull()

    // Mobile menu command toggles sidebar
    const menu = wrapper.vm.mobileMenuItems
    expect(menu.length).toBeGreaterThan(0)
    const firstCourse = menu[0].items?.[0]
    if (firstCourse?.command) {
      sidebarInjected.value = true
      firstCourse.command()
      expect(sidebarInjected.value).toBe(false)
    }

    wrapper.unmount()
  })
})
