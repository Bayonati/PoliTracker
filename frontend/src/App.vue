<script setup>
import { computed, onMounted, ref } from 'vue'
import { useExplorer } from './stores/explorer.js'
import { formatoCiudadano } from './utils/formato.js'
import { getSectorInfo } from './utils/sectorInfo.js'
import TreemapExplorer from './components/TreemapExplorer.vue'
import Breadcrumb from './components/Breadcrumb.vue'
import BarraComparativa from './components/BarraComparativa.vue'
import IngresosVsGastos from './components/IngresosVsGastos.vue'
import SelectorAnio from './components/SelectorAnio.vue'
import TablaDetalle from './components/TablaDetalle.vue'

const { state, nivel, inicializar, cambiarAnio, drillDown, irANivel } = useExplorer()

const vista = ref('acerca')
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

// Items con info de ave para la leyenda (solo nivel 0)
const itemsConAve = computed(() => {
  if (!state.datos?.items || nivel.value !== 0) return []
  return state.datos.items.map(i => ({ ...i, ...getSectorInfo(i.nombre) }))
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-papel">
    <!-- ===== HEADER ===== -->
    <header class="relative" style="background: #15294A;">
      <!-- Brillo radial turquesa -->
      <div class="absolute inset-0 pointer-events-none"
           style="background: radial-gradient(130% 150% at 86% 24%, rgba(43,167,181,0.26), transparent 58%)"></div>

      <div class="relative max-w-6xl mx-auto px-4 sm:px-6" style="min-height: 80px;">

        <!-- Fila 1: Logo + Navegación (desktop) -->
        <div class="header-row1 flex items-center justify-between gap-3 py-3 sm:py-4">

          <!-- Marca -->
          <div class="flex flex-col gap-0.5 flex-shrink-0">
            <div style="line-height: 0.94;">
              <span class="block font-display font-extrabold text-white tracking-tight"
                    style="font-size: clamp(16px, 4.5vw, 27px);">Colombia</span>
              <span class="block font-display font-semibold tracking-tight"
                    style="font-size: clamp(16px, 4.5vw, 27px); color: #7FD3DE;">Observa</span>
            </div>
            <span class="hidden sm:block font-semibold"
                  style="font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: #8295B4;">
              Vigilancia del gasto público
            </span>
          </div>

          <!-- Navegación — solo en sm+ (en móvil va en la fila 2) -->
          <nav class="hidden sm:flex gap-1" aria-label="Navegación principal">
            <button
              v-for="v in [['acerca', 'Acerca'], ['explorador', 'Explorador'], ['ingresos', 'Ingresos']]"
              :key="v[0]"
              class="px-3 py-2 rounded-lg transition-colors font-medium text-sm"
              :style="{
                background: vista === v[0] ? 'rgba(255,255,255,0.16)' : 'transparent',
                color: vista === v[0] ? '#FFFFFF' : 'rgba(255,255,255,0.72)',
                fontWeight: vista === v[0] ? 700 : 500,
              }"
              @click="vista = v[0]"
            >{{ v[1] }}</button>
          </nav>
        </div>

        <!-- Fila 2: Navegación centrada — solo en móvil -->
        <nav class="flex sm:hidden justify-center gap-2 pb-3" aria-label="Navegación principal">
          <button
            v-for="v in [['acerca', 'Acerca'], ['explorador', 'Explorador'], ['ingresos', 'Ingresos']]"
            :key="v[0]"
            class="px-5 py-2 rounded-lg transition-colors font-medium text-sm"
            :style="{
              background: vista === v[0] ? 'rgba(255,255,255,0.16)' : 'transparent',
              color: vista === v[0] ? '#FFFFFF' : 'rgba(255,255,255,0.72)',
              fontWeight: vista === v[0] ? 700 : 500,
            }"
            @click="vista = v[0]"
          >{{ v[1] }}</button>
        </nav>

        <!-- Barranquero — visible en todos los tamaños, escala con clamp -->
        <img
          src="/assets/barranquero.png"
          alt="Barranquero, el ave de Colombia Observa"
          class="barranquero absolute pointer-events-none"
        />
      </div>

      <!-- Franja de la bandera -->
      <div class="flex h-1">
        <div class="flex-1" style="background: #FCD116;"></div>
        <div class="flex-1" style="background: #1351A6;"></div>
        <div class="flex-1" style="background: #CE1126;"></div>
      </div>
    </header>

    <!-- ===== MAIN ===== -->
    <main class="flex-1 max-w-6xl w-full mx-auto px-4 py-6">

      <!-- ============ EXPLORADOR (home) ============ -->
      <section v-if="vista === 'explorador'">
        <div v-if="state.error" class="bg-alerta/10 text-alerta rounded-xl p-4 mb-4">
          {{ state.error }}
        </div>

        <template v-if="state.datos">
          <div class="flex flex-wrap items-end justify-between gap-3 mb-1">
            <h1 class="font-display font-extrabold text-2xl md:text-3xl text-tinta">{{ tituloNivel }}</h1>
            <SelectorAnio :anios="state.aniosDisponibles" :model-value="state.anio"
                          @update:model-value="cambiarAnio" />
          </div>
          <p class="text-neutro mb-3 max-w-3xl" style="font-size: 15.5px; line-height: 1.55;">
            El Estado colombiano tiene
            <strong class="text-tinta">{{ formatoCiudadano(state.datos.total_apropiado) }}</strong>
            para gastar en {{ state.anio }}<span v-if="nivel === 0"> — así se reparten</span><span v-else> en este nivel</span>.
            Toca un bloque para ver el detalle.
          </p>

          <div class="flex flex-wrap items-center justify-between gap-3 mb-3">
            <div class="flex items-center gap-2">
              <button
                v-if="nivel > 0"
                class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium text-sm transition-colors"
                style="background: #178A99; color: #fff;"
                @click="irANivel(nivel - 1)"
              >
                ← Volver
              </button>
              <Breadcrumb :path="state.path" @navegar="irANivel" />
            </div>
            <div class="flex rounded-lg border overflow-hidden text-sm" style="border-color: rgba(107,118,134,0.3);"
                 role="group" aria-label="Cambiar entre mapa y tabla">
              <button class="px-3 py-1.5 font-medium transition-colors"
                      :style="!modoTabla ? 'background:#178A99;color:#fff;font-weight:700;' : 'color:#6B7686;'"
                      :aria-pressed="!modoTabla" @click="modoTabla = false">Mapa</button>
              <button class="px-3 py-1.5 font-medium transition-colors"
                      :style="modoTabla ? 'background:#178A99;color:#fff;font-weight:700;' : 'color:#6B7686;'"
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

          <!-- Leyenda: cada sector, un ave (solo en nivel raíz) -->
          <div v-if="nivel === 0 && itemsConAve.length" class="mt-6">
            <div class="text-xs font-bold tracking-widest uppercase text-neutro mb-3">
              Cada sector, un ave de Colombia
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
              <div v-for="item in itemsConAve" :key="item.nombre"
                   class="flex items-center gap-2.5 bg-white border rounded-xl px-3 py-2"
                   style="border-color: rgba(107,118,134,0.12);">
                <span class="flex-shrink-0 w-3 h-3 rounded"
                      :style="{ background: item.color }"></span>
                <div class="min-w-0">
                  <div class="text-xs font-semibold text-tinta truncate">{{ item.nombre }}</div>
                  <div class="text-xs text-neutro truncate">{{ item.ave }}</div>
                </div>
              </div>
            </div>
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
      <section v-else class="max-w-5xl">
        <div class="grid gap-8 grid-cols-1 md:grid-cols-[1.4fr_1fr]">
          <div>
            <h1 class="font-display font-extrabold text-2xl md:text-3xl mb-3 text-tinta">¿Qué es Colombia Observa?</h1>
            <div class="space-y-4 text-tinta/90" style="font-size: 16px; line-height: 1.65;">
              <p>
                Una plataforma ciudadana para entender <strong>en qué se gastan
                tus impuestos</strong>. Sin jerga técnica, sin agenda política: los datos
                oficiales del Presupuesto General de la Nación, en gráficas que cualquiera entiende.
              </p>
              <p>Los datos vienen de los conjuntos abiertos que publica el Ministerio de Hacienda (sistema SIIF) en datos.gov.co:</p>
              <ul class="list-disc pl-5 space-y-1">
                <li>
                  <a class="text-turquesa hover:underline font-semibold"
                     href="https://www.datos.gov.co/Hacienda-y-Cr-dito-P-blico/5phs-yqfw" target="_blank" rel="noopener">
                    Información de Gastos del Presupuesto General de la Nación</a>
                </li>
                <li>
                  <a class="text-turquesa hover:underline font-semibold"
                     href="https://www.datos.gov.co/Hacienda-y-Cr-dito-P-blico/22f3-gynv" target="_blank" rel="noopener">
                    Ingresos por Vigencia</a>
                </li>
              </ul>
              <p v-if="fechaDatos" class="text-neutro">
                Datos actualizados a: <strong class="text-tinta">{{ fechaDatos }}</strong>.
                Los montos mensuales del SIIF son acumulados del año; mostramos el corte más reciente.
              </p>

              <h2 class="font-display font-bold text-xl pt-2 text-tinta">El barranquero y nuestra fauna</h2>
              <p>
                Cada sector del presupuesto tiene un ave colombiana que lo acompaña. Una forma de recordar
                que detrás de cada cifra hay un país vivo, biodiverso, que vale la pena cuidar y vigilar.
              </p>

              <h2 class="font-display font-bold text-xl pt-2 text-tinta">Glosario rápido</h2>
              <ul class="space-y-1" style="font-size: 15px; line-height: 1.85;">
                <li><strong>Asignado (apropiado):</strong> plata asignada para gastar este año.</li>
                <li><strong>Pagado:</strong> plata que ya salió de la cuenta del Estado.</li>
                <li><strong>Compromisos:</strong> plata ya prometida en contratos firmados.</li>
                <li><strong>Un billón:</strong> en Colombia es un millón de millones ($1.000.000.000.000).</li>
              </ul>
            </div>
          </div>

          <div class="bg-white border rounded-2xl p-5 self-start sticky top-4"
               style="border-color: rgba(107,118,134,0.15);">
            <img src="/assets/colombia-observa-logo.png" alt="Logo Colombia Observa"
                 class="w-full rounded-xl block" />
            <p class="text-xs text-neutro mt-3 text-center leading-relaxed">
              Datos oficiales de datos.gov.co · sin agenda política · actualización manual.
            </p>
          </div>
        </div>
      </section>
    </main>

    <!-- ===== FOOTER ===== -->
    <footer class="border-t mt-8" style="border-color: rgba(107,118,134,0.15);">
      <div class="max-w-6xl mx-auto px-4 py-4 text-sm text-neutro flex flex-wrap justify-between gap-2">
        <span>Colombia Observa — datos oficiales de datos.gov.co, sin agenda política.</span>
        <span v-if="fechaDatos">Datos actualizados a {{ fechaDatos }}</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* En sm+ reserva espacio a la derecha de la fila 1 para el barranquero */
@media (min-width: 640px) {
  .header-row1 {
    padding-right: clamp(90px, 14vw, 180px);
  }
}

/* Pájaro: móvil descansa sobre los botones de nav; desktop la cola asoma */
.barranquero {
  right: 0;
  bottom: 0;           /* móvil: pegado al fondo del wrapper (encima de nav) */
  height: clamp(72px, 19vw, 96px);
  z-index: 10;
  filter: drop-shadow(0 6px 14px rgba(0,0,0,0.38));
}
@media (min-width: 640px) {
  .barranquero {
    bottom: -16px;     /* desktop: la cola asoma ~16px bajo la franja */
    height: clamp(82px, 11vw, 100px);
  }
}
</style>
