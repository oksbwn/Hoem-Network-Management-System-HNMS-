<template>
  <div class="space-y-6">
    <!-- Header with Stats -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-900 dark:text-white">Events Log</h1>
        <p class="text-slate-500 dark:text-slate-400">Track device connectivity and network trends</p>
      </div>
      <div class="flex items-center gap-3">
        <div
          class="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-medium">
          <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          <span class="text-emerald-700 dark:text-emerald-400">{{ onlineNowCount }} Online Now</span>
        </div>
        <button @click="fetchData"
          class="p-2 text-slate-500 hover:bg-white dark:hover:bg-slate-800 border border-transparent hover:border-slate-200 dark:hover:border-slate-700 rounded-lg transition-all"
          v-tooltip="'Refresh All'">
          <RefreshCwIcon :class="{ 'animate-spin': loading }" class="h-5 w-5" />
        </button>
      </div>
    </div>

    <!-- Trend Chart Card -->
    <div class="grid grid-cols-1 gap-6">
      <div
        class="bg-white/60 dark:bg-slate-800/60 backdrop-blur-md rounded-2xl border border-white/20 dark:border-slate-700/50 p-6 shadow-sm">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-3">
            <div class="p-2.5 bg-blue-500/10 rounded-xl">
              <ActivityIcon class="h-5 w-5 text-blue-500" />
            </div>
            <div>
              <h3 class="text-lg font-bold text-slate-900 dark:text-white">Network Activity Trend</h3>
              <p class="text-xs text-slate-500">Hourly aggregation of connectivity events</p>
            </div>
          </div>
          <div
            class="flex bg-slate-100/50 dark:bg-slate-900/50 backdrop-blur-sm rounded-xl p-1 border border-slate-200/50 dark:border-slate-700/50">
            <button v-for="opt in timeOptions" :key="opt.value" @click="statsTimeRange = opt.value; fetchStats()"
              class="px-3 py-1.5 text-xs font-bold rounded-lg transition-all"
              :class="statsTimeRange === opt.value ? 'bg-white dark:bg-slate-800 shadow-md text-blue-600 dark:text-blue-400' : 'text-slate-500 hover:text-slate-700'">
              {{ opt.label }}
            </button>
          </div>
        </div>
        <div class="h-64">
          <apexchart v-if="chartSeries[0].data.length > 0" type="line" height="100%" :options="chartOptions"
            :series="chartSeries"></apexchart>
          <div v-else-if="!loadingStats"
            class="h-full flex flex-col items-center justify-center text-slate-400 italic gap-2">
            <ZapOffIcon class="h-8 w-8 text-slate-300" />
            <span>No trend data for this period</span>
          </div>
          <div v-else class="h-full flex items-center justify-center">
            <Loader2Icon class="h-8 w-8 animate-spin text-blue-500/50" />
          </div>
        </div>
      </div>
    </div>

    <!-- Filters & List -->
    <div
      class="bg-white/60 dark:bg-slate-800/60 backdrop-blur-md rounded-2xl border border-white/20 dark:border-slate-700/50 shadow-sm overflow-hidden flex flex-col">
      <!-- Filter Bar -->
      <div
        class="p-4 border-b border-slate-100/50 dark:border-slate-700/50 flex flex-col sm:flex-row gap-4 items-center">
        <div class="relative flex-1 w-full">
          <SearchIcon class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input v-model="search" @input="debounceFetch" type="text" placeholder="Search IP, Mac or Name..."
            class="w-full pl-11 pr-4 py-2 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 rounded-xl outline-none focus:ring-2 focus:ring-blue-500/20 transition-all text-sm" />
        </div>
        <div class="flex items-center gap-2 w-full sm:w-auto">
          <select v-model="statusFilter" @change="fetchData"
            class="flex-1 sm:flex-none px-4 py-2 bg-slate-100/50 dark:bg-slate-900/50 border border-slate-200/50 dark:border-slate-700/50 rounded-xl outline-none focus:ring-2 focus:ring-blue-500/20 transition-all text-sm appearance-none">
            <option value="">All Statuses</option>
            <option value="online">Online Only</option>
            <option value="offline">Offline Only</option>
          </select>
          <div class="h-8 w-[1px] bg-slate-200 dark:bg-slate-700 hidden sm:block"></div>
          <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest hidden md:block px-2">
            {{ totalEvents }} Records
          </p>
        </div>
      </div>

      <!-- Events List -->
      <div class="overflow-x-auto min-h-[400px]">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr
              class="text-slate-500 font-bold uppercase text-[10px] tracking-[0.15em] border-b border-slate-100 dark:border-slate-700/50">
              <th class="px-8 py-4">Device</th>
              <th class="px-6 py-4">Status</th>
              <th class="px-6 py-4">Activity</th>
              <th class="px-6 py-4">Time</th>
              <th class="px-8 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-700/30">
            <tr v-for="event in events" :key="event.id"
              class="hover:bg-blue-50/30 dark:hover:bg-blue-500/5 transition-all group">
              <td class="px-8 py-4">
                <div class="flex items-center gap-4">
                  <div
                    class="p-2.5 bg-slate-100 dark:bg-slate-900 rounded-xl group-hover:bg-white dark:group-hover:bg-slate-800 transition-colors shadow-sm">
                    <component :is="getIcon(event.icon, event.device_type)"
                      class="h-5 w-5 text-slate-600 dark:text-slate-400" />
                  </div>
                  <div>
                    <div class="font-bold text-slate-900 dark:text-white leading-tight mb-0.5">{{ event.display_name }}
                    </div>
                    <div class="text-[10px] text-slate-500 font-mono tracking-wider">{{ event.ip }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span v-if="event.status === 'online'"
                  class="inline-flex items-center px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-black uppercase tracking-widest border border-emerald-500/20">
                  ONLINE
                </span>
                <span v-else
                  class="inline-flex items-center px-2.5 py-1 rounded-lg bg-red-500/10 text-red-600 dark:text-red-400 text-[10px] font-black uppercase tracking-widest border border-red-500/20">
                  OFFLINE
                </span>
              </td>
              <td class="px-6 py-4">
                <p class="text-xs text-slate-600 dark:text-slate-400">
                  {{ event.status === 'online' ? 'Device joined the network' : 'Device disconnected from network' }}
                </p>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-xs text-slate-900 dark:text-slate-200 font-medium">
                  {{ formatDistance(new Date(event.changed_at), new Date(), { addSuffix: true }) }}
                </div>
                <div class="text-[9px] text-slate-400 tracking-tight">
                  {{ format(new Date(event.changed_at), 'MMM dd, HH:mm') }}
                </div>
              </td>
              <td class="px-8 py-4 text-right">
                <button @click="showDeviceDetail(event)"
                  class="p-2 text-slate-400 hover:text-blue-500 hover:bg-blue-100/50 dark:hover:bg-blue-900/30 rounded-xl transition-all opacity-0 group-hover:opacity-100">
                  <ArrowRightCircleIcon class="h-5 w-5" />
                </button>
              </td>
            </tr>
            <tr v-if="events.length === 0 && !loading">
              <td colspan="5" class="px-8 py-20 text-center">
                <div class="flex flex-col items-center gap-2 text-slate-400">
                  <InboxIcon class="h-10 w-10 text-slate-200" />
                  <p class="text-sm italic">No events found matching your criteria</p>
                </div>
              </td>
            </tr>
            <tr v-if="loading">
              <td colspan="5" class="px-8 py-20 text-center">
                <Loader2Icon class="h-8 w-8 animate-spin text-blue-500/30 mx-auto" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Main Pagination -->
      <div v-if="totalPages > 1"
        class="px-8 py-6 border-t border-slate-100 dark:border-slate-700/50 bg-slate-50/50 dark:bg-slate-900/30 flex items-center justify-center gap-4">
        <button @click="changePage(currentPage - 1)" :disabled="currentPage <= 1"
          class="px-6 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-sm">
          Previous
        </button>
        <div
          class="px-5 py-2 bg-slate-900 dark:bg-white rounded-xl text-xs font-black text-white dark:text-slate-900 shadow-md">
          {{ currentPage }} / {{ totalPages }}
        </div>
        <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages"
          class="px-6 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs font-bold text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-30 disabled:cursor-not-allowed transition-all shadow-sm">
          Next
        </button>
      </div>
    </div>

    <!-- Device History Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="selectedDevice" class="fixed inset-0 z-[9999] flex items-center justify-center p-4 md:p-8"
          @click.self="closeModal">
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-slate-950/60 backdrop-blur-md animate-in fade-in duration-300"></div>

          <!-- Modal Content -->
          <div
            class="relative bg-white dark:bg-slate-900 rounded-[2.5rem] border border-white/20 dark:border-slate-700/50 shadow-[0_32px_64px_-12px_rgba(0,0,0,0.5)] w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 slide-in-from-bottom-5 duration-300">

            <!-- Premium Border Shimmer -->
            <div
              class="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-blue-400/50 to-transparent z-10">
            </div>

            <!-- Modal Header -->
            <div class="p-8 pb-6 flex items-start justify-between">
              <div class="flex items-center gap-6">
                <div class="relative">
                  <div
                    class="p-5 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-[1.5rem] shadow-xl shadow-blue-500/20 text-white">
                    <component :is="getIcon(selectedDevice.icon, selectedDevice.device_type)" class="h-8 w-8" />
                  </div>
                  <div :class="selectedDevice.status === 'online' ? 'bg-emerald-500' : 'bg-red-500'"
                    class="absolute -bottom-1 -right-1 w-5 h-5 rounded-full border-4 border-white dark:border-slate-900 shadow-sm">
                  </div>
                </div>
                <div>
                  <h3 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight">{{
                    selectedDevice.display_name }}</h3>
                  <div class="flex items-center gap-3 mt-1">
                    <span
                      class="text-xs font-mono text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-md">{{
                        selectedDevice.ip }}</span>
                    <span class="text-xs text-slate-400 capitalize">{{ selectedDevice.device_type || 'Unknown Device'
                    }}</span>
                  </div>
                </div>
              </div>
              <button @click="closeModal"
                class="p-3 bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-2xl hover:rotate-90 transition-all duration-300 text-[10px] font-black group">
                <XIcon class="h-6 w-6 group-hover:scale-110 transition-transform" />
              </button>
            </div>

            <!-- Modal Body (Scrollable) -->
            <div class="flex-1 overflow-y-auto p-8 pt-0 custom-scrollbar">
              <!-- Mini Chart -->
              <div
                class="bg-slate-50/50 dark:bg-slate-800/50 rounded-[1.5rem] border border-slate-100 dark:border-slate-700/50 p-6 mb-8">
                <div class="flex items-center justify-between mb-4">
                  <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Connectivity Timeline
                  </h4>
                  <div class="flex items-center gap-4 text-[10px] font-bold">
                    <div class="flex items-center gap-1.5">
                      <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div><span
                        class="text-emerald-600 dark:text-emerald-400">ONLINE</span>
                    </div>
                    <div class="flex items-center gap-1.5">
                      <div class="w-1.5 h-1.5 rounded-full bg-red-500"></div><span
                        class="text-red-600 dark:text-red-400">OFFLINE</span>
                    </div>
                  </div>
                </div>
                <div class="h-32">
                  <apexchart v-if="deviceHistory.length > 0" type="line" height="100%" :options="deviceChartOptions"
                    :series="deviceChartSeries"></apexchart>
                  <div v-else class="h-full flex items-center justify-center text-slate-400 italic text-xs">Generating
                    heatmap...</div>
                </div>
              </div>

              <!-- History List -->
              <div class="space-y-4">
                <div class="flex items-center justify-between px-2">
                  <h4 class="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Detailed Logs</h4>
                  <p class="text-[10px] font-bold text-slate-400">{{ historyTotal }} Events Found</p>
                </div>

                <div class="grid grid-cols-1 gap-3">
                  <div v-for="h in deviceHistory" :key="h.id"
                    class="flex items-center justify-between p-4 rounded-2xl bg-white dark:bg-slate-800/50 border border-slate-100 dark:border-slate-700/50 hover:border-blue-500/30 hover:shadow-lg hover:shadow-blue-500/5 transition-all">
                    <div class="flex items-center gap-4">
                      <div
                        :class="h.status === 'online' ? 'bg-emerald-500 text-emerald-100' : 'bg-red-500 text-red-100'"
                        class="w-10 h-10 rounded-xl flex items-center justify-center shadow-inner">
                        <component :is="h.status === 'online' ? WifiIcon : WifiOffIcon" class="h-5 w-5" />
                      </div>
                      <div>
                        <span class="text-xs font-black uppercase tracking-widest"
                          :class="h.status === 'online' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'">
                          {{ h.status }}
                        </span>
                        <p class="text-[10px] text-slate-500 mt-0.5 leading-none">
                          {{ h.status === 'online' ? 'Connected successfully' : 'Connection dropped' }}
                        </p>
                      </div>
                    </div>
                    <div class="text-right">
                      <div class="text-[11px] font-bold text-slate-900 dark:text-slate-200">
                        {{ format(new Date(h.changed_at), 'HH:mm:ss') }}
                      </div>
                      <div class="text-[9px] text-slate-400 uppercase font-black tracking-tight mt-0.5">
                        {{ format(new Date(h.changed_at), 'MMM dd, yyyy') }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- History Load More -->
                <div v-if="deviceHistory.length < historyTotal" class="pt-4 pb-8">
                  <button @click="loadMoreHistory" :disabled="loadingHistory"
                    class="w-full py-4 rounded-2xl bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 text-xs font-black uppercase tracking-widest hover:bg-slate-200 dark:hover:bg-slate-700 transition-all flex items-center justify-center gap-2 border border-transparent hover:border-slate-200 dark:hover:border-slate-700">
                    <Loader2Icon v-if="loadingHistory" class="h-4 w-4 animate-spin text-blue-500" />
                    <span v-else>Load Older Events</span>
                  </button>
                </div>

                <div v-else-if="deviceHistory.length > 0" class="py-10 text-center">
                  <div class="w-1.5 h-1.5 bg-slate-300 dark:bg-slate-700 rounded-full mx-auto mb-2 opacity-50"></div>
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">End of History</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { formatDistance, format } from 'date-fns'
import {
  RefreshCwIcon, SearchIcon, ActivityIcon, ArrowRightCircleIcon, XIcon, Loader2Icon, ZapOffIcon, InboxIcon,
  ChevronLeftIcon, ChevronRightIcon, LaptopIcon, SmartphoneIcon, ServerIcon, GlobeIcon, CpuIcon, TvIcon, WifiIcon, WifiOffIcon,
  TabletIcon, MonitorIcon, RouterIcon, NetworkIcon, LayersIcon, RssIcon, PrinterIcon, HardDriveIcon, Gamepad2Icon, HelpCircleIcon, LightbulbIcon, PlugIcon, MicrochipIcon, CameraIcon, WavesIcon, SpeakerIcon, PlayIcon
} from 'lucide-vue-next'

// State
const events = ref([])
const stats = ref([])
const loading = ref(false)
const loadingStats = ref(false)
const onlineNowCount = ref(0)
const statsTimeRange = ref(24) // Default to 24 hours
const timeOptions = [
  { label: '24h', value: 24 },
  { label: '7d', value: 168 }, // 7 * 24
  { label: '30d', value: 720 } // 30 * 24
]

// Main Pagination & Filtering
const currentPage = ref(1)
const totalEvents = ref(0)
const itemsPerPage = 20
const search = ref('')
const statusFilter = ref('')

// Modal / Device History
const selectedDevice = ref(null)
const deviceHistory = ref([])
const historyPage = ref(0)
const historyTotal = ref(0)
const loadingHistory = ref(false)

const totalPages = computed(() => Math.ceil(totalEvents.value / itemsPerPage) || 1)

const visiblePages = computed(() => {
  const pages = []
  const range = 2
  for (let i = Math.max(1, currentPage.value - range); i <= Math.min(totalPages.value, currentPage.value + range); i++) {
    pages.push(i)
  }
  return pages
})

const iconMap = {
  smartphone: SmartphoneIcon, tablet: TabletIcon, laptop: LaptopIcon, monitor: MonitorIcon, server: ServerIcon,
  router: RouterIcon, network: NetworkIcon, layers: LayersIcon, rss: RssIcon, tv: TvIcon, speaker: SpeakerIcon,
  play: PlayIcon, cpu: CpuIcon, lightbulb: LightbulbIcon, plug: PlugIcon, microchip: MicrochipIcon,
  camera: CameraIcon, waves: WavesIcon, printer: PrinterIcon, 'hard-drive': HardDriveIcon,
  'gamepad-2': Gamepad2Icon, 'help-circle': HelpCircleIcon, 'globe': GlobeIcon
}

const getIcon = (iconName, deviceType) => {
  // Priority 1: Specifically set icon
  if (iconName && iconMap[iconName.toLowerCase()]) {
    return iconMap[iconName.toLowerCase()]
  }

  // Priority 2: Inferred icon from type
  const typeKey = deviceType?.toLowerCase()
  if (typeKey) {
    if (typeKey.includes('mobile') || typeKey.includes('phone')) return SmartphoneIcon
    if (typeKey.includes('laptop')) return LaptopIcon
    if (typeKey.includes('desktop') || typeKey.includes('monitor')) return MonitorIcon
    if (typeKey.includes('server')) return ServerIcon
    if (typeKey.includes('router') || typeKey.includes('gateway')) return RouterIcon
    if (typeKey.includes('iot') || typeKey.includes('cpu')) return CpuIcon
    if (typeKey.includes('tv') || typeKey.includes('television')) return TvIcon
    if (typeKey.includes('printer')) return PrinterIcon
  }

  // Fallback
  return HelpCircleIcon
}

// Data Fetching
const fetchCount = async () => {
  try {
    const params = { status: statusFilter.value || undefined, search: search.value || undefined }
    const res = await axios.get('/api/v1/events/count', { params })
    totalEvents.value = res.data.total
  } catch (err) { console.error('Count failed', err) }
}

const fetchData = async () => {
  loading.value = true
  try {
    await fetchCount()
    const offset = (currentPage.value - 1) * itemsPerPage
    const params = {
      limit: itemsPerPage,
      offset: offset,
      status: statusFilter.value || undefined,
      search: search.value || undefined
    }
    const response = await axios.get('/api/v1/events/', { params })
    events.value = response.data

    // Approximate Online Now
    const devRes = await axios.get('/api/v1/devices/')
    onlineNowCount.value = devRes.data.filter(d => d.status === 'online').length
  } catch (err) {
    console.error('Failed to fetch events', err)
  } finally {
    loading.value = false
  }
}

let debounceTimer = null
const debounceFetch = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    currentPage.value = 1
    fetchData()
  }, 400)
}

