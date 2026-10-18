<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Search, Download, Calendar } from 'lucide-vue-next'
import axios from 'axios'
import { Filesystem, Directory } from '@capacitor/filesystem'
import { Share } from '@capacitor/share'
import { Capacitor } from '@capacitor/core'

type LotteryType = 'double_color_ball' | 'super_lotto' | 'lottery_3d' | 'happy_8' | 'arrangement_3' | 'arrangement_5' | 'seven_star' | 'seven_color'

const currentLottery = ref<LotteryType>('double_color_ball')
const searchQuery = ref('')
const currentPage = ref(1)
const totalPages = ref(1)
const dataList = ref<any[]>([])

const lotteryLabels: Record<string, string> = {
  double_color_ball: '双色球',
  super_lotto: '大乐透',
  lottery_3d: '福彩3D',
  happy_8: '快乐8',
  arrangement_3: '排列3',
  arrangement_5: '排列5',
  seven_star: '七星彩',
  seven_color: '七乐彩'
}

const lotteryConfig: Record<string, { numberFields: string[]; numberTypes: string[]; colorClasses: string[] }> = {
  double_color_ball: { numberFields: ['red_numbers', 'blue_number'], numberTypes: ['红球', '蓝球'], colorClasses: ['bg-red-500', 'bg-blue-500'] },
  super_lotto: { numberFields: ['front_numbers', 'back_numbers'], numberTypes: ['前区', '后区'], colorClasses: ['bg-green-500', 'bg-blue-500'] },
  lottery_3d: { numberFields: ['numbers'], numberTypes: [''], colorClasses: ['bg-purple-500'] },
  happy_8: { numberFields: ['numbers'], numberTypes: [''], colorClasses: ['bg-orange-500'] },
  arrangement_3: { numberFields: ['numbers'], numberTypes: [''], colorClasses: ['bg-indigo-500'] },
  arrangement_5: { numberFields: ['numbers'], numberTypes: [''], colorClasses: ['bg-cyan-500'] },
  seven_star: { numberFields: ['numbers'], numberTypes: [''], colorClasses: ['bg-teal-500'] },
  seven_color: { numberFields: ['basic_numbers', 'special_number'], numberTypes: ['基本号', '特别号'], colorClasses: ['bg-pink-500', 'bg-yellow-500'] }
}

const loadData = async () => {
  try {
    const endpointMap: Record<string, string> = {
      double_color_ball: '/api/lottery/double-color-ball',
      super_lotto: '/api/lottery/super-lotto',
      lottery_3d: '/api/lottery/lottery-3d',
      happy_8: '/api/lottery/happy-8',
      arrangement_3: '/api/lottery/arrangement-3',
      arrangement_5: '/api/lottery/arrangement-5',
      seven_star: '/api/lottery/seven-star',
      seven_color: '/api/lottery/seven-color'
    }
    
    const response = await axios.get(endpointMap[currentLottery.value], {
      params: { page: currentPage.value, limit: 20 }
    })

    dataList.value = response.data.data
    totalPages.value = Math.ceil(response.data.total / 20)
  } catch (error) {
    console.error('Failed to load data:', error)
  }
}

const filteredData = computed(() => {
  if (!searchQuery.value) return dataList.value
  return dataList.value.filter(item => 
    item.id.includes(searchQuery.value) ||
    item.date.includes(searchQuery.value)
  )
})

const downloadData = async () => {
  try {
    const config = lotteryConfig[currentLottery.value]
    const fileName = `${lotteryLabels[currentLottery.value]}_data.csv`
    const csvContent = dataList.value.map(item => {
      const values = config.numberFields.map(field => {
        const val = item[field]
        return Array.isArray(val) ? val.join(' ') : val
      })
      return `${item.id},${item.date},${values.join(',')}`
    }).join('\n')

    if (Capacitor.isNativePlatform()) {
      // 写入临时文件
      const result = await Filesystem.writeFile({
        path: fileName,
        data: csvContent,
        directory: Directory.Cache,
        encoding: 'utf8' as any
      });

      // 调用原生分享面板
      await Share.share({
        title: '导出彩票数据',
        text: `LuckyDD - ${lotteryLabels[currentLottery.value]}历史数据`,
        url: result.uri,
      });
    } else {
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = fileName
      link.click()
    }
  } catch (error: any) {
    console.error('Export error:', error);
    alert('导出失败: ' + (error.message || '未知错误'));
  }
}

