// frontend/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/PrSubmit.vue')
  },
  {
    path: '/review/:taskId',
    name: 'ReviewDetail',
    component: () => import('../views/ReviewDetail.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router