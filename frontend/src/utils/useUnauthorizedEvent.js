import { onMounted, onBeforeUnmount } from 'vue'

export function useUnauthorizedEvent(handler) {
  onMounted(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('app:unauthorized', handler)
    }
  })

  onBeforeUnmount(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('app:unauthorized', handler)
    }
  })
}
