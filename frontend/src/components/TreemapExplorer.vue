<script setup>
// D3 calcula el layout; Vue renderiza divs HTML (no SVG) para más libertad visual.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { hierarchy, treemap, treemapSquarify } from 'd3-hierarchy'
import { formatoCiudadano, formatoPorcentaje, fraseEjecucion } from '../utils/formato.js'
import { getSectorInfo } from '../utils/sectorInfo.js'

const props = defineProps({
  items: { type: Array, required: true },
  esUltimoNivel: { type: Boolean, default: false },
})
const emit = defineEmits(['drill', 'subir'])

const contenedor = ref(null)
const ancho = ref(900)
const alto = ref(504)
const esMovil = ref(false)
const tooltip = ref(null)
const otrosAbierto = ref(false)
const focoIdx = ref(-1)

let observador = null

onMounted(() => {
  observador = new ResizeObserver((entradas) => {
    const r = entradas[0].contentRect
    ancho.value = Math.max(320, r.width)
    alto.value = Math.max(280, r.height || Math.round(r.width * 560 / 1000))
    esMovil.value = window.innerWidth < 768
  })
  observador.observe(contenedor.value)
  esMovil.value = window.innerWidth < 768
})
onBeforeUnmount(() => observador?.disconnect())

const agrupados = computed(() => {
  const grandes = props.items.filter((i) => i.porcentaje_del_total >= 1)
  const chicos = props.items.filter((i) => i.porcentaje_del_total < 1)
  const nodos = grandes.map((i) => ({ ...i, esOtros: false }))
  if (chicos.length > 1) {
    nodos.push({
      nombre: `Otros (${chicos.length})`,
      apropiado: String(chicos.reduce((s, i) => s + Number(i.apropiado), 0)),
      pagado: String(chicos.reduce((s, i) => s + Number(i.pagado), 0)),
      porcentaje_del_total: Math.round(chicos.reduce((s, i) => s + i.porcentaje_del_total, 0) * 10) / 10,
      porcentaje_ejecucion: 0,
      esOtros: true,
      hijos: chicos,
    })
  } else if (chicos.length === 1) {
    nodos.push({ ...chicos[0], esOtros: false })
  }
  return nodos
})

const itemsOtros = computed(() => agrupados.value.find((n) => n.esOtros)?.hijos ?? [])

// D3 layout → posiciones en porcentaje para CSS
const rects = computed(() => {
  if (!ancho.value) return []
  const raiz = hierarchy({ children: agrupados.value })
    .sum((d) => Number(d.apropiado) || 0)
    .sort((a, b) => b.value - a.value)
  treemap()
    .tile(treemapSquarify)
    .size([ancho.value, alto.value])
    .paddingInner(4)(raiz)
  return (raiz.children ?? []).map((n) => ({
    item: n.data,
    // Dimensiones en px para decidir qué mostrar
    pw: n.x1 - n.x0,
    ph: n.y1 - n.y0,
    // Posiciones en % para CSS (evitan recalcular al resize)
    left:   (n.x0       / ancho.value * 100).toFixed(3),
    top:    (n.y0       / alto.value  * 100).toFixed(3),
    width:  ((n.x1 - n.x0) / ancho.value * 100).toFixed(3),
    height: ((n.y1 - n.y0) / alto.value  * 100).toFixed(3),
  }))
})

function infoColor(item) {
  if (item.esOtros) return { color: '#9AA2AE', textColor: '#15294A', ave: null }
  return getSectorInfo(item.nombre)
}

function labelSize(pw) { return Math.max(10, Math.min(13, pw / 16)) + 'px' }
function valueSize(pw) { return Math.max(13, Math.min(26, pw / 11.5)) + 'px' }

function clickNodo(item) {
  if (item.esOtros) { otrosAbierto.value = !otrosAbierto.value }
  else if (!props.esUltimoNivel) { emit('drill', item.nombre) }
}

