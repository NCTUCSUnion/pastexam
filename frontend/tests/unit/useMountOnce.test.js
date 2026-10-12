import { describe, expect, it } from 'vitest'
import { nextTick, ref } from 'vue'
import { useMountOnce } from '@/utils/useMountOnce'

describe('useMountOnce', () => {
  it('stays false until the source is first truthy', async () => {
    const visible = ref(false)
    const mounted = useMountOnce(visible)
    expect(mounted.value).toBe(false)

    visible.value = true
    await nextTick()
    expect(mounted.value).toBe(true)
  })

  it('stays true after the source turns falsy again', async () => {
    const visible = ref(true)
    const mounted = useMountOnce(visible)
    expect(mounted.value).toBe(true)

    visible.value = false
    await nextTick()
    expect(mounted.value).toBe(true)
  })
})
