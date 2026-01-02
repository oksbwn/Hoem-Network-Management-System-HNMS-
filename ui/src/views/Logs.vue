<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <h1 class="text-2xl font-bold text-slate-900 dark:text-white">System Logs</h1>
                <p class="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    View backend system events and errors. Found {{ total }} records.
                </p>
            </div>

            <div class="flex items-center gap-3">
                <!-- Search Input -->
                <div class="relative w-full md:w-64">
                    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <MagnifyingGlassIcon class="h-4 w-4 text-slate-400" />
                    </div>
                    <input v-model="search" @input="debounceSearch" type="text"
                        class="block w-full rounded-xl border-0 py-2 pl-10 text-slate-900 shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6 dark:bg-slate-800 dark:text-white dark:ring-slate-700 dark:placeholder:text-slate-500"
                        placeholder="Search logs..." />
                </div>

                <div
                    class="flex items-center gap-3 bg-white dark:bg-slate-800 p-1.5 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                    <!-- Level Filter Dropdown -->
                    <div class="relative" v-click-outside="() => isLevelOpen = false">
                        <button @click="isLevelOpen = !isLevelOpen"
                            class="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors group border-r border-slate-200 dark:border-slate-700 pr-4 mr-2">
                            <div class="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-300">
                                <FunnelIcon class="h-4 w-4 text-slate-400" />
                                <span>{{ levelFilter || 'All Levels' }}</span>
                            </div>
                            <ChevronDownIcon class="h-4 w-4 text-slate-400 transition-transform duration-200"
                                :class="{ 'rotate-180': isLevelOpen }" />
                        </button>

                        <transition enter-active-class="transition duration-100 ease-out"
                            enter-from-class="transform scale-95 opacity-0"
                            enter-to-class="transform scale-100 opacity-100"
                            leave-active-class="transition duration-75 ease-in"
                            leave-from-class="transform scale-100 opacity-100"
                            leave-to-class="transform scale-95 opacity-0">
                            <div v-if="isLevelOpen"
                                class="absolute top-full left-0 mt-2 w-40 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl py-1 z-20 overflow-hidden">
                                <button @click="levelFilter = ''; isLevelOpen = false; fetchLogs()"
                                    class="w-full px-4 py-2 text-sm text-left hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:text-blue-600 dark:hover:text-blue-400 transition-colors flex items-center justify-between"
                                    :class="levelFilter === '' ? 'bg-blue-50/50 dark:bg-blue-900/10 text-blue-600 dark:text-blue-400 font-medium' : 'text-slate-600 dark:text-slate-300'">
                                    All Levels
                                    <CheckIcon v-if="levelFilter === ''" class="h-3.5 w-3.5" />
                                </button>
                                <button v-for="lvl in ['INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG']" :key="lvl"
                                    @click="levelFilter = lvl; isLevelOpen = false; fetchLogs()"
                                    class="w-full px-4 py-2 text-sm text-left hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:text-blue-600 dark:hover:text-blue-400 transition-colors flex items-center justify-between"
                                    :class="levelFilter === lvl ? 'bg-blue-50/50 dark:bg-blue-900/10 text-blue-600 dark:text-blue-400 font-medium' : 'text-slate-600 dark:text-slate-300'">
                                    {{ lvl }}
                                    <CheckIcon v-if="levelFilter === lvl" class="h-3.5 w-3.5" />
                                </button>
                            </div>
                        </transition>
                    </div>

                    <!-- Custom Rows Dropdown -->
                    <div class="relative" v-click-outside="() => isRowsOpen = false">
                        <button @click="isRowsOpen = !isRowsOpen"
                            class="flex items-center gap-2 pl-3 pr-2 py-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors group">
                            <span
                                class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Rows:</span>
                            <span
                                class="text-sm font-semibold text-slate-700 dark:text-slate-200 min-w-[2rem] text-left">{{
                                    limit }}</span>
                            <ChevronDownIcon class="h-4 w-4 text-slate-400 transition-transform duration-200"
                                :class="{ 'rotate-180': isRowsOpen }" />
                        </button>

                        <transition enter-active-class="transition duration-100 ease-out"
                            enter-from-class="transform scale-95 opacity-0"
                            enter-to-class="transform scale-100 opacity-100"
                            leave-active-class="transition duration-75 ease-in"
                            leave-from-class="transform scale-100 opacity-100"
                            leave-to-class="transform scale-95 opacity-0">
                            <div v-if="isRowsOpen"
                                class="absolute top-full left-0 mt-2 w-32 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl shadow-xl py-1 z-20 overflow-hidden">
                                <button v-for="opt in [50, 100, 500, 1000]" :key="opt"
                                    @click="limit = opt; isRowsOpen = false; changePage(1)"
                                    class="w-full px-4 py-2 text-sm text-left hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:text-blue-600 dark:hover:text-blue-400 transition-colors flex items-center justify-between"
                                    :class="limit === opt ? 'bg-blue-50/50 dark:bg-blue-900/10 text-blue-600 dark:text-blue-400 font-medium' : 'text-slate-600 dark:text-slate-300'">
                                    {{ opt }}
                                    <CheckIcon v-if="limit === opt" class="h-3.5 w-3.5" />
                                </button>
                            </div>
                        </transition>
                    </div>

                    <div class="h-5 w-px bg-slate-200 dark:bg-slate-700"></div>

                    <button @click="fetchLogs"
                        class="inline-flex items-center px-3 py-2 border border-transparent text-sm font-semibold rounded-lg text-blue-600 bg-blue-50 hover:bg-blue-100 dark:text-blue-400 dark:bg-blue-500/10 dark:hover:bg-blue-500/20 transition-all active:scale-95">
                        <ArrowPathIcon class="h-4 w-4 mr-1.5" :class="{ 'animate-spin': loading }" />
                        Refresh
                    </button>

                    <div class="h-5 w-px bg-slate-200 dark:bg-slate-700"></div>

                    <button @click="clearLogs"
                        class="p-2 ml-1 bg-white dark:bg-slate-800 border border-transparent rounded-lg hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors text-slate-400 dark:text-slate-500"
                        title="Clear All Logs">
                        <TrashIcon class="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>

        <!-- Logs Table -->
        <div
            class="bg-white dark:bg-slate-800 shadow sm:rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700 flex flex-col min-h-[500px]">
            <div class="flex-1 overflow-x-auto">
                <table class="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                    <thead class="bg-slate-50 dark:bg-slate-900/50">
                        <tr>
                            <th scope="col"
                                class="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider w-48">
                                Timestamp</th>
                            <th scope="col"
                                class="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider w-24">
                                Level</th>
                            <th scope="col"
                                class="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider w-48">
                                Module</th>
                            <th scope="col"
                                class="px-6 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                                Message</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white dark:bg-slate-800 divide-y divide-slate-200 dark:divide-slate-700">
                        <tr v-if="loading && logs.length === 0">
                            <td colspan="4" class="px-6 py-20 text-center">
                                <ArrowPathIcon class="h-8 w-8 mx-auto animate-spin mb-2 text-slate-400" />
                                <p class="text-slate-500 dark:text-slate-400">Loading logs...</p>
                            </td>
                        </tr>
                        <tr v-else-if="logs.length === 0">
                            <td colspan="4" class="px-6 py-20 text-center">
                                <p class="text-slate-500 dark:text-slate-400 italic">No logs found matching your
                                    criteria.</p>
                            </td>
                        </tr>
                        <tr v-for="(log, idx) in logs" :key="idx"
                            class="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                            <td
                                class="px-6 py-2 text-xs font-mono text-slate-500 dark:text-slate-400 whitespace-nowrap">
                                {{ formatTime(log.timestamp) }}
                            </td>
                            <td class="px-6 py-2 whitespace-nowrap">
                                <span :class="[
                                    'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                                    levelColors[log.level] || 'bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-300'
                                ]">
                                    {{ log.level }}
                                </span>
                            </td>
                            <td class="px-6 py-2 text-xs text-slate-600 dark:text-slate-300 font-mono whitespace-nowrap"
                                :title="log.path">
                                {{ log.module }}:{{ log.line }}
                            </td>
                            <td class="px-6 py-2 text-sm text-slate-900 dark:text-slate-100 break-all font-mono">
                                {{ log.message }}
                                <div v-if="log.exception"
                                    class="mt-2 p-2 bg-slate-50 dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-700 text-xs text-red-600 dark:text-red-400 whitespace-pre-wrap font-mono overflow-x-auto">
                                    {{ log.exception }}
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Pagination -->
            <div v-if="totalPages > 1"
                class="flex justify-center items-center gap-2 p-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/30">
                <button @click="changePage(page - 1)" :disabled="page <= 1"
                    class="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                    Previous
                </button>
                <div
                    class="px-4 py-2 bg-slate-900 dark:bg-white rounded-lg text-sm font-medium text-white dark:text-slate-900">
                    {{ page }} / {{ totalPages }}
                </div>
                <button @click="changePage(page + 1)" :disabled="page >= totalPages"
                    class="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                    Next
                </button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ArrowPathIcon, ChevronDownIcon, CheckIcon, MagnifyingGlassIcon, TrashIcon, FunnelIcon } from '@heroicons/vue/24/outline'

