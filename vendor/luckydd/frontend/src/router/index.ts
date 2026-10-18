import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/Home.vue')
  },
  {
    path: '/data',
    name: 'data',
    component: () => import('../views/DataQuery.vue')
  },
  {
    path: '/analysis',
    name: 'analysis',
    component: () => import('../views/Statistics.vue')
  },
  {
    path: '/advanced',
    name: 'advanced',
    component: () => import('../views/AdvancedAnalysis.vue')
  },
  {
    path: '/recommend',
    name: 'recommend',
    component: () => import('../views/Recommend.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router