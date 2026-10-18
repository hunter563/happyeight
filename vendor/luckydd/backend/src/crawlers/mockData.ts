import { insertOrReplace } from '../database'

const generateRandomNumbers = (min: number, max: number, count: number): number[] => {
  const numbers: number[] = []
  while (numbers.length < count) {
    const num = Math.floor(Math.random() * (max - min + 1)) + min
    if (!numbers.includes(num)) {
      numbers.push(num)
    }
  }
  return numbers.sort((a, b) => a - b)
}

const generateDate = (offset: number): string => {
  const date = new Date()
  date.setDate(date.getDate() - offset)
  return date.toISOString().split('T')[0]
}

export const generateMockData = (): void => {
  const today = new Date()
  
  for (let i = 0; i < 30; i++) {
    const date = generateDate(i)
    const month = String(today.getMonth() + 1).padStart(2, '0')
    const day = String(today.getDate() - i).padStart(2, '0')
    
    insertOrReplace('double_color_ball', {
      id: `2026${String(i + 1).padStart(3, '0')}`,
      date,
      red_numbers: generateRandomNumbers(1, 33, 6),
      blue_number: Math.floor(Math.random() * 16) + 1
    })

    insertOrReplace('super_lotto', {
      id: `2026${String(i + 1).padStart(3, '0')}`,
      date: i % 3 === 0 ? date : '',
      front_numbers: generateRandomNumbers(1, 35, 5),
      back_numbers: generateRandomNumbers(1, 12, 2)
    })

    insertOrReplace('lottery_3d', {
      id: `2026${String(i + 1).padStart(3, '0')}`,
      date,
      numbers: [Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10)],
      type: '直选'
    })

    insertOrReplace('happy_8', {
      id: `2026${String(i + 1).padStart(3, '0')}`,
      date,
      numbers: generateRandomNumbers(1, 80, 20)
    })

    insertOrReplace('arrangement_3', {
      id: `2026${String(i + 1).padStart(3, '0')}`,
      date: i % 2 === 0 ? date : '',
      numbers: [Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10)],
      type: '直选'
    })

    insertOrReplace('arrangement_5', {
      id: `2026${String(i + 1).padStart(3, '0')}`,
      date: i % 2 === 0 ? date : '',
      numbers: [Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10)]
    })

    insertOrReplace('seven_star', {
      id: `2026${String(i + 1).padStart(3, '0')}`,
      date: i % 3 === 0 ? date : '',
      numbers: [Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10), Math.floor(Math.random() * 10)]
    })

    insertOrReplace('seven_color', {
      id: `2026${String(i + 1).padStart(3, '0')}`,
      date: i % 3 === 1 ? date : '',
      basic_numbers: generateRandomNumbers(1, 30, 7),
      special_number: Math.floor(Math.random() * 30) + 1
    })
  }

  console.log('Mock data generated successfully')
}
