<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Sparkles, RefreshCw, Copy, Check, Settings, Sliders } from 'lucide-vue-next';
import axios from 'axios';

type LotteryType = 'double_color_ball' | 'super_lotto' | 'lottery_3d' | 'happy_8' | 'arrangement_3' | 'arrangement_5' | 'seven_star' | 'seven_color';

const currentLottery = ref<LotteryType>('double_color_ball');
const recommendations = ref<any[]>([]);
const isLoading = ref(false);
const copiedIndex = ref<number | null>(null);
const showConfigPanel = ref(false);

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

const weights = ref({
  hotNumbers: 30,
  coldNumbers: 20,
  missingNumbers: 30,
  consecutiveNumbers: 10,
  repeatNumbers: 10
});

const loadRecommendations = async (customWeights?: typeof weights.value) => {
  isLoading.value = true;
  try {
    const endpointMap: Record<string, string> = {
      double_color_ball: '/api/analysis/recommendations/double-color-ball',
      super_lotto: '/api/analysis/recommendations/super-lotto',
      lottery_3d: '/api/analysis/recommendations/lottery-3d',
      happy_8: '/api/analysis/recommendations/happy-8',
      arrangement_3: '/api/analysis/recommendations/arrangement-3',
      arrangement_5: '/api/analysis/recommendations/arrangement-5',
      seven_star: '/api/analysis/recommendations/seven-star',
      seven_color: '/api/analysis/recommendations/seven-color'
    };
    
    const params = customWeights ? { weights: JSON.stringify(customWeights) } : {};
    const response = await axios.get(endpointMap[currentLottery.value], { params });
    recommendations.value = response.data;
  }
  catch (error) {
    console.error('Failed to load recommendations:', error);
  }
  finally {
    isLoading.value = false;
  }
};

const copyToClipboard = async (index: number, rec: any) => {
  let text = '';
  if (currentLottery.value === 'double_color_ball') {
    text = `红球: ${rec.redNumbers.join(' ')} 蓝球: ${rec.blueNumber}`;
  }
  else if (currentLottery.value === 'super_lotto') {
    text = `前区: ${rec.frontNumbers.join(' ')} 后区: ${rec.backNumbers.join(' ')}`;
  }
  else if (currentLottery.value === 'seven_color') {
    text = `基本号: ${rec.basicNumbers.join(' ')} 特别号: ${rec.specialNumber}`;
  }
  else {
    text = `号码: ${rec.numbers?.join(' ') || rec.frontNumbers?.join(' ') || ''}`;
  }
  await navigator.clipboard.writeText(text);
  copiedIndex.value = index;
  setTimeout(() => {
    copiedIndex.value = null;
  }, 2000);
};

const getScoreColor = (score: number) => {
  if (score >= 80)
    return 'text-green-500';
  if (score >= 60)
    return 'text-yellow-500';
  return 'text-gray-500';
};

const getScoreBarColor = (score: number) => {
  if (score >= 80)
    return 'bg-green-500';
  if (score >= 60)
    return 'bg-yellow-500';
  return 'bg-gray-500';
};

const applyCustomWeights = () => {
  const total = weights.value.hotNumbers + weights.value.coldNumbers + weights.value.missingNumbers + weights.value.consecutiveNumbers + weights.value.repeatNumbers;
  if (total !== 100) {
    alert('权重总和必须为100');
    return;
  }
  loadRecommendations(weights.value);
  showConfigPanel.value = false;
};

const resetWeights = () => {
  weights.value = {
    hotNumbers: 30,
    coldNumbers: 20,
    missingNumbers: 30,
    consecutiveNumbers: 10,
    repeatNumbers: 10
  };
};

