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
      },
      {
        path: 'scans',
        name: 'ScanHistory',
        component: () => import('@/views/ScanHistory.vue')
      },
      {
        path: 'events',
        name: 'Events',
        component: () => import('@/views/Events.vue')
      },
      {
        path: 'analytics',
        name: 'Analytics',
        component: () => import('@/views/Analytics.vue')
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
