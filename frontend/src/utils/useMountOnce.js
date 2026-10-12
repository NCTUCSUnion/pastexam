import { ref, watch } from 'vue'

// Becomes true the first time `source` is truthy and stays true, so a lazily loaded
// component is only fetched when first opened but keeps its state (and close animation) afterwards.
export function useMountOnce(source) {
  const mounted = ref(false)
  watch(
    source,
    (value) => {
      if (value) mounted.value = true
    },
    { immediate: true }
  )
  return mounted
}
