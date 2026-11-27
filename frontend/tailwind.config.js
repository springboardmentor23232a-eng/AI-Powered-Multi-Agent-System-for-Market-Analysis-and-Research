/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: {
          50: '#FCFBF8',
          100: '#F6F5F0',
          200: '#EDEAE0',
          300: '#DFDBD0',
        },
        forest: {
          50: '#ECFDF5',
          100: '#D1FAE5',
          500: '#0D7A5F',
          600: '#0A624C',
          700: '#084C3B',
          800: '#06372B',
        },
        brand: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#0d7a5f',
          600: '#0a624c',
          700: '#084c3b',
          800: '#06372b',
          900: '#0f172a',
          950: '#071310',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['"Space Grotesk"', '"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
    },
  },
  plugins: [],
}
