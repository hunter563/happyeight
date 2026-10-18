import express from 'express'
import { query, count, getLatest } from '../database'

const router = express.Router()

const createRoute = (table: string) => {
  return (req: express.Request, res: express.Response) => {
    const page = parseInt(req.query.page as string) || 1
    const limit = parseInt(req.query.limit as string) || 20
    const offset = (page - 1) * limit

    const rows = query(table as any, { limit, offset, orderBy: 'date', order: 'DESC' })
    const total = count(table as any)

    res.json({
      data: rows,
      total,
      page,
      limit
    })
  }
}

router.get('/double-color-ball', createRoute('double_color_ball'))
router.get('/super-lotto', createRoute('super_lotto'))
router.get('/lottery-3d', createRoute('lottery_3d'))
router.get('/happy-8', createRoute('happy_8'))
router.get('/arrangement-3', createRoute('arrangement_3'))
router.get('/arrangement-5', createRoute('arrangement_5'))
router.get('/seven-star', createRoute('seven_star'))
router.get('/seven-color', createRoute('seven_color'))

router.get('/latest/:type', (req, res) => {
  const type = req.params.type

  const tableMap: Record<string, string> = {
    'double-color-ball': 'double_color_ball',
    'super-lotto': 'super_lotto',
    'lottery-3d': 'lottery_3d',
    'happy-8': 'happy_8',
    'arrangement-3': 'arrangement_3',
    'arrangement-5': 'arrangement_5',
    'seven-star': 'seven_star',
    'seven-color': 'seven_color'
  }

  const table = tableMap[type]

  if (!table) {
    res.status(400).json({ error: 'Invalid lottery type' })
    return
  }

  const row = getLatest(table as any)

  if (!row) {
    res.status(404).json({ error: 'No data found' })
    return
  }

  res.json(row)
})

export const lotteryRoutes = router