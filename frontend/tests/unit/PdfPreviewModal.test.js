import { describe, it, expect, vi, beforeEach, afterEach, beforeAll } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref, nextTick } from 'vue'

const unauthorizedCallbacks = vi.hoisted(() => [])
let consoleErrorSpy
let PdfPreviewModal
const pdfState = {
  pdfRef: ref(null),
  pagesRef: ref([]),
}

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

vi.mock('@/utils/useUnauthorizedEvent.js', () => ({
  useUnauthorizedEvent: (handler) => {
    unauthorizedCallbacks.push(handler)
  },
}))

vi.mock('@tato30/vue-pdf', () => {
  const { pdfRef, pagesRef } = pdfState
  return {
    __esModule: true,
    VuePDF: { template: '<div class="vue-pdf"></div>' },
    usePDF: vi.fn(() => ({
      pdf: pdfRef,
      pages: pagesRef,
    })),
  }
})

const stubComponent = { template: '<div><slot /></div>' }

describe('PdfPreviewModal', () => {
  beforeAll(async () => {
    ensureDomMatrix()
    PdfPreviewModal = (await import('@/components/PdfPreviewModal.vue')).default
  })

  beforeEach(() => {
    unauthorizedCallbacks.length = 0
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    pdfState.pdfRef.value = null
    pdfState.pagesRef.value = [1, 2]
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('handles pdf events and download workflow', async () => {
    const wrapper = mount(PdfPreviewModal, {
      props: {
        visible: true,
        previewUrl: '',
      },
      global: {
        stubs: {
          Dialog: stubComponent,
          ProgressSpinner: stubComponent,
          Button: stubComponent,
          VuePdfEmbed: stubComponent,
        },
      },
    })

    const vm = wrapper.vm

    vm.handlePdfError(new Error('failed'))
    expect(vm.pdfError).toBe(true)
    expect(wrapper.emitted('error')).toBeTruthy()

    vm.handlePdfLoaded()
    expect(vm.pdfError).toBe(false)
    expect(wrapper.emitted('load')).toBeTruthy()

    vm.onHide()
    expect(wrapper.emitted('hide')).toBeTruthy()

    vm.handleDownload()
    expect(vm.downloading).toBe(true)
    const downloadEmit = wrapper.emitted('download')
    expect(downloadEmit).toBeTruthy()
    const complete = downloadEmit[0][0]
    complete()
    expect(vm.downloading).toBe(false)

    unauthorizedCallbacks.forEach((cb) => cb())
    expect(wrapper.emitted('update:visible')).toBeTruthy()

    wrapper.unmount()
  })

  it('handles loading lifecycle for pdf task', async () => {
    const wrapper = mount(PdfPreviewModal, {
      props: {
        visible: true,
        previewUrl: 'https://example.com/file.pdf',
      },
      global: {
        stubs: {
          Dialog: stubComponent,
          ProgressSpinner: stubComponent,
          Button: stubComponent,
        },
      },
    })

    // trigger load with url and expect loading
    await wrapper.setProps({ previewUrl: 'https://example.com/file.pdf' })

    // simulate pdf loading task success
    let resolveTask
    const resolvePromise = new Promise((res) => {
      resolveTask = res
    })
    pdfState.pdfRef.value = { promise: resolvePromise }
    await nextTick()
    expect(wrapper.vm.pdfLoading).toBe(true)
    resolveTask()
    await flushPromises()
    expect(wrapper.vm.pdfLoading).toBe(false)
    expect(wrapper.vm.pdfError).toBe(false)

    // simulate a new task that fails after swapping preview URL
    const rejectPromise = Promise.reject(new Error('load failed'))
    pdfState.pdfRef.value = { promise: rejectPromise }
    await Promise.resolve() // allow watch to run
    await rejectPromise.catch(() => {})
    await flushPromises()
    expect(wrapper.vm.pdfError).toBe(true)
    expect(wrapper.emitted('error')).toBeTruthy()

    // clear url resets loading/error
    await wrapper.setProps({ previewUrl: '' })
    await nextTick()
    expect(wrapper.vm.pdfLoading).toBe(false)
    expect(wrapper.vm.pdfError).toBe(false)

    wrapper.unmount()
  })

  it('can disable discussion panel explicitly', async () => {
    const wrapper = mount(PdfPreviewModal, {
      props: {
        visible: true,
        previewUrl: '',
        courseId: 1,
        archiveId: 2,
        showDiscussion: false,
      },
      global: {
        stubs: {
          Dialog: stubComponent,
          ProgressSpinner: stubComponent,
          Button: stubComponent,
          ArchiveDiscussionPanel: { template: '<div class="discussion-panel-stub"></div>' },
        },
      },
    })

    expect(wrapper.find('.discussion-panel-stub').exists()).toBe(false)
    wrapper.unmount()
  })

  it('renders discussion panel when enabled and ids present', async () => {
    const wrapper = mount(PdfPreviewModal, {
      props: {
        visible: true,
        previewUrl: '',
        courseId: 1,
        archiveId: 2,
        showDiscussion: true,
      },
      global: {
        stubs: {
          Dialog: stubComponent,
          ProgressSpinner: stubComponent,
          Button: stubComponent,
          ArchiveDiscussionPanel: { template: '<div class="discussion-panel-stub"></div>' },
        },
      },
    })

    expect(wrapper.find('.discussion-panel-stub').exists()).toBe(true)
    wrapper.unmount()
  })
})