function moverTooltip(ev, item) {
  const caja = contenedor.value.getBoundingClientRect()
  tooltip.value = {
    x: Math.min(ev.clientX - caja.left + 14, caja.width - 275),
    y: ev.clientY - caja.top + 14,
    item,
  }
}

function colorDeNombre(nombre) { return getSectorInfo(nombre).color }

function tecla(ev) {
  const n = rects.value.length
  if (n === 0) return
  if (ev.key === 'ArrowRight' || ev.key === 'ArrowDown') {
    focoIdx.value = (focoIdx.value + 1) % n; ev.preventDefault()
  } else if (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp') {
    focoIdx.value = (focoIdx.value - 1 + n) % n; ev.preventDefault()
  } else if (ev.key === 'Enter' && focoIdx.value >= 0) {
    clickNodo(rects.value[focoIdx.value].item); ev.preventDefault()
  } else if (ev.key === 'Escape') {
    emit('subir'); ev.preventDefault()
  }
}
</script>

<template>
  <div ref="contenedor" class="relative w-full select-none" @keydown="tecla">

    <!-- Móvil: barras horizontales (treemap táctil pequeño es inusable) -->
    <div v-if="esMovil" class="flex flex-col gap-2">
      <button
        v-for="item in agrupados"
        :key="item.nombre"
        class="text-left rounded-xl p-3 transition-transform active:scale-[0.99]"
        :style="{ backgroundColor: infoColor(item).color, color: infoColor(item).textColor }"
        @click="clickNodo(item)"
      >
        <div class="flex justify-between gap-2 items-baseline">
          <span class="font-semibold text-sm leading-tight">{{ item.nombre }}</span>
          <span class="text-xs opacity-80 shrink-0">{{ formatoPorcentaje(item.porcentaje_del_total) }}</span>
        </div>
        <div class="font-display font-bold tabular text-base mt-0.5">{{ formatoCiudadano(item.apropiado) }}</div>
        <div class="h-1.5 mt-1.5 rounded overflow-hidden" style="background: rgba(0,0,0,0.2);" v-if="!item.esOtros">
          <div class="h-full rounded"
               :style="{
                 width: Math.min(item.porcentaje_ejecucion, 100) + '%',
                 background: infoColor(item).textColor === '#FFFFFF' ? 'rgba(255,255,255,0.6)' : 'rgba(21,41,74,0.4)',
               }" />
        </div>
      </button>
    </div>

    <!-- Escritorio: treemap con divs absolutamente posicionados -->
    <div
      v-else
      class="relative w-full rounded-xl overflow-hidden"
      style="aspect-ratio: 1000/560; background: #EEF1EB; min-height: 280px;"
      role="group"
      aria-label="Treemap del presupuesto. Use flechas para moverse, Enter para entrar, Escape para subir."
      tabindex="0"
    >
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
          padding:    '10px 12px',
          boxSizing:  'border-box',
          display:    'flex',
          flexDirection: 'column',
          gap:        '3px',
          cursor:     r.item.esOtros || !esUltimoNivel ? 'pointer' : 'default',
          outline:    focoIdx === i ? '3px solid #E9B44C' : 'none',
          outlineOffset: '-2px',
          transition: 'left .3s ease-out, top .3s ease-out, width .3s ease-out, height .3s ease-out',
        }"
        @click="clickNodo(r.item)"
        @mousemove="moverTooltip($event, r.item)"
        @mouseleave="tooltip = null"
      >
        <!-- Nombre + pluma decorativa -->
        <div v-if="r.pw > 80"
             class="flex items-center gap-1.5 overflow-hidden font-bold uppercase leading-tight tracking-wide"
             :style="{ fontSize: labelSize(r.pw) }">
          <span
            v-if="!r.item.esOtros"
            class="flex-shrink-0"
            :style="{
              display: 'inline-block',
              width: '7px', height: '9.5px',
              borderRadius: '60% 60% 60% 0',
              transform: 'rotate(40deg)',
              background: infoColor(r.item).textColor === '#FFFFFF'
                ? 'rgba(255,255,255,0.8)'
                : 'rgba(21,41,74,0.55)',
            }"
          ></span>
          <span class="truncate">{{ r.item.nombre }}</span>
        </div>

        <!-- Monto -->
        <div v-if="r.pw > 100 && r.ph > 68"
             class="font-display font-extrabold leading-none overflow-hidden whitespace-nowrap"
             :style="{ fontSize: valueSize(r.pw) }">
          {{ formatoCiudadano(r.item.apropiado) }}
        </div>

        <!-- Porcentaje -->
        <div v-if="r.pw > 110 && r.ph > 100" style="font-size: 12px; opacity: 0.82;">
          {{ formatoPorcentaje(r.item.porcentaje_del_total) }} del total
        </div>
      </div>
    </div>

    <!-- Tooltip -->
    <div
      v-if="tooltip && !esMovil"
      class="absolute z-10 pointer-events-none rounded-xl shadow-xl text-white"
      style="width: 265px; background: #0E1B30; padding: 13px 15px; font-size: 13.5px;"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      role="tooltip"
    >
      <!-- Encabezado con pluma -->
      <div class="flex items-center gap-2 font-bold mb-2" style="font-size: 14.5px;">
        <span :style="{
          display: 'inline-block', width: '9px', height: '12px', flexShrink: 0,
          borderRadius: '60% 60% 60% 0', transform: 'rotate(40deg)',
          background: infoColor(tooltip.item).color,
        }"></span>
        {{ tooltip.item.nombre }}
      </div>

      <div class="flex justify-between py-0.5">
        <span style="opacity:.7">Asignado</span>
        <span class="tabular">{{ formatoCiudadano(tooltip.item.apropiado) }}</span>
      </div>
      <div class="flex justify-between py-0.5">
        <span style="opacity:.7">Pagado</span>
        <span class="tabular">{{ formatoCiudadano(tooltip.item.pagado) }}</span>
      </div>
      <div v-if="!tooltip.item.esOtros" class="flex justify-between py-0.5">
        <span style="opacity:.7">Ejecución</span>
        <span class="tabular">{{ formatoPorcentaje(tooltip.item.porcentaje_ejecucion) }}</span>
      </div>

      <template v-if="!tooltip.item.esOtros">
        <div class="mt-2 pt-2 border-t text-sm" style="border-color:rgba(255,255,255,0.18); color:#7FD3DE;">
          {{ fraseEjecucion(tooltip.item.porcentaje_ejecucion) }}
        </div>
        <div v-if="infoColor(tooltip.item).ave" class="mt-1" style="font-size: 12px; opacity: 0.6;">
          Ave guía: <strong class="text-white">{{ infoColor(tooltip.item).ave }}</strong>
        </div>
      </template>
      <div v-else class="mt-2 pt-2 border-t text-sm" style="border-color:rgba(255,255,255,0.18); opacity:.75;">
        Toca para ver la lista completa
      </div>
    </div>

    <!-- Lista expandida de "Otros" -->
    <div v-if="otrosAbierto && itemsOtros.length"
         class="mt-3 bg-white border border-neutro/20 rounded-xl p-4">
      <div class="flex justify-between items-center mb-3">
        <h3 class="font-semibold text-tinta">Otros sectores ({{ itemsOtros.length }})</h3>
        <button class="text-sm text-turquesa hover:underline" @click="otrosAbierto = false">Cerrar</button>
      </div>
      <ul class="divide-y divide-neutro/10">
        <li v-for="item in itemsOtros" :key="item.nombre">
          <button
            class="w-full flex items-center justify-between gap-3 py-2 text-left text-sm hover:bg-neutro/5 rounded px-1"
            :disabled="esUltimoNivel"
            @click="emit('drill', item.nombre)"
          >
            <div class="flex items-center gap-2 min-w-0">
              <span class="flex-shrink-0 w-3 h-3 rounded-sm"
                    :style="{ background: colorDeNombre(item.nombre) }"></span>
              <span class="truncate">{{ item.nombre }}</span>
            </div>
            <span class="tabular text-neutro shrink-0">{{ formatoCiudadano(item.apropiado) }}</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
