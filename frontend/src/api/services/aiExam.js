import { api } from './client'

export const aiExamService = {
  /**
   * Submit a mock exam generation task
   * @param {Object} params - Generation parameters
   * @param {Array<number>} params.archive_ids - List of archive IDs
   * @param {string} params.prompt - Optional custom prompt
   * @param {number} params.temperature - Optional temperature (0-1)
   * @returns {Promise<{task_id: string, status: string, message: string}>}
   */
  generateMockExam(params) {
    return api.post('/ai-exam/generate', {
      archive_ids: params.archive_ids,
      prompt: params.prompt || null,
      temperature: params.temperature || 0.7,
    })
  },

  /**
   * Get the status of a generation task
   * @param {string} taskId - Task ID
   * @returns {Promise<{task_id: string, status: string, result: Object, error: string}>}
   */
  getTaskStatus(taskId) {
    return api.get(`/ai-exam/task/${taskId}`)
  },

  /**
   * List all tasks for the current user
   * @returns {Promise<{tasks: Array}>}
   */
  listTasks() {
    return api.get('/ai-exam/tasks')
  },

  /**
   * Delete a task
   * @param {string} taskId - Task ID
   * @returns {Promise<{success: boolean, message: string}>}
   */
  deleteTask(taskId) {
    return api.delete(`/ai-exam/task/${taskId}`)
  },

  /**
   * Fetch the current API key status
   * @returns {Promise<{has_api_key: boolean, api_key_masked: string|null}>}
   */
  getApiKeyStatus() {
    return api.get('/ai-exam/api-key')
  },

  /**
   * Update the API key (validity is tested automatically)
   * @param {string} apiKey - API key
   * @returns {Promise<{has_api_key: boolean, api_key_masked: string|null}>}
   */
  updateApiKey(apiKey) {
    return api.put('/ai-exam/api-key', {
      gemini_api_key: apiKey,
    })
  },
}
