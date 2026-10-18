import axios from 'axios'
import cheerio from 'cheerio'
import { insertOrReplace } from '../database'

const BASE_URL = 'https://kaijiang.500.com'

export const crawlDoubleColorBall500 = async (): Promise<void> => {
  try {
    const response = await axios.get(`${BASE_URL}/ssq.shtml`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': BASE_URL
      },
      timeout: 15000
    })

    const $ = cheerio.load(response.data)
    const historyTable = $('.iDataTable') || $('#tablelist')
    const rows = historyTable.find('tr').slice(1)

    if (rows.length === 0) {
      console.log('No data found for Double Color Ball on 500.com')
      return
    }

    rows.each((_, row) => {
      const tds = $(row).find('td')
      const id = $(tds[0]).text().trim()
      const date = $(tds[1]).text().trim()
      const balls = $(row).find('.ball_red, .ball_blue')

      if (!id || !date) return

      const redNumbers: number[] = []
      let blueNumber = 0

      balls.each((i, ball) => {
        const num = parseInt($(ball).text().trim())
        if (!isNaN(num)) {
          if (i < 6) {
            redNumbers.push(num)
          } else {
            blueNumber = num
          }
        }
      })

      if (redNumbers.length === 6 && blueNumber > 0) {
        insertOrReplace('double_color_ball', {
          id,
          date,
          red_numbers: redNumbers,
          blue_number: blueNumber
        })
      }
    })

    console.log('Crawled Double Color Ball from 500.com successfully')
  } catch (error) {
    console.error('Error crawling Double Color Ball from 500.com:', error)
  }
}

export const crawlSuperLotto500 = async (): Promise<void> => {
  try {
    const response = await axios.get(`${BASE_URL}/dlt.shtml`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': BASE_URL
      },
      timeout: 15000
    })

    const $ = cheerio.load(response.data)
    const historyTable = $('.iDataTable') || $('#tablelist')
    const rows = historyTable.find('tr').slice(1)

    if (rows.length === 0) {
      console.log('No data found for Super Lotto on 500.com')
      return
    }

    rows.each((_, row) => {
      const tds = $(row).find('td')
      const id = $(tds[0]).text().trim()
      const date = $(tds[1]).text().trim()
      const balls = $(row).find('.ball_red, .ball_blue')

      if (!id || !date) return

      const frontNumbers: number[] = []
      const backNumbers: number[] = []

      balls.each((i, ball) => {
        const num = parseInt($(ball).text().trim())
        if (!isNaN(num)) {
          if (i < 5) {
            frontNumbers.push(num)
          } else {
            backNumbers.push(num)
          }
        }
      })

      if (frontNumbers.length === 5 && backNumbers.length === 2) {
        insertOrReplace('super_lotto', {
          id,
          date,
          front_numbers: frontNumbers,
          back_numbers: backNumbers
        })
      }
    })

    console.log('Crawled Super Lotto from 500.com successfully')
  } catch (error) {
    console.error('Error crawling Super Lotto from 500.com:', error)
  }
}

export const crawlLottery3D500 = async (): Promise<void> => {
  try {
    const response = await axios.get(`${BASE_URL}/3d/`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': BASE_URL
      },
      timeout: 15000
    })

    const $ = cheerio.load(response.data)
    const historyTable = $('.iDataTable') || $('#tablelist')
    const rows = historyTable.find('tr').slice(1)

    if (rows.length === 0) {
      console.log('No data found for Lottery 3D on 500.com')
      return
    }

    rows.each((_, row) => {
      const tds = $(row).find('td')
      const id = $(tds[0]).text().trim()
      const date = $(tds[1]).text().trim()
      const numbers = $(tds[2]).text().trim()

      if (!id || !date || !numbers) return

      const numberArray = numbers.split('').map(Number).filter(n => !isNaN(n))

      if (numberArray.length === 3) {
        insertOrReplace('lottery_3d', {
          id,
          date,
          numbers: numberArray,
          type: '直选'
        })
      }
    })

    console.log('Crawled Lottery 3D from 500.com successfully')
  } catch (error) {
    console.error('Error crawling Lottery 3D from 500.com:', error)
  }
}