import express from 'express'
import cors from 'cors'
import dotenv from 'dotenv'
import { initDatabase } from './database'
import { lotteryRoutes } from './routes/lottery'
import { crawlerRoutes } from './routes/crawler'
import { analysisRoutes } from './routes/analysis'
import { advancedAnalysisRoutes } from './routes/advancedAnalysis'

dotenv.config()

const app = express()
const PORT = process.env.PORT || 3000

app.use(cors())
app.use(express.json())

app.use('/api/lottery', lotteryRoutes)
app.use('/api/crawler', crawlerRoutes)
app.use('/api/analysis', analysisRoutes)
app.use('/api/advanced', advancedAnalysisRoutes)

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'LuckyDD Backend is running' })
})

const start = () => {
  try {
    initDatabase()
    console.log('Database initialized successfully')
    app.listen(PORT, () => {
      console.log(`Server running on port ${PORT}`)
    })
  } catch (error) {
    console.error('Failed to start server:', error)
    process.exit(1)
  }
}

start()