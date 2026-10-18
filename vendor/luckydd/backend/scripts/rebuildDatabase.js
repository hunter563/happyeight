const fs = require('fs');
const path = require('path');
const axios = require('axios');
const cheerio = require('cheerio');

const DATABASE_PATH = path.join(__dirname, '../data/database.json');

const crawlerConfigs = [
  {
    name: '双色球',
    url: 'https://www.8200.cn/kjh/ssq/history.htm?size=300',
    lotteryType: 'double_color_ball',
    parseFunction: (html) => {
      const $ = cheerio.load(html);
      const data = [];
      $('.kjhTable tbody tr').each((_, row) => {
        const cells = $(row).find('td');
        if (cells.length < 9) return;
        const issue = cells.eq(0).text().trim();
        const dateStr = cells.eq(1).text().trim();
        const year = issue.substring(0, 4);
        const match = dateStr.match(/(\d{2})-(\d{2})/);
        const drawDate = match ? `${year}-${match[1]}-${match[2]}` : dateStr;
        const redNumbers = [];
        let blueNumber = 0;
        const numCell = cells.eq(2).text().trim();
        const redMatch = numCell.match(/(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})/);
        const blueMatch = numCell.match(/\+\s*(\d{2})/);
        if (redMatch) {
          for (let i = 1; i <= 6; i++) redNumbers.push(parseInt(redMatch[i]));
        }
        if (blueMatch) {
          blueNumber = parseInt(blueMatch[1]);
        }
        if (redNumbers.length === 6 && blueNumber > 0) {
          data.push({ id: issue, date: drawDate, red_numbers: redNumbers, blue_number: blueNumber, numbers: [...redNumbers, blueNumber] });
        }
      });
      return data;
    }
  },
  {
    name: '大乐透',
    url: 'https://www.8200.cn/kjh/dlt/history.htm?size=300',
    lotteryType: 'super_lotto',
    parseFunction: (html) => {
      const $ = cheerio.load(html);
      const data = [];
      $('.kjhTable tbody tr').each((_, row) => {
        const cells = $(row).find('td');
        if (cells.length < 9) return;
        const issue = cells.eq(0).text().trim();
        const dateStr = cells.eq(1).text().trim();
        const year = issue.length === 5 ? '20' + issue.substring(0, 2) : issue.substring(0, 4);
        const match = dateStr.match(/(\d{2})-(\d{2})/);
        const drawDate = match ? `${year}-${match[1]}-${match[2]}` : dateStr;
        const numCell = cells.eq(2).text().trim();
        const frontMatch = numCell.match(/(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})\s+(\d{2})/);
        const backMatch = numCell.match(/\+\s*(\d{2})\s+(\d{2})/);
        const frontNumbers = frontMatch ? frontMatch.slice(1, 6).map(Number) : [];
        const backNumbers = backMatch ? backMatch.slice(1, 3).map(Number) : [];
        if (frontNumbers.length === 5 && backNumbers.length === 2) {
          data.push({ id: issue, date: drawDate, front_numbers: frontNumbers, back_numbers: backNumbers, numbers: [...frontNumbers, ...backNumbers] });
        }
      });
      return data;
    }
  },
  {
    name: '福彩3D',
    url: 'https://www.8200.cn/kjh/3d/history.htm?size=300',
    lotteryType: 'lottery_3d',
    parseFunction: (html) => {
      const $ = cheerio.load(html);
      const data = [];
      $('.kjhTable tbody tr').each((_, row) => {
        const cells = $(row).find('td');
        if (cells.length < 5) return;
        const issue = cells.eq(0).text().trim();
        const dateStr = cells.eq(1).text().trim();
        const year = issue.substring(0, 4);
        const match = dateStr.match(/(\d{2})-(\d{2})/);
        const drawDate = match ? `${year}-${match[1]}-${match[2]}` : dateStr;
        const numCell = cells.eq(2).text().trim();
        const numMatch = numCell.match(/(\d)\s+(\d)\s+(\d)/);
        const numbers = numMatch ? numMatch.slice(1, 4).map(Number) : [];
        if (numbers.length === 3) {
          data.push({ id: issue, date: drawDate, numbers });
        }
      });
      return data;
    }
  },
  {
    name: '快乐8',
    url: 'https://www.8200.cn/kjh/kl8/history.htm?size=300',
    lotteryType: 'happy_8',
    parseFunction: (html) => {
      const $ = cheerio.load(html);
      const data = [];
      $('.kjhTable tbody tr').each((_, row) => {
        const cells = $(row).find('td');
        if (cells.length < 3) return;
        const issue = cells.eq(0).text().trim();
        const dateStr = cells.eq(1).text().trim();
        const year = issue.substring(0, 4);
        const match = dateStr.match(/(\d{2})-(\d{2})/);
        const drawDate = match ? `${year}-${match[1]}-${match[2]}` : dateStr;
        const numCell = cells.eq(2).text().trim();
        const numMatches = numCell.match(/(\d{2})/g) || [];
        const numbers = numMatches.slice(0, 20).map(Number);
        if (numbers.length === 20) {
          data.push({ id: issue, date: drawDate, numbers });
        }
      });
      return data;
    }
  },
  {
    name: '排列3',
    url: 'https://www.8200.cn/kjh/p3/history.htm?size=300',
    lotteryType: 'arrangement_3',
    parseFunction: (html) => {
      const $ = cheerio.load(html);
      const data = [];
      $('.kjhTable tbody tr').each((_, row) => {
        const cells = $(row).find('td');
        if (cells.length < 5) return;
        const issue = cells.eq(0).text().trim();
        const dateStr = cells.eq(1).text().trim();
        const year = issue.length === 5 ? '20' + issue.substring(0, 2) : issue.substring(0, 4);
        const match = dateStr.match(/(\d{2})-(\d{2})/);
        const drawDate = match ? `${year}-${match[1]}-${match[2]}` : dateStr;
        const numCell = cells.eq(2).text().trim();
        const numMatch = numCell.match(/(\d)\s+(\d)\s+(\d)/);
        const numbers = numMatch ? numMatch.slice(1, 4).map(Number) : [];
        if (numbers.length === 3) {
          data.push({ id: issue, date: drawDate, numbers });
        }
      });
      return data;
    }
  },
  {
    name: '排列5',
    url: 'https://www.8200.cn/kjh/p5/history.htm?size=300',
    lotteryType: 'arrangement_5',
    parseFunction: (html) => {
      const $ = cheerio.load(html);
      const data = [];
      $('.kjhTable tbody tr').each((_, row) => {
        const cells = $(row).find('td');
        if (cells.length < 7) return;
        const issue = cells.eq(0).text().trim();
        const dateStr = cells.eq(1).text().trim();
        const year = issue.length === 5 ? '20' + issue.substring(0, 2) : issue.substring(0, 4);
        const match = dateStr.match(/(\d{2})-(\d{2})/);
        const drawDate = match ? `${year}-${match[1]}-${match[2]}` : dateStr;
        const numCell = cells.eq(2).text().trim();
        const numMatch = numCell.match(/(\d)\s+(\d)\s+(\d)\s+(\d)\s+(\d)/);
        const numbers = numMatch ? numMatch.slice(1, 6).map(Number) : [];
        if (numbers.length === 5) {
          data.push({ id: issue, date: drawDate, numbers });
        }
      });
      return data;
    }
  },
  {
    name: '七星彩',
    url: 'https://www.8200.cn/kjh/qxc/history.htm?size=300',
    lotteryType: 'seven_star',
    parseFunction: (html) => {
      const $ = cheerio.load(html);
      const data = [];
      $('.kjhTable tbody tr').each((_, row) => {
        const cells = $(row).find('td');
        if (cells.length < 9) return;
        const issue = cells.eq(0).text().trim();
        const dateStr = cells.eq(1).text().trim();
        const year = issue.length === 5 ? '20' + issue.substring(0, 2) : issue.substring(0, 4);
        const match = dateStr.match(/(\d{2})-(\d{2})/);
        const drawDate = match ? `${year}-${match[1]}-${match[2]}` : dateStr;
        const numCell = cells.eq(2).text().trim();
        const numMatches = numCell.match(/(\d)/g) || [];
        const numbers = numMatches.slice(0, 7).map(Number);
        if (numbers.length === 7) {
          data.push({ id: issue, date: drawDate, numbers });
        }
      });
      return data;
    }
  },
  {
    name: '七乐彩',
    url: 'https://www.8200.cn/kjh/qlc/history.htm?size=300',
    lotteryType: 'seven_color',
    parseFunction: (html) => {
      const $ = cheerio.load(html);
      const data = [];
      $('.kjhTable tbody tr').each((_, row) => {
        const cells = $(row).find('td');
        if (cells.length < 9) return;
        const issue = cells.eq(0).text().trim();
        const dateStr = cells.eq(1).text().trim();
        const year = issue.substring(0, 4);
        const match = dateStr.match(/(\d{2})-(\d{2})/);
        const drawDate = match ? `${year}-${match[1]}-${match[2]}` : dateStr;
        const numCell = cells.eq(2).text().trim();
        const numMatches = numCell.match(/(\d{2})/g) || [];
        const basicNumbers = numMatches.slice(0, 7).map(Number);
        const specialNumber = numMatches.length >= 8 ? parseInt(numMatches[7]) : 0;
        if (basicNumbers.length === 7 && specialNumber > 0) {
          data.push({ id: issue, date: drawDate, basic_numbers: basicNumbers, special_number: specialNumber, numbers: [...basicNumbers, specialNumber] });
        }
      });
      return data;
    }
  }
];

const fetchData = async (config) => {
  try {
    const response = await axios.get(config.url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' },
      timeout: 10000
    });
    return config.parseFunction(response.data);
  } catch (error) {
    console.error(`抓取 ${config.name} 失败:`, error.message);
    return [];
  }
};

const rebuildDatabase = async () => {
  const db = {};
  
  for (const config of crawlerConfigs) {
    console.log(`正在抓取 ${config.name}...`);
    const data = await fetchData(config);
    if (data.length > 0) {
      db[config.lotteryType] = data.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
      console.log(`${config.name}: 获取到 ${data.length} 条数据`);
    } else {
      db[config.lotteryType] = [];
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  fs.writeFileSync(DATABASE_PATH, JSON.stringify(db, null, 2), 'utf-8');
  console.log('数据库重建完成！');
};

rebuildDatabase();