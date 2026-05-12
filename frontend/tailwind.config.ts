import type { Config } from 'tailwindcss'
import forms from '@tailwindcss/forms'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        card: '#111111',
        elevated: '#1a1a1a',
        border: '#333333',
        'g-blue': '#4285F4',
        'g-red': '#EA4335',
        'g-green': '#34A853',
      },
      fontFamily: {
        sans: ['Outfit', 'sans-serif'],
        mono: ['Outfit', 'sans-serif'],
      },
      animation: {
        shimmer: 'shimmer 1.5s infinite',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  plugins: [forms],
} satisfies Config
