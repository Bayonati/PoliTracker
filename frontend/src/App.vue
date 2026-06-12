<script setup>
import { computed, onMounted, ref } from 'vue'
import { useExplorer } from './stores/explorer.js'
import { formatoCiudadano } from './utils/formato.js'
import TreemapExplorer from './components/TreemapExplorer.vue'
import Breadcrumb from './components/Breadcrumb.vue'
import BarraComparativa from './components/BarraComparativa.vue'
import IngresosVsGastos from './components/IngresosVsGastos.vue'
import SelectorAnio from './components/SelectorAnio.vue'
import TablaDetalle from './components/TablaDetalle.vue'

const { state, nivel, inicializar, cambiarAnio, drillDown, irANivel } = useExplorer()

// Navegación simple de 3 vistas (sin vue-router: una dependencia menos)
const vista = ref('explorador')
const modoTabla = ref(false)

onMounted(inicializar)

const tituloNivel = computed(() => {
  if (nivel.value === 0) return '¿En qué se gasta la plata?'
  if (nivel.value === 1) return `¿Quién gasta la plata de ${state.path[0]}?`
  return `¿Cómo gasta ${state.path[1]}?`
})

const fechaDatos = computed(() => {
  if (!state.ultimaIngesta) return ''
  return new Date(state.ultimaIngesta).toLocaleDateString('es-CO',
    { year: 'numeric', month: 'long', day: 'numeric' })
})
</script>

