import axios from 'axios'
import * as cheerio from 'cheerio'
import { insertOrReplace, getAll } from '../database'

const DATA_SOURCE_8200 = {
  baseUrl: 'https://www.8200.cn',
  lotteryUrlMap: {
    ssq: '/kjh/ssq/history.htm',
    dlt: '/kjh/dlt/history.htm',
    fc3d: '/kjh/3d/history.htm',
    kl8: '/kjh/kl8/history.htm',
    pl3: '/kjh/p3/history.htm',
    pl5: '/kjh/p5/history.htm',
    qxc: '/kjh/qxc/history.htm',
    qlc: '/kjh/qlc/history.htm'
  },
  defaultSize: 300
}

const REQUEST_CONFIG = {
  timeout: 20000,
  maxRedirects: 5,
  headers: {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.8200.cn/',
    'Connection': 'keep-alive',
    'Cache-Control': 'no-cache'
  }
}

const TABLE_MAP: Record<string, string> = {
  ssq: 'double_color_ball',
  dlt: 'super_lotto',
  fc3d: 'lottery_3d',
  kl8: 'happy_8',
  pl3: 'arrangement_3',
  pl5: 'arrangement_5',
  qxc: 'seven_star',
  qlc: 'seven_color'
}

const formatNumber = (num: string): string => {
  const n = parseInt(num)
  return isNaN(n) ? '00' : String(n).padStart(2, '0')
}

const parseDate = (dateStr: string): string => {
  if (!dateStr) return new Date().toISOString().split('T')[0]
  
  const date = new Date(dateStr)
  if (!isNaN(date.getTime())) {
    return date.toISOString().split('T')[0]
  }
  
  const now = new Date()
  const currentYear = now.getFullYear()
  
  const monthDayMatch = dateStr.match(/(\d{1,2})[-/](\d{1,2})/)
  if (monthDayMatch) {
    const month = parseInt(monthDayMatch[1])
    const day = parseInt(monthDayMatch[2])
    let year = currentYear
    if (month > now.getMonth() + 1) {
      year = currentYear - 1
    }
    return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  }
  
  return new Date().toISOString().split('T')[0]
}

const parseNumberString = (str: string): string[] => {
  if (!str) return []
  return str
    .toString()
    .trim()
    .split(/[\s,，、]+/)
    .filter(n => n && !isNaN(parseInt(n)))
    .map(n => formatNumber(n))
}

