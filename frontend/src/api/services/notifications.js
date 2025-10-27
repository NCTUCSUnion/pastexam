import { api } from './client'

const BASE_PATH = '/notifications'

export const notificationService = {
  getActive() {
    return api.get(`${BASE_PATH}/active`)
  },
  getAll() {
    return api.get(BASE_PATH)
  },
  getAllAdmin() {
    return api.get(`${BASE_PATH}/admin/notifications`)
  },
  create(payload) {
    return api.post(`${BASE_PATH}/admin/notifications`, payload)
  },
  update(id, payload) {
    return api.put(`${BASE_PATH}/admin/notifications/${id}`, payload)
  },
  remove(id) {
    return api.delete(`${BASE_PATH}/admin/notifications/${id}`)
  },
}
