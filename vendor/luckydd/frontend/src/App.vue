<script setup lang="ts">
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <NavBar />
    <main class="container mx-auto px-4 py-6">
      <RouterView />
    </main>
    <footer class="bg-white border-t mt-8">
      <div class="container mx-auto px-4 py-4 text-center text-sm text-gray-500">
        <p>⚠️ 仅供娱乐研究，彩票开奖为随机事件，分析结果不构成投注建议</p>
        <p class="mt-1">LuckyDD © 2026</p>
      </div>
    </footer>
  </div>
</template>