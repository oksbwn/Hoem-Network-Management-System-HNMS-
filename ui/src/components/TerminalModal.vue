<template>
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
        <div class="terminal-panel">
            <!-- Header -->
            <div class="terminal-header">
                <div class="flex items-center space-x-2">
                    <div class="h-3 w-3 rounded-full bg-red-500"></div>
                    <div class="h-3 w-3 rounded-full bg-yellow-500"></div>
                    <div class="h-3 w-3 rounded-full bg-green-500"></div>
                    <span class="ml-2 text-gray-300 font-mono text-sm">ssh {{ device.ip }}</span>
                </div>
                <button @click="$emit('close')" class="text-gray-400 hover:text-white">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>

            <!-- Auth Form -->
            <div v-if="!connected && !terminalActive" class="flex-1 flex items-center justify-center">
                <div class="w-full max-w-xs space-y-4">
                    <h3 class="text-white text-lg font-bold text-center">SSH Credentials</h3>
                    <div>
                        <label class="block text-xs font-mono text-gray-400 mb-1">Username</label>
                        <input v-model="username" type="text" class="terminal-input" placeholder="pi" />
                    </div>
                    <div>
                        <label class="block text-xs font-mono text-gray-400 mb-1">Password</label>
                        <input v-model="password" type="password" class="terminal-input" />
                    </div>
                    <button @click="connect" :disabled="connecting"
                        class="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 font-bold disabled:opacity-50">
                        {{ connecting ? 'Connecting...' : 'Connect' }}
                    </button>
                    <p v-if="error" class="text-red-400 text-xs text-center">{{ error }}</p>
                </div>
            </div>

            <!-- Terminal -->
            <div v-show="terminalActive" class="flex-1 bg-black p-2 overflow-hidden relative">
                <div ref="terminalContainer" class="h-full w-full"></div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'

const props = defineProps({
    device: Object,
    port: {
        type: Number,
        default: 22
    }
})

const emit = defineEmits(['close'])

const username = ref('')
const password = ref('')
const connecting = ref(false)
const connected = ref(false)
const terminalActive = ref(false)
const error = ref('')
const terminalContainer = ref(null)

let term = null
let fitAddon = null
let ws = null

const connect = async () => {
    if (!username.value || !password.value) {
        error.value = "Username and password required"
        return
    }

    connecting.value = true
    error.value = ''

    // Switch UI immediately to terminal style logs
    terminalActive.value = true

    await nextTick()
    initTerminal()

    term.write(`\r\nConnecting to ${props.device.ip}:${props.port}...\r\n`)

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ssh/ws/${props.device.ip}`

    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
        // Send auth
        ws.send(JSON.stringify({
            username: username.value,
            password: password.value,
            port: props.port
        }))
    }

    ws.onmessage = (event) => {
        if (event.data instanceof Blob) {
            const reader = new FileReader()
            reader.onload = () => {
                term.write(new Uint8Array(reader.result))
            }
            reader.readAsArrayBuffer(event.data)
        } else {
            term.write(event.data)
        }
    }

    ws.onclose = (e) => {
        term.write(`\r\n*** Connection Closed (${e.code}: ${e.reason || 'No reason'}) ***\r\n`)
        console.error("WebSocket Close:", e)
        connected.value = false
        connecting.value = false
    }

    ws.onerror = (e) => {
        term.write('\r\n*** WebSocket Error ***\r\n')
        console.error("WebSocket Error:", e)
        connecting.value = false
    }

    term.onData(data => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(data)
        }
    })
}

const initTerminal = () => {
    if (term) return

    term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Menlo, Monaco, "Courier New", monospace',
        theme: {
            background: '#000000',
        }
    })

    fitAddon = new FitAddon()
    term.loadAddon(fitAddon)

    term.open(terminalContainer.value)
    fitAddon.fit()

    term.write('Welcome to Network Scanner SSH Console\r\n')

    window.addEventListener('resize', handleResize)
}

const handleResize = () => {
    if (fitAddon) fitAddon.fit()
}

onUnmounted(() => {
    if (ws) ws.close()
    if (term) term.dispose()
    window.removeEventListener('resize', handleResize)
})
</script>
