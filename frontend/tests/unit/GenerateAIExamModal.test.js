import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import GenerateAIExamModal from '@/components/GenerateAIExamModal.vue'

const trackEventMock = vi.hoisted(() => vi.fn())
const toastAddMock = vi.hoisted(() => vi.fn())
const confirmRequireMock = vi.hoisted(() => vi.fn((options) => options.accept && options.accept()))
const unauthorizedHandlers = vi.hoisted(() => [])
const clipboardWriteMock = vi.hoisted(() => vi.fn())
const isUnauthorizedErrorMock = vi.hoisted(() => vi.fn(() => false))
const webSocketInstances = vi.hoisted(() => [])
let originalClipboard
let originalWebSocket
let consoleErrorSpy

const coursesList = {
  freshman: [
    { id: 'course-1', name: 'Calculus I' },
    { id: 'course-2', name: 'Physics' },
  ],
}

const archiveResponse = {
  data: [
    {
      id: 'arch-1',
      archive_type: 'midterm',
      academic_year: '2023',
      name: 'Midterm',
      professor: 'Prof. Lin',
    },
    {
      id: 'arch-2',
      archive_type: 'final',
      academic_year: '2022',
      name: 'Final',
      professor: 'Prof. Lin',
    },
    {
      id: 'arch-3',
      archive_type: 'midterm',
      academic_year: '2021',
      name: 'Quiz',
      professor: 'Prof. Chen',
    },
  ],
}

const taskResult = {
  status: 'complete',
  result: {
    generated_content: 'Mock exam content',
    archives_used: archiveResponse.data,
  },
}

const aiExamServiceMock = vi.hoisted(() => ({
  getApiKeyStatus: vi.fn(),
  generateMockExam: vi.fn(),
  openTaskStatusWebSocket: vi.fn(
    (taskId) => new WebSocket(`ws://localhost/api/ai-exam/ws/task/${taskId}`)
  ),
  updateApiKey: vi.fn(),
  clearApiKey: vi.fn(),
}))

const courseServiceMock = vi.hoisted(() => ({
  getCourseArchives: vi.fn(),
}))

const archiveServiceMock = vi.hoisted(() => ({
  getArchivePreviewUrl: vi.fn(),
  getArchiveDownloadUrl: vi.fn(),
}))

vi.mock('@/api', () => ({
  aiExamService: aiExamServiceMock,
  courseService: courseServiceMock,
  archiveService: archiveServiceMock,
}))

vi.mock('@/utils/analytics', () => ({
  trackEvent: trackEventMock,
  EVENTS: {
    GENERATE_AI_EXAM: 'generate-ai-exam',
  },
}))

vi.mock('@/utils/useUnauthorizedEvent.js', () => ({
  useUnauthorizedEvent: (handler) => unauthorizedHandlers.push(handler),
}))

vi.mock('@/utils/http', () => ({
  isUnauthorizedError: isUnauthorizedErrorMock,
}))

const stubComponent = { template: '<div><slot /></div>' }
const pdfPreviewStub = {
  template: '<div class="pdf-preview-stub" :data-show-discussion="String(showDiscussion)"></div>',
  props: ['showDiscussion'],
}

function mountModal() {
  return mount(GenerateAIExamModal, {
    props: {
      visible: false,
      coursesList,
    },
    global: {
      stubs: {
        Dialog: stubComponent,
        ProgressSpinner: stubComponent,
        Select: stubComponent,
        Checkbox: stubComponent,
        Button: stubComponent,
        Stepper: stubComponent,
        StepList: stubComponent,
        Step: stubComponent,
        StepPanels: stubComponent,
        StepPanel: stubComponent,
        AutoComplete: stubComponent,
        DatePicker: stubComponent,
        InputText: stubComponent,
        FileUpload: stubComponent,
        Divider: stubComponent,
        PdfPreviewModal: pdfPreviewStub,
        Password: stubComponent,
      },
      provide: {
        toast: { add: toastAddMock },
        confirm: { require: confirmRequireMock },
      },
    },
  })
}

