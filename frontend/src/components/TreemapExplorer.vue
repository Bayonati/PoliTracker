<script setup>
// D3 calcula el layout; Vue renderiza divs absolutos sobre un contenedor responsive.
// Un único treemap para desktop Y móvil — sin bifurcación de vistas.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { hierarchy, treemap, treemapSquarify } from 'd3-hierarchy'
import { formatoCiudadano, formatoPorcentaje, fraseEjecucion } from '../utils/formato.js'
import { getSectorInfo } from '../utils/sectorInfo.js'

const props = defineProps({
  items:        { type: Array,   required: true },
  esUltimoNivel:{ type: Boolean, default: false },
})
const emit = defineEmits(['drill', 'subir'])

// Dimensiones reales del contenedor (px) — las actualiza el ResizeObserver
const ancho = ref(600)
const alto  = ref(336)

const contenedor  = ref(null)
const tooltip     = ref(null)   // { x, y, item }
const otrosAbierto = ref(false)
const focoIdx     = ref(-1)

let observador = null

onMounted(() => {
  observador = new ResizeObserver(([entry]) => {
    const w = entry.contentRect.width
    const h = entry.contentRect.height
    ancho.value = Math.max(240, w)
    // La altura CSS usa clamp(180px, 56vw, 560px); aquí la reflejamos exactamente
    alto.value  = Math.max(180, h || Math.round(w * 0.56))
  })
  observador.observe(contenedor.value)
})
onBeforeUnmount(() => observador?.disconnect())

// ── Agrupa los ítems <1% en un bloque "Otros" ──────────────────────────────
const agrupados = computed(() => {
  const grandes = props.items.filter(i => i.porcentaje_del_total >= 1)
  const chicos  = props.items.filter(i => i.porcentaje_del_total <  1)
  const nodos   = grandes.map(i => ({ ...i, esOtros: false }))
  if (chicos.length > 1) {
    nodos.push({
      nombre:            `Otros (${chicos.length})`,
      apropiado:         String(chicos.reduce((s, i) => s + Number(i.apropiado), 0)),
      pagado:            String(chicos.reduce((s, i) => s + Number(i.pagado), 0)),
      porcentaje_del_total: Math.round(chicos.reduce((s, i) => s + i.porcentaje_del_total, 0) * 10) / 10,
      porcentaje_ejecucion: 0,
      esOtros:           true,
      hijos:             chicos,
    })
  } else if (chicos.length === 1) {
    nodos.push({ ...chicos[0], esOtros: false })
  }
  return nodos
})

const itemsOtros = computed(() =>
  agrupados.value.find(n => n.esOtros)?.hijos ?? [])

// ── Layout D3 → posiciones en % para CSS ───────────────────────────────────
const rects = computed(() => {
  if (!ancho.value || !alto.value) return []

  const raiz = hierarchy({ children: agrupados.value })
    .sum(d => Number(d.apropiado) || 0)
    .sort((a, b) => b.value - a.value)

  treemap()
    .tile(treemapSquarify)
    .size([ancho.value, alto.value])
    .paddingInner(3)(raiz)

  return (raiz.children ?? []).map(n => ({
    item:   n.data,
    pw:     n.x1 - n.x0,         // ancho en px (para thresholds de texto)
    ph:     n.y1 - n.y0,         // alto en px
    left:   (n.x0           / ancho.value * 100).toFixed(3),
    top:    (n.y0           / alto.value  * 100).toFixed(3),
    width:  ((n.x1 - n.x0)  / ancho.value * 100).toFixed(3),
    height: ((n.y1 - n.y0)  / alto.value  * 100).toFixed(3),
  }))
})

// ── Color y ave por sector ──────────────────────────────────────────────────
function infoColor(item) {
  if (item.esOtros) return { color: '#9AA2AE', textColor: '#15294A', ave: null }
  return getSectorInfo(item.nombre)
}

// Tamaños de fuente escalados al ancho real del bloque
function labelSize(pw) { return Math.max(9,  Math.min(13, pw / 16)) + 'px' }
function valueSize(pw) { return Math.max(11, Math.min(26, pw / 11)) + 'px' }