<template>
  <header class="bg-tinta text-white">
    <div class="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
      <span class="text-xl tracking-tight">
        <span class="font-bold font-display">Poli</span><span class="font-display">Tracker</span>
      </span>
      <nav class="flex gap-1 text-sm" aria-label="Navegación principal">
        <button
          v-for="v in [['explorador', 'Explorador'], ['ingresos', 'Ingresos vs Gastos'], ['acerca', 'Acerca de']]"
          :key="v[0]"
          class="px-3 py-1.5 rounded-md transition-colors"
          :class="vista === v[0] ? 'bg-white/15 font-semibold' : 'hover:bg-white/10'"
          @click="vista = v[0]"
        >{{ v[1] }}</button>
      </nav>
    </div>
  </header>

  <main class="max-w-6xl mx-auto px-4 py-6">
    <!-- ============ EXPLORADOR (home) ============ -->
    <section v-if="vista === 'explorador'">
      <div v-if="state.error" class="bg-alerta/10 text-alerta rounded-lg p-4 mb-4">
        {{ state.error }}
      </div>

      <template v-if="state.datos">
        <div class="flex flex-wrap items-end justify-between gap-3 mb-1">
          <h1 class="font-display font-bold text-2xl md:text-3xl">{{ tituloNivel }}</h1>
          <SelectorAnio :anios="state.aniosDisponibles" :model-value="state.anio"
                        @update:model-value="cambiarAnio" />
        </div>
        <p class="text-neutro mb-3 max-w-3xl">
          El Estado colombiano tiene
          <strong class="text-tinta">{{ formatoCiudadano(state.datos.total_apropiado) }}</strong>
          para gastar en {{ state.anio }}<span v-if="nivel === 0"> — así se reparten</span><span v-else> en este nivel</span>.
          Toca un bloque para ver el detalle.
        </p>

        <div class="flex flex-wrap items-center justify-between gap-3 mb-3">
          <Breadcrumb :path="state.path" @navegar="irANivel" />
          <div class="flex rounded-md border border-neutro/30 overflow-hidden text-sm" role="group"
               aria-label="Cambiar entre treemap y tabla">
            <button class="px-3 py-1.5"
                    :class="!modoTabla ? 'bg-andino text-white font-semibold' : 'text-neutro hover:text-andino'"
                    :aria-pressed="!modoTabla" @click="modoTabla = false">Mapa</button>
            <button class="px-3 py-1.5"
                    :class="modoTabla ? 'bg-andino text-white font-semibold' : 'text-neutro hover:text-andino'"
                    :aria-pressed="modoTabla" @click="modoTabla = true">Tabla</button>
          </div>
        </div>

        <div :class="{ 'opacity-50 pointer-events-none': state.cargando }">
          <TablaDetalle v-if="modoTabla" :items="state.datos.items"
                        :es-ultimo-nivel="nivel >= 2" @drill="drillDown" />
          <TreemapExplorer v-else :items="state.datos.items"
                           :es-ultimo-nivel="nivel >= 2"
                           @drill="drillDown" @subir="irANivel(Math.max(nivel - 1, 0))" />
        </div>

        <div class="mt-4">
          <BarraComparativa :apropiado="state.datos.total_apropiado"
                            :pagado="state.datos.total_pagado" />
        </div>
      </template>

      <div v-else-if="state.cargando || !state.error" class="text-neutro p-12 text-center">
        Cargando datos del presupuesto…
      </div>
    </section>

    <!-- ============ INGRESOS VS GASTOS ============ -->
    <section v-else-if="vista === 'ingresos'">
      <div class="flex justify-end mb-3" v-if="state.aniosDisponibles.length">
        <SelectorAnio :anios="state.aniosDisponibles" :model-value="state.anio"
                      @update:model-value="cambiarAnio" />
      </div>
      <IngresosVsGastos v-if="state.anio" :anio="state.anio" />
    </section>

    <!-- ============ ACERCA DE ============ -->
    <section v-else class="max-w-3xl">
      <h1 class="font-display font-bold text-2xl md:text-3xl mb-3">¿Qué es PoliTracker?</h1>
      <div class="space-y-4 text-tinta/90">
        <p>
          PoliTracker es una plataforma ciudadana para entender <strong>en qué se gastan
          tus impuestos</strong>. Sin jerga técnica, sin agenda política: los datos
          oficiales del Presupuesto General de la Nación, en gráficas que cualquiera entiende.
        </p>
        <p>
          Los datos vienen directamente de los datasets abiertos que publica el
          Ministerio de Hacienda (sistema SIIF) en datos.gov.co:
        </p>
        <ul class="list-disc pl-6 space-y-1">
          <li>
            <a class="text-andino hover:underline"
               href="https://www.datos.gov.co/Hacienda-y-Cr-dito-P-blico/5phs-yqfw" target="_blank" rel="noopener">
              Información de Gastos del Presupuesto General de la Nación</a>
          </li>
          <li>
            <a class="text-andino hover:underline"
               href="https://www.datos.gov.co/Hacienda-y-Cr-dito-P-blico/22f3-gynv" target="_blank" rel="noopener">
              Ingresos por Vigencia</a>
          </li>
        </ul>
        <p v-if="fechaDatos" class="text-neutro">
          Datos actualizados a: <strong class="text-tinta">{{ fechaDatos }}</strong>.
          Los montos mensuales del SIIF son acumulados del año; mostramos el corte más reciente.
        </p>
        <h2 class="font-display font-bold text-xl pt-2">Glosario rápido</h2>
        <ul class="space-y-1">
          <li><strong>Asignado (apropiado):</strong> plata asignada para gastar este año.</li>
          <li><strong>Pagado:</strong> plata que ya salió de la cuenta del Estado.</li>
          <li><strong>Compromisos:</strong> plata ya prometida en contratos firmados.</li>
          <li><strong>Un billón:</strong> en Colombia es un millón de millones ($1.000.000.000.000).</li>
        </ul>
      </div>
    </section>
  </main>

  <footer class="border-t border-neutro/20 mt-8">
    <div class="max-w-6xl mx-auto px-4 py-4 text-sm text-neutro flex flex-wrap justify-between gap-2">
      <span>PoliTracker — datos oficiales de datos.gov.co, sin agenda política.</span>
      <span v-if="fechaDatos">Datos actualizados a {{ fechaDatos }}</span>
    </div>
  </footer>
</template>
