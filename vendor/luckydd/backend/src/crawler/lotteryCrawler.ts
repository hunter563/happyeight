import axios from 'axios'
import * as cheerio from 'cheerio'
import * as fs from 'fs'
import * as path from 'path'

const DATABASE_PATH = path.join(process.cwd(), 'data', 'database.json')

export interface LotteryCrawlerConfig {
  name: string
  url: string
  lotteryType: string
  parseFunction: (html: string) => any[]
}

const parseDate = (dateStr: string): string => {
  if (!dateStr) return ''
  
  const fullDateMatch = dateStr.match(/^(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日]?/)
  if (fullDateMatch) {
    return `${fullDateMatch[1]}-${String(fullDateMatch[2]).padStart(2, '0')}-${String(fullDateMatch[3]).padStart(2, '0')}`
  }
  
  const monthDayMatch = dateStr.match(/(\d{1,2})[-/](\d{1,2})/)
  if (monthDayMatch) {
    const month = parseInt(monthDayMatch[1])
    const day = parseInt(monthDayMatch[2])
    const now = new Date()
    let year = now.getFullYear()
    
    if (month > now.getMonth() + 1) {
      year = now.getFullYear() - 1
    }
    
    return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  }
  
  return dateStr
}

export const crawlerConfigs: LotteryCrawlerConfig[] = [
  {
    name: '双色球',
    url: 'https://www.8200.cn/kjh/ssq/history.htm?size=100',
    lotteryType: 'double_color_ball',
    parseFunction: (html) => {
      const $ = cheerio.load(html)
      const data: any[] = []
      
      $('.kjhTable tbody tr').each((_, row) => {
        const $row = $(row)
        const cells = $row.find('td')
        if (cells.length < 9) return

        const issue = cells.eq(0).text().trim().replace(/[^\d]/g, '')
        const dateStr = cells.eq(1).text().trim()
        const drawDate = parseDate(dateStr)
        
        const redNumbers: number[] = []
        let blueNumber = 0

        for (let i = 2; i < 8; i++) {
          const num = parseInt(cells.eq(i).text().trim())
          if (!isNaN(num)) redNumbers.push(num)
        }
        const blueNum = parseInt(cells.eq(8).text().trim())
        if (!isNaN(blueNum)) blueNumber = blueNum

        if (issue && drawDate && redNumbers.length === 6 && blueNumber > 0) {
          data.push({
            id: issue,
            date: drawDate,
            red_numbers: redNumbers,
            blue_number: blueNumber
          })
        }
      })

      return data
    }
  },
  {
    name: '大乐透',
    url: 'https://www.8200.cn/kjh/dlt/history.htm?size=100',
    lotteryType: 'super_lotto',
    parseFunction: (html) => {
      const $ = cheerio.load(html)
      const data: any[] = []
      
      $('.kjhTable tbody tr').each((_, row) => {
        const $row = $(row)
        const cells = $row.find('td')
        if (cells.length < 9) return

        const issue = cells.eq(0).text().trim().replace(/[^\d]/g, '')
        const dateStr = cells.eq(1).text().trim()
        const drawDate = parseDate(dateStr)
        
        const frontNumbers: number[] = []
        const backNumbers: number[] = []

        for (let i = 2; i < 7; i++) {
          const num = parseInt(cells.eq(i).text().trim())
          if (!isNaN(num)) frontNumbers.push(num)
        }
        const back1 = parseInt(cells.eq(7).text().trim())
        const back2 = parseInt(cells.eq(8).text().trim())
        if (!isNaN(back1)) backNumbers.push(back1)
        if (!isNaN(back2)) backNumbers.push(back2)

        if (issue && drawDate && frontNumbers.length === 5 && backNumbers.length === 2) {
          data.push({
            id: issue,
            date: drawDate,
            front_numbers: frontNumbers,
            back_numbers: backNumbers
          })
        }
      })

      return data
    }
  },
  {
    name: '福彩3D',
    url: 'https://www.8200.cn/kjh/3d/history.htm?size=100',
    lotteryType: 'lottery_3d',
    parseFunction: (html) => {
      const $ = cheerio.load(html)
      const data: any[] = []
      
      $('.kjhTable tbody tr').each((_, row) => {
        const $row = $(row)
        const cells = $row.find('td')
        if (cells.length < 5) return

        const issue = cells.eq(0).text().trim().replace(/[^\d]/g, '')
        const dateStr = cells.eq(1).text().trim()
        const drawDate = parseDate(dateStr)
        
        const numbers: number[] = []

        for (let i = 2; i < 5; i++) {
          const num = parseInt(cells.eq(i).text().trim())
          if (!isNaN(num)) numbers.push(num)
        }

        if (issue && drawDate && numbers.length === 3) {
          data.push({
            id: issue,
            date: drawDate,
            numbers
          })
        }
      })

      return data
    }
  },
  {
    name: '快乐8',
    url: 'https://www.8200.cn/kjh/kl8/history.htm?size=100',
    lotteryType: 'happy_8',
    parseFunction: (html) => {
      const $ = cheerio.load(html)
      const data: any[] = []
      
      $('.kjhTable tbody tr').each((_, row) => {
        const $row = $(row)
        const cells = $row.find('td')
        if (cells.length < 22) return

        const issue = cells.eq(0).text().trim().replace(/[^\d]/g, '')
        const dateStr = cells.eq(1).text().trim()
        const drawDate = parseDate(dateStr)
        
        const numbers: number[] = []

        for (let i = 2; i < 22; i++) {
          const num = parseInt(cells.eq(i).text().trim())
          if (!isNaN(num)) numbers.push(num)
        }

        if (issue && drawDate && numbers.length === 20) {
          data.push({
            id: issue,
            date: drawDate,
            numbers
          })
        }
      })

      return data
    }
  },
  {
    name: '排列3',
    url: 'https://www.8200.cn/kjh/p3/history.htm?size=100',
    lotteryType: 'arrangement_3',
    parseFunction: (html) => {
      const $ = cheerio.load(html)
      const data: any[] = []
      
      $('.kjhTable tbody tr').each((_, row) => {
        const $row = $(row)
        const cells = $row.find('td')
        if (cells.length < 5) return

        const issue = cells.eq(0).text().trim().replace(/[^\d]/g, '')
        const dateStr = cells.eq(1).text().trim()
        const drawDate = parseDate(dateStr)
        
        const numbers: number[] = []

        for (let i = 2; i < 5; i++) {
          const num = parseInt(cells.eq(i).text().trim())
          if (!isNaN(num)) numbers.push(num)
        }

        if (issue && drawDate && numbers.length === 3) {
          data.push({
            id: issue,
            date: drawDate,
            numbers
          })
        }
      })

      return data
    }
  },
  {
    name: '排列5',
    url: 'https://www.8200.cn/kjh/p5/history.htm?size=100',
    lotteryType: 'arrangement_5',
    parseFunction: (html) => {
      const $ = cheerio.load(html)
      const data: any[] = []
      
      $('.kjhTable tbody tr').each((_, row) => {
        const $row = $(row)
        const cells = $row.find('td')
        if (cells.length < 7) return

        const issue = cells.eq(0).text().trim().replace(/[^\d]/g, '')
        const dateStr = cells.eq(1).text().trim()
        const drawDate = parseDate(dateStr)
        
        const numbers: number[] = []

        for (let i = 2; i < 7; i++) {
          const num = parseInt(cells.eq(i).text().trim())
          if (!isNaN(num)) numbers.push(num)
        }

        if (issue && drawDate && numbers.length === 5) {
          data.push({
            id: issue,
            date: drawDate,
            numbers
          })
        }
      })

      return data
    }
  },
  {
    name: '七星彩',
    url: 'https://www.8200.cn/kjh/qxc/history.htm?size=100',
    lotteryType: 'seven_star',
    parseFunction: (html) => {
      const $ = cheerio.load(html)
      const data: any[] = []
      
      $('.kjhTable tbody tr').each((_, row) => {
        const $row = $(row)
        const cells = $row.find('td')
        if (cells.length < 9) return

        const issue = cells.eq(0).text().trim().replace(/[^\d]/g, '')
        const dateStr = cells.eq(1).text().trim()
        const drawDate = parseDate(dateStr)
        
        const numbers: number[] = []

        for (let i = 2; i < 9; i++) {
          const num = parseInt(cells.eq(i).text().trim())
          if (!isNaN(num)) numbers.push(num)
        }

        if (issue && drawDate && numbers.length === 7) {
          data.push({
            id: issue,
            date: drawDate,
            numbers
          })
        }
      })

      return data
    }
  },
  {
    name: '七乐彩',
    url: 'https://www.8200.cn/kjh/qlc/history.htm?size=100',
    lotteryType: 'seven_color',
    parseFunction: (html) => {
      const $ = cheerio.load(html)
      const data: any[] = []
      
      $('.kjhTable tbody tr').each((_, row) => {
        const $row = $(row)
        const cells = $row.find('td')
        if (cells.length < 9) return

        const issue = cells.eq(0).text().trim().replace(/[^\d]/g, '')
        const dateStr = cells.eq(1).text().trim()
        const drawDate = parseDate(dateStr)
        
        const basicNumbers: number[] = []
        let specialNumber = 0

        for (let i = 2; i < 9; i++) {
          const num = parseInt(cells.eq(i).text().trim())
          if (!isNaN(num)) basicNumbers.push(num)
        }
        const specialNum = parseInt(cells.eq(9).text().trim())
        if (!isNaN(specialNum)) specialNumber = specialNum

        if (issue && drawDate && basicNumbers.length === 7 && specialNumber > 0) {
          data.push({
            id: issue,
            date: drawDate,
            basic_numbers: basicNumbers,
            special_number: specialNumber
          })
        }
      })

      return data
    }
  }
]

