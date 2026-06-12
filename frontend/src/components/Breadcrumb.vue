<script setup>
defineProps({
  // path del drill-down, ej: ['SALUD Y PROTECCIÓN SOCIAL', 'MINSALUD - GESTIÓN GENERAL']
  path: { type: Array, required: true },
})
const emit = defineEmits(['navegar'])
</script>

<template>
  <nav aria-label="Nivel de navegación" class="flex flex-wrap items-center gap-1 text-sm">
    <button
      class="font-semibold transition-colors"
      :class="path.length === 0 ? 'text-tinta cursor-default' : 'text-andino hover:underline'"
      :disabled="path.length === 0"
      @click="emit('navegar', 0)"
    >
      Todo el presupuesto
    </button>
    <template v-for="(tramo, i) in path" :key="i">
      <span class="text-neutro" aria-hidden="true">›</span>
      <button
        class="font-semibold text-left transition-colors"
        :class="i === path.length - 1 ? 'text-tinta cursor-default' : 'text-andino hover:underline'"
        :disabled="i === path.length - 1"
        @click="emit('navegar', i + 1)"
      >
        {{ tramo }}
      </button>
    </template>
  </nav>
</template>
