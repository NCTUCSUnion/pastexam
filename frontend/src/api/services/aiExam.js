import { api } from './client'

export const aiExamService = {
  /**
   * 生成模擬考題
   * @param {Object} params - 生成參數
   * @param {Array<number>} params.archive_ids - 考古題 ID 列表
   * @param {string} params.prompt - 自定義 prompt（可選）
   * @param {number} params.temperature - 生成溫度（可選，0-1）
   */
  generateMockExam(params) {
    return api.post('/ai-exam/generate', {
      archive_ids: params.archive_ids,
      prompt: params.prompt || null,
      temperature: params.temperature || 0.7,
    })
  },

  /**
   * 測試 AI service 是否正常運作
   */
  testAIService() {
    return api.get('/ai-exam/test')
  },
}
