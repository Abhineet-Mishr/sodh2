/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#1e1b4b',   // indigo-950
          primary: '#4c1d95', // violet-900
          accent: '#8b5cf6', // violet-500
          lavender: '#e9d5ff', // purple-200
          light: '#faf5ff', // fuchsia-50
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      }
    },
  },
  plugins: [require("tailwindcss-animate")],
}
