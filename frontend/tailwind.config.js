/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fincrew: {
          bg: '#EAF2FF',
          lime: '#C5F500',
          limeHover: '#b3e000',
          dark: '#17191F',
          darkCard: '#17191F',
          nearBlack: '#111318',
          slate: '#64748B',
          border: '#DCE7F6',
          card: '#FFFFFF',
          softBlue: '#F0F6FE',
        },
        lime: {
          brand: '#C5F500',
          hover: '#b3e000',
          light: '#d3f3b4',
          wall: '#d3f3b4',
          badge: '#C5F500',
        },
        forest: {
          floor: '#17191F',
          dark: '#101217',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      borderRadius: {
        'panel': '32px',
      },
      boxShadow: {
        'panel': '0 20px 50px -12px rgba(15, 23, 42, 0.12), 0 0 1px 1px rgba(0, 0, 0, 0.02)',
        'btn': '0 4px 14px 0 rgba(155, 217, 70, 0.35)',
      }
    },
  },
  plugins: [],
}
