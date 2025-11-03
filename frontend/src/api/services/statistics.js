import { api } from './client'

export const statisticsService = {
  getSystemStatistics() {
    return api.get('/statistics')
  },
}