// ── Interacción ────────────────────────────────────────────────────────────
function clickNodo(item) {
  if (item.esOtros)          { otrosAbierto.value = !otrosAbierto.value }
  else if (!props.esUltimoNivel) { emit('drill', item.nombre) }
}

function moverTooltip(ev, item) {
  const caja = contenedor.value.getBoundingClientRect()
  tooltip.value = {
    x:    Math.min(ev.clientX - caja.left + 12, caja.width - 270),
    y:    ev.clientY - caja.top  + 12,
    item,
  }
}

function colorDeNombre(nombre) { return getSectorInfo(nombre).color }

// Navegación por teclado: flechas / Enter / Escape
function tecla(ev) {
  const n = rects.value.length
  if (!n) return
  if      (ev.key === 'ArrowRight' || ev.key === 'ArrowDown')  { focoIdx.value = (focoIdx.value + 1) % n;       ev.preventDefault() }
  else if (ev.key === 'ArrowLeft'  || ev.key === 'ArrowUp')    { focoIdx.value = (focoIdx.value - 1 + n) % n;   ev.preventDefault() }
  else if (ev.key === 'Enter' && focoIdx.value >= 0)           { clickNodo(rects.value[focoIdx.value].item);      ev.preventDefault() }
  else if (ev.key === 'Escape')                                 { emit('subir');                                   ev.preventDefault() }
}
</script>

