<script setup>
// Vista "¿De dónde sale y a dónde va la plata?" — barras apiladas CSS, sin Chart.js.
import { computed, ref, watch } from 'vue'
import { apiGet } from '../api/client.js'
import { formatoCiudadano, formatoPorcentaje } from '../utils/formato.js'

const props = defineProps({
  anio: { type: Number, required: true },
})

const datos  = ref(null)
const error  = ref(null)

const BAR_H   = 360
const ING_COLORES = ['#178A99', '#1E3A5F', '#D29A33', '#A83C80', '#3F8A4C', '#BC5630', '#9AA2AE']

async function cargar() {
  error.value = null
  datos.value = null
  try {
    datos.value = await apiGet('/api/ingresos/resumen', { anio: props.anio })
  } catch (e) {
    error.value = e.message
  }
}

watch(() => props.anio, cargar, { immediate: true })

const maxTotal = computed(() => {
  if (!datos.value) return 1
  return Math.max(Number(datos.value.total_aforo), Number(datos.value.total_gasto_apropiado))
})

// Segmentos de la barra de INGRESOS (top 5 conceptos + Otros)
const ingresosSegmentos = computed(() => {
  if (!datos.value?.items?.length) return []
  const items = datos.value.items
  const top = items.slice(0, 5)
  const restTotal = items.slice(5).reduce((s, i) => s + Number(i.aforo), 0)

  const segs = top.map((item, i) => ({
    label: item.concepto,
    valor: Number(item.aforo),
    color: ING_COLORES[i],
    h: Math.max(1, Math.round(Number(item.aforo) / maxTotal.value * BAR_H)),
  }))
  if (restTotal > 0) {
    segs.push({
      label: 'Otros conceptos',
      valor: restTotal,
      color: ING_COLORES[6],
      h: Math.max(1, Math.round(restTotal / maxTotal.value * BAR_H)),
    })
  }
  // Ajustar para que sumen exactamente BAR_H
  const used = segs.reduce((s, g) => s + g.h, 0)
  if (used !== BAR_H && segs.length) segs[segs.length - 1].h += BAR_H - used
  return segs
})

// Alturas de la barra de GASTOS
const gastosPagadoH = computed(() => {
  if (!datos.value) return 0
  return Math.max(1, Math.round(Number(datos.value.total_gasto_pagado) / maxTotal.value * BAR_H))
})

const gastosSinEjH = computed(() => {
  if (!datos.value) return 0
  const sinEj = Number(datos.value.total_gasto_apropiado) - Number(datos.value.total_gasto_pagado)
  const base = Math.max(0, Math.round(sinEj / maxTotal.value * BAR_H))
  // Ajustar para que sumen BAR_H
  const total = gastosPagadoH.value + base
  return total !== BAR_H ? base + (BAR_H - total) : base
})

const pctEjecucion = computed(() => {
  if (!datos.value) return 0
  return Number(datos.value.total_gasto_pagado) / Number(datos.value.total_gasto_apropiado) * 100
})
</script>

