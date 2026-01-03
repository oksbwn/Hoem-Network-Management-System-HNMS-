<template>
    <TransitionRoot appear :show="isOpen" as="template">
        <Dialog as="div" @close="closeModal" class="relative z-50">
            <TransitionChild as="template" enter="duration-300 ease-out" enter-from="opacity-0" enter-to="opacity-100"
                leave="duration-200 ease-in" leave-from="opacity-100" leave-to="opacity-0">
                <div class="fixed inset-0 bg-black/50 backdrop-blur-sm" />
            </TransitionChild>

            <div class="fixed inset-0 overflow-y-auto">
                <div class="flex min-h-full items-center justify-center p-4 text-center">
                    <TransitionChild as="template" enter="duration-300 ease-out" enter-from="opacity-0 scale-95"
                        enter-to="opacity-100 scale-100" leave="duration-200 ease-in" leave-from="opacity-100 scale-100"
                        leave-to="opacity-0 scale-95">
                        <DialogPanel
                            class="w-full max-w-md transform rounded-2xl bg-white dark:bg-slate-800 p-6 text-left align-middle shadow-xl transition-all border border-slate-200 dark:border-slate-700">
                            <DialogTitle as="h3"
                                class="text-lg font-medium leading-6 text-slate-900 dark:text-white mb-4">
                                Edit Device Details
                            </DialogTitle>

                            <form @submit.prevent="saveDevice" class="space-y-4">
                                <!-- IP Address (Read Only) -->
                                <div>
                                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">IP
                                        Address</label>
                                    <p class="mt-1 text-sm text-slate-500 font-mono">{{ device.ip }}</p>
                                </div>

                                <!-- Display Name -->
                                <div>
                                    <label class="block text-sm font-medium text-slate-700 dark:text-slate-300">Display
                                        Name</label>
                                    <input v-model="form.display_name" type="text"
                                        class="mt-1 block w-full rounded-md border-slate-300 dark:border-slate-600 dark:bg-slate-700 dark:text-white shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                                        placeholder="e.g. Living Room TV" />
                                </div>

                                <!-- Device Type -->
                                <div>
                                    <label
                                        class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Device
                                        Category</label>
                                    <Popover class="relative" v-slot="{ open, close }">
                                        <PopoverButton
                                            class="w-full flex items-center justify-between px-4 py-2.5 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all group">
                                            <span class="truncate">{{ form.device_type || 'Select Category' }}</span>
                                            <ChevronDown
                                                class="h-4 w-4 text-slate-400 transition-transform duration-200"
                                                :class="{ 'rotate-180': open }" />
                                        </PopoverButton>

                                        <transition enter-active-class="transition duration-200 ease-out"
                                            enter-from-class="translate-y-1 opacity-0"
                                            enter-to-class="translate-y-0 opacity-100"
                                            leave-active-class="transition duration-150 ease-in"
                                            leave-from-class="translate-y-0 opacity-100"
                                            leave-to-class="translate-y-1 opacity-0">
                                            <PopoverPanel
                                                class="absolute z-50 mt-2 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl overflow-hidden focus:outline-none">
                                                <div class="p-2 border-b border-slate-100 dark:border-slate-700/50">
                                                    <div
                                                        class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                                                        <Search class="w-3.5 h-3.5 text-slate-400" />
                                                        <input v-model="categorySearch" type="text"
                                                            placeholder="Search..."
                                                            class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                                                    </div>
                                                </div>
                                                <div class="max-h-48 overflow-y-auto custom-scrollbar p-1">
                                                    <button v-for="type in filteredDeviceTypes" :key="type"
                                                        type="button" @click="form.device_type = type; close()"
                                                        class="w-full flex items-center px-4 py-2 text-sm text-left rounded-lg hover:bg-blue-600 hover:text-white transition-colors"
                                                        :class="form.device_type === type ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                                        {{ type }}
                                                    </button>
                                                    <div v-if="filteredDeviceTypes.length === 0"
                                                        class="px-4 py-2 text-xs text-slate-400 text-center">
                                                        No matches
                                                    </div>
                                                </div>
                                            </PopoverPanel>
                                        </transition>
                                    </Popover>
                                </div>

                                <!-- Icon Picker Popover -->
                                <div>
                                    <label
                                        class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Select
                                        Icon</label>
                                    <Popover class="relative">
                                        <PopoverButton
                                            class="w-full flex items-center justify-between px-4 py-2.5 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all group">
                                            <div class="flex items-center gap-3">
                                                <component :is="getIcon(form.icon)" class="h-5 w-5 text-blue-500" />
                                                <span class="text-sm">{{ form.icon || 'Select Icon' }}</span>
                                            </div>
                                            <ChevronDown
                                                class="w-4 h-4 text-slate-400 group-hover:text-slate-600 transition-colors" />
                                        </PopoverButton>

                                        <transition enter-active-class="transition duration-200 ease-out"
                                            enter-from-class="translate-y-1 opacity-0"
                                            enter-to-class="translate-y-0 opacity-100"
                                            leave-active-class="transition duration-150 ease-in"
                                            leave-from-class="translate-y-0 opacity-100"
                                            leave-to-class="translate-y-1 opacity-0">
                                            <PopoverPanel
                                                class="absolute z-50 bottom-full mb-2 right-0 w-[280px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl p-4 focus:outline-none overflow-hidden">
                                                <div
                                                    class="grid grid-cols-4 gap-2 max-h-[220px] overflow-y-auto pr-2 custom-scrollbar">
                                                    <button v-for="icon in availableIcons" :key="icon" type="button"
                                                        @click="form.icon = icon"
                                                        class="p-3 rounded-lg flex items-center justify-center transition-all"
                                                        :class="form.icon === icon ? 'bg-blue-600 text-white shadow-lg' : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500'">
                                                        <component :is="getIcon(icon)" class="h-5 w-5" />
                                                    </button>
                                                </div>
                                            </PopoverPanel>
                                        </transition>
                                    </Popover>
                                </div>

                                <!-- Parent Device Selection -->
                                <div>
                                    <label
                                        class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Connected
                                        Via (Parent)</label>
                                    <Popover class="relative" v-slot="{ open, close }">
                                        <PopoverButton
                                            class="w-full flex items-center justify-between px-4 py-2.5 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all group">
                                            <span class="truncate">{{ getParentLabel }}</span>
                                            <ChevronDown
                                                class="h-4 w-4 text-slate-400 group-hover:text-slate-600 transition-colors"
                                                :class="{ 'rotate-180': open }" />
                                        </PopoverButton>

                                        <transition enter-active-class="transition duration-200 ease-out"
                                            enter-from-class="translate-y-1 opacity-0"
                                            enter-to-class="translate-y-0 opacity-100"
                                            leave-active-class="transition duration-150 ease-in"
                                            leave-from-class="translate-y-0 opacity-100"
                                            leave-to-class="translate-y-1 opacity-0">
                                            <PopoverPanel
                                                class="absolute z-50 bottom-full mb-2 right-0 w-[280px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-2xl overflow-hidden focus:outline-none">
                                                <div class="p-2 border-b border-slate-100 dark:border-slate-700/50">
                                                    <div
                                                        class="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-900/50 rounded-lg">
                                                        <Search class="w-3.5 h-3.5 text-slate-400" />
                                                        <input v-model="parentSearch" @click.stop type="text"
                                                            placeholder="Search devices..."
                                                            class="bg-transparent border-none outline-none text-xs text-slate-700 dark:text-slate-200 w-full placeholder:text-slate-400" />
                                                    </div>
                                                </div>
                                                <div class="max-h-48 overflow-y-auto custom-scrollbar p-1">
                                                    <button type="button" @click="form.parent_id = null; close()"
                                                        class="w-full flex items-center px-4 py-2 text-sm text-left rounded-lg hover:bg-blue-600 hover:text-white transition-colors"
                                                        :class="!form.parent_id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                                        Main Gateway (Default)
                                                    </button>
                                                    <button v-for="d in filteredPotentialParents" :key="d.id"
                                                        type="button" @click="form.parent_id = d.id; close()"
                                                        class="w-full flex items-center gap-2 px-4 py-2 text-sm text-left rounded-lg hover:bg-blue-600 hover:text-white transition-colors"
                                                        :class="form.parent_id === d.id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' : 'text-slate-600 dark:text-slate-300'">
                                                        <component :is="getIcon(d.icon)"
                                                            class="w-4 h-4 mr-2 opacity-70" />
                                                        <span class="truncate">{{ d.display_name || d.name || d.ip
                                                        }}</span>
                                                    </button>
                                                </div>
                                            </PopoverPanel>
                                        </transition>
                                    </Popover>
                                </div>

                                <div class="mt-6 flex justify-end gap-3">
                                    <button type="button"
                                        class="px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-slate-700 dark:text-slate-200 dark:border-slate-600 dark:hover:bg-slate-600"
                                        @click="closeModal">
                                        Cancel
                                    </button>
                                    <button type="submit" :disabled="isSaving"
                                        class="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed">
                                        <Loader2 v-if="isSaving" class="mr-2 h-4 w-4 animate-spin" />
                                        {{ isSaving ? 'Saving...' : 'Save Changes' }}
                                    </button>
                                </div>
                            </form>
                        </DialogPanel>
                    </TransitionChild>
                </div>
            </div>
        </Dialog>
    </TransitionRoot>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import {
    TransitionRoot,
    TransitionChild,
    Dialog,
    DialogPanel,
    DialogTitle,
    Popover,
    PopoverButton,
    PopoverPanel
} from '@headlessui/vue'
import {
    Search,
    ChevronDown,
    Loader2
} from 'lucide-vue-next'
import api from '@/utils/api'
import { getIcon } from '@/utils/icons'
import { useNotifications } from '@/composables/useNotifications'
import { deviceTypes, availableIcons, typeToIconMap } from '@/constants/devices'

