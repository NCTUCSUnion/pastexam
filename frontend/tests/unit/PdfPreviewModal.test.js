import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import PdfPreviewModal from '@/components/PdfPreviewModal.vue'

const unauthorizedCallbacks = vi.hoisted(() => [])
let consoleErrorSpy

vi.mock('@/utils/useUnauthorizedEvent.js', () => ({
  useUnauthorizedEvent: (handler) => {
    unauthorizedCallbacks.push(handler)
  },
}))

const stubComponent = { template: '<div><slot /></div>' }

describe('PdfPreviewModal', () => {
  beforeEach(() => {
    unauthorizedCallbacks.length = 0
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('handles pdf events and download workflow', async () => {
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
})
