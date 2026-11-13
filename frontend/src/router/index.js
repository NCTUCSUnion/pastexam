import { createRouter, createWebHistory } from 'vue-router'
import { getCurrentUser, isAuthenticated } from '../utils/auth.js'

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

router.beforeEach((to) => {
  const isLoggedIn = isAuthenticated()
  const currentUser = getCurrentUser()

  if (to.meta.requiresAuth && !isLoggedIn) {
    return { name: 'Home' }
  }
  if (to.meta.requiresGuest && isLoggedIn) {
    return { name: 'Archive' }
  }
  if (to.meta.requiresAdmin && (!currentUser || !currentUser.is_admin)) {
    return { name: 'Archive' }
  }
})

export default router
