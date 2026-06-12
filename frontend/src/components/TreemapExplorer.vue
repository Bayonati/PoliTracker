<script setup>
// Treemap con drill-down estilo USAspending. D3 SOLO calcula el layout
// (d3-hierarchy); Vue es dueño del DOM y renderiza los <rect> — así no
// peleamos con el reactivity de Vue.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { hierarchy, treemap, treemapSquarify } from 'd3-hierarchy'
import { formatoCiudadano, formatoPorcentaje, fraseEjecucion } from '../utils/formato.js'

const props = defineProps({
  items: { type: Array, required: true },     // [{nombre, apropiado, pagado, porcentaje_del_total, porcentaje_ejecucion}]
  esUltimoNivel: { type: Boolean, default: false },
})
const emit = defineEmits(['drill', 'subir'])

const contenedor = ref(null)
const ancho = ref(900)
const alto = ref(520)
const esMovil = ref(false)
const tooltip = ref(null)        // {x, y, item}
const otrosAbierto = ref(false)
const focoIdx = ref(-1)

let observador = null

onMounted(() => {
  observador = new ResizeObserver((entradas) => {
    const w = entradas[0].contentRect.width
    ancho.value = Math.max(320, w)
    alto.value = Math.max(380, Math.min(560, w * 0.55))
    esMovil.value = window.innerWidth < 768
  })
  observador.observe(contenedor.value)
  esMovil.value = window.innerWidth < 768
})
onBeforeUnmount(() => observador?.disconnect())

// Agrupa los menores al 1% en un bloque "Otros" clickeable
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

// Layout del treemap (solo cálculo; nada de DOM)
const rects = computed(() => {
  const raiz = hierarchy({ children: agrupados.value })
    .sum((d) => Number(d.apropiado) || 0)
    .sort((a, b) => b.value - a.value)
  treemap()
    .tile(treemapSquarify)
    .size([ancho.value, alto.value])
    .paddingInner(3)(raiz)
  return (raiz.children ?? []).map((n) => ({
    item: n.data,
    x: n.x0, y: n.y0, w: n.x1 - n.x0, h: n.y1 - n.y0,
  }))
})

const maxApropiado = computed(() =>
  Math.max(...agrupados.value.map((i) => Number(i.apropiado)), 1))

// Escala de luminosidad sobre `andino` (hsl 203,52%): más oscuro = más plata.
function colorDe(item) {
  if (item.esOtros) return 'hsl(210, 12%, 62%)'
  const f = Math.sqrt(Number(item.apropiado) / maxApropiado.value) // sqrt para diferenciar los chicos
  const luz = 72 - f * 42 // 72% (poco) -> 30% (mucho)
  return `hsl(203, 52%, ${luz}%)`
}

// Contraste AA: texto blanco sobre tonos oscuros, tinta sobre claros
function colorTexto(item) {
  if (item.esOtros) return '#16233A'
  const f = Math.sqrt(Number(item.apropiado) / maxApropiado.value)
  return 72 - f * 42 < 55 ? '#FFFFFF' : '#16233A'
}

function clickNodo(item) {
  if (item.esOtros) {
    otrosAbierto.value = !otrosAbierto.value
  } else if (!props.esUltimoNivel) {
    emit('drill', item.nombre)
  }
}

function moverTooltip(ev, item) {
  const caja = contenedor.value.getBoundingClientRect()
  tooltip.value = {
    x: Math.min(ev.clientX - caja.left + 14, caja.width - 270),
    y: ev.clientY - caja.top + 14,
    item,
  }
}

// Navegación por teclado: flechas mueven el foco, Enter baja, Escape sube
function tecla(ev) {
  const n = rects.value.length
  if (n === 0) return
  if (ev.key === 'ArrowRight' || ev.key === 'ArrowDown') {
    focoIdx.value = (focoIdx.value + 1) % n
    ev.preventDefault()
  } else if (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp') {
    focoIdx.value = (focoIdx.value - 1 + n) % n
    ev.preventDefault()
  } else if (ev.key === 'Enter' && focoIdx.value >= 0) {
    clickNodo(rects.value[focoIdx.value].item)
    ev.preventDefault()
  } else if (ev.key === 'Escape') {
    emit('subir')
    ev.preventDefault()
  }
}
</script>

