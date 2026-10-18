interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

class Cache<T> {
  private cache: Map<string, CacheEntry<T>> = new Map()

  set(key: string, data: T, ttl: number = 5 * 60 * 1000): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl
    }
    this.cache.set(key, entry)
  }

  get(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null

    const now = Date.now()
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return null
    }

    return entry.data
  }

  clear(): void {
    this.cache.clear()
  }

  delete(key: string): boolean {
    return this.cache.delete(key)
  }

  has(key: string): boolean {
    const entry = this.cache.get(key)
    if (!entry) return false

    const now = Date.now()
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return false
    }

    return true
  }
}

export const statisticsCache = new Cache<any>()
export const patternCache = new Cache<any>()
export const recommendationCache = new Cache<any>()

export const generateCacheKey = (lotteryType: string, ...params: any[]): string => {
  return `${lotteryType}_${params.map(p => JSON.stringify(p)).join('_')}`
}