interface LogRecord {
    timestamp: string
    level: string
    message: string
    module: string
    funcName: string
    line: number
    path: string
    exception?: string
}

const logs = ref<LogRecord[]>([])
const loading = ref(false)
const limit = ref(100)
const page = ref(1)
const total = ref(0)
const totalPages = ref(1)
const search = ref('')
const levelFilter = ref('WARNING') // Default to WARNING
const isRowsOpen = ref(false)
const isLevelOpen = ref(false)

// Custom directive
const vClickOutside = {
    mounted(el: any, binding: any) {
        el._clickOutside = (event: Event) => {
            if (!(el === event.target || el.contains(event.target))) {
                binding.value(event)
            }
        }
        document.addEventListener('click', el._clickOutside)
    },
    unmounted(el: any) {
        document.removeEventListener('click', el._clickOutside)
    }
}

const levelColors: Record<string, string> = {
    'INFO': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    'WARNING': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    'ERROR': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    'CRITICAL': 'bg-red-200 text-red-900 dark:bg-red-900/50 dark:text-red-100 animate-pulse',
    'DEBUG': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
}

const formatTime = (ts: string) => {
    try {
        return new Date(ts).toLocaleString()
    } catch {
        return ts
    }
}

let debounceTimer: any = null
const debounceSearch = () => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
        page.value = 1
        fetchLogs()
    }, 400)
}

