import { api } from './client'

export const statisticsService = {
  async getSystemStatistics() {
    try {
      const response = await api.get('/statistics')
      return response
    } catch (error) {
      console.error('Error fetching system statistics:', error)
      throw error
    }
  },
}
