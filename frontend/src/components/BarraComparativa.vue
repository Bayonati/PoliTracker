<script setup>
// Barra horizontal apropiado vs pagado del nivel actual del explorador.
import { computed } from 'vue'
import { formatoCiudadano, formatoPorcentaje, fraseEjecucion } from '../utils/formato.js'

const props = defineProps({
  apropiado: { type: String, required: true },
  pagado: { type: String, required: true },
})

const porcentaje = computed(() => {
  const ap = Number(props.apropiado)
  if (!ap) return 0
  return Math.round((Number(props.pagado) / ap) * 1000) / 10
})
</script>

<template>
  <div class="bg-white rounded-lg border border-neutro/20 p-4">
    <div class="flex flex-wrap justify-between gap-2 text-sm mb-2">
      <span>
        <span class="text-neutro">Asignado
          <span class="cursor-help text-andino" title="Plata asignada para gastar este año" tabindex="0">ⓘ</span>
        </span>
        <strong class="ml-1 tabular">{{ formatoCiudadano(apropiado) }}</strong>
      </span>
      <span>
        <span class="text-neutro">Pagado
          <span class="cursor-help text-andino" title="Plata que ya salió de la cuenta del Estado" tabindex="0">ⓘ</span>
        </span>
        <strong class="ml-1 tabular">{{ formatoCiudadano(pagado) }}</strong>
      </span>
    </div>
    <div class="h-4 rounded-full bg-andino/15 overflow-hidden"
         role="progressbar" :aria-valuenow="porcentaje" aria-valuemin="0" aria-valuemax="100"
         :aria-label="`Ejecución: ${porcentaje}%`">
      <div
        class="h-full rounded-full transition-all duration-300"
        :class="porcentaje > 70 ? 'bg-ejecutado' : porcentaje < 40 ? 'bg-alerta' : 'bg-andino'"
        :style="{ width: Math.min(porcentaje, 100) + '%' }"
      />
    </div>
    <p class="text-sm text-neutro mt-2">
      {{ fraseEjecucion(porcentaje) }} ({{ formatoPorcentaje(porcentaje) }} de ejecución)
    </p>
  </div>
</template>
