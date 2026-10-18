<script setup lang="ts">import { ref, onMounted, computed } from 'vue';
import { BarChart3, TrendingUp, PieChart, Activity } from 'lucide-vue-next';
import axios from 'axios';
import { Bar, Doughnut } from 'vue-chartjs';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement);
type LotteryType = 'double_color_ball' | 'super_lotto' | 'lottery_3d' | 'happy_8' | 'arrangement_3' | 'arrangement_5' | 'seven_star' | 'seven_color';
const currentLottery = ref<LotteryType>('double_color_ball');
const statistics = ref<any>(null);
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
const loadStatistics = async () => {
 try {
 const endpointMap: Record<string, string> = {
 double_color_ball: '/api/analysis/statistics/double-color-ball',
 super_lotto: '/api/analysis/statistics/super-lotto',
 lottery_3d: '/api/analysis/statistics/lottery-3d',
 happy_8: '/api/analysis/statistics/happy-8',
 arrangement_3: '/api/analysis/statistics/arrangement-3',
 arrangement_5: '/api/analysis/statistics/arrangement-5',
 seven_star: '/api/analysis/statistics/seven-star',
 seven_color: '/api/analysis/statistics/seven-color'
 };
 const response = await axios.get(endpointMap[currentLottery.value]);
 statistics.value = response.data;
 }
 catch (error) {
 console.error('Failed to load statistics:', error);
 }
};
const hotNumbersChartData = computed(() => {
 if (!statistics.value?.hotNumbers)
 return { labels: [], datasets: [] };
 return {
 labels: statistics.value.hotNumbers.map((n: any) => n.number),
 datasets: [{
 label: '出现次数',
 data: statistics.value.hotNumbers.map((n: any) => n.count),
 backgroundColor: 'rgba(239, 68, 68, 0.8)',
 borderRadius: 8
 }]
 };
});
const coldNumbersChartData = computed(() => {
 if (!statistics.value?.coldNumbers)
 return { labels: [], datasets: [] };
 return {
 labels: statistics.value.coldNumbers.map((n: any) => n.number),
 datasets: [{
 label: '出现次数',
 data: statistics.value.coldNumbers.map((n: any) => n.count),
 backgroundColor: 'rgba(59, 130, 246, 0.8)',
 borderRadius: 8
 }]
 };
});
const parityChartData = computed(() => {
 if (!statistics.value?.parityAnalysis)
 return { labels: [], datasets: [] };
 return {
 labels: ['奇数', '偶数'],
 datasets: [{
 data: [
 statistics.value.parityAnalysis.oddRate * 100,
 statistics.value.parityAnalysis.evenRate * 100
 ],
 backgroundColor: ['rgba(239, 68, 68, 0.8)', 'rgba(59, 130, 246, 0.8)']
 }]
 };
});
const chartOptions = {
 responsive: true,
 maintainAspectRatio: false,
 plugins: {
 legend: {
 display: false
 }
 }
};
const doughnutOptions = {
 responsive: true,
 maintainAspectRatio: false,
 plugins: {
 legend: {
 position: 'bottom' as const
 }
 }
};
onMounted(() => {
 loadStatistics();
});
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center gap-2">
      <button
        v-for="(label, key) in lotteryLabels"
        :key="key"
        @click="currentLottery = key as LotteryType; loadStatistics()"
        :class="[
          'px-4 py-2 rounded-lg font-medium transition-colors',
          currentLottery === key
            ? 'bg-gradient-to-r from-red-500 to-blue-600 text-white'
            : 'bg-white text-gray-600 hover:bg-gray-100'
        ]"
      >
        {{ label }}
      </button>
    </div>

    <div v-if="statistics" class="space-y-6">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded-xl shadow-md p-6">
          <div class="flex items-center space-x-3">
            <div class="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
              <TrendingUp class="w-6 h-6 text-red-500" />
            </div>
            <div>
              <p class="text-sm text-gray-500">最热号码</p>
              <p class="text-2xl font-bold text-red-500">
                {{ statistics.hotNumbers[0]?.number || '-' }}
              </p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-md p-6">
          <div class="flex items-center space-x-3">
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <TrendingUp class="w-6 h-6 text-blue-500" />
            </div>
            <div>
              <p class="text-sm text-gray-500">最冷号码</p>
              <p class="text-2xl font-bold text-blue-500">
                {{ statistics.coldNumbers[0]?.number || '-' }}
              </p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-md p-6">
          <div class="flex items-center space-x-3">
            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <Activity class="w-6 h-6 text-green-500" />
            </div>
            <div>
              <p class="text-sm text-gray-500">平均和值</p>
              <p class="text-2xl font-bold text-green-500">
                {{ statistics.sumAnalysis?.avg?.toFixed(1) || '-' }}
              </p>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-md p-6">
          <div class="flex items-center space-x-3">
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <PieChart class="w-6 h-6 text-purple-500" />
            </div>
            <div>
              <p class="text-sm text-gray-500">最大遗漏</p>
              <p class="text-2xl font-bold text-purple-500">
                {{ statistics.missingNumbers[0]?.missingDays || '-' }}期
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-white rounded-xl shadow-md p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4 flex items-center space-x-2">
            <BarChart3 class="w-5 h-5 text-red-500" />
            <span>热门号码</span>
          </h3>
          <div class="h-64">
            <Bar :data="hotNumbersChartData" :options="chartOptions" />
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-md p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4 flex items-center space-x-2">
            <BarChart3 class="w-5 h-5 text-blue-500" />
            <span>冷门号码</span>
          </h3>
          <div class="h-64">
            <Bar :data="coldNumbersChartData" :options="chartOptions" />
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="bg-white rounded-xl shadow-md p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4 flex items-center space-x-2">
            <PieChart class="w-5 h-5 text-gray-500" />
            <span>奇偶比例</span>
          </h3>
          <div class="h-64">
            <Doughnut :data="parityChartData" :options="doughnutOptions" />
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-md p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">和值分析</h3>
          <div class="space-y-4">
            <div class="flex justify-between items-center">
              <span class="text-gray-600">最小值</span>
              <span class="text-xl font-bold text-blue-500">{{ statistics.sumAnalysis?.min }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-600">最大值</span>
              <span class="text-xl font-bold text-red-500">{{ statistics.sumAnalysis?.max }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-600">平均值</span>
              <span class="text-xl font-bold text-green-500">{{ statistics.sumAnalysis?.avg?.toFixed(1) }}</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-600">标准差</span>
              <span class="text-xl font-bold text-purple-500">{{ statistics.sumAnalysis?.std?.toFixed(1) }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-md p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">遗漏号码TOP10</h3>
          <div class="space-y-2">
            <div
              v-for="(item, index) in statistics.missingNumbers.slice(0, 10)"
              :key="index"
              class="flex items-center space-x-3"
            >
              <div class="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                {{ item.number }}
              </div>
              <div class="flex-1">
                <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-purple-500 transition-all"
                    :style="{ width: `${Math.min(item.missingDays * 5, 100)}%` }"
                  ></div>
                </div>
              </div>
              <span class="text-sm text-gray-500 w-12 text-right">{{ item.missingDays }}期</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="statistics.intervalAnalysis" class="bg-white rounded-xl shadow-md p-6">
        <h3 class="text-lg font-semibold text-gray-800 mb-4">区间分布</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            v-for="interval in statistics.intervalAnalysis"
            :key="interval.interval"
            class="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4"
          >
            <div class="flex justify-between items-center mb-2">
              <span class="font-medium text-gray-700">{{ interval.interval }}</span>
              <span class="text-sm text-gray-500">{{ interval.start }}-{{ interval.end }}</span>
            </div>
            <div class="flex items-end space-x-2">
              <span class="text-2xl font-bold text-blue-500">{{ interval.count }}</span>
              <span class="text-sm text-gray-500 mb-1">次 ({{ (interval.rate * 100).toFixed(1) }}%)</span>
            </div>
            <div class="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                class="h-full bg-blue-500 transition-all"
                :style="{ width: `${interval.rate * 100}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="statistics.positionAnalysis" class="bg-white rounded-xl shadow-md p-6">
        <h3 class="text-lg font-semibold text-gray-800 mb-4">位置分析</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div
            v-for="pos in statistics.positionAnalysis"
            :key="pos.position"
            class="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4"
          >
            <h4 class="font-medium text-gray-700 mb-3">第{{ pos.position }}位</h4>
            <div class="space-y-3">
              <div>
                <p class="text-xs text-gray-500 mb-1">热号</p>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="num in pos.hotNumbers"
                    :key="num.number"
                    class="w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center text-sm font-bold"
                  >
                    {{ num.number }}
                  </span>
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1">冷号</p>
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="num in pos.coldNumbers"
                    :key="num.number"
                    class="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold"
                  >
                    {{ num.number }}
                  </span>
                </div>
              </div>
              <div>
                <p class="text-xs text-gray-500 mb-1">遗漏TOP3</p>
                <div class="space-y-1">
                  <div
                    v-for="item in pos.missingNumbers.slice(0, 3)"
                    :key="item.number"
                    class="flex items-center justify-between text-sm"
                  >
                    <span class="text-gray-600">{{ item.number }}</span>
                    <span class="text-purple-500">{{ item.missingDays }}期</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="statistics.secondaryAnalysis" class="bg-white rounded-xl shadow-md p-6">
        <h3 class="text-lg font-semibold text-gray-800 mb-4">
          {{ currentLottery === 'double_color_ball' ? '蓝球' : currentLottery === 'super_lotto' ? '后区' : '特别号' }}分析
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
            <h4 class="font-medium text-gray-700 mb-3">热号</h4>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="num in statistics.secondaryAnalysis.hotNumbers"
                :key="num.number"
                class="w-10 h-10 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold"
              >
                {{ num.number }}
              </span>
            </div>
          </div>
          <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
            <h4 class="font-medium text-gray-700 mb-3">冷号</h4>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="num in statistics.secondaryAnalysis.coldNumbers"
                :key="num.number"
                class="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-bold"
              >
                {{ num.number }}
              </span>
            </div>
          </div>
          <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
            <h4 class="font-medium text-gray-700 mb-3">遗漏TOP5</h4>
            <div class="space-y-2">
              <div
                v-for="item in statistics.secondaryAnalysis.missingNumbers.slice(0, 5)"
                :key="item.number"
                class="flex items-center space-x-2"
              >
                <span class="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  {{ item.number }}
                </span>
                <span class="text-sm text-gray-600">{{ item.missingDays }}期未出</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-12 text-gray-400">
      <p>加载中...</p>
    </div>
  </div>
</template>