onMounted(() => {
  loadRecommendations();
});
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex flex-wrap items-center gap-2">
        <button
          v-for="(label, key) in lotteryLabels"
          :key="key"
          @click="currentLottery = key as LotteryType; loadRecommendations()"
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

      <div class="flex items-center gap-2">
        <button
          @click="showConfigPanel = !showConfigPanel"
          class="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg hover:bg-gray-200 transition-colors"
        >
          <Sliders class="w-5 h-5" />
          <span>策略配置</span>
        </button>
        <button
          @click="loadRecommendations()"
          :disabled="isLoading"
          class="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
        >
          <RefreshCw class="w-5 h-5" :class="{ 'animate-spin': isLoading }" />
          <span>刷新推荐</span>
        </button>
      </div>
    </div>

    <div v-if="showConfigPanel" class="bg-white rounded-xl shadow-md p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-800 flex items-center space-x-2">
          <Settings class="w-5 h-5 text-blue-500" />
          <span>自定义策略权重</span>
        </h3>
        <button @click="resetWeights" class="text-sm text-gray-500 hover:text-gray-700">重置默认</button>
      </div>
      
      <div class="space-y-4">
        <div>
          <div class="flex justify-between mb-2">
            <label class="text-sm font-medium text-gray-700">热门号码权重</label>
            <span class="text-sm text-gray-500">{{ weights.hotNumbers }}%</span>
          </div>
          <input type="range" v-model.number="weights.hotNumbers" min="0" max="100" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
        </div>
        
        <div>
          <div class="flex justify-between mb-2">
            <label class="text-sm font-medium text-gray-700">冷门号码权重</label>
            <span class="text-sm text-gray-500">{{ weights.coldNumbers }}%</span>
          </div>
          <input type="range" v-model.number="weights.coldNumbers" min="0" max="100" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
        </div>
        
        <div>
          <div class="flex justify-between mb-2">
            <label class="text-sm font-medium text-gray-700">遗漏号码权重</label>
            <span class="text-sm text-gray-500">{{ weights.missingNumbers }}%</span>
          </div>
          <input type="range" v-model.number="weights.missingNumbers" min="0" max="100" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
        </div>
        
        <div>
          <div class="flex justify-between mb-2">
            <label class="text-sm font-medium text-gray-700">连号偏好权重</label>
            <span class="text-sm text-gray-500">{{ weights.consecutiveNumbers }}%</span>
          </div>
          <input type="range" v-model.number="weights.consecutiveNumbers" min="0" max="100" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
        </div>
        
        <div>
          <div class="flex justify-between mb-2">
            <label class="text-sm font-medium text-gray-700">重复号偏好权重</label>
            <span class="text-sm text-gray-500">{{ weights.repeatNumbers }}%</span>
          </div>
          <input type="range" v-model.number="weights.repeatNumbers" min="0" max="100" class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer">
        </div>
        
        <div class="pt-4 border-t border-gray-200">
          <div class="flex justify-between mb-4">
            <span class="text-sm font-medium text-gray-700">权重总和</span>
            <span :class="['text-sm font-semibold', (weights.hotNumbers + weights.coldNumbers + weights.missingNumbers + weights.consecutiveNumbers + weights.repeatNumbers) === 100 ? 'text-green-500' : 'text-red-500']">
              {{ weights.hotNumbers + weights.coldNumbers + weights.missingNumbers + weights.consecutiveNumbers + weights.repeatNumbers }}%
            </span>
          </div>
          <button
            @click="applyCustomWeights"
            class="w-full py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            应用自定义权重
          </button>
        </div>
      </div>
    </div>

    <div class="bg-gradient-to-r from-red-500 to-blue-600 rounded-xl p-6 text-white">
      <div class="flex items-center space-x-3 mb-3">
        <Sparkles class="w-6 h-6" />
        <h2 class="text-xl font-bold">智能推荐</h2>
      </div>
      <p class="text-white/80">基于统计特征和模式挖掘算法生成的推荐号码</p>
      <p class="text-white/60 text-sm mt-2">⚠️ 仅供娱乐研究，不构成投注建议</p>
    </div>

    <div v-if="recommendations.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div
        v-for="(rec, index) in recommendations"
        :key="rec.id"
        class="bg-white rounded-xl shadow-md overflow-hidden"
      >
        <div class="p-6">
          <div class="flex items-center justify-between mb-4">
            <span class="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
              {{ rec.strategy }}
            </span>
            <div class="flex items-center space-x-2">
              <span class="text-sm text-gray-500">评分</span>
              <span :class="['text-xl font-bold', getScoreColor(rec.score)]">
                {{ rec.score }}
              </span>
            </div>
          </div>

          <div class="flex flex-wrap gap-2 mb-4">
            <template v-if="currentLottery === 'double_color_ball'">
              <div
                v-for="(num, numIndex) in rec.redNumbers"
                :key="numIndex"
                class="w-12 h-12 bg-red-500 text-white rounded-full flex items-center justify-center text-lg font-bold shadow-lg"
              >
                {{ num }}
              </div>
              <div class="flex items-center justify-center">
                <span class="mx-2 text-gray-400">+</span>
              </div>
              <div class="w-12 h-12 bg-blue-500 text-white rounded-full flex items-center justify-center text-lg font-bold shadow-lg">
                {{ rec.blueNumber }}
              </div>
            </template>

            <template v-else-if="currentLottery === 'super_lotto'">
              <div
                v-for="(num, numIndex) in rec.frontNumbers"
                :key="numIndex"
                class="w-10 h-10 bg-green-500 text-white rounded-full flex items-center justify-center font-bold shadow-lg"
              >
                {{ num }}
              </div>
              <div class="flex items-center justify-center">
                <span class="mx-2 text-gray-400">+</span>
              </div>
              <div
                v-for="(num, numIndex) in rec.backNumbers"
                :key="numIndex"
                class="w-10 h-10 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold shadow-lg"
              >
                {{ num }}
              </div>
            </template>
            <template v-else-if="currentLottery === 'seven_color'">
              <div
                v-for="(num, numIndex) in rec.basicNumbers"
                :key="numIndex"
                class="w-10 h-10 bg-purple-500 text-white rounded-full flex items-center justify-center font-bold shadow-lg"
              >
                {{ num }}
              </div>
              <div class="flex items-center justify-center">
                <span class="mx-2 text-gray-400">+</span>
              </div>
              <div class="w-10 h-10 bg-orange-500 text-white rounded-full flex items-center justify-center font-bold shadow-lg">
                {{ rec.specialNumber }}
              </div>
            </template>
            <template v-else>
              <div
                v-for="(num, numIndex) in rec.numbers"
                :key="numIndex"
                class="w-8 h-8 bg-indigo-500 text-white rounded-full flex items-center justify-center font-bold shadow-md"
              >
                {{ num }}
              </div>
            </template>
          </div>

          <div class="mb-4">
            <div class="flex justify-between text-sm text-gray-500 mb-1">
              <span>推荐指数</span>
              <span>{{ rec.score }}%</span>
            </div>
            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                :class="['h-full transition-all duration-500', getScoreBarColor(rec.score)]"
                :style="{ width: `${rec.score}%` }"
              ></div>
            </div>
          </div>

          <p class="text-sm text-gray-600 mb-4">{{ rec.description }}</p>

          <button
            @click="copyToClipboard(index, rec)"
            class="w-full flex items-center justify-center space-x-2 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <Copy v-if="copiedIndex !== index" class="w-5 h-5 text-gray-600" />
            <Check v-else class="w-5 h-5 text-green-500" />
            <span>{{ copiedIndex === index ? '已复制' : '复制号码' }}</span>
          </button>
        </div>
      </div>
    </div>

    <div v-else-if="!isLoading" class="text-center py-12 text-gray-400">
      <p>暂无推荐数据</p>
    </div>

    <div v-if="isLoading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      <p class="mt-4 text-gray-500">正在生成推荐...</p>
    </div>

    <div class="bg-white rounded-xl shadow-md p-6">
      <h3 class="text-lg font-semibold text-gray-800 mb-4">推荐策略说明</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div class="p-4 bg-green-50 rounded-lg">
          <h4 class="font-medium text-green-800 mb-2">智能综合</h4>
          <p class="text-sm text-green-600">融合统计分析与模式挖掘，综合冷热号、遗漏值和区间分布</p>
        </div>
        <div class="p-4 bg-blue-50 rounded-lg">
          <h4 class="font-medium text-blue-800 mb-2">连号策略</h4>
          <p class="text-sm text-blue-600">分析历史连号出现概率，优先选择有连号趋势的组合</p>
        </div>
        <div class="p-4 bg-purple-50 rounded-lg">
          <h4 class="font-medium text-purple-800 mb-2">重复号策略</h4>
          <p class="text-sm text-purple-600">追踪上一期号码重复规律，选择有重复趋势的号码</p>
        </div>
        <div class="p-4 bg-orange-50 rounded-lg">
          <h4 class="font-medium text-orange-800 mb-2">遗漏回补</h4>
          <p class="text-sm text-orange-600">优先选择遗漏期数即将达到平均值的号码</p>
        </div>
        <div class="p-4 bg-yellow-50 rounded-lg">
          <h4 class="font-medium text-yellow-800 mb-2">均衡稳健</h4>
          <p class="text-sm text-yellow-600">冷热号码按比例搭配，追求号码分布均衡</p>
        </div>
        <div class="p-4 bg-gray-50 rounded-lg">
          <h4 class="font-medium text-gray-800 mb-2">随机参考</h4>
          <p class="text-sm text-gray-600">完全随机生成号码，作为对比参考</p>
        </div>
      </div>
    </div>
  </div>
</template>