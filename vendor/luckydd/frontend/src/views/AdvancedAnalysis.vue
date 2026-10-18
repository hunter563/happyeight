<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import { TrendingUp, Grid3x3, Maximize2, Minimize2 } from 'lucide-vue-next';
import axios from 'axios';
import { Line } from 'vue-chartjs';
import { ScreenOrientation } from '@capacitor/screen-orientation';
import { Capacitor } from '@capacitor/core';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  LineController
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, LineController);

type LotteryType = 'double_color_ball' | 'super_lotto' | 'lottery_3d' | 'happy_8' | 'arrangement_3' | 'arrangement_5' | 'seven_star' | 'seven_color';

const currentLottery = ref<LotteryType>('double_color_ball');
const trendsData = ref<any>(null);
const heatmapData = ref<any>(null);
const selectedNumbers = ref<number[]>([]);
const limit = ref(50);
const chartKey = ref(0);
const isLandscape = ref(false);

const toggleOrientation = async () => {
  if (!Capacitor.isNativePlatform()) {
    isLandscape.value = !isLandscape.value;
    nextTick(() => chartKey.value++);
    return;
  }

  try {
    if (isLandscape.value) {
      await ScreenOrientation.unlock();
      await ScreenOrientation.lock({ orientation: 'portrait' });
    } else {
      await ScreenOrientation.lock({ orientation: 'landscape' });
    }
    const current = await ScreenOrientation.orientation();
    isLandscape.value = current.type.includes('landscape');
    chartKey.value++;
  } catch (e) {
    console.error('Failed to change orientation', e);
    // Fallback for emulator issues
    isLandscape.value = !isLandscape.value;
    chartKey.value++;
  }
};

let orientationListener: any = null;

onMounted(async () => {
  loadTrends();
  loadHeatmap();

  if (Capacitor.isNativePlatform()) {
    try {
      const current = await ScreenOrientation.orientation();
      isLandscape.value = current.type.includes('landscape');

      orientationListener = await ScreenOrientation.addListener('screenOrientationChange', (orientation) => {
        isLandscape.value = orientation.type.includes('landscape');
        chartKey.value++;
      });
    } catch (err) {
      console.error('Orientation plugin initialization error:', err);
    }
  }
});

onUnmounted(async () => {
  if (Capacitor.isNativePlatform()) {
    if (orientationListener) {
      orientationListener.remove();
    }
    try {
      await ScreenOrientation.unlock();
    } catch (err) {}
  }
});

const lotteryLabels: Record<string, string> = {
  double_color_ball: '双色球',
  super_lotto: '大乐透',
  lottery_3d: '福彩3D',
  happy_8: '快乐8',
  arrangement_3: '排列3',
  arrangement_5: '排列5',
  seven_star: '七星彩',
  seven_color: '七乐彩'
};

const loadTrends = async () => {
  try {
    const response = await axios.get(`/api/advanced/trends/${currentLottery.value}?limit=${limit.value}`);
    trendsData.value = response.data;
    selectedNumbers.value = [];
    chartKey.value++;
  } catch (error) {
    console.error('Failed to load trends:', error);
  }
};

const loadHeatmap = async () => {
  try {
    const response = await axios.get(`/api/advanced/heatmap/${currentLottery.value}`);
    heatmapData.value = response.data;
  } catch (error) {
    console.error('Failed to load heatmap:', error);
  }
};

const toggleNumber = (num: number) => {
  const index = selectedNumbers.value.indexOf(num);
  if (index >= 0) {
    selectedNumbers.value = selectedNumbers.value.filter(n => n !== num);
  } else if (selectedNumbers.value.length < 5) {
    selectedNumbers.value = [...selectedNumbers.value, num].sort((a, b) => a - b);
  }
  chartKey.value++;
};

watch(selectedNumbers, () => {
  chartKey.value++;
});

const trendChartData = computed(() => {
  if (!trendsData.value || selectedNumbers.value.length === 0) {
    return { labels: [], datasets: [] };
  }
  
  const { issues, trends, startNumber } = trendsData.value;
  const datasets: any[] = [];
  const colors = [
    'rgb(239, 68, 68)', 'rgb(59, 130, 246)', 'rgb(16, 185, 129)', 'rgb(245, 158, 11)', 'rgb(139, 92, 246)'
  ];
  
  selectedNumbers.value.forEach((num, index) => {
    const numIndex = num - startNumber;
    if (trends[numIndex]) {
      datasets.push({
        label: `号码 ${num}`,
        data: trends[numIndex],
        borderColor: colors[index % colors.length],
        backgroundColor: `${colors[index % colors.length]}20`,
        tension: 0,
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: false
      });
    }
  });
  
  return { labels: issues, datasets };
});

