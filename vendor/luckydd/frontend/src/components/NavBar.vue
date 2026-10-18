<script setup lang="ts">
import { ref } from 'vue'
import { Ticket, BarChart3, LineChart, Sparkles, Menu, X } from 'lucide-vue-next'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const isMenuOpen = ref(false)

const navItems = [
  { name: '首页', icon: Ticket, path: '/' },
  { name: '数据查询', icon: BarChart3, path: '/data' },
  { name: '统计分析', icon: LineChart, path: '/analysis' },
  { name: '创新分析', icon: Sparkles, path: '/advanced' },
  { name: '智能推荐', icon: Sparkles, path: '/recommend' }
]

const toggleMenu = () => {
  isMenuOpen.value = !isMenuOpen.value
}

const isActive = (path: string) => route.path === path
</script>

<template>
  <nav class="bg-white shadow-md sticky top-0 z-50">
    <div class="container mx-auto px-4">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center space-x-2">
          <div class="w-10 h-10 bg-gradient-to-br from-red-500 to-blue-600 rounded-lg flex items-center justify-center">
            <Ticket class="w-6 h-6 text-white" />
          </div>
          <span class="text-xl font-bold bg-gradient-to-r from-red-500 to-blue-600 bg-clip-text text-transparent">
            LuckyDD
          </span>
        </div>

        <div class="hidden md:flex items-center space-x-1">
          <button
            v-for="item in navItems"
            :key="item.path"
            @click="router.push(item.path)"
            :class="[
              'flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200',
              isActive(item.path)
                ? 'bg-gradient-to-r from-red-500 to-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            ]"
          >
            <component :is="item.icon" class="w-5 h-5" />
            <span>{{ item.name }}</span>
          </button>
        </div>

        <button @click="toggleMenu" class="md:hidden p-2 rounded-lg hover:bg-gray-100">
          <Menu v-if="!isMenuOpen" class="w-6 h-6 text-gray-600" />
          <X v-else class="w-6 h-6 text-gray-600" />
        </button>
      </div>

      <div
        v-if="isMenuOpen"
        class="md:hidden py-4 border-t"
      >
        <button
          v-for="item in navItems"
          :key="item.path"
          @click="router.push(item.path); isMenuOpen = false"
          :class="[
            'flex items-center space-x-3 w-full px-4 py-3 rounded-lg transition-all duration-200',
            isActive(item.path)
              ? 'bg-gradient-to-r from-red-500 to-blue-600 text-white'
              : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          <component :is="item.icon" class="w-5 h-5" />
          <span>{{ item.name }}</span>
        </button>
      </div>
    </div>
  </nav>
</template>