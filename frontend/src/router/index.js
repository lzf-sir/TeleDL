import { createRouter, createWebHistory } from 'vue-router'
import BasicLayout from '@/layouts/BasicLayout.vue'
import Login from '@/views/Login.vue'
import { ElMessage } from 'element-plus'
import api from '@/api'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true }
  },
  {
    path: '/',
    component: BasicLayout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: 'Dashboard', requiresAuth: true }
      },
      {
        path: 'downloads',
        name: 'Downloads',
        component: () => import('@/views/Downloads.vue'),
        meta: { title: '下载管理', requiresAuth: true }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue').catch(() => import('@/views/Settings.vue')),
        meta: { title: 'Settings', requiresAuth: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

router.beforeEach(async (to, from, next) => {
  // Skip auth check for public routes
  if (to.meta.public) return next()

  const token = localStorage.getItem('access_token')
  
  // Redirect to login if no token
  if (!token && to.meta.requiresAuth) {
    ElMessage.warning('请先登录')
    return next({ path: '/login', replace: true })
  }

  // Verify token validity for protected routes
  if (token && to.meta.requiresAuth) {
    try {
      // Skip if already authenticated
      if (localStorage.getItem('authenticated') === 'true') return next()
      
      const meResponse = await api.getMe()
      localStorage.setItem('user_info', JSON.stringify(meResponse.data))
      localStorage.setItem('authenticated', 'true')
      return next()
    } catch (error) {
      localStorage.removeItem('access_token')
      ElMessage.error('登录已过期，请重新登录')
      return next({ path: '/login', replace: true })
    }
  }

  next()
})

export default router
