import { describe, it, expect, vi, beforeEach } from 'vitest'
import { courseService } from '@/api/services/courses.js'
import { archiveService } from '@/api/services/archives.js'
import { notificationService } from '@/api/services/notifications.js'
import { authService } from '@/api/services/auth.js'
import { aiExamService } from '@/api/services/aiExam.js'
import { memeService } from '@/api/services/meme.js'
import { statisticsService } from '@/api/services/statistics.js'
import { discussionService } from '@/api/services/discussion.js'
import { userService } from '@/api/services/users.js'
import * as adminService from '@/api/services/admin.js'

const getMock = vi.hoisted(() => vi.fn())
const postMock = vi.hoisted(() => vi.fn())
const deleteMock = vi.hoisted(() => vi.fn())
const patchMock = vi.hoisted(() => vi.fn())
const putMock = vi.hoisted(() => vi.fn())
const interceptors = vi.hoisted(() => ({
  request: { use: vi.fn() },
  response: { use: vi.fn() },
}))

vi.mock('@/api/services/client', () => ({
  api: {
    get: getMock,
    post: postMock,
    delete: deleteMock,
    patch: patchMock,
    put: putMock,
    interceptors,
  },
  bindUnauthorizedWebSocket: (ws) => ws,
  buildWebSocketUrl: (path) => `ws://localhost${path}`,
}))

