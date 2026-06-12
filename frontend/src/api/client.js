// Wrapper de fetch con base URL configurable por entorno.
const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function apiGet(path, params = {}) {
  const url = new URL(path, BASE)
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
  }
  const resp = await fetch(url)
  if (!resp.ok) {
    let detalle = `Error ${resp.status}`
    try {
      const body = await resp.json()
      if (body.detail) detalle = body.detail
    } catch { /* respuesta sin JSON */ }
    throw new Error(detalle)
  }
  return resp.json()
}