export const fetchLotteryData = async (config: LotteryCrawlerConfig, retryCount = 3): Promise<any[]> => {
  for (let attempt = 0; attempt < retryCount; attempt++) {
    try {
      const response = await axios.get(config.url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
          'Accept-Encoding': 'gzip, deflate, br',
          'Referer': 'https://www.8200.cn/',
          'Connection': 'keep-alive',
          'Cache-Control': 'no-cache'
        },
        timeout: 20000
      })

      return config.parseFunction(response.data)
    } catch (error) {
      console.error(`抓取 ${config.name} 失败 (尝试 ${attempt + 1}/${retryCount}):`, error)
      if (attempt === retryCount - 1) {
        throw new Error(`无法抓取 ${config.name} 数据: ${error}`)
      }
      await new Promise(resolve => setTimeout(resolve, 2000))
    }
  }
  return []
}

export const updateDatabase = async (): Promise<{ success: boolean; updated: string[]; errors: string[] }> => {
  const updated: string[] = []
  const errors: string[] = []

  if (!fs.existsSync(DATABASE_PATH)) {
    errors.push('数据库文件不存在')
    return { success: false, updated, errors }
  }

  const database = JSON.parse(fs.readFileSync(DATABASE_PATH, 'utf-8'))

  for (const config of crawlerConfigs) {
    try {
      const newData = await fetchLotteryData(config)

      if (newData.length === 0) {
        errors.push(`${config.name}: 没有获取到新数据`)
        continue
      }

      const existingData = database[config.lotteryType] || []
      const existingIssues = new Set(existingData.map((d: any) => d.id))
      const newEntries = newData.filter((d: any) => !existingIssues.has(d.id))

      if (newEntries.length > 0) {
        database[config.lotteryType] = [...existingData, ...newEntries].sort((a: any, b: any) => a.id.localeCompare(b.id))
        updated.push(`${config.name}: 新增 ${newEntries.length} 条数据`)
      } else {
        updated.push(`${config.name}: 没有新数据`)
      }
    } catch (error) {
      errors.push(`${config.name}: ${error}`)
    }
  }

  fs.writeFileSync(DATABASE_PATH, JSON.stringify(database, null, 2), 'utf-8')

  return {
    success: errors.length === 0,
    updated,
    errors
  }
}

