<template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
                <h1 class="text-2xl font-semibold text-slate-900 dark:text-white">Network Analytics</h1>
                <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
                    Traffic insights and device distribution
                </p>
            </div>

            <!-- Time Range Picker -->
            <div class="flex flex-wrap gap-1 bg-white dark:bg-slate-800 rounded-lg p-1 border border-slate-200 dark:border-slate-700 shadow-sm"
                v-if="localConfigured">
                <button v-for="r in ['24h', 'yesterday', '7d', '30d', '3m', 'mtd', 'last_month', 'ytd', '1y', 'all']"
                    :key="r" @click="timeRange = r"
                    class="px-3 py-1.5 text-xs font-medium rounded-md transition-all whitespace-nowrap"
                    :class="timeRange === r ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400 shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'">
                    {{ {
                        '24h': '24H', 'yesterday': 'Yesterday', '7d': '7D', '30d': '30D', '3m': '3M', 'mtd': 'MTD',
                        'last_month': 'Last Month', 'ytd': 'YTD', '1y': '1Y', 'all': 'All'
                    }[r] }}
                </button>
            </div>
        </div>

        <!-- Not Configured State -->
        <div v-if="!loading && !localConfigured"
            class="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-8 text-center max-w-2xl mx-auto mt-12">
            <div
                class="w-16 h-16 bg-slate-50 dark:bg-slate-700/50 rounded-full flex items-center justify-center mx-auto mb-4">
                <Router class="w-8 h-8 text-slate-400" />
            </div>
            <h2 class="text-lg font-semibold text-slate-900 dark:text-white mb-2">OpenWRT Integration Required</h2>
            <p class="text-slate-500 dark:text-slate-400 text-sm mb-6 max-w-md mx-auto">
                To view traffic analytics, you need to connect your OpenWRT router and install the <code
                    class="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded text-xs font-mono text-blue-600">nlbwmon</code>
                package.
            </p>
            <router-link to="/settings"
                class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors">
                <Settings class="w-4 h-4" />
                Configure Integration
            </router-link>

            <div class="mt-8 pt-8 border-t border-slate-100 dark:border-slate-700 text-left">
                <p class="text-xs font-semibold text-slate-900 dark:text-white uppercase tracking-wider mb-3">Quick
                    Setup Guide</p>
                <ol class="space-y-2 text-sm text-slate-600 dark:text-slate-400 list-decimal pl-4">
                    <li>SSH into your OpenWRT router</li>
                    <li>Run: <code
                            class="bg-slate-100 dark:bg-slate-900 px-1 py-0.5 rounded font-mono text-xs">opkg update && opkg install nlbwmon</code>
                    </li>
                    <li>Go to Settings > Integrations in this app</li>
                    <li>Enter your router IP and credentials</li>
                </ol>
            </div>
        </div>

        <!-- Dashboard -->
        <div v-else-if="!loading" class="space-y-6">

            <!-- Key Metrics -->
            <!-- Active Devices Count Fix -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div
                    class="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">
                    <div class="absolute right-0 top-0 p-4 opacity-5">
                        <Download class="w-16 h-16" />
                    </div>
                    <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                        Total Download</p>
                    <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ formatBytes(trafficTotals.download)
                        }}</p>
                </div>
                <div
                    class="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">
                    <div class="absolute right-0 top-0 p-4 opacity-5">
                        <Upload class="w-16 h-16" />
                    </div>
                    <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                        Total Upload</p>
                    <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ formatBytes(trafficTotals.upload) }}
                    </p>
                </div>
                <div
                    class="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">
                    <div class="absolute right-0 top-0 p-4 opacity-5">
                        <Users class="w-16 h-16" />
                    </div>
                    <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">
                        Active Devices</p>
                    <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ trafficTotals.active_devices }}</p>
                </div>
                <div
                    class="bg-white dark:bg-slate-800 p-5 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm relative overflow-hidden">
                    <div class="absolute right-0 top-0 p-4 opacity-5">
                        <Activity class="w-16 h-16" />
                    </div>
                    <p class="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1">Avg
                        Throughput</p>
                    <p class="text-2xl font-bold text-slate-900 dark:text-white">{{ calculateAvgThroughput() }}</p>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Main Traffic Chart -->
                <div
                    class="lg:col-span-3 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                    <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-6">Traffic Overview</h3>
                    <div class="h-[350px]">
                        <apexchart type="area" height="100%" :options="chartOptions" :series="chartSeries" />
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Top Consumers List (Moved here, resized) -->
                <div
                    class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col">
                    <div class="p-6 border-b border-slate-100 dark:border-slate-700">
                        <h3 class="text-base font-semibold text-slate-900 dark:text-white">Top Consumers</h3>
                    </div>
                    <div class="flex-1 overflow-y-auto max-h-[350px] p-4 space-y-4 custom-scrollbar">
                        <div v-for="(device, idx) in topDevices" :key="device.id" class="flex items-center gap-3 group">
                            <div class="w-6 text-center text-xs font-bold text-slate-400">#{{ idx + 1 }}</div>
                            <div
                                class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-700 flex items-center justify-center text-slate-600 dark:text-slate-400">
                                <component :is="getIcon(device.icon || 'help-circle')" class="w-5 h-5" />
                            </div>
                            <div class="flex-1 min-w-0">
                                <div class="flex justify-between mb-1">
                                    <span class="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">{{
                                        device.name }}</span>
                                    <span class="text-xs font-semibold text-slate-900 dark:text-white">{{
                                        formatBytes(device.total) }}</span>
                                </div>
                                <div class="w-full h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                    <div class="h-full bg-blue-500 rounded-full"
                                        :style="{ width: getUsagePercent(device.total) + '%' }"></div>
                                </div>
                                <div class="flex justify-between mt-1 text-[10px] text-slate-400">
                                    <span>↓ {{ formatBytes(device.download) }}</span>
                                    <span>↑ {{ formatBytes(device.upload) }}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Vendor Distribution (Moved next to Top Consumers) -->
                <div
                    class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                    <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-4">Vendor Distribution (Count)
                    </h3>
                    <div class="h-[350px] flex items-center justify-center">
                        <apexchart type="donut" height="300" :options="donutOptions" :series="vendorSeries" />
                    </div>
                </div>
            </div>

            <!-- Bottom Row: Category Usage & Device Types -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Usage by Category (Traffic) -->
                <div
                    class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm flex flex-col">
                    <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-2">Traffic Volume by Category
                    </h3>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mb-4">Total data consumed by device type</p>
                    <div class="flex-1 min-h-[300px] flex items-center justify-center">
                        <div v-if="categorySeries.length === 0" class="text-sm text-slate-400">No data available</div>
                        <apexchart v-else type="donut" width="100%" height="300" :options="categoryOptions"
                            :series="categorySeries" />
                    </div>
                </div>

                <!-- Device Types (Count) -->
                <div
                    class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-6 shadow-sm">
                    <h3 class="text-base font-semibold text-slate-900 dark:text-white mb-2">Device Count by Category
                    </h3>
                    <p class="text-sm text-slate-500 dark:text-slate-400 mb-4">Number of devices per type</p>
                    <div class="h-[300px]">
                        <apexchart type="bar" height="100%" :options="barOptions" :series="typeSeries" />
                    </div>
                </div>
            </div>



        </div>

        <!-- Loading State -->
        <div v-else class="h-96 flex items-center justify-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import * as LucideIcons from 'lucide-vue-next'
