import { api } from './client'

export const aiExamService = {
  generateMockExam(params) {
    return api.post('/ai-exam/generate', {
      archive_ids: params.archive_ids,
      prompt: params.prompt || null,
      temperature: params.temperature || 0.7,
    })
  },

  getTaskStatus(taskId) {
    return api.get(`/ai-exam/task/${taskId}`)
  },

  listTasks() {
    return api.get('/ai-exam/tasks')
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
