import { getAll } from '../database'

export interface HotColdNumber {
  number: number
  count: number
  frequency: number
  isHot: boolean
  isCold: boolean
}

export interface PositionAnalysis {
  position: number
  hotNumbers: HotColdNumber[]
  coldNumbers: HotColdNumber[]
  missingNumbers: { number: number; missingDays: number }[]
}

export interface IntervalAnalysis {
  interval: string
  start: number
  end: number
  count: number
  rate: number
}

export interface StatisticalResult {
  hotNumbers: HotColdNumber[]
  coldNumbers: HotColdNumber[]
  missingNumbers: { number: number; missingDays: number }[]
  sumAnalysis: {
    min: number
    max: number
    avg: number
    std: number
  }
  parityAnalysis: {
    oddCount: number
    evenCount: number
    oddRate: number
    evenRate: number
  }
  positionAnalysis?: PositionAnalysis[]
  intervalAnalysis?: IntervalAnalysis[]
  secondaryAnalysis?: {
    hotNumbers: HotColdNumber[]
    coldNumbers: HotColdNumber[]
    missingNumbers: { number: number; missingDays: number }[]
  }
}

export const calculateHotColdNumbers = (data: number[][], totalNumbers: number, startNumber: number = 1): HotColdNumber[] => {
  const countMap: Record<number, number> = {}
  
  data.forEach(row => {
    row.forEach(num => {
      countMap[num] = (countMap[num] || 0) + 1
    })
  })

  const totalDraws = data.length
  const numbersPerDraw = data[0]?.length || 1
  const totalNumberOccurrences = totalDraws * numbersPerDraw
  const avgFrequency = totalNumberOccurrences / totalNumbers

  const sorted = Object.entries(countMap)
    .map(([num, count]) => ({
      number: parseInt(num),
      count,
      frequency: count / totalDraws,
      isHot: false,
      isCold: false
    }))
    .sort((a, b) => b.count - a.count)

  const hotCount = Math.min(Math.max(3, Math.ceil(totalNumbers * 0.3)), Math.ceil(sorted.length * 0.3))
  const coldCount = Math.min(Math.max(3, Math.ceil(totalNumbers * 0.3)), Math.ceil(sorted.length * 0.3))

  for (let i = 0; i < hotCount; i++) {
    sorted[i].isHot = true
  }
  for (let i = sorted.length - coldCount; i < sorted.length; i++) {
    sorted[i].isCold = true
  }

  return sorted
}

export const calculateMissingNumbers = (data: number[][], totalNumbers: number, startNumber: number = 1): { number: number; missingDays: number }[] => {
  const lastOccurrence: Record<number, number> = {}
  const result: { number: number; missingDays: number }[] = []

  data.forEach((row, index) => {
    row.forEach(num => {
      lastOccurrence[num] = index
    })
  })

  for (let i = startNumber; i < startNumber + totalNumbers; i++) {
    const lastIndex = lastOccurrence[i] ?? data.length
    result.push({
      number: i,
      missingDays: data.length - lastIndex
    })
  }

  return result.sort((a, b) => b.missingDays - a.missingDays)
}

export const calculateSumAnalysis = (data: number[][]): { min: number; max: number; avg: number; std: number } => {
  if (data.length === 0) {
    return { min: 0, max: 0, avg: 0, std: 0 }
  }
  const sums = data.map(row => row.reduce((a, b) => a + b, 0))
  const min = Math.min(...sums)
  const max = Math.max(...sums)
  const avg = sums.reduce((a, b) => a + b, 0) / sums.length
  const variance = sums.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / sums.length
  const std = Math.sqrt(variance)

  return { min, max, avg, std }
}

export const calculateParityAnalysis = (data: number[][]): { oddCount: number; evenCount: number; oddRate: number; evenRate: number } => {
  let oddCount = 0
  let evenCount = 0

  data.forEach(row => {
    row.forEach(num => {
      if (num % 2 === 0) {
        evenCount++
      } else {
        oddCount++
      }
    })
  })

  const total = oddCount + evenCount || 1

  return {
    oddCount,
    evenCount,
    oddRate: oddCount / total,
    evenRate: evenCount / total
  }
}