<template>
  <section>
    <h2 class="font-display font-extrabold text-2xl md:text-3xl mb-1 text-tinta">
      ¿De dónde sale y a dónde va la plata?
    </h2>
    <p class="mb-6" style="font-size: 15.5px; color: #55657E; line-height: 1.55; max-width: 760px;">
      En {{ anio }}, lo que el Estado planea recibir financia exactamente lo que planea gastar.
      La altura de cada bloque es proporcional a su tamaño.
    </p>

    <div v-if="error" class="bg-alerta/10 text-alerta rounded-xl p-4">{{ error }}</div>

    <template v-else-if="datos">

      <!-- Columnas side-by-side -->
      <div class="flex gap-10 flex-wrap items-start">

        <!-- INGRESOS -->
        <div class="flex-1 min-w-[200px]">
          <h3 class="font-display font-bold text-lg text-tinta mb-0.5">Ingresos</h3>
          <p class="text-sm text-neutro mb-3">¿De dónde sale?</p>
          <div class="font-display font-extrabold text-2xl tabular mb-3" style="color: #178A99;">
            {{ formatoCiudadano(datos.total_aforo) }}
          </div>

          <div class="rounded-xl overflow-hidden border" style="border-color: rgba(107,118,134,0.15);"
               :style="{ height: BAR_H + 'px' }">
            <div
              v-for="seg in ingresosSegmentos"
              :key="seg.label"
              class="flex items-center px-3 overflow-hidden"
              :style="{ height: seg.h + 'px', background: seg.color, borderBottom: '2px solid rgba(255,255,255,0.5)' }"
            >
              <div v-if="seg.h > 26" class="flex justify-between items-center w-full gap-2">
                <span class="text-white font-semibold text-xs truncate">{{ seg.label }}</span>
                <span class="text-white font-extrabold text-sm tabular font-display whitespace-nowrap">
                  {{ formatoCiudadano(seg.valor) }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- GASTOS -->
        <div class="flex-1 min-w-[200px]">
          <h3 class="font-display font-bold text-lg text-tinta mb-0.5">Gastos</h3>
          <p class="text-sm text-neutro mb-3">¿A dónde va?</p>
          <div class="font-display font-extrabold text-2xl tabular text-tinta mb-3">
            {{ formatoCiudadano(datos.total_gasto_apropiado) }}
          </div>

          <div class="rounded-xl overflow-hidden border flex flex-col" style="border-color: rgba(107,118,134,0.15);"
               :style="{ height: BAR_H + 'px' }">
            <!-- Pagado -->
            <div class="flex items-center px-3 overflow-hidden"
                 :style="{ height: gastosPagadoH + 'px', background: '#2E8B57', borderBottom: '2px solid rgba(255,255,255,0.5)', flexShrink: 0 }">
              <div v-if="gastosPagadoH > 26" class="flex justify-between items-center w-full gap-2">
                <span class="text-white font-semibold text-xs">Pagado</span>
                <span class="text-white font-extrabold text-sm tabular font-display whitespace-nowrap">
                  {{ formatoCiudadano(datos.total_gasto_pagado) }}
                </span>
              </div>
            </div>
            <!-- Sin ejecutar -->
            <div class="flex items-center px-3 overflow-hidden flex-1"
                 :style="{ background: '#4A7FA0' }">
              <div v-if="gastosSinEjH > 26" class="flex justify-between items-center w-full gap-2">
                <span class="text-white font-semibold text-xs">Sin ejecutar</span>
                <span class="text-white font-extrabold text-sm tabular font-display whitespace-nowrap">
                  {{ formatoCiudadano(Number(datos.total_gasto_apropiado) - Number(datos.total_gasto_pagado)) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Nota de ejecución -->
      <div class="mt-4 bg-white border rounded-xl p-4" style="border-color: rgba(107,118,134,0.15);">
        <div class="text-sm text-neutro">
          De cada $100 asignados para gastar en {{ anio }}, se han pagado
          <strong class="text-tinta">${{ Math.round(pctEjecucion) }}</strong>
          ({{ formatoPorcentaje(pctEjecucion) }} de ejecución).
        </div>
        <div class="mt-2 h-2.5 rounded-full overflow-hidden bg-neutro/15">
          <div class="h-full rounded-full transition-all duration-500"
               :style="{ width: Math.min(pctEjecucion, 100) + '%', background: 'linear-gradient(90deg,#2E8B57,#46A36B)' }"></div>
        </div>
      </div>

      <!-- Tabla de conceptos de ingreso -->
      <h3 class="font-semibold text-lg mt-8 mb-2 text-tinta">¿De dónde sale la plata? Detalle</h3>
      <div class="overflow-x-auto bg-white rounded-xl border" style="border-color: rgba(107,118,134,0.15);">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b text-left text-neutro" style="border-color: rgba(107,118,134,0.15);">
              <th class="px-4 py-3 font-semibold">Concepto</th>
              <th class="px-4 py-3 font-semibold text-right">Esperado (aforo)</th>
              <th class="px-4 py-3 font-semibold text-right">Recaudado</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, i) in datos.items.slice(0, 15)"
              :key="item.concepto"
              class="border-b last:border-0"
              :class="i % 2 === 1 ? 'bg-papel' : 'bg-white'"
              style="border-color: rgba(107,118,134,0.08);"
            >
              <td class="px-4 py-2.5 text-tinta">{{ item.concepto }}</td>
              <td class="px-4 py-2.5 text-right tabular text-tinta">{{ formatoCiudadano(item.aforo) }}</td>
              <td class="px-4 py-2.5 text-right tabular" style="color: #178A99;">{{ formatoCiudadano(item.recaudo) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-if="datos.items.length > 15" class="text-sm text-neutro mt-2">
        Mostrando los 15 conceptos más grandes de {{ datos.items.length }}.
      </p>
    </template>

    <div v-else class="text-neutro p-8 text-center">Cargando…</div>
  </section>
</template>