<template>
  <div ref="contenedor" class="relative w-full" @keydown="tecla">
    <!-- Versión móvil: barras horizontales (un treemap táctil pequeño es inusable) -->
    <div v-if="esMovil" class="flex flex-col gap-2">
      <button
        v-for="(item, i) in agrupados"
        :key="item.nombre"
        class="text-left rounded-md p-3 transition-transform active:scale-[0.99]"
        :style="{ backgroundColor: colorDe(item), color: colorTexto(item) }"
        @click="clickNodo(item)"
      >
        <div class="flex justify-between gap-2 items-baseline">
          <span class="font-semibold text-sm leading-tight">{{ item.nombre }}</span>
          <span class="text-xs opacity-90 shrink-0">{{ formatoPorcentaje(item.porcentaje_del_total) }}</span>
        </div>
        <div class="font-display font-bold tabular">{{ formatoCiudadano(item.apropiado) }}</div>
        <div class="h-1.5 mt-2 rounded bg-black/20 overflow-hidden" v-if="!item.esOtros">
          <div class="h-full bg-oro" :style="{ width: Math.min(item.porcentaje_ejecucion, 100) + '%' }" />
        </div>
      </button>
    </div>

    <!-- Versión escritorio: treemap SVG -->
    <svg
      v-else
      :viewBox="`0 0 ${ancho} ${alto}`"
      :width="ancho"
      :height="alto"
      role="group"
      aria-label="Treemap del presupuesto. Use las flechas para moverse, Enter para entrar, Escape para subir."
      tabindex="0"
      class="select-none outline-offset-4"
    >
      <g
        v-for="(r, i) in rects"
        :key="r.item.nombre"
        :transform="`translate(${r.x},${r.y})`"
        style="transition: transform 300ms ease-out"
        class="cursor-pointer"
        :tabindex="-1"
        @click="clickNodo(r.item)"
        @mousemove="moverTooltip($event, r.item)"
        @mouseleave="tooltip = null"
      >
        <rect
          :width="r.w"
          :height="r.h"
          :fill="colorDe(r.item)"
          rx="4"
          style="transition: width 300ms ease-out, height 300ms ease-out"
          :stroke="focoIdx === i ? '#E9B44C' : 'transparent'"
          stroke-width="3"
        />
        <!-- Labels solo si caben -->
        <text v-if="r.w > 90 && r.h > 46" :x="10" :y="22"
              :fill="colorTexto(r.item)" font-size="13" font-weight="600"
              style="pointer-events: none">
          {{ r.item.nombre.length > r.w / 7 ? r.item.nombre.slice(0, r.w / 7) + '…' : r.item.nombre }}
        </text>
        <text v-if="r.w > 90 && r.h > 64" :x="10" :y="42"
              :fill="colorTexto(r.item)" font-size="15" font-weight="700"
              font-family="Archivo, sans-serif" style="pointer-events: none">
          {{ formatoCiudadano(r.item.apropiado) }}
        </text>
        <text v-if="r.w > 90 && r.h > 84" :x="10" :y="60"
              :fill="colorTexto(r.item)" font-size="12" opacity="0.85"
              style="pointer-events: none">
          {{ formatoPorcentaje(r.item.porcentaje_del_total) }} del total
        </text>
      </g>
    </svg>

    <!-- Tooltip -->
    <div
      v-if="tooltip && !esMovil"
      class="absolute z-10 pointer-events-none bg-tinta text-white rounded-lg p-3 shadow-xl w-64 text-sm"
      :style="{ left: tooltip.x + 'px', top: tooltip.y + 'px' }"
      role="tooltip"
    >
      <div class="font-semibold mb-1">{{ tooltip.item.nombre }}</div>
      <div class="flex justify-between"><span class="opacity-75">Asignado</span>
        <span class="tabular">{{ formatoCiudadano(tooltip.item.apropiado) }}</span></div>
      <div class="flex justify-between"><span class="opacity-75">Pagado</span>
        <span class="tabular">{{ formatoCiudadano(tooltip.item.pagado) }}</span></div>
      <div v-if="!tooltip.item.esOtros" class="flex justify-between">
        <span class="opacity-75">Ejecución</span>
        <span class="tabular">{{ formatoPorcentaje(tooltip.item.porcentaje_ejecucion) }}</span></div>
      <div v-if="!tooltip.item.esOtros" class="mt-2 pt-2 border-t border-white/20 text-oro">
        {{ fraseEjecucion(tooltip.item.porcentaje_ejecucion) }}
      </div>
      <div v-else class="mt-2 pt-2 border-t border-white/20 opacity-75">
        Click para ver la lista completa
      </div>
    </div>

    <!-- Lista expandida de "Otros" -->
    <div v-if="otrosAbierto && itemsOtros.length"
         class="mt-3 bg-white border border-neutro/20 rounded-lg p-4">
      <div class="flex justify-between items-center mb-2">
        <h3 class="font-semibold">Otros ({{ itemsOtros.length }})</h3>
        <button class="text-sm text-andino hover:underline" @click="otrosAbierto = false">Cerrar</button>
      </div>
      <ul class="divide-y divide-neutro/10">
        <li v-for="item in itemsOtros" :key="item.nombre">
          <button
            class="w-full flex justify-between gap-3 py-2 text-left text-sm hover:bg-andino/5 rounded px-1"
            :disabled="esUltimoNivel"
            @click="emit('drill', item.nombre)"
          >
            <span>{{ item.nombre }}</span>
            <span class="tabular text-neutro shrink-0">{{ formatoCiudadano(item.apropiado) }}</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
