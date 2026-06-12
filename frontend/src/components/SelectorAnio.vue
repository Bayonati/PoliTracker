<script setup>
defineProps({
  anios: { type: Array, required: true },
  modelValue: { type: Number, default: null },
})
const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <div class="flex items-center gap-1" role="group" aria-label="Seleccionar año">
    <button
      v-for="a in anios"
      :key="a"
      class="px-3 py-1.5 rounded-md text-sm font-semibold transition-colors"
      :class="a === modelValue
        ? 'bg-andino text-white'
        : 'text-neutro hover:bg-andino/10 hover:text-andino'"
      :aria-pressed="a === modelValue"
      @click="emit('update:modelValue', a)"
    >
      {{ a }}
    </button>
  </div>
</template>
