import { Router } from 'express'
import { getAll, query } from '../database'
import { calculateHotColdNumbers } from '../analysis/statistics'
import { findSequencePatterns } from '../analysis/patternMining'

const router = Router()

router.get('/trends/:lotteryType', (req, res) => {
  const { lotteryType } = req.params
  const limit = parseInt(req.query.limit as string) || 100
  
  const data = query(lotteryType as any, { limit, orderBy: 'date', order: 'DESC' })
  if (!data || data.length === 0) {
    return res.json({ issues: [], trends: [] })
  }

  const issues = data.map((d: any) => d.date)
  
  const fieldMap: Record<string, string> = {
    'double_color_ball': 'red_numbers',
    'super_lotto': 'front_numbers',
    'lottery_3d': 'numbers',
    'happy_8': 'numbers',
    'arrangement_3': 'numbers',
    'arrangement_5': 'numbers',
    'seven_star': 'numbers',
    'seven_color': 'basic_numbers'
  }

  const field = fieldMap[lotteryType] || 'numbers'
  const totalNumbers = lotteryType === 'happy_8' ? 80 : lotteryType.includes('lottery_3d') || lotteryType.includes('arrangement') || lotteryType.includes('seven_star') ? 10 : lotteryType === 'seven_color' ? 30 : lotteryType === 'double_color_ball' ? 33 : 35
  const startNumber = lotteryType.includes('lottery_3d') || lotteryType.includes('arrangement') || lotteryType.includes('seven_star') ? 0 : 1

  const trends: number[][] = Array.from({ length: totalNumbers }, () => [])

  data.forEach((row: any) => {
    const numbers = row[field]
    const drawnNumbers = Array.isArray(numbers) ? numbers : [numbers]
    const drawnSet = new Set(drawnNumbers)

    for (let i = startNumber; i < startNumber + totalNumbers; i++) {
      const value = drawnSet.has(i) ? 1 : 0
      trends[i - startNumber].push(value)
    }
  })

  res.json({
    issues,
    trends,
    totalNumbers,
    startNumber
  })
})

router.get('/heatmap/:lotteryType', (req, res) => {
  const { lotteryType } = req.params
  
  const data = getAll(lotteryType as any)
  if (!data || data.length === 0) {
    return res.json({ heatmap: [] })
  }

  const fieldMap: Record<string, string> = {
    'double_color_ball': 'red_numbers',
    'super_lotto': 'front_numbers',
    'lottery_3d': 'numbers',
    'happy_8': 'numbers',
    'arrangement_3': 'numbers',
    'arrangement_5': 'numbers',
    'seven_star': 'numbers',
    'seven_color': 'basic_numbers'
  }

  const field = fieldMap[lotteryType] || 'numbers'
  const totalNumbers = lotteryType === 'happy_8' ? 80 : lotteryType.includes('lottery_3d') || lotteryType.includes('arrangement') || lotteryType.includes('seven_star') ? 10 : lotteryType === 'seven_color' ? 30 : lotteryType === 'double_color_ball' ? 33 : 35
  const startNumber = lotteryType.includes('lottery_3d') || lotteryType.includes('arrangement') || lotteryType.includes('seven_star') ? 0 : 1

  const numbers = data.map((row: any) => row[field]).flat()
  const frequency = Array.from({ length: totalNumbers }, (_, i) => ({
    number: i + startNumber,
    count: 0,
    rate: 0
  }))

  numbers.forEach((num: number) => {
    const index = num - startNumber
    if (index >= 0 && index < totalNumbers) {
      frequency[index].count++
    }
  })

  const totalDraws = data.length
  const totalCount = numbers.length

  frequency.forEach(item => {
    item.rate = totalDraws > 0 ? item.count / totalDraws : 0
  })

  res.json({
    heatmap: frequency,
    totalDraws,
    totalCount
  })
})

router.get('/sequences/:lotteryType', (req, res) => {
  const { lotteryType } = req.params
  const windowSize = parseInt(req.query.windowSize as string) || 5
  
  const data = getAll(lotteryType as any)
  if (!data || data.length === 0) {
    return res.json({ sequences: [] })
  }

  const fieldMap: Record<string, string> = {
    'double_color_ball': 'red_numbers',
    'super_lotto': 'front_numbers',
    'lottery_3d': 'numbers',
    'happy_8': 'numbers',
    'arrangement_3': 'numbers',
    'arrangement_5': 'numbers',
    'seven_star': 'numbers',
    'seven_color': 'basic_numbers'
  }

  const field = fieldMap[lotteryType] || 'numbers'
  const numbers = data.map((row: any) => row[field])
  const sequences = findSequencePatterns(numbers, windowSize)

  res.json({ sequences })
})

export const advancedAnalysisRoutes = router