const parseRow = ($: cheerio.CheerioAPI, $row: cheerio.Cheerio<any>, type: string): any => {
  try {
    const cells = $row.find('td, .cell, .col')
    if (cells.length < 3) {
      return null
    }

    const periodText = $row.find('td:first-child, .period, .issue').text().trim()
    const period = periodText.replace(/[^\d]/g, '')

    if (!period) {
      return null
    }

    let dateText = ''
    const now = new Date()
    const currentYear = now.getFullYear()

    cells.each((index: number, cell: any) => {
      const text = $(cell).text().trim()
      
      if (/^\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?/.test(text)) {
        dateText = text.replace(/[年月]/g, '-').replace(/[日]/g, '')
        return false
      }
      
      const monthDayMatch = text.match(/(\d{1,2})[-/](\d{1,2})/)
      if (monthDayMatch && !dateText) {
        const month = parseInt(monthDayMatch[1])
        const day = parseInt(monthDayMatch[2])
        let year = currentYear
        if (month > now.getMonth() + 1) {
          year = currentYear - 1
        }
        dateText = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
        return false
      }
    })

    if (!dateText) {
      const dateAttr = $row.attr('data-date') || $row.attr('title') || $row.find('[data-date]').attr('data-date')
      if (dateAttr) {
        if (/^\d{4}[-/]\d{1,2}[-/]\d{1,2}/.test(dateAttr)) {
          dateText = dateAttr
        } else {
          const monthDayMatch = dateAttr.match(/(\d{1,2})[-/](\d{1,2})/)
          if (monthDayMatch) {
            const month = parseInt(monthDayMatch[1])
            const day = parseInt(monthDayMatch[2])
            let year = currentYear
            if (month > now.getMonth() + 1) {
              year = currentYear - 1
            }
            dateText = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
          }
        }
      }
    }

    if (!dateText) {
      const rowText = $row.text()
      const fullDateMatch = rowText.match(/(\d{4}[-/]\d{1,2}[-/]\d{1,2})/)
      if (fullDateMatch) {
        dateText = fullDateMatch[1]
      } else {
        const monthDayMatch = rowText.match(/(\d{1,2})[-/](\d{1,2})/)
        if (monthDayMatch) {
          const month = parseInt(monthDayMatch[1])
          const day = parseInt(monthDayMatch[2])
          let year = currentYear
          if (month > now.getMonth() + 1) {
            year = currentYear - 1
          }
          dateText = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
        }
      }
    }

    const drawDate = dateText ? parseDate(dateText) : new Date().toISOString().split('T')[0]

    const numbers: string[] = []
    const red: string[] = []
    const blue: string[] = []

    cells.each((index: number, cell: any) => {
      const $cell = $(cell)
      const text = $cell.text().trim()
      
      if (index < 2) return

      const numberText = text || $cell.find('.ball, .number, .num').text().trim()
      if (numberText) {
        const parsed = parseNumberString(numberText)
        numbers.push(...parsed)
      }
    })

    if (type === 'ssq') {
      if (numbers.length >= 7) {
        red.push(...numbers.slice(0, 6))
        blue.push(numbers[6])
      } else if (numbers.length === 6) {
        red.push(...numbers)
        const blueText = $row.find('.blue, .blue-ball, td:last-child').text().trim()
        if (blueText) {
          const blueNum = parseNumberString(blueText)
          if (blueNum.length > 0) {
            blue.push(blueNum[0])
          }
        }
      }
    } else if (type === 'dlt') {
      if (numbers.length >= 7) {
        red.push(...numbers.slice(0, 5))
        blue.push(...numbers.slice(5, 7))
      } else if (numbers.length === 5) {
        red.push(...numbers)
        const blueText = $row.find('.blue, .back, td:last-child').text().trim()
        if (blueText) {
          const blueNums = parseNumberString(blueText)
          blue.push(...blueNums.slice(0, 2))
        }
      }
    } else if (type === 'fc3d' || type === 'pl3') {
      if (numbers.length >= 3) {
        red.push(...numbers.slice(0, 3))
      } else {
        red.push(...numbers)
      }
    } else if (type === 'pl5') {
      if (numbers.length >= 5) {
        red.push(...numbers.slice(0, 5))
      } else {
        red.push(...numbers)
      }
    } else if (type === 'qxc') {
      const validNumbers = numbers.filter(n => {
        const num = parseInt(n)
        return !isNaN(num) && num >= 0 && num <= 9
      })
      if (validNumbers.length >= 7) {
        red.push(...validNumbers.slice(0, 7))
      } else {
        red.push(...validNumbers)
      }
    } else if (type === 'qlc') {
      if (numbers.length >= 8) {
        red.push(...numbers.slice(0, 7))
        blue.push(numbers[7])
      } else if (numbers.length === 7) {
        red.push(...numbers)
        const blueText = $row.find('.blue, .special, td:last-child').text().trim()
        if (blueText) {
          const blueNum = parseNumberString(blueText)
          if (blueNum.length > 0) {
            blue.push(blueNum[0])
          }
        }
      }
    } else if (type === 'kl8') {
      if (numbers.length >= 20) {
        red.push(...numbers.slice(0, 20))
      } else {
        red.push(...numbers)
      }
    } else {
      red.push(...numbers)
    }

    if (red.length === 0 && blue.length === 0) {
      $row.find('.red-ball, .red, .front').each((_: number, el: any) => {
        const num = $(el).text().trim()
        if (num) {
          red.push(formatNumber(num))
        }
      })
      $row.find('.blue-ball, .blue, .back').each((_: number, el: any) => {
        const num = $(el).text().trim()
        if (num) {
          blue.push(formatNumber(num))
        }
      })
    }

    if (red.length === 0 && blue.length === 0) {
      return null
    }

    return {
      period,
      date: drawDate,
      red: red.map(Number),
      blue: blue.map(Number),
      numbers: red.concat(blue).map(Number)
    }
  } catch {
    return null
  }
}

const parse8200HTML = (html: string, type: string): any[] => {
  const $ = cheerio.load(html)
  const draws: any[] = []

  try {
    let table = $('table.history-table, table.kj-table, table.tb, table').first()
    
    if (table.length === 0) {
      table = $('.history-list, .kj-list, .result-list').first()
    }

    if (table.length === 0) {
      const rows = $('tbody tr, .history-item, .kj-item')
      if (rows.length > 0) {
        rows.each((_, element) => {
          const draw = parseRow($, $(element), type)
          if (draw && draw.period) {
            draws.push(draw)
          }
        })
      }
    } else {
      table.find('tbody tr, tr').each((_, element) => {
        const draw = parseRow($, $(element), type)
        if (draw && draw.period) {
          draws.push(draw)
        }
      })
    }

    if (draws.length === 0) {
      $('tr, .item, .row').each((_, element) => {
        const draw = parseRow($, $(element), type)
        if (draw && draw.period && draw.red && draw.red.length > 0) {
          draws.push(draw)
        }
      })
    }

    return draws
  } catch {
    return []
  }
}

