/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        tinta: '#16233A',
        papel: '#FAFBFC',
        andino: '#2D6A8F',
        oro: '#E9B44C',
        ejecutado: '#2E8B57',
        alerta: '#C0392B',
        neutro: '#6B7686',
      },
      fontFamily: {
        display: ['Archivo', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
