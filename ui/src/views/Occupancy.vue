<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
                <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">IP Occupancy</h1>
                <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Network map for {{ selectedSubnet }}.0/24</p>
            </div>
            <div
                class="relative flex items-center gap-3 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 px-4 py-2.5 shadow-sm hover:border-blue-400/50 transition-colors group">
                <Network class="w-5 h-5 text-slate-400 group-hover:text-blue-500 transition-colors" />
                <div class="flex flex-col pr-2">
                    <span
                        class="text-[10px] uppercase tracking-wider font-bold text-slate-500 dark:text-slate-400 leading-none mb-1">Select
                        Network</span>
                    <div class="relative flex items-center gap-2">
                        <!-- Filter Dropdown -->
                        <div class="relative min-w-[140px]" v-click-outside="() => isFilterOpen = false">
                            <button @click="isFilterOpen = !isFilterOpen"
                                class="w-full flex items-center justify-between px-3 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 hover:border-blue-400/50 hover:shadow-sm transition-all focus:ring-2 focus:ring-blue-500/20 active:scale-[0.98]">
                                <span class="truncate mr-2">
                                    {{ filterStatus === 'all' ? 'All Status' : (filterStatus === 'online'
                                        ? 'Online Only'
                                        : (filterStatus === 'offline' ? 'Offline Only' : 'Available Only')) }}
                                </span>
                                <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200"
                                    :class="{ 'rotate-180': isFilterOpen }" />
                            </button>

                            <transition enter-active-class="transition duration-100 ease-out"
                                enter-from-class="transform scale-95 opacity-0"
                                enter-to-class="transform scale-100 opacity-100"
                                leave-active-class="transition duration-75 ease-in"
                                leave-from-class="transform scale-100 opacity-100"
                                leave-to-class="transform scale-95 opacity-0">
                                <div v-if="isFilterOpen"
                                    class="absolute z-50 top-full left-0 mt-2 w-full min-w-[140px] bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl overflow-hidden py-1">
                                    <button v-for="opt in ['all', 'online', 'offline', 'available']" :key="opt"
                                        @click="filterStatus = opt; isFilterOpen = false"
                                        class="w-full text-left px-4 py-2 text-sm flex items-center justify-between hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors group"
                                        :class="filterStatus === opt ? 'text-blue-600 dark:text-blue-400 bg-blue-50/50 dark:bg-blue-900/10' : 'text-slate-600 dark:text-slate-300'">
                                        <span class="capitalize">{{ opt }}</span>
                                        <Check v-if="filterStatus === opt" class="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </transition>
                        </div>


                        <div class="relative min-w-[200px]" v-click-outside="() => isSubnetOpen = false">
                            <button @click="isSubnetOpen = !isSubnetOpen"
                                class="w-full flex items-center justify-between px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 hover:border-blue-400/50 hover:shadow-sm transition-all focus:ring-2 focus:ring-blue-500/20 active:scale-[0.98]">
                                <span class="truncate mr-2">
                                    {{ selectedSubnet ? `${selectedSubnet}.0/24` : 'Select Subnet' }}
                                </span>
                                <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-200"
                                    :class="{ 'rotate-180': isSubnetOpen }" />
                            </button>

                            <transition enter-active-class="transition duration-100 ease-out"
                                enter-from-class="transform scale-95 opacity-0"
                                enter-to-class="transform scale-100 opacity-100"
                                leave-active-class="transition duration-75 ease-in"
                                leave-from-class="transform scale-100 opacity-100"
                                leave-to-class="transform scale-95 opacity-0">
                                <div v-if="isSubnetOpen"
                                    class="absolute z-50 top-full left-0 mt-2 w-full min-w-[200px] bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl overflow-hidden py-1 max-h-60 overflow-y-auto custom-scrollbar">
                                    <button v-for="sub in availableSubnets" :key="sub"
                                        @click="selectedSubnet = sub; isSubnetOpen = false"
                                        class="w-full text-left px-4 py-2 text-sm flex items-center justify-between hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors group"
                                        :class="selectedSubnet === sub ? 'text-blue-600 dark:text-blue-400 bg-blue-50/50 dark:bg-blue-900/10' : 'text-slate-600 dark:text-slate-300'">
                                        <span class="font-mono">{{ sub }}.0/24</span>
                                        <Check v-if="selectedSubnet === sub" class="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </transition>
                        </div>
                        <button @click="fetchOccupancy" :disabled="loading"
                            class="p-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-slate-500 dark:text-slate-400"
                            v-tooltip="'Refresh Occupancy Data'">
                            <component :is="refreshIcon" class="w-5 h-5"
                                :class="{ 'animate-spin': loading, 'text-emerald-500': showSuccess }" />
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Summary Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div v-for="stat in summaryStats" :key="stat.label"
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
                        <span
                            :class="[stat.changeType === 'up' ? 'text-emerald-600' : 'text-rose-500', 'text-[10px] font-bold']">
                            {{ stat.changeType === 'down' ? '↓' : '↑' }} {{ stat.change }}
                        </span>
                    </div>
                </div>

                <!-- Center Content: Metric & Label -->
                <div class="relative z-10 flex flex-col items-center text-center -mt-1">
                    <p class="text-2xl font-black text-slate-900 dark:text-white tracking-tight leading-none">
                        {{ stat.value }}
                    </p>
                    <p :style="{ color: stat.color }"
                        class="text-[9px] font-black uppercase tracking-[0.2em] opacity-80 mt-1">
                        {{ stat.label }}
                    </p>
                </div>
            </div>
        </div>

        <!-- IP Grid -->
        <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-6">
            <div class="space-y-6">
                <div v-for="rowIndex in 8" :key="rowIndex">
                    <div class="flex items-center gap-3 mb-3">
                        <span class="text-xs font-medium text-slate-500 dark:text-slate-400">.{{ (rowIndex - 1) * 32 + 1
                        }} - .{{ Math.min(rowIndex * 32, 254) }}</span>
                        <div class="flex-1 h-px bg-slate-200 dark:bg-slate-700"></div>
                    </div>
                    <div class="grid grid-cols-8 md:grid-cols-16 gap-2">
                        <template v-for="i in 32" :key="i">
                            <div v-if="((rowIndex - 1) * 32 + i) <= 254" class="relative group">
                                <div :class="['h-10 flex flex-col items-center justify-center text-[10px] font-mono leading-none rounded cursor-pointer transition-all gap-0.5 px-0.5', getStatusClass((rowIndex - 1) * 32 + i)]"
                                    @click="goToDevice((rowIndex - 1) * 32 + i)">
                                    <span class="opacity-40 text-[9px] font-bold">{{ (rowIndex - 1) * 32 + i }}</span>
                                    <span v-if="getDevice((rowIndex - 1) * 32 + i)"
                                        class="truncate w-full text-center font-bold px-0.5">
                                        {{ getDevice((rowIndex - 1) * 32 + i).display_name || getDevice((rowIndex - 1) *
                                            32 + i).hostname || 'Active' }}
                                    </span>
                                </div>
                                <div v-if="getDevice((rowIndex - 1) * 32 + i)"
                                    class="pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200 absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-[10px] p-3 rounded-lg shadow-xl z-50 w-52">
                                    <div class="font-semibold truncate text-xs">{{ getDevice((rowIndex - 1) * 32 +
                                        i).display_name || getDevice((rowIndex - 1) * 32 + i).ip }}</div>
                                    <div class="text-[10px] opacity-75 font-mono truncate mt-1">{{ getDevice((rowIndex -
                                        1) * 32 + i).mac || 'N/A' }}</div>

                                    <div class="mt-2 space-y-1 border-t border-white/10 dark:border-slate-200 pt-2">
                                        <div class="flex justify-between items-center">
                                            <span class="opacity-75">Status:</span>
                                            <span
                                                :class="getDevice((rowIndex - 1) * 32 + i).status === 'online' ? 'text-emerald-400 dark:text-emerald-600' : 'text-slate-400 dark:text-slate-500'">
                                                {{ getDevice((rowIndex - 1) * 32 + i).status }}
                                            </span>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="opacity-75">Last Seen:</span>
                                            <span>{{ formatRelativeTime(getDevice((rowIndex - 1) * 32 + i).last_seen)
                                                }}</span>
                                        </div>
                                        <div class="flex justify-between items-center">
                                            <span class="opacity-75">Open Ports:</span>
                                            <span class="font-mono text-blue-400 dark:text-blue-600">
                                                {{ parsePortsCount(getDevice((rowIndex - 1) * 32 + i).open_ports) }}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </template>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import { Network, ChevronDown, Database, Wifi, ZapOff, CheckCircle, RefreshCw, Check } from 'lucide-vue-next'