const { Router, Settings, Download, Upload, Users, Activity } = LucideIcons
import { formatBytes } from '@/utils/format'

const loading = ref(true)
const localConfigured = ref(false)
const timeRange = ref('7d')

const trafficTotals = ref({ download: 0, upload: 0, active_devices: 0 })
const topDevices = ref([])

const chartSeries = ref([])
const vendorSeries = ref([])
const categorySeries = ref([])
const typeSeries = ref([])

// Icon Helper
const getIcon = (name) => {
    if (!name) return LucideIcons.HelpCircle
    if (LucideIcons[name]) return LucideIcons[name]

    const legacyMap = {
        'smartphone': 'Smartphone', 'tablet': 'Tablet', 'laptop': 'Laptop', 'monitor': 'Monitor',
        'server': 'Server', 'router': 'Router', 'network': 'Network', 'tv': 'Tv', 'printer': 'Printer',
        'computer-desktop': 'Monitor', 'device-laptop': 'Laptop', 'device-phone-mobile': 'Smartphone',
        'device-tablet': 'Tablet'
    }
    if (legacyMap[name] && LucideIcons[legacyMap[name]]) return LucideIcons[legacyMap[name]]

    const camel = name.split('-').map(p => p.charAt(0).toUpperCase() + p.slice(1)).join('')
    if (LucideIcons[camel]) return LucideIcons[camel]

    return LucideIcons.HelpCircle
}

