export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Bricolage Grotesque"', 'system-ui', 'sans-serif'],
        serif: ['Newsreader', 'Georgia', 'serif'],
      },
      colors: {
        cobalt: { DEFAULT: '#2430D6', deep: '#1A24AD' },
        ink: '#0C1030',
        paper: '#F2F3F5',
        line: '#D9DCE3',
        mute: '#5B6180',
        gain: '#0B8A57',
        loss: '#D4302B',
        amber: '#A96A00',
        mark: '#FFE14D',
      },
    },
  },
  plugins: [],
}
