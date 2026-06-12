<script setup>
defineProps({
  etiqueta: { type: String, required: true },
  cifra: { type: String, required: true },
  contexto: { type: String, default: '' },
  ayuda: { type: String, default: '' }, // glosario ciudadano en tooltip
})
</script>

<template>
  <div class="bg-white rounded-lg border border-neutro/20 p-4">
    <div class="flex items-center gap-1 text-sm text-neutro">
      {{ etiqueta }}
      <span v-if="ayuda" class="cursor-help text-andino" :title="ayuda" tabindex="0"
            role="img" :aria-label="ayuda">ⓘ</span>
    </div>
    <div class="font-display font-bold text-2xl md:text-3xl mt-1 tabular">{{ cifra }}</div>
    <div v-if="contexto" class="text-sm text-neutro mt-1">{{ contexto }}</div>
  </div>
</template>
