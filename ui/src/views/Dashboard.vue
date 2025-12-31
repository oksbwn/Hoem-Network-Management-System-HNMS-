<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Dashboard</h1>
      <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Network overview and system status</p>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div v-for="stat in stats" :key="stat.label"
        class="relative bg-white/70 dark:bg-slate-800/70 backdrop-blur-md rounded-2xl border border-slate-200 dark:border-slate-700 p-4 hover:shadow-xl transition-all flex flex-col justify-between overflow-hidden group min-h-[100px]">

        <!-- Sparkline Background -->
        <Sparkline :data="stat.trend" :color="stat.color" class="opacity-15" />

        <!-- Header Row: Icon & Trend -->
        <div class="relative z-10 flex items-center justify-between w-full">
          <div :class="[stat.bgClass, 'p-1.5 rounded-lg shadow-sm border border-white/10']">
            <component :is="stat.icon" class="h-4 w-4" />
          </div>
          <div
            class="flex items-center gap-1 bg-white/50 dark:bg-slate-900/40 px-2 py-0.5 rounded-full backdrop-blur-sm border border-slate-200/50 dark:border-slate-700/50">
            <span :class="[stat.changeType === 'up' ? 'text-emerald-600' : 'text-rose-500', 'text-[10px] font-bold']">
              {{ stat.changeType === 'down' ? '↓' : '↑' }} {{ stat.change }}
            </span>
          </div>
        </div>

        <!-- Center Content: Metric & Label -->
        <div class="relative z-10 flex flex-col items-center text-center -mt-1">
          <p class="text-2xl font-black text-slate-900 dark:text-white tracking-tight leading-none">
            {{ stat.value }}
          </p>
          <p :style="{ color: stat.color }" class="text-[9px] font-black uppercase tracking-[0.2em] opacity-80 mt-1">
            {{ stat.label }}
          </p>
        </div>
      </div>
    </div>

    <!-- Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Network Topology -->
      <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-semibold text-slate-900 dark:text-white">Network Topology</h2>
          <span
            class="px-2 py-1 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 text-xs font-medium rounded">
            Preview
          </span>
        </div>

        <div
          class="h-64 flex items-center justify-center bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-dashed border-slate-300 dark:border-slate-600">
          <div class="text-center">
            <div class="inline-flex p-4 bg-white dark:bg-slate-800 rounded-full shadow-sm mb-3">
              <component :is="stats[0].icon" class="h-8 w-8 text-slate-400" />
            </div>
            <p class="text-sm font-medium text-slate-600 dark:text-slate-400">Topology Visualization</p>
            <p class="text-xs text-slate-500 mt-1">Coming in v0.4.0</p>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-semibold text-slate-900 dark:text-white">Recent Activity</h2>
          <div class="flex items-center space-x-2">
            <div class="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
            <span class="text-xs font-medium text-emerald-600 dark:text-emerald-400">Live</span>
          </div>
        </div>

        <div class="space-y-3">
          <div v-for="i in 5" :key="i"
            class="flex items-start space-x-3 p-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
            <div class="w-2 h-2 mt-1.5 rounded-full bg-blue-500 flex-shrink-0"></div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-slate-700 dark:text-slate-300">
                Device scan completed successfully
              </p>
              <p class="text-xs text-slate-500 dark:text-slate-500 mt-0.5">
                Process ID: scan_{{ i }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ComputerDesktopIcon, WifiIcon, ExclamationTriangleIcon } from '@heroicons/vue/24/outline'
import axios from 'axios'
import Sparkline from '@/components/Sparkline.vue'

const stats = ref([
  {
    label: 'Total Devices',
    value: '0',
    icon: ComputerDesktopIcon,
    bgClass: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
    color: '#3b82f6',
    trend: [18, 19, 18, 20, 22, 21, 23, 22, 24, 23],
    change: '2.4%',
    changeType: 'up'
  },
  {
    label: 'Online',
    value: '0',
    icon: WifiIcon,
    bgClass: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
    color: '#10b981',
    trend: [15, 16, 14, 17, 18, 18, 20, 19, 21, 20],
    change: '12.1%',
    changeType: 'up'
  },
  {
    label: 'Offline',
    value: '0',
    icon: ExclamationTriangleIcon,
    bgClass: 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400',
    color: '#f43f5e',
    trend: [3, 2, 3, 2, 2, 3, 2, 2, 3, 2],
    change: '14.5%',
    changeType: 'down'
  },
])

const devices = ref([])
const hideOffline = ref(false)

const filteredDevices = computed(() => {
  if (hideOffline.value) {
    return devices.value.filter(d => d.status === 'online')
  }
  return devices.value
})

onMounted(async () => {
  try {
    const configRes = await axios.get('/api/v1/config/hide_offline')
    hideOffline.value = configRes.data.value === 'true'
  } catch { }

  try {
    const res = await axios.get('/api/v1/devices/')
    // The API returns a paginated response { items: [], total: ..., global_stats: ... }
    devices.value = res.data.items || [] // fallback if items is missing

    if (res.data.global_stats) {
      stats.value[0].value = res.data.global_stats.total
      stats.value[1].value = res.data.global_stats.online
      stats.value[2].value = res.data.global_stats.offline
    } else {
      // Fallback for older API shape if necessary (though API is updated)
      stats.value[0].value = res.data.total || devices.value.length
      stats.value[1].value = devices.value.filter(d => d.status === 'online').length
      stats.value[2].value = devices.value.filter(d => d.status === 'offline').length
    }
  } catch (e) {
    console.error(e)
  }
})
</script>
