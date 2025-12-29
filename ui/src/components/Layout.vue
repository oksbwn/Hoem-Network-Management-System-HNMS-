<template>
  <div class="flex h-screen w-full bg-slate-50 dark:bg-slate-900">
    <!-- Desktop Sidebar -->
    <aside :class="[
      'hidden md:flex flex-col bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transition-all duration-300',
      sidebarCollapsed ? 'w-16' : 'w-56'
    ]">
      <!-- Logo -->
      <div class="h-16 flex items-center justify-center border-b border-slate-200 dark:border-slate-700"
        :class="sidebarCollapsed ? '' : 'px-4 justify-start'">
        <AppLogo :compact="sidebarCollapsed" class="scale-90 origin-left" />
      </div>

      <!-- Navigation -->
      <nav class="flex-1 overflow-y-auto py-4 px-2">
        <ul class="space-y-1">
          <li v-for="item in navItems" :key="item.name">
            <router-link :to="item.path"
              class="flex items-center px-3 py-2.5 text-sm font-medium rounded-lg transition-colors group" :class="[
                $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')
                  ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400'
                  : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
              ]" v-tooltip:right="sidebarCollapsed ? item.name : null">
              <component :is="item.icon" class="h-5 w-5 flex-shrink-0" :class="sidebarCollapsed ? '' : 'mr-3'" />
              <span v-if="!sidebarCollapsed">{{ item.name }}</span>
            </router-link>
          </li>
        </ul>
      </nav>

      <!-- Version & Toggle -->
      <div class="p-2 border-t border-slate-200 dark:border-slate-700 space-y-2">
        <div v-if="!sidebarCollapsed"
          class="text-[10px] uppercase font-bold tracking-widest text-slate-400 dark:text-slate-600 text-center py-2">
          {{ version }}
        </div>
        <button @click="sidebarCollapsed = !sidebarCollapsed"
          class="w-full flex items-center p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-all duration-300"
          :class="sidebarCollapsed ? 'justify-center' : 'px-3 space-x-3'"
          v-tooltip:right="sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'">
          <component :is="sidebarCollapsed ? ChevronRightIcon : ChevronLeftIcon" class="h-5 w-5 flex-shrink-0" />
          <span v-if="!sidebarCollapsed" class="text-sm font-medium">Collapse</span>
        </button>
      </div>
    </aside>

    <!-- Mobile Header -->
    <div
      class="md:hidden fixed top-0 left-0 right-0 z-50 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
      <div class="h-16 flex items-center justify-between px-4">
        <AppLogo class="scale-90 origin-left" />
        <button @click="mobileMenuOpen = !mobileMenuOpen"
          class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300">
          <Bars3Icon class="h-6 w-6" />
        </button>
      </div>
    </div>

    <!-- Mobile Menu -->
    <Transition enter-active-class="transition-transform duration-300" enter-from-class="translate-x-full"
      enter-to-class="translate-x-0" leave-active-class="transition-transform duration-300"
      leave-from-class="translate-x-0" leave-to-class="translate-x-full">
      <div v-if="mobileMenuOpen" class="md:hidden fixed inset-0 z-40 bg-white dark:bg-slate-800 pt-16">
        <nav class="p-4">
          <ul class="space-y-1">
            <li v-for="item in navItems" :key="item.name">
              <router-link :to="item.path" @click="mobileMenuOpen = false"
                class="flex items-center px-4 py-3 text-sm font-medium rounded-lg" :class="[
                  $route.path === item.path || ($route.path.startsWith(item.path) && item.path !== '/')
                    ? 'bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400'
                    : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                ]">
                <component :is="item.icon" class="h-5 w-5 mr-3 flex-shrink-0" />
                {{ item.name }}
              </router-link>
            </li>
          </ul>
        </nav>
      </div>
    </Transition>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto pt-16 md:pt-0">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-8">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppLogo from './AppLogo.vue'
import {
  HomeIcon,
  ComputerDesktopIcon,
  TableCellsIcon,
  Cog6ToothIcon,
  Bars3Icon,
  ListBulletIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  BellIcon
} from '@heroicons/vue/24/outline'

const sidebarCollapsed = ref(true)
const mobileMenuOpen = ref(false)
const version = import.meta.env.VITE_APP_VERSION || 'v0.3.1'

const navItems = [
  { name: 'Dashboard', path: '/', icon: HomeIcon },
  { name: 'Devices', path: '/devices', icon: ComputerDesktopIcon },
  { name: 'Scan History', path: '/scans', icon: ListBulletIcon },
  { name: 'Events', path: '/events', icon: BellIcon },
  { name: 'IP Occupancy', path: '/occupancy', icon: TableCellsIcon },
  { name: 'Settings', path: '/settings', icon: Cog6ToothIcon },
]
</script>
