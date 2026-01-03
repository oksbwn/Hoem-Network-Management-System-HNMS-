<template>
    <div class="absolute inset-0 overflow-hidden group" @mousemove="handleMouseMove" @mouseleave="handleMouseLeave"
        ref="container">
        <svg :viewBox="`0 0 ${width} ${height}`" class="w-full h-full overflow-visible" preserveAspectRatio="none">

            <!-- Up Link (Tx) - Blue -->
            <path :d="upPath" fill="none" stroke="#3b82f6" stroke-width="1.5" stroke-linecap="round"
                stroke-linejoin="round" class="opacity-60" />

            <!-- Down Link (Rx) - Green -->
            <path :d="downPath" fill="none" stroke="#10b981" stroke-width="1.5" stroke-linecap="round"
                stroke-linejoin="round" />

            <!-- Hover Vertical Line -->
            <line v-if="hoverIndex !== -1" :x1="hoverX" y1="0" :x2="hoverX" :y2="height" stroke="#64748b"
                stroke-width="1" stroke-dasharray="2 2" class="opacity-50" />
        </svg>

        <!-- Tooltip -->
        <div v-if="hoverIndex !== -1"
            class="hover-popover !opacity-100 !p-1.5 !bg-slate-900/90 !backdrop-blur !border-slate-700/50 !shadow-lg whitespace-nowrap flex flex-col gap-0.5 top-1/2 -translate-y-1/2"
            :class="[
                tooltipX > width / 2 ? '-translate-x-[105%]' : 'translate-x-[5%]'
            ]" :style="{ left: `${tooltipX}px` }">
            <div class="flex items-center gap-1.5">
                <div class="w-1.5 h-1.5 rounded-full bg-emerald-500"></div>
                <span class="font-mono">{{ formatBytes(tooltipData.down) }}</span>
            </div>
            <div class="flex items-center gap-1.5">
                <div class="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
                <span class="font-mono">{{ formatBytes(tooltipData.up) }}</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
    data: {
        type: Array, // Array of {down, up, timestamp}
        required: true
    },
    width: {
        type: Number,
        default: 100
    },
    height: {
        type: Number,
        default: 40
    }
})

const container = ref(null)
const hoverIndex = ref(-1)
const hoverX = ref(0)
const tooltipX = ref(0)

const tooltipData = computed(() => {
    if (hoverIndex.value === -1 || !props.data[hoverIndex.value]) return { down: 0, up: 0 }
    return props.data[hoverIndex.value]
})

const handleMouseMove = (e) => {
    if (!props.data || props.data.length < 2 || !container.value) return

    const rect = container.value.getBoundingClientRect()
    const x = e.clientX - rect.left
    const w = rect.width

    // Find closest index
    const count = props.data.length
    const idx = Math.min(Math.max(Math.round((x / w) * (count - 1)), 0), count - 1)

    hoverIndex.value = idx

    // Map index back to X coordinate for the line
    // The path uses points relative to props.width, but we are viewing in a container that scales content?
    // The SVG has viewBox="0 0 width height".
    // If the SVG scales to fit the container, then x/w ratio aligns with internal coordinate system.

    // Internal X coordinate
    const internalX = (idx / (count - 1)) * props.width
    hoverX.value = internalX

    // Tooltip position (visual pixels relative to container)
    // We can use the mouse X or the snapped X. Snapped X is better.
    tooltipX.value = (internalX / props.width) * w
}

const handleMouseLeave = () => {
    hoverIndex.value = -1
}

const formatBytes = (bytes, decimals = 1) => {
    if (!+bytes) return '0B'
    const k = 1024
    const dm = decimals < 0 ? 0 : decimals
    const sizes = ['B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))}${sizes[i]}`
}

const processPoints = (key) => {
    if (!props.data || props.data.length < 2) return ''

    // Find global max to scale both lines consistently (or relative to each other?)
    // Usually scaling relative to each other is better visually, or independent?
    // Independent makes them comparable in shape but misleading in magnitude. 
    // Consistent limit is better.
    // Let's use independent limits for "sparkline" purposes to show activity shape,
    // as up/down speeds can differ by orders of magnitude (100Mbps down vs 5Mbps up).
    // If we share limits, the 5Mbps line will be flat.

    const values = props.data.map(d => d[key])
    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = (max - min) || 1

    const padY = 5
    const usableHeight = props.height - (padY * 2)

    const pts = values.map((val, i) => ({
        x: (i / (values.length - 1)) * props.width,
        y: props.height - ((val - min) / range) * usableHeight - padY
    }))

    if (pts.length < 2) return ''

    // Simple line (no smoothing for performance/sharpness on small charts)
    let d = `M ${pts[0].x},${pts[0].y}`
    for (let i = 1; i < pts.length; i++) {
        d += ` L ${pts[i].x},${pts[i].y}`
    }
    return d
}

const upPath = computed(() => processPoints('up'))
const downPath = computed(() => processPoints('down'))

</script>
