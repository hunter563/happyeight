<script setup lang="ts">import { ref, onMounted } from 'vue';
import { Ticket, TrendingUp, Sparkles, RefreshCw, X } from 'lucide-vue-next';
import axios from 'axios';

interface LotteryData {
  id: string
  date: string
  red_numbers?: number[]
  blue_number?: number
  front_numbers?: number[]
  back_numbers?: number[]
  numbers?: number[]
  basic_numbers?: number[]
  special_number?: number
}

const latestData = ref<Record<string, LotteryData>>({});
const isLoading = ref(false);
const showQrModal = ref(false);

const lotteryTypes = [
  { key: 'double_color_ball', label: '双色球', color: 'red', subColor: 'blue' },
  { key: 'super_lotto', label: '大乐透', color: 'green', subColor: 'blue' },
  { key: 'lottery_3d', label: '福彩3D', color: 'purple', subColor: 'purple' },
  { key: 'happy_8', label: '快乐8', color: 'orange', subColor: 'orange' },
  { key: 'arrangement_3', label: '排列3', color: 'indigo', subColor: 'indigo' },
  { key: 'arrangement_5', label: '排列5', color: 'cyan', subColor: 'cyan' },
  { key: 'seven_star', label: '七星彩', color: 'teal', subColor: 'teal' },
  { key: 'seven_color', label: '七乐彩', color: 'pink', subColor: 'yellow' }
]

const colorClasses: Record<string, Record<string, string>> = {
  red: { primary: 'bg-red-500', secondary: 'bg-red-100', text: 'text-red-600' },
  blue: { primary: 'bg-blue-500', secondary: 'bg-blue-100', text: 'text-blue-600' },
  green: { primary: 'bg-green-500', secondary: 'bg-green-100', text: 'text-green-600' },
  purple: { primary: 'bg-purple-500', secondary: 'bg-purple-100', text: 'text-purple-600' },
  orange: { primary: 'bg-orange-500', secondary: 'bg-orange-100', text: 'text-orange-600' },
  indigo: { primary: 'bg-indigo-500', secondary: 'bg-indigo-100', text: 'text-indigo-600' },
  cyan: { primary: 'bg-cyan-500', secondary: 'bg-cyan-100', text: 'text-cyan-600' },
  teal: { primary: 'bg-teal-500', secondary: 'bg-teal-100', text: 'text-teal-600' },
  pink: { primary: 'bg-pink-500', secondary: 'bg-pink-100', text: 'text-pink-600' },
  yellow: { primary: 'bg-yellow-500', secondary: 'bg-yellow-100', text: 'text-yellow-600' }
}

const loadLatestData = async () => {
  isLoading.value = true;
  try {
    const promises = lotteryTypes.map(type => 
      axios.get(`/api/lottery/latest/${type.key.replace(/_/g, '-')}`)
    );
    
    const results = await Promise.allSettled(promises);
    
    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        latestData.value[lotteryTypes[index].key] = result.value.data;
      }
    });
  }
  catch (error) {
    console.error('Failed to load latest data:', error);
  }
  finally {
    isLoading.value = false;
  }
};

const refreshData = async () => {
  try {
    await axios.post('/api/crawler/all');
    await loadLatestData();
  }
  catch (error) {
    console.error('Failed to refresh data:', error);
  }
};

onMounted(() => {
  loadLatestData();
});
</script>

