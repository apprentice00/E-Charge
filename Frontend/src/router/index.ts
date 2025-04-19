import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'login',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue')
    },
    {
      path: '/user-dashboard',
      name: 'userDashboard',
      component: () => import('../views/UserDashboardView.vue'),
      meta: { requiresAuth: true, userType: 'user' }
    },
    {
      path: '/admin-dashboard',
      name: 'adminDashboard',
      component: () => import('../views/AdminDashboardView.vue'),
      meta: { requiresAuth: true, userType: 'admin' }
    },
    {
      path: '/charge-request',
      name: 'chargeRequest',
      component: () => import('../views/ChargeRequestView.vue'),
      meta: { requiresAuth: true, userType: 'user' }
    },
    {
      path: '/queue-status',
      name: 'queueStatus',
      component: () => import('../views/QueueStatusView.vue'),
      meta: { requiresAuth: true, userType: 'user' }
    },
    {
      path: '/charging-status',
      name: 'chargingStatus',
      component: () => import('../views/ChargingStatusView.vue'),
      meta: { requiresAuth: true, userType: 'user' }
    },
    {
      path: '/bill-records',
      name: 'billRecords',
      component: () => import('../views/BillRecordsView.vue'),
      meta: { requiresAuth: true, userType: 'user' }
    },
    {
      path: '/pile-details/:id',
      name: 'pileDetails',
      component: () => import('../views/PileDetailsView.vue'),
      meta: { requiresAuth: true, userType: 'admin' }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userJson = localStorage.getItem('currentUser')
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  
  if (requiresAuth && !userJson) {
    // 需要登录但用户未登录，跳转到登录页
    next({ name: 'login' })
  } else if (requiresAuth && userJson) {
    // 需要登录且用户已登录，检查用户类型是否匹配
    const user = JSON.parse(userJson)
    const requiredUserType = to.matched.find(record => record.meta.userType)?.meta.userType
    
    if (requiredUserType && user.type !== requiredUserType) {
      // 用户类型不匹配，跳转到对应的仪表盘
      next({ name: user.type === 'admin' ? 'adminDashboard' : 'userDashboard' })
    } else {
      // 用户类型匹配，允许访问
      next()
    }
  } else {
    // 不需要登录或用户已登录，允许访问
    next()
  }
})

export default router
