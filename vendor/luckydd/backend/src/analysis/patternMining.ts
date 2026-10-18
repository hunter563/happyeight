import { getAll } from '../database'

export interface Pattern {
  numbers: number[]
  count: number
  support: number
  confidence?: number
}

export interface SequencePattern {
  sequence: number[][]
  count: number
  support: number
}

export const findFrequentPatterns = (data: number[][], minSupport: number = 0.02): Pattern[] => {
  const patternMap: Record<string, number> = {}
  const totalDraws = data.length

  data.forEach(row => {
    const sortedRow = [...row].sort((a, b) => a - b)
    
    for (let i = 0; i < sortedRow.length; i++) {
      for (let j = i + 1; j <= sortedRow.length; j++) {
        const pattern = sortedRow.slice(i, j).join(',')
        if (pattern.length > 0) {
          patternMap[pattern] = (patternMap[pattern] || 0) + 1
        }
      }
    }
  })

  return Object.entries(patternMap)
    .map(([pattern, count]) => ({
      numbers: pattern.split(',').map(Number),
      count,
      support: count / totalDraws
    }))
    .filter(p => p.support >= minSupport && p.numbers.length >= 2)
    .sort((a, b) => b.support - a.support)
    .slice(0, 50)
}

export const findSequencePatterns = (data: number[][], windowSize: number = 5): SequencePattern[] => {
  const sequenceMap: Record<string, number> = {}
  const totalDraws = data.length

  for (let i = 0; i < totalDraws - windowSize + 1; i++) {
    const window = data.slice(i, i + windowSize)
    const sequenceKey = window.map(row => row.join(',')).join('|')
    sequenceMap[sequenceKey] = (sequenceMap[sequenceKey] || 0) + 1
  }

  return Object.entries(sequenceMap)
    .map(([key, count]) => ({
      sequence: key.split('|').map(s => s.split(',').map(Number)),
      count,
      support: count / (totalDraws - windowSize + 1)
    }))
    .filter(s => s.support > 0.01)
    .sort((a, b) => b.support - a.support)
    .slice(0, 20)
}

export const findNumberCorrelations = (data: number[][], totalNumbers: number, startNumber: number = 1): { number1: number; number2: number; correlation: number; count: number }[] => {
  const pairCount: Record<string, number> = {}
  const singleCount: Record<number, number> = {}
  const totalDraws = data.length

  data.forEach(row => {
    row.forEach(num1 => {
      singleCount[num1] = (singleCount[num1] || 0) + 1
      row.forEach(num2 => {
        if (num1 < num2) {
          const key = `${num1},${num2}`
          pairCount[key] = (pairCount[key] || 0) + 1
        }
      })
    })
  })

  return Object.entries(pairCount)
    .map(([key, count]) => {
      const [num1, num2] = key.split(',').map(Number)
      const expected = (singleCount[num1] / totalDraws) * (singleCount[num2] / totalDraws) * totalDraws
      const correlation = count / expected
      return { number1: num1, number2: num2, correlation, count }
    })
    .sort((a, b) => b.correlation - a.correlation)
    .slice(0, 30)
}

export const getPatterns = (table: string, numberField: string, totalNumbers: number, startNumber: number = 1): { patterns: Pattern[]; correlations: { number1: number; number2: number; correlation: number; count: number }[] } => {
  const rows = getAll(table as any)
  const numbers = rows.map(row => row[numberField])
  const patterns = findFrequentPatterns(numbers)
  const correlations = findNumberCorrelations(numbers, totalNumbers, startNumber)

  return { patterns, correlations }
}

export const getDoubleColorBallPatterns = (): { patterns: Pattern[]; correlations: { number1: number; number2: number; correlation: number; count: number }[]; bluePatterns?: Pattern[]; blueCorrelations?: { number1: number; number2: number; correlation: number; count: number }[] } => {
  const rows = getAll('double_color_ball')
  const redNumbers = rows.map(row => row.red_numbers)
  const blueNumbers = rows.map(row => [row.blue_number])
  
  return {
    patterns: findFrequentPatterns(redNumbers),
    correlations: findNumberCorrelations(redNumbers, 33),
    bluePatterns: findFrequentPatterns(blueNumbers, 0.05),
    blueCorrelations: findNumberCorrelations(blueNumbers, 16)
  }
}

export const getSuperLottoPatterns = (): { patterns: Pattern[]; correlations: { number1: number; number2: number; correlation: number; count: number }[]; backPatterns?: Pattern[]; backCorrelations?: { number1: number; number2: number; correlation: number; count: number }[] } => {
  const rows = getAll('super_lotto')
  const frontNumbers = rows.map(row => row.front_numbers)
  const backNumbers = rows.map(row => row.back_numbers)
  
  return {
    patterns: findFrequentPatterns(frontNumbers),
    correlations: findNumberCorrelations(frontNumbers, 35),
    backPatterns: findFrequentPatterns(backNumbers, 0.05),
    backCorrelations: findNumberCorrelations(backNumbers, 12)
  }
}

export const getLottery3DPatterns = (): { patterns: Pattern[]; correlations: { number1: number; number2: number; correlation: number; count: number }[] } => {
  return getPatterns('lottery_3d', 'numbers', 10, 0)
}

export const getHappy8Patterns = (): { patterns: Pattern[]; correlations: { number1: number; number2: number; correlation: number; count: number }[] } => {
  return getPatterns('happy_8', 'numbers', 80)
}

export const getArrangement3Patterns = (): { patterns: Pattern[]; correlations: { number1: number; number2: number; correlation: number; count: number }[] } => {
  return getPatterns('arrangement_3', 'numbers', 10, 0)
}

export const getArrangement5Patterns = (): { patterns: Pattern[]; correlations: { number1: number; number2: number; correlation: number; count: number }[] } => {
  return getPatterns('arrangement_5', 'numbers', 10, 0)
}

export const getSevenStarPatterns = (): { patterns: Pattern[]; correlations: { number1: number; number2: number; correlation: number; count: number }[] } => {
  return getPatterns('seven_star', 'numbers', 10, 0)
}

export const getSevenColorPatterns = (): { patterns: Pattern[]; correlations: { number1: number; number2: number; correlation: number; count: number }[] } => {
  return getPatterns('seven_color', 'basic_numbers', 30)
}
