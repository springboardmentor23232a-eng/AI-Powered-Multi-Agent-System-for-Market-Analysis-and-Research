/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        soc: {
          bg: '#070b14',
          panel: '#0d1424',
          panel2: '#111a2e',
          raised: '#16213a',
          border: '#1c2942',
          borderLight: '#263656',
          accent: '#3b82f6',
          accentBright: '#60a5fa',
          cyan: '#22d3ee',
          green: '#34d399',
          danger: '#f87171',
          warning: '#fbbf24',
          muted: '#8b9bb8',
          text: '#e6edf7',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      boxShadow: {
        card: '0 1px 3px rgba(0,0,0,0.4), 0 4px 16px rgba(2,6,23,0.5)',
        glow: '0 0 24px rgba(59,130,246,0.15)',
      },
    },
  },
  plugins: [],
}
