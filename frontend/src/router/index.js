import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated, getCurrentUser } from '../utils/auth.js'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { requiresGuest: true },
  },
  {
    path: '/archive',
    name: 'Archive',
    component: () => import('../views/Archive.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/Admin.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/login/callback',
    name: 'LoginCallback',
    component: () => import('../views/LoginCallback.vue'),
    meta: { requiresGuest: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
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
