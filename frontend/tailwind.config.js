/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        tinta: '#15294A',
        papel: '#F7F8F5',
        andino: '#2D6A8F',
        turquesa: '#178A99',
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
