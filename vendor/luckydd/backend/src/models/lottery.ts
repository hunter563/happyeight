export interface DoubleColorBall {
  id: string
  date: string
  redNumbers: number[]
  blueNumber: number
  prizeLevel?: {
    level1: number
    level2: number
    prizePool: string
  }
}

export interface SuperLotto {
  id: string
  date: string
  frontNumbers: number[]
  backNumbers: number[]
  prizeLevel?: {
    level1: number
    level2: number
    prizePool: string
  }
}

export interface Lottery3D {
  id: string
  date: string
  numbers: number[]
  type?: string
}

export interface Happy8 {
  id: string
  date: string
  numbers: number[]
}

export interface Arrangement3 {
  id: string
  date: string
  numbers: number[]
  type?: string
}

export interface Arrangement5 {
  id: string
  date: string
  numbers: number[]
}

export interface SevenStar {
  id: string
  date: string
  numbers: number[]
}

export interface SevenColor {
  id: string
  date: string
  basicNumbers: number[]
  specialNumber: number
}

export type LotteryType = 'double_color_ball' | 'super_lotto' | 'lottery_3d' | 'happy_8' | 'arrangement_3' | 'arrangement_5' | 'seven_star' | 'seven_color'