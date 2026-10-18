import axios from 'axios'
import cheerio from 'cheerio'
import { insertOrReplace } from '../database'

const BASE_URL = 'https://www.zhcw.com'

export const crawlDoubleColorBall = async (): Promise<void> => {
  try {
    const response = await axios.get(`${BASE_URL}/ssq/kjgg/`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': BASE_URL
      },
      timeout: 15000
    })

    const $ = cheerio.load(response.data)
    const rows = $('.kjgg_list tr').slice(1)

    rows.each((_, row) => {
      const tds = $(row).find('td')
      const id = $(tds[0]).text().trim()
      const date = $(tds[1]).text().trim()
      const numbers = $(tds[2]).text().trim()
      
      if (!id || !date || !numbers) return

      const parts = numbers.split(' ')
      const redNumbers = parts.slice(0, 6).map(Number)
      const blueNumber = parseInt(parts[6])

      if (redNumbers.length === 6 && blueNumber > 0) {
        insertOrReplace('double_color_ball', {
          id,
          date,
          red_numbers: redNumbers,
          blue_number: blueNumber
        })
      }
    })

    console.log('Crawled Double Color Ball data successfully from zhcw')
  } catch (error) {
    console.error('Error crawling Double Color Ball from zhcw:', error)
  }
}

export const crawlSuperLotto = async (): Promise<void> => {
  try {
    const response = await axios.get(`${BASE_URL}/dlt/kjgg/`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': BASE_URL
      },
      timeout: 15000
    })

    const $ = cheerio.load(response.data)
    const rows = $('.kjgg_list tr').slice(1)

    rows.each((_, row) => {
      const tds = $(row).find('td')
      const id = $(tds[0]).text().trim()
      const date = $(tds[1]).text().trim()
      const numbers = $(tds[2]).text().trim()

      if (!id || !date || !numbers) return

      const parts = numbers.split(' ')
      const frontNumbers = parts.slice(0, 5).map(Number)
      const backNumbers = parts.slice(5, 7).map(Number)

      if (frontNumbers.length === 5 && backNumbers.length === 2) {
        insertOrReplace('super_lotto', {
          id,
          date,
          front_numbers: frontNumbers,
          back_numbers: backNumbers
        })
      }
    })

    console.log('Crawled Super Lotto data successfully from zhcw')
  } catch (error) {
    console.error('Error crawling Super Lotto from zhcw:', error)
  }
}

export const crawlLottery3D = async (): Promise<void> => {
  try {
    const response = await axios.get(`${BASE_URL}/3d/kjgg/`, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': BASE_URL
      },
      timeout: 15000
    })

    const $ = cheerio.load(response.data)
    const rows = $('.kjgg_list tr').slice(1)

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

    console.log('Crawled Lottery 3D data successfully from zhcw')
  } catch (error) {
    console.error('Error crawling Lottery 3D from zhcw:', error)
  }
}