import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/components/Layout.vue'
import Dashboard from '@/views/Dashboard.vue'

const routes = [
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('@/views/DeviceList.vue')
      },
      {
        path: 'devices/:id',
        name: 'DeviceDetails',
        component: () => import('@/views/DeviceDetails.vue')
      },
      {
        path: 'occupancy',
        name: 'Occupancy',
        component: () => import('@/views/Occupancy.vue')
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
