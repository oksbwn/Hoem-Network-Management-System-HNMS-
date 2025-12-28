<template>
  <div v-if="device">
    <div class="flex items-center mb-6">
      <router-link to="/devices" class="mr-4 text-gray-500 hover:text-gray-700">
        &larr; Back
      </router-link>
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Device Details</h1>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Info Card -->
      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-slate-700">
        <div class="flex justify-between items-start mb-4">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">General Info</h2>
          <button @click="saveChanges" class="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700">
            Save Changes
          </button>
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Display Name</label>
            <input v-model="form.display_name" type="text"
              class="mt-1 block w-full rounded-md border-gray-300 dark:border-slate-600 dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Hostname</label>
            <input v-model="form.name" type="text"
              class="mt-1 block w-full rounded-md border-gray-300 dark:border-slate-600 dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Device Type</label>
            <select v-model="form.device_type"
              class="mt-1 block w-full rounded-md border-gray-300 dark:border-slate-600 dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2">
              <option value="unknown">Unknown</option>
              <option value="Router/Gateway">Router/Gateway</option>
              <option value="Desktop">Desktop</option>
              <option value="Laptop">Laptop</option>
              <option value="Mobile">Mobile</option>
              <option value="IoT">IoT</option>
              <option value="Printer">Printer</option>
            </select>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">IP Address</label>
              <div class="mt-1 text-sm text-gray-900 dark:text-white">{{ device.ip }}</div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">MAC Address</label>
              <div class="mt-1 text-sm text-gray-900 dark:text-white">{{ device.mac || 'N/A' }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-slate-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Open Ports</h2>
        <div v-if="parsedPorts.length > 0" class="space-y-3">
          <div v-for="port in parsedPorts" :key="port.port"
            class="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
            <div class="flex items-center space-x-3">
              <div
                class="h-8 w-8 rounded-full flex items-center justify-center bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400 font-mono text-xs font-bold">
                {{ port.port }}
              </div>
              <div>
                <div class="text-sm font-medium text-gray-900 dark:text-white">{{ port.service || 'Unknown Service' }}
                </div>
                <div class="text-xs text-gray-500">{{ port.protocol || 'TCP' }}</div>
              </div>
            </div>
            <button v-if="port.port === 22" @click="openSSH(port.port)"
              class="px-3 py-1.5 bg-slate-900 text-white text-xs rounded hover:bg-slate-700 transition">
              Connect
            </button>
            <a v-if="[80, 443, 3000, 8080, 8000].includes(port.port)" :href="`http://${device.ip}:${port.port}`"
              target="_blank" class="px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700 transition">
              Open
            </a>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-500 text-sm">
          No open ports detected.
        </div>
      </div>
    </div>

    <TerminalModal v-if="showTerminal" :device="device" :port="sshPort" @close="showTerminal = false" />
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import TerminalModal from '../components/TerminalModal.vue'

const route = useRoute()
const device = ref(null)
const showTerminal = ref(false)
const sshPort = ref(22)

const form = reactive({
  display_name: '',
  name: '',
  device_type: ''
})

const parsedPorts = computed(() => {
  if (!device.value || !device.value.open_ports) return []
  try {
    const parsed = JSON.parse(device.value.open_ports)
    if (Array.isArray(parsed) && parsed.length > 0) {
      if (typeof parsed[0] === 'number') {
        return parsed.map(p => ({ port: p, service: 'Unknown', protocol: 'TCP' }))
      }
      return parsed
    }
    return []
  } catch {
    return []
  }
})

const openSSH = (port) => {
  sshPort.value = port
  showTerminal.value = true
}

const fetchDevice = async () => {
  try {
    const res = await axios.get(`/api/v1/devices/${route.params.id}`)
    device.value = res.data
    form.display_name = device.value.display_name
    form.name = device.value.name
    form.device_type = device.value.device_type || 'unknown'
  } catch (e) {
    console.error(e)
  }
}

const saveChanges = async () => {
  try {
    await axios.put(`/api/v1/devices/${device.value.id}`, form)
    alert('Saved!')
    fetchDevice() // reload
  } catch (e) {
    alert('Failed to save')
  }
}

onMounted(() => {
  fetchDevice()
})
</script>
