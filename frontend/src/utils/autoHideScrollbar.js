export function setupAutoHideScrollbars({ idleMs = 1000 } = {}) {
  const timeouts = new WeakMap()

  function markScrolling(target) {
    if (!(target instanceof HTMLElement)) return
    if (target === document.documentElement || target === document.body) return

    const style = window.getComputedStyle(target)
    const overflowY = style.overflowY
    const overflowX = style.overflowX
    const scrollableY =
      (overflowY === 'auto' || overflowY === 'scroll') && target.scrollHeight > target.clientHeight
    const scrollableX =
      (overflowX === 'auto' || overflowX === 'scroll') && target.scrollWidth > target.clientWidth

    if (!scrollableX && !scrollableY) return

    target.dataset.scrollbarScrolling = '1'

    const existing = timeouts.get(target)
    if (existing) window.clearTimeout(existing)

    const timeoutId = window.setTimeout(() => {
      delete target.dataset.scrollbarScrolling
      timeouts.delete(target)
    }, idleMs)

    timeouts.set(target, timeoutId)
  }

  const onScroll = (e) => {
    markScrolling(e.target)
  }

  window.addEventListener('scroll', onScroll, { capture: true, passive: true })

  return () => {
    window.removeEventListener('scroll', onScroll, { capture: true })
    for (const timeoutId of timeouts.values()) window.clearTimeout(timeoutId)
  }
}