export const calculatePositionAnalysis = (data: number[][], totalNumbers: number, startNumber: number = 1): PositionAnalysis[] => {
  const positions = data[0]?.length || 0
  const result: PositionAnalysis[] = []

  for (let pos = 0; pos < positions; pos++) {
    const positionData = data.map(row => [row[pos]])
    const hotCold = calculateHotColdNumbers(positionData, totalNumbers, startNumber)
    result.push({
      position: pos + 1,
      hotNumbers: hotCold.filter(n => n.isHot).slice(0, 5),
      coldNumbers: hotCold.filter(n => n.isCold).slice(0, 5),
      missingNumbers: calculateMissingNumbers(positionData, totalNumbers, startNumber).slice(0, 5)
    })
  }

  return result
}

export const calculateIntervalAnalysis = (data: number[][], intervals: { start: number; end: number; label: string }[]): IntervalAnalysis[] => {
  const totalOccurrences = data.reduce((acc, row) => acc + row.length, 0)
  
  return intervals.map(interval => {
    const count = data.reduce((acc, row) => {
      return acc + row.filter(num => num >= interval.start && num <= interval.end).length
    }, 0)
    return {
      interval: interval.label,
      start: interval.start,
      end: interval.end,
      count,
      rate: totalOccurrences > 0 ? count / totalOccurrences : 0
    }
  })
}

export const getStatistics = (table: string, numberField: string, totalNumbers: number, startNumber: number = 1): StatisticalResult => {
  const rows = getAll(table as any)
  const numbers = rows.map(row => row[numberField])
  
  const hotCold = calculateHotColdNumbers(numbers, totalNumbers, startNumber)
  const hotNumbers = hotCold.filter(n => n.isHot).slice(0, 10)
  const coldNumbers = hotCold.filter(n => n.isCold).slice(0, 10)
  const missingNumbers = calculateMissingNumbers(numbers, totalNumbers, startNumber)
  const sumAnalysis = calculateSumAnalysis(numbers)
  const parityAnalysis = calculateParityAnalysis(numbers)

  return {
    hotNumbers,
    coldNumbers,
    missingNumbers,
    sumAnalysis,
    parityAnalysis
  }
}

export const getDoubleColorBallStatistics = (): StatisticalResult => {
  const rows = getAll('double_color_ball')
  const redNumbers = rows.map(row => row.red_numbers)
  const blueNumbers = rows.map(row => [row.blue_number])
  
  const redHotCold = calculateHotColdNumbers(redNumbers, 33)
  const blueHotCold = calculateHotColdNumbers(blueNumbers, 16)
  
  const result: StatisticalResult = {
    hotNumbers: redHotCold.filter(n => n.isHot).slice(0, 10),
    coldNumbers: redHotCold.filter(n => n.isCold).slice(0, 10),
    missingNumbers: calculateMissingNumbers(redNumbers, 33).slice(0, 10),
    sumAnalysis: calculateSumAnalysis(redNumbers),
    parityAnalysis: calculateParityAnalysis(redNumbers),
    intervalAnalysis: calculateIntervalAnalysis(redNumbers, [
      { start: 1, end: 11, label: '一区' },
      { start: 12, end: 22, label: '二区' },
      { start: 23, end: 33, label: '三区' }
    ]),
    secondaryAnalysis: {
      hotNumbers: blueHotCold.filter(n => n.isHot).slice(0, 5),
      coldNumbers: blueHotCold.filter(n => n.isCold).slice(0, 5),
      missingNumbers: calculateMissingNumbers(blueNumbers, 16).slice(0, 5)
    }
  }
  
  return result
}

export const getSuperLottoStatistics = (): StatisticalResult => {
  const rows = getAll('super_lotto')
  const frontNumbers = rows.map(row => row.front_numbers)
  const backNumbers = rows.map(row => row.back_numbers)
  
  const frontHotCold = calculateHotColdNumbers(frontNumbers, 35)
  const backHotCold = calculateHotColdNumbers(backNumbers, 12)
  
  const result: StatisticalResult = {
    hotNumbers: frontHotCold.filter(n => n.isHot).slice(0, 10),
    coldNumbers: frontHotCold.filter(n => n.isCold).slice(0, 10),
    missingNumbers: calculateMissingNumbers(frontNumbers, 35).slice(0, 10),
    sumAnalysis: calculateSumAnalysis(frontNumbers),
    parityAnalysis: calculateParityAnalysis(frontNumbers),
    intervalAnalysis: calculateIntervalAnalysis(frontNumbers, [
      { start: 1, end: 7, label: '一区' },
      { start: 8, end: 14, label: '二区' },
      { start: 15, end: 21, label: '三区' },
      { start: 22, end: 28, label: '四区' },
      { start: 29, end: 35, label: '五区' }
    ]),
    secondaryAnalysis: {
      hotNumbers: backHotCold.filter(n => n.isHot).slice(0, 5),
      coldNumbers: backHotCold.filter(n => n.isCold).slice(0, 5),
      missingNumbers: calculateMissingNumbers(backNumbers, 12).slice(0, 5)
    }
  }
  
  return result
}

