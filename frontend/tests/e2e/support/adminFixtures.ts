import type { Page } from '@playwright/test'
import { JSON_HEADERS } from './constants'

export type Course = { id: number; name: string; category: string }
export type User = {
  id: number
  name: string
  email: string
  is_admin: boolean
  is_local: boolean
  last_login: string | null
}

export type Notification = {
  id: number
  title: string
  body: string
  severity: string
  is_active: boolean
  created_at: string
  updated_at: string
  starts_at: string | null
  ends_at: string | null
}

type CatalogEntry = Array<{ id: number; name: string }>
type Catalog = Record<Course['category'], CatalogEntry>

export const buildCoursesCatalog = (courses: Course[]): Catalog => ({
  freshman: courses
    .filter((course) => course.category === 'freshman')
    .map(({ id, name }) => ({ id, name })),
  sophomore: courses
    .filter((course) => course.category === 'sophomore')
    .map(({ id, name }) => ({ id, name })),
  junior: courses
    .filter((course) => course.category === 'junior')
    .map(({ id, name }) => ({ id, name })),
  senior: courses
    .filter((course) => course.category === 'senior')
    .map(({ id, name }) => ({ id, name })),
  graduate: courses
    .filter((course) => course.category === 'graduate')
    .map(({ id, name }) => ({ id, name })),
  interdisciplinary: courses
    .filter((course) => course.category === 'interdisciplinary')
    .map(({ id, name }) => ({ id, name })),
  general: courses
    .filter((course) => course.category === 'general')
    .map(({ id, name }) => ({ id, name })),
})

export const defaultCourses: Course[] = [
  { id: 1, name: '資料結構', category: 'freshman' },
  { id: 2, name: '演算法', category: 'junior' },
]

export const defaultUsers: User[] = [
  {
    id: 1,
    name: 'Admin',
    email: 'admin@example.com',
    is_admin: true,
    is_local: false,
    last_login: '2025-10-30T10:00:00Z',
  },
  {
    id: 2,
    name: '一般使用者',
    email: 'user@example.com',
    is_admin: false,
    is_local: true,
    last_login: '2025-10-29T12:00:00Z',
  },
]

export const defaultNotifications: Notification[] = [
  {
    id: 1,
    title: '系統維護公告',
    body: '系統將於週末進行維護',
    severity: 'danger',
    is_active: true,
    created_at: '2025-10-30T15:00:00Z',
    updated_at: '2025-10-30T15:00:00Z',
    starts_at: null,
    ends_at: null,
  },
]

export type CourseMocks = {
  getCourses: () => Course[]
  createPayloads: Array<Record<string, unknown>>
  updatePayloads: Array<{ id: number; payload: Record<string, unknown> }>
  deleteIds: number[]
}

export const mockAdminCourseEndpoints = async (
  page: Page,
  initialCourses: Course[] = defaultCourses
): Promise<CourseMocks> => {
  let courses = [...initialCourses]
  const createPayloads: Array<Record<string, unknown>> = []
  const updatePayloads: Array<{ id: number; payload: Record<string, unknown> }> = []
  const deleteIds: number[] = []
  let createdCourseId = 100

  await page.route('**/api/courses', async (route) => {
    await route.fulfill({
      status: 200,
      headers: JSON_HEADERS,
      body: JSON.stringify(buildCoursesCatalog(courses)),
    })
  })

  await page.route('**/api/courses/admin/courses**', async (route) => {
    const request = route.request()
    const method = request.method()

    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify(courses),
      })
      return
    }

    if (method === 'POST') {
      const payload = request.postDataJSON() as Record<string, unknown>
      createPayloads.push(payload)
      createdCourseId += 1
      const created = {
        id: createdCourseId,
        ...(payload as Record<string, unknown>),
      }
      courses = [...courses, created as Course]
      await route.fulfill({
        status: 201,
        headers: JSON_HEADERS,
        body: JSON.stringify(created),
      })
      return
    }

    if (method === 'PUT') {
      const id = Number(request.url().split('/').pop())
      const payload = request.postDataJSON() as Record<string, unknown>
      updatePayloads.push({ id, payload })
      courses = courses.map((course) =>
        course.id === id ? { ...course, ...(payload as Record<string, string>) } : course
      )
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify({ id, ...(payload as Record<string, unknown>) }),
      })
      return
    }

    if (method === 'DELETE') {
      const id = Number(request.url().split('/').pop())
      deleteIds.push(id)
      courses = courses.filter((course) => course.id !== id)
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify({ message: 'Course deleted successfully' }),
      })
      return
    }

    await route.continue()
  })

  return { getCourses: () => courses, createPayloads, updatePayloads, deleteIds }
}

