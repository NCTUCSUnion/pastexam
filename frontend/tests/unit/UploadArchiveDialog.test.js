import { describe, it, expect, vi, beforeEach, afterEach, beforeAll } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

const courseServiceMock = vi.hoisted(() => ({
  getCourseArchives: vi.fn(),
}))

const archiveServiceMock = vi.hoisted(() => ({
  uploadArchive: vi.fn(),
}))

const trackEventMock = vi.hoisted(() => vi.fn())
const toastAddMock = vi.hoisted(() => vi.fn())
const isUnauthorizedErrorMock = vi.hoisted(() => vi.fn(() => false))

let originalURL
let consoleErrorSpy
let UploadArchiveDialog

const ensureDomMatrix = vi.hoisted(() => () => {
  if (typeof globalThis.DOMMatrix === 'undefined') {
    class DOMMatrixPolyfill {
      constructor() {
        this.a = 1
        this.b = 0
        this.c = 0
        this.d = 1
        this.e = 0
        this.f = 0
      }
      multiplySelf() {
        return this
      }
      translateSelf() {
        return this
      }
      scaleSelf() {
        return this
      }
      rotateSelf() {
        return this
      }
    }
    globalThis.DOMMatrix = DOMMatrixPolyfill
    globalThis.DOMMatrixReadOnly = DOMMatrixPolyfill
  }
})

const pdfLoadMock = vi.hoisted(() =>
  vi.fn(async () => ({
    setTitle: vi.fn(),
    setAuthor: vi.fn(),
    setSubject: vi.fn(),
    setKeywords: vi.fn(),
    setProducer: vi.fn(),
    setCreator: vi.fn(),
    setCreationDate: vi.fn(),
    setModificationDate: vi.fn(),
    save: vi.fn(async () => new Uint8Array([1, 2, 3])),
  }))
)

vi.mock('@/api', () => ({
  courseService: courseServiceMock,
  archiveService: archiveServiceMock,
}))

vi.mock('primevue/usetoast', () => ({
  useToast: () => ({
    add: toastAddMock,
  }),
}))

vi.mock('pdf-lib', () => ({
  PDFDocument: {
    load: pdfLoadMock,
  },
}))

vi.mock('@/utils/analytics', () => ({
  trackEvent: trackEventMock,
  EVENTS: {
    PREVIEW_ARCHIVE: 'preview-archive',
  },
}))

vi.mock('@/utils/http', () => ({
  isUnauthorizedError: isUnauthorizedErrorMock,
}))

const sampleCourses = {
  freshman: [
    { id: 'c1', name: 'Calculus I' },
    { id: 'c2', name: 'Physics' },
  ],
  sophomore: [],
  junior: [],
  senior: [],
  graduate: [],
  interdisciplinary: [],
  general: [],
}

const stubComponent = { template: '<div><slot /></div>' }

const componentStubs = {
  Dialog: stubComponent,
  Stepper: stubComponent,
  StepList: stubComponent,
  StepPanel: stubComponent,
  StepPanels: stubComponent,
  Step: stubComponent,
  Button: stubComponent,
  Select: stubComponent,
  AutoComplete: stubComponent,
  DatePicker: stubComponent,
  InputText: stubComponent,
  Checkbox: stubComponent,
  FileUpload: stubComponent,
  Divider: stubComponent,
  PdfPreviewModal: stubComponent,
  ProgressSpinner: stubComponent,
}

function mountDialog() {
  return mount(UploadArchiveDialog, {
    props: {
      modelValue: true,
      coursesList: sampleCourses,
    },
    global: {
      stubs: componentStubs,
    },
  })
}

