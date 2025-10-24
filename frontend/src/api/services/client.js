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
    if (error.response?.status === 401) {
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
        router.push('/')
      }
    }
    return Promise.reject(error)
  }
)
