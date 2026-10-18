import { getAll } from '../database'

export interface AnomalyResult {
  period: string
  date: string
  numbers: number[]
  anomalyScore: number
  anomalyType: string
  description: string
}

export const detectOutlierSums = (data: { id: string; date: string; numbers: number[] }[], threshold: number = 2): AnomalyResult[] => {
  const sums = data.map(d => d.numbers.reduce((a, b) => a + b, 0))
  const avg = sums.reduce((a, b) => a + b, 0) / sums.length
  const variance = sums.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / sums.length
  const std = Math.sqrt(variance)

  return data
    .map((d, i) => {
      const sum = sums[i]
      const zScore = Math.abs((sum - avg) / std)
      return {
        period: d.id,
        date: d.date,
        numbers: d.numbers,
        anomalyScore: zScore,
        anomalyType: zScore > threshold ? '和值异常' : '正常',
        description: zScore > threshold ? `和值${sum}偏离均值${avg.toFixed(2)}达${zScore.toFixed(2)}个标准差` : ''
      }
    })
    .filter(a => a.anomalyType !== '正常')
    .sort((a, b) => b.anomalyScore - a.anomalyScore)
}

export const detectRepeatedNumbers = (data: { id: string; date: string; numbers: number[] }[]): AnomalyResult[] => {
  const results: AnomalyResult[] = []

  for (let i = 1; i < data.length; i++) {
    const current = data[i].numbers
    const previous = data[i - 1].numbers
    
    const repeated = current.filter(n => previous.includes(n)).length
    
    if (repeated >= 4) {
      results.push({
        period: data[i].id,
        date: data[i].date,
        numbers: current,
        anomalyScore: repeated,
        anomalyType: '重复号码异常',
        description: `与上期重复${repeated}个号码`
      })
    }
  }

  return results.sort((a, b) => b.anomalyScore - a.anomalyScore)
}

export const detectPatternAnomalies = (data: { id: string; date: string; numbers: number[] }[]): AnomalyResult[] => {
  const results: AnomalyResult[] = []

  data.forEach(d => {
    const sorted = [...d.numbers].sort((a, b) => a - b)
    
    const consecutiveCount = sorted.reduce((count, num, i) => {
      if (i > 0 && num === sorted[i - 1] + 1) return count + 1
      return count
    }, 0)

    if (consecutiveCount >= 4) {
      results.push({
        period: d.id,
        date: d.date,
        numbers: d.numbers,
        anomalyScore: consecutiveCount,
        anomalyType: '连号异常',
        description: `出现${consecutiveCount + 1}个连续号码: ${sorted.join(', ')}`
      })
    }
  })

  return results.sort((a, b) => b.anomalyScore - a.anomalyScore)
}

export const getAnomalies = (table: string, numberField: string): AnomalyResult[] => {
  const rows = getAll(table as any).sort((a, b) => a.date.localeCompare(b.date))
  const data = rows.map(row => ({
    id: row.id,
    date: row.date,
    numbers: row[numberField]
  }))

  const outlierResults = detectOutlierSums(data)
  const repeatedResults = detectRepeatedNumbers(data)
  const patternResults = detectPatternAnomalies(data)

  const allResults = [...outlierResults, ...repeatedResults, ...patternResults]
    .sort((a, b) => b.anomalyScore - a.anomalyScore)
    .slice(0, 20)

  return allResults
}

export const getDoubleColorBallAnomalies = (): AnomalyResult[] => {
  return getAnomalies('double_color_ball', 'red_numbers')
}

export const getSuperLottoAnomalies = (): AnomalyResult[] => {
  return getAnomalies('super_lotto', 'front_numbers')
}

export const getLottery3DAnomalies = (): AnomalyResult[] => {
  return getAnomalies('lottery_3d', 'numbers')
}

export const getHappy8Anomalies = (): AnomalyResult[] => {
  return getAnomalies('happy_8', 'numbers')
}

export const getArrangement3Anomalies = (): AnomalyResult[] => {
  return getAnomalies('arrangement_3', 'numbers')
}

export const getArrangement5Anomalies = (): AnomalyResult[] => {
  return getAnomalies('arrangement_5', 'numbers')
}

export const getSevenStarAnomalies = (): AnomalyResult[] => {
  return getAnomalies('seven_star', 'numbers')
}

export const getSevenColorAnomalies = (): AnomalyResult[] => {
  return getAnomalies('seven_color', 'basic_numbers')
}