const chartOptions: any = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index' as const,
    intersect: false,
  },
  plugins: {
    legend: {
      position: 'top' as const,
      labels: {
        usePointStyle: true,
        padding: 20
      }
    },
    tooltip: {
      callbacks: {
        label: (context: any) => {
          const value = context.parsed.y;
          return `${context.dataset.label}: ${value === 1 ? '开出' : '未开'}`;
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      max: 1.2,
      min: -0.2,
      ticks: {
        stepSize: 1,
        callback: (value: any) => {
          if (value === 1) return '开出'
          if (value === 0) return '未开'
          return ''
        }
      },
      grid: {
        drawBorder: false
      }
    },
    x: {
      ticks: {
        maxRotation: 45,
        minRotation: 45,
        maxTicksLimit: 20,
        font: {
          size: 10
        }
      },
      grid: {
        display: false
      }
    }
  }
};
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
    <div class="max-w-7xl mx-auto">
      <h1 class="text-3xl font-bold text-gray-800 mb-6">高级分析</h1>
      
      <div class="bg-white rounded-xl shadow-md p-6 mb-6">
        <div class="flex flex-wrap gap-4 items-center mb-4">
          <select
            v-model="currentLottery"
            @change="loadTrends(); loadHeatmap()"
            class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option v-for="(label, type) in lotteryLabels" :key="type" :value="type">{{ label }}</option>
          </select>
          
          <select
            v-model="limit"
            @change="loadTrends()"
            class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option :value="30">近30期</option>
            <option :value="50">近50期</option>
            <option :value="100">近100期</option>
          </select>
        </div>
      </div>
      
      <div v-if="heatmapData" class="bg-white rounded-xl shadow-md p-6 mb-6">
        <h2 class="text-xl font-semibold text-gray-800 mb-4 flex items-center space-x-2">
          <Grid3x3 class="w-5 h-5 text-blue-500" />
          <span>号码热度热力图</span>
        </h2>
        <p class="text-sm text-gray-600 mb-4">显示每个号码的历史出现频率（数据总量：{{ heatmapData.totalDraws }}期，{{ heatmapData.totalCount }}次）</p>
        
        <div class="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 gap-2">
          <div
            v-for="item in heatmapData.heatmap"
            :key="item.number"
            :class="[
              'flex flex-col items-center justify-center py-2 rounded-lg cursor-pointer transition-all active:scale-95',
              selectedNumbers.includes(item.number) ? 'ring-2 ring-blue-500 shadow-md' : 'shadow-sm'
            ]"
            :style="{
              backgroundColor: `rgba(59, 130, 246, ${Math.max(0.1, item.rate * 8)})`,
              color: item.rate > 0.15 ? 'white' : 'gray-800'
            }"
            @click="toggleNumber(item.number)"
          >
            <span class="font-bold text-base">{{ item.number }}</span>
            <span class="text-[9px] opacity-80 leading-tight">{{ (item.rate * 100).toFixed(0) }}%</span>
          </div>
        </div>
        
        <div class="mt-4 text-sm text-gray-600">
          <span class="font-semibold">已选择号码：{{ selectedNumbers.join(', ') || '无' }}</span>
          <span class="ml-4 text-gray-500">(点击号码可选择/取消，最多选择5个)</span>
        </div>
      </div>
      
      <!-- 走势分析图表卡片 -->
      <div
        v-if="trendsData && selectedNumbers.length > 0"
        :class="[
          'bg-white shadow-xl transition-all duration-500 flex flex-col',
          isLandscape ? 'fixed inset-0 z-[999] p-4' : 'rounded-xl p-6 mb-6'
        ]"
      >
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-xl font-semibold text-gray-800 flex items-center space-x-2">
            <TrendingUp class="w-5 h-5 text-green-500" />
            <span>号码走势分析</span>
          </h2>

          <button
            @click="toggleOrientation"
            class="group flex items-center space-x-2 px-5 py-2.5 bg-blue-600 text-white rounded-full shadow-lg active:bg-blue-700 transition-all hover:pr-6"
          >
            <Minimize2 v-if="isLandscape" class="w-5 h-5" />
            <Maximize2 v-else class="w-5 h-5" />
            <span class="font-bold tracking-wide">{{ isLandscape ? '返回竖屏' : '全屏横屏' }}</span>
          </button>
        </div>

        <div :class="['flex-1 relative w-full', isLandscape ? 'h-full' : 'h-80']">
          <Line :key="chartKey" :data="trendChartData" :options="chartOptions" />
        </div>
      </div>
      
      <div v-else class="bg-white rounded-xl shadow-md p-6 text-center text-gray-400">
        <p>请在热力图中选择号码以查看走势分析</p>
      </div>
    </div>
  </div>
</template>
