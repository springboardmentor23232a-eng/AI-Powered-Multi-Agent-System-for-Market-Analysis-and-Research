/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fintech: {
          dark: '#05080a',
          card: '#0b0f15',
          cardBorder: '#1c2533',
          input: '#111620',
          inputBorder: '#1e293b',
          emerald: '#00d084',
          emeraldHover: '#00b875',
          emeraldDark: '#043825',
          teal: '#00cbb8',
          muted: '#8b98a5',
          textMuted: '#94a3b8',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

