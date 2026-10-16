/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        peach: { 50: '#FFF7F1', 100: '#FFEBDD', 300: '#FFC9A8', 500: '#F59E7A' },
        emerald: { 700: '#0F6B53', 800: '#0B4F3E', 900: '#063328' },
        ink: '#1C1B19',
      },
    },
  },
  plugins: [],
};