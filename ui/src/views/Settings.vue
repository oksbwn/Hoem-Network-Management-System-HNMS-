<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">Settings</h1>

    <div class="max-w-2xl bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-slate-700">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Scanning Configuration</h2>
      
      <div class="space-y-4">
         <div>
            <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Target IP Range / Subnet</label>
            <input v-model="form.scan_target" type="text" placeholder="e.g., 192.168.1.0/24" class="mt-1 block w-full rounded-md border-gray-300 dark:border-slate-600 dark:bg-slate-700 shadow-sm p-2" />
         </div>

         <div>
            <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Scan Interval (seconds)</label>
            <input v-model="form.scan_interval" type="number" class="mt-1 block w-full rounded-md border-gray-300 dark:border-slate-600 dark:bg-slate-700 shadow-sm p-2" />
         </div>

         <div class="pt-4 border-t border-gray-200 dark:border-slate-700">
            <h3 class="text-md font-medium text-gray-900 dark:text-white mb-2">MQTT Settings</h3>
            <div class="grid grid-cols-2 gap-4">
                 <div>
                    <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Broker Host</label>
                    <input v-model="form.mqtt_broker" type="text" class="mt-1 block w-full rounded-md border-gray-300 dark:border-slate-600 dark:bg-slate-700 shadow-sm p-2" />
                 </div>
                 <div>
                    <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Port</label>
                    <input v-model="form.mqtt_port" type="number" class="mt-1 block w-full rounded-md border-gray-300 dark:border-slate-600 dark:bg-slate-700 shadow-sm p-2" />
                 </div>
            </div>
         </div>

         <div class="pt-4 flex justify-end">
            <button @click="saveSettings" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                Save Configuration
            </button>
         </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

const form = reactive({
    scan_target: '',
    scan_interval: '300',
    mqtt_broker: 'localhost',
    mqtt_port: '1883'
})

const fetchSettings = async () => {
    try {
        const res = await axios.get('/api/v1/config/')
        const data = res.data
        // Convert list [{key, value}] to map
        data.forEach(item => {
            if (item.key in form) {
                form[item.key] = item.value
            }
        })
    } catch (e) {
        console.error(e)
    }
}

const saveSettings = async () => {
    try {
        await axios.post('/api/v1/config/', form)
        alert('Settings saved. Requires backend restart to fully apply some changes.')
    } catch (e) {
        alert('Error saving settings')
    }
}

onMounted(() => {
    fetchSettings()
})
</script>
