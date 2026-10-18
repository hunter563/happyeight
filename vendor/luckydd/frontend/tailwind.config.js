/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        red: {
          DEFAULT: '#ef4444',
          100: '#fee2e2',
          500: '#ef4444',
          600: '#dc2626',
        },
        blue: {
          DEFAULT: '#3b82f6',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
        },
        green: {
          DEFAULT: '#22c55e',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
        },
        yellow: {
          DEFAULT: '#eab308',
          100: '#fef9c3',
          500: '#eab308',
          600: '#ca8a04',
        },
        purple: {
          DEFAULT: '#a855f7',
          100: '#f3e8ff',
          500: '#a855f7',
          600: '#9333ea',
        }
      }
    },
  },
  plugins: [],
}