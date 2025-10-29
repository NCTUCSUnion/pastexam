import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, nextTick } from 'vue'
import ArchiveView from '@/views/Archive.vue'

const trackEventMock = vi.hoisted(() => vi.fn())
const isUnauthorizedErrorMock = vi.hoisted(() => vi.fn())

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
    props: ['visible', 'archive', 'loading', 'error'],
    emits: ['update:visible', 'download'],
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
  getCurrentUser: vi.fn(() => ({ id: 10, is_admin: true })),
  isAuthenticated: vi.fn(() => true),
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
    vi.useFakeTimers()
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

    vm.filters.year = '2023'
    vm.filters.professor = 'Prof. Chen'
    vm.filters.type = 'midterm'
    vm.filters.hasAnswers = true
    await nextTick()

    vm.searchQuery = 'calc'
    vi.runAllTimers()
    await flushPromises()

    const archiveItem = vm.groupedArchives[0].list[0]
    await vm.downloadArchive(archiveItem)
    await flushPromises()

    expect(getArchiveDownloadUrlMock).toHaveBeenCalled()
    expect(toastAddMock).toHaveBeenCalled()

    await vm.previewArchive(archiveItem)
    expect(vm.showPreview).toBe(true)
    expect(vm.selectedArchive.previewUrl).toContain('preview')

    vm.handlePreviewError()
    expect(vm.previewError).toBe(true)

    const onDownloadComplete = vi.fn()
    await vm.handlePreviewDownload(onDownloadComplete)
    expect(onDownloadComplete).toHaveBeenCalled()

    vm.closePreview()
    expect(vm.showPreview).toBe(false)

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
})
