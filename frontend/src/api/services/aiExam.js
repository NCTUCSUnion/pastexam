import { api, bindUnauthorizedWebSocket, buildWebSocketUrl } from './client'
import { STORAGE_KEYS, getSessionItem, getLocalItem } from '../../utils/storage'

export const aiExamService = {
  generateMockExam(params) {
    return api.post('/ai-exam/generate', {
      archive_ids: params.archive_ids,
      prompt: params.prompt || null,
      temperature: params.temperature || 0.7,
    })
  },

  openTaskStatusWebSocket(taskId, { token } = {}) {
    const authToken =
      token ??
      getSessionItem(STORAGE_KEYS.session.AUTH_TOKEN) ??
      getLocalItem(STORAGE_KEYS.local.AUTH_TOKEN)
    const url = buildWebSocketUrl(`/ai-exam/ws/task/${taskId}`, {
      queryParams: authToken ? { token: authToken } : {},
    })
    if (!url) return null
    return bindUnauthorizedWebSocket(new WebSocket(url))
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