const props = defineProps({
    isOpen: Boolean,
    device: Object
})

const emit = defineEmits(['close', 'save'])

const isSaving = ref(false)
const allDevices = ref([])
const parentSearch = ref('')

const { notifySuccess, notifyError } = useNotifications()

const form = ref({
    display_name: '',
    device_type: '',
    icon: '',
    parent_id: null
})

const categorySearch = ref('')

const filteredDeviceTypes = computed(() => {
    if (!categorySearch.value) return deviceTypes
    return deviceTypes.filter(t => t.toLowerCase().includes(categorySearch.value.toLowerCase()))
})

const filteredPotentialParents = computed(() => {
    const others = allDevices.value.filter(d => d.id !== props.device?.id)
    if (!parentSearch.value) return others
    const s = parentSearch.value.toLowerCase()
    return others.filter(d =>
        (d.display_name || '').toLowerCase().includes(s) ||
        (d.name || '').toLowerCase().includes(s) ||
        (d.ip || '').includes(s)
    )
})

const getParentLabel = computed(() => {
    if (!form.value.parent_id) return 'Main Gateway (Default)'
    const p = allDevices.value.find(d => d.id === form.value.parent_id)
    return p ? (p.display_name || p.name || p.ip) : 'Unknown Device'
})

watch(() => form.value.device_type, (newType) => {
    if (newType && typeToIconMap[newType]) {
        form.value.icon = typeToIconMap[newType]
    }
})

// getIcon is now imported from @/utils/icons

const fetchAllDevices = async () => {
    try {
        const res = await api.get('/devices/?limit=-1')
        allDevices.value = res.data.items || []
    } catch (e) {
        console.error('Failed to fetch devices:', e)
    }
}

onMounted(() => {
    fetchAllDevices()
})

watch(() => props.device, (newVal) => {
    if (newVal) {
        form.value = {
            display_name: newVal.display_name || newVal.name || '',
            device_type: newVal.device_type || 'unknown',
            icon: newVal.icon || 'help-circle',
            parent_id: newVal.parent_id || null
        }
    }
}, { immediate: true })

const closeModal = () => {
    emit('close')
}

const saveDevice = async () => {
    if (!props.device) return
    isSaving.value = true
    try {
        const response = await api.patch(`/devices/${props.device.id}`, form.value)
        notifySuccess('Device updated successfully')
        emit('save', response.data)
        closeModal()
    } catch (error) {
        console.error('Failed to update device', error)
        notifyError('Failed to update device')
    } finally {
        isSaving.value = false
    }
}
</script>
