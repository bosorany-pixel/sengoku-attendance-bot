/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['Outfit', 'system-ui', 'sans-serif'],
        sans: ['Outfit', 'system-ui', 'sans-serif'],
      },
      colors: {
        dark: {
          bg: '#1e1e1e',
          card: '#2a2a2a',
          border: '#444',
          text: '#e0e0e0',
          textLight: '#bbbbbb',
        },
        accent: {
          blue: '#7aa2f7',
          green: '#00ff88',
        }
      },
    },
  },
  plugins: [],
}