describe('UploadArchiveDialog', () => {
  beforeAll(async () => {
    ensureDomMatrix()
    UploadArchiveDialog = (await import('@/components/UploadArchiveDialog.vue')).default
  })

  beforeEach(() => {
    trackEventMock.mockReset()
    toastAddMock.mockReset()
    archiveServiceMock.uploadArchive.mockResolvedValue()
    courseServiceMock.getCourseArchives.mockResolvedValue({
      data: [{ professor: 'Prof. Lin' }, { professor: 'Prof. Chen' }, { professor: 'Prof. Lin' }],
    })
    isUnauthorizedErrorMock.mockReturnValue(false)
    pdfLoadMock.mockClear()
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    originalURL = globalThis.URL
    globalThis.URL = {
      createObjectURL: vi.fn(() => 'blob:url'),
      revokeObjectURL: vi.fn(),
    }
  })

  afterEach(() => {
    if (consoleErrorSpy) {
      consoleErrorSpy.mockRestore()
    }
    globalThis.URL = originalURL
  })

  it('validates and uploads archive successfully', async () => {
    const wrapper = mountDialog()
    const vm = wrapper.vm

    vm.form.category = 'freshman'
    vm.form.subject = 'Calculus I'
    vm.form.professor = 'Prof. Lin'
    vm.form.filename = 'midterm1'
    vm.form.type = 'midterm'
    vm.form.academicYear = new Date('2023-01-01')

    vm.validateFilename()
    expect(vm.isFilenameValid).toBe(true)

    vm.searchSubject({ query: 'calc' })
    expect(vm.availableSubjects.length).toBe(1)

    vm.onSubjectSelect({ value: { name: 'Calculus I', code: 'c1' } })
    expect(vm.form.subjectId).toBe('c1')

    await vm.fetchProfessorsForSubject('c1')
    expect(courseServiceMock.getCourseArchives).toHaveBeenCalledWith('c1')

    vm.searchProfessor({ query: '' })
    expect(vm.availableProfessors.length).toBe(2)

    vm.searchProfessor({ query: 'lin' })
    expect(vm.availableProfessors.length).toBe(1)

    const fakeFile = {
      name: 'midterm.pdf',
      size: 2048,
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
    }

    vm.form.file = fakeFile

    vm.previewUploadFile()
    expect(vm.showUploadPreview).toBe(true)
    expect(trackEventMock).toHaveBeenCalledWith('preview-archive', expect.any(Object))

    await vm.handleUpload()
    await flushPromises()

    expect(pdfLoadMock).toHaveBeenCalled()
    expect(archiveServiceMock.uploadArchive).toHaveBeenCalled()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'success', summary: '上傳成功' })
    )
    expect(wrapper.emitted('upload-success')).toBeTruthy()

    wrapper.unmount()
  })

  it('covers helper utilities, watchers, and error branches', async () => {
    const wrapper = mountDialog()
    const vm = wrapper.vm

    expect(vm.getCategoryName('freshman')).toBe('大一課程')
    expect(vm.getCategoryName('unknown')).toBe('unknown')
    expect(vm.getTypeName('final')).toBe('期末考')
    expect(vm.formatFileSize(0)).toBe('0 Bytes')
    expect(vm.formatFileSize(2048)).toContain('KB')

    courseServiceMock.getCourseArchives.mockRejectedValueOnce(new Error('fetch error'))
    await vm.fetchProfessorsForSubject('c1')
    expect(vm.uploadFormProfessors).toEqual([])
    courseServiceMock.getCourseArchives.mockResolvedValue({ data: [] })

    vm.uploadFormProfessors = [
      { name: 'Prof. Lin', code: 'Prof. Lin' },
      { name: 'Prof. Chen', code: 'Prof. Chen' },
    ]
    vm.searchProfessor({ query: 'lin' })
    expect(vm.availableProfessors).toEqual([expect.objectContaining({ name: 'Prof. Lin' })])

    vm.onProfessorSelect({ value: 'Prof. Hsu' })
    expect(vm.form.professor).toBeNull()

    vm.onProfessorSelect({ value: { name: 'Prof. Hsu' } })
    expect(vm.form.professor).toBe('Prof. Hsu')

    vm.handleUploadPreviewError()
    expect(vm.uploadPreviewError).toBe(true)

    const clearSpy = vi.fn()
    vm.fileUpload = { clear: clearSpy }
    const file = {
      name: 'calc.pdf',
      size: 100,
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(4)),
    }
    vm.onFileSelect({ files: [file] })
    await flushPromises()
    expect(clearSpy).toHaveBeenCalled()
    expect(vm.form.file).toEqual(file)

    vm.form.category = 'freshman'
    await flushPromises()
    expect(vm.form.subject).toBeNull()

    vm.form.subject = 'Calculus I'
    vm.form.subjectId = 'c1'
    await flushPromises()
    vm.form.subject = null
    await flushPromises()
    expect(vm.uploadFormProfessors).toEqual([])

    vm.fileUpload = { clear: vi.fn() }
    await wrapper.setProps({ modelValue: false })
    await flushPromises()
    expect(vm.form.category).toBeNull()
    expect(vm.uploadStep).toBe('1')

    wrapper.unmount()
  })

  it('handles upload failures and unauthorized responses', async () => {
    const wrapper = mountDialog()
    const vm = wrapper.vm

    Object.assign(vm.form, {
      category: 'freshman',
      subject: 'Calculus I',
      subjectId: 'c1',
      professor: 'Prof. Lin',
      filename: 'midterm1',
      type: 'midterm',
      hasAnswers: true,
      academicYear: new Date('2024-01-01'),
    })

    const failingFile = {
      name: 'midterm.pdf',
      size: 1024,
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
    }
    vm.form.file = failingFile

    archiveServiceMock.uploadArchive.mockRejectedValueOnce(new Error('upload failed'))
    await vm.handleUpload()
    await flushPromises()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '上傳失敗' })
    )

    toastAddMock.mockClear()
    archiveServiceMock.uploadArchive.mockRejectedValueOnce(new Error('unauthorized'))
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    await vm.handleUpload()
    await flushPromises()
    expect(toastAddMock).not.toHaveBeenCalled()
    expect(vm.uploading).toBe(false)

    wrapper.unmount()
  })

  it('manages preview lifecycle, validation, and clearing helpers', () => {
    const wrapper = mountDialog()
    const vm = wrapper.vm

    vm.form.filename = 'InvalidName'
    vm.validateFilename()
    expect(vm.isFilenameValid).toBe(false)

    vm.form.filename = 'validname1'
    vm.validateFilename()
    expect(vm.isFilenameValid).toBe(true)

    vm.form.category = null
    vm.searchSubject({ query: 'calc' })
    expect(vm.availableSubjects).toEqual([])

    vm.form.file = { name: 'archive.pdf', size: 512 }
    globalThis.URL.createObjectURL.mockImplementationOnce(() => {
      throw new Error('preview error')
    })
    vm.previewUploadFile()
    expect(vm.uploadPreviewError).toBe(true)
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '預覽失敗' })
    )

    toastAddMock.mockClear()
    vm.form.file = { name: 'archive.pdf', size: 512 }
    vm.previewUploadFile()
    expect(vm.showUploadPreview).toBe(true)

    vm.closeUploadPreview()
    expect(globalThis.URL.revokeObjectURL).toHaveBeenCalled()
    expect(vm.showUploadPreview).toBe(false)

    const fileUploadClearSpy = vi.fn()
    vm.fileUpload = { clear: fileUploadClearSpy }
    vm.form.file = { name: 'tmp.pdf' }
    const removeSpy = vi.fn()
    vm.clearSelectedFile(removeSpy)
    expect(removeSpy).toHaveBeenCalledWith(0)
    expect(fileUploadClearSpy).toHaveBeenCalled()
    expect(vm.form.file).toBeNull()

    wrapper.unmount()
  })
})
