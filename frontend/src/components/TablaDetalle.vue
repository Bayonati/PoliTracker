<script setup>
// Vista tabla: misma data del treemap, accesible para lectores de pantalla
// y preferida en móvil. Columnas ordenables.
import { computed, ref } from 'vue'
import { formatoCompleto, formatoCiudadano, formatoPorcentaje } from '../utils/formato.js'

const props = defineProps({
  items: { type: Array, required: true },
  esUltimoNivel: { type: Boolean, default: false },
})
const emit = defineEmits(['drill'])

const columna = ref('apropiado')
const asc = ref(false)

const COLUMNAS = [
  { id: 'nombre', titulo: 'Nombre', numerica: false },
  { id: 'apropiado', titulo: 'Asignado', numerica: true },
  { id: 'pagado', titulo: 'Pagado', numerica: true },
  { id: 'porcentaje_ejecucion', titulo: '% ejecución', numerica: true },
]

function ordenarPor(id) {
  if (columna.value === id) asc.value = !asc.value
  else { columna.value = id; asc.value = id === 'nombre' }
}

const ordenados = computed(() => {
  const col = columna.value
  const numerica = COLUMNAS.find((c) => c.id === col)?.numerica
  return [...props.items].sort((a, b) => {
    const va = numerica ? Number(a[col]) : a[col]
    const vb = numerica ? Number(b[col]) : b[col]
    const cmp = va < vb ? -1 : va > vb ? 1 : 0
    return asc.value ? cmp : -cmp
  })
})

function claseEjecucion(p) {
  if (p > 70) return 'text-ejecutado'
  if (p < 40) return 'text-alerta'
  return 'text-tinta'
}
</script>

<template>
  <div class="overflow-x-auto bg-white rounded-lg border border-neutro/20">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-neutro/20 text-left">
          <th v-for="c in COLUMNAS" :key="c.id" class="p-0">
            <button
              class="w-full px-3 py-2.5 font-semibold text-neutro hover:text-andino text-left flex items-center gap-1"
              :class="{ 'justify-end': c.numerica }"
              :aria-sort="columna === c.id ? (asc ? 'ascending' : 'descending') : 'none'"
              @click="ordenarPor(c.id)"
            >
              {{ c.titulo }}
              <span v-if="columna === c.id" aria-hidden="true">{{ asc ? '↑' : '↓' }}</span>
            </button>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in ordenados" :key="item.nombre"
            class="border-b border-neutro/10 last:border-0 hover:bg-andino/5">
          <td class="px-3 py-2.5">
            <button
              v-if="!esUltimoNivel"
              class="text-andino hover:underline text-left font-medium"
              @click="emit('drill', item.nombre)"
            >{{ item.nombre }}</button>
            <span v-else class="font-medium">{{ item.nombre }}</span>
          </td>
          <td class="px-3 py-2.5 text-right tabular" :title="formatoCompleto(item.apropiado)">
            {{ formatoCiudadano(item.apropiado) }}
          </td>
          <td class="px-3 py-2.5 text-right tabular" :title="formatoCompleto(item.pagado)">
            {{ formatoCiudadano(item.pagado) }}
          </td>
          <td class="px-3 py-2.5 text-right tabular font-semibold"
              :class="claseEjecucion(item.porcentaje_ejecucion)">
            {{ formatoPorcentaje(item.porcentaje_ejecucion) }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