<template>
  <div ref="contenedor" class="relative w-full select-none" @keydown="tecla">

    <!--
      Contenedor del treemap.
      height usa clamp para que sea usable tanto en móvil (180 px mínimo)
      como en escritorio (560 px máximo), proporcional al ancho disponible.
    -->
    <div
      class="relative w-full rounded-xl overflow-hidden"
      style="height: clamp(180px, 56vw, 560px); background: #EEF1EB;"
      role="group"
      aria-label="Treemap del presupuesto. Flechas para moverse, Enter para entrar, Escape para subir."
      tabindex="0"
    >
      <!-- Un div por bloque, posicionado en % ────────────────────────────── -->
      <div
        v-for="(r, i) in rects"
        :key="r.item.nombre"
        class="absolute overflow-hidden rounded-lg"
        :style="{
          left:       r.left   + '%',
          top:        r.top    + '%',
          width:      r.width  + '%',
          height:     r.height + '%',
          background: infoColor(r.item).color,
          color:      infoColor(r.item).textColor,
          padding:    '8px 10px',
          boxSizing:  'border-box',
          display:    'flex',
          flexDirection: 'column',
          gap:        '2px',
          cursor:     r.item.esOtros || !esUltimoNivel ? 'pointer' : 'default',
          outline:    focoIdx === i ? '3px solid #E9B44C' : 'none',
          outlineOffset: '-2px',
          transition: 'left .3s ease-out, top .3s ease-out, width .3s ease-out, height .3s ease-out',
        }"
        @click="clickNodo(r.item)"
        @mousemove="moverTooltip($event, r.item)"
        @mouseleave="tooltip = null"
      >
        <!-- Nombre + pluma decorativa (si el bloque tiene espacio) -->
        <div
          v-if="r.pw > 52"
          class="flex items-center gap-1 overflow-hidden font-bold uppercase leading-tight tracking-wide"
          :style="{ fontSize: labelSize(r.pw) }"
        >
          <span
            v-if="!r.item.esOtros"
            class="flex-shrink-0"
            :style="{
              display: 'inline-block',
              width: '6px', height: '8px',
              borderRadius: '60% 60% 60% 0',
              transform: 'rotate(40deg)',
              background: infoColor(r.item).textColor === '#FFFFFF'
                ? 'rgba(255,255,255,0.8)'
                : 'rgba(21,41,74,0.55)',
            }"
          ></span>
          <span class="truncate">{{ r.item.nombre }}</span>
        </div>

        <!-- Monto (requiere más espacio) -->
        <div
          v-if="r.pw > 72 && r.ph > 52"
          class="font-display font-extrabold leading-none overflow-hidden whitespace-nowrap"
          :style="{ fontSize: valueSize(r.pw) }"
        >
          {{ formatoCiudadano(r.item.apropiado) }}
        </div>

        <!-- Porcentaje (solo si hay espacio generoso) -->
        <div
          v-if="r.pw > 88 && r.ph > 82"
          style="font-size: 11px; opacity: 0.82;"
        >
          {{ formatoPorcentaje(r.item.porcentaje_del_total) }} del total
        </div>
      </div><!-- /bloque -->
    </div><!-- /contenedor treemap -->

    <!-- Tooltip (solo en dispositivos con puntero) ──────────────────────── -->
    <div
      v-if="tooltip"
      class="absolute z-10 pointer-events-none rounded-xl shadow-xl text-white"
      style="width: 258px; background: #0E1B30; padding: 12px 14px; font-size: 13px;"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      role="tooltip"
    >
      <div class="flex items-center gap-2 font-bold mb-2" style="font-size: 14px;">
        <span :style="{
          display: 'inline-block', width: '8px', height: '11px', flexShrink: 0,
          borderRadius: '60% 60% 60% 0', transform: 'rotate(40deg)',
          background: infoColor(tooltip.item).color,
        }"></span>
        {{ tooltip.item.nombre }}
      </div>
      <div class="flex justify-between py-0.5"><span style="opacity:.7">Asignado</span><span class="tabular">{{ formatoCiudadano(tooltip.item.apropiado) }}</span></div>
      <div class="flex justify-between py-0.5"><span style="opacity:.7">Pagado</span><span class="tabular">{{ formatoCiudadano(tooltip.item.pagado) }}</span></div>
      <div v-if="!tooltip.item.esOtros" class="flex justify-between py-0.5">
        <span style="opacity:.7">Ejecución</span>
        <span class="tabular">{{ formatoPorcentaje(tooltip.item.porcentaje_ejecucion) }}</span>
      </div>
      <template v-if="!tooltip.item.esOtros">
        <div class="mt-2 pt-2 border-t text-sm" style="border-color:rgba(255,255,255,0.18); color:#7FD3DE;">
          {{ fraseEjecucion(tooltip.item.porcentaje_ejecucion) }}
        </div>
        <div v-if="infoColor(tooltip.item).ave" class="mt-1" style="font-size:11px; opacity:.6;">
          Ave guía: <strong class="text-white">{{ infoColor(tooltip.item).ave }}</strong>
        </div>
      </template>
      <div v-else class="mt-2 pt-2 border-t text-sm" style="border-color:rgba(255,255,255,0.18); opacity:.75;">
        Toca para ver la lista completa
      </div>
    </div>

    <!-- Lista expandida de "Otros" ─────────────────────────────────────── -->
    <div
      v-if="otrosAbierto && itemsOtros.length"
      class="mt-3 bg-white border border-neutro/20 rounded-xl p-4"
    >
      <div class="flex justify-between items-center mb-3">
        <h3 class="font-semibold text-tinta text-sm">Otros sectores ({{ itemsOtros.length }})</h3>
        <button class="text-xs text-turquesa hover:underline" @click="otrosAbierto = false">Cerrar</button>
      </div>
      <ul class="divide-y divide-neutro/10">
        <li v-for="item in itemsOtros" :key="item.nombre">
          <button
            class="w-full flex items-center justify-between gap-3 py-2 text-left text-sm hover:bg-neutro/5 rounded px-1"
            :disabled="esUltimoNivel"
            @click="emit('drill', item.nombre)"
          >
            <div class="flex items-center gap-2 min-w-0">
              <span class="flex-shrink-0 w-2.5 h-2.5 rounded-sm"
                    :style="{ background: colorDeNombre(item.nombre) }"></span>
              <span class="truncate text-tinta">{{ item.nombre }}</span>
            </div>
            <span class="tabular text-neutro shrink-0 text-xs">{{ formatoCiudadano(item.apropiado) }}</span>
          </button>
        </li>
      </ul>
    </div>

  </div>
</template>