const changePage = (newPage: number) => {
    if (newPage < 1 || newPage > totalPages.value) return
    page.value = newPage
    fetchLogs()
    // Scroll to top of table
    window.scrollTo({ top: 0, behavior: 'smooth' })
}

const fetchLogs = async () => {
    loading.value = true
    try {
        const queryParams = new URLSearchParams({
            limit: limit.value.toString(),
            page: page.value.toString(),
            ...(search.value ? { search: search.value } : {}),
            ...(levelFilter.value ? { level: levelFilter.value } : {})
        })

        const res = await fetch(`/api/v1/logs/?${queryParams}`)
        if (res.ok) {
            const data = await res.json()
            logs.value = data.items
            total.value = data.total
            totalPages.value = data.total_pages
            page.value = data.page
        } else {
            console.error('Failed to fetch logs')
        }
    } catch (e) {
        console.error('Error fetching logs:', e)
    } finally {
        loading.value = false
    }
}

const clearLogs = async () => {
    if (!confirm('Are you sure you want to clear all system logs? This action cannot be undone.')) return

    loading.value = true
    try {
        const res = await fetch('/api/v1/logs/', { method: 'DELETE' })
        if (res.ok) {
            logs.value = []
            total.value = 0
            totalPages.value = 1
            page.value = 1
        } else {
            console.error('Failed to clear logs')
        }
    } catch (e) {
        console.error('Error clearing logs:', e)
    } finally {
        loading.value = false
        fetchLogs()
    }
}

onMounted(() => {
    fetchLogs()
})
</script>
