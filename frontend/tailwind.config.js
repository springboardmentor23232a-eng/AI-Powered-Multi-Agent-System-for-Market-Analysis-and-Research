/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'Courier New', 'monospace'],
      },
      colors: {
        charcoal: {
          950: '#060608', // Deepest background
          900: '#0a0a0e', // Primary dark background
          850: '#0e0e14', // Elevated surface
          800: '#14141c', // Card background
          750: '#1a1a24', // Card hover / border
          700: '#22222e', // Divider / border
          600: '#323242',
          500: '#525266',
        },
        crimson: {
          50:  '#fff1f2',
          100: '#ffe4e6',
          200: '#fecdd3',
          300: '#fda4af',
          400: '#fb7185',
          500: '#f43f5e',
          600: '#e11d48', // Nexora primary red accent
          700: '#be123c',
          800: '#9f1239',
          900: '#881337',
          950: '#4c0519',
        },
        brand: {
          primary: '#e11d48',
          hover: '#f43f5e',
          accent: '#ef4444',
          dark: '#0a0a0e',
          card: '#111116',
          border: 'rgba(255, 255, 255, 0.08)',
        },
      },
      boxShadow: {
        'crimson-sm': '0 0 15px -3px rgba(225, 29, 72, 0.25)',
        'crimson-md': '0 0 25px -4px rgba(225, 29, 72, 0.35)',
        'crimson-lg': '0 0 45px -5px rgba(225, 29, 72, 0.45)',
        'card-dark': '0 20px 40px -15px rgba(0, 0, 0, 0.8)',
      },
      animation: {
        'spin-slow': 'spin 1.4s linear infinite',
        'fade-in':   'fadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
        'pulse-subtle': 'pulseSubtle 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)'   },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '0.9' },
          '50%': { opacity: '0.6' },
        },
      },
    },
  },
  plugins: [],
};