watch(currentLottery, () => {
  currentPage.value = 1
  loadData()
})

watch(currentPage, loadData)

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div class="flex flex-wrap items-center gap-2">
        <button
          v-for="(label, key) in lotteryLabels"
          :key="key"
          @click="currentLottery = key as LotteryType"
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

      <div class="flex items-center space-x-4">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索期号或日期..."
            class="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <button
          @click="downloadData"
          class="flex items-center space-x-2 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
        >
          <Download class="w-5 h-5" />
          <span>导出CSV</span>
        </button>
      </div>
    </div>

    <div class="bg-white rounded-xl shadow-md overflow-hidden">
      <table class="w-full">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-sm font-semibold text-gray-600">期号</th>
            <th class="px-4 py-3 text-left text-sm font-semibold text-gray-600">
              <div class="flex items-center space-x-1">
                <Calendar class="w-4 h-4" />
                <span>日期</span>
              </div>
            </th>
            <th class="px-4 py-3 text-left text-sm font-semibold text-gray-600">开奖号码</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="item in filteredData"
            :key="item.id"
            class="border-t hover:bg-gray-50 transition-colors"
          >
            <td class="px-4 py-4 text-sm font-medium text-gray-800">{{ item.id }}</td>
            <td class="px-4 py-4 text-sm text-gray-500">{{ item.date }}</td>
            <td class="px-4 py-4">
              <div class="flex flex-wrap gap-2">
                <template v-if="currentLottery === 'double_color_ball'">
                  <div
                    v-for="(num, index) in item.red_numbers"
                    :key="index"
                    class="w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center text-sm font-bold"
                  >
                    {{ num }}
                  </div>
                  <div class="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {{ item.blue_number }}
                  </div>
                </template>

                <template v-else-if="currentLottery === 'super_lotto'">
                  <div
                    v-for="(num, index) in item.front_numbers"
                    :key="index"
                    class="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-bold"
                  >
                    {{ num }}
                  </div>
                  <div
                    v-for="(num, index) in item.back_numbers"
                    :key="'back-' + index"
                    class="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold"
                  >
                    {{ num }}
                  </div>
                </template>

                <template v-else-if="currentLottery === 'seven_color'">
                  <div
                    v-for="(num, index) in item.basic_numbers"
                    :key="index"
                    class="w-8 h-8 bg-pink-500 text-white rounded-full flex items-center justify-center text-sm font-bold"
                  >
                    {{ num }}
                  </div>
                  <div class="w-8 h-8 bg-yellow-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {{ item.special_number }}
                  </div>
                </template>

                <template v-else>
                  <div
                    v-for="(num, index) in item.numbers"
                    :key="index"
                    :class="[
                      'w-8 h-8 text-white rounded-full flex items-center justify-center text-sm font-bold',
                      currentLottery === 'lottery_3d' ? 'bg-purple-500' :
                      currentLottery === 'happy_8' ? 'bg-orange-500' :
                      currentLottery === 'arrangement_3' ? 'bg-indigo-500' :
                      currentLottery === 'arrangement_5' ? 'bg-cyan-500' :
                      'bg-teal-500'
                    ]"
                  >
                    {{ num }}
                  </div>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredData.length === 0" class="text-center py-12 text-gray-400">
        <p>暂无数据</p>
      </div>
    </div>

    <div class="flex items-center justify-center space-x-2">
      <button
        @click="currentPage = Math.max(1, currentPage - 1)"
        :disabled="currentPage === 1"
        class="px-4 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        上一页
      </button>
      
      <span class="px-4 py-2 text-gray-600">
        第 {{ currentPage }} / {{ totalPages }} 页
      </span>
      
      <button
        @click="currentPage = Math.min(totalPages, currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="px-4 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        下一页
      </button>
    </div>
  </div>
</template>