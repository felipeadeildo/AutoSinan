<script setup lang="ts">
  withDefaults(defineProps<{ text?: string; textClass?: string }>(), {
    text: 'Carregando...',
    textClass: 'text-lg',
  })
</script>

<template>
  <div class="flex justify-center items-center">
    <UIcon
      name="i-heroicons-arrow-path-20-solid"
      size="lg"
      class="animate-spin"
    />
    <span :class="['ml-3 text-primary-500', textClass]">{{ text }}</span>
  </div>
</template>
