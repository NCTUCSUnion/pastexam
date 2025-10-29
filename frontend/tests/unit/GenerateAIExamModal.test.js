import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import GenerateAIExamModal from '@/components/GenerateAIExamModal.vue'

const trackEventMock = vi.hoisted(() => vi.fn())
const toastAddMock = vi.hoisted(() => vi.fn())
const confirmRequireMock = vi.hoisted(() => vi.fn((options) => options.accept && options.accept()))
const unauthorizedHandlers = vi.hoisted(() => [])
const clipboardWriteMock = vi.hoisted(() => vi.fn())
const isUnauthorizedErrorMock = vi.hoisted(() => vi.fn(() => false))
let originalClipboard
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
  getTaskStatus: vi.fn(),
  updateApiKey: vi.fn(),
  clearApiKey: vi.fn(),
}))

const courseServiceMock = vi.hoisted(() => ({
  getCourseArchives: vi.fn(),
}))

vi.mock('@/api', () => ({
  aiExamService: aiExamServiceMock,
  courseService: courseServiceMock,
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
        PdfPreviewModal: stubComponent,
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
    aiExamServiceMock.getTaskStatus.mockResolvedValue({ data: taskResult })
    aiExamServiceMock.updateApiKey.mockResolvedValue({ data: { has_api_key: true } })
    aiExamServiceMock.clearApiKey.mockResolvedValue({})
    courseServiceMock.getCourseArchives.mockResolvedValue(archiveResponse)
    trackEventMock.mockReset()
    toastAddMock.mockReset()
    confirmRequireMock.mockClear()
    isUnauthorizedErrorMock.mockReturnValue(false)
    localStorage.clear()
  })

  afterEach(() => {
    vi.useRealTimers()
    if (consoleErrorSpy) {
      consoleErrorSpy.mockRestore()
    }
    if (typeof navigator !== 'undefined') {
      navigator.clipboard = originalClipboard
    }
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

  it('handles task lifecycle, polling, downloads, and regeneration helpers', async () => {
    const appendSpy = vi.spyOn(document.body, 'appendChild')
    const removeSpy = vi.spyOn(document.body, 'removeChild')
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
    const objectUrlSpy = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock')
    const revokeSpy = vi.spyOn(URL, 'revokeObjectURL').mockReturnValue()
    let intervalFn
    const setIntervalSpy = vi.spyOn(globalThis, 'setInterval').mockImplementation((fn) => {
      intervalFn = fn
      return 1
    })
    const clearIntervalSpy = vi.spyOn(globalThis, 'clearInterval').mockImplementation(() => {
      intervalFn = null
    })

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
    aiExamServiceMock.getTaskStatus.mockResolvedValueOnce({ data: { status: 'pending' } })
    aiExamServiceMock.getTaskStatus.mockResolvedValueOnce({ data: { status: 'in_progress' } })
    aiExamServiceMock.getTaskStatus.mockResolvedValueOnce({ data: taskResult })

    await vm.generateExam()
    await flushPromises()
    const firstPoll = intervalFn
    expect(typeof firstPoll).toBe('function')
    await firstPoll()
    await flushPromises()
    await firstPoll()
    await flushPromises()
    await firstPoll()
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
    aiExamServiceMock.getTaskStatus.mockResolvedValueOnce({ data: { status: 'failed' } })
    await vm.generateExam()
    await flushPromises()
    const failPoll = intervalFn
    expect(typeof failPoll).toBe('function')
    await failPoll()
    await flushPromises()
    expect(vm.currentStep).toBe('error')

    vm.selectedArchiveIds = ['arch-1']
    vm.currentStep = 'selectArchives'
    aiExamServiceMock.generateMockExam.mockResolvedValueOnce({ data: { task_id: 'task-error' } })
    aiExamServiceMock.getTaskStatus.mockRejectedValueOnce(new Error('poll error'))
    await vm.generateExam()
    await flushPromises()
    const errorPoll = intervalFn
    expect(typeof errorPoll).toBe('function')
    await errorPoll()
    await flushPromises()
    expect(vm.currentStep).toBe('error')

    wrapper.unmount()
    appendSpy.mockRestore()
    removeSpy.mockRestore()
    clickSpy.mockRestore()
    objectUrlSpy.mockRestore()
    revokeSpy.mockRestore()
    setIntervalSpy.mockRestore()
    clearIntervalSpy.mockRestore()
  })

  it('resumes saved tasks and resets state on close', async () => {
    const wrapper = mountModal()
    const vm = wrapper.vm

    let intervalFn
    const setIntervalSpy = vi.spyOn(globalThis, 'setInterval').mockImplementation((fn) => {
      intervalFn = fn
      return 1
    })
    const clearIntervalSpy = vi.spyOn(globalThis, 'clearInterval').mockImplementation(() => {
      intervalFn = null
    })

    vm.saveTaskToStorage('task-resume', {
      course_name: 'Calculus I',
      professor: 'Prof. Lin',
    })

    aiExamServiceMock.getTaskStatus.mockResolvedValueOnce({
      data: {
        status: 'pending',
        result: null,
      },
    })
    aiExamServiceMock.getTaskStatus.mockResolvedValueOnce({ data: taskResult })

    await wrapper.setProps({ visible: true })
    await flushPromises()
    const resumePoll = intervalFn
    expect(typeof resumePoll).toBe('function')
    await resumePoll()
    await flushPromises()
    await resumePoll()
    await flushPromises()
    expect(vm.currentStep).toBe('result')

    await wrapper.setProps({ visible: false })
    await flushPromises()
    vi.advanceTimersByTime(300)
    expect(vm.form.category).toBeNull()
    expect(vm.availableProfessors).toEqual([])

    aiExamServiceMock.getTaskStatus.mockResolvedValueOnce({ data: { status: 'failed' } })
    await wrapper.setProps({ visible: true })
    await flushPromises()
    expect(vm.currentStep).toBe('selectProfessor')

    aiExamServiceMock.getTaskStatus.mockRejectedValueOnce(new Error('resume error'))
    await wrapper.setProps({ visible: true })
    await flushPromises()
    expect(vm.currentStep).toBe('selectProfessor')

    wrapper.unmount()
    setIntervalSpy.mockRestore()
    clearIntervalSpy.mockRestore()
  })
})
