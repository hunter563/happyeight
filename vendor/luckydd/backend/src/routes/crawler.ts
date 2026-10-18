import express from 'express'
import {
  crawlDoubleColorBall,
  crawlSuperLotto,
  crawlLottery3D,
  crawlHappy8,
  crawlArrangement3,
  crawlArrangement5,
  crawlSevenStar,
  crawlSevenColor,
  crawlAll
} from '../crawlers/8200cn'
import { generateMockData } from '../crawlers/mockData'
import { manualUpdate, resetDatabase } from '../crawler/lotteryCrawler'

const router = express.Router()

router.post('/double-color-ball', async (req, res) => {
  try {
    await crawlDoubleColorBall()
    res.json({ status: 'success', message: '双色球数据采集完成' })
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/super-lotto', async (req, res) => {
  try {
    await crawlSuperLotto()
    res.json({ status: 'success', message: '大乐透数据采集完成' })
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/lottery-3d', async (req, res) => {
  try {
    await crawlLottery3D()
    res.json({ status: 'success', message: '福彩3D数据采集完成' })
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/happy-8', async (req, res) => {
  try {
    await crawlHappy8()
    res.json({ status: 'success', message: '快乐8数据采集完成' })
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/arrangement-3', async (req, res) => {
  try {
    await crawlArrangement3()
    res.json({ status: 'success', message: '排列3数据采集完成' })
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/arrangement-5', async (req, res) => {
  try {
    await crawlArrangement5()
    res.json({ status: 'success', message: '排列5数据采集完成' })
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/seven-star', async (req, res) => {
  try {
    await crawlSevenStar()
    res.json({ status: 'success', message: '七星彩数据采集完成' })
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/seven-color', async (req, res) => {
  try {
    await crawlSevenColor()
    res.json({ status: 'success', message: '七乐彩数据采集完成' })
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/all', async (req, res) => {
  try {
    await crawlAll()
    res.json({ status: 'success', message: '所有彩种数据采集完成' })
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/mock', async (req, res) => {
  try {
    generateMockData()
    res.json({ status: 'success', message: '模拟数据生成完成' })
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/update', async (req, res) => {
  try {
    const result = await manualUpdate()
    res.json(result)
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

router.post('/reset', async (req, res) => {
  try {
    const result = await resetDatabase()
    res.json(result)
  } catch (error) {
    res.status(500).json({ status: 'error', message: (error as Error).message })
  }
})

export const crawlerRoutes = router