const changePage = (p) => {
  if (p < 1 || p > totalPages.value) return
  currentPage.value = p
  fetchData()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const fetchStats = async () => {
  loadingStats.value = true
  try {
    const response = await axios.get(`/api/v1/events/stats?hours=${statsTimeRange.value}`)
    stats.value = response.data
  } catch (err) {
    console.error('Failed to fetch stats', err)
  } finally {
    loadingStats.value = false
  }
}

const showDeviceDetail = async (device) => {
  selectedDevice.value = device
  deviceHistory.value = []
  historyPage.value = 0
  await fetchDeviceHistoryCount(device.device_id)
  await loadMoreHistory()
}

const fetchDeviceHistoryCount = async (id) => {
  try {
    const res = await axios.get(`/api/v1/events/device/${id}/count`)
    historyTotal.value = res.data.total
  } catch (err) { console.error(err) }
}

const loadMoreHistory = async () => {
  if (!selectedDevice.value) return
  loadingHistory.value = true
  try {
    const limit = 20
    const offset = historyPage.value * limit
    const response = await axios.get(`/api/v1/events/device/${selectedDevice.value.device_id}`, {
      params: { limit, offset }
    })
    deviceHistory.value = [...deviceHistory.value, ...response.data]
    historyPage.value++
  } catch (err) {
    console.error('Failed to fetch device history', err)
  } finally {
    loadingHistory.value = false
  }
}

const closeModal = () => {
  selectedDevice.value = null
}

// Charts Config
const chartOptions = computed(() => ({
  chart: {
    id: 'network-trend',
    type: 'line',
    stacked: false,
    toolbar: { show: false },
    animations: { enabled: true, easing: 'easeinout', speed: 800 },
    background: 'transparent',
    fontFamily: 'inherit'
  },
  colors: ['#10b981', '#ef4444'],
  stroke: { curve: 'smooth', width: 3 },
  xaxis: {
    type: 'datetime',
    labels: {
      style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 600 },
      formatter: function (val, timestamp) {
        // Use time-only for 24h view, date for longer ranges
        const date = new Date(timestamp)
        if (statsTimeRange.value <= 24) {
          return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
      }
    },
    axisBorder: { show: false }, axisTicks: { show: false }
  },
  yaxis: {
    min: 0, forceNiceScale: true,
    labels: { style: { colors: '#94a3b8', fontSize: '9px', fontWeight: 600 } }
  },
  grid: { borderColor: 'rgba(148, 163, 184, 0.1)', strokeDashArray: 6, padding: { left: 10, right: 10 } },
  tooltip: { theme: 'dark', x: { format: 'HH:mm' } },
  dataLabels: { enabled: false },
  legend: { position: 'top', horizontalAlign: 'right', fontSize: '10px', fontWeight: 700, labels: { colors: '#94a3b8' }, markers: { radius: 12 } }
}))

const chartSeries = computed(() => {
  // Client-side aggregation
  const buckets = {}

  stats.value.forEach(s => {
    const date = new Date(s.timestamp)

    if (statsTimeRange.value <= 24) {
      // Round to nearest 5 min
      const min = date.getMinutes()
      date.setMinutes(Math.floor(min / 5) * 5, 0, 0)
    } else if (statsTimeRange.value <= 168) {
      // Round to 4 hours
      const hours = date.getHours()
      date.setHours(Math.floor(hours / 4) * 4, 0, 0, 0)
    } else {
      // Round to day
      date.setHours(0, 0, 0, 0)
    }

    const key = date.getTime()
    if (!buckets[key]) buckets[key] = { online: 0, offline: 0 }
    buckets[key].online += s.online_count
    buckets[key].offline += s.offline_count
  })

  const sortedKeys = Object.keys(buckets).sort()

  return [
    { name: 'Online', data: sortedKeys.map(k => ({ x: parseInt(k), y: buckets[k].online })) },
    { name: 'Offline', data: sortedKeys.map(k => ({ x: parseInt(k), y: buckets[k].offline })) }
  ]
})

const deviceChartOptions = computed(() => ({
  chart: { toolbar: { show: false }, background: 'transparent', animations: { enabled: true } },
  xaxis: { type: 'datetime', labels: { show: false }, axisBorder: { show: false }, axisTicks: { show: false } },
  yaxis: { labels: { show: false }, min: 0, max: 1.2 },
  grid: { show: false, padding: { left: -10, right: -10 } },
  tooltip: { theme: 'dark', x: { format: 'HH:mm' } },
  colors: ['#3b82f6'],
  stroke: { curve: 'stepline', width: 3 },
  markers: {
    size: 4,
    colors: ['#3b82f6'],
    strokeColors: '#fff',
    strokeWidth: 2,
    hover: { size: 6 }
  },
  dataLabels: { enabled: false }
}))

const deviceChartSeries = computed(() => [{
  name: 'State',
  data: deviceHistory.value.slice().reverse().map(h => ({
    x: new Date(h.changed_at).getTime(),
    y: h.status === 'online' ? 1 : 0.2
  }))
}])

onMounted(() => {
  fetchData()
  fetchStats()
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  backdrop-filter: blur(0px);
  transform: scale(0.95);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.1);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.3);
}
</style>
