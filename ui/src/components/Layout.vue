<template>
  <div class="flex h-screen w-full bg-gray-50 dark:bg-slate-900">
    <!-- Sidebar -->
    <aside class="w-64 flex-shrink-0 bg-white dark:bg-slate-800 border-r border-gray-200 dark:border-slate-700 hidden md:flex flex-col">
      <div class="h-16 flex items-center justify-center border-b border-gray-200 dark:border-slate-700">
        <h1 class="text-xl font-bold bg-gradient-to-r from-blue-500 to-indigo-600 bg-clip-text text-transparent">
          HNMS
        </h1>
      </div>

      <nav class="flex-1 overflow-y-auto py-4">
        <ul class="space-y-1 px-2">
          <li v-for="item in navItems" :key="item.name">
            <router-link
              :to="item.path"
              class="flex items-center px-4 py-2 text-sm font-medium rounded-md transition-colors duration-150"
              :class="[
                $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')
                  ? 'bg-blue-50 dark:bg-slate-700 text-blue-700 dark:text-blue-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-slate-700'
              ]"
            >
              <component :is="item.icon" class="mr-3 h-5 w-5 flex-shrink-0" />
              {{ item.name }}
            </router-link>
          </li>
        </ul>
      </nav>

      <div class="p-4 border-t border-gray-200 dark:border-slate-700">
        <p class="text-xs text-gray-500 dark:text-gray-400 text-center">
          v0.1.0 Alpha
        </p>
      </div>
    </aside>

    <!-- Mobile Header -->
    <div class="md:hidden fixed top-0 w-full bg-white dark:bg-slate-800 z-10 border-b border-gray-200 dark:border-slate-700 h-16 flex items-center justify-between px-4">
      <h1 class="text-lg font-bold">HNMS</h1>
      <button @click="mobileMenuOpen = !mobileMenuOpen" class="text-gray-500">
        <Bars3Icon class="h-6 w-6" />
      </button>
    </div>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto pt-16 md:pt-0">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 md:px-8 py-6">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { 
  HomeIcon, 
  ComputerDesktopIcon, 
  TableCellsIcon, 
  Cog6ToothIcon,
  Bars3Icon
} from '@heroicons/vue/24/outline'

const mobileMenuOpen = ref(false)

const navItems = [
  { name: 'Dashboard', path: '/', icon: HomeIcon },
  { name: 'Devices', path: '/devices', icon: ComputerDesktopIcon },
  { name: 'IP Occupancy', path: '/occupancy', icon: TableCellsIcon },
  { name: 'Settings', path: '/settings', icon: Cog6ToothIcon },
]
</script>
