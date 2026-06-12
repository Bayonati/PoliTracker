<script setup>
// Vista "¿Cuánto entra vs cuánto sale?": Chart.js para las barras.
import { onBeforeUnmount, ref, watch } from 'vue'
import {
  BarController, BarElement, CategoryScale, Chart, Legend, LinearScale, Tooltip,
} from 'chart.js'
import { apiGet } from '../api/client.js'
import { formatoCiudadano } from '../utils/formato.js'
import TarjetaCifra from './TarjetaCifra.vue'

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const props = defineProps({
  anio: { type: Number, required: true },
})

const datos = ref(null)
const error = ref(null)
const lienzo = ref(null)
let grafica = null

async function cargar() {
  error.value = null
  try {
    datos.value = await apiGet('/api/ingresos/resumen', { anio: props.anio })
    dibujar()
  } catch (e) {
    error.value = e.message
    datos.value = null
  }
}

function dibujar() {
  if (!lienzo.value || !datos.value) return
  grafica?.destroy()
  const d = datos.value
  grafica = new Chart(lienzo.value, {
    type: 'bar',
    data: {
      labels: ['Ingresos', 'Gastos'],
      datasets: [
        {
          label: 'Presupuestado',
          data: [Number(d.total_aforo), Number(d.total_gasto_apropiado)],
          backgroundColor: 'rgba(45, 106, 143, 0.35)',
          borderColor: '#2D6A8F',
          borderWidth: 1.5,
        },
        {
          label: 'Real (recaudado / pagado)',
          data: [Number(d.total_recaudo), Number(d.total_gasto_pagado)],
          backgroundColor: '#2D6A8F',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatoCiudadano(ctx.raw)}`,
          },
        },
        legend: { labels: { font: { family: 'Inter' } } },
      },
      scales: {
        y: {
          ticks: { callback: (v) => formatoCiudadano(v) },
        },
      },
    },
  })
}

watch(() => props.anio, cargar, { immediate: true })
onBeforeUnmount(() => grafica?.destroy())
</script>

<template>
  <section>
    <h2 class="font-display font-bold text-2xl md:text-3xl mb-1">
      ¿Cuánto entra vs cuánto sale?
    </h2>
    <p class="text-neutro mb-4">
      Lo que el Estado esperaba recaudar y gastar en {{ anio }}, frente a lo que realmente pasó.
    </p>

    <div v-if="error" class="bg-alerta/10 text-alerta rounded-lg p-4">{{ error }}</div>

    <template v-else-if="datos">
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <TarjetaCifra
          etiqueta="Ingresos recaudados"
          :cifra="formatoCiudadano(datos.total_recaudo)"
          :contexto="`De ${formatoCiudadano(datos.total_aforo)} esperados`"
          ayuda="Plata que efectivamente entró a la cuenta del Estado en el año"
        />
        <TarjetaCifra
          etiqueta="Gastos pagados"
          :cifra="formatoCiudadano(datos.total_gasto_pagado)"
          :contexto="`De ${formatoCiudadano(datos.total_gasto_apropiado)} asignados`"
          ayuda="Plata que ya salió de la cuenta del Estado"
        />
      </div>

      <div class="bg-white rounded-lg border border-neutro/20 p-4" style="height: 360px">
        <canvas ref="lienzo" role="img"
                aria-label="Gráfica de barras comparando ingresos y gastos del año"></canvas>
      </div>

      <h3 class="font-semibold text-lg mt-6 mb-2">¿De dónde sale la plata?</h3>
      <div class="overflow-x-auto bg-white rounded-lg border border-neutro/20">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-neutro/20 text-left text-neutro">
              <th class="px-3 py-2.5 font-semibold">Concepto</th>
              <th class="px-3 py-2.5 font-semibold text-right">Esperado (aforo)</th>
              <th class="px-3 py-2.5 font-semibold text-right">Recaudado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in datos.items.slice(0, 15)" :key="item.concepto"
                class="border-b border-neutro/10 last:border-0">
              <td class="px-3 py-2">{{ item.concepto }}</td>
              <td class="px-3 py-2 text-right tabular">{{ formatoCiudadano(item.aforo) }}</td>
              <td class="px-3 py-2 text-right tabular">{{ formatoCiudadano(item.recaudo) }}</td>
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
