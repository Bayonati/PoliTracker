// Estado global del explorador (composable simple, sin Pinia: el estado es
// pequeño y así evitamos una dependencia).
import { reactive, computed } from 'vue'
import { apiGet } from '../api/client.js'

const state = reactive({
  anio: null,
  aniosDisponibles: [],
  ultimaIngesta: null,
  // path del drill-down: [] = sectores, [sector] = entidades, [sector, entidad] = tipos
  path: [],
  datos: null,        // respuesta del nivel actual
  cargando: false,
  error: null,
  cache: new Map(),   // clave "anio|nivel|path" -> respuesta (no re-pedir al volver)
})

const NIVELES = ['sectores', 'entidades', 'tipos']

const nivel = computed(() => state.path.length)
const nombreNivel = computed(() => NIVELES[nivel.value])

function claveCache() {
  return `${state.anio}|${state.path.join('>')}`
}

async function cargarNivel() {
  const clave = claveCache()
  if (state.cache.has(clave)) {
    state.datos = state.cache.get(clave)
    state.error = null
    return
  }
  state.cargando = true
  state.error = null
  try {
    const params = { anio: state.anio }
    if (state.path[0]) params.sector = state.path[0]
    if (state.path[1]) params.entidad = state.path[1]
    const datos = await apiGet(`/api/gasto/${nombreNivel.value}`, params)
    state.cache.set(clave, datos)
    state.datos = datos
  } catch (e) {
    state.error = e.message
    state.datos = null
  } finally {
    state.cargando = false
  }
}

async function inicializar() {
  try {
    const meta = await apiGet('/api/meta')
    state.aniosDisponibles = meta.anios
    state.ultimaIngesta = meta.ultima_ingesta
    state.anio = meta.anios[meta.anios.length - 1]
    await cargarNivel()
  } catch (e) {
    state.error = e.message
  }
}

async function cambiarAnio(anio) {
  state.anio = anio
  state.path = []
  await cargarNivel()
}

async function drillDown(nombre) {
  if (state.path.length >= 2) return // nivel 3 es el último
  state.path = [...state.path, nombre]
  await cargarNivel()
}

async function irANivel(profundidad) {
  // profundidad 0 = raíz (sectores); 1 = entidades del sector elegido; etc.
  state.path = state.path.slice(0, profundidad)
  await cargarNivel()
}

export function useExplorer() {
  return {
    state, nivel, nombreNivel,
    inicializar, cambiarAnio, drillDown, irANivel,
  }
}
