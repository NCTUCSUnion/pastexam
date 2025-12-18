import { api, buildWebSocketUrl } from './client'

export const aiExamService = {
  generateMockExam(params) {
    return api.post('/ai-exam/generate', {
      archive_ids: params.archive_ids,
      prompt: params.prompt || null,
      temperature: params.temperature || 0.7,
    })
  },

  openTaskStatusWebSocket(taskId, { token } = {}) {
    const authToken = token ?? sessionStorage.getItem('authToken')
    const url = buildWebSocketUrl(`/ai-exam/ws/task/${taskId}`, {
      queryParams: authToken ? { token: authToken } : {},
    })
    if (!url) return null
    return new WebSocket(url)
  },

  deleteTask(taskId) {
    return api.delete(`/ai-exam/task/${taskId}`)
  },

  getApiKeyStatus() {
    return api.get('/ai-exam/api-key')
  },

  updateApiKey(apiKey) {
    return api.put('/ai-exam/api-key', {
      gemini_api_key: apiKey,
    })
  },
}
