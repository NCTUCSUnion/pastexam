import { api } from './client'

export const aiExamService = {
  /**
   * 提交 AI 生成考題任務
   * @param {Object} params - 生成參數
   * @param {Array<number>} params.archive_ids - 考古題 ID 列表
   * @param {string} params.prompt - 自定義 prompt（可選）
   * @param {number} params.temperature - 生成溫度（可選，0-1）
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
   * 查詢任務狀態
   * @param {string} taskId - 任務 ID
   * @returns {Promise<{task_id: string, status: string, result: Object, error: string}>}
   */
  getTaskStatus(taskId) {
    return api.get(`/ai-exam/task/${taskId}`)
  },

  /**
   * 列出用戶的所有任務
   * @returns {Promise<{tasks: Array}>}
   */
  listTasks() {
    return api.get('/ai-exam/tasks')
  },

  /**
   * 刪除任務
   * @param {string} taskId - 任務 ID
   * @returns {Promise<{success: boolean, message: string}>}
   */
  deleteTask(taskId) {
    return api.delete(`/ai-exam/task/${taskId}`)
  },
}
