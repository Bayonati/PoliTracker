// Formateo de pesos colombianos en "escala ciudadana".
// OJO: en Colombia un billón = 10^12 (millón de millones), NO el billion gringo.

const BILLON = 1e12
const MIL_MILLONES = 1e9
const MILLON = 1e6

const nf1 = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const nf0 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 })

/**
 * Convierte un monto (string del API) a texto ciudadano: "$62,3 billones",
 * "$450 mil millones", "$87 millones".
 */
export function formatoCiudadano(monto) {
  const n = Number(monto)
  if (!Number.isFinite(n)) return '—'
  const abs = Math.abs(n)
  if (abs >= BILLON) return `$${nf1.format(n / BILLON)} billones`
  if (abs >= MIL_MILLONES) return `$${nf0.format(n / MIL_MILLONES)} mil millones`
  if (abs >= MILLON) return `$${nf0.format(n / MILLON)} millones`
  return `$${nf0.format(n)}`
}

/** Monto completo con separadores es-CO, para tablas y tooltips. */
export function formatoCompleto(monto) {
  const n = Number(monto)
  if (!Number.isFinite(n)) return '—'
  return `$${nf0.format(n)}`
}

/** Porcentaje con 1 decimal y coma decimal: "66,1 %". */
export function formatoPorcentaje(p) {
  if (!Number.isFinite(Number(p))) return '—'
  return `${nf1.format(Number(p))} %`
}

/** Frase ciudadana: "De cada $100 asignados, se han pagado $66". */
export function fraseEjecucion(porcentaje) {
  const p = Math.round(Number(porcentaje))
  if (!Number.isFinite(p)) return ''
  return `De cada $100 asignados, se han pagado $${p}`
}

export const NOMBRES_MES = [
  '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]
