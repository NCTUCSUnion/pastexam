import { beforeEach, describe, expect, it, vi } from 'vitest'

const authMocks = vi.hoisted(() => ({
  decodeToken: vi.fn(),
  getCurrentUser: vi.fn(),
  isAuthenticated: vi.fn(),
  setToken: vi.fn(),
}))
const removeSessionItemMock = vi.hoisted(() => vi.fn())

vi.mock('@/utils/auth.js', () => authMocks)
vi.mock('@/utils/storage', async (importOriginal) => ({
  ...(await importOriginal()),
  removeSessionItem: removeSessionItemMock,
}))
// Route components are lazily imported; keep them out of the test
vi.mock('@/views/Home.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/Archive.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/Admin.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/LoginCallback.vue', () => ({ default: { template: '<div />' } }))
vi.mock('@/views/NotFound.vue', () => ({ default: { template: '<div />' } }))

const { default: router } = await import('@/router/index.js')

function login({ admin = false } = {}) {
  authMocks.isAuthenticated.mockReturnValue(true)
  authMocks.getCurrentUser.mockReturnValue({ name: 'user', is_admin: admin })
}

async function visit(path) {
  await router.push(path)
  return router.currentRoute.value.name
}

describe('router guard', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    authMocks.isAuthenticated.mockReturnValue(false)
    authMocks.getCurrentUser.mockReturnValue(null)
    // Start every test from a neutral page
    await router.push('/does-not-exist')
  })

  it('sends guests from protected pages to home', async () => {
    expect(await visit('/archive')).toBe('Home')
    expect(await visit('/admin')).toBe('Home')
  })

  it('sends logged-in users from home to the archive', async () => {
    login()
    expect(await visit('/')).toBe('Archive')
  })

  it('only lets admins open the admin page', async () => {
    login()
    expect(await visit('/admin')).toBe('Archive')

    login({ admin: true })
    expect(await visit('/admin')).toBe('Admin')
  })

  it('lets everyone reach unknown routes', async () => {
    expect(await visit('/nowhere')).toBe('NotFound')
  })

  it('stores a valid token from the OAuth callback', async () => {
    authMocks.decodeToken.mockReturnValue({ exp: Math.floor(Date.now() / 1000) + 60 })
    // Storing the token logs the user in
    authMocks.setToken.mockImplementation(() => login())
    expect(await visit('/login/callback?token=good')).toBe('Archive')
    expect(authMocks.setToken).toHaveBeenCalledWith('good')
  })

  it('drops an expired token from the OAuth callback', async () => {
    authMocks.decodeToken.mockReturnValue({ exp: Math.floor(Date.now() / 1000) - 60 })
    expect(await visit('/login/callback?token=old')).toBe('Home')
    expect(authMocks.setToken).not.toHaveBeenCalled()
    expect(removeSessionItemMock).toHaveBeenCalled()
  })
})