describe('API service wrappers', () => {
  beforeEach(() => {
    getMock.mockReset()
    postMock.mockReset()
    deleteMock.mockReset()
    patchMock.mockReset()
    putMock.mockReset()
  })

  it('courseService proxies to API client', () => {
    courseService.listCourses()
    expect(getMock).toHaveBeenCalledWith('/courses')

    courseService.getCourseArchives('course-1')
    expect(getMock).toHaveBeenCalledWith('/courses/course-1/archives')

    courseService.getAllCourses()
    expect(getMock).toHaveBeenCalledWith('/courses/admin/courses')

    courseService.createCourse({ name: 'Algorithms' })
    expect(postMock).toHaveBeenCalledWith('/courses/admin/courses', { name: 'Algorithms' })

    courseService.updateCourse('course-1', { name: 'Updated' })
    expect(putMock).toHaveBeenCalledWith('/courses/admin/courses/course-1', { name: 'Updated' })

    courseService.deleteCourse('course-1')
    expect(deleteMock).toHaveBeenCalledWith('/courses/admin/courses/course-1')
  })

  it('archiveService proxies to API client', () => {
    const formData = new FormData()
    archiveService.uploadArchive(formData)
    expect(postMock).toHaveBeenCalledWith(
      '/archives/upload',
      formData,
      expect.objectContaining({
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    )

    archiveService.getArchivePreviewUrl('course-1', 'arch-1')
    expect(getMock).toHaveBeenCalledWith('/courses/course-1/archives/arch-1/preview')

    archiveService.getArchiveDownloadUrl('course-1', 'arch-1')
    expect(getMock).toHaveBeenCalledWith('/courses/course-1/archives/arch-1/download')

    archiveService.deleteArchive('course-1', 'arch-1')
    expect(deleteMock).toHaveBeenCalledWith('/courses/course-1/archives/arch-1')

    archiveService.updateArchive('course-1', 'arch-1', { name: 'Exam' })
    expect(patchMock).toHaveBeenCalledWith(
      '/courses/course-1/archives/arch-1',
      expect.any(FormData)
    )

    archiveService.updateArchiveCourse('course-1', 'arch-1', 'course-2')
    expect(patchMock).toHaveBeenCalledWith('/courses/course-1/archives/arch-1/course', {
      course_id: 'course-2',
    })

    archiveService.updateArchiveCourseByCategoryAndName('course-1', 'arch-1', 'Linear', 'freshman')
    expect(patchMock).toHaveBeenCalledWith('/courses/course-1/archives/arch-1/course', {
      course_name: 'Linear',
      course_category: 'freshman',
    })
  })

  it('notification service proxies', () => {
    notificationService.getActive()
    expect(getMock).toHaveBeenCalledWith('/notifications/active')

    notificationService.getAll()
    expect(getMock).toHaveBeenCalledWith('/notifications')

    notificationService.getAllAdmin()
    expect(getMock).toHaveBeenCalledWith('/notifications/admin/notifications')

    notificationService.create({ title: 'New' })
    expect(postMock).toHaveBeenCalledWith('/notifications/admin/notifications', { title: 'New' })

    notificationService.update(1, { title: 'Updated' })
    expect(putMock).toHaveBeenCalledWith('/notifications/admin/notifications/1', {
      title: 'Updated',
    })

    notificationService.remove(1)
    expect(deleteMock).toHaveBeenCalledWith('/notifications/admin/notifications/1')
  })

  it('auth service proxies', async () => {
    postMock.mockResolvedValueOnce({ data: { token: 'abc' } })
    const data = await authService.localLogin('user', 'pass')
    expect(postMock).toHaveBeenCalledWith('/auth/login', expect.any(FormData))
    expect(data).toEqual({ token: 'abc' })

    authService.logout()
    expect(postMock).toHaveBeenCalledWith('/auth/logout')
  })

  it('ai exam service proxies', async () => {
    const params = { archive_ids: ['a1'], prompt: 'test', temperature: 0.9 }
    const taskId = 'task-1'
    const originalWebSocket = globalThis.WebSocket
    const webSocketMock = vi.fn(function WebSocket(url) {
      return { url }
    })
    globalThis.WebSocket = webSocketMock

    aiExamService.generateMockExam(params)
    expect(postMock).toHaveBeenCalledWith('/ai-exam/generate', {
      archive_ids: params.archive_ids,
      prompt: params.prompt,
      temperature: params.temperature,
    })

    aiExamService.deleteTask(taskId)
    expect(deleteMock).toHaveBeenCalledWith(`/ai-exam/task/${taskId}`)

    const ws = aiExamService.openTaskStatusWebSocket(taskId)
    expect(webSocketMock).toHaveBeenCalledWith(
      expect.stringContaining(`/ai-exam/ws/task/${taskId}`)
    )
    expect(ws.url).toContain(`/ai-exam/ws/task/${taskId}`)

    aiExamService.getApiKeyStatus()
    expect(getMock).toHaveBeenCalledWith('/ai-exam/api-key')

    aiExamService.updateApiKey('secret')
    expect(putMock).toHaveBeenCalledWith('/ai-exam/api-key', { gemini_api_key: 'secret' })

    globalThis.WebSocket = originalWebSocket
  })

  it('meme service proxies', () => {
    memeService.getRandomMeme()
    expect(getMock).toHaveBeenCalledWith('/meme')
  })

  it('statistics service handles success and error', async () => {
    const response = { data: { count: 1 } }
    getMock.mockResolvedValueOnce(response)
    await expect(statisticsService.getSystemStatistics()).resolves.toBe(response)

    const error = new Error('fail')
    getMock.mockRejectedValueOnce(error)
    await expect(statisticsService.getSystemStatistics()).rejects.toThrow('fail')
  })

  it('discussion service proxies', () => {
    discussionService.listArchiveMessages('course-1', 'arch-1')
    expect(getMock).toHaveBeenCalledWith('/courses/course-1/archives/arch-1/discussion/messages', {
      params: { limit: 50, before_id: undefined },
    })

    discussionService.deleteArchiveMessage('course-1', 'arch-1', 123)
    expect(deleteMock).toHaveBeenCalledWith('/courses/course-1/archives/arch-1/discussion/123')

    const originalWebSocket = globalThis.WebSocket
    const webSocketMock = vi.fn(function WebSocket(url) {
      return { url }
    })
    globalThis.WebSocket = webSocketMock

    const ws = discussionService.openArchiveDiscussionWebSocket('course-1', 'arch-1')
    expect(webSocketMock).toHaveBeenCalledWith(
      expect.stringContaining('/courses/course-1/archives/arch-1/discussion/ws')
    )
    expect(ws.url).toContain('/courses/course-1/archives/arch-1/discussion/ws')

    globalThis.WebSocket = originalWebSocket
  })

  it('user service proxies', () => {
    userService.getMe()
    expect(getMock).toHaveBeenCalledWith('/users/me')

    userService.updateMyNickname('Nick')
    expect(patchMock).toHaveBeenCalledWith('/users/me/nickname', { nickname: 'Nick' })
  })

  it('admin service exports call API client', () => {
    adminService.getCourses()
    expect(getMock).toHaveBeenCalledWith('/courses/admin/courses')

    adminService.createCourse({ name: 'New' })
    expect(postMock).toHaveBeenCalledWith('/courses/admin/courses', { name: 'New' })

    adminService.updateCourse(1, { name: 'Updated' })
    expect(putMock).toHaveBeenCalledWith('/courses/admin/courses/1', { name: 'Updated' })

    adminService.deleteCourse(1)
    expect(deleteMock).toHaveBeenCalledWith('/courses/admin/courses/1')

    adminService.getUsers()
    expect(getMock).toHaveBeenCalledWith('/users/admin/users')

    adminService.createUser({ name: 'Alice' })
    expect(postMock).toHaveBeenCalledWith('/users/admin/users', { name: 'Alice' })

    adminService.updateUser(2, { name: 'Bob' })
    expect(putMock).toHaveBeenCalledWith('/users/admin/users/2', { name: 'Bob' })

    adminService.deleteUser(2)
    expect(deleteMock).toHaveBeenCalledWith('/users/admin/users/2')
  })
})
