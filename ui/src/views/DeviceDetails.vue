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
            <input v-model="form.display_name" type="text" class="mt-1 block w-full rounded-md border-gray-300 dark:border-slate-600 dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2" />
          </div>
          
           <div>
            <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Hostname</label>
            <input v-model="form.name" type="text" class="mt-1 block w-full rounded-md border-gray-300 dark:border-slate-600 dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2" />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-500 dark:text-gray-400">Device Type</label>
             <select v-model="form.device_type" class="mt-1 block w-full rounded-md border-gray-300 dark:border-slate-600 dark:bg-slate-700 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2">
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

       <!-- Ports Card (Placeholder as we don't have an endpoint for ports details in list yet, assuming implicit) -->
       <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-slate-700">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Open Ports</h2>
        <p class="text-sm text-gray-500">Port scanning details would appear here.</p>
        <!-- TODO: Fetch ports -->
       </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const device = ref(null)
const form = reactive({
    display_name: '',
    name: '',
    device_type: ''
})

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