import Sparkline from '@/components/Sparkline.vue'
import { formatRelativeTime } from '@/utils/date'

const devices = ref([])
const router = useRouter()
const selectedSubnet = ref('')
const isSubnetOpen = ref(false)
const filterStatus = ref('all')
const isFilterOpen = ref(false)



const vClickOutside = {
    mounted(el, binding) {
        el._clickOutside = (event) => {
            if (!(el === event.target || el.contains(event.target))) {
                binding.value(event)
            }
        }
        document.addEventListener('click', el._clickOutside)
    },
    unmounted(el) {
        document.removeEventListener('click', el._clickOutside)
    }
}

const availableSubnets = computed(() => {
    const subnets = new Set()
    devices.value.forEach(d => {
        const parts = d.ip.split('.')
        if (parts.length === 4) {
            subnets.add(`${parts[0]}.${parts[1]}.${parts[2]}`)
        }
    })
    return Array.from(subnets).sort()
})

const getDevice = (suffix) => {
    return devices.value.find(d => {
        const parts = d.ip.split('.')
        return parts.length === 4 && `${parts[0]}.${parts[1]}.${parts[2]}` === selectedSubnet.value && parseInt(parts[3]) === suffix
    })
}

const summaryStats = computed(() => {
    const subnetDevices = devices.value.filter(d => {
        const parts = d.ip.split('.')
        return parts.length === 4 && `${parts[0]}.${parts[1]}.${parts[2]}` === selectedSubnet.value
    })
    const onlineCount = subnetDevices.filter(d => d.status === 'online').length
    const offlineCount = subnetDevices.filter(d => d.status === 'offline').length
    const usedCount = subnetDevices.length
    const freeCount = 254 - usedCount

    return [
        {
            label: 'Total Known',
            value: usedCount,
            icon: Database,
            color: '#3b82f6',
            bgClass: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400',
            trend: [10, 12, 11, 13, 12, 14, 13],
            change: '2.4%',
            changeType: 'up'
        },
        {
            label: 'Online',
            value: onlineCount,
            icon: Wifi,
            color: '#10b981',
            bgClass: 'bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400',
            trend: [8, 9, 7, 10, 9, 11, 10],
            change: '5.2%',
            changeType: 'up'
        },
        {
            label: 'Offline',
            value: offlineCount,
            icon: ZapOff,
            color: '#f43f5e',
            bgClass: 'bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400',
            trend: [2, 3, 4, 3, 3, 3, 3],
            change: '3.1%',
            changeType: 'up'
        },
        {
            label: 'Available',
            value: freeCount,
            icon: CheckCircle,
            color: '#8b5cf6',
            bgClass: 'bg-violet-100 text-violet-600 dark:bg-violet-900/30 dark:text-violet-400',
            trend: [244, 242, 243, 241, 242, 240, 241],
            change: '0.8%',
            changeType: 'down'
        }
    ]
})

