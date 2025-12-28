<template>
  <div class="h-screen flex flex-col pt-16">
    <div
      class="px-4 md:px-6 lg:px-8 py-4 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex items-center justify-between z-10">
      <div class="flex items-center gap-3">
        <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400">
          <svg viewBox="0 0 24 24" class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2">
            <path
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <div>
          <h1 class="text-xl font-bold text-slate-900 dark:text-white">Settings</h1>
          <p class="text-sm text-slate-500">System configuration and preferences</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <button @click="saveSettings" :disabled="saveStatus === 'saving'"
          class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-800"
          :class="[
            saveStatus === 'saving' ? 'bg-blue-600/80 cursor-wait' :
              saveStatus === 'saved' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-blue-600 hover:bg-blue-700',
            'text-white'
          ]" v-tooltip="'Save All Settings'">
          <Loader2 v-if="saveStatus === 'saving'" class="w-4 h-4 animate-spin" />
          <svg v-else-if="saveStatus === 'saved'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <Save v-else class="w-4 h-4" />
          <span>{{ saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved' : 'Save Configuration'
          }}</span>
        </button>
      </div>
    </div>

    <div class="flex-1 overflow-auto p-4 md:p-6 lg:p-8">
      <div class="max-w-6xl mx-auto space-y-6">

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

          <!-- Main Content (Left Column) -->
          <div class="lg:col-span-2 space-y-6">

            <!-- Automated Discovery -->
            <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
              <div class="flex items-center gap-3 mb-6">
                <div class="p-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400">
                  <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h2 class="text-base font-semibold text-slate-900 dark:text-white">Automated Discovery</h2>
                  <p class="text-xs text-slate-500">Configure background network scanning</p>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Left: Subnets -->
                <div class="space-y-3">
                  <label
                    class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Target Subnets
                  </label>
                  <div class="flex gap-2">
                    <input v-model="newSubnet" @keyup.enter="addSubnet" type="text" placeholder="e.g. 192.168.1.0/24"
                      class="flex-1 px-3 py-2 border rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm transition-colors"
                      :class="subnetError ? 'border-red-500' : 'border-slate-300 dark:border-slate-600'" />
                    <button @click="addSubnet"
                      class="p-2 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-lg hover:opacity-90 transition-opacity"
                      v-tooltip="'Add Subnet'">
                      <Plus class="w-5 h-5" />
                    </button>
                  </div>
                  <p v-if="subnetError" class="text-xs text-red-500 font-medium animate-pulse">{{ subnetError }}</p>

                  <div class="flex flex-wrap gap-2 pt-1">
                    <div v-for="s in subnetList" :key="s"
                      class="flex items-center gap-2 px-2.5 py-1 bg-slate-100 dark:bg-slate-700 rounded-full text-sm text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600">
                      <span>{{ s }}</span>
                      <button @click="removeSubnet(s)" class="text-slate-400 hover:text-red-500 transition-colors"
                        v-tooltip="'Remove Subnet'">
                        <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                    <div v-if="subnetList.length === 0" class="text-sm text-slate-400 italic">
                      No subnets configured
                    </div>
                  </div>
                </div>

                <!-- Right: Schedule -->
                <div class="space-y-4">
                  <div>
                    <label
                      class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                      Scan Interval
                    </label>
                    <div class="relative">
                      <select v-model="settings.scan_interval"
                        class="w-full pl-3 pr-10 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm appearance-none">
                        <option value="300">Every 5 minutes</option>
                        <option value="600">Every 10 minutes</option>
                        <option value="1800">Every 30 minutes</option>
                        <option value="3600">Every hour</option>
                        <option value="86400">Once per day</option>
                      </select>
                      <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label
                      class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
                      Last Run
                    </label>
                    <div
                      class="px-3 py-2 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700 text-sm text-slate-600 dark:text-slate-400 flex items-center gap-2">
                      <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
                      {{ formatLastRun(settings.last_discovery_run_at) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- MQTT Configuration -->
            <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
              <div class="flex items-center gap-3 mb-6">
                <div class="p-2 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-purple-600 dark:text-purple-400">
                  <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2">
                    <path
                      d="M8.25 3v1.5M4.5 8.25H3m12.375-3.75a8.25 8.25 0 018.25 8.25H21M6.75 3a12 12 0 0112 12H16.5M3 13.5a8.25 8.25 0 018.25-8.25V6a7.5 7.5 0 00-7.5 7.5v.75m17.625 0V15a6 6 0 01-6 6H12m0 0V21" />
                  </svg>
                </div>
                <div>
                  <h2 class="text-base font-semibold text-slate-900 dark:text-white">MQTT Configuration</h2>
                  <p class="text-xs text-slate-500">Integration with Home Assistant</p>
                </div>
              </div>
              <div class="space-y-4">
                <!-- Connection Details -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div class="md:col-span-2">
                    <label
                      class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Broker
                      Address</label>
                    <input v-model="settings.mqtt_broker" type="text" placeholder="localhost"
                      class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm" />
                  </div>
                  <div>
                    <label
                      class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Port</label>
                    <input v-model="settings.mqtt_port" type="text" placeholder="1883"
                      class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm" />
                  </div>
                </div>

                <!-- Authentication & Topic -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 border-t border-slate-100 dark:border-slate-700 pt-4">
                  <div>
                    <label
                      class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Username
                      (Optional)</label>
                    <input v-model="settings.mqtt_username" type="text" placeholder="mqtt_user" autocomplete="off"
                      class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm" />
                  </div>
                  <div>
                    <label
                      class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Password
                      (Optional)</label>
                    <input v-model="settings.mqtt_password" type="password" placeholder="••••••••"
                      autocomplete="new-password"
                      class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm" />
                  </div>
                  <div>
                    <label
                      class="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Base
                      Topic</label>
                    <input v-model="settings.mqtt_base_topic" type="text" placeholder="network_scanner"
                      class="w-full px-3 py-2 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-900 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Sidebar (Right Column) -->
          <div class="space-y-6">

            <!-- UI Appearance -->
            <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
              <div class="flex items-center gap-3 mb-6">
                <div class="p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg text-emerald-600 dark:text-emerald-400">
                  <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2">
                    <path
                      d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                  </svg>
                </div>
                <div>
                  <h2 class="text-base font-semibold text-slate-900 dark:text-white">UI Appearance</h2>
                  <p class="text-xs text-slate-500">Configure dashboard visibility</p>
                </div>
              </div>
              <div class="space-y-4">
                <label
                  class="flex items-center gap-3 cursor-pointer p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors border border-transparent hover:border-slate-200 dark:hover:border-slate-600 w-full md:w-auto">
                  <div
                    class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none"
                    :class="settings.hide_offline === 'true' ? 'bg-blue-600' : 'bg-slate-300 dark:bg-slate-600'">
                    <input type="checkbox" v-model="settings.hide_offline" true-value="true" false-value="false"
                      class="hidden" />
                    <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
                      :class="settings.hide_offline === 'true' ? 'translate-x-6' : 'translate-x-1'"></span>
                  </div>
                  <div>
                    <div class="text-sm font-medium text-slate-900 dark:text-white">Hide Offline Devices</div>
                    <div class="text-xs text-slate-500">Only show active network nodes</div>
                  </div>
                </label>
              </div>
            </div>

            <!-- Discovery Metrics -->
            <div class="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 p-4">
              <h3 class="text-sm font-semibold text-slate-900 dark:text-white mb-4">Discovery Metrics</h3>
              <div v-if="gist" class="space-y-4">
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-xs text-slate-500">Total Scans Run</span>
                  <span class="text-sm font-semibold text-slate-900 dark:text-white">{{ gist.total_scans }}</span>
                </div>
                <div class="flex justify-between items-center py-2 border-b border-slate-100 dark:border-slate-700">
                  <span class="text-xs text-slate-500">Discovery Jobs</span>
                  <span class="text-sm font-semibold text-emerald-600">{{ gist.scans_done }}</span>
                </div>
                <div class="flex justify-between items-center py-2">
                  <span class="text-xs text-slate-500">Currently Active</span>
                  <span class="flex items-center gap-2">
                    <span v-if="gist.scans_running > 0"
                      class="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse"></span>
                    <span class="text-sm font-semibold text-blue-600">{{ gist.scans_running }}</span>
                  </span>
                </div>
              </div>
              <div v-else class="text-sm text-slate-500 italic">No metrics available</div>
            </div>

            <!-- System Maintenance -->
            <div class="bg-white dark:bg-slate-800 rounded-lg border border-red-200 dark:border-red-900/20 p-4">
              <h3 class="text-sm font-semibold text-red-600 dark:text-red-400 mb-2">System Maintenance</h3>
              <p class="text-xs text-slate-500 mb-4">Cleanup tools and data management</p>
              <div class="flex items-center gap-2">
                <button @click="clearAllData"
                  class="p-2 border border-red-200 dark:border-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  v-tooltip="'Factory Reset (Delete All Data)'">
                  <Trash2 class="w-5 h-5" />
                </button>
                <button @click="resetConfig" :disabled="loading"
                  class="p-2 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                  v-tooltip="'Restore Default Configuration'">
                  <RotateCcw class="w-5 h-5" :class="{ 'animate-spin': loading }" />
                </button>
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>

    <!-- Confirmation Modal -->
    <div v-if="confirmModal.isOpen" class="fixed inset-0 z-50 overflow-y-auto" @click.self="closeConfirmation">
      <div class="flex min-h-screen items-center justify-center p-4">
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" @click="closeConfirmation"></div>

        <!-- Modal Card -->
        <div
          class="relative bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-sm w-full p-6 border border-slate-200 dark:border-slate-700 transform transition-all scale-100 opacity-100">
          <div class="flex flex-col items-center text-center">
            <div class="h-12 w-12 rounded-full flex items-center justify-center mb-4"
              :class="confirmModal.type === 'delete' ? 'bg-red-100 dark:bg-red-900/30' : 'bg-blue-100 dark:bg-blue-900/30'">
              <component :is="confirmModal.type === 'delete' ? Trash2 : AlertTriangle" class="h-6 w-6"
                :class="confirmModal.type === 'delete' ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'" />
            </div>

            <h3 class="text-xl font-bold text-slate-900 dark:text-white mb-2">{{ confirmModal.title }}</h3>

            <p class="text-sm text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">
              {{ confirmModal.message }}
            </p>

            <div class="flex gap-3 w-full">
              <button @click="closeConfirmation"
                class="flex-1 px-4 py-2.5 text-sm font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors border border-slate-200 dark:border-slate-600">
                Cancel
              </button>
              <button @click="confirmAction" :disabled="loading"
                class="flex-1 px-4 py-2.5 text-white rounded-lg text-sm font-semibold shadow-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-slate-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                :class="confirmModal.confirmClass">
                <Loader2 v-if="loading" class="w-4 h-4 animate-spin" />
                {{ loading ? 'Processing...' : confirmModal.confirmText }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import axios from 'axios'
import { Save, RotateCcw, Trash2, AlertTriangle, Loader2, Plus } from 'lucide-vue-next'

const settings = reactive({
  scan_subnets: '[]',
  scan_interval: '300',
  last_discovery_run_at: '',
  hide_offline: 'false',
  mqtt_broker: 'localhost',
  mqtt_port: '1883',
  mqtt_base_topic: 'network_scanner',
  mqtt_username: '',
  mqtt_password: ''
})

const subnetList = ref([])
const newSubnet = ref('')
const gist = ref(null)
const saveStatus = ref('idle')
const loading = ref(false)
const subnetError = ref('')

// Clear error when user types
watch(newSubnet, () => {
  if (subnetError.value) subnetError.value = ''
})

// Confirmation Modal State
const confirmModal = reactive({
  isOpen: false,
  type: '', // 'delete' or 'reset'
  title: '',
  message: '',
  confirmText: '',
  confirmClass: ''
})

const addSubnet = () => {
  const s = newSubnet.value.trim()
  if (!s) {
    subnetError.value = 'Subnet range cannot be empty'
    return
  }
  if (subnetList.value.includes(s)) {
    subnetError.value = 'Subnet already exists'
    return
  }

  subnetList.value.push(s)
  settings.scan_subnets = JSON.stringify(subnetList.value)
  newSubnet.value = ''
  subnetError.value = ''
}

const removeSubnet = (s) => {
  subnetList.value = subnetList.value.filter(item => item !== s)
  settings.scan_subnets = JSON.stringify(subnetList.value)
}

const fetchSettings = async () => {
  try {
    const res = await axios.get('/api/v1/config/')
    const mapping = {}
    res.data.forEach(item => {
      mapping[item.key] = item.value
    })

    // Apply mapping
    if (mapping.scan_subnets) {
      settings.scan_subnets = mapping.scan_subnets
      try {
        subnetList.value = JSON.parse(mapping.scan_subnets)
      } catch { subnetList.value = [] }
    }
    if (mapping.scan_interval) settings.scan_interval = mapping.scan_interval
    if (mapping.last_discovery_run_at) settings.last_discovery_run_at = mapping.last_discovery_run_at
    if (mapping.hide_offline) settings.hide_offline = mapping.hide_offline
    if (mapping.mqtt_broker) settings.mqtt_broker = mapping.mqtt_broker
    if (mapping.mqtt_port) settings.mqtt_port = mapping.mqtt_port
    if (mapping.mqtt_base_topic) settings.mqtt_base_topic = mapping.mqtt_base_topic
    if (mapping.mqtt_username) settings.mqtt_username = mapping.mqtt_username
    if (mapping.mqtt_password) settings.mqtt_password = mapping.mqtt_password
  } catch (e) {
    console.error("Failed to fetch config:", e)
  }
}

const fetchGist = async () => {
  try {
    const res = await axios.get('/api/v1/scans/gist')
    gist.value = res.data
  } catch (e) {
    console.error(e)
  }
}

const saveSettings = async () => {
  saveStatus.value = 'saving'
  try {
    await axios.post('/api/v1/config/', settings)
    saveStatus.value = 'saved'
    setTimeout(() => { saveStatus.value = 'idle' }, 2000)
  } catch (e) {
    alert('Failed to save settings')
    saveStatus.value = 'idle'
  }
}

const openConfirmation = (type) => {
  confirmModal.type = type
  confirmModal.isOpen = true

  if (type === 'delete') {
    confirmModal.title = 'Factory Reset?'
    confirmModal.message = 'This will permanently delete all discovered devices, scan history, and metrics. This action cannot be undone.'
    confirmModal.confirmText = 'Yes, Delete Everything'
    confirmModal.confirmClass = 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
  } else if (type === 'reset') {
    confirmModal.title = 'Restore Defaults?'
    confirmModal.message = 'This will revert all settings (scan intervals, subnets, UI preferences) to their default values. Your data will be preserved.'
    confirmModal.confirmText = 'Restore Defaults'
    confirmModal.confirmClass = 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
  }
}

const closeConfirmation = () => {
  confirmModal.isOpen = false
}

const confirmAction = async () => {
  closeConfirmation()
  loading.value = true

  try {
    if (confirmModal.type === 'delete') {
      await axios.delete('/api/v1/devices/')
      await axios.delete('/api/v1/scans/')
      window.location.reload()
    } else if (confirmModal.type === 'reset') {
      // Reset local state to defaults
      settings.scan_interval = '300'
      settings.scan_subnets = '[]'
      settings.hide_offline = 'false'
      settings.mqtt_broker = 'localhost'
      settings.mqtt_port = '1883'
      settings.mqtt_base_topic = 'network_scanner'
      settings.mqtt_username = ''
      settings.mqtt_password = ''
      subnetList.value = []

      // Save these defaults
      await axios.post('/api/v1/config/', settings)

      // Re-fetch to confirm
      await fetchSettings()
    }
  } catch (e) {
    console.error(e)
    alert('Action failed')
  } finally {
    loading.value = false
  }
}

// Wrappers for buttons
const clearAllData = () => openConfirmation('delete')
const resetConfig = () => openConfirmation('reset')

const formatLastRun = (dateStr) => {
  if (!dateStr) return 'Never'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString()
  } catch { return 'Never' }
}

onMounted(() => {
  fetchSettings()
  fetchGist()
})
</script>
