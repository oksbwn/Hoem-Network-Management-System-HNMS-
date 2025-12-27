<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Dashboard</h1>
    
    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div v-for="stat in stats" :key="stat.label" class="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-slate-700">
        <div class="flex items-center">
          <div class="p-3 rounded-full" :class="stat.bgClass">
            <component :is="stat.icon" class="h-6 w-6" :class="stat.textClass" />
          </div>
          <div class="ml-4">
            <h2 class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ stat.label }}</h2>
            <p class="text-2xl font-semibold text-gray-900 dark:text-white">{{ stat.value }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Hierarchy / Network Map (Placeholder for now) -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700 p-6 mb-8">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Network Hierarchy</h2>
      <div class="h-64 flex items-center justify-center bg-gray-50 dark:bg-slate-900 rounded-lg border border-dashed border-gray-300 dark:border-slate-700">
        <div class="text-center">
          <p class="text-gray-500 dark:text-gray-400 mb-2">Network Topology Visualization</p>
          <p class="text-sm text-gray-400">Gateway → Switches → Devices</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ComputerDesktopIcon, WifiIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import axios from 'axios'

const stats = ref([
  { label: 'Total Devices', value: '0', icon: ComputerDesktopIcon, bgClass: 'bg-blue-100 dark:bg-blue-900', textClass: 'text-blue-600 dark:text-blue-200' },
  { label: 'Online Now', value: '0', icon: WifiIcon, bgClass: 'bg-green-100 dark:bg-green-900', textClass: 'text-green-600 dark:text-green-200' },
  { label: 'Alerts', value: '0', icon: ExclamationTriangleIcon, bgClass: 'bg-orange-100 dark:bg-orange-900', textClass: 'text-orange-600 dark:text-orange-200' },
])

onMounted(async () => {
    try {
        const res = await axios.get('/api/v1/devices/')
        const devices = res.data
        stats.value[0].value = devices.length
        stats.value[1].value = devices.filter(d => {
             if (!d.last_seen) return false
             const diff = new Date() - new Date(d.last_seen + 'Z') // create UTC date
             return diff < 300000 // 5 mins
        }).length
    } catch (e) {
        console.error(e)
    }
})
</script>