const get8200Data = async (type: string, size: number = DATA_SOURCE_8200.defaultSize): Promise<any[]> => {
  const urlPath = DATA_SOURCE_8200.lotteryUrlMap[type as keyof typeof DATA_SOURCE_8200.lotteryUrlMap]
  if (!urlPath) {
    throw new Error(`不支持的彩种类型: ${type}`)
  }

  const axiosInstance = axios.create({
    baseURL: DATA_SOURCE_8200.baseUrl,
    ...REQUEST_CONFIG
  })

  try {
    const response = await axiosInstance.get(urlPath, {
      params: { size }
    })

    if (response.status !== 200) {
      throw new Error(`HTTP错误: ${response.status}`)
    }

    const draws = parse8200HTML(response.data, type)
    console.log(`解析${type}成功，获取到 ${draws.length} 期数据`)

    return draws
  } catch (error) {
    console.error(`获取${type}数据失败:`, (error as Error).message)
    throw error
  }
}

const validateDraw = (draw: any, type: string): boolean => {
  if (!draw.period) return false
  if (!draw.date) return false

  const red = draw.red || []
  const blue = draw.blue || []

  if (type === 'dlt') {
    return red.length === 5 && blue.length === 2
  } else if (type === 'ssq') {
    return red.length === 6 && blue.length === 1
  } else if (type === 'fc3d') {
    return red.length === 3
  } else if (type === 'pl3') {
    return red.length === 3
  } else if (type === 'pl5') {
    return red.length === 5
  } else if (type === 'qxc') {
    return red.length === 7
  } else if (type === 'qlc') {
    return red.length === 7 && blue.length === 1
  } else if (type === 'kl8') {
    return red.length === 20
  }

  return red.length > 0
}

const saveToDatabase = (type: string, draws: any[]): void => {
  const tableName = TABLE_MAP[type as keyof typeof TABLE_MAP]
  if (!tableName) return

  let successCount = 0

  draws.forEach(draw => {
    if (!validateDraw(draw, type)) {
      console.warn(`跳过无效数据: ${type} ${draw.period}`)
      return
    }

    try {
      const data: any = {
        id: draw.period,
        date: draw.date,
        numbers: draw.numbers
      }

      if (type === 'ssq') {
        data.red_numbers = draw.red
        data.blue_number = draw.blue[0]
      } else if (type === 'dlt') {
        data.front_numbers = draw.red
        data.back_numbers = draw.blue
      } else if (type === 'fc3d' || type === 'pl3') {
        data.numbers = draw.red
        data.type = '直选'
      } else if (type === 'pl5') {
        data.numbers = draw.red
      } else if (type === 'qxc') {
        data.numbers = draw.red
      } else if (type === 'qlc') {
        data.basic_numbers = draw.red
        data.special_number = draw.blue[0]
      } else if (type === 'kl8') {
        data.numbers = draw.red
      }

      insertOrReplace(tableName as any, data)
      successCount++
    } catch (error) {
      console.warn(`保存数据失败 (${type} ${draw.period}):`, (error as Error).message)
    }
  })

  if (successCount > 0) {
    console.log(`成功保存 ${type} ${successCount} 条数据`)
  }
}

const crawlByType = async (type: string): Promise<void> => {
  try {
    const draws = await get8200Data(type)
    saveToDatabase(type, draws)
  } catch (error) {
    console.error(`爬取${type}失败:`, (error as Error).message)
  }
}

export const crawlDoubleColorBall = async (): Promise<void> => {
  await crawlByType('ssq')
}

export const crawlSuperLotto = async (): Promise<void> => {
  await crawlByType('dlt')
}

export const crawlLottery3D = async (): Promise<void> => {
  await crawlByType('fc3d')
}

export const crawlHappy8 = async (): Promise<void> => {
  await crawlByType('kl8')
}

export const crawlArrangement3 = async (): Promise<void> => {
  await crawlByType('pl3')
}

export const crawlArrangement5 = async (): Promise<void> => {
  await crawlByType('pl5')
}

export const crawlSevenStar = async (): Promise<void> => {
  await crawlByType('qxc')
}

export const crawlSevenColor = async (): Promise<void> => {
  await crawlByType('qlc')
}

export const crawlAll = async (): Promise<void> => {
  const types = ['ssq', 'dlt', 'fc3d', 'kl8', 'pl3', 'pl5', 'qxc', 'qlc']
  
  for (let i = 0; i < types.length; i += 2) {
    const batch = types.slice(i, i + 2)
    await Promise.all(batch.map(crawlByType))
  }
}
