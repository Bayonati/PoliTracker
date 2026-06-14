// Mapeo sector → color propio + ave colombiana (identidad visual Colombia Observa)
const MAPA = {
  'servicio de la deuda':            { color: '#1E3A5F', ave: 'Cóndor de los Andes' },
  'educacion':                        { color: '#178A99', ave: 'Barranquero' },
  'salud y proteccion social':        { color: '#4E8C2B', ave: 'Tángara real' },
  'defensa y policia':                { color: '#2E6FC9', ave: 'Águila harpía' },
  'trabajo':                          { color: '#D29A33', ave: 'Turpial' },
  'hacienda':                         { color: '#BC5630', ave: 'Tucán pico iris' },
  'inclusion social':                 { color: '#A83C80', ave: 'Colibrí esmeralda' },
  'transporte':                       { color: '#1E9E93', ave: 'Martín pescador' },
  'agricultura':                      { color: '#3F8A4C', ave: 'Guacamaya bandera' },
  'minas y energia':                  { color: '#C2901F', ave: 'Gallito de roca' },
  'rama judicial':                    { color: '#45539E', ave: 'Búho de anteojos' },
  'vivienda':                         { color: '#C5563B', ave: 'Carpintero real' },
  'justicia y del derecho':           { color: '#7E4F92', ave: 'Garza real' },
  'interior':                         { color: '#5F7A33', ave: 'Siririí' },
  'ciencia tecnologia e innovacion':  { color: '#1E9E93', ave: 'Quetzal' },
  'ambiente y desarrollo sostenible': { color: '#5F7A33', ave: 'Tucán esmeralda' },
  'comercio industria y turismo':     { color: '#C2901F', ave: 'Flamenco caribeño' },
  'cultura':                          { color: '#A83C80', ave: 'Pava caucana' },
  'deporte y recreacion':             { color: '#45539E', ave: 'Halcón peregrino' },
  'relaciones exteriores':            { color: '#BC5630', ave: 'Águila pescadora' },
  'tecnologias de la informacion':    { color: '#1E3A5F', ave: 'Loro orejiamarillo' },
  'presidencia':                      { color: '#C5563B', ave: 'Cóndor andino' },
  'planeacion':                       { color: '#3F8A4C', ave: 'Carpintero' },
  'informacion estadistica':          { color: '#45539E', ave: 'Mirla común' },
  'organismos de control':            { color: '#D29A33', ave: 'Gavilán caminero' },
  'registraduria':                    { color: '#178A99', ave: 'Paloma colorada' },
}

const FALLBACK = [
  '#1E3A5F','#178A99','#4E8C2B','#2E6FC9','#D29A33',
  '#BC5630','#A83C80','#1E9E93','#3F8A4C','#C2901F',
]

function normalize(str) {
  return (str || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function luminance(hex) {
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0, 2), 16) / 255
  const g = parseInt(h.slice(2, 4), 16) / 255
  const b = parseInt(h.slice(4, 6), 16) / 255
  return 0.299 * r + 0.587 * g + 0.114 * b
}

export function getSectorInfo(nombre) {
  const key = normalize(nombre)
  const found = MAPA[key]
  if (found) {
    return { ...found, textColor: luminance(found.color) > 0.42 ? '#15294A' : '#FFFFFF' }
  }
  const hash = [...(nombre || '')].reduce((a, c) => a + c.charCodeAt(0), 0)
  const color = FALLBACK[hash % FALLBACK.length]
  return { color, ave: 'Ave de Colombia', textColor: luminance(color) > 0.42 ? '#15294A' : '#FFFFFF' }
}