export const getLottery3DStatistics = (): StatisticalResult => {
  const rows = getAll('lottery_3d')
  const numbers = rows.map(row => row.numbers)
  
  const hotCold = calculateHotColdNumbers(numbers, 10, 0)
  
  return {
    hotNumbers: hotCold.filter(n => n.isHot).slice(0, 5),
    coldNumbers: hotCold.filter(n => n.isCold).slice(0, 5),
    missingNumbers: calculateMissingNumbers(numbers, 10, 0).slice(0, 5),
    sumAnalysis: calculateSumAnalysis(numbers),
    parityAnalysis: calculateParityAnalysis(numbers),
    positionAnalysis: calculatePositionAnalysis(numbers, 10, 0)
  }
}

export const getHappy8Statistics = (): StatisticalResult => {
  return getStatistics('happy_8', 'numbers', 80)
}

export const getArrangement3Statistics = (): StatisticalResult => {
  const rows = getAll('arrangement_3')
  const numbers = rows.map(row => row.numbers)
  
  const hotCold = calculateHotColdNumbers(numbers, 10, 0)
  
  return {
    hotNumbers: hotCold.filter(n => n.isHot).slice(0, 5),
    coldNumbers: hotCold.filter(n => n.isCold).slice(0, 5),
    missingNumbers: calculateMissingNumbers(numbers, 10, 0).slice(0, 5),
    sumAnalysis: calculateSumAnalysis(numbers),
    parityAnalysis: calculateParityAnalysis(numbers),
    positionAnalysis: calculatePositionAnalysis(numbers, 10, 0)
  }
}

export const getArrangement5Statistics = (): StatisticalResult => {
  const rows = getAll('arrangement_5')
  const numbers = rows.map(row => row.numbers)
  
  const hotCold = calculateHotColdNumbers(numbers, 10, 0)
  
  return {
    hotNumbers: hotCold.filter(n => n.isHot).slice(0, 5),
    coldNumbers: hotCold.filter(n => n.isCold).slice(0, 5),
    missingNumbers: calculateMissingNumbers(numbers, 10, 0).slice(0, 5),
    sumAnalysis: calculateSumAnalysis(numbers),
    parityAnalysis: calculateParityAnalysis(numbers),
    positionAnalysis: calculatePositionAnalysis(numbers, 10, 0)
  }
}

export const getSevenStarStatistics = (): StatisticalResult => {
  const rows = getAll('seven_star')
  const numbers = rows.map(row => row.numbers)
  
  const hotCold = calculateHotColdNumbers(numbers, 10, 0)
  
  return {
    hotNumbers: hotCold.filter(n => n.isHot).slice(0, 5),
    coldNumbers: hotCold.filter(n => n.isCold).slice(0, 5),
    missingNumbers: calculateMissingNumbers(numbers, 10, 0).slice(0, 5),
    sumAnalysis: calculateSumAnalysis(numbers),
    parityAnalysis: calculateParityAnalysis(numbers),
    positionAnalysis: calculatePositionAnalysis(numbers, 10, 0)
  }
}

export const getSevenColorStatistics = (): StatisticalResult => {
  const rows = getAll('seven_color')
  const basicNumbers = rows.map(row => row.basic_numbers)
  const specialNumbers = rows.map(row => [row.special_number])
  
  const basicHotCold = calculateHotColdNumbers(basicNumbers, 30)
  const specialHotCold = calculateHotColdNumbers(specialNumbers, 30)
  
  return {
    hotNumbers: basicHotCold.filter(n => n.isHot).slice(0, 10),
    coldNumbers: basicHotCold.filter(n => n.isCold).slice(0, 10),
    missingNumbers: calculateMissingNumbers(basicNumbers, 30).slice(0, 10),
    sumAnalysis: calculateSumAnalysis(basicNumbers),
    parityAnalysis: calculateParityAnalysis(basicNumbers),
    secondaryAnalysis: {
      hotNumbers: specialHotCold.filter(n => n.isHot).slice(0, 5),
      coldNumbers: specialHotCold.filter(n => n.isCold).slice(0, 5),
      missingNumbers: calculateMissingNumbers(specialNumbers, 30).slice(0, 5)
    }
  }
}