describe('GenerateAIExamModal', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    unauthorizedHandlers.length = 0
    webSocketInstances.length = 0
    if (typeof navigator === 'undefined') {
      globalThis.navigator = { clipboard: { writeText: clipboardWriteMock } }
      originalClipboard = undefined
    } else {
      originalClipboard = navigator.clipboard
      navigator.clipboard = { writeText: clipboardWriteMock }
    }
    clipboardWriteMock.mockReset()
    clipboardWriteMock.mockResolvedValue()
    aiExamServiceMock.getApiKeyStatus.mockResolvedValue({ data: { has_api_key: false } })
    aiExamServiceMock.generateMockExam.mockResolvedValue({ data: { task_id: 'task-1' } })
    aiExamServiceMock.updateApiKey.mockResolvedValue({ data: { has_api_key: true } })
    aiExamServiceMock.clearApiKey.mockResolvedValue({})
    courseServiceMock.getCourseArchives.mockResolvedValue(archiveResponse)
    trackEventMock.mockReset()
    toastAddMock.mockReset()
    confirmRequireMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValue(false)
    localStorage.clear()

    originalWebSocket = globalThis.WebSocket
    globalThis.WebSocket = vi.fn(function WebSocket(url) {
      const socket = {
        url,
        onmessage: null,
        onerror: null,
        onclose: null,
        close: vi.fn(() => {
          socket.onclose?.()
        }),
        emitMessage(data) {
          socket.onmessage?.({ data: JSON.stringify(data) })
        },
        emitError() {
          socket.onerror?.()
        },
      }
      webSocketInstances.push(socket)
      return socket
    })
  })

  afterEach(() => {
    vi.useRealTimers()
    if (consoleErrorSpy) {
      consoleErrorSpy.mockRestore()
    }
    if (typeof navigator !== 'undefined') {
      navigator.clipboard = originalClipboard
    }
    globalThis.WebSocket = originalWebSocket
  })

  it('handles archive selection and task persistence helpers', async () => {
    const wrapper = mountModal()
    const vm = wrapper.vm

    await wrapper.setProps({ visible: true })
    await flushPromises()
    expect(vm.currentStep).toBe('selectProfessor')
    expect(vm.showApiKeyModal).toBe(true)

    vm.resetToSelect()
    expect(vm.currentStep).toBe('selectProfessor')

    vm.form.category = 'freshman'
    vm.form.course_name = 'Calculus I'
    await vm.onCourseChange()
    await flushPromises()
    expect(courseServiceMock.getCourseArchives).toHaveBeenCalledWith('course-1')

    vm.availableArchives = archiveResponse.data
    vm.toggleArchiveSelection('arch-1')
    vm.toggleArchiveSelection('arch-2')
    vm.toggleArchiveSelection('arch-3')
    expect(vm.selectedArchiveIds).toEqual(['arch-1', 'arch-2', 'arch-3'])
    expect(vm.isArchiveDisabled('arch-4')).toBe(true)

    vm.saveTaskToStorage('task-1', { course_name: 'Calculus I' })
    const stored = vm.loadTaskFromStorage()
    expect(stored.taskId).toBe('task-1')
    vm.clearTaskFromStorage()
    expect(vm.loadTaskFromStorage()).toBeNull()

    vm.result = {
      generated_content: 'Generated text',
      archives_used: archiveResponse.data,
    }
    await vm.copyContent()
    expect(clipboardWriteMock).toHaveBeenCalledWith('Generated text')

    vm.apiKeyForm.key = 'test-key'
    await vm.saveApiKey()
    expect(aiExamServiceMock.updateApiKey).toHaveBeenCalledWith('test-key')

    vm.apiKeyForm.key = ''
    await vm.clearApiKey()
    expect(aiExamServiceMock.updateApiKey).toHaveBeenCalledWith('')

    unauthorizedHandlers.forEach((handler) => handler())
    expect(wrapper.emitted('update:visible')).toBeTruthy()

    wrapper.unmount()
  })

  it('manages API key modal lifecycle and handles errors', async () => {
    aiExamServiceMock.getApiKeyStatus.mockResolvedValue({ data: { has_api_key: true } })
    const wrapper = mountModal()
    const vm = wrapper.vm

    await wrapper.setProps({ visible: true })
    await flushPromises()
    expect(vm.showApiKeyModal).toBe(false)

    aiExamServiceMock.getApiKeyStatus.mockResolvedValue({ data: { has_api_key: true } })
    await vm.openApiKeyModal()
    expect(vm.showApiKeyModal).toBe(true)
    expect(aiExamServiceMock.getApiKeyStatus).toHaveBeenCalled()

    vm.apiKeyForm.key = 'valid-key'
    aiExamServiceMock.updateApiKey.mockRejectedValueOnce(new Error('save failed'))
    await vm.saveApiKey()
    await flushPromises()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '設定失敗' })
    )

    toastAddMock.mockClear()
    vm.apiKeyForm.key = 'valid-key'
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    aiExamServiceMock.updateApiKey.mockRejectedValueOnce(new Error('unauthorized'))
    await vm.saveApiKey()
    await flushPromises()
    expect(toastAddMock).not.toHaveBeenCalled()

    toastAddMock.mockClear()
    aiExamServiceMock.updateApiKey.mockRejectedValueOnce(new Error('clear failed'))
    await vm.clearApiKey()
    await flushPromises()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '移除失敗' })
    )

    toastAddMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    aiExamServiceMock.updateApiKey.mockRejectedValueOnce(new Error('unauthorized clear'))
    await vm.clearApiKey()
    await flushPromises()
    expect(toastAddMock).not.toHaveBeenCalled()

    vm.apiKeyStatus.has_api_key = false
    vm.handleApiKeyModalClose(false)
    expect(wrapper.emitted('update:visible')).toBeTruthy()

    aiExamServiceMock.getApiKeyStatus.mockRejectedValueOnce(new Error('status failed'))
    toastAddMock.mockClear()
    await vm.openApiKeyModal()
    await flushPromises()
    expect(vm.showApiKeyModal).toBe(true)

    wrapper.unmount()
  })

  it('disables discussion panel in archive preview modal', async () => {
    const wrapper = mountModal()
    const vm = wrapper.vm

    vm.selectedCourseId = 'course-1'
    vm.archivePreviewMeta = {
      archiveId: 'arch-1',
      title: 'Midterm',
      academicYear: '2023',
      archiveType: 'midterm',
      courseName: 'Calculus I',
      professorName: 'Prof. Lin',
    }
    vm.archivePreviewUrl = 'https://example.com/preview.pdf'
    vm.showArchivePreview = true

    await flushPromises()

    const preview = wrapper.find('.pdf-preview-stub')
    expect(preview.exists()).toBe(true)
    expect(preview.attributes('data-show-discussion')).toBe('false')
    wrapper.unmount()
  })

  it('handles course and archive selection edge cases', async () => {
    const wrapper = mountModal()
    const vm = wrapper.vm

    await wrapper.setProps({ visible: true })
    await flushPromises()

    toastAddMock.mockClear()
    vm.form.category = 'freshman'
    vm.form.course_name = 'Calculus I'

    courseServiceMock.getCourseArchives.mockRejectedValueOnce(new Error('prof fetch failed'))
    await vm.onCourseChange()
    await flushPromises()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '載入失敗' })
    )

    toastAddMock.mockClear()
    vm.form.course_name = 'Calculus I'
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    courseServiceMock.getCourseArchives.mockRejectedValueOnce(new Error('unauthorized'))
    await vm.onCourseChange()
    await flushPromises()
    expect(toastAddMock).not.toHaveBeenCalled()

    toastAddMock.mockClear()
    vm.form.professor = 'Prof. Lin'
    courseServiceMock.getCourseArchives.mockResolvedValueOnce({ data: [] })
    await vm.goToArchiveSelection()
    await flushPromises()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'warning', summary: '找不到考古題' })
    )

    toastAddMock.mockClear()
    vm.form.professor = 'Prof. Lin'
    courseServiceMock.getCourseArchives.mockResolvedValueOnce({
      data: [
        { id: 'quiz-only', archive_type: 'quiz', professor: 'Prof. Lin', academic_year: '2020' },
      ],
    })
    await vm.goToArchiveSelection()
    await flushPromises()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '找不到考古題' })
    )

    toastAddMock.mockClear()
    vm.form.professor = 'Prof. Lin'
    courseServiceMock.getCourseArchives.mockResolvedValueOnce({
      data: [
        {
          id: 'valid-1',
          archive_type: 'midterm',
          professor: 'Prof. Lin',
          academic_year: '2023',
          name: 'Midterm',
        },
      ],
    })
    await vm.goToArchiveSelection()
    await flushPromises()
    expect(vm.currentStep).toBe('selectArchives')

    toastAddMock.mockClear()
    vm.form.professor = 'Prof. Lin'
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    courseServiceMock.getCourseArchives.mockRejectedValueOnce(new Error('unauthorized archive'))
    await vm.goToArchiveSelection()
    await flushPromises()
    expect(toastAddMock).not.toHaveBeenCalled()

    toastAddMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValueOnce(false)
    courseServiceMock.getCourseArchives.mockRejectedValueOnce(new Error('archive failure'))
    await vm.goToArchiveSelection()
    await flushPromises()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '載入失敗' })
    )

    wrapper.unmount()
  })

  it('handles task lifecycle, downloads, and regeneration helpers', async () => {
    const appendSpy = vi.spyOn(document.body, 'appendChild')
    const removeSpy = vi.spyOn(document.body, 'removeChild')
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    const objectUrlSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock')
    const revokeSpy = vi.spyOn(URL, 'revokeObjectURL').mockReturnValue()

    const wrapper = mountModal()
    const vm = wrapper.vm

    await wrapper.setProps({ visible: true })
    await flushPromises()

    vm.currentStep = 'selectArchives'
    vm.selectedArchiveIds = ['arch-1']
    vm.form.category = 'freshman'
    vm.form.course_name = 'Calculus I'
    vm.form.professor = 'Prof. Lin'

    aiExamServiceMock.generateMockExam.mockResolvedValueOnce({ data: { task_id: 'task-42' } })

    await vm.generateExam()
    await flushPromises()
    expect(webSocketInstances.length).toBe(1)
    const socket = webSocketInstances[0]
    expect(socket.url).toContain('ai-exam/ws/task/task-42')

    socket.emitMessage({ task_id: 'task-42', status: 'pending' })
    await flushPromises()
    expect(vm.currentStep).toBe('generating')

    socket.emitMessage({ task_id: 'task-42', ...taskResult })
    await flushPromises()

    expect(vm.currentStep).toBe('result')
    expect(trackEventMock).toHaveBeenCalledWith('generate-ai-exam', expect.any(Object))

    vm.result = taskResult.result
    await vm.downloadResult()
    expect(objectUrlSpy).toHaveBeenCalled()
    expect(appendSpy).toHaveBeenCalled()
    expect(clickSpy).toHaveBeenCalled()
    expect(revokeSpy).toHaveBeenCalledWith('blob:mock')

    vm.confirmRegenerate()
    expect(confirmRequireMock).toHaveBeenCalled()
    expect(vm.currentStep).toBe('selectProfessor')

    vm.selectedArchiveIds = ['arch-1']
    vm.form.professor = 'Prof. Lin'
    vm.currentStep = 'selectArchives'
    aiExamServiceMock.generateMockExam.mockRejectedValueOnce({
      response: { status: 409 },
    })
    await vm.generateExam()
    await flushPromises()
    expect(vm.currentStep).toBe('error')

    toastAddMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValueOnce(true)
    aiExamServiceMock.generateMockExam.mockRejectedValueOnce(new Error('unauthorized create'))
    await vm.generateExam()
    await flushPromises()
    expect(toastAddMock).not.toHaveBeenCalled()

    toastAddMock.mockClear()
    aiExamServiceMock.generateMockExam.mockRejectedValueOnce(new Error('submission failed'))
    await vm.generateExam()
    await flushPromises()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '提交失敗' })
    )

    vm.selectedArchiveIds = ['arch-1']
    vm.currentStep = 'selectArchives'
    aiExamServiceMock.generateMockExam.mockResolvedValueOnce({ data: { task_id: 'task-fail' } })
    await vm.generateExam()
    await flushPromises()
    expect(webSocketInstances.length).toBe(2)
    webSocketInstances[1].emitMessage({ task_id: 'task-fail', status: 'failed' })
    await flushPromises()
    expect(vm.currentStep).toBe('error')

    vm.selectedArchiveIds = ['arch-1']
    vm.currentStep = 'selectArchives'
    aiExamServiceMock.generateMockExam.mockResolvedValueOnce({ data: { task_id: 'task-error' } })
    await vm.generateExam()
    await flushPromises()
    expect(webSocketInstances.length).toBe(3)
    webSocketInstances[2].emitError()
    await flushPromises()
    expect(vm.currentStep).toBe('error')

    wrapper.unmount()
    appendSpy.mockRestore()
    removeSpy.mockRestore()
    clickSpy.mockRestore()
    objectUrlSpy.mockRestore()
    revokeSpy.mockRestore()
  })

  it('resumes saved tasks and resets state on close', async () => {
    const wrapper = mountModal()
    const vm = wrapper.vm

    vm.saveTaskToStorage('task-resume', {
      course_name: 'Calculus I',
      professor: 'Prof. Lin',
    })

    await wrapper.setProps({ visible: true })
    await flushPromises()
    expect(webSocketInstances.length).toBe(1)
    webSocketInstances[0].emitMessage({ task_id: 'task-resume', ...taskResult })
    await flushPromises()
    expect(vm.currentStep).toBe('result')

    await wrapper.setProps({ visible: false })
    await flushPromises()
    vi.advanceTimersByTime(300)
    expect(vm.form.category).toBeNull()
    expect(vm.availableProfessors).toEqual([])

    vm.saveTaskToStorage('task-resume-failed', {
      course_name: 'Calculus I',
      professor: 'Prof. Lin',
    })
    await wrapper.setProps({ visible: true })
    await flushPromises()
    expect(webSocketInstances.length).toBe(2)
    webSocketInstances[1].emitMessage({ task_id: 'task-resume-failed', status: 'failed' })
    await flushPromises()
    expect(vm.currentStep).toBe('error')

    wrapper.unmount()
  })

  it('covers clipboard errors and API key utilities', async () => {
    const objectUrlSpy = vi.spyOn(URL, 'createObjectURL')
    const wrapper = mountModal()
    const vm = wrapper.vm

    await wrapper.setProps({ visible: true })
    await flushPromises()

    // verify early return when no content for download
    vm.result = null
    vm.downloadResult()
    expect(objectUrlSpy).not.toHaveBeenCalled()

    vm.result = {
      generated_content: 'content',
    }
    clipboardWriteMock.mockRejectedValueOnce(new Error('copy fail'))
    toastAddMock.mockClear()
    await vm.copyContent()
    expect(toastAddMock).toHaveBeenCalledWith(
      expect.objectContaining({ severity: 'error', summary: '複製失敗' })
    )

    // ensure saveApiKey trims and bails when empty
    toastAddMock.mockClear()
    aiExamServiceMock.updateApiKey.mockClear()
    vm.apiKeyForm.key = '   '
    await vm.saveApiKey()
    expect(aiExamServiceMock.updateApiKey).not.toHaveBeenCalled()

    // load api key status failure branch
    aiExamServiceMock.getApiKeyStatus.mockRejectedValueOnce(new Error('status fail'))
    await vm.loadApiKeyStatus()
    aiExamServiceMock.getApiKeyStatus.mockResolvedValue({ data: { has_api_key: true } })

    // handle modal close when API key already configured
    vm.apiKeyStatus.has_api_key = true
    const emittedBefore = wrapper.emitted('update:visible')?.length || 0
    vm.handleApiKeyModalClose(false)
    const emittedAfter = wrapper.emitted('update:visible')?.length || 0
    expect(emittedAfter).toBe(emittedBefore)

    // open API key modal fallback path
    aiExamServiceMock.getApiKeyStatus.mockRejectedValueOnce(new Error('modal fail'))
    await vm.openApiKeyModal()
    expect(vm.showApiKeyModal).toBe(true)

    objectUrlSpy.mockRestore()
    wrapper.unmount()
  })

  it('resets selection state helpers and closes modals correctly', async () => {
    const wrapper = mountModal()
    const vm = wrapper.vm

    await wrapper.setProps({ visible: true })
    await flushPromises()

    vm.form.category = 'freshman'
    vm.form.course_name = 'Calculus I'
    vm.form.professor = 'Prof. Lin'
    vm.availableArchives = [{ id: 'arch-1', archive_type: 'midterm' }]
    vm.selectedArchiveIds = ['arch-1']
    vm.archiveTypeFilter = 'midterm'

    vm.goBackToProfessorSelection()
    expect(vm.currentStep).toBe('selectProfessor')
    expect(vm.selectedArchiveIds).toEqual([])
    expect(vm.archiveTypeFilter).toBeNull()

    vm.form.category = 'freshman'
    vm.form.course_name = 'Calculus I'
    vm.form.professor = 'Prof. Lin'
    vm.availableArchives = [{ id: 'arch-1', archive_type: 'midterm' }]
    vm.selectedArchiveIds = ['arch-1']

    vm.onCategoryChange()
    expect(vm.form.course_name).toBeNull()
    expect(vm.form.professor).toBeNull()
    expect(vm.availableArchives).toEqual([])
    expect(vm.selectedArchiveIds).toEqual([])

    vm.form.course_name = 'Calculus I'
    vm.availableArchives = [{ id: 'arch-2', archive_type: 'final' }]
    vm.selectedArchiveIds = ['arch-2']

    vm.onProfessorChange()
    expect(vm.availableArchives).toEqual([])
    expect(vm.selectedArchiveIds).toEqual([])

    vm.showApiKeyModal = true
    vm.apiKeyStatus.has_api_key = false
    const emittedBefore = wrapper.emitted('update:visible')?.length || 0
    vm.handleApiKeyModalClose(false)
    const emittedAfter = wrapper.emitted('update:visible')?.length || 0
    expect(emittedAfter).toBe(emittedBefore + 1)
    expect(vm.showApiKeyModal).toBe(false)

    wrapper.unmount()
  })
})