// Check Config
const checkConfig = async () => {
    try {
        const res = await axios.get('/api/v1/integrations/openwrt/config')
        localConfigured.value = res.data && res.data.verified && res.data.enabled
    } catch (e) {
        localConfigured.value = false
    }
}

const usagePage = ref(1)
const usageTotalPages = ref(1)
const usageDevices = ref([])
const usageLoading = ref(false)

const fetchData = async () => {
    if (!localConfigured.value) {
        loading.value = false
        return
    }

    loading.value = true
    try {
        // Parallel Fetch (Top Consumers Limit reduced to 5)
        const [trafficRes, topRes, distRes, catRes] = await Promise.all([
            axios.get(`/api/v1/analytics/traffic?range=${timeRange.value}`),
            axios.get(`/api/v1/analytics/top-devices?range=${timeRange.value}&limit=5`),
            axios.get(`/api/v1/analytics/distribution?range=${timeRange.value}`),
            axios.get(`/api/v1/analytics/category-usage?range=${timeRange.value}`)
        ])

        // Process Traffic
        trafficTotals.value = trafficRes.data.totals
        const series = trafficRes.data.series
        chartSeries.value = [
            { name: 'Download', data: series.map(d => [new Date(d.timestamp).getTime(), d.download]) },
            { name: 'Upload', data: series.map(d => [new Date(d.timestamp).getTime(), d.upload]) }
        ]

        // Process Top Devices (Top 5 for widget)
        topDevices.value = topRes.data

        // Process Distribution
        vendorSeries.value = distRes.data.vendors.map(v => v.value)
        typeSeries.value = [{ name: 'Devices', data: distRes.data.types.map(t => t.value) }]

        // Process Category Usage
        categorySeries.value = catRes.data.map(c => c.total)

        // Update Options
        updateChartOptions(distRes.data, topRes.data, catRes.data)

        // Fetch paginated table
        await fetchUsageDetails()

    } catch (e) {
        console.error("Failed to load analytics", e)
    } finally {
        loading.value = false
    }
}

const fetchUsageDetails = async () => {
    usageLoading.value = true
    try {
        const res = await axios.get(`/api/v1/analytics/usage-details?range=${timeRange.value}&page=${usagePage.value}&limit=10`)
        usageDevices.value = res.data.items
        usageTotalPages.value = res.data.pages
    } catch (e) {
        console.error("Failed to load usage details", e)
    } finally {
        usageLoading.value = false
    }
}

const changeUsagePage = (delta) => {
    const newPage = usagePage.value + delta
    if (newPage >= 1 && newPage <= usageTotalPages.value) {
        usagePage.value = newPage
        fetchUsageDetails()
    }
}

// Chart Options
const commonOptions = {
    chart: { toolbar: { show: false }, fontFamily: 'inherit', background: 'transparent' },
    theme: { mode: 'light' },
    stroke: { curve: 'smooth', width: 2 },
    xaxis: { type: 'datetime', tooltip: { enabled: false }, axisBorder: { show: false }, axisTicks: { show: false } },
    grid: { borderColor: '#f1f5f9', strokeDashArray: 4, padding: { top: 0, right: 0, bottom: 0, left: 10 } },
    colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'],
    dataLabels: { enabled: false },
    tooltip: { theme: 'dark' },
    legend: { position: 'top' }
}

