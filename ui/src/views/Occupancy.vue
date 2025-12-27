<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">IP Occupancy</h1>
    
    <div class="bg-white dark:bg-slate-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-slate-700">
      <div class="mb-4 flex justify-between">
         <p class="text-sm text-gray-500">Visual map of the subnet /24.</p>
         <div class="flex space-x-4 text-xs">
            <span class="flex items-center"><span class="w-3 h-3 bg-green-500 rounded-full mr-1"></span> Online</span>
            <span class="flex items-center"><span class="w-3 h-3 bg-red-400 rounded-full mr-1"></span> Offline</span>
            <span class="flex items-center"><span class="w-3 h-3 bg-gray-100 border border-gray-200 rounded-full mr-1"></span> Free</span>
         </div>
      </div>

      <div class="grid grid-cols-16 gap-1 md:gap-2">
         <div 
            v-for="i in 255" 
            :key="i"
            class="aspect-square flex items-center justify-center text-[10px] rounded hover:scale-110 transition cursor-pointer relative group"
            :class="getStatusClass(i)"
            @click="goToDevice(i)"
         >
            {{ i }}
            
            <!-- Tooltip -->
            <div v-if="getDevice(i)" class="hidden group-hover:block absolute bottom-full mb-2 bg-gray-900 text-white text-xs p-2 rounded z-10 w-32 text-center">
                {{ getDevice(i).display_name || getDevice(i).ip }}
            </div>
         </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const devices = ref([])
const router = useRouter()

// Simplistic subnet assumption: User is scanning a /24 and IPs end in .1 to .255
const getDevice = (suffix) => {
    // This is a naive check that assumes the scan matches the current subnet logic
    // We would need to parse the device IP and see if the last octet matches 'suffix'
    // For visual demo, let's look for matching suffix
    return devices.value.find(d => {
        const parts = d.ip.split('.')
        return parseInt(parts[3]) === suffix
    })
}

const getStatusClass = (suffix) => {
    const d = getDevice(suffix)
    if (!d) return 'bg-gray-50 dark:bg-slate-700 text-gray-400'
    // Online check
    const diff = new Date() - new Date(d.last_seen)
    if (diff < 300 * 1000) return 'bg-green-100 text-green-700 border border-green-300 dark:bg-green-900 dark:text-green-300'
    return 'bg-red-50 text-red-700 border border-red-200 dark:bg-red-900/20 dark:text-red-400'
}

const goToDevice = (suffix) => {
    const d = getDevice(suffix)
    if (d) {
        router.push(`/devices/${d.id}`)
    }
}

onMounted(async () => {
    const res = await axios.get('/api/v1/devices/')
    devices.value = res.data
})
</script>

<style scoped>
.grid-cols-16 {
    grid-template-columns: repeat(16, minmax(0, 1fr));
}
</style>
