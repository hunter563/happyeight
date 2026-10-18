import fs from 'fs'
import path from 'path'

const DATA_DIR = path.join(__dirname, 'data')
const DB_FILE = path.join(DATA_DIR, 'database.json')

interface TableData {
  double_color_ball: any[]
  super_lotto: any[]
  lottery_3d: any[]
  happy_8: any[]
  arrangement_3: any[]
  arrangement_5: any[]
  seven_star: any[]
  seven_color: any[]
  crawler_log: any[]
}

let db: TableData = {
  double_color_ball: [],
  super_lotto: [],
  lottery_3d: [],
  happy_8: [],
  arrangement_3: [],
  arrangement_5: [],
  seven_star: [],
  seven_color: [],
  crawler_log: []
}

export const initDatabase = (): void => {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true })
  }

  if (fs.existsSync(DB_FILE)) {
    try {
      const content = fs.readFileSync(DB_FILE, 'utf-8')
      const existing = JSON.parse(content)
      db = { ...db, ...existing }
    } catch {
      db = {
        double_color_ball: [],
        super_lotto: [],
        lottery_3d: [],
        happy_8: [],
        arrangement_3: [],
        arrangement_5: [],
        seven_star: [],
        seven_color: [],
        crawler_log: []
      }
    }
  }
}

const saveDatabase = (): void => {
  fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2))
}

export const insertOrReplace = (table: keyof TableData, data: any): void => {
  const tableData = db[table]
  const idField = table === 'crawler_log' ? 'id' : 'id'
  
  const index = tableData.findIndex(item => item[idField] === data[idField])
  if (index >= 0) {
    tableData[index] = { ...tableData[index], ...data }
  } else {
    tableData.push(data)
  }
  
  saveDatabase()
}

export const query = (table: keyof TableData, options?: {
  limit?: number
  offset?: number
  orderBy?: string
  order?: 'ASC' | 'DESC'
}): any[] => {
  let result = [...db[table]]
  
  if (options?.orderBy) {
    const field = options.orderBy as string
    result.sort((a, b) => {
      const aVal = a[field]
      const bVal = b[field]
      if (options.order === 'DESC') {
        return aVal < bVal ? 1 : aVal > bVal ? -1 : 0
      }
      return aVal < bVal ? -1 : aVal > bVal ? 1 : 0
    })
  }
  
  if (options?.offset !== undefined) {
    result = result.slice(options.offset)
  }
  
  if (options?.limit !== undefined) {
    result = result.slice(0, options.limit)
  }
  
  return result
}

export const count = (table: keyof TableData): number => {
  return db[table].length
}

export const getAll = (table: keyof TableData): any[] => {
  return [...db[table]]
}

export const getLatest = (table: keyof TableData): any | null => {
  const result = query(table, { limit: 1, orderBy: 'date', order: 'DESC' })
  return result.length > 0 ? result[0] : null
}