const chartOptions = ref({
    ...commonOptions,
    tooltip: { theme: 'dark', x: { format: 'dd MMM HH:mm' } },
    yaxis: {
        labels: { formatter: (val) => formatBytes(val, 0) }
    },
    fill: { type: 'gradient', gradient: { opacityFrom: 0.5, opacityTo: 0.1 } }
})

const donutOptions = ref({
    ...commonOptions,
    chart: { type: 'donut', fontFamily: 'inherit' },
    plotOptions: { pie: { donut: { size: '65%' } } },
    stroke: { show: false },
    labels: [],
    dataLabels: { enabled: false },
    legend: { position: 'bottom' }
})

const categoryOptions = ref({
    ...commonOptions,
    chart: { type: 'donut', fontFamily: 'inherit' },
    plotOptions: { pie: { donut: { size: '65%' } } },
    stroke: { show: false },
    labels: [],
    colors: ['#6366f1', '#8b5cf6', '#d946ef', '#f43f5e', '#f97316'],
    dataLabels: { enabled: false },
    legend: { position: 'bottom' },
    tooltip: {
        theme: 'dark',
        y: { formatter: (val) => formatBytes(val) }
    }
})

const barOptions = ref({
    ...commonOptions,
    chart: { type: 'bar', fontFamily: 'inherit', toolbar: { show: false } },
    xaxis: { categories: [], axisBorder: { show: false }, axisTicks: { show: false } },
    plotOptions: { bar: { borderRadius: 4, columnWidth: '50%' } }
})

const updateChartOptions = (distData, topData, catData) => {
    donutOptions.value = {
        ...donutOptions.value,
        labels: distData.vendors.map(v => v.label)
    }

    barOptions.value = {
        ...barOptions.value,
        xaxis: { ...barOptions.value.xaxis, categories: distData.types.map(t => t.label) }
    }

    categoryOptions.value = {
        ...categoryOptions.value,
        labels: catData.map(c => c.label)
    }
}

const getUsagePercent = (val) => {
    if (topDevices.value.length === 0) return 0
    const max = topDevices.value[0].total
    return max > 0 ? (val / max) * 100 : 0
}

const calculateAvgThroughput = () => {
    const total = trafficTotals.value.download + trafficTotals.value.upload
    if (total === 0) return '0 B/s'

    let seconds = 1
    const now = new Date()

    switch (timeRange.value) {
        case '24h':
        case 'yesterday':
            seconds = 24 * 3600
            break
        case '7d':
            seconds = 7 * 24 * 3600
            break
        case '30d':
            seconds = 30 * 24 * 3600
            break
        case '3m':
            seconds = 90 * 24 * 3600
            break
        case 'last_month':
            const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1)
            const lastMonthEnd = new Date(thisMonth.getTime() - 1)
            const lastMonthStart = new Date(lastMonthEnd.getFullYear(), lastMonthEnd.getMonth(), 1)
            seconds = Math.ceil((lastMonthEnd - lastMonthStart) / 1000)
            break
        case 'mtd':
            const mtdStart = new Date(now.getFullYear(), now.getMonth(), 1)
            seconds = Math.max(1, (now - mtdStart) / 1000)
            break
        case 'ytd':
            const ytdStart = new Date(now.getFullYear(), 0, 1)
            seconds = Math.max(1, (now - ytdStart) / 1000)
            break
        case '1y':
            seconds = 365 * 24 * 3600
            break
        case 'all':
            // Try to find earliest data point, else default to 1y
            let earliest = now.getTime()
            if (chartSeries.value.length > 0 && chartSeries.value[0].data.length > 0) {
                earliest = chartSeries.value[0].data[0][0]
            }
            const diff = (now.getTime() - earliest) / 1000
            seconds = Math.max(24 * 3600, diff) // Min 1 day
            break
    }

    return formatBytes(total / seconds) + '/s'
}

onMounted(async () => {
    await checkConfig()
    if (localConfigured.value) {
        await fetchData()
    } else {
        loading.value = false
    }
})

watch(timeRange, () => {
    usagePage.value = 1
    fetchData()
})

</script>
