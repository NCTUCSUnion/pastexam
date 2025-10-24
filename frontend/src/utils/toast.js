let globalToastInstance = null

export function setGlobalToast(toast) {
  globalToastInstance = toast
}

export function getGlobalToast() {
  return globalToastInstance
}
