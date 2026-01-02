<template>
    <div
        class="h-[calc(100vh-120px)] bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 relative overflow-hidden">

        <!-- Loading State -->
        <div v-if="loading"
            class="absolute inset-0 flex items-center justify-center z-10 bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
            <Loader2 class="h-10 w-10 animate-spin text-blue-500" />
        </div>

        <!-- Graph -->
        <v-network-graph v-if="!loading" class="w-full h-full" :nodes="nodes" :edges="edges" :configs="configs"
            v-model:zoom-level="zoomLevel">
            <!-- Custom Node Rendering -->
            <template #override-node="{ nodeId, scale, config }">
                <circle :r="(config.radius || 20) * 1.5" :fill="getNodeColor(nodes[nodeId])"
                    class="transition-all duration-300" :class="{ 'filter drop-shadow-lg': true }" />
                <!-- Icon Scaling -->
                <foreignObject :x="-(config.radius || 20)" :y="-(config.radius || 20)"
                    :width="(config.radius || 20) * 2" :height="(config.radius || 20) * 2" style="pointer-events: none">
                    <div class="flex items-center justify-center h-full w-full text-white">
                        <component :is="getIcon(nodes[nodeId].icon)" :size="(config.radius || 20) * 1.2"
                            stroke-width="2" />
                    </div>
                </foreignObject>
            </template>

            <!-- Tooltip / Label -->
            <template #override-node-label="{ nodeId, scale, config, text }">
                <text x="0" :y="(config.radius || 20) + 20" :font-size="14 * scale" text-anchor="middle"
                    fill="currentColor" class="text-slate-700 dark:text-slate-300 font-medium pointer-events-none"
                    :style="{ fontSize: (12 / scale) + 'px' }">
                    {{ text }}
                </text>
            </template>
        </v-network-graph>

        <!-- Controls -->
        <div
            class="absolute bottom-4 right-4 flex flex-col gap-2 bg-white dark:bg-slate-800 p-2 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
            <button @click="zoomIn"
                class="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors text-slate-600 dark:text-slate-400">
                <Plus class="h-5 w-5" />
            </button>
            <button @click="zoomOut"
                class="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors text-slate-600 dark:text-slate-400">
                <Minus class="h-5 w-5" />
            </button>
            <button @click="fetchTopology"
                class="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors text-slate-600 dark:text-slate-400">
                <RefreshCw class="h-5 w-5" :class="{ 'animate-spin': loading }" />
            </button>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from "vue"
import * as vNG from "v-network-graph"
import { ForceLayout } from "v-network-graph/lib/force-layout"
import { getIcon } from '@/utils/icons'
import {
    Loader2, Plus, Minus, RefreshCw,
} from 'lucide-vue-next'

const nodes = ref({})
const edges = ref({})
const loading = ref(true)
const zoomLevel = ref(1.0)

// Configs for v-network-graph
const configs = reactive(
    vNG.defineConfigs({
        view: {
            panEnabled: true,
            zoomEnabled: true,
            layoutHandler: new ForceLayout({
                positionFixedByDrag: false,
                positionFixedByClickWithAltKey: true,
                createSimulation: (d3, nodes, edges) => {
                    const forceLink = d3.forceLink(edges).id((d: any) => d.id)
                    return d3
                        .forceSimulation(nodes)
                        .force("edge", forceLink.distance(120))
                        .force("charge", d3.forceManyBody().strength(-1000))
                        .force("collide", d3.forceCollide(50)) // Prevent overlap
                        .force("center", d3.forceCenter().strength(0.05))
                        .alphaMin(0.001)
                }
            }),
        },
        node: {
            normal: {
                type: "circle",
                radius: 20, // Base radius
                color: "#4466cc",
            },
            hover: {
                radius: 24,
            },
            label: {
                visible: true,
                fontFamily: "Inter, sans-serif",
                fontSize: 14,
                color: "#ffffff", // Overridden by template
            },
        },
        edge: {
            normal: {
                width: 2,
                color: "#94a3b8", // slate-400
            },
            hover: {
                width: 4,
                color: "#3b82f6", // blue-500
            },
        },
    })
)

const fetchTopology = async () => {
    loading.value = true
    try {
        const res = await fetch("/api/v1/topology/")
        if (res.ok) {
            const data = await res.json()
            nodes.value = data.nodes
            edges.value = data.edges
        }
    } catch (e) {
        console.error("Failed to load topology", e)
    } finally {
        loading.value = false
    }
}

const getNodeColor = (node: any) => {
    if (node.type === 'Router') return '#8b5cf6' // Violet
    if (node.status === 'offline') return '#94a3b8' // Slate
    return '#3b82f6' // Blue
}

const zoomIn = () => {
    zoomLevel.value = Math.min(zoomLevel.value * 1.2, 5)
}
const zoomOut = () => {
    zoomLevel.value = Math.max(zoomLevel.value / 1.2, 0.1)
}

onMounted(() => {
    fetchTopology()
})
</script>

<style>
/* Ensure the foreignObject text color inherits correctly in dark mode if needed, 
   though we forced white inside the circle. */
</style>
