import { createRouter, createWebHistory } from 'vue-router'
import { decodeToken, getCurrentUser, isAuthenticated, setToken } from '../utils/auth.js'
import { STORAGE_KEYS, removeSessionItem } from '../utils/storage'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import(/* webpackChunkName: "home" */ '../views/Home.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/archive',
    name: 'Archive',
    component: () => import(/* webpackChunkName: "archive" */ '../views/Archive.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import(/* webpackChunkName: "admin" */ '../views/Admin.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/login/callback',
    name: 'LoginCallback',
    component: () => import(/* webpackChunkName: "login-callback" */ '../views/LoginCallback.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import(/* webpackChunkName: "not-found" */ '../views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  if (to.name === 'LoginCallback' && to.query?.token) {
    const token = Array.isArray(to.query.token) ? to.query.token[0] : to.query.token
    const decoded = decodeToken(token)
    const nowInSeconds = Math.floor(Date.now() / 1000)

    if (decoded?.exp && decoded.exp > nowInSeconds) {
      setToken(token)
      next({ name: 'Archive', replace: true })
      return
    }

    removeSessionItem(STORAGE_KEYS.session.AUTH_TOKEN)
    next({ name: 'Home', replace: true })
    return
  }

  const isLoggedIn = isAuthenticated()
  const currentUser = getCurrentUser()

  if (to.meta.requiresAuth && !isLoggedIn) {
    next({ name: 'Home' })
  } else if (to.meta.requiresGuest && isLoggedIn) {
    next({ name: 'Archive' })
  } else if (to.meta.requiresAdmin && (!currentUser || !currentUser.is_admin)) {
    next({ name: 'Archive' })
  } else {
    next()
  }
})

export default router