export const resetDatabase = async (): Promise<{ success: boolean; message: string }> => {
  try {
    const emptyDb = {
      double_color_ball: [],
      super_lotto: [],
      lottery_3d: [],
      happy_8: [],
      arrangement_3: [],
      arrangement_5: [],
      seven_star: [],
      seven_color: []
    }
    fs.writeFileSync(DATABASE_PATH, JSON.stringify(emptyDb, null, 2), 'utf-8')
    return { success: true, message: '数据库已重置' }
  } catch (error) {
    return { success: false, message: (error as Error).message }
  }
}

export const startAutoUpdate = (intervalHours = 12): void => {
  console.log(`自动更新已启动，每 ${intervalHours} 小时更新一次数据`)

  const update = async () => {
    console.log('开始更新彩票数据...')
    const result = await updateDatabase()

    if (result.success) {
      console.log('更新成功:', result.updated.join(', '))
    } else {
      console.error('更新失败:', result.errors.join(', '))
    }
  }

  update()

  setInterval(update, intervalHours * 60 * 60 * 1000)
}

export const manualUpdate = async (): Promise<{ success: boolean; message: string; details: string[] }> => {
  const result = await updateDatabase()

  if (result.success) {
    return {
      success: true,
      message: '数据更新成功',
      details: result.updated
    }
  } else {
    return {
      success: false,
      message: '数据更新部分失败',
      details: [...result.updated, ...result.errors]
    }
  }
}