<template>
  <div class="space-y-6">
    <div class="bg-gradient-to-r from-red-500 to-blue-600 rounded-2xl p-6 text-white">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold mb-2">LuckyDD</h1>
          <p class="text-white/80">彩票数据分析与特征探索平台</p>
        </div>
        <div class="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
          <Ticket class="w-8 h-8" />
        </div>
      </div>
      <div class="mt-4 flex items-center space-x-4">
        <button
          @click="refreshData"
          :disabled="isLoading"
          class="flex items-center space-x-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg transition-colors"
        >
          <RefreshCw class="w-4 h-4" :class="{ 'animate-spin': isLoading }" />
          <span>刷新数据</span>
        </button>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div
        v-for="type in lotteryTypes"
        :key="type.key"
        class="bg-white rounded-xl shadow-md p-4"
      >
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-lg font-semibold text-gray-800">{{ type.label }}</h3>
          <span :class="[
            'px-2 py-1 text-xs rounded-full',
            colorClasses[type.color].secondary,
            colorClasses[type.color].text
          ]">最新</span>
        </div>
        
        <div v-if="latestData[type.key]" class="space-y-3">
          <div class="flex justify-between text-sm text-gray-500">
            <span>期号: {{ latestData[type.key].id }}</span>
            <span>{{ latestData[type.key].date }}</span>
          </div>
          
          <div class="flex flex-wrap gap-1">
            <template v-if="type.key === 'double_color_ball'">
              <div
                v-for="(num, index) in latestData[type.key].red_numbers"
                :key="index"
                :class="[
                  'w-8 h-8 text-white rounded-full flex items-center justify-center text-sm font-bold',
                  colorClasses['red'].primary
                ]"
              >
                {{ num }}
              </div>
              <div
                :class="[
                  'w-8 h-8 text-white rounded-full flex items-center justify-center text-sm font-bold',
                  colorClasses['blue'].primary
                ]"
              >
                {{ latestData[type.key].blue_number }}
              </div>
            </template>

            <template v-else-if="type.key === 'super_lotto'">
              <div
                v-for="(num, index) in latestData[type.key].front_numbers"
                :key="index"
                :class="[
                  'w-8 h-8 text-white rounded-full flex items-center justify-center text-sm font-bold',
                  colorClasses['green'].primary
                ]"
              >
                {{ num }}
              </div>
              <div
                v-for="(num, index) in latestData[type.key].back_numbers"
                :key="'back-' + index"
                :class="[
                  'w-8 h-8 text-white rounded-full flex items-center justify-center text-sm font-bold',
                  colorClasses['blue'].primary
                ]"
              >
                {{ num }}
              </div>
            </template>

            <template v-else-if="type.key === 'seven_color'">
              <div
                v-for="(num, index) in latestData[type.key].basic_numbers"
                :key="index"
                :class="[
                  'w-7 h-7 text-white rounded-full flex items-center justify-center text-xs font-bold',
                  colorClasses['pink'].primary
                ]"
              >
                {{ num }}
              </div>
              <div
                :class="[
                  'w-7 h-7 text-white rounded-full flex items-center justify-center text-xs font-bold',
                  colorClasses['yellow'].primary
                ]"
              >
                {{ latestData[type.key].special_number }}
              </div>
            </template>

            <template v-else-if="type.key === 'happy_8'">
              <div
                v-for="(num, index) in latestData[type.key]?.numbers?.slice(0, 10) || []"
                :key="index"
                :class="[
                  'w-6 h-6 text-white rounded-full flex items-center justify-center text-xs font-bold',
                  colorClasses['orange'].primary
                ]"
              >
                {{ num }}
              </div>
              <span class="text-gray-400 text-xs self-center">...</span>
            </template>

            <template v-else>
              <div
                v-for="(num, index) in latestData[type.key].numbers"
                :key="index"
                :class="[
                  type.key === 'lottery_3d' ? 'w-10 h-10 text-lg' : 'w-8 h-8 text-sm',
                  'text-white rounded-full flex items-center justify-center font-bold',
                  colorClasses[type.color].primary
                ]"
              >
                {{ num }}
              </div>
            </template>
          </div>
        </div>
        
        <div v-else class="text-center text-gray-400 py-4">
          <p>暂无数据</p>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="bg-white rounded-xl shadow-md p-6">
        <div class="flex items-center space-x-2 mb-4">
          <TrendingUp class="w-5 h-5 text-blue-500" />
          <h3 class="text-lg font-semibold text-gray-800">统计分析</h3>
        </div>
        <p class="text-gray-600 mb-4">深入分析历史开奖数据，挖掘统计特征和规律</p>
        <ul class="space-y-2 text-sm text-gray-500">
          <li class="flex items-center space-x-2">
            <span class="w-2 h-2 bg-red-500 rounded-full"></span>
            <span>冷热号分析</span>
          </li>
          <li class="flex items-center space-x-2">
            <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
            <span>遗漏值统计</span>
          </li>
          <li class="flex items-center space-x-2">
            <span class="w-2 h-2 bg-green-500 rounded-full"></span>
            <span>区间分布分析</span>
          </li>
          <li class="flex items-center space-x-2">
            <span class="w-2 h-2 bg-yellow-500 rounded-full"></span>
            <span>和值与奇偶分析</span>
          </li>
        </ul>
      </div>

      <div class="bg-white rounded-xl shadow-md p-6">
        <div class="flex items-center space-x-2 mb-4">
          <Sparkles class="w-5 h-5 text-purple-500" />
          <h3 class="text-lg font-semibold text-gray-800">创新分析</h3>
        </div>
        <p class="text-gray-600 mb-4">采用数据挖掘算法，发现隐藏的号码模式和异常</p>
        <ul class="space-y-2 text-sm text-gray-500">
          <li class="flex items-center space-x-2">
            <span class="w-2 h-2 bg-purple-500 rounded-full"></span>
            <span>频繁号码组合挖掘</span>
          </li>
          <li class="flex items-center space-x-2">
            <span class="w-2 h-2 bg-orange-500 rounded-full"></span>
            <span>号码关联规则分析</span>
          </li>
          <li class="flex items-center space-x-2">
            <span class="w-2 h-2 bg-red-500 rounded-full"></span>
            <span>异常开奖模式检测</span>
          </li>
          <li class="flex items-center space-x-2">
            <span class="w-2 h-2 bg-teal-500 rounded-full"></span>
            <span>序列模式发现</span>
          </li>
        </ul>
      </div>
    </div>

    <div class="bg-gradient-to-r from-red-500 to-blue-600 rounded-2xl p-6 text-white">
      <div class="flex items-center space-x-3 mb-4">
        <svg class="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 0C5.374 0 0 5.374 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
        </svg>
        <h3 class="text-xl font-bold">QQ交流群</h3>
      </div>
      <div class="flex flex-col md:flex-row items-center justify-between gap-4">
          <div class="text-center md:text-left">
            <p class="text-white/80 mb-2">扫码加入交流群，一起探讨彩票分析技巧</p>
            <p class="text-lg font-semibold">群号：1038534078</p>
          </div>
          <div class="bg-white/20 rounded-xl p-3 cursor-pointer hover:bg-white/30 transition-colors" @click="showQrModal = true">
            <img src="/qrcode_qq_group.jpg" alt="QQ群二维码" class="w-48 h-48 md:w-56 md:h-56 object-contain" />
            <p class="text-center text-sm text-white/70 mt-2">点击放大查看</p>
          </div>
        </div>
    </div>

    <div v-if="showQrModal" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" @click="showQrModal = false">
      <div class="bg-white rounded-2xl p-6 max-w-md w-full" @click.stop>
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-bold text-gray-800">QQ群二维码</h3>
          <button @click="showQrModal = false" class="p-2 hover:bg-gray-100 rounded-full transition-colors">
            <X class="w-6 h-6 text-gray-500" />
          </button>
        </div>
        <div class="flex justify-center">
          <img src="/qrcode_qq_group.jpg" alt="QQ群二维码" class="w-64 h-64 object-contain" />
        </div>
        <p class="text-center text-gray-600 mt-4">群号：1038534078</p>
        <p class="text-center text-gray-400 text-sm mt-2">保存图片或截屏后在QQ中扫描</p>
      </div>
    </div>
  </div>
</template>