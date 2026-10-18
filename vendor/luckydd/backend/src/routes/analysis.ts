import express from 'express'
import {
  getDoubleColorBallStatistics,
  getSuperLottoStatistics,
  getLottery3DStatistics,
  getHappy8Statistics,
  getArrangement3Statistics,
  getArrangement5Statistics,
  getSevenStarStatistics,
  getSevenColorStatistics
} from '../analysis/statistics'

import {
  getDoubleColorBallPatterns,
  getSuperLottoPatterns,
  getLottery3DPatterns,
  getHappy8Patterns,
  getArrangement3Patterns,
  getArrangement5Patterns,
  getSevenStarPatterns,
  getSevenColorPatterns
} from '../analysis/patternMining'

import {
  getDoubleColorBallAnomalies,
  getSuperLottoAnomalies,
  getLottery3DAnomalies,
  getHappy8Anomalies,
  getArrangement3Anomalies,
  getArrangement5Anomalies,
  getSevenStarAnomalies,
  getSevenColorAnomalies
} from '../analysis/anomalyDetection'

import {
  getDoubleColorBallRecommendations,
  getSuperLottoRecommendations,
  getLottery3DRecommendations,
  getHappy8Recommendations,
  getArrangement3Recommendations,
  getArrangement5Recommendations,
  getSevenStarRecommendations,
  getSevenColorRecommendations
} from '../analysis/recommendation'

const router = express.Router()

const statisticsRoutes: Record<string, () => any> = {
  'double-color-ball': getDoubleColorBallStatistics,
  'super-lotto': getSuperLottoStatistics,
  'lottery-3d': getLottery3DStatistics,
  'happy-8': getHappy8Statistics,
  'arrangement-3': getArrangement3Statistics,
  'arrangement-5': getArrangement5Statistics,
  'seven-star': getSevenStarStatistics,
  'seven-color': getSevenColorStatistics
}

const patternsRoutes: Record<string, () => any> = {
  'double-color-ball': getDoubleColorBallPatterns,
  'super-lotto': getSuperLottoPatterns,
  'lottery-3d': getLottery3DPatterns,
  'happy-8': getHappy8Patterns,
  'arrangement-3': getArrangement3Patterns,
  'arrangement-5': getArrangement5Patterns,
  'seven-star': getSevenStarPatterns,
  'seven-color': getSevenColorPatterns
}

const recommendationsRoutes: Record<string, (weights?: any) => any> = {
  'double-color-ball': getDoubleColorBallRecommendations,
  'super-lotto': getSuperLottoRecommendations,
  'lottery-3d': getLottery3DRecommendations,
  'happy-8': getHappy8Recommendations,
  'arrangement-3': getArrangement3Recommendations,
  'arrangement-5': getArrangement5Recommendations,
  'seven-star': getSevenStarRecommendations,
  'seven-color': getSevenColorRecommendations
}

router.get('/statistics/:type', (req, res) => {
  try {
    const handler = statisticsRoutes[req.params.type]
    if (!handler) {
      res.status(400).json({ error: 'Invalid lottery type' })
      return
    }
    const result = handler()
    res.json(result)
  } catch (error) {
    res.status(500).json({ error: (error as Error).message })
  }
})

router.get('/patterns/:type', (req, res) => {
  try {
    const handler = patternsRoutes[req.params.type]
    if (!handler) {
      res.status(400).json({ error: 'Invalid lottery type' })
      return
    }
    const result = handler()
    res.json(result)
  } catch (error) {
    res.status(500).json({ error: (error as Error).message })
  }
})

const anomaliesRoutes: Record<string, () => any> = {
  'double-color-ball': getDoubleColorBallAnomalies,
  'super-lotto': getSuperLottoAnomalies,
  'lottery-3d': getLottery3DAnomalies,
  'happy-8': getHappy8Anomalies,
  'arrangement-3': getArrangement3Anomalies,
  'arrangement-5': getArrangement5Anomalies,
  'seven-star': getSevenStarAnomalies,
  'seven-color': getSevenColorAnomalies
}

router.get('/anomalies/:type', (req, res) => {
  try {
    const handler = anomaliesRoutes[req.params.type]
    if (!handler) {
      res.status(400).json({ error: 'Invalid lottery type' })
      return
    }
    const result = handler()
    res.json(result)
  } catch (error) {
    res.status(500).json({ error: (error as Error).message })
  }
})

router.get('/recommendations/:type', (req, res) => {
  try {
    const handler = recommendationsRoutes[req.params.type]
    if (!handler) {
      res.status(400).json({ error: 'Invalid lottery type' })
      return
    }
    
    let weights: any = null
    if (req.query.weights) {
      try {
        weights = JSON.parse(req.query.weights as string)
      } catch (e) {
        res.status(400).json({ error: 'Invalid weights parameter' })
        return
      }
    }
    
    const result = weights ? handler(weights) : handler()
    res.json(result)
  } catch (error) {
    res.status(500).json({ error: (error as Error).message })
  }
})

export const analysisRoutes = router
