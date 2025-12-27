<template>
    <div class="space-y-6">
        <div class="flex justify-between items-center">
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white">IP Occupancy</h1>

            <div
                class="flex items-center space-x-3 bg-white dark:bg-slate-800 p-2 rounded-lg border border-gray-100 dark:border-slate-700 shadow-sm">
                <label class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">Subnet:</label>
                <select v-model="selectedSubnet"
                    class="bg-transparent text-sm font-medium text-gray-900 dark:text-white outline-none cursor-pointer">
                    <option v-for="s in availableSubnets" :key="s" :value="s">{{ s }}.0/24</option>
                </select>
            </div>
        </div>

        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm p-6 border border-gray-100 dark:border-slate-700">
            <div class="mb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 class="text-lg font-bold text-gray-800 dark:text-white">Subnet Map</h2>
                    <p class="text-xs text-gray-500">Visualizing {{ selectedSubnet }}.1 - {{ selectedSubnet }}.254</p>
                </div>
                <div class="flex space-x-4 text-[10px] font-bold uppercase tracking-wider">
                    <div class="flex items-center text-green-600 dark:text-green-400"><span
                            class="w-2.5 h-2.5 bg-green-500 rounded-sm mr-2 shadow-sm"></span> Online</div>
                    <div class="flex items-center text-amber-600 dark:text-amber-400"><span
                            class="w-2.5 h-2.5 bg-amber-400 rounded-sm mr-2 shadow-sm"></span> Offline</div>
                    <div class="flex items-center text-slate-400 dark:text-slate-500"><span
                            class="w-2.5 h-2.5 bg-slate-100 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-sm mr-2"></span>
                        Free</div>
                </div>
            </div>

            <div class="flex flex-wrap gap-1">
                <div v-for="i in 254" :key="i"
                    class="w-6 h-6 flex items-center justify-center text-[7px] font-mono font-bold rounded-sm transition-all duration-150 cursor-pointer relative group border border-transparent hover:z-20 hover:scale-150 hover:shadow-lg hover:border-blue-400"
                    :class="getStatusClass(i)" @click="goToDevice(i)">
                    {{ i }}

                    <!-- Ultra Compact Tooltip -->
                    <div v-if="getDevice(i)"
                        class="invisible group-hover:visible absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-white dark:bg-slate-900 text-slate-900 dark:text-white text-[10px] p-2 rounded-lg shadow-2xl z-50 w-44 border border-slate-100 dark:border-slate-700 origin-bottom ring-4 ring-slate-900/5">
                        <div class="flex items-center space-x-2">
                            <div class="p-1 bg-slate-50 dark:bg-slate-800 rounded">
                                <component :is="getIcon(getDevice(i).icon)"
                                    class="h-3.5 w-3.5 text-slate-600 dark:text-slate-400" />
                            </div>
                            <div class="flex-1 min-w-0 text-left">
                                <div class="font-bold truncate text-[10px]">{{ getDevice(i).display_name ||
                                    getDevice(i).ip }}</div>
                                <div class="text-[8px] text-slate-500 font-mono truncate leading-none">{{
                                    getDevice(i).ip }}</div>
                            </div>
                        </div>
                        <div
                            class="mt-1.5 text-[8px] space-y-0.5 border-t border-slate-50 dark:border-slate-800 pt-1.5">
                            <div v-if="getDevice(i).mac"
                                class="text-slate-400 font-mono truncate flex justify-between uppercase">
                                <span>MAC</span> <span class="text-slate-600 dark:text-slate-300 ml-2 truncate">{{
                                    getDevice(i).mac }}</span>
                            </div>
                            <div v-if="getDevice(i).vendor"
                                class="text-blue-500 font-bold truncate flex justify-between">
                                <span>Vendor</span> <span class="max-w-[70%] truncate ml-2">{{ getDevice(i).vendor
                                    }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import {
    Smartphone, Tablet, Laptop, Monitor, Server, Router as RouterIcon,
    Network, Layers, Rss, Tv, Cpu, Printer, HardDrive, Gamepad2, HelpCircle,
    Lightbulb, Plug, Microchip, Camera, Waves, Speaker, Play
} from 'lucide-vue-next'

const devices = ref([])
const router = useRouter()
const selectedSubnet = ref('')

const availableIcons = {
    'smartphone': Smartphone, 'tablet': Tablet, 'laptop': Laptop, 'monitor': Monitor,
    'server': Server, 'router': RouterIcon, 'network': Network, 'layers': Layers,
    'rss': Rss, 'tv': Tv, 'speaker': Speaker, 'play': Play, 'cpu': Cpu,
    'lightbulb': Lightbulb, 'plug': Plug, 'microchip': Microchip, 'camera': Camera,
    'waves': Waves, 'printer': Printer, 'hard-drive': HardDrive, 'gamepad-2': Gamepad2,
    'help-circle': HelpCircle
}

const getIcon = (name) => availableIcons[name] || HelpCircle

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
        return parts.length === 4 &&
            `${parts[0]}.${parts[1]}.${parts[2]}` === selectedSubnet.value &&
            parseInt(parts[3]) === suffix
    })
}

const getStatusClass = (suffix) => {
    const d = getDevice(suffix)
    if (!d) return 'bg-slate-50 dark:bg-slate-800/40 text-slate-300 dark:text-slate-600 border-transparent'

    // Online check
    const diff = new Date() - new Date(d.last_seen)
    if (diff < 300 * 1000) {
        return 'bg-green-500 text-white border-green-600 shadow-sm'
    }
    return 'bg-amber-400 text-white border-amber-500 shadow-sm'
}

const goToDevice = (suffix) => {
    const d = getDevice(suffix)
    if (d) {
        router.push(`/devices/${d.id}`)
    }
}

const formatTime = (t) => {
    if (!t) return 'N/A'
    const date = new Date(t)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
    const res = await axios.get('/api/v1/devices/')
    devices.value = res.data

    // Auto-detect most common subnet
    if (availableSubnets.value.length > 0) {
        // Count occurrences
        const counts = {}
        devices.value.forEach(d => {
            const sub = d.ip.split('.').slice(0, 3).join('.')
            counts[sub] = (counts[sub] || 0) + 1
        })
        selectedSubnet.value = Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b)
    }
})
</script>

<style scoped></style>