const getStatusClass = (suffix) => {
    const d = getDevice(suffix)
    let opacityClass = ''

    // Dimming Logic & Highlighting
    let highlightClass = ''
    if (filterStatus.value === 'online') {
        if (!d || d.status !== 'online') opacityClass = 'opacity-5 grayscale blur-[1px] transition-all duration-500'
    } else if (filterStatus.value === 'offline') {
        if (!d || d.status !== 'offline') opacityClass = 'opacity-5 grayscale blur-[1px] transition-all duration-500'
    } else if (filterStatus.value === 'available') {
        if (d) {
            opacityClass = 'opacity-5 grayscale blur-[1px] transition-all duration-500'
        } else {
            // Highlight available slots
            highlightClass = 'ring-2 ring-blue-500 bg-blue-100 scale-105 z-10 shadow-md font-bold'
        }
    }

    // Non-used IP: Blue accent
    if (!d) return `bg-blue-50 dark:bg-blue-900/10 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/20 border-blue-100/50 dark:border-blue-800/20 shadow-sm ${opacityClass} ${highlightClass}`

    // Online Device: Emerald accent
    if (d.status === 'online') return `bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-200 ring-1 ring-emerald-200 dark:ring-emerald-800/50 ${opacityClass}`

    // Offline Device: Red accent
    return `bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 hover:bg-red-200 ring-1 ring-red-200 dark:ring-red-800/50 ${opacityClass}`
}

const goToDevice = (suffix) => {
    const d = getDevice(suffix)
    if (d) router.push(`/devices/${d.id}`)
}


const parsePortsCount = (ports) => {
    if (!ports) return 0
    if (Array.isArray(ports)) return ports.length
    try {
        const parsed = JSON.parse(ports)
        return Array.isArray(parsed) ? parsed.length : 0
    } catch (e) {
        return 0
    }
}

const loading = ref(false)
const showSuccess = ref(false)
const refreshIcon = computed(() => showSuccess.value ? CheckCircle : RefreshCw)

const fetchOccupancy = async () => {
    loading.value = true
    try {
        const res = await axios.get('/api/v1/devices/export/json')
        devices.value = res.data.items || res.data

        // Show success state
        showSuccess.value = true
        setTimeout(() => {
            showSuccess.value = false
        }, 2000)
    } catch (e) {
        console.error("Failed to fetch devices:", e)
    } finally {
        loading.value = false
    }
}

onMounted(async () => {
    await fetchOccupancy()
    if (devices.value.length > 0 && !selectedSubnet.value) {
        const counts = {}
        devices.value.forEach(d => {
            const parts = d.ip.split('.')
            if (parts.length === 4) {
                const sub = `${parts[0]}.${parts[1]}.${parts[2]}`
                counts[sub] = (counts[sub] || 0) + 1
            }
        })
        const subnetKeys = Object.keys(counts)
        if (subnetKeys.length > 0) {
            selectedSubnet.value = subnetKeys.reduce((a, b) => counts[a] > counts[b] ? a : b)
        }
    }
})
</script>
