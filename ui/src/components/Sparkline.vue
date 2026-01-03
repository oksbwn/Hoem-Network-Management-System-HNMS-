<template>
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
        <svg :viewBox="`0 0 ${width} ${height}`" class="w-full h-full overflow-visible" preserveAspectRatio="none">
            <!-- Glow Effect -->
            <path :d="path" fill="none" :stroke="color" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
                class="opacity-5 blur-[2px]" />

            <!-- Area Fill -->
            <path :d="fillPath" :fill="`url(#gradient-${uniqueId})`" class="transition-opacity duration-1000 delay-300"
                :class="isVisible ? 'opacity-5 dark:opacity-10' : 'opacity-0'" />

            <!-- Main Path -->
            <path :d="path" fill="none" :stroke="color" stroke-width="1.2" stroke-linecap="round"
                stroke-linejoin="round" class="transition-all duration-1000 ease-out [stroke-dasharray:1000]"
                :class="isVisible ? '[stroke-dashoffset:0]' : '[stroke-dashoffset:1000]'" />

            <defs>
                <linearGradient :id="`gradient-${uniqueId}`" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" :stop-color="color" />
                    <stop offset="100%" :stop-color="color" stop-opacity="0" />
                </linearGradient>
            </defs>
        </svg>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
    data: {
        type: Array,
        required: true
    },
    color: {
        type: String,
        default: '#3b82f6'
    },
    width: {
        type: Number,
        default: 100
    },
    height: {
        type: Number,
        default: 100 // Scale to container
    },
    showPoints: {
        type: Boolean,
        default: true
    }
})

const isVisible = ref(false)
const uniqueId = Math.random().toString(36).substring(2, 9)

const points = computed(() => {
    if (props.data.length < 2) return []

    const min = Math.min(...props.data)
    const max = Math.max(...props.data)
    const range = (max - min) || 1

    // Padding inside the SVG to ensure dots/line aren't clipped
    const padY = 20
    const usableHeight = props.height - (padY * 2)

    return props.data.map((val, i) => ({
        x: (i / (props.data.length - 1)) * props.width,
        y: props.height - ((val - min) / range) * usableHeight - padY
    }))
})

const getControlPoints = (p0, p1, p2, t) => {
    const d01 = Math.sqrt(Math.pow(p1.x - p0.x, 2) + Math.pow(p1.y - p0.y, 2))
    const d12 = Math.sqrt(Math.pow(p2.x - p1.x, 2) + Math.pow(p2.y - p1.y, 2))
    const fa = (t * d01) / (d01 + d12)
    const fb = (t * d12) / (d01 + d12)
    const p1x = p1.x - fa * (p2.x - p0.x)
    const p1y = p1.y - fa * (p2.y - p0.y)
    const p2x = p1.x + fb * (p2.x - p0.x)
    const p2y = p1.y + fb * (p2.y - p0.y)
    return { p1: { x: p1x, y: p1y }, p2: { x: p2x, y: p2y } }
}

const path = computed(() => {
    const pts = points.value
    if (pts.length < 2) return ''

    let d = `M ${pts[0].x},${pts[0].y}`

    for (let i = 0; i < pts.length - 1; i++) {
        const p0 = pts[i - 1] || pts[i]
        const p1 = pts[i]
        const p2 = pts[i + 1]
        const p3 = pts[i + 2] || p2

        const cp1 = getControlPoints(p0, p1, p2, 0.2).p2
        const cp2 = getControlPoints(p1, p2, p3, 0.2).p1

        d += ` C ${cp1.x},${cp1.y} ${cp2.x},${cp2.y} ${p2.x},${p2.y}`
    }

    return d
})

const fillPath = computed(() => {
    const p = path.value
    if (!p) return ''
    return `${p} L ${props.width},${props.height} L 0,${props.height} Z`
})

onMounted(() => {
    setTimeout(() => {
        isVisible.value = true
    }, 100)
})
</script>