export type UserMocks = {
  getUsers: () => User[]
  createPayloads: Array<Record<string, unknown>>
  updatePayloads: Array<{ id: number; payload: Record<string, unknown> }>
  deleteIds: number[]
}

export const mockAdminUserEndpoints = async (
  page: Page,
  initialUsers: User[] = defaultUsers
): Promise<UserMocks> => {
  let users = [...initialUsers]
  const createPayloads: Array<Record<string, unknown>> = []
  const updatePayloads: Array<{ id: number; payload: Record<string, unknown> }> = []
  const deleteIds: number[] = []
  let createdUserId = 1000

  await page.route('**/api/users/admin/users**', async (route) => {
    const request = route.request()
    const method = request.method()

    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify(users),
      })
      return
    }

    if (method === 'POST') {
      const payload = request.postDataJSON() as Record<string, unknown>
      createPayloads.push(payload)
      createdUserId += 1
      const created = {
        id: createdUserId,
        ...(payload as Record<string, unknown>),
      }
      users = [...users, created as User]
      await route.fulfill({
        status: 201,
        headers: JSON_HEADERS,
        body: JSON.stringify(created),
      })
      return
    }

    if (method === 'PUT') {
      const id = Number(request.url().split('/').pop())
      const payload = request.postDataJSON() as Record<string, unknown>
      updatePayloads.push({ id, payload })
      users = users.map((user) =>
        user.id === id ? { ...user, ...(payload as Record<string, unknown>) } : user
      )
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify({ id, ...(payload as Record<string, unknown>) }),
      })
      return
    }

    if (method === 'DELETE') {
      const id = Number(request.url().split('/').pop())
      deleteIds.push(id)
      users = users.filter((user) => user.id !== id)
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify({ message: 'User deleted successfully' }),
      })
      return
    }

    await route.continue()
  })

  return { getUsers: () => users, createPayloads, updatePayloads, deleteIds }
}

export type NotificationMocks = {
  getNotifications: () => Notification[]
  createPayloads: Array<Record<string, unknown>>
  updatePayloads: Array<{ id: number; payload: Record<string, unknown> }>
  deleteIds: number[]
}

export const mockAdminNotificationEndpoints = async (
  page: Page,
  initialNotifications: Notification[] = defaultNotifications
): Promise<NotificationMocks> => {
  let notifications = [...initialNotifications]
  const createPayloads: Array<Record<string, unknown>> = []
  const updatePayloads: Array<{ id: number; payload: Record<string, unknown> }> = []
  const deleteIds: number[] = []
  let createdNotificationId = 500

  await page.route('**/api/notifications/admin/notifications**', async (route) => {
    const request = route.request()
    const method = request.method()

    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify(notifications),
      })
      return
    }

    if (method === 'POST') {
      const payload = request.postDataJSON() as Record<string, unknown>
      createPayloads.push(payload)
      createdNotificationId += 1
      const created = {
        id: createdNotificationId,
        ...(payload as Record<string, unknown>),
        created_at: '2025-10-31T00:00:00Z',
        updated_at: '2025-10-31T00:00:00Z',
      }
      notifications = [created as Notification, ...notifications]
      await route.fulfill({
        status: 201,
        headers: JSON_HEADERS,
        body: JSON.stringify(created),
      })
      return
    }

    if (method === 'PUT') {
      const id = Number(request.url().split('/').pop())
      const payload = request.postDataJSON() as Record<string, unknown>
      updatePayloads.push({ id, payload })
      notifications = notifications.map((notification) =>
        notification.id === id
          ? {
              ...notification,
              ...(payload as Record<string, unknown>),
              updated_at: '2025-10-31T01:00:00Z',
            }
          : notification
      )
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify({ id, ...(payload as Record<string, unknown>) }),
      })
      return
    }

    if (method === 'DELETE') {
      const id = Number(request.url().split('/').pop())
      deleteIds.push(id)
      notifications = notifications.filter((notification) => notification.id !== id)
      await route.fulfill({
        status: 200,
        headers: JSON_HEADERS,
        body: JSON.stringify({ message: 'Notification deleted successfully' }),
      })
      return
    }

    await route.continue()
  })

  return { getNotifications: () => notifications, createPayloads, updatePayloads, deleteIds }
}
