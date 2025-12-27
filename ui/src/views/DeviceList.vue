<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Devices</h1>
      <button 
        @click="triggerScan" 
        :disabled="isScanning"
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
      >
        <component :is="isScanning ? Loader2 : RefreshCw" class="h-4 w-4 mr-2" :class="{ 'animate-spin': isScanning }" />
        {{ isScanning ? 'Scanning...' : 'Scan Now' }}
      </button>
    </div>

    <!-- Error state -->
    <div v-if="error" class="p-4 bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 rounded-lg border border-red-100 dark:border-red-900/30">
      {{ error }}
    </div>

    <!-- Device Table -->
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-gray-100 dark:border-slate-700 overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 dark:divide-slate-700">
        <thead class="bg-gray-50 dark:bg-slate-900">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Device</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Vendor</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Last Seen</th>
            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200 dark:divide-slate-700">
          <tr v-for="device in devices" :key="device.id" class="hover:bg-gray-50 dark:hover:bg-slate-700/50 transition">
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="flex items-center space-x-3">
                <div class="relative">
                  <div class="p-2 bg-gray-100 dark:bg-slate-700 rounded-lg">
                    <component :is="getIcon(device.icon || 'help-circle')" class="h-5 w-5 text-gray-600 dark:text-gray-400" />
                  </div>
                  <span 
                    class="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-white dark:border-slate-800"
                    :class="isOnline(device) ? 'bg-green-500' : 'bg-gray-300'"
                  ></span>
                </div>
                <div>
                  <div class="text-sm font-bold text-gray-900 dark:text-white">{{ device.display_name || 'Unknown Device' }}</div>
                  <div class="text-xs text-gray-500 font-mono">{{ device.ip }}</div>
                </div>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div class="text-sm text-gray-900 dark:text-gray-200">{{ device.vendor || 'Unknown Vendor' }}</div>
              <div class="text-xs text-gray-500 font-mono">{{ device.mac || 'No MAC' }}</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span class="px-2.5 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                {{ device.device_type || 'unclassified' }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
              {{ formatTime(device.last_seen) }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right space-x-2">
              <button 
                @click="editDevice(device)" 
                class="p-1.5 text-gray-400 hover:text-blue-600 transition dark:hover:text-blue-400"
                title="Edit Device"
              >
                <Edit2 class="h-4 w-4" />
              </button>
              <router-link 
                :to="'/devices/' + device.id" 
                class="p-1.5 text-gray-400 hover:text-gray-900 transition dark:hover:text-white inline-block"
                title="View Details"
              >
                <ExternalLink class="h-4 w-4" />
              </router-link>
            </td>
          </tr>
          <tr v-if="devices.length === 0 && !loading">
            <td colspan="5" class="px-6 py-12 text-center text-gray-500 dark:text-gray-400 italic">
              No devices found. Run a scan to discover your network.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Edit Modal -->
    <div v-if="editingDevice" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md border border-slate-200 dark:border-slate-700 overflow-hidden transform transition-all scale-100">
        <div class="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center">
          <h3 class="text-lg font-bold text-slate-800 dark:text-white">Edit Device</h3>
          <button @click="editingDevice = null" class="text-slate-400 hover:text-slate-600 dark:hover:text-white">
            <X class="h-5 w-5" />
          </button>
        </div>
        
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-1">Friendly Name</label>
            <input 
              v-model="editForm.display_name" 
              class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-slate-900 dark:text-white"
              placeholder="e.g. My Phone"
            />
          </div>
          
          <div class="grid grid-cols-1 gap-4">
            <div>
              <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-1">Device Type</label>
              <select 
                v-model="editForm.device_type" 
                class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-slate-900 dark:text-white"
              >
                <option v-for="type in deviceTypes" :key="type" :value="type">{{ type }}</option>
              </select>
            </div>
            
            <div>
              <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-1">Select Icon</label>
              <div class="grid grid-cols-7 gap-2 p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-xl">
                <button 
                  v-for="(iconComp, key) in availableIcons" 
                  :key="key"
                  @click="editForm.icon = key"
                  type="button"
                  class="p-2.5 flex items-center justify-center rounded-lg border-2 transition-all"
                  :class="editForm.icon === key ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 text-blue-600' : 'border-transparent hover:bg-white dark:hover:bg-slate-800 text-slate-400'"
                  :title="key"
                >
                  <component :is="iconComp" class="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-500 dark:text-slate-400 uppercase mb-1">Vendor</label>
            <input 
              v-model="editForm.vendor" 
              class="w-full px-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none text-slate-900 dark:text-white"
            />
          </div>
        </div>

        <div class="px-6 py-4 bg-slate-50 dark:bg-slate-900/50 flex justify-end space-x-3">
          <button @click="editingDevice = null" class="px-4 py-2 text-slate-500 hover:text-slate-700 font-medium">Cancel</button>
          <button 
            @click="saveDevice" 
            :disabled="saving"
            class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-bold disabled:opacity-50"
          >
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import axios from 'axios'
import { 
  Smartphone, Tablet, Laptop, Monitor, Server, Router as RouterIcon, 
  Network, Layers, Rss, Tv, Cpu, Printer, HardDrive, Gamepad2, 
  HelpCircle, Edit2, ExternalLink, X, RefreshCw, Loader2,
  Lightbulb, Plug, Microchip, Camera, Waves, Speaker, Play
} from 'lucide-vue-next'

const devices = ref([])
const isScanning = ref(false)
const loading = ref(true)
const error = ref('')
const saving = ref(false)

const editingDevice = ref(null)
const editForm = reactive({
  display_name: '',
  device_type: '',
  vendor: '',
  icon: ''
})

const deviceTypes = [
  'Smartphone', 'Tablet', 'Laptop', 'Desktop', 'Server', 
  'Router/Gateway', 'Network Bridge', 'Switch', 'Access Point', 
  'TV/Entertainment', 'Audio/Speaker', 'Streaming Device', 
  'IoT Device', 'Smart Bulb', 'Smart Plug/Switch',
  'Microcontroller', 'Security Camera', 'Sensor', 'Printer', 
  'NAS/Storage', 'Game Console', 'Generic', 'unknown'
]

const availableIcons = {
  'smartphone': Smartphone,
  'tablet': Tablet,
  'laptop': Laptop,
  'monitor': Monitor,
  'server': Server,
  'router': RouterIcon,
  'network': Network,
  'layers': Layers,
  'rss': Rss,
  'tv': Tv,
  'speaker': Speaker,
  'play': Play,
  'cpu': Cpu,
  'lightbulb': Lightbulb,
  'plug': Plug,
  'microchip': Microchip,
  'camera': Camera,
  'waves': Waves,
  'printer': Printer,
  'hard-drive': HardDrive,
  'gamepad-2': Gamepad2,
  'help-circle': HelpCircle
}

const getIcon = (name) => {
  return availableIcons[name] || HelpCircle
}

const fetchDevices = async () => {
  error.value = ''
  try {
    const res = await axios.get('/api/v1/devices/')
    devices.value = res.data
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load devices. Backend might be offline.'
  } finally {
    loading.value = false
  }
}

const editDevice = (device) => {
  editingDevice.value = device
  editForm.display_name = device.display_name
  editForm.device_type = device.device_type
  editForm.vendor = device.vendor
  editForm.icon = device.icon || 'help-circle'
}

const saveDevice = async () => {
  saving.value = true
  try {
    const res = await axios.put(`/api/v1/devices/${editingDevice.value.id}`, editForm)
    Object.assign(editingDevice.value, res.data)
    editingDevice.value = null
  } catch (e) {
    alert('Failed to save device updates')
    console.error(e)
  } finally {
    saving.value = false
  }
}

const checkActiveScan = async () => {
    try {
        const res = await axios.get('/api/v1/scans/')
        isScanning.value = res.data.some(s => s.status === 'queued' || s.status === 'running')
    } catch (e) {
        console.error('Failed to check active scans', e)
    }
}

const triggerScan = async () => {
    isScanning.value = true
    try {
        await axios.post('/api/v1/scans/discovery')
    } catch (error) {
        console.error('Scan failed:', error)
    } finally {
        await checkActiveScan()
    }
}

const isOnline = (d) => {
  if (!d.last_seen) return false
  const lastSeenDate = new Date(d.last_seen)
  return (new Date() - lastSeenDate) < 300000 // 5 mins
}

const formatTime = (t) => {
  if (!t) return 'Never'
  return new Date(t).toLocaleString()
}

let pollInterval = null

onMounted(() => {
  fetchDevices()
  checkActiveScan()
  pollInterval = setInterval(() => {
    checkActiveScan()
    fetchDevices()
  }, 10000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>
