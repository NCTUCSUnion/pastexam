import axios from 'axios'
import router from '../../router'
import { getGlobalToast } from '../../utils/toast'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
let unauthorizedToastActive = false
let unauthorizedToastTimer = null

export const api = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
})

export const buildWebSocketUrl = (path, { baseURL, queryParams = {} } = {}) => {
  const base =
    baseURL ||
    api?.defaults?.baseURL ||
    apiBaseUrl ||
    (typeof window !== 'undefined' ? `${window.location.origin}/api` : null)
  if (!base) return null

  let resolvedBase
  try {
    resolvedBase = new URL(base, typeof window !== 'undefined' ? window.location.origin : undefined)
  } catch {
    return null
  }

  if (resolvedBase.pathname === '/') {
    resolvedBase.pathname = '/api/'
  }

  if (!resolvedBase.pathname.endsWith('/')) {
    resolvedBase.pathname = `${resolvedBase.pathname}/`
  }

  resolvedBase.protocol = resolvedBase.protocol === 'https:' ? 'wss:' : 'ws:'

  const normalizedPath = String(path || '').replace(/^\//, '')
  const wsUrl = new URL(normalizedPath, resolvedBase)

  Object.entries(queryParams || {}).forEach(([key, value]) => {
    if (value === undefined || value === null) return
    const str = String(value)
    if (!str) return
    wsUrl.searchParams.set(key, str)
  })

  return wsUrl.toString()
}

api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const requestUrl = error.config?.url || ''
    const method = (error.config?.method || '').toLowerCase()
    const isLoginRequest = status === 401 && method === 'post' && requestUrl.includes('/auth/login')

    if (isLoginRequest) {
      error.isInvalidCredentials = true
      return Promise.reject(error)
    }

    if (status === 401) {
      sessionStorage.removeItem('authToken')
      error.isUnauthorized = true

      const toast = getGlobalToast()
      if (toast) {
        if (!unauthorizedToastActive) {
          unauthorizedToastActive = true
          toast.add({
            severity: 'warn',
            summary: '登入階段已過期',
            detail: '請重新登入。',
            life: 3000,
          })
        }

        clearTimeout(unauthorizedToastTimer)
        unauthorizedToastTimer = setTimeout(() => {
          unauthorizedToastActive = false
        }, 1000)
      }

      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('app:unauthorized'))
      }

      if (router.currentRoute.value.path !== '/') {
        const navigate = typeof router.replace === 'function' ? router.replace : router.push
        const result = navigate.call(router, '/')
        result?.catch?.(() => {
          window.location.href = '/'
        })
      }
    }
    return Promise.reject(error)
  }
)
