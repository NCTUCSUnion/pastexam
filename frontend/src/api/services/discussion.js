import { api, bindUnauthorizedWebSocket, buildWebSocketUrl } from './client'

export const discussionService = {
  listArchiveMessages(courseId, archiveId, { limit = 50, beforeId } = {}) {
    return api.get(`/courses/${courseId}/archives/${archiveId}/discussion/messages`, {
      params: {
        limit,
        before_id: beforeId,
      },
    })
  },

  deleteArchiveMessage(courseId, archiveId, messageId) {
    return api.delete(`/courses/${courseId}/archives/${archiveId}/discussion/${messageId}`)
  },

  openArchiveDiscussionWebSocket(courseId, archiveId, { token } = {}) {
    const authToken = token ?? sessionStorage.getItem('authToken')
    const url = buildWebSocketUrl(`/courses/${courseId}/archives/${archiveId}/discussion/ws`, {
      queryParams: authToken ? { token: authToken } : {},
    })
    if (!url) return null
    return bindUnauthorizedWebSocket(new WebSocket(